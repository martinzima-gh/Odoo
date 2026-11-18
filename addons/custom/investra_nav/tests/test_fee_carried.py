"""ZJ-12 krok 4a: opravy výkonnostní odměny a daně – převzaté opravy, platnost, ukončení, naběhlá odměna (B.7)."""

import json
from datetime import date

from odoo.exceptions import UserError, ValidationError
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

    # --- oprava základu (4b) ------------------------------------------------------------------------------------------

    def correct_base(self, valuation, rule, amount, code=None, validity="period"):
        cls = self.cls(valuation.fund_id, code) if code else self.env["investra.fund.class"]
        return self.manual_fee(valuation, amount, note="Ruční úprava základu", account_id=False,
                               corrects_rule_id=rule.id, class_id=cls.id, correction_target="base", validity=validity)

    def periodic(self, fund, source="fk", rate=0.012):
        return self.Rule.create({"fund_id": fund.id, "name": "Obhospodařování", "kind": "periodic", "base_step": "1",
                                 "base_source": source, "expense_role": "expense_management",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})]})

    def test_tax_base_correction_carried_to_year_end(self):
        # Připočitatelná položka +10 000: základ 110 000, daň 5 500; řádek opravy nic neúčtuje. Únor převezme (doplatek 0),
        # leden 2028 už ne (nový rok, výsledek 0 → daň 0).
        fund = self.fund()
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct_base(january, tax, 10000)
        self.run_to_posted(january)
        line, detail = self.rule_line(january, tax)
        self.assertAlmostEqual(line.amount, 5500, places=2)
        self.assertAlmostEqual(float(detail["base"]), 110000, places=2)
        correction = january.fee_line_ids.filtered(lambda l: l.external_id == entry)
        self.assertEqual((correction.amount, json.loads(correction.detail)["target"]), (0, "base"))
        february = self.run_to_posted(self.valuation(fund, FEBRUARY))
        line, detail = self.rule_line(february, tax)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertEqual(detail["base_correction_ids"], entry.ids)
        next_year = self.valuation(fund, date(2028, 1, 31))
        next_year.action_compute()
        line, detail = self.rule_line(next_year, tax)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertNotIn("base_correction", detail)

    def test_average_base_correction_adjusts_average_to_year_end(self):
        # Oprava průměru +1 000 000: lednový průměr o 1 000 000 vyšší; únor ji převezme. Rozdíl únorového průměru proti
        # fondu bez opravy = rozdíl lednového FK (vyšší úplata) + 1 000 000.
        averages, capitals = {}, {}
        for corrected in (False, True):
            fund = self.fund()
            rule = self.periodic(fund, "average_fk")
            january = self.valuation(fund, JANUARY)
            if corrected:
                self.correct_base(january, rule, 1000000)
            self.run_to_posted(january)
            capitals[corrected] = january.fund_capital
            february = self.valuation(fund, FEBRUARY)
            february.action_compute()
            line, detail = self.rule_line(february, rule)
            averages[corrected] = float(detail["average"])
            if corrected:
                self.assertAlmostEqual(float(detail["base_correction"]), 1000000, places=2)
        self.assertAlmostEqual(averages[True] - averages[False], capitals[True] - capitals[False] + 1000000, places=2)

    def test_point_in_time_base_correction_only_this_valuation(self):
        # Úplata z FK: oprava základu +1 000 000 jen v lednu; únor ji nepřevezme a upozorní.
        fund = self.fund()
        rule = self.periodic(fund)
        january = self.valuation(fund, JANUARY)
        self.correct_base(january, rule, 1000000)
        self.run_to_posted(january)
        line, detail = self.rule_line(january, rule)
        self.assertAlmostEqual(float(detail["base"]), 2000000, places=2)
        self.assertEqual(january.check_ids.filtered(lambda c: c.code == "base_correction_ended").status, "ok")
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.rule_line(february, rule)
        self.assertNotIn("base_correction", detail)
        self.assertLess(float(detail["base"]), 1100000)
        check = february.check_ids.filtered(lambda c: c.code == "base_correction_ended")
        self.assertEqual(check.status, "warning")
        self.assertIn("Obhospodařování", check.detail)

    def test_performance_base_correction_carried_until_crystallisation(self):
        # Odměna po kroku 2: výsledek 100 000, oprava základu −50 000 → odměna 10 000; únor převezme (doplatek 0).
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        self.correct_base(january, perf, -50000, "A")
        self.run_to_posted(january)
        self.assertAlmostEqual(self.total(january, perf), 10000, places=2)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.rule_line(february, perf)
        self.assertAlmostEqual(line.amount, 0, places=2)
        self.assertAlmostEqual(float(detail["base_correction"]), -50000, places=2)
        self.consistent(february)

    def test_base_correction_needs_base(self):
        fund = self.fund()
        rule = self.periodic(fund, "none")
        with self.assertRaises(ValidationError):
            self.correct_base(self.valuation(fund, JANUARY), rule, 100)

    # --- kontroly a Ponechat rozdíl / výsledek (4c) ----------------------------------------------------------------

    def check(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code)

    def changed_correction(self):
        # Úplata z FK 1,2 % p. a., oprava −100 bez tlačítka: snímek se pořídí při prvním výpočtu. Pak výnos 1 000 000
        # (vyšší FK) → vypočteno se změní a ocenění se zastaví.
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.valuation(fund, JANUARY)
        entry = self.correct(valuation, rule, -100)
        valuation.action_compute()
        before = entry.computed_at_entry
        self.assertTrue(entry.computed_captured)
        self.assertAlmostEqual(before, 0.012 * 31 / 365 * 1000000, places=1)
        self.assertEqual(self.check(valuation, "correction_changed").status, "ok")
        self.common_result(fund, "v1", "2027-01-20", 1000000)
        valuation.action_compute()
        check = self.check(valuation, "correction_changed")
        self.assertEqual(check.status, "stop")
        self.assertIn(f"při opravě {before:.2f}", check.detail)
        return valuation, rule, entry, before

    def test_changed_computation_stops_and_keep_difference(self):
        valuation, rule, entry, before = self.changed_correction()
        now = entry.computed_now
        self.assertGreater(now, before)
        with self.assertRaises(UserError):
            valuation.action_submit()
        entry.with_user(self.preparer).action_keep_difference()
        self.assertEqual((entry.amount, entry.computed_at_entry), (-100, now))
        self.assertEqual(self.check(valuation, "correction_changed").status, "ok")
        self.assertAlmostEqual(self.total(valuation, rule), now - 100, places=2)

    def test_keep_result(self):
        valuation, rule, entry, before = self.changed_correction()
        now = entry.computed_now
        entry.with_user(self.preparer).action_keep_result()
        self.assertAlmostEqual(entry.amount, round(before - 100 - now, 2), places=2)
        self.assertEqual(self.check(valuation, "correction_changed").status, "ok")
        self.assertAlmostEqual(self.total(valuation, rule), before - 100, places=2)

    def test_correction_of_archived_or_changed_rule_stops(self):
        fund = self.fund(classes=("A", "B"))
        rule = self.periodic(fund)
        valuation = self.valuation(fund, JANUARY)
        self.correct(valuation, rule, -100)
        rule.class_ids = [(6, 0, self.cls(fund, "A").ids)]
        with self.assertRaisesRegex(UserError, "neodpovídá pravidlu"):
            valuation.action_compute()
        rule.class_ids = [(5, 0, 0)]
        rule.active = False
        with self.assertRaisesRegex(UserError, "archivované"):
            valuation.action_compute()

    def test_warnings_carried_and_once_ended(self):
        # Leden: oprava odměny do konce období a oprava daně jen pro toto ocenění. Únor: „převzaté opravy (1)“ a
        # „oprava jen toto ocenění skončila“; únor opravu ukončí, březen už nic nepřebírá.
        fund = self.fund()
        perf = self.performance(fund)
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct(january, perf, -1000, "A")
        self.correct(january, tax, -50, validity="valuation")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        carried = self.check(february, "carried_corrections")
        self.assertEqual((carried.status, carried.name), ("warning", "Obsahuje převzaté opravy (1)"))
        once = self.check(february, "correction_once_ended")
        self.assertEqual(once.status, "warning")
        self.assertIn("Daň", once.detail)
        february.with_user(self.preparer).end_correction(entry, "Konec opravy")
        february.action_compute()
        self.assertEqual(self.check(february, "carried_corrections").status, "ok")
        self.run_to_posted(february)
        march = self.valuation(fund, MARCH)
        march.action_compute()
        self.assertEqual(self.check(march, "carried_corrections").status, "ok")
        self.assertEqual(self.check(march, "correction_once_ended").status, "ok")

    # --- stopa a převzetí z verze (4d) -----------------------------------------------------------------------------

    def test_trail_lists_corrections(self):
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        valuation = self.valuation(fund, JANUARY)
        self.correct(valuation, perf, -1000, "A")
        valuation.action_compute()
        valuation.action_submit()
        notes = {step.step: step.note or "" for step in valuation.step_ids}
        for step in ("computed", "submitted"):
            self.assertIn("Opravy: Odměna A: vypočteno 20000.00 → 19000.00 (oprava -1000.00)", notes[step])
            self.assertIn("Dohoda s depozitářem", notes[step])
            self.assertIn(f"zadal {self.preparer.name}", notes[step])

    def test_copy_from_returned_version(self):
        # Verze 1: oprava odměny a ruční úplata s přílohou; vrácení → verze 2 upozorní na 2 chybějící řádky. Převzetí
        # zkopíruje oba (origin_id, nová příloha patřící verzi 2), opakované převzetí nic nepřidá.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        first = self.valuation(fund, JANUARY)
        correction = self.correct(first, perf, -1000, "A")
        attachment = self.env["ir.attachment"].create({"name": "faktura.pdf", "raw": b"%PDF",
                                                       "res_model": "investra.valuation", "res_id": first.id})
        manual = self.manual_fee(first, 300, attachment_id=attachment.id)
        first.action_compute()
        first.action_submit()
        second = first.with_user(self.approver).action_return("Chybná faktura")
        second.action_compute()
        check = self.check(second, "version_entries_missing")
        self.assertEqual((check.status, check.name),
                         ("warning", "Předchozí verze měla ruční úpravy (2), které v této verzi nejsou"))
        self.assertEqual(second.with_user(self.preparer).action_copy_from_version(), 2)
        copies = second.external_fee_ids
        self.assertEqual(copies.mapped("origin_id"), correction | manual)
        copy = copies.filtered(lambda l: l.origin_id == manual)
        self.assertNotEqual(copy.attachment_id, attachment)
        self.assertEqual((copy.attachment_id.res_id, copy.attachment_id.raw.content), (second.id, b"%PDF"))
        self.assertFalse(copies.mapped("ended_id"))
        self.assertEqual(second.with_user(self.preparer).action_copy_from_version(), 0)
        second.action_compute()
        self.assertEqual(self.check(second, "version_entries_missing").status, "ok")
        # Ruční úplata 300 je krok 2, odměna po kroku 2 ji zahrnuje: 0,2 × (100 000 − 300) − 1 000 = 18 940.
        self.assertAlmostEqual(self.total(second, perf), 18940, places=2)

    def test_copy_ending_from_returned_version(self):
        # Ukončení zadané ve vrácené verzi února se do verze 2 převezme (ukončení ve vrácené verzi se nepočítá).
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        entry = self.correct(january, perf, -1000, "A")
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        february.with_user(self.preparer).end_correction(entry, "Konec")
        february.action_compute()
        february.action_submit()
        second = february.with_user(self.approver).action_return("Oprava")
        self.assertEqual(second.with_user(self.preparer).action_copy_from_version(), 1)
        ending = second.external_fee_ids
        self.assertEqual((ending.ended_id, ending.origin_id.valuation_id), (entry, february))
        second.action_compute()
        self.assertAlmostEqual(self.accrued(second), 20000, places=2)
        self.assertIn("ukončuje opravu", second._corrections_summary())
        self.assertIn("převzato z verze 1", second._corrections_summary())

    # --- pojistka archivace (4e) -----------------------------------------------------------------------------------

    def payable(self, fund, role):
        account = self.expense_account(fund, role)
        lines = self.env["account.move.line"].sudo().search([("account_id", "=", account.id),
                                                             ("company_id", "=", fund.company_id.id)])
        return -sum(lines.mapped("balance"))

    def test_archive_stops_with_accrued_performance_fee_until_zero_rate(self):
        # Naběhlá odměna 20 000: archivace se zastaví. Postup: verze sazby 0 % od 1. 2., únor odměnu rozpustí (−20 000),
        # pak archivace projde.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        self.run_to_posted(self.valuation(fund, JANUARY))
        with self.assertRaisesRegex(UserError, "verzi sazby 0 %"):
            perf.action_archive()
        perf.write({"version_ids": [(0, 0, {"valid_from": "2027-02-01", "rate": 0, "initial_reference": 0})]})
        february = self.run_to_posted(self.valuation(fund, FEBRUARY))
        self.assertAlmostEqual(self.total(february, perf), -20000, places=2)
        self.assertAlmostEqual(self.accrued(february), 0, places=2)
        perf.action_archive()
        self.assertFalse(perf.active)

    def test_archived_rule_no_longer_releases_accrual(self):
        # Důvod pojistky: pravidlo archivované obejitím (přímo v databázi) se v dalším ocenění nepočítá, naběhlá odměna
        # 20 000 zůstane v závazku i v kapitálu třídy.
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        self.run_to_posted(self.valuation(fund, JANUARY))
        self.env.cr.execute("UPDATE investra_fee_rule SET active = false WHERE id = %s", [perf.id])
        perf.invalidate_recordset(["active"])
        february = self.run_to_posted(self.valuation(fund, FEBRUARY))
        self.assertFalse(february.fee_line_ids.filtered(lambda l: l.rule_id == perf))
        self.assertAlmostEqual(self.payable(fund, "performance_payable"), 20000, places=2)

    def test_archive_stops_with_booked_tax(self):
        fund = self.fund()
        tax = self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        self.run_to_posted(self.valuation(fund, JANUARY))
        with self.assertRaisesRegex(UserError, "zaúčtovanou daň"):
            tax.action_archive()

    def test_archive_rule_without_amount(self):
        # Omylem založené pravidlo (ocenění bez zisku: daň 0) archivovat jde.
        fund = self.fund()
        tax = self.tax(fund)
        self.run_to_posted(self.valuation(fund, JANUARY))
        tax.action_archive()
        self.assertFalse(tax.active)
