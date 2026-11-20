from datetime import date
from decimal import Decimal

from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_nav import engine


def rule(*versions):
    return {"basis": "act365", "versions": [
        {"valid_from": date.fromisoformat(day), "fixed_monthly": 10000, "fixed_mode": "started_month", "rate": 0} for day in versions]}


@tagged("post_install", "-at_install")
class TestFeeStartedMonth(TransactionCase):
    """ZJ-20, bod 17: „Za každý započatý měsíc“ počítá kalendářní měsíce, kterých se období (start, konec] dotýká."""

    def fee(self, start, end, *versions):
        return engine.periodic_fee(rule(*(versions or ("2026-01-01",))), start, end, Decimal(0))["amount"]

    def test_period_inside_one_month_counts_the_started_month(self):
        # Úplata třídy začíná dnem prvního úpisu (1. 10.); dřív vycházelo 0.
        self.assertEqual(self.fee(date(2026, 10, 1), date(2026, 10, 31)), Decimal("10000.00"))
        self.assertEqual(self.fee(date(2026, 10, 15), date(2026, 10, 31)), Decimal("10000.00"))

    def test_month_end_to_month_end_unchanged(self):
        self.assertEqual(self.fee(date(2026, 9, 30), date(2026, 10, 31)), Decimal("10000.00"))
        self.assertEqual(self.fee(date(2026, 10, 31), date(2026, 12, 31)), Decimal("20000.00"))
        self.assertEqual(self.fee(date(2026, 12, 31), date(2027, 3, 31)), Decimal("30000.00"))

    def test_mid_month_period_across_two_months(self):
        self.assertEqual(self.fee(date(2026, 10, 15), date(2026, 11, 15)), Decimal("20000.00"))

    def test_version_change_inside_month_does_not_count_month_twice(self):
        # Druhá verze začíná 15. 11.; listopad se platí jednou (v úseku, ve kterém začíná).
        self.assertEqual(self.fee(date(2026, 10, 31), date(2026, 11, 30), "2026-01-01", "2026-11-15"), Decimal("10000.00"))
