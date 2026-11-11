from datetime import date

from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestClassCurrency(NavCase):
    """Třída v EUR ve fondu v CZK; rok 2033 je jen pro tyto testy."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "E", "currency_id": self.eur.id}])
        self.fund_class = self.cls(self.fund, "E")
        self.rate("2033-01-03", 25)
        self.rate("2033-01-31", 26)

    def movement(self, kind="subscription", **vals):
        record = self.env["investra.class.movement"].create({
            "class_id": self.fund_class.id, "date": "2033-01-03", "manual_reason": "Test", "movement_type": kind, "amount_class": 1000, "units": 10, **vals,
        })
        record._book()
        return record

    def test_amount_uses_published_rate(self):
        movement = self.movement()
        self.assertEqual(movement.fx_rate, 25)
        self.assertEqual(movement.amount, 25000)

    def test_explicit_rate_wins(self):
        self.assertEqual(self.movement(fx_rate=24.5).amount, 24500)

    def test_bank_is_in_class_currency_and_capital_in_functional(self):
        movement = self.movement()
        lines = movement.event_id.move_id.line_ids
        bank = lines.filtered(lambda l: l.currency_id == self.eur)
        self.assertEqual(bank.amount_currency, 1000)
        self.assertEqual(bank.balance, 25000)
        capital = lines - bank
        self.assertEqual(capital.balance, -25000)
        self.assertEqual(capital.investra_class_id, self.fund_class)

    def test_redemption_reduces_bank_in_class_currency(self):
        self.movement()
        redemption = self.movement("redemption", amount_class=200, units=2)
        bank = redemption.event_id.move_id.line_ids.filtered(lambda l: l.currency_id == self.eur)
        self.assertEqual(bank.amount_currency, -200)
        self.assertEqual(bank.balance, -5000)

    def test_movement_events_carry_class_currency(self):
        """Bod 15: úpis i odkup ukazují částku v měně třídy kladně, zdroj a fond."""
        subscription = self.movement()
        redemption = self.movement("redemption", amount_class=200, units=2)
        for movement, functional, original in ((subscription, 25000, 1000), (redemption, 5000, 200)):
            event = movement.event_id
            self.assertEqual(event.event_type, "class_movement")
            self.assertEqual((event.res_model, event.res_id, event.fund_id), ("investra.class.movement", movement.id, self.fund))
            self.assertEqual(event.amount, functional)
            self.assertEqual(event.foreign_currency_id, self.eur)
            self.assertEqual(event.amount_currency, original)

    def test_nav_in_functional_price_in_class_currency(self):
        """EUR na účtu posílí v CZK; FK roste, kurz v EUR zůstává."""
        self.movement()
        valuation = self.valuation(self.fund, date(2033, 1, 31))
        self.run_to_posted(valuation)
        self.assertEqual(valuation.fund_capital, 26000)
        line = valuation.class_line_ids
        self.assertEqual(line.capital, 26000)
        self.assertEqual(line.price, "100.0000")

    def test_functional_class_without_amount_class_is_unchanged(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        movement = self.subscribe(self.cls(fund, "A"), "2033-01-03", 1000, 10)
        self.assertEqual(movement.amount, 1000)
        self.assertFalse(movement.event_id.move_id.line_ids.filtered(lambda l: l.currency_id == self.eur))
