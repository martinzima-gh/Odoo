import io
import zipfile
from decimal import Decimal

from odoo.tests import tagged

from .common import NavCase

BRIDGE_CHECKS = {"bridge_movements", "bridge_units", "bridge_result", "bridge_opening"}


@tagged("post_install", "-at_install")
class TestBridge(NavCase):
    """Přemostění kapitálu tříd (rozhodnutí 2026-11-10): rozpad je spočtený ručně, výsledek NAV se nemění."""

    def two_classes(self):
        fund = self.make_fund(classes=[{"code": "A", "price_digits": 4}, {"code": "B", "price_digits": 4}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000000, 10000)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", 500000, 5000)
        return fund

    def assertBridgeChecksOk(self, valuation):
        checks = {c.code: c.status for c in valuation.check_ids if c.code in BRIDGE_CHECKS}
        self.assertEqual(checks, dict.fromkeys(BRIDGE_CHECKS, "ok"))

    def test_first_period_starts_from_zero(self):
        # Leden: společný výsledek 30 000, specifická položka třídy B −1 500 (stejně jako scénář s2).
        fund = self.two_classes()
        self.common_result(fund, "common0", "2027-01-31", 30000)
        self.specific(fund, self.cls(fund, "B"), "specB", "2027-01-31", -1500)
        valuation = self.run_to_posted(self.valuation(fund, "2027-01-31"))
        a, b = self.result(valuation, "A"), self.result(valuation, "B")
        self.assertEqual((a.opening_capital, a.opening_units, a.opening_price), (0, 0, False))
        self.assertEqual((a.subscription_amount, a.subscription_units), (1000000, 10000))
        # 1 530 000 × 2/3 = 1 020 000 → změna společná A = 20 000; B = 510 000 − 500 000 = 10 000.
        self.assertAlmostEqual(a.shared_result, 20000, places=2)
        self.assertAlmostEqual(b.shared_result, 10000, places=2)
        self.assertAlmostEqual(b.delta, -1500, places=2)
        self.assertAlmostEqual(b.other_amount, -1500, places=2)
        self.assertEqual((b.fee_amount, b.performance_amount, b.allocation_amount), (0, 0, 0))
        self.assertAlmostEqual(b.capital, 508500, places=2)
        self.assertEqual(a.price_change_pct, 0)
        self.assertBridgeChecksOk(valuation)

    def test_second_period_with_subscription_and_redemption(self):
        fund = self.two_classes()
        self.common_result(fund, "common0", "2027-01-31", 30000)
        self.specific(fund, self.cls(fund, "B"), "specB", "2027-01-31", -1500)
        self.run_to_posted(self.valuation(fund, "2027-01-31"))
        self.common_result(fund, "common1", "2027-02-28", -12000)
        self.subscribe(self.cls(fund, "A"), "2027-02-28", 200000, 1960)
        self.subscribe(self.cls(fund, "B"), "2027-02-28", 50000, 490, "redemption")
        valuation = self.run_to_posted(self.valuation(fund, "2027-02-28"))
        a, b = self.result(valuation, "A"), self.result(valuation, "B")
        # Počáteční stav = konec ledna.
        self.assertAlmostEqual(a.opening_capital, 1020000, places=2)
        self.assertEqual((a.opening_units, a.opening_price), (10000, "102.0000"))
        self.assertAlmostEqual(b.opening_capital, 508500, places=2)
        # Pohyby; odkupy kladně.
        self.assertEqual((a.subscription_amount, a.subscription_units), (200000, 1960))
        self.assertEqual((b.redemption_amount, b.redemption_units), (50000, 490))
        self.assertAlmostEqual(a.pre_capital, 1220000, places=2)
        self.assertAlmostEqual(b.pre_capital, 458500, places=2)
        # NFK 1 666 500 podle poměru 1 220 000 : 458 500 → FK A 1 211 277,93, B 455 222,07.
        self.assertAlmostEqual(a.shared_result, -8722.07, places=2)
        self.assertAlmostEqual(b.shared_result, -3277.93, places=2)
        self.assertAlmostEqual(b.delta, 0, places=2)
        for line in (a, b):
            end = line.opening_capital + line.subscription_amount - line.redemption_amount + line.shared_result + line.delta
            self.assertAlmostEqual(end, line.capital, places=2)
        expected_change = (Decimal("101.2774") / Decimal("102.0000") - 1) * 100
        self.assertAlmostEqual(a.price_change_pct, float(expected_change), places=4)
        # Zobrazení v tabulce tříd (jazyk testu en_US): kód třídy, kurz z uloženého textu, změna se znaménkem.
        self.assertEqual(a.class_code, "A")
        self.assertEqual((a.price_display, a.price_change_display), ("101.2774", "−0.71 %"))
        self.assertBridgeChecksOk(valuation)

    def test_fee_and_performance_are_split_from_specific_change(self):
        # Leden ze scénáře s4: úplata ze společné části, výkonnostní odměna třídy A 9 643,29.
        fund = self.make_fund(classes=[{"code": "A", "price_digits": 4}, {"code": "B", "price_digits": 4}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000000, 1000)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", 1000000, 1000)
        Rule = self.env["investra.fee.rule"]
        Rule.create({
            "fund_id": fund.id, "name": "Úplata", "kind": "periodic", "basis": "act365",
            "base_step": "1", "expense_role": "expense_management",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.02})],
        })
        Rule.create({
            "fund_id": fund.id, "name": "Odměna A", "kind": "performance",
            "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
            "crystallisation": "none",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit",
                                    "initial_reference": 1000})],
        })
        self.common_result(fund, "common0", "2027-01-31", 100000)
        valuation = self.run_to_posted(self.valuation(fund, "2027-01-31"))
        a, b = self.result(valuation, "A"), self.result(valuation, "B")
        self.assertAlmostEqual(a.performance_amount, -9643.29, places=2)
        self.assertAlmostEqual(a.delta, -9643.29, places=2)
        self.assertEqual((a.fee_amount, a.other_amount, a.allocation_amount), (0, 0, 0))
        self.assertEqual((b.fee_amount, b.performance_amount, b.other_amount), (0, 0, 0))
        self.assertBridgeChecksOk(valuation)

    def s4_fund(self):
        """Scénář s4: úplata 2 % ze společné části, odměna třídy A 20 % (HWM 1 000 na kus), daň 5 %."""
        fund = self.make_fund(classes=[{"code": "A", "price_digits": 4}, {"code": "B", "price_digits": 4}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000000, 1000)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", 1000000, 1000)
        Rule = self.env["investra.fee.rule"]
        Rule.create({
            "fund_id": fund.id, "name": "Úplata", "kind": "periodic", "basis": "act365",
            "base_step": "1", "expense_role": "expense_management",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.02})],
        })
        perf = Rule.create({
            "fund_id": fund.id, "name": "Odměna A", "kind": "performance",
            "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
            "crystallisation": "none",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit",
                                    "initial_reference": 1000})],
        })
        Rule.create({"fund_id": fund.id, "name": "Daň", "kind": "tax",
                     "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.05})]})
        return fund, perf

    def test_tax_effect_has_own_column(self):
        # ZJ-12 krok 6c (schváleno 2026-11-19), čísla ze scénáře s4 (tax_transfers): přesun daňového efektu má vlastní
        # sloupec, Ostatní specifické zůstane 0. FK a kurzy tříd se nemění (kontroluje test_s4).
        fund, _perf = self.s4_fund()
        expected = {
            "2027-01-31": {"A": (-9643.29, 241.08, -9402.21), "B": (0, -241.08, -241.08)},
            "2027-02-28": {"A": (7276.61, -182.72, 7093.89), "B": (0, 182.72, 182.72)},
        }
        for index, (day, classes) in enumerate(expected.items()):
            self.common_result(fund, f"common{index}", day, (100000, -70000)[index])
            valuation = self.run_to_posted(self.valuation(fund, day))
            for code, (performance, tax_effect, delta) in classes.items():
                line = self.result(valuation, code)
                self.assertAlmostEqual(line.performance_amount, performance, places=2, msg=f"{code} {day}")
                self.assertAlmostEqual(line.tax_effect_amount, tax_effect, places=2, msg=f"{code} {day}")
                self.assertAlmostEqual(line.other_amount, 0, places=2, msg=f"{code} {day}")
                self.assertAlmostEqual(line.fee_amount, 0, places=2, msg=f"{code} {day}")
                self.assertAlmostEqual(line.delta, delta, places=2, msg=f"{code} {day}")
            self.assertBridgeChecksOk(valuation)

    def test_performance_correction_in_performance_column(self):
        # ZJ-12 krok 6c varianta (b): oprava odměny třídy A −1 000 patří do Výkonnostní odměny, ne do Úplat třídy.
        fund, perf = self.s4_fund()
        self.common_result(fund, "common0", "2027-01-31", 100000)
        valuation = self.valuation(fund, "2027-01-31")
        self.manual_fee(valuation, -1000, note="Dohoda s depozitářem", account_id=False, corrects_rule_id=perf.id,
                        class_id=self.cls(fund, "A").id)
        valuation.action_compute()
        a = self.result(valuation, "A")
        corrections = valuation.fee_line_ids.filtered(lambda l: l.external_id.corrects_rule_id == perf)
        self.assertAlmostEqual(sum(corrections.mapped("amount")), -1000, places=2)
        rule_line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == perf)
        self.assertAlmostEqual(a.performance_amount, -(rule_line.amount - 1000), places=2)
        self.assertAlmostEqual(a.fee_amount, 0, places=2)
        self.assertAlmostEqual(a.other_amount, 0, places=2)
        self.assertBridgeChecksOk(valuation)

    def test_waterfall_transfer_has_own_column(self):
        # Stejně jako test_fees: PIA 1 000 s cílem 6 %, VIA 100, výnos 110 za rok → PIA 1 060, VIA 150.
        # Podle poměru 10 : 1 by PIA dostala 100 a VIA 10; pořadí nároků přesune 40 z PIA do VIA.
        from datetime import date
        fund = self.make_fund(classes=[{"code": "PIA"}, {"code": "VIA"}])
        pia, via = self.cls(fund, "PIA"), self.cls(fund, "VIA")
        self.subscribe(pia, "2027-01-01", 1000, 100)
        self.subscribe(via, "2027-01-01", 100, 10)
        self.common_result(fund, "v", "2027-06-01", 110)
        self.env["investra.allocation.scheme"].create({"fund_id": fund.id, "valid_from": "2020-01-01", "method": "waterfall", "line_ids": [
            (0, 0, {"class_id": pia.id, "rank": 1, "target_rate": 0.06}),
            (0, 0, {"class_id": via.id, "rank": 2, "residual_share": 1, "loss_rank": 1}),
        ]})
        valuation = self.valuation(fund, date(2027, 12, 31))
        valuation.action_compute()
        p, v = self.result(valuation, "PIA"), self.result(valuation, "VIA")
        self.assertAlmostEqual(p.shared_result, 100, places=2)
        self.assertAlmostEqual(v.shared_result, 10, places=2)
        self.assertAlmostEqual(p.allocation_amount, -40, places=2)
        self.assertAlmostEqual(v.allocation_amount, 40, places=2)
        self.assertEqual((p.other_amount, v.other_amount), (0, 0))
        self.assertAlmostEqual(p.capital, 1060, places=2)
        self.assertBridgeChecksOk(valuation)

    def test_class_in_other_currency_shows_class_currency_values(self):
        # Rok 2034 je jen pro tento test: kurzy jsou v databázi společné.
        fund = self.make_fund(launch="2033-12-31", classes=[{"code": "E", "price_digits": 4, "currency_id": self.eur.id}])
        self.rate("2034-01-02", 25)
        self.rate("2034-01-31", 25)
        self.env["investra.class.movement"].create({
            "class_id": self.cls(fund, "E").id, "date": "2034-01-02", "manual_reason": "Test", "movement_type": "subscription",
            "amount_class": 40000, "fx_rate": 25, "units": 400,
        })._book()
        self.common_result(fund, "common0", "2034-01-31", 25000)
        valuation = self.run_to_posted(self.valuation(fund, "2034-01-31"))
        line = self.result(valuation, "E")
        self.assertTrue(line.foreign_currency)
        self.assertAlmostEqual(line.fx_rate, 25, places=6)
        self.assertAlmostEqual(line.subscription_amount_class, 40000, places=2)
        # 1 000 000 + 25 000 CZK = 1 025 000 CZK / 25 = 41 000 EUR.
        self.assertAlmostEqual(line.capital_class, 41000, places=2)
        self.assertBridgeChecksOk(valuation)

    def test_package_has_bridge_sheet(self):
        fund = self.two_classes()
        self.common_result(fund, "common0", "2027-01-31", 30000)
        valuation = self.run_to_posted(self.valuation(fund, "2027-01-31"))
        data = zipfile.ZipFile(io.BytesIO(valuation.action_build_package().raw))
        self.assertIn("Přemostění tříd", data.read("xl/workbook.xml").decode())
        strings = data.read("xl/sharedStrings.xml").decode()
        for label in ("FK (t−1)", "Změna společná", "Změna specifická", "Výkonnostní odměna", "FK v měně třídy"):
            self.assertIn(label, strings)
