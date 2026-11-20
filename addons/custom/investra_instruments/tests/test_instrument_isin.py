from odoo.tests import TransactionCase, tagged

from .common import with_ids


@tagged("post_install", "-at_install")
class TestInstrumentIsinSearch(TransactionCase):
    """AG-024: nástroj se zobrazuje jako „ISIN název“ a hledá se podle ISIN i názvu."""

    def setUp(self):
        super().setUp()
        self.czk = self.env.ref("base.CZK")
        self.instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Testovací akcie ISIN", "currency_id": self.czk.id, "isin": "CZ0009999991",
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }))

    def test_display_name_starts_with_isin(self):
        self.assertEqual(self.instrument.display_name, "CZ0009999991 Testovací akcie ISIN")

    def test_search_by_isin_and_by_name(self):
        Instrument = self.env["investra.instrument"]
        self.assertIn(self.instrument.id, [found_id for found_id, _name in Instrument.name_search("cz00099999")])
        found = Instrument._search_display_name("ilike", "CZ00099999")
        self.assertIn(self.instrument, Instrument.search(found))
        found = Instrument._search_display_name("ilike", "Testovací akcie")
        self.assertIn(self.instrument, Instrument.search(found))
