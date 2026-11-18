"""ZJ-12 krok 3: společný dopočet úplat, výkonnostní odměny a daně (engine.solve_fees) a zaúčtování po ustálení."""

import json
from datetime import date

from odoo.tests import BaseCase, tagged

from . import ref_fee_adapter as adapter
from . import ref_fee_model as model
from .common import NavCase

YEAR_END = date(2027, 12, 31)
JANUARY = date(2027, 1, 31)


@tagged("post_install", "-at_install")
class TestSolveFeesEngine(BaseCase):
    """Čistá funkce dopočtu proti referenčnímu modelu (příloha A): stejné kombinace, opravy a rozdělení daně."""

    def test_all_combinations_match_reference_model(self):
        count = 0
        for base in model.base_scenarios():
            for s1 in range(4):
                for s2 in range(4):
                    for sp in (0, 1, 3):
                        for st in range(3):
                            sc = model.with_states(base, s1, s2, sp, st)
                            expected = model.solve(sc, model.amounts())["X"]
                            result = adapter.solve(sc)
                            label = f"{sc['Name']} [F1 S{s1}, F2 S{s2}, P S{sp}, daň S{st}]"
                            for key in model.KEYS:
                                self.assertAlmostEqual(float(result["amounts"][key]), expected[key], delta=1e-6, msg=label)
                            for c in sc["Classes"]:
                                self.assertAlmostEqual(
                                    float(adapter.class_value(sc, result, c["Code"])),
                                    model.class_value(sc, expected, c["Code"], True, True, True), delta=1e-6, msg=label)
                            self.assertLess(result["residual"], 1e-12, label)
                            self.assertLessEqual(result["steps"], 500)
                            count += 1
        self.assertEqual(count, 720)

    def test_corrections_match_reference_model(self):
        count = 0
        for base in (model.base_scenarios()[0], model.base_scenarios()[3]):
            for s1 in range(4):
                for s2 in range(4):
                    for sp in (0, 1, 3):
                        for st in range(3):
                            sc = model.with_states(base, s1, s2, sp, st)
                            plain = adapter.solve(sc)["amounts"]
                            for corr in ({"F1": -100.0}, {"F2": -50.0}, {"P": -30.0}, {"T": -20.0}):
                                key = next(iter(corr))
                                expected = model.solve_with_corrections(sc, corr)["X"]
                                if key == "T":
                                    amounts = adapter.solve(sc, pinned={"T": plain["T"] + adapter.D(corr[key])})["amounts"]
                                else:
                                    # Opravené pravidlo pevně na „Vypočteno“, oprava jako samostatná pevná položka.
                                    amounts = adapter.solve(sc, pinned={key: plain[key]}, corrections=corr)["amounts"]
                                for k in model.KEYS:
                                    total = amounts[k] + amounts.get(f"corr:{k}", 0)
                                    self.assertAlmostEqual(float(total), expected[k], delta=1e-6, msg=f"{key} {k}")
                                count += 1
        self.assertEqual(count, 1152)

    def test_does_not_converge_raises(self):
        # Úplata 150 % z FK po sobě samé (po kroku 2): x = 1,5 (V − x) diverguje při Jacobiho iteraci.
        items = [{"key": "F", "stage": 2, "payer": None, "base": {"scope": "fund", "step": 2},
                  "amount": lambda base: adapter.D("1.5") * base}]
        with self.assertRaisesRegex(ValueError, "neustálil"):
            adapter.engine.solve_fees({"A": {"value": 100, "ratio": 1}}, items, max_steps=50)


@tagged("post_install", "-at_install")
class TestFeeSolverValuation(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, classes=("A",), capital=1000000, units=1000):
        fund = self.make_fund(classes=[{"code": c} for c in classes])
        for code in classes:
            self.subscribe(self.cls(fund, code), "2027-01-01", capital, units)
        return fund

    def periodic(self, fund, rate, step="1", **vals):
        return self.Rule.create({"fund_id": fund.id, "name": vals.pop("name", "Úplata"), "kind": "periodic",
                                 "base_step": step, "expense_role": "expense_management", **vals,
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})]})

    def performance(self, fund, code, step="2", rate=0.2, **version):
        version = {"valid_from": "2020-01-01", "rate": rate, "initial_reference": 0, **version}
        return self.Rule.create({"fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "none",
                                 "base_step": step, "class_ids": [(6, 0, self.cls(fund, code).ids)],
                                 "expense_role": "expense_performance", "version_ids": [(0, 0, version)]})

    def tax(self, fund, step="3", rate=0.05):
        return self.Rule.create({"fund_id": fund.id, "name": "Daň", "kind": "tax", "base_step": step,
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})]})

    def amount(self, valuation, rule):
        return sum(valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule).mapped("amount"))

    def tax_detail(self, valuation, rule):
        return json.loads(valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule).detail)

    def assert_consistent(self, valuation):
        check = valuation.check_ids.filtered(lambda c: c.code == "fee_consistency")
        self.assertEqual(check.status, "ok", check.detail)

    # --- kombinace kroků -------------------------------------------------------------------------------------------

    def test_steps_match_reference_model(self):
        # Třída 1 000 / 10 kusů, výsledek 100; úplata fondu 1 % p. a. za 31 dní, odměna 20 % nad kurzem 100, daň 5 %.
        # Očekávané hodnoty z referenčního modelu (měřítko na kus s pevnými kusy = kapitál nad HWM 1 000).
        version = 0
        for fee_step in ("1", "2", "3", "4"):
            for perf_step in ("1", "2", "4"):
                for tax_step in ("1", "2", "3"):
                    with self.subTest(fee=fee_step, perf=perf_step, tax=tax_step):
                        fund = self.fund(capital=1000, units=10)
                        self.common_result(fund, "v1", "2027-01-20", 100)
                        fee = self.periodic(fund, 0.01, fee_step)
                        perf = self.performance(fund, "A", perf_step, perf_measure="unit", initial_reference=100)
                        tax = self.tax(fund, tax_step)
                        version += 1
                        valuation = self.valuation(fund, JANUARY)
                        valuation.action_compute()
                        sc = model.with_states(
                            model.scenario("Odoo", [{"Code": "A", "Pre": 1000.0}], 100.0, 1000.0, 0.01 * 31 / 365, 0, 0.2, 0.05),
                            int(fee_step) - 1, 0, {"1": 0, "2": 1, "4": 3}[perf_step], int(tax_step) - 1)
                        expected = model.solve(sc, model.amounts())["X"]
                        self.assertAlmostEqual(self.amount(valuation, fee), expected["F1"], delta=0.006)
                        self.assertAlmostEqual(self.amount(valuation, perf), expected["P"], delta=0.006)
                        self.assertAlmostEqual(self.amount(valuation, tax), expected["T"], delta=0.011)
                        self.assertEqual(len(valuation.event_ids.filtered(lambda e: ":tax:" in e.key)), 1)
                        self.assert_consistent(valuation)

    def test_c4_fee_after_tax_with_tax_after_fees(self):
        # C4: úplata 1 % po kroku 4, daň 5 % po kroku 2: S = f (N − t R) / (1 + f (1 − t)) = 10 846,95; daň 4 457,65.
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-30", 100000)
        fee = self.periodic(fund, 0.01, "4")
        tax = self.tax(fund, "2")
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        self.assertAlmostEqual(self.amount(valuation, fee), 10846.95, places=2)
        self.assertAlmostEqual(self.amount(valuation, tax), 4457.65, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 1100000 - 10846.95 - 4457.65, places=2)
        self.assert_consistent(valuation)

    def test_average_fk_after_fees(self):
        # Průměrný FK po kroku 2: dnešní bod je FK po úplatě, S = 0,0031 × (1 000 000 − S) = 3 090,42.
        fund = self.fund()
        rule = self.periodic(fund, 0.0365, "2", base_source="average_fk")
        valuation = self.valuation(fund, JANUARY)
        valuation.action_compute()
        self.assertAlmostEqual(self.amount(valuation, rule), 3090.42, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 1000000 - 3090.42, places=2)

    # --- odměna po kroku 1: přičtení úplat od krystalizace (B.3) ----------------------------------------------------

    def test_performance_before_fees_adds_back_fees_since_crystallisation(self):
        # Měsíční ocenění, krystalizace čtvrtletně, výsledek 10 000 měsíčně, úplata 1,2 % p. a. Odměna po kroku 1 =
        # 20 % z výsledku před všemi úplatami období: 2 000, 4 000, 6 000 naběhlé; po kroku 2 by byla nižší o úplaty.
        fund = self.fund()
        fee = self.periodic(fund, 0.012)
        perf = self.performance(fund, "A", "1")
        perf.crystallisation = "quarter"
        expected = {date(2027, 1, 31): 2000, date(2027, 2, 28): 4000, date(2027, 3, 31): 6000}
        for index, (day, accrued) in enumerate(expected.items()):
            self.common_result(fund, f"v{index}", day.isoformat(), 10000)
            valuation = self.run_to_posted(self.valuation(fund, day))
            detail = json.loads(valuation.fee_line_ids.filtered(lambda l: l.rule_id == perf).detail)
            self.assertAlmostEqual(float(detail["required"]), accrued, places=2, msg=str(day))
            earlier = self.env["investra.valuation"].search([("fund_id", "=", fund.id), ("date", "<", day)])
            self.assertAlmostEqual(float(detail["added_fees"]), sum(self.amount(v, fee) for v in earlier), places=2)
        # Krystalizace 31. 3.: další období začíná bez přičtených úplat.
        self.assertEqual(self.result(valuation, "A").perf_base_date, date(2027, 3, 31))

    def test_performance_per_unit_adds_fee_per_unit(self):
        # Měřítko na kus, úpis v polovině období: lednová úplata na kus (1 000 kusů) × dnešní kusy (2 000).
        fund = self.fund()
        fee = self.periodic(fund, 0.012)
        perf = self.performance(fund, "A", "1", perf_measure="unit", initial_reference=1000)
        self.common_result(fund, "v1", "2027-01-20", 10000)
        january = self.run_to_posted(self.valuation(fund, JANUARY))
        self.subscribe(self.cls(fund, "A"), "2027-02-10", 1010000, 1000)
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        detail = json.loads(february.fee_line_ids.filtered(lambda l: l.rule_id == perf).detail)
        self.assertAlmostEqual(float(detail["added_fees"]), self.amount(january, fee) / 1000 * 2000, places=2)

    # --- daňový efekt tříd (B.5) ---------------------------------------------------------------------------------

    def test_c5_tax_effect_of_class_performance(self):
        # C5: A, B po 1 000 000, výsledek 100 000, odměna A 20 % nad 1 000 000 po kroku 1, daň 5 % po kroku 3.
        # Odměna 10 000, daň 4 500; daňový efekt odměny 0,05 × (10 000 − 0,5 × 10 000) = 250 třídě A.
        fund = self.fund(classes=("A", "B"))
        self.common_result(fund, "v", "2027-01-20", 100000)
        perf = self.performance(fund, "A", "1")
        tax = self.tax(fund)
        valuation = self.valuation(fund, JANUARY)
        valuation.action_compute()
        self.assertAlmostEqual(self.amount(valuation, perf), 10000, places=2)
        self.assertAlmostEqual(self.amount(valuation, tax), 4500, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1038000, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1047500, places=2)
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.assertEqual(self.tax_detail(valuation, tax)["transfers"], {str(a.id): "250.00", str(b.id): "-250.00"})
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "clearing_zero").status, "ok")

    def test_c7_tax_effect_across_zero(self):
        # C7: výsledek 5 000, úplata A 1 % po kroku 1 (10 025), daň po kroku 2: fond ve ztrátě, daň 0;
        # efekt úplaty A je jen 5 000 × 0,05 = 250 → třída A +125, B −125.
        fund = self.fund(classes=("A", "B"))
        self.common_result(fund, "v", "2027-06-30", 5000)
        fee = self.periodic(fund, 0.01, "1", base_source="class_fk", class_ids=[(6, 0, self.cls(fund, "A").ids)])
        tax = self.tax(fund, "2")
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        self.assertAlmostEqual(self.amount(valuation, fee), 10025, places=2)
        self.assertAlmostEqual(self.amount(valuation, tax), 0, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1002500 - 10025 + 125, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1002500 - 125, places=2)

    def test_tax_effect_transfer_is_incremental(self):
        # Leden jako C5 (efekt A 500, přesun A +250). Únor ztráta 100 000: odměna se rozpustí, daň i efekt od 1. 1. jsou 0.
        # Přírůstkový přesun A = ΔE_A − ρ_A × ΔΣE = −500 + ρ_A × 500, ρ_A = 1 038 000 / 2 085 500 (po lednu) → −251,14.
        fund = self.fund(classes=("A", "B"))
        self.common_result(fund, "v1", "2027-01-20", 100000)
        perf = self.performance(fund, "A", "1")
        tax = self.tax(fund)
        january = self.run_to_posted(self.valuation(fund, JANUARY))
        self.common_result(fund, "v2", "2027-02-20", -100000)
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.assertAlmostEqual(self.amount(february, perf), -10000, places=2)
        self.assertAlmostEqual(self.amount(february, tax), -4500, places=2)
        self.assertEqual(self.tax_detail(january, tax)["transfers"], {str(a.id): "250.00", str(b.id): "-250.00"})
        effect = self.tax_detail(january, tax)["effect"]
        self.assertAlmostEqual(float(effect[str(a.id)]), 500, places=6)
        self.assertAlmostEqual(float(effect[str(b.id)]), 0, places=6)
        self.assertEqual(self.tax_detail(february, tax)["transfers"], {str(a.id): "-251.14", str(b.id): "251.14"})
        self.assert_consistent(february)

    def test_tax_effect_not_restated_by_later_subscription(self):
        # Leden jako C5 (efekt A 500, přesun A +250). Únor: úpis 8 000 000 do B, žádný výsledek.
        # Odměna po kroku 1: 1 038 000 + 10 000 → 9 600 (−400; lednová daň třídy A se podle B.3 nepřičítá). Daň 0,05 × 90 400
        # = 4 520 (+20). Efekt 480, ΔE_A = ΔΣE = −20, ρ_A = 1 038 000 / 10 085 500 → přesun A = −20 × (1 − ρ_A) = −17,94.
        # Lednový přesun se novým poměrem nepřepočítá; kumulativní výpočet by dal 0,05 × 9 600 × (1 − ρ_A) − 250 = +180,59.
        fund = self.fund(classes=("A", "B"))
        self.common_result(fund, "v1", "2027-01-20", 100000)
        perf = self.performance(fund, "A", "1")
        tax = self.tax(fund)
        self.run_to_posted(self.valuation(fund, JANUARY))
        self.subscribe(self.cls(fund, "B"), "2027-02-10", 8000000, 8000)
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.assertAlmostEqual(self.amount(february, perf), -400, places=2)
        self.assertAlmostEqual(self.amount(february, tax), 20, places=2)
        self.assertEqual(self.tax_detail(february, tax)["transfers"], {str(a.id): "-17.94", str(b.id): "17.94"})
        self.assertAlmostEqual(self.result(february, "A").capital, 1038000 + 400 - 20 * 1038000 / 10085500 - 17.94, places=2)
        self.assert_consistent(february)
