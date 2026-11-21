from datetime import date
from decimal import Decimal

from odoo.tests import tagged

from . import test_scenarios
from .common import NavCase


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


@tagged("post_install", "-at_install")
class TestZj25SplitScenarios(test_scenarios.TestScenarios):
    """ZJ-25 G1: na referenčních scénářích sedí kontrola `class_split` a součet vlivu = změna společná + specifická."""

    def run_to_posted(self, valuation):
        valuation = super().run_to_posted(valuation)
        check = valuation.check_ids.filtered(lambda c: c.code == "class_split")
        self.assertEqual(check.status, "ok", check.detail)
        for line, modes in valuation._class_split().items():
            impact = sum((r["impact"] for r in modes["balance"]), Decimal(0))
            self.assertEqual(impact, money(line.shared_result) + money(line.delta), line.class_id.code)
        return valuation


@tagged("post_install", "-at_install")
class TestZj25Split(NavCase):
    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}, {"code": "M", "shares_common": False},
                                            {"code": "E", "currency_id": self.eur.id}])
        self.a, self.b, self.m, self.e = (self.cls(self.fund, c) for c in ("A", "B", "M", "E"))
        for day, value in (("2027-01-01", 25), ("2027-01-31", 26), ("2027-02-28", 27)):
            self.rate(day, value)
        self.subscribe(self.a, "2027-01-01", 60000, 600)
        self.subscribe(self.b, "2027-01-01", 40000, 400)
        self.subscribe(self.m, "2027-01-01", 2000, 20)
        movement = self.env["investra.class.movement"].create({
            "class_id": self.e.id, "date": "2027-01-01", "manual_reason": "Test", "movement_type": "subscription",
            "amount_class": 1000, "units": 10})
        movement._book()
        self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Třída B", "kind": "periodic", "base_source": "class_fk",
            "class_ids": [(6, 0, self.b.ids)], "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})]})

    def first_period(self):
        self.common_result(self.fund, "c1", "2027-01-20", 5000)
        self.specific(self.fund, self.a, "s1", "2027-01-20", 300)
        self.specific(self.fund, self.m, "s2", "2027-01-21", 50)
        return self.run_to_posted(self.valuation(self.fund, date(2027, 1, 31)))

    def second_period(self):
        self.subscribe(self.a, "2027-02-10", 3000, 30)
        self.subscribe(self.b, "2027-02-15", 1000, 10, "redemption")
        self.common_result(self.fund, "c2", "2027-02-20", 2000)
        return self.run_to_posted(self.valuation(self.fund, date(2027, 2, 28)))

    def assert_split(self, valuation):
        check = valuation.check_ids.filtered(lambda c: c.code == "class_split")
        self.assertEqual(check.status, "ok", check.detail)
        split = valuation._class_split()
        self.assertEqual(len(split), 4)
        for line, modes in split.items():
            for mode, rows in modes.items():
                impact = sum((r["impact"] for r in rows), Decimal(0))
                self.assertEqual(impact, money(line.shared_result) + money(line.delta), f"{line.class_id.code} {mode}")
                self.assertEqual(sum((r["specific"] for r in rows), Decimal(0)), money(line.delta), f"{line.class_id.code} {mode}")
        return split

    def test_classes_with_and_without_share_foreign_currency_and_fee(self):
        self.assert_split(self.first_period())

    def test_subscription_and_redemption_give_capital_row(self):
        self.first_period()
        valuation = self.second_period()
        split = self.assert_split(valuation)
        movements = sum((money(l.pre_capital) - money(l.opening_capital) for l in valuation.class_line_ids), Decimal(0))
        self.assertNotEqual(movements, 0)
        for modes in split.values():
            capital = [r for r in modes["balance"] if r["group"] == "capital"]
            self.assertEqual(capital[0]["common"], -movements)

    def test_entry_into_past_period_gives_prior_row(self):
        self.first_period()
        # Zápis do minulého období po zaúčtování minulého ocenění nejde (zámek); stejný stav vznikne, když minulé ocenění
        # eviduje o 700 míň, než kniha k jeho datu obsahuje.
        previous = self.env["investra.valuation"].search([("fund_id", "=", self.fund.id)])
        self.result(previous, "A").sudo().capital -= 700
        valuation = self.valuation(self.fund, date(2027, 2, 28))
        valuation.action_compute()  # jiná kontrola (součet FK (t−1)) ocenění zastaví, rozpad ale sedí
        split = self.assert_split(valuation)
        for modes in split.values():
            prior = [r for r in modes["balance"] if r["group"] == "prior"]
            self.assertEqual(prior[0]["common"], Decimal("700.00"))

    def test_result_mode_has_same_totals_and_transfers_reconcile(self):
        self.first_period()
        valuation = self.second_period()
        for line, modes in valuation._class_split().items():
            for key in ("common", "share", "specific", "impact"):
                self.assertEqual(sum((r[key] for r in modes["balance"]), Decimal(0)),
                                 sum((r[key] for r in modes["result"]), Decimal(0)), f"{line.class_id.code} {key}")
            transfer = [r for r in modes["result"] if r["group"] == "transfer"]
            documents = valuation._class_split_transfers(line)
            self.assertEqual(money(sum(d["common"] for d in documents)), transfer[0]["common"] if transfer else Decimal("0.00"))
            self.assertEqual(money(sum(d["specific"] for d in documents)), transfer[0]["specific"] if transfer else Decimal("0.00"))

    def test_published_valuation_can_be_opened_without_changes(self):
        self.first_period()
        valuation = self.second_period()
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        valuation.with_user(self.approver).action_publish()
        self.assertEqual(valuation.state, "published")
        line = self.result(valuation, "A")
        snapshot = (valuation.fund_capital, line.capital, self.env["account.move"].search_count([]))
        action = line.with_context(split_mode="balance").action_open_split()
        rows = self.env["investra.valuation.class.account"].search(action["domain"])
        self.assertTrue(rows)
        self.assertEqual((valuation.fund_capital, line.capital, self.env["account.move"].search_count([])), snapshot)
        # druhé otevření nahradí starší dočasné řádky, ne přidá
        action = line.with_context(split_mode="balance").action_open_split()
        self.assertEqual(len(self.env["investra.valuation.class.account"].search(action["domain"])), len(rows))

    def test_open_lines_domain(self):
        valuation = self.first_period()
        line = self.result(valuation, "A")
        action = line.with_context(split_mode="balance").action_open_split()
        rows = self.env["investra.valuation.class.account"].search(action["domain"]).filtered("account_id")
        self.assertTrue(rows)
        start = valuation._period_start()
        for row in rows:
            moves = self.env["account.move.line"].search(row.action_open_lines()["domain"])
            self.assertTrue(moves)
            for move_line in moves:
                self.assertEqual(move_line.account_id, row.account_id)
                self.assertGreater(move_line.date, start)
                self.assertIn(move_line.investra_class_id.id, (False, line.class_id.id))
