from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.investra_instruments.tests.common import with_ids
from odoo.addons.investra_instruments.tests.test_instrument import InstrumentCase


@tagged("post_install", "-at_install")
class TestAccountingProfile(InstrumentCase):
    """Výběr účetního profilu podle společnosti, portfolia a druhu BA0088 (úkol IM-07); nic se neúčtuje."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Profile = cls.env["investra.accounting.profile"]
        cls.Rule = cls.env["investra.accounting.profile.assignment"]
        cls.portfolio_fv = cls.portfolio(cls.fund)
        cls.equity = cls.make_instrument("equity", cls.ba("211"))
        cls.bond = cls.make_instrument("bond", cls.ba("149"), coupon_type="fixed")
        cls.eq_class = cls.classify(cls.fund, cls.equity)
        cls.bond_class = cls.classify(cls.fund, cls.bond)
        cls.p_equity = cls.profile("PE", cls.eq_class.role_id)
        cls.p_bond = cls.profile("PB", cls.bond_class.role_id)

    @classmethod
    def ba(cls, code):
        return cls.env["investra.ba0088.code"].search([("code", "=", code)])

    @classmethod
    def make_instrument(cls, kind, ba0088, **vals):
        return cls.env["investra.instrument"].create(with_ids(cls.env, {
            "name": f"{kind} {ba0088.code}", "currency_id": cls.czk.id, "ba0088_id": ba0088.id,
            "type_id": cls.env.ref(f"investra_instruments.type_{kind}").id, **vals,
        }, cls.fund))

    @classmethod
    def profile(cls, code, role):
        return cls.Profile.create({"code": code, "name": f"Profil {code}", "role_id": role.id})

    def rule(self, profile, **vals):
        return self.Rule.create({
            "company_id": self.company.id, "accounting_profile_id": profile.id, "valid_from": "2020-01-01", **vals,
        })

    def pick(self, classification, day="2026-11-15"):
        return self.Rule._select(self.company, classification.portfolio_id, classification.instrument_id.ba0088_id, day)

    # --- výběr -----------------------------------------------------------------------------------------------

    def test_same_portfolio_different_codes_get_different_profiles(self):
        self.rule(self.p_equity, portfolio_id=self.portfolio_fv.id, ba0088_id=self.ba("211").id)
        self.rule(self.p_bond, portfolio_id=self.portfolio_fv.id, ba0088_id=self.ba("149").id)
        self.assertEqual(self.eq_class.portfolio_id, self.bond_class.portfolio_id)
        self.assertEqual(self.eq_class.accounting_profile_id, self.p_equity)
        self.assertEqual(self.bond_class.accounting_profile_id, self.p_bond)
        self.assertEqual((self.eq_class.profile_state, self.bond_class.profile_state), ("ok", "ok"))

    def test_code_beats_group_beats_general(self):
        general = self.rule(self.p_bond)
        group = self.rule(self.p_equity, ba0088_group_id=self.ba("211").group_id.id)
        code = self.rule(self.p_bond, ba0088_id=self.ba("211").id)
        self.assertEqual(self.pick(self.eq_class), code)
        code.valid_to = "2020-06-30"      # mimo platnost: nastupuje skupina
        self.assertEqual(self.pick(self.eq_class), group)
        group.valid_to = "2020-06-30"
        self.assertEqual(self.pick(self.eq_class), general)

    def test_lower_priority_number_wins_over_specificity(self):
        self.rule(self.p_bond, ba0088_id=self.ba("211").id, priority=20)
        general = self.rule(self.p_equity, priority=5)
        self.assertEqual(self.pick(self.eq_class), general)

    def test_specific_portfolio_beats_general_with_same_priority(self):
        self.rule(self.p_bond, ba0088_id=self.ba("211").id)
        specific = self.rule(self.p_equity, ba0088_id=self.ba("211").id, portfolio_id=self.portfolio_fv.id, priority=10)
        # stejná priorita i kód: konkrétní portfolio má přednost před obecným
        self.assertEqual(self.pick(self.eq_class), specific)

    def test_rule_outside_validity_is_ignored(self):
        self.rule(self.p_equity, ba0088_id=self.ba("211").id, valid_from="2027-01-01")
        self.rule(self.p_equity, ba0088_id=self.ba("211").id, valid_from="2020-01-01", valid_to="2020-12-31", priority=11)
        self.assertFalse(self.pick(self.eq_class))
        self.assertEqual(self.eq_class.profile_state, "missing")

    # --- kontroly --------------------------------------------------------------------------------------------

    def test_duplicate_rule_is_rejected(self):
        self.rule(self.p_equity, ba0088_id=self.ba("211").id)
        with self.assertRaisesRegex(ValidationError, "už platí pravidlo"):
            self.rule(self.p_bond, ba0088_id=self.ba("211").id, valid_from="2025-01-01")

    def test_same_combination_with_other_priority_or_period_is_allowed(self):
        self.rule(self.p_equity, ba0088_id=self.ba("211").id, valid_to="2020-12-31")
        self.rule(self.p_equity, ba0088_id=self.ba("211").id, valid_from="2021-01-01")
        self.rule(self.p_equity, ba0088_id=self.ba("211").id, valid_from="2021-01-01", priority=20)

    def test_code_and_group_together_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "buď druh BA0088, nebo skupinu"):
            self.rule(self.p_equity, ba0088_id=self.ba("211").id, ba0088_group_id=self.ba("211").group_id.id)

    def test_portfolio_of_other_company_is_rejected(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond jiný", "fund", "cas501", self.czk, "investra_fund")
        other_fund = self.env["investra.fund"].sudo().create({"entity_id": other_book.id})
        with self.assertRaisesRegex(ValidationError, "patří jiné společnosti"):
            self.rule(self.p_equity, portfolio_id=other_fund.portfolio_ids[:1].id)

    # --- stav a _require_profile -------------------------------------------------------------------------------

    def test_missing_profile_state_and_require_profile(self):
        self.assertFalse(self.eq_class.accounting_profile_id)
        self.assertEqual(self.eq_class.profile_state, "missing")
        with self.assertRaisesRegex(UserError, r"Pro portfolio .* a druh 211 .* není nastaven účetní profil\."):
            self.eq_class._require_profile()

    def test_role_deviation_is_shown_and_nothing_is_overwritten(self):
        role_before = self.eq_class.role_id
        self.rule(self.p_bond, ba0088_id=self.ba("211").id)
        self.assertEqual(self.eq_class.accounting_profile_id, self.p_bond)
        self.assertEqual(self.eq_class.profile_state, "deviates")
        self.assertEqual(self.eq_class.role_id, role_before)
        self.assertEqual(self.eq_class._require_profile(), self.p_bond)

    # --- oprávnění -------------------------------------------------------------------------------------------

    def test_foreign_company_assignment_is_invisible(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond cizí", "fund", "cas501", self.czk, "investra_fund")
        foreign = self.Rule.sudo().create({
            "company_id": other_book.company_id.id, "accounting_profile_id": self.p_equity.id, "valid_from": "2020-01-01",
        })
        own = self.rule(self.p_equity, ba0088_id=self.ba("211").id)
        visible = self.Rule.with_user(self.preparer).search([])
        self.assertIn(own, visible)
        self.assertNotIn(foreign, visible)
