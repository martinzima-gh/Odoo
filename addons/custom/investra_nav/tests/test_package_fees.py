"""ZJ-12 krok 6 (E) a ZJ-11 krok 3: list Úplaty balíčku pro depozitáře – základ, opravy a odkazy ze snímku v detailu řádku."""

import io
import json
from datetime import date

import openpyxl

from odoo.tests import Form, tagged

from .common import NavCase

JANUARY, FEBRUARY = date(2027, 1, 31), date(2027, 2, 28)


@tagged("post_install", "-at_install")
class TestPackageFees(NavCase):
    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000000, 1000)
        self.Rule = self.env["investra.fee.rule"]

    def periodic(self, step="1"):
        return self.Rule.create({"fund_id": self.fund.id, "name": "Obhospodařování", "kind": "periodic", "base_step": step,
                                 "base_source": "fk", "expense_role": "expense_management", "statute_ref": "čl. 7",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.012})]})

    def performance(self):
        return self.Rule.create({
            "fund_id": self.fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "none", "base_step": "2",
            "class_ids": [(6, 0, self.cls(self.fund, "A").ids)], "expense_role": "expense_performance",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "initial_reference": 0})]})

    def correct(self, line, **values):
        action = line.action_correct()
        view = self.env["ir.ui.view"].browse(action["views"][0][0])
        form = Form(self.env["investra.valuation.external"].with_user(self.preparer).with_context(**action["context"]), view=view)
        for name, value in values.items():
            setattr(form, name, value)
        return form.save()

    def sheet(self, valuation):
        attachment = valuation.with_user(self.preparer).action_build_package()
        book = openpyxl.load_workbook(io.BytesIO(attachment.raw))
        rows = list(book["Úplaty"].iter_rows(min_row=3, values_only=True))
        return rows[0], rows[1:]

    def test_without_correction_base_columns_only(self):
        rule = self.periodic()
        valuation = self.valuation(self.fund, JANUARY)
        valuation.action_compute()
        rows, has_fix = valuation._package_rows_fees()
        self.assertFalse(has_fix)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        detail = json.loads(line.detail)
        row = rows[0]
        self.assertEqual((row["step"], row["statute"]), ("po kroku 1", "čl. 7"))
        self.assertAlmostEqual(row["base"], float(detail["base"]), places=2)
        self.run_to_posted(valuation)
        amount = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule).amount
        # Snímek, ne pravidlo: změna volby Základ po zaúčtování se v listu neprojeví.
        rule.base_step = "2"
        header, data = self.sheet(valuation)
        self.assertEqual(header, ("Pravidlo", "Třída", "Základ", "Částka základu", "Částka", "Článek statutu"))
        self.assertEqual(data[0][2], "po kroku 1")
        self.assertAlmostEqual(data[0][4], amount, places=2)

    def test_correction_columns_from_snapshot(self):
        rule = self.periodic()
        valuation = self.valuation(self.fund, JANUARY)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.correct(line, amount=-100, note="Faktura správce")
        valuation.action_compute()
        computed = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule).amount
        rows, has_fix = valuation._package_rows_fees()
        self.assertTrue(has_fix)
        rule_row = next(r for r in rows if r["statute"])
        fix_row = next(r for r in rows if r["note"] == "Faktura správce")
        self.assertAlmostEqual(rule_row["computed"], computed, places=2)
        self.assertAlmostEqual(rule_row["correction"], -100, places=2)
        self.assertAlmostEqual(rule_row["result"], computed - 100, places=2)
        self.assertAlmostEqual(fix_row["correction"], -100, places=2)
        self.assertIsNone(fix_row["base"])
        self.run_to_posted(valuation)
        header, data = self.sheet(valuation)
        self.assertEqual(header[6:], ("Vypočteno", "Oprava", "Výsledek", "Zdůvodnění", "Převzato z / Ukončuje opravu"))
        self.assertIn("Faktura správce", [r[9] for r in data])

    def test_legacy_detail_keys_converted(self):
        step = self.env["investra.valuation"]._fee_detail_step
        self.assertEqual(step({"base": "1000", "base_mode": "before"}), "1")
        self.assertEqual(step({"base": "1000", "base_mode": "after"}), "2")
        self.assertEqual(step({"gross": "1000", "perf_base": "after_tax"}), "4")
        self.assertEqual(step({"base": "1000"}), "")  # bez klíče se z dnešního pravidla nedoplňuje
        self.assertEqual(step({"base_step": "3"}), "3")
        base = self.env["investra.valuation"]._fee_detail_base
        self.assertEqual(base({"average": "12.5"}), 12.5)
        self.assertIsNone(base({"base": {"scope": "fund"}}))

    def test_carried_and_ending_links(self):
        perf = self.performance()
        self.common_result(self.fund, "v1", "2027-01-20", 100000)
        january = self.valuation(self.fund, JANUARY)
        january.action_compute()
        line = january.fee_line_ids.filtered(lambda l: l.rule_id == perf)
        entry = self.correct(line, amount=-1000, note="Dohoda")
        self.run_to_posted(january)
        february = self.valuation(self.fund, FEBRUARY)
        february.action_compute()
        rows, has_fix = february._package_rows_fees()
        self.assertTrue(has_fix)
        rule_row = next(r for r in rows if r["name"] == february.fee_line_ids.filtered(lambda l: l.rule_id == perf).name)
        self.assertIn("převzato z 2027-01-31 v1: Odměna", rule_row["link"])
        self.assertAlmostEqual(rule_row["correction"], -1000, places=2)
        february.with_user(self.preparer).end_correction(entry, "Dohoda skončila")
        february.action_compute()
        rows, _has_fix = february._package_rows_fees()
        end_row = next(r for r in rows if r["note"] == "Dohoda skončila")
        self.assertIn("ukončuje 2027-01-31 v1: Odměna", end_row["link"])
        self.assertAlmostEqual(end_row["correction"], 1000, places=2)
