from decimal import Decimal

from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestPriceHistory(NavCase):
    """Přehled zveřejněných kurzů tříd pro grafy: třída A v CZK, B v EUR; rok 2032 je jen pro tyto testy."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B", "currency_id": self.eur.id}])
        for day, value in (("2032-01-02", 25), ("2032-01-31", 25.5), ("2032-02-29", 25.2), ("2032-03-31", 25.1)):
            self.rate(day, value)
        self.subscribe(self.cls(self.fund, "A"), "2032-01-02", 60000, 600)
        movement = self.env["investra.class.movement"].create({
            "class_id": self.cls(self.fund, "B").id, "date": "2032-01-02", "manual_reason": "Test",
            "movement_type": "subscription", "amount_class": 1600, "units": 400,
        })
        movement._book()
        self.History = self.env["investra.valuation.price.history"]

    def history(self):
        return self.History.search([("fund_id", "=", self.fund.id)])

    def test_published_price_in_class_currency(self):
        valuation = self.run_to_published(self.valuation(self.fund, "2032-01-31"))
        rows = self.history()
        self.assertEqual(len(rows), 2)
        for row in rows:
            line = valuation.class_line_ids.filtered(lambda l: l.class_id == row.class_id)
            # Stejná hodnota jako zveřejněný kurz (text), v měně třídy, bez přepočtu.
            self.assertEqual(Decimal(str(row.price)), Decimal(line.price))
            self.assertEqual(row.currency_id, row.class_id.currency_id)
            self.assertEqual((row.date, row.valuation_id), (valuation.date, valuation))
        self.assertEqual(rows.filtered(lambda r: r.class_id.code == "B").currency_id, self.eur)
        self.assertEqual(rows.filtered(lambda r: r.class_id.code == "A").currency_id, self.czk)

    def test_only_published(self):
        self.run_to_published(self.valuation(self.fund, "2032-01-31"))
        self.run_to_posted(self.valuation(self.fund, "2032-02-29"))
        self.valuation(self.fund, "2032-03-31").action_compute()
        self.assertEqual(sorted({str(day) for day in self.history().mapped("date")}), ["2032-01-31"])
