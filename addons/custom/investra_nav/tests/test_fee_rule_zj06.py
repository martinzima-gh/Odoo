from datetime import date

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFeeRuleZj06(NavCase):
    """ZJ-06: statut a poznámka, stav verze sazby, kontroly tříd pravidla, krystalizace při každém ocenění."""

    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def rule(self, fund, **vals):
        return self.Rule.create({
            "fund_id": fund.id, "name": "Úplata", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})], **vals,
        })

    def test_statute_and_note_is_one_multiline_field(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        rule = self.rule(fund, statute_ref="čl. 8.1\nPoznámka na druhém řádku")
        self.assertEqual(rule.statute_ref.count("\n"), 1)
        self.assertNotIn("note", self.Rule._fields)

    def test_version_state_follows_next_version(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        rule = self.rule(fund)
        today = fields.Date.context_today(rule)
        rule.write({"version_ids": [
            (0, 0, {"valid_from": date(today.year - 1, 1, 1), "rate": 0.02}),
            (0, 0, {"valid_from": date(today.year + 1, 1, 1), "rate": 0.03}),
        ]})
        states = {v.valid_from: v.validity_state for v in rule.version_ids}
        self.assertEqual(states[date(2020, 1, 1)], "ended")
        self.assertEqual(states[date(today.year - 1, 1, 1)], "current")
        self.assertEqual(states[date(today.year + 1, 1, 1)], "future")
        self.assertNotIn("valid_to", self.env["investra.fee.version"]._fields)

    def test_classes_must_belong_to_rule_fund(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        other = self.make_fund(classes=[{"code": "X"}])
        with self.assertRaises(ValidationError):
            self.rule(fund, class_ids=[Command.set(self.cls(other, "X").ids)])
        with self.assertRaises(ValidationError):
            self.rule(fund, recipient_class_ids=[Command.set(self.cls(other, "X").ids)])
        with self.assertRaises(ValidationError):
            self.rule(fund, kind="performance", cover_class_id=self.cls(other, "X").id)

    def test_class_cannot_pay_and_receive(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        with self.assertRaises(ValidationError):
            self.rule(fund, class_ids=[Command.set((a | b).ids)], recipient_class_ids=[Command.set(a.ids)])
        ok = self.rule(fund, class_ids=[Command.set(a.ids)], recipient_class_ids=[Command.set(b.ids)])
        self.assertEqual(ok.recipient_class_ids, b)

    def test_cover_class_cannot_pay_but_may_receive(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        with self.assertRaises(ValidationError):
            self.rule(fund, kind="performance", class_ids=[Command.set(a.ids)], cover_class_id=a.id)
        ok = self.rule(
            fund, kind="performance", class_ids=[Command.set(a.ids)], cover_class_id=b.id,
            recipient_share=1, recipient_class_ids=[Command.set(b.ids)],
        )
        self.assertEqual(ok.cover_class_id, b)

    def test_change_of_fund_clears_foreign_classes(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        other = self.make_fund(classes=[{"code": "X"}])
        rule = self.Rule.new({"fund_id": fund.id, "class_ids": [Command.set(self.cls(fund, "A").ids)]})
        rule.fund_id = other
        rule._onchange_fund_id_classes()
        self.assertFalse(rule.class_ids)

    def test_crystallisation_at_every_valuation(self):
        # Jako test_crystallisation_updates_hwm_and_clears_accrual, ale ocenění uprostřed měsíce:
        # po prvním se posune HWM a naběhlá odměna se vynuluje, druhé ocenění začíná z nové hodnoty.
        fund = self.make_fund(classes=[{"code": "A"}], launch="2026-12-31")
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        self.rule(
            fund, kind="performance", crystallisation="valuation", expense_role="expense_performance",
            class_ids=[Command.set(self.cls(fund, "A").ids)],
            version_ids=[(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit", "initial_reference": 100})],
        )
        self.common_result(fund, "v1", "2027-01-20", 100)
        first = self.run_to_posted(self.valuation(fund, date(2027, 1, 25)))
        self.assertAlmostEqual(first.fee_line_ids.amount, 20, places=2)
        self.assertAlmostEqual(self.result(first, "A").perf_hwm, 108, places=4)
        self.assertEqual(self.result(first, "A").perf_accrued, 0)
        self.common_result(fund, "v2", "2027-02-10", 10)
        second = self.valuation(fund, date(2027, 2, 15))
        second.action_compute()
        self.assertAlmostEqual(second.fee_line_ids.amount, 2, places=2)

    def test_calendar_crystallisation_does_not_fire_mid_month(self):
        fund = self.make_fund(classes=[{"code": "A"}], launch="2026-12-31")
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        self.rule(
            fund, kind="performance", crystallisation="month", expense_role="expense_performance",
            class_ids=[Command.set(self.cls(fund, "A").ids)],
            version_ids=[(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit", "initial_reference": 100})],
        )
        self.common_result(fund, "v1", "2027-01-20", 100)
        first = self.run_to_posted(self.valuation(fund, date(2027, 1, 25)))
        self.assertAlmostEqual(self.result(first, "A").perf_accrued, 20, places=2)
