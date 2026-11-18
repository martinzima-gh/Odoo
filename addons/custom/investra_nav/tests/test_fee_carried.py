"""ZJ-12 krok 4a: opravy výkonnostní odměny a daně – převzaté opravy, platnost, ukončení, naběhlá odměna (B.7)."""

import json
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NavCase

JANUARY, FEBRUARY, MARCH, APRIL = date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31), date(2027, 4, 30)


@tagged("post_install", "-at_install")
class TestCarriedCorrections(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, classes=("A",)):
        fund = self.make_fund(classes=[{"code": c} for c in classes])
        for code in classes:
            self.subscribe(self.cls(fund, code), "2027-01-01", 1000000, 1000)
        return fund

    def performance(self, fund, code="A", step="2", crystallisation="none"):
        return self.Rule.create({
            "fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": crystallisation,
            "base_step": step, "class_ids": [(6, 0, self.cls(fund, code).ids)], "expense_role": "expense_performance",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "initial_reference": 0})]})

    def tax(self, fund, step="3"):
        return self.Rule.create({"fund_id": fund.id, "name": "Daň", "kind": "tax", "base_step": step,
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.05})]})

    def correct(self, valuation, rule, amount, code=None, validity="period"):
        cls = self.cls(valuation.fund_id, code) if code else self.env["investra.fund.class"]
        return self.manual_fee(valuation, amount, note="Dohoda s depozitářem", account_id=False,
                               corrects_rule_id=rule.id, class_id=cls.id, validity=validity)

    def total(self, valuation, rule):
        """Rozpis pravidla včetně jeho oprav (řádky oprav nemají pravidlo, jen odkaz na řádek opravy)."""
        lines = valuation.fee_line_ids.filtered(
            lambda l: l.rule_id == rule or l.external_id.corrects_rule_id == rule)
        return sum(lines.mapped("amount"))

    def rule_line(self, valuation, rule):
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        return line, json.loads(line.detail or "{}")

    def accrued(self, valuation, code="A"):
        return self.result(valuation, code).perf_accrued

    def consistent(self, valuation):
        check = valuation.check_ids.filtered(lambda c: c.code == "fee_consistency")
        self.assertEqual(check.status, "ok", check.detail)

    # --- výkonnostní odměna -------------------------------------------------------------------------------------------

    def test_performance_correction_for_period_is_carried(self):
        # Leden +100 000: vypočteno 20 000, oprava −1 000 do konce období → naběhlá 19 000. Únor beze změny: vypočteno
        # 20 000 − 19 000 = +1 000, převzato −1 000 → řádek pravidla 0, naběhlá zůstává 19 000.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct(january, perf, -1000, "A")
        self.run_to_posted(january)
        self.assertAlmostEqual(self.total(january, perf), 19000, places=2)
        self.assertAlmostEqual(self.accrued(january), 19000, places=2)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.rule_line(february, perf)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertAlmostEqual(float(detail["computed"]), 1000, places=2)
        self.assertAlmostEqual(float(detail["carried"]), -1000, places=2)
        self.assertEqual(detail["carried_ids"], entry.ids)
        self.assertAlmostEqual(self.accrued(february), 19000, places=2)
        self.assertAlmostEqual(self.result(february, "A").capital, 1081000, places=2)
        self.consistent(february)

    def test_performance_correction_for_valuation_only_reverses(self):
        # Oprava „jen toto ocenění“: únor se vrátí na vypočtený stav (+1 000), naběhlá 20 000, nic se nepřebírá.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, perf, -1000, "A", validity="valuation")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.rule_line(february, perf)
        self.assertAlmostEqual(line.amount, 1000, places=2)
        self.assertNotIn("carried", detail)
        self.assertAlmostEqual(self.accrued(february), 20000, places=2)

    def test_crystallisation_pays_correction_and_ends_carrying(self):
        # Čtvrtletní krystalizace: oprava −1 000 z ledna je v naběhlé odměně 31. 3. (splatná 19 000); duben už nic
        # nepřebírá (období odměny začíná 31. 3.).
        fund = self.fund()
        perf = self.performance(fund, crystallisation="quarter")
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, perf, -1000, "A")
        self.run_to_posted(january)
        self.run_to_posted(self.valuation(fund, FEBRUARY))
        march = self.run_to_posted(self.valuation(fund, MARCH))
        self.assertAlmostEqual(self.total(march, perf), 0, places=2)
        self.assertEqual(self.result(march, "A").perf_base_date, MARCH)
        self.assertAlmostEqual(self.accrued(march), 0, places=2)
        payable = self.env["investra.account.role"].sudo().account_for(fund.company_id, "performance_payable")
        lines = self.env["account.move.line"].sudo().search([("account_id", "=", payable.id),
                                                             ("company_id", "=", fund.company_id.id)])
        self.assertAlmostEqual(-sum(lines.mapped("balance")), 19000, places=2)
        april = self.valuation(fund, APRIL)
        april.action_compute()
        line, detail = self.rule_line(april, perf)
        self.assertNotIn("carried", detail)
        self.assertAlmostEqual(line.amount, 0, places=2)

    def test_ending_carried_correction(self):
        # Únor ukončí lednovou opravu: řádek pravidla 0 (vypočteno +1 000, převzato −1 000), ukončení +1 000 → naběhlá
        # 20 000. Březen: převzato −1 000 + 1 000 = 0, odměna beze změny.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct(january, perf, -1000, "A")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        ending = february.with_user(self.preparer).end_correction(entry, "Depozitář opravu zrušil")
        self.assertEqual((ending.amount, ending.ended_id, ending.origin_id), (1000, entry, ending.origin_id.browse()))
        self.run_to_posted(february)
        self.assertAlmostEqual(self.total(february, perf), 1000, places=2)
        self.assertAlmostEqual(self.accrued(february), 20000, places=2)
        march = self.valuation(fund, MARCH)
        march.action_compute()
        line, detail = self.rule_line(march, perf)
        self.assertAlmostEqual(float(detail["carried"]), 0, places=2)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertAlmostEqual(self.accrued(march), 20000, places=2)

    def test_ending_rules(self):
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct(january, perf, -1000, "A")
        once = self.correct(january, perf, -500, "A", validity="valuation")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.manual_fee(february, 999, account_id=False, corrects_rule_id=perf.id, class_id=self.cls(fund, "A").id,
                            ended_id=entry.id)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            february.with_user(self.preparer).end_correction(once, "Jen toto ocenění se neukončuje")
        february.with_user(self.preparer).end_correction(entry, "Konec")
        with self.assertRaises(ValidationError), self.cr.savepoint():
            february.with_user(self.preparer).end_correction(entry, "Podruhé")

    # --- daň ------------------------------------------------------------------------------------------------------------

    def test_tax_correction_carried_to_year_end(self):
        # Daň 5 % z 100 000 = 5 000, oprava −200 do konce období (doklad na daňových účtech) → zaúčtováno 4 800.
        # Únor beze změny: vypočteno 5 000 − 4 800 = +200, převzato −200 → doplatek 0.
        fund = self.fund()
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, tax, -200)
        self.run_to_posted(january)
        self.assertAlmostEqual(self.total(january, tax), 4800, places=2)
        tax_account = self.expense_account(fund, "expense_tax")
        lines = self.env["account.move.line"].sudo().search([("account_id", "=", tax_account.id),
                                                             ("company_id", "=", fund.company_id.id)])
        self.assertAlmostEqual(sum(lines.mapped("balance")), 4800, places=2)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.rule_line(february, tax)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertAlmostEqual(float(detail["carried"]), -200, places=2)
        self.consistent(february)

    def test_tax_correction_for_valuation_only_reverses(self):
        fund = self.fund()
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, tax, -200, validity="valuation")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        self.assertAlmostEqual(self.rule_line(february, tax)[0].amount, 200, places=2)

    def test_tax_correction_is_not_class_specific(self):
        # Dvě třídy: oprava daně se dělí poměrem a nemá daňový efekt; přesuny zůstávají nulové.
        fund = self.fund(classes=("A", "B"))
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, tax, -200)
        january.action_compute()
        self.assertEqual(self.rule_line(january, tax)[1]["transfers"], {})
        self.assertAlmostEqual(self.result(january, "A").capital, self.result(january, "B").capital, places=2)
        self.consistent(january)

    def test_performance_correction_is_class_specific_for_tax(self):
        # Odměna A vypočteno 10 000, oprava −1 000 → 9 000; daň 0,05 × (100 000 − 9 000) = 4 550; efekt 0,05 × 9 000
        # = 450, přesun A = 450 − 0,5 × 450 = +225.
        fund = self.fund(classes=("A", "B"))
        perf = self.performance(fund, "A", "1")
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct(january, perf, -1000, "A")
        january.action_compute()
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.assertAlmostEqual(self.total(january, perf), 9000, places=2)
        self.assertAlmostEqual(self.total(january, tax), 4550, places=2)
        self.assertEqual(self.rule_line(january, tax)[1]["transfers"], {str(a.id): "225.00", str(b.id): "-225.00"})
        self.consistent(january)
