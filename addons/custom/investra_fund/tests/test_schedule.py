from datetime import date

from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_fund.models.schedule import next_valuation_date


@tagged("post_install", "-at_install")
class TestSchedule(TransactionCase):
    """Očekávané datum dalšího ocenění z frekvence (MN-14); čistá funkce, pravidla dnů jsou návrh."""

    def test_monthly(self):
        self.assertEqual(next_valuation_date(date(2026, 9, 30), "monthly"), date(2026, 10, 31))
        self.assertEqual(next_valuation_date(date(2026, 1, 31), "monthly"), date(2026, 2, 28))
        self.assertEqual(next_valuation_date(date(2032, 1, 31), "monthly"), date(2032, 2, 29))  # přestupný rok
        self.assertEqual(next_valuation_date(date(2026, 12, 31), "monthly"), date(2027, 1, 31))  # přelom roku
        self.assertEqual(next_valuation_date(date(2026, 3, 15), "monthly"), date(2026, 4, 30))

    def test_quarterly(self):
        self.assertEqual(next_valuation_date(date(2026, 3, 31), "quarterly"), date(2026, 6, 30))
        self.assertEqual(next_valuation_date(date(2026, 2, 15), "quarterly"), date(2026, 6, 30))
        self.assertEqual(next_valuation_date(date(2026, 12, 31), "quarterly"), date(2027, 3, 31))
        self.assertEqual(next_valuation_date(date(2026, 11, 16), "quarterly"), date(2027, 3, 31))

    def test_yearly(self):
        self.assertEqual(next_valuation_date(date(2026, 12, 31), "yearly"), date(2027, 12, 31))
        self.assertEqual(next_valuation_date(date(2026, 5, 5), "yearly"), date(2027, 12, 31))

    def test_weekly_is_next_friday(self):
        self.assertEqual(next_valuation_date(date(2026, 11, 13), "weekly"), date(2026, 11, 20))  # pátek -> další pátek
        self.assertEqual(next_valuation_date(date(2026, 11, 16), "weekly"), date(2026, 11, 20))  # pondělí
        self.assertEqual(next_valuation_date(date(2026, 11, 14), "weekly"), date(2026, 11, 20))  # sobota
        self.assertEqual(next_valuation_date(date(2026, 12, 31), "weekly"), date(2027, 1, 1))  # přelom roku

    def test_daily_is_next_working_day(self):
        self.assertEqual(next_valuation_date(date(2026, 11, 12), "daily"), date(2026, 11, 13))  # čtvrtek -> pátek
        self.assertEqual(next_valuation_date(date(2026, 11, 13), "daily"), date(2026, 11, 16))  # pátek -> pondělí
        self.assertEqual(next_valuation_date(date(2026, 11, 14), "daily"), date(2026, 11, 16))  # sobota
        self.assertEqual(next_valuation_date(date(2026, 12, 31), "daily"), date(2027, 1, 1))

    def test_missing_input(self):
        self.assertFalse(next_valuation_date(False, "monthly"))
        self.assertFalse(next_valuation_date(date(2026, 1, 1), "unknown"))
        # prázdná frekvence (False, None, "") při platném datu – nález revize CP-MN14, bod 5
        for empty in (False, None, ""):
            self.assertFalse(next_valuation_date(date(2026, 1, 1), empty))
