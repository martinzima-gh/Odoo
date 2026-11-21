from datetime import date

from odoo.tests import tagged

from odoo.addons.investra_instruments.tests.common import with_ids

from .common import NavCase


@tagged("post_install", "-at_install")
class TestZj25Portfolio(NavCase):
    """ZJ-25 G9: Změna ceny a z toho kurz u pozice v cizí měně proti ručně spočtené hodnotě."""

    def test_price_change_and_fx_part(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 100000, 1000)
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie EUR {fund.id}", "currency_id": self.eur.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, fund))
        first = self.valuation(fund, date(2027, 1, 31))
        second = self.valuation(fund, date(2027, 2, 28))
        second.sudo().previous_id = first
        Line = self.env["investra.valuation.portfolio"].sudo()
        common = {"kind": "equity", "instrument_id": instrument.id, "name": instrument.name, "currency_id": self.eur.id}
        # 10 ks po 100 EUR při kurzu 25; po měsíci 110 EUR při kurzu 26
        Line.create({**common, "valuation_id": first.id, "quantity": 10, "fair_value_currency": 1000, "fx_rate": 25, "fair_value": 25000})
        line = Line.create({**common, "valuation_id": second.id, "quantity": 10, "fair_value_currency": 1100, "fx_rate": 26, "fair_value": 28600})
        self.assertEqual(line.prev_line_id.valuation_id, first)
        self.assertAlmostEqual(line.price_change, 10 * (110 * 26 - 100 * 25), places=2)  # 3 600
        self.assertAlmostEqual(line.fx_change, 10 * 100 * (26 - 25), places=2)  # 1 000
        # řádek bez minulého řádku a řádek bez kusů: nuly
        orphan = Line.create({**common, "valuation_id": first.id, "name": "Jiný", "instrument_id": False, "quantity": 0,
                              "fair_value_currency": 0, "fx_rate": 1, "fair_value": 0})
        self.assertEqual((orphan.price_change, orphan.fx_change), (0, 0))
