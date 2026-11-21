import io
from datetime import date

import openpyxl

from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestZj25Package(NavCase):
    """ZJ-25 G7: list Předvaha po třídách a list Rozpad tříd v souboru pro depozitáře."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        self.subscribe(self.cls(self.fund, "B"), "2027-01-01", 3000, 30)
        self.common_result(self.fund, "c1", "2027-01-20", 400)
        self.specific(self.fund, self.cls(self.fund, "A"), "s1", "2027-01-21", 50)

    def build(self):
        valuation = self.run_to_posted(self.valuation(self.fund, date(2027, 1, 31)))
        attachment = valuation.with_user(self.preparer).action_build_package()
        return valuation, openpyxl.load_workbook(io.BytesIO(attachment.raw))

    def test_trial_balance_has_column_per_class_and_zero_total(self):
        _valuation, book = self.build()
        rows = list(book["Předvaha"].iter_rows(min_row=3, values_only=True))
        header, body = rows[0], rows[1:]
        self.assertIn("Pohyb: A", header)
        self.assertIn("Pohyb: B", header)
        self.assertIn("Pohyb: Společné", header)
        total = body[-1]
        self.assertEqual(total[0], "Celkem")
        # Podvojná kniha: zůstatek k začátku, pohyb celkem a zůstatek k datu dávají 0; sloupce Společné + třídy se vyruší.
        for value in (total[2], total[-2], total[-1], sum(total[3:-2])):
            self.assertAlmostEqual(value, 0, places=2)

    def test_split_sheet_exists_and_difference_is_zero(self):
        valuation, book = self.build()
        self.assertIn("Rozpad tříd", book.sheetnames)
        rows = list(book["Rozpad tříd"].iter_rows(min_row=3, values_only=True))
        self.assertEqual(rows[0][:3], ("Účet", "Název", "Společné – fond"))
        self.assertIn("Vliv A", rows[0])
        difference = [r for r in rows if r[0] == "Rozdíl"][0]
        self.assertTrue(all(abs(v) < 0.01 for v in difference[2:] if isinstance(v, (int, float))))
        check = [r for r in rows if r[0] and str(r[0]).startswith("Kontrola")][0]
        values = [v for v in check[2:] if isinstance(v, (int, float))]
        expected = sorted(round(l.shared_result + l.delta, 2) for l in valuation.class_line_ids)
        self.assertEqual(sorted(round(v, 2) for v in values), expected)
