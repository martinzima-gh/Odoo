from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFees(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def two_class_fund(self, a=1000, b=1000):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", a, 100)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", b, 100)
        return fund

    def test_rate_change_within_period(self):
        # 3,65 % do 15. 1. (15 dní), 7,3 % do 31. 1. (16 dní), základ 36 500:
        # 36 500 × (0,0365 × 15 + 0,073 × 16) / 365 = 54,75 + 116,80 = 171,55
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 36500, 100)
        self.Rule.create({"fund_id": fund.id, "name": "Úplata", "kind": "periodic", "version_ids": [
            (0, 0, {"valid_from": "2020-01-01", "rate": 0.0365}),
            (0, 0, {"valid_from": "2027-01-16", "rate": 0.073}),
        ]})
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 171.55, places=2)

    def test_used_version_cannot_be_rewritten(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 36500, 100)
        rule = self.Rule.create({"fund_id": fund.id, "name": "Úplata", "kind": "periodic",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})]})
        self.run_to_posted(self.valuation(fund, date(2027, 1, 31)))
        with self.assertRaises(UserError):
            rule.version_ids.rate = 0.01
        with self.assertRaises(UserError):
            rule.version_ids.unlink()
        self.env["investra.fee.version"].create({"rule_id": rule.id, "valid_from": "2027-02-01", "rate": 0.01})

    def test_class_specific_fee_hits_only_that_class(self):
        fund = self.two_class_fund()
        self.Rule.create({"fund_id": fund.id, "name": "Třída A", "kind": "periodic", "base_source": "class_fk",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)],
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0})]})
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        fee = valuation.fee_line_ids.amount  # 1 000 × 31/365
        self.assertAlmostEqual(fee, 84.93, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1000 - fee, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1000, places=2)

    def test_fee_of_class_paid_to_other_class_keeps_fk(self):
        # Odměna třídy C je příjmem třídy A: FK se nezmění, přesun je přes vnitřní zúčtování
        fund = self.two_class_fund()
        self.Rule.create({"fund_id": fund.id, "name": "Přesun", "kind": "periodic", "base_source": "class_fk",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "recipient_share": 1,
                          "recipient_class_ids": [(6, 0, self.cls(fund, "B").ids)],
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0})]})
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 2000, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 915.07, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1084.93, places=2)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "clearing_zero").status, "ok")

    def test_half_to_classes_half_to_manager(self):
        fund = self.two_class_fund()
        self.Rule.create({"fund_id": fund.id, "name": "Dělená", "kind": "periodic", "base_source": "class_fk",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "recipient_share": 0.5,
                          "recipient_class_ids": [(6, 0, self.cls(fund, "B").ids)],
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0})]})
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        # Úplata 84,93: polovina 42,47 třídě B, 42,46 obhospodařovateli
        self.assertAlmostEqual(valuation.fund_capital, 2000 - 42.46, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1042.47, places=2)

    def test_external_amount_requires_attachment_and_reason(self):
        fund = self.two_class_fund()
        rule = self.Rule.create({"fund_id": fund.id, "name": "Mimo Odoo", "kind": "external"})
        valuation = self.valuation(fund, date(2027, 1, 31))
        with self.assertRaises(UserError):
            valuation.action_compute()
        entry = self.env["investra.valuation.external"].with_user(self.preparer).create(
            {"valuation_id": valuation.id, "rule_id": rule.id, "amount": 25}
        )
        with self.assertRaises(UserError):
            valuation.action_compute()
        attachment = self.env["ir.attachment"].create({"name": "vypocet.xlsx", "raw": b"x"})
        entry.write({"attachment_id": attachment.id, "reason": "Výpočet podle čl. 7"})
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 1975, places=2)

    def test_performance_with_hurdle_on_class_capital(self):
        # Vstup 1 000 dne 1. 1. 2027, do 30. 6. je 180 dní, hurdle 5 %: cíl 1 000 × (1 + 0,05 × 180/365) = 1 024,66
        # Hrubě 1 100 (výnos 200 dělí 50 : 50), 100 % přebytku = 75,34
        fund = self.two_class_fund()
        self.common_result(fund, "v", "2027-06-15", 200)
        self.Rule.create({"fund_id": fund.id, "name": "Odměna", "kind": "performance",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0, "initial_reference": 0,
                                                  "perf_use_hwm": False, "hurdle_kind": "fixed", "hurdle_rate": 0.05})]})
        valuation = self.valuation(fund, date(2027, 6, 30))
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 75.34, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1024.66, places=2)

    def test_shortfall_is_covered_by_junior_class_up_to_its_capital(self):
        # Třída A cíl 5 % ročně za 365 dní; výnos 0, chybí 50; třída B má kapitál 30, kryje jen 30
        fund = self.two_class_fund(1000, 30)
        self.Rule.create({"fund_id": fund.id, "name": "Priorita", "kind": "performance", "crystallisation": "none",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "cover_class_id": self.cls(fund, "B").id,
                          "recipient_share": 1, "recipient_class_ids": [(6, 0, self.cls(fund, "B").ids)],
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0, "perf_use_hwm": False,
                                                  "hurdle_kind": "fixed", "hurdle_rate": 0.05})]})
        valuation = self.valuation(fund, date(2027, 12, 31))
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1030, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 0, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 1030, places=2)

    def test_crystallisation_updates_hwm_and_clears_accrual(self):
        fund = self.make_fund(classes=[{"code": "A"}], launch="2026-12-31")
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        self.Rule.create({"fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "month",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit",
                                                  "initial_reference": 100})]})
        self.common_result(fund, "v1", "2027-01-20", 100)
        first = self.run_to_posted(self.valuation(fund, date(2027, 1, 31)))
        # Kurz před odměnou 110, odměna 0,2 × 10 × 10 = 20, kurz po odměně 108 je nový HWM
        self.assertAlmostEqual(first.fee_line_ids.amount, 20, places=2)
        self.assertAlmostEqual(self.result(first, "A").perf_hwm, 108, places=4)
        self.assertEqual(self.result(first, "A").perf_accrued, 0)
        self.common_result(fund, "v2", "2027-02-20", 10)
        second = self.valuation(fund, date(2027, 2, 28))
        second.action_compute()
        # Kurz 109, přebytek nad 108 je 1: 0,2 × 1 × 10 = 2
        self.assertAlmostEqual(second.fee_line_ids.amount, 2, places=2)

    def test_waterfall_gives_priority_class_target_and_junior_the_rest(self):
        # 365 dní, PIA 1 000 s cílem 6 %, VIA 100; výnos 110: PIA 60, VIA 50
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
        self.assertAlmostEqual(self.result(valuation, "PIA").capital, 1060, places=2)
        self.assertAlmostEqual(self.result(valuation, "VIA").capital, 150, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 1210, places=2)

    def test_waterfall_loss_hits_junior_first(self):
        fund = self.make_fund(classes=[{"code": "PIA"}, {"code": "VIA"}])
        pia, via = self.cls(fund, "PIA"), self.cls(fund, "VIA")
        self.subscribe(pia, "2027-01-01", 1000, 100)
        self.subscribe(via, "2027-01-01", 100, 10)
        self.common_result(fund, "v", "2027-06-01", -150)
        self.env["investra.allocation.scheme"].create({"fund_id": fund.id, "valid_from": "2020-01-01", "method": "waterfall", "line_ids": [
            (0, 0, {"class_id": pia.id, "rank": 1, "target_rate": 0.06}),
            (0, 0, {"class_id": via.id, "rank": 2, "residual_share": 1, "loss_rank": 1}),
        ]})
        valuation = self.valuation(fund, date(2027, 12, 31))
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "VIA").capital, 0, places=2)
        self.assertAlmostEqual(self.result(valuation, "PIA").capital, 950, places=2)


@tagged("post_install", "-at_install")
class TestRuleFields(NavCase):
    """Varianty přes skutečné záznamy pravidel, ne jen přes výpočetní jádro."""

    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, capital=1000000, classes=("A",), launch="2026-12-31"):
        fund = self.make_fund(classes=[{"code": c} for c in classes], launch=launch)
        for code in classes:
            self.subscribe(self.cls(fund, code), "2027-01-01", capital, 1000)
        return fund

    def fee(self, fund, day, **version):
        rule_values = version.pop("rule", {})
        rule = self.Rule.create({"fund_id": fund.id, "name": "Pravidlo", "kind": "periodic", **rule_values,
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", **version})]})
        valuation = self.valuation(fund, day)
        valuation.action_compute()
        return sum(valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule).mapped("amount"))

    def test_fixed_started_month(self):
        self.assertAlmostEqual(self.fee(self.fund(), date(2027, 1, 31), fixed_monthly=110000, fixed_mode="started_month"), 110000, places=2)

    def test_fixed_plus_percent_above_threshold(self):
        # Rok: 1 000 × 12 + 1 % z (5 000 000 − 1 000 000) = 12 000 + 40 000
        fund = self.fund(5000000)
        amount = self.fee(fund, date(2027, 12, 31), fixed_monthly=1000, fixed_mode="started_month", rate=0.01, threshold=1000000)
        self.assertAlmostEqual(amount, 52000, places=2)

    def test_sliding_tiers_from_records(self):
        # Rok: 0 do 1 mil., 1 % z dalšího 1 mil., 0,5 % ze zbývajícího 1 mil. = 10 000 + 5 000
        fund = self.fund(3000000)
        amount = self.fee(fund, date(2027, 12, 31), tier_ids=[
            (0, 0, {"amount_from": 0, "rate": 0}),
            (0, 0, {"amount_from": 1000000, "rate": 0.01}),
            (0, 0, {"amount_from": 2000000, "rate": 0.005}),
        ])
        self.assertAlmostEqual(amount, 15000, places=2)

    def test_step_price_from_records(self):
        # FK 1,2 mil., pásmo 500 tis.: dvě započatá pásma nad prvním, 45 000 + 2 × 10 000
        fund = self.fund(1200000)
        amount = self.fee(fund, date(2027, 1, 31), fixed_monthly=45000, fixed_mode="started_month",
                          step_size=500000, step_amount=10000)
        self.assertAlmostEqual(amount, 65000, places=2)

    def test_annual_minimum_and_maximum(self):
        self.assertAlmostEqual(self.fee(self.fund(100000), date(2027, 12, 31), rate=0.001, min_annual=200), 200, places=2)

    def test_annual_maximum(self):
        self.assertAlmostEqual(self.fee(self.fund(100000000), date(2027, 12, 31), rate=0.01, max_annual=1000), 1000, places=2)

    def test_extra_class_surcharge(self):
        fund = self.fund(1000, classes=("A", "B", "C"))
        amount = self.fee(fund, date(2027, 1, 31), fixed_monthly=100, fixed_mode="started_month", included_classes=2, extra_class_monthly=10)
        self.assertAlmostEqual(amount, 110, places=2)

    def test_base_from_assets(self):
        # Aktiva 1 000 000 i po závazku 100 000: základ se nesnižuje o závazky
        fund = self.fund()
        self.book(fund, "z", "2027-01-10", [{"role": "bank", "amount": "100000"}, {"role": "fee_payable", "amount": "-100000"}])
        amount = self.fee(fund, date(2027, 12, 31), rate=0.01, rule={"base_source": "assets"})
        self.assertAlmostEqual(amount, 11000, places=2)

    def test_day_count_months(self):
        amount = self.fee(self.fund(), date(2027, 3, 31), rate=0.012, rule={"basis": "months"})
        self.assertAlmostEqual(amount, 3000, places=2)

    def test_day_count_30e_360(self):
        # 31. 12. → 31. 3.: 90 dní, 1 000 000 × 1,2 % × 90/360 = 3 000
        amount = self.fee(self.fund(), date(2027, 3, 31), rate=0.012, rule={"basis": "thirty360_eu"})
        self.assertAlmostEqual(amount, 3000, places=2)

    def test_average_fk_with_true_up(self):
        # Sazba 3,65 %, leden 31 dní: průměr 1 000 000, úplata 3 100
        fund = self.fund()
        rule = self.Rule.create({"fund_id": fund.id, "name": "Fixní", "kind": "periodic", "base_source": "average_fk",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})]})
        january = self.run_to_posted(self.valuation(fund, date(2027, 1, 31)))
        self.assertAlmostEqual(january.fee_line_ids.amount, 3100, places=2)
        self.assertAlmostEqual(january.fund_capital, 996900, places=2)
        # Únor: úpis 1 000 000, FK 1 996 900, průměr (996 900 + 1 996 900) / 2 = 1 496 900
        # Nárok za 59 dní: 1 496 900 × 0,0365 × 59/365 = 8 831,71; doúčtování 8 831,71 − 3 100 = 5 731,71
        self.subscribe(self.cls(fund, "A"), "2027-02-10", 1000000, 1000)
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        self.assertAlmostEqual(february.fee_line_ids.filtered(lambda l: l.rule_id == rule).amount, 5731.71, places=2)

    def performance(self, fund, day, rule=None, **version):
        code = fund.class_ids[0]
        values = {"rate": 0.2, "perf_measure": "unit", "initial_reference": 1000, **version}
        self.Rule.create({"fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "none",
                          "expense_role": "expense_performance", "class_ids": [(6, 0, code.ids)], **(rule or {}),
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", **values})]})
        valuation = self.valuation(fund, day)
        valuation.action_compute()
        return valuation

    def test_index_benchmark_with_margin(self):
        # Index 100 → 104, marže 2 % za 365 dní, faktor 1,06; kus 1 000 → 1 100: 0,2 × 40 × 1 000 kusů = 8 000
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-01", 100000)
        benchmark = self.env["investra.benchmark"].create({"name": "Index", "value_ids": [
            (0, 0, {"date": "2026-12-31", "value": 100}), (0, 0, {"date": "2027-12-31", "value": 104}),
        ]})
        valuation = self.performance(fund, date(2027, 12, 31), perf_use_hwm=False, hurdle_kind="index",
                                     hurdle_margin=0.02, benchmark_id=benchmark.id)
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 8000, places=2)

    def test_fee_on_negative_return_needs_flag(self):
        # Index −10 %, fond −5 %: bez příznaku se platí, s příznakem ne
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-01", -50000)
        benchmark = self.env["investra.benchmark"].create({"name": "Index", "value_ids": [
            (0, 0, {"date": "2026-12-31", "value": 100}), (0, 0, {"date": "2027-12-31", "value": 90}),
        ]})
        valuation = self.performance(fund, date(2027, 12, 31), perf_use_hwm=False, hurdle_kind="index",
                                     benchmark_id=benchmark.id, require_positive_return=True)
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 0, places=2)

    def test_soft_hurdle_catch_up_from_records(self):
        # Kus 1 000 → 1 300, hurdle 8 %, plné dohánění: 20 % z celého zisku = 60 na kus, 60 000
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-01", 300000)
        valuation = self.performance(fund, date(2027, 12, 31), perf_use_hwm=False, hurdle_kind="fixed", hurdle_rate=0.08,
                                     hurdle_type="soft", catch_up=1)
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 60000, places=2)

    def test_probability_weighted_accrual(self):
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-01", 100000)
        valuation = self.performance(fund, date(2027, 12, 31), probability=0.5)
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 10000, places=2)

    def test_cap_from_gross_value(self):
        # Odměna 20 000 omezená na 1 % z hodnoty 1 100 000 = 11 000
        fund = self.fund()
        self.common_result(fund, "v", "2027-06-01", 100000)
        valuation = self.performance(fund, date(2027, 12, 31), cap_rate=0.01)
        self.assertAlmostEqual(valuation.fee_line_ids.amount, 11000, places=2)

    def test_quarter_crystallises_only_at_quarter_end(self):
        fund = self.fund()
        rule = {"crystallisation": "quarter"}
        self.common_result(fund, "v", "2027-01-20", 100000)
        january = self.performance(fund, date(2027, 1, 31), rule=rule)
        self.assertEqual(self.result(january, "A").perf_hwm, 1000)
        self.assertAlmostEqual(self.result(january, "A").perf_accrued, 20000, places=2)

    def test_quarter_end_sets_new_hwm(self):
        fund = self.fund()
        self.common_result(fund, "v", "2027-03-20", 100000)
        march = self.performance(fund, date(2027, 3, 31), rule={"crystallisation": "quarter"})
        self.assertAlmostEqual(self.result(march, "A").perf_hwm, 1080, places=4)
        self.assertEqual(self.result(march, "A").perf_accrued, 0)

    def test_waterfall_residual_half_by_capital(self):
        # Zbytek 100: polovina podle kapitálů 3 : 1, polovina třídě V
        fund = self.make_fund(classes=[{"code": "P"}, {"code": "V"}])
        p, v = self.cls(fund, "P"), self.cls(fund, "V")
        self.subscribe(p, "2027-01-01", 300, 3)
        self.subscribe(v, "2027-01-01", 100, 1)
        self.common_result(fund, "v", "2027-01-15", 100)
        self.env["investra.allocation.scheme"].create({
            "fund_id": fund.id, "valid_from": "2020-01-01", "method": "waterfall", "residual_pro_rata": 0.5,
            "line_ids": [(0, 0, {"class_id": v.id, "rank": 2, "residual_share": 1}), (0, 0, {"class_id": p.id, "rank": 1})],
        })
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "P").capital, 337.5, places=2)
        self.assertAlmostEqual(self.result(valuation, "V").capital, 162.5, places=2)

    def test_rule_order_changes_base(self):
        # Pořadí podle statutu: druhá úplata má základ po první
        fund = self.fund(1000000)
        self.Rule.create({"fund_id": fund.id, "name": "První", "kind": "periodic", "sequence": 1,
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.1})]})
        self.Rule.create({"fund_id": fund.id, "name": "Druhá", "kind": "periodic", "sequence": 2,
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.1})]})
        valuation = self.valuation(fund, date(2027, 12, 31))
        valuation.action_compute()
        amounts = valuation.fee_line_ids.sorted("id").mapped("amount")
        self.assertAlmostEqual(amounts[0], 100000, places=2)
        self.assertAlmostEqual(amounts[1], 90000, places=2)
