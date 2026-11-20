from datetime import date
from decimal import Decimal

from odoo.tests import tagged

from .common import DerivativeCase


@tagged("post_install", "-at_install")
class TestDerivativePortfolioClass(DerivativeCase):
    """ZJ-09 A7: forward v portfoliu třídy B mění jen třídu B (zajištění třídy), příklad DE-04 z docs/navrh-fx-derivaty.md.

    Fond se třídami A a B po 25 000 000 Kč; forward prodej 1 000 000 EUR za 24 900 000 Kč k 31. 12. 2025 v portfoliu B.
    """

    def setUp(self):
        super().setUp()
        self.example_rates()
        self.b = self.env["investra.fund.class"].create({"fund_id": self.fund.id, "code": "B", "name": "B",
                                                         "currency_id": self.czk.id})
        self.subscribe(self.cls(self.fund, "A"), "2025-01-01", 25_000_000, 250_000)
        self.subscribe(self.b, "2025-01-01", 25_000_000, 250_000)
        self.class_b = self.env["investra.fund.portfolio"].create({
            "fund_id": self.fund.id, "name": "Zajištění B", "business_model": "trading", "class_id": self.b.id})

    def capitals(self, valuation):
        return {line.class_id.code: Decimal(str(line.capital)) for line in valuation.class_line_ids}

    def forward_in(self, portfolio):
        return self.env["investra.derivative"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "partner_id": self.bank.id, "kind": "forward", "trade_date": "2025-09-30",
            "contract_ref": "FX-B", "portfolio_id": portfolio.id,
            "leg_ids": [self.leg("2025-12-31", self.czk, 24_900_000, self.eur, 1_000_000)],
        })

    def post(self, day):
        return self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))

    def test_forward_in_class_portfolio_changes_only_class(self):
        forward = self.forward_in(self.class_b)
        forward.action_agree()
        self.assertEqual(set(forward.event_id.move_id.line_ids.investra_class_id.mapped("code")), {"B"})
        first = self.post("2025-10-31")
        self.assertEqual(self.capitals(first), {"A": Decimal("25000000.00"), "B": Decimal("25166304.35")})
        self.assertAlmostEqual(self.result(first, "B").other_amount, 166304.35, places=2)
        second = self.post("2025-11-30")
        self.assertEqual(self.capitals(second), {"A": Decimal("25000000.00"), "B": Decimal("24833695.65")})
        forward.leg_ids.action_settle()
        settlement = forward.leg_ids.settlement_event_id.move_id
        self.assertFalse(settlement.line_ids.filtered(lambda l: l.account_id.account_type == "asset_cash").investra_class_id)
        third = self.post("2025-12-31")
        self.assertEqual(self.capitals(third), {"A": Decimal("25000000.00"), "B": Decimal("24700000.00")})
        self.assertEqual(third.check_ids.filtered(lambda c: c.status == "stop"), self.env["investra.valuation.check"])

    def test_shared_forward_lines_without_classification(self):
        """Derivát sdíleného portfolia: řádky bez zařazení a třídy jako dřív (otisk dřívějších dokladů)."""
        forward = self.forward_in(self.fund.portfolio_ids.filtered(lambda p: not p.class_id)[:1])
        forward.action_agree()
        lines = forward.event_id.move_id.line_ids
        self.assertFalse(lines.investra_classification_id)
        self.assertFalse(lines.investra_class_id)
