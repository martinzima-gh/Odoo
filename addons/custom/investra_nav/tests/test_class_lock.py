from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestClassLock(NavCase):
    """MN-07: po prvním zaúčtovaném pohybu třídy nejde změnit kód, měna a zaokrouhlení; poplatky ano."""

    def _locked_class(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        return fund, self.cls(fund, "A"), self.cls(fund, "B")

    def test_free_before_first_movement(self):
        fund, class_a, _class_b = self._locked_class()
        class_a.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_a.movement_locked)
        class_a.write({"code": "A1", "currency_id": self.eur.id, "price_digits": 2, "unit_digits": 3,
                       "price_rounding": "up", "unit_rounding": "up"})
        self.assertEqual(class_a.code, "A1")

    def test_draft_movement_does_not_lock(self):
        _fund, class_a, _class_b = self._locked_class()
        self.env["investra.class.movement"].create({
            "class_id": class_a.id, "date": "2027-01-01", "manual_reason": "Test", "movement_type": "subscription",
            "amount": 1000, "units": 10,
        })
        class_a.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_a.movement_locked)
        class_a.code = "A2"

    def test_locked_after_posted_movement(self):
        _fund, class_a, class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        class_a.invalidate_recordset(["movement_locked"])
        self.assertTrue(class_a.movement_locked)
        for vals in ({"code": "X"}, {"currency_id": self.eur.id}, {"price_digits": 2}, {"price_rounding": "up"},
                     {"unit_digits": 2}, {"unit_rounding": "up"}):
            with self.assertRaisesRegex(UserError, "zaúčtovaný úpis nebo odkup"):
                class_a.write(vals)
        # Stejná hodnota není změna; jiná třída bez pohybu zůstává volná.
        class_a.write({"code": class_a.code, "currency_id": class_a.currency_id.id})
        class_b.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_b.movement_locked)
        class_b.code = "B2"

    def test_fees_and_name_stay_editable(self):
        _fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        class_a.write({
            "name": "Nový název", "entry_fee_rate": 1.5, "exit_fee_rate": 0.5,
            "entry_fee_recipient": "distributor", "exit_fee_recipient": "fund", "isin": "US0378331005", "sequence": 5,
        })
        self.assertEqual(class_a.entry_fee_rate, 1.5)
        self.assertEqual(class_a.entry_fee_recipient, "distributor")

    def test_reversed_movement_keeps_lock(self):
        _fund, class_a, _class_b = self._locked_class()
        movement = self.subscribe(class_a, "2027-01-01", 1000, 10)
        movement.sudo().write({"state": "reversed"})
        class_a.invalidate_recordset(["movement_locked"])
        self.assertTrue(class_a.movement_locked)
        with self.assertRaisesRegex(UserError, "zaúčtovaný úpis nebo odkup"):
            class_a.code = "X"

    def test_form_fields_read_only_when_locked(self):
        fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        view = fund.get_view(self.env.ref("investra_fund.view_fund_form").id)
        arch = view["arch"]
        for name in ("code", "currency_id", "price_digits", "unit_digits", "price_rounding", "unit_rounding"):
            self.assertRegex(arch, rf'<field name="{name}"[^>]*readonly="movement_locked"', name)
        self.assertIn('widget="handle"', arch)
        Form(fund)  # formulář se načte
