import re
from datetime import date
from pathlib import Path

from odoo.tests import tagged

from ..models.check_catalog import CHECK_AREAS, CHECK_CATALOG
from .common import NavCase

ADDONS = Path(__file__).resolve().parents[2]


@tagged("post_install", "-at_install")
class TestZj25Checks(NavCase):
    """ZJ-25 G8: katalog kontrol, strukturovaný výsledek a položky."""

    def valuation_for(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        return fund, valuation

    def test_catalog_covers_every_code_in_source(self):
        codes = set()
        for module in ("investra_nav", "investra_derivative"):
            for path in (ADDONS / module / "models").glob("*.py"):
                codes |= set(re.findall(r'self\._check\(\s*"([a-z_]+)"', path.read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(codes), 44)
        self.assertFalse(codes - set(CHECK_CATALOG), codes - set(CHECK_CATALOG))
        areas = {key for key, _label in CHECK_AREAS}
        for code, (area, what, how) in CHECK_CATALOG.items():
            self.assertIn(area, areas, code)
            self.assertTrue(what and how, code)

    def test_structured_result_of_sample_checks(self):
        _fund, valuation = self.valuation_for()
        classes_sum = valuation.check_ids.filtered(lambda c: c.code == "classes_sum")
        self.assertEqual(classes_sum.status, "ok")
        self.assertTrue(classes_sum.expected and classes_sum.actual)
        self.assertEqual(classes_sum.expected, classes_sum.actual)
        self.assertEqual(classes_sum.area, "capital")
        self.assertTrue(classes_sum.what and classes_sum.how)
        opening = valuation.check_ids.filtered(lambda c: c.code == "bridge_opening")
        self.assertTrue(opening.expected and opening.difference)
        self.assertTrue(valuation.check_ids.filtered(lambda c: c.code == "class_split"))

    def test_items_open_record_and_are_stored_only_for_failed_check(self):
        fund, valuation = self.valuation_for()
        valuation._check("test_fail", "Zkouška", False, "detail", items=[{"record": fund, "values": "očekáváno 1, skutečnost 2"}],
                         expected=1, actual=2.5, difference=1.5)
        valuation._check("test_ok", "Zkouška ok", True, items=[{"record": fund}])
        failed = valuation.check_ids.filtered(lambda c: c.code == "test_fail")
        self.assertEqual(failed.item_count, 1)
        self.assertEqual((failed.expected, failed.actual), ("1", valuation._check_format(2.5)))
        action = failed.item_ids.action_open()
        self.assertEqual((action["res_model"], action["res_id"]), ("investra.fund", fund.id))
        self.assertFalse(valuation.check_ids.filtered(lambda c: c.code == "test_ok").item_ids)

    def test_old_check_without_new_fields_shows_detail_and_status_order(self):
        _fund, valuation = self.valuation_for()
        valuation._check("legacy_code", "Stará kontrola", False, "podrobnosti", severity="warning")
        valuation._check("legacy_stop", "Stará kontrola stop", False, "podrobnosti")
        legacy = valuation.check_ids.filtered(lambda c: c.code == "legacy_code")
        self.assertEqual((legacy.what, legacy.detail, legacy.area), ("Stará kontrola", "podrobnosti", False))
        order = [c.status for c in self.env["investra.valuation.check"].search([("valuation_id", "=", valuation.id)])]
        self.assertEqual(order, sorted(order, key=lambda s: {"stop": 0, "warning": 1, "ok": 2}[s]))
