from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.investra_instruments.tests.test_instrument import InstrumentCase

from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestInstrumentClassification(InstrumentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Instrument = cls.env["investra.instrument"]
        cls.bond_type = cls.env.ref("investra_instruments.type_bond")
        cls.deposit_type = cls.env.ref("investra_instruments.type_deposit")
        cls.partner = cls.env["res.partner"].create({"name": "Emitent"})

    def ba(self, code):
        return self.env["investra.ba0088.code"].search([("code", "=", code)])

    def make(self, type_=None, **vals):
        type_ = type_ or self.bond_type
        return self.Instrument.create(with_ids(self.env, {
            "name": "Test", "currency_id": self.czk.id, "type_id": type_.id, **vals}, self.fund))

    def helper_code(self, code, **vals):
        return self.env["investra.ba0088.code"].create({
            "code": code, "name": f"Pomocný {code}", "selectable": True, "asset_family": "other", **vals})

    # --- CFI -------------------------------------------------------------------------------------------------------

    def test_cfi_valid_and_uppercased(self):
        self.assertEqual(self.make(cfi_code="ABCDEF").cfi_code, "ABCDEF")
        self.assertEqual(self.make(cfi_code="abcdef").cfi_code, "ABCDEF")
        instrument = self.make()
        instrument.write({"cfi_code": " ghijkl "})
        self.assertEqual(instrument.cfi_code, "GHIJKL")

    def test_cfi_invalid_is_rejected(self):
        for bad in ("ABCDE", "ABCDEFG", "ABC123", "123456"):
            with self.assertRaises(ValidationError, msg=bad):
                self.make(cfi_code=bad)

    def test_cfi_warning_follows_map(self):
        instrument = self.make(ba0088_id=self.ba("211").id, cfi_code="ESVUFR")
        self.assertFalse(instrument.cfi_warning)
        self.env["investra.cfi.ba0088.map"].create({"cfi_prefix": "ES", "ba0088_id": self.ba("212").id})
        instrument.invalidate_recordset()
        self.assertIn("ESVUFR", instrument.cfi_warning)
        self.env["investra.cfi.ba0088.map"].create({"cfi_prefix": "ESV", "ba0088_id": self.ba("211").id})
        instrument.invalidate_recordset()
        self.assertFalse(instrument.cfi_warning)

    # --- BA0088 a rodina -------------------------------------------------------------------------------------------

    def test_family_follows_ba0088(self):
        equity = self.make(ba0088_id=self.ba("211").id)
        self.assertEqual(equity.asset_family, "equity")
        debt = self.make(ba0088_id=self.ba("141").id)
        self.assertEqual(debt.asset_family, "debt")
        debt.ba0088_id = self.ba("211")
        self.assertEqual(debt.asset_family, "equity")

    def test_debt_form_shows_maturity_nominal_coupon(self):
        arch = self.Instrument.get_view(self.env.ref("investra_instruments.view_instrument_form").id)["arch"]
        for name in ("maturity_date", "nominal_value", "coupon_type", "coupon_rate", "asset_family", "ba0088_id", "cfi_code"):
            self.assertIn(f'name="{name}"', arch)
        self.assertIn("asset_family != &#39;debt&#39;", arch.replace("'", "&#39;"))

    def test_leverage_rule(self):
        must_true = self.helper_code("T901", leverage_rule="must_true")
        must_false = self.helper_code("T902", leverage_rule="must_false")
        with self.assertRaises(ValidationError):
            self.make(ba0088_id=must_true.id)
        self.make(ba0088_id=must_true.id, leverage_flag=True)
        with self.assertRaises(ValidationError):
            self.make(ba0088_id=must_false.id, leverage_flag=True)
        self.make(ba0088_id=must_false.id)

    def test_justification_required(self):
        code = self.helper_code("T903", requires_justification=True)
        with self.assertRaises(ValidationError):
            self.make(ba0088_id=code.id)
        self.assertTrue(self.make(ba0088_id=code.id, ba0088_note="Důvod").ba0088_note)

    def test_other_attributes_checks(self):
        with self.assertRaises(ValidationError):
            self.make(issue_date="2026-02-01", maturity_date="2026-01-01")
        with self.assertRaises(ValidationError):
            self.make(nominal_value=-1)

    # --- ISIN ------------------------------------------------------------------------------------------------------

    def test_isin_warning_does_not_block(self):
        bad = self.make(isin="CZ0000000001")
        self.assertIn("CZ0000000001", bad.isin_warning)
        good = self.make(isin="US0378331005")
        self.assertFalse(good.isin_warning)

    # --- potvrzení a zámek -----------------------------------------------------------------------------------------

    def test_confirm_requires_ba0088_for_required_type(self):
        instrument = self.make()
        with self.assertRaises(UserError):
            instrument.with_user(self.approver).action_confirm_classification()
        deposit = self.make(self.deposit_type)
        deposit.with_user(self.approver).action_confirm_classification()
        self.assertEqual(deposit.review_state, "reviewed")

    def test_confirm_requires_issuer_and_maturity(self):
        instrument = self.make(ba0088_id=self.ba("141").id)
        self.assertIn("emitent", instrument.classification_gap)
        with self.assertRaises(UserError):
            instrument.with_user(self.approver).action_confirm_classification()
        instrument.issuer_id = self.partner
        with self.assertRaises(UserError):
            instrument.with_user(self.approver).action_confirm_classification()
        instrument.maturity_date = "2030-01-01"
        self.assertFalse(instrument.classification_gap)
        instrument.with_user(self.approver).action_confirm_classification()
        self.assertEqual((instrument.review_state, instrument.reviewed_by), ("reviewed", self.approver))

    def test_only_approver_confirms(self):
        deposit = self.make(self.deposit_type)
        with self.assertRaises(UserError):
            deposit.with_user(self.preparer).action_confirm_classification()

    def confirmed(self):
        instrument = self.make(self.env.ref("investra_instruments.type_participation"), fund_id=self.fund.id, ba0088_id=self.ba("211").id, issuer_id=self.partner.id, cfi_code="ESVUFR")
        instrument.with_user(self.approver).action_confirm_classification()
        return instrument

    def test_direct_write_after_confirmation_fails(self):
        instrument = self.confirmed().with_user(self.preparer)
        for vals in ({"ba0088_id": self.ba("212").id}, {"cfi_code": "ESVUFX"}, {"isin": "US0378331005"},
                     {"issuer_id": False}):
            with self.assertRaises(UserError, msg=str(vals)):
                instrument.write(vals)
        instrument.write({"name": "Přejmenovaný", "cfi_code": "ESVUFR"})  # nezměněná hodnota ani jiné pole nevadí

    def test_wizard_changes_confirmed_classification_with_history(self):
        instrument = self.confirmed()
        wizard = self.env["investra.masterdata.change.wizard"].with_user(self.preparer).create({
            "instrument_id": instrument.id, "ba0088_id": self.ba("212").id, "cfi_code": "esvufx",
            "isin": instrument.isin, "issuer_id": self.partner.id, "reason": "Oprava podle prospektu"})
        wizard.action_apply()
        self.assertEqual((instrument.ba0088_id, instrument.cfi_code), (self.ba("212"), "ESVUFX"))
        history = self.env["investra.masterdata.change"].search([("res_id", "=", instrument.id)])
        self.assertEqual(set(history.mapped("reason")), {"Oprava podle prospektu"})
        self.assertEqual(len(history), 2)
        self.assertEqual(history.filtered(lambda h: h.field_name == "CFI").new_value, "ESVUFX")
        self.assertEqual(history.user_id, self.preparer)

    def test_wizard_requires_reason_and_change(self):
        instrument = self.confirmed()
        Wizard = self.env["investra.masterdata.change.wizard"].with_user(self.preparer)
        with self.assertRaises(Exception):
            Wizard.create({"instrument_id": instrument.id})
        same = Wizard.create({
            "instrument_id": instrument.id, "ba0088_id": instrument.ba0088_id.id, "cfi_code": instrument.cfi_code,
            "isin": instrument.isin, "issuer_id": self.partner.id, "reason": "Nic"})
        with self.assertRaises(UserError):
            same.action_apply()

    def test_history_is_read_only_for_users(self):
        from odoo.exceptions import AccessError
        with self.assertRaises(AccessError):
            self.env["investra.masterdata.change"].with_user(self.preparer).create({
                "res_model": "x", "res_id": 1, "reason": "x"})
