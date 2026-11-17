"""Neaktuální výpočet ocenění (rozhodnutí Martina 2026-11-17): upozornění ve formuláři a zákaz odeslání bez nového výpočtu."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase

DAY = date(2027, 1, 31)


@tagged("post_install", "-at_install")
class TestStaleCompute(NavCase):
    def computed_valuation(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 100)
        valuation = self.valuation(fund, DAY)
        valuation.action_compute()
        return fund, valuation

    def test_fresh_compute_is_current_and_stamped(self):
        _fund, valuation = self.computed_valuation()
        self.assertTrue(valuation.computed_at)
        self.assertTrue(valuation.inputs_stamp)
        self.assertFalse(valuation.stale_note)
        self.assertEqual(valuation._inputs_changed(), [])

    def test_manual_fee_after_compute_warns_and_blocks_submit(self):
        _fund, valuation = self.computed_valuation()
        self.manual_fee(valuation, 100)
        self.assertIn("ruční úplaty", valuation.stale_note)
        with self.assertRaisesRegex(UserError, "není aktuální"):
            valuation.action_submit()
        self.assertEqual(valuation.state, "computed")
        valuation.action_compute()
        self.assertFalse(valuation.stale_note)
        valuation.action_submit()
        self.assertEqual(valuation.state, "submitted")

    def test_deleted_manual_fee_is_detected(self):
        _fund, valuation = self.computed_valuation()
        fee = self.manual_fee(valuation, 100)
        valuation.action_compute()
        self.assertFalse(valuation.stale_note)
        fee.unlink()
        self.assertIn("ruční úplaty", valuation.stale_note)

    def test_new_subscription_after_compute_warns(self):
        fund, valuation = self.computed_valuation()
        self.subscribe(self.cls(fund, "A"), "2027-01-15", 500, 100)
        self.assertIn("úpisy a odkupy", valuation.stale_note)
