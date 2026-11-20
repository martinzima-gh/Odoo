"""ZJ-17: účetní (hospodářský) rok fondu – výpočty „od začátku období“ podle knihy, ne podle kalendářního roku.

Kniha s účetním obdobím 1. 7. – 30. 6. (`fiscalyear_last_day/month` společnosti). Kalendářní kniha dává stejné výsledky jako dřív
(referenční scénáře a snímek ocenění 35 a 39 to ověřují mimo tento soubor).
"""

import json
from datetime import date, timedelta

from odoo import fields
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFiscalYear(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def july_fund(self, launch="2026-03-01", subscription=1000000):
        """Fond s účetním obdobím 1. 7. – 30. 6., třída A upsaná ke dni vzniku (kusy po 1 000 Kč → kurz 1 000)."""
        fund = self.make_fund(launch=launch, classes=[{"code": "A"}])
        fund.company_id.write({"fiscalyear_last_day": 30, "fiscalyear_last_month": "6"})
        # Úpis až po dni vzniku: úpis ke dni vzniku by do prvního období nespadl.
        self.subscribe(self.cls(fund, "A"), fields.Date.to_date(launch) + timedelta(days=1), subscription, subscription / 1000)
        return fund

    def tax_rule(self, fund, rate=0.05):
        return self.Rule.create({"fund_id": fund.id, "name": "Daň", "kind": "tax",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})]})

    def tax_amount(self, valuation):
        return round(sum(valuation.fee_line_ids.filtered(lambda f: f.rule_id.kind == "tax").mapped("amount")), 2)

    # --- funkce fondu ------------------------------------------------------------------------------------------------

    def test_fiscal_year_start_follows_book(self):
        calendar = self.make_fund(classes=[{"code": "A"}])
        july = self.july_fund()
        for day, start_calendar, start_july in [
            (date(2027, 3, 15), date(2027, 1, 1), date(2026, 7, 1)),
            (date(2027, 6, 30), date(2027, 1, 1), date(2026, 7, 1)),
            (date(2027, 7, 1), date(2027, 1, 1), date(2027, 7, 1)),
            (date(2027, 12, 31), date(2027, 1, 1), date(2027, 7, 1)),
        ]:
            with self.subTest(day=day):
                self.assertEqual(calendar._fiscal_year_start(day), start_calendar)
                self.assertEqual(july._fiscal_year_start(day), start_july)
        self.assertEqual(july._fiscal_year_dates(date(2027, 3, 15)), (date(2026, 7, 1), date(2027, 6, 30)))

    def test_year_start_of_valuation_is_day_before_period(self):
        # Ocenění „od začátku období“ mají datum po tomto dni.
        self.assertEqual(self.valuation(self.july_fund(), date(2026, 8, 31))._year_start(), date(2026, 6, 30))
        self.assertEqual(self.valuation(self.make_fund(), date(2027, 3, 31))._year_start(), date(2026, 12, 31))

    # --- daň se na začátku období nuluje ----------------------------------------------------------------------------

    def test_tax_restarts_at_period_start(self):
        fund = self.july_fund()
        self.tax_rule(fund)
        self.common_result(fund, "v1", "2027-03-15", 1000)
        march = self.run_to_posted(self.valuation(fund, date(2027, 3, 31)))
        self.assertAlmostEqual(self.tax_amount(march), 50, places=2)
        # Nové období od 1. 7. 2027 začíná ztrátou: daň od začátku období je 0 (základ −400), dřívější daň se neuvolňuje.
        # Při kalendářním roce by základ od 1. 1. byl 600 a doúčtovala by se záporná daň −20.
        self.common_result(fund, "v2", "2027-08-10", -400)
        august = self.valuation(fund, date(2027, 8, 31))
        august.action_compute()
        self.assertAlmostEqual(self.tax_amount(august), 0, places=2)

    def test_tax_in_same_period_across_new_year_is_cumulative(self):
        # Přes Nový rok uvnitř jednoho období se daň dopočítává kumulativně (leden 2027 patří do období od 1. 7. 2026).
        fund = self.july_fund()
        self.tax_rule(fund)
        self.common_result(fund, "v1", "2026-12-15", 1000)
        december = self.run_to_posted(self.valuation(fund, date(2026, 12, 31)))
        self.assertAlmostEqual(self.tax_amount(december), 50, places=2)
        self.common_result(fund, "v2", "2027-01-15", -400)
        january = self.valuation(fund, date(2027, 1, 31))
        january.action_compute()
        # Základ od 1. 7. 2026 je 600 → daň 30 celkem, 50 už zaúčtováno → uvolnění −20 (kalendářně by základ od 1. 1. byl −400).
        self.assertAlmostEqual(self.tax_amount(january), -20, places=2)

    # --- odměna: krystalizace „ročně“ ------------------------------------------------------------------------------

    def performance(self, fund):
        return self.Rule.create({
            "fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "year",
            "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit", "initial_reference": 1000})]})

    def test_crystallisation_year_is_period_end(self):
        fund = self.july_fund(launch="2026-07-01")
        self.performance(fund)
        self.common_result(fund, "v1", "2026-12-20", 100000)
        december = self.run_to_posted(self.valuation(fund, date(2026, 12, 31)))
        # 31. 12. není konec účetního období: odměna jen naběhne (kurz 1 100 nad 1 000: 0,2 × 100 × 1 000 = 20 000).
        self.assertAlmostEqual(self.result(december, "A").perf_accrued, 20000, places=2)
        self.assertAlmostEqual(self.result(december, "A").perf_hwm, 1000, places=4)
        # 30. 6. 2027 je konec období: krystalizace, naběhlá odměna se vynuluje a kurz po odměně (1 080) je nový HWM.
        june = self.run_to_posted(self.valuation(fund, date(2027, 6, 30)))
        self.assertAlmostEqual(self.result(june, "A").perf_hwm, 1080, places=4)
        self.assertEqual(self.result(june, "A").perf_accrued, 0)

    def test_crystallisation_year_calendar_book_unchanged(self):
        fund = self.make_fund(launch="2026-12-31", classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000000, 1000)
        self.performance(fund)
        self.common_result(fund, "v1", "2027-06-20", 100000)
        june = self.run_to_posted(self.valuation(fund, date(2027, 6, 30)))
        self.assertAlmostEqual(self.result(june, "A").perf_accrued, 20000, places=2)
        self.common_result(fund, "v2", "2027-12-20", 1)
        december = self.run_to_posted(self.valuation(fund, date(2027, 12, 31)))
        self.assertEqual(self.result(december, "A").perf_accrued, 0)

    # --- průměrný FK a zaúčtované úplaty jen od začátku období -----------------------------------------------------

    def test_average_fk_starts_at_period_start(self):
        fund = self.july_fund(launch="2026-03-01")
        rule = self.Rule.create({
            "fund_id": fund.id, "name": "Obhospodařování", "kind": "periodic", "base_source": "average_fk", "base_step": "2",
            "expense_role": "expense_management", "class_ids": [(6, 0, self.cls(fund, "A").ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})]})
        # Ocenění v předchozím období (do 30. 6. 2026): jeho úplata se do nového období nepočítá.
        april = self.run_to_posted(self.valuation(fund, date(2026, 4, 30)))
        self.assertTrue(april.fee_line_ids.filtered(lambda l: l.rule_id == rule))
        august = self.valuation(fund, date(2026, 8, 31))
        august.action_compute()
        line = august.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        detail = json.loads(line.detail)
        # Začátek nároku je 30. 6. 2026 (poslední den minulého období), ne 1. 3. (vznik) ani 31. 12. 2025; 62 dní, nic zaúčtováno.
        self.assertEqual(detail["start"], "2026-06-30")
        self.assertAlmostEqual(float(detail["booked"]), 0, places=2)
        # Bod průměru je jen dnešní hodnota třídy po vlastní úplatě (zaúčtované dubnové ocenění je v minulém období):
        # úplata = průměr × 3,65 % × 62 / 365.
        self.assertAlmostEqual(float(detail["average"]), float(detail["today"]), places=2)
        self.assertAlmostEqual(line.amount, float(detail["average"]) * 0.0365 * 62 / 365, places=2)
        self.assertGreater(line.amount, 6000)
