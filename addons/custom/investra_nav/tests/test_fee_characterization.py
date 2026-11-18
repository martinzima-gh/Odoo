"""ZJ-12 krok 1: charakterizační testy dnešního chování před změnou (výsledky se nesmí změnit, dokud je ZJ-12 neschválí)."""

import json
from datetime import date

from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFeeCharacterization(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def test_average_fk_rule_with_two_classes(self):
        # ZJ-12 B.6: pravidlo průměrného FK s více třídami dřív vytvořilo řádek rozpisu za každou třídu (doklad jeden).
        # Od kroku 3 je to jedna položka dopočtu: jeden řádek, jeden doklad.
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 500000, 500)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", 500000, 500)
        rule = self.Rule.create({
            "fund_id": fund.id, "name": "Fixní", "kind": "periodic", "base_source": "average_fk",
            "expense_role": "expense_management", "class_ids": [(6, 0, fund.class_ids.ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})],
        })
        january = self.valuation(fund, date(2027, 1, 31))
        january.action_compute()
        lines = january.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.assertEqual(lines.mapped("amount"), [3100.0])
        events = january.event_ids.filtered(lambda e: f":fee:{rule.id}:" in e.key)
        self.assertEqual(len(events), 1, "doklad se nezdvojil (stejný klíč)")

    def test_average_fk_two_classes_next_valuation_deducts_booked_twice(self):
        # ZJ-12 B.6: únorové ocenění dřív odečetlo zaúčtovanou lednovou úplatu 3 100 dvakrát (6 200). Od kroku 3 jednou.
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 500000, 500)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", 500000, 500)
        rule = self.Rule.create({
            "fund_id": fund.id, "name": "Fixní", "kind": "periodic", "base_source": "average_fk",
            "expense_role": "expense_management", "class_ids": [(6, 0, fund.class_ids.ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})],
        })
        self.run_to_posted(self.valuation(fund, date(2027, 1, 31)))
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        detail = json.loads(february.fee_line_ids.filtered(lambda l: l.rule_id == rule)[0].detail)
        self.assertAlmostEqual(float(detail["booked"]), 3100.0, places=2)
