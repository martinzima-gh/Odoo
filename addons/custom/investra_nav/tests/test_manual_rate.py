from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestManualRate(NavCase):
    """Ruční kurz a ocenění (rozhodnutí 2026-11-10 „Ochrana kurzů“). Rok 2036 je jen pro tyto testy."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(launch="2035-12-31", classes=[
            {"code": "C", "price_digits": 4}, {"code": "E", "price_digits": 4, "currency_id": self.eur.id},
        ])
        self.rate("2036-01-02", 25)
        self.rate("2036-01-31", 25)
        self.subscribe(self.cls(self.fund, "C"), "2036-01-02", 1000, 10)
        self.env["investra.class.movement"].create({
            "class_id": self.cls(self.fund, "E").id, "date": "2036-01-02", "movement_type": "subscription",
            "amount_class": 40, "fx_rate": 25, "units": 10,
        })._book()
        self.day = date(2036, 1, 31)

    def override(self, day, rate=26):
        return self.env["investra.rate"].with_user(self.approver).create_manual(
            "override", "cnb", self.eur, day, 1, rate, "Chyba zdroje",
        )

    def check(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code)

    def test_valuation_warns_when_rate_is_manual(self):
        self.override(self.day)
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        check = self.check(valuation, "manual_rate")
        self.assertEqual(check.status, "warning")
        self.assertIn("EUR", check.detail)
        self.assertIn("Chyba zdroje", check.detail)

    def test_valuation_without_manual_rate_is_ok(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.assertEqual(self.check(valuation, "manual_rate").status, "ok")

    def test_override_refused_after_approved_valuation(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        valuation.with_user(self.approver).action_approve()
        with self.assertRaisesRegex(UserError, "schválené ocenění"):
            self.override(self.day)
        with self.assertRaisesRegex(UserError, "schválené ocenění"):
            self.override(date(2036, 1, 2))

    def test_override_allowed_while_valuation_is_only_computed(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.override(self.day)
        valuation.action_compute()
        self.assertEqual(self.check(valuation, "manual_rate").status, "warning")
