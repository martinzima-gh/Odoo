from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestZj24Messages(NavCase):
    """ZJ-24 body 13 a 14: úpis před vznikem fondu a chybějící sazba pravidla úplaty říkají, co je špatně."""

    def movement_form(self, fund, day):
        form = Form(self.env["investra.class.movement"].with_context(default_movement_type="subscription"))
        form.class_id = self.cls(fund, "A")
        form.date = day
        return form

    def test_form_warns_when_movement_is_not_after_launch(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}])
        self.assertIn("2026-12-31", self.movement_form(fund, "2026-12-20").launch_warning)
        # Pohyb ke dni vzniku se do prvního období (po datu vzniku) také nezapočte.
        self.assertTrue(self.movement_form(fund, "2026-12-31").launch_warning)
        self.assertFalse(self.movement_form(fund, "2027-01-05").launch_warning)

    def test_zero_capital_names_early_movement(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2026-12-20", 1000, 10)
        with self.assertRaisesRegex(UserError, "před datem vzniku fondu.*2026-12-20|2026-12-20.*před datem vzniku fondu"):
            self.valuation(fund, date(2027, 1, 31)).action_compute()

    def test_zero_capital_without_movements_keeps_general_message(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}])
        with self.assertRaisesRegex(UserError, "Předběžný kapitál fondu je nulový"):
            self.valuation(fund, date(2027, 1, 31)).action_compute()

    def test_missing_rate_names_rule_fund_and_first_version(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-05", 36500, 100)
        rule = self.env["investra.fee.rule"].create({
            "fund_id": fund.id, "name": "Úplata správce", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2027-01-10", "rate": 0.0365})],
        })
        with self.assertRaises(UserError) as raised:
            self.valuation(fund, date(2027, 1, 31)).action_compute()
        message = str(raised.exception)
        self.assertIn("Úplata správce", message)
        self.assertIn(fund.display_name, message)
        self.assertIn("2027-01-10", message)
        self.assertIn("2027-01-01", message)  # den, ke kterému sazba chybí (první den období po datu vzniku)
        self.assertEqual(rule.version_ids.valid_from, date(2027, 1, 10))
