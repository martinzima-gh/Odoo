from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_nav import engine

from .common import NavCase


def version(day, **vals):
    return {"valid_from": date.fromisoformat(day), "rate": 0, "fixed_monthly": 0, "fixed_mode": "pro_rata", **vals}


def rule(*versions):
    return {"basis": "act365", "versions": list(versions)}


@tagged("post_install", "-at_install")
class TestZj24Bod15Engine(TransactionCase):
    """ZJ-24 bod 15: období před první verzí sazby se neúčtuje (0); pravidlo bez verze zůstává chybou."""

    def fee(self, start, end, base, *versions):
        return engine.periodic_fee(rule(*versions), start, end, Decimal(base))

    def test_period_before_first_version_is_zero(self):
        result = self.fee(date(2026, 12, 31), date(2027, 1, 31), 1000000, version("2027-03-01", rate="0.01"))
        self.assertEqual(result["amount"], Decimal("0.00"))
        self.assertEqual(result["uncovered_days"], 31)
        self.assertEqual(len(result["segments"]), 1)
        self.assertTrue(result["segments"][0]["uncovered"])

    def test_part_of_period_before_first_version(self):
        result = self.fee(date(2026, 12, 31), date(2027, 1, 31), 1000000, version("2027-01-10", rate="0.01"))
        # úsek s verzí je (9. 1., 31. 1.] = 22 dní
        self.assertEqual(result["amount"], engine.money(Decimal(1000000) * Decimal("0.01") * 22 / 365))
        self.assertEqual(result["uncovered_days"], 9)

    def test_started_month_counts_first_covered_segment(self):
        result = self.fee(date(2026, 12, 31), date(2027, 1, 31), 0,
                          version("2027-01-10", fixed_monthly=10000, fixed_mode="started_month"))
        self.assertEqual(result["amount"], Decimal("10000.00"))

    def test_minimum_applies_only_to_covered_days(self):
        result = self.fee(date(2026, 12, 31), date(2027, 1, 31), 0, version("2027-01-10", min_annual=120000))
        self.assertEqual(result["amount"], engine.money(Decimal(120000) * 22 / 365))

    def test_rule_without_version_is_error(self):
        with self.assertRaises(ValueError):
            self.fee(date(2026, 12, 31), date(2027, 1, 31), 1000)

    def test_fully_covered_period_unchanged(self):
        # Pevná hodnota spočtená z kódu před změnou (K1): dvě verze, změna 15. 1. 2026.
        result = self.fee(date(2025, 12, 31), date(2026, 1, 31), 1000000,
                          version("2025-01-01", rate="0.01", fixed_monthly=500, min_annual=1000),
                          version("2026-01-15", rate="0.02"))
        self.assertEqual(result["amount"], Decimal("1545.21"))
        self.assertEqual(result["uncovered_days"], 0)


@tagged("post_install", "-at_install")
class TestZj24Bod15Valuation(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def make(self, first):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 36500, 100)
        self.Rule.create({"fund_id": fund.id, "name": "Úplata správce", "kind": "periodic",
                          "version_ids": [(0, 0, {"valid_from": first, "rate": 0.0365})]})
        return fund

    def late_check(self, valuation):
        return valuation.check_ids.filtered(lambda c: c.code == "fee_not_in_force")

    def test_rule_starting_inside_period_charges_covered_part(self):
        valuation = self.valuation(self.make("2027-01-10"), date(2027, 1, 31))
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 80.30, places=2)  # 36 500 × 3,65 % × 22/365
        check = self.late_check(valuation)
        self.assertEqual(check.status, "warning")
        self.assertIn("Úplata správce", check.detail)

    def test_rule_starting_after_valuation_charges_nothing(self):
        valuation = self.valuation(self.make("2027-03-01"), date(2027, 1, 31))
        valuation.action_compute()
        self.assertFalse(valuation.fee_line_ids.filtered("amount"))
        self.assertTrue(self.late_check(valuation))

    def test_rule_in_force_adds_no_check(self):
        valuation = self.valuation(self.make("2020-01-01"), date(2027, 1, 31))
        valuation.action_compute()
        self.assertFalse(self.late_check(valuation))

    def test_zero_capital_names_classes_sharing_common_items(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}, {"code": "B", "shares_common": False}])
        self.subscribe(self.cls(fund, "B"), "2026-12-20", 1000, 10)
        with self.assertRaises(UserError) as raised:
            self.valuation(fund, date(2027, 1, 31)).action_compute()
        message = str(raised.exception)
        self.assertIn("tříd A", message)
        self.assertNotIn("před datem vzniku fondu", message)
