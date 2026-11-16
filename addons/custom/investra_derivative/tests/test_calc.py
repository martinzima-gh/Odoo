from datetime import date
from decimal import Decimal

from odoo.tests import BaseCase, tagged

from ..calc import days_left, leg_fair_value, leg_value, money


@tagged("post_install", "-at_install")
class TestDerivativeCalc(BaseCase):
    """Čistý výpočet reálné hodnoty (varianta B) proti tabulce příkladu v docs/navrh-fx-derivaty.md, na haléř."""

    TRADE, SETTLE = date(2026, 9, 30), date(2026, 12, 31)

    def fair_value(self, day, rate):
        # Vzdálená noha: koupě 24 900 000 CZK (kurz 1), prodej 1 000 000 EUR.
        b0 = leg_value(24_900_000, 1, 1_000_000, Decimal("25.00"))
        value = leg_value(24_900_000, 1, 1_000_000, Decimal(str(rate)))
        return value, money(leg_fair_value(value, b0, days_left(day, self.SETTLE), (self.SETTLE - self.TRADE).days))

    def test_example_table(self):
        table = [
            (date(2026, 9, 30), "25.00", "-100000.00", "0.00"),
            (date(2026, 10, 31), "24.80", "100000.00", "166304.35"),
            (date(2026, 11, 30), "25.10", "-200000.00", "-166304.35"),
            (date(2026, 12, 31), "25.20", "-300000.00", "-300000.00"),
        ]
        previous, changes = Decimal(0), []
        for day, rate, value, fair in table:
            got_value, got_fair = self.fair_value(day, rate)
            self.assertEqual(money(got_value), Decimal(value), day)
            self.assertEqual(got_fair, Decimal(fair), day)
            changes.append(got_fair - previous)
            previous = got_fair
        self.assertEqual(changes[1:], [Decimal("166304.35"), Decimal("-332608.70"), Decimal("-133695.65")])
        self.assertEqual(sum(changes), Decimal("-300000.00"))

    def test_zero_on_trade_date_and_value_after_maturity(self):
        self.assertEqual(self.fair_value(self.TRADE, "25.00")[1], Decimal("0.00"))
        self.assertEqual(self.fair_value(date(2027, 1, 15), "25.30")[1], Decimal("-400000.00"))

    def test_same_day_leg_has_no_points_to_release(self):
        self.assertEqual(leg_fair_value(Decimal("-5"), Decimal("-5"), 0, 0), Decimal("-5"))
