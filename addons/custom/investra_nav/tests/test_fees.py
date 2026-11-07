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
