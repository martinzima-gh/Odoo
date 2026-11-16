import json
from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DerivativeCase


@tagged("post_install", "-at_install")
class TestDerivativeValuation(DerivativeCase):
    """FX derivát v ocenění (DE-04): tabulka příkladu z docs/navrh-fx-derivaty.md na haléř (rok 2025)."""

    def setUp(self):
        super().setUp()
        self.example_rates()
        self.subscribe(self.cls(self.fund, "A"), "2025-01-01", 50_000_000, 500_000)

    def agreed_forward(self, **kwargs):
        forward = self.forward(year=2025, **kwargs)
        forward.action_agree()
        return forward

    def computed(self, day, fund=None):
        valuation = self.valuation(fund or self.fund, date.fromisoformat(day))
        valuation.action_compute()
        return valuation

    def event_rows(self, valuation, name):
        event = valuation.event_ids.filtered(lambda e: e.name.startswith(name) and e.state != "discarded")
        self.assertEqual(len(event), 1, name)
        return self.move_rows(event.move_id)

    def check(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code).status

    def assert_capital_matches_ledger(self, valuation):
        """FK = aktiva − závazky z hlavní knihy včetně návrhů ocenění; pozice sedí na hlavní knihu."""
        self.assertEqual(Decimal(str(valuation.fund_capital)), valuation._net_assets())
        self.assertEqual(self.check(valuation, "positions_ledger"), "ok")
        self.assertEqual(self.check(valuation, "classes_sum"), "ok")

    # --- příklad -----------------------------------------------------------------------------------------------------

    def test_example_two_valuations_and_settlement(self):
        start = self.net_assets()
        forward = self.agreed_forward()
        leg = forward.leg_ids

        first = self.computed("2025-10-31")
        line = first.derivative_line_ids
        self.assertEqual((line.computed_value, line.used_value, line.booked_before, line.change),
                         (166304.35, 166304.35, 0.0, 166304.35))
        self.assertFalse(line.has_manual)
        inputs = json.loads(line.inputs)[0]
        self.assertEqual((inputs["sell_rate"], inputs["value"], inputs["days_left"], inputs["days_total"]),
                         ("24.8", "100000.00", 61, 92))
        self.assertEqual(self.event_rows(first, "Přecenění derivátů"), [("313000", 166304.35, 0.0), ("719100", 0.0, 166304.35)])
        self.assertEqual(self.event_rows(first, "Přepočet podrozvahy"), [("954100", 200000.0, 0.0), ("992000", 0.0, 200000.0)])
        row = first.portfolio_line_ids.filtered(lambda r: r.kind == "derivative")
        self.assertEqual((row.instrument_id, row.fair_value), (forward.instrument_id, 166304.35))
        self.assert_capital_matches_ledger(first)
        self.assertEqual(first._net_assets(), start + Decimal("166304.35"))
        for code in ("derivative_settled", "derivative_rate", "derivative_manual_evidence", "derivative_manual_difference",
                     "derivative_draft"):
            self.assertEqual(self.check(first, code), "ok", code)
        self.run_to_posted(first)
        self.assertEqual(self.net_assets(), start + Decimal("166304.35"))

        second = self.computed("2025-11-30")
        line = second.derivative_line_ids
        self.assertEqual((line.used_value, line.booked_before, line.change), (-166304.35, 166304.35, -332608.70))
        self.assertEqual(self.event_rows(second, "Přecenění derivátů"), [
            ("313000", 0.0, 166304.35), ("313100", 0.0, 166304.35), ("619100", 332608.70, 0.0)])
        self.assertEqual(self.event_rows(second, "Přepočet podrozvahy"), [("954100", 0.0, 300000.0), ("992000", 300000.0, 0.0)])
        self.assertEqual(second.portfolio_line_ids.filtered(lambda r: r.kind == "derivative").fair_value, -166304.35)
        self.assert_capital_matches_ledger(second)
        self.run_to_posted(second)
        self.assertEqual(self.net_assets(), start - Decimal("166304.35"))

        leg.action_settle()
        self.assertEqual(self.move_rows(leg.settlement_event_id.move_id), sorted([
            ("619100", 133695.65, 0.0), ("313100", 0.0, 133695.65),
            ("131100", 24_900_000.0, 0.0), ("131100", 0.0, 25_200_000.0), ("313100", 300_000.0, 0.0),
        ]))
        self.assertEqual(self.move_rows(leg.offbalance_event_id.move_id), [
            ("953100", 0.0, 24_900_000.0), ("954100", 25_100_000.0, 0.0), ("992000", 0.0, 200_000.0)])
        self.assertEqual(self.net_assets(), start - Decimal("300000.00"))
        self.assertEqual(self.role_balance("loss_derivative") + self.role_balance("gain_derivative"), Decimal("300000.00"))
        for role in ("derivative", "derivative_liability", "offbalance_forward_receivable", "offbalance_forward_payable",
                     "offbalance_clearing"):
            self.assertEqual(self.role_balance(role), Decimal("0.00"), role)

        third = self.computed("2025-12-31")
        self.assertFalse(third.derivative_line_ids)
        self.assertFalse(third.event_ids.filtered(lambda e: "deriv" in e.name.lower() or "podrozvah" in e.name.lower()))
        self.assertEqual(self.check(third, "derivative_settled"), "ok")
        self.assert_capital_matches_ledger(third)

    def test_fair_value_is_zero_on_trade_date(self):
        self.agreed_forward()
        valuation = self.computed("2025-09-30")
        line = valuation.derivative_line_ids
        self.assertEqual((line.computed_value, line.change), (0.0, 0.0))
        self.assertFalse(valuation.event_ids.filtered(lambda e: e.name.startswith(("Přecenění derivátů", "Přepočet podrozvahy"))))
        self.assert_capital_matches_ledger(valuation)

    def test_recompute_replaces_proposals(self):
        self.agreed_forward()
        valuation = self.computed("2025-10-31")
        valuation.action_compute()
        valuation.action_compute()
        self.assertEqual(len(valuation.derivative_line_ids), 1)
        self.assertEqual(len(valuation.portfolio_line_ids.filtered(lambda r: r.kind == "derivative")), 1)
        self.assertEqual(self.event_rows(valuation, "Přecenění derivátů"), [("313000", 166304.35, 0.0), ("719100", 0.0, 166304.35)])
        drafts = self.env["account.move"].sudo().search([
            ("company_id", "=", self.fund.company_id.id), ("state", "=", "draft"), ("ref", "like", "Přecenění derivátů")])
        self.assertEqual(len(drafts), 1)

    def test_cancelled_draft_removes_proposals(self):
        self.agreed_forward()
        valuation = self.computed("2025-10-31")
        valuation.action_cancel_draft()
        self.assertFalse(self.env["account.move"].sudo().search([
            ("company_id", "=", self.fund.company_id.id), ("ref", "like", "Přecenění derivátů")]))
        self.assertEqual(self.role_balance("derivative"), Decimal("0.00"))

    def test_overdue_leg_stops_valuation(self):
        self.agreed_forward()
        valuation = self.computed("2025-12-31")
        self.assertEqual(self.check(valuation, "derivative_settled"), "stop")
        self.assertEqual(valuation.derivative_line_ids.used_value, -300000.0)

    def test_draft_contract_warns(self):
        self.forward(year=2025)
        valuation = self.computed("2025-10-31")
        self.assertEqual(self.check(valuation, "derivative_draft"), "warning")
        self.assertFalse(valuation.derivative_line_ids)

    def test_missing_rate_stops_valuation(self):
        self.rate("2025-09-30", 22, currency="USD")
        forward = self.derivative("forward", [self.leg("2025-12-31", self.czk, 21_900_000, self.usd, 1_000_000)],
                                  ref="FX-USD", day=2025)
        forward.action_agree()
        # Kurz USD je jen z 30. 9.; k 31. 10. je starší než povolených 5 dnů (Platnost kurzů), tedy chybí.
        valuation = self.computed("2025-10-31")
        self.assertEqual(self.check(valuation, "derivative_rate"), "stop")
        self.assertTrue(valuation.derivative_line_ids.problem)
        self.assertFalse(valuation.event_ids.filtered(lambda e: e.name.startswith("Přecenění derivátů")))

    # --- ruční hodnota ---------------------------------------------------------------------------------------------

    def manual(self, forward, day, amount, currency=None, **vals):
        return self.env["investra.derivative.value"].with_user(self.preparer).create({
            "derivative_id": forward.id, "date": day, "amount": amount, "currency_id": (currency or self.czk).id,
            "source": "Potvrzení banky", **vals,
        })

    def test_manual_value_takes_precedence_only_for_its_date(self):
        forward = self.agreed_forward()
        self.manual(forward, "2025-10-31", 6000, currency=self.eur, reason="Ocenění protistrany")
        first = self.computed("2025-10-31")
        line = first.derivative_line_ids
        # 6 000 EUR × 24,80 = 148 800; spočtená 166 304,35; rozdíl −17 504,35 je v toleranci 0,10 % z 24 900 000.
        self.assertTrue(line.has_manual)
        self.assertEqual((line.manual_value, line.computed_value, line.difference, line.used_value),
                         (148800.0, 166304.35, -17504.35, 148800.0))
        self.assertEqual(self.event_rows(first, "Přecenění derivátů"), [("313000", 148800.0, 0.0), ("719100", 0.0, 148800.0)])
        self.assertEqual(self.check(first, "derivative_manual_evidence"), "ok")
        self.assertEqual(self.check(first, "derivative_manual_difference"), "ok")
        self.assert_capital_matches_ledger(first)
        self.run_to_posted(first)
        second = self.computed("2025-11-30")
        line = second.derivative_line_ids
        self.assertFalse(line.has_manual)
        self.assertEqual((line.used_value, line.booked_before, line.change), (-166304.35, 148800.0, -315104.35))

    def test_manual_value_checks(self):
        forward = self.agreed_forward()
        value = self.manual(forward, "2025-10-31", 500000)
        valuation = self.computed("2025-10-31")
        self.assertEqual(self.check(valuation, "derivative_manual_evidence"), "stop")
        self.assertEqual(self.check(valuation, "derivative_manual_difference"), "warning")
        value.reason = "Model banky"
        self.fund.derivative_tolerance_pct = 5
        valuation.action_compute()
        self.assertEqual(self.check(valuation, "derivative_manual_evidence"), "ok")
        self.assertEqual(self.check(valuation, "derivative_manual_difference"), "ok")

    def test_used_manual_value_is_frozen(self):
        forward = self.agreed_forward()
        value = self.manual(forward, "2025-10-31", 150000, reason="Banka")
        valuation = self.computed("2025-10-31")
        value.amount = 151000  # spočtené ocenění ještě nic nezamyká
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            value.amount = 152000
        with self.assertRaises(UserError):
            value.unlink()

    # --- swap a fond v EUR -----------------------------------------------------------------------------------------

    def test_swap_far_leg_after_near_settlement(self):
        swap = self.swap(year=2025)
        swap.action_agree()
        swap.leg_ids.sorted("settlement_date")[0].action_settle()
        valuation = self.computed("2025-10-31")
        line = valuation.derivative_line_ids
        # Zaúčtováno po vypořádání blízké nohy: RH vzdálené nohy ke 2. 10. = −100 000 + 100 000 × 90 / 92.
        self.assertEqual((line.used_value, line.booked_before), (166304.35, -2173.91))
        self.assertEqual(self.event_rows(valuation, "Přecenění derivátů"), [
            ("313200", 166304.35, 0.0), ("313300", 2173.91, 0.0), ("719200", 0.0, 168478.26)])
        self.assertEqual(self.event_rows(valuation, "Přepočet podrozvahy"), [("954200", 200000.0, 0.0), ("992000", 0.0, 200000.0)])
        self.assert_capital_matches_ledger(valuation)

    def test_fund_in_eur(self):
        for day, value in (("2025-09-30", "25.00"), ("2025-10-31", "24.80")):
            self.env["investra.rate"]._store("ecb", date.fromisoformat(day), {"CZK": (Decimal(1), Decimal(value))}, f"ecb{day}")
        fund = self.make_fund(currency=self.eur, launch="2024-12-31", classes=[{"code": "A", "currency_id": self.eur.id}])
        self.subscribe(self.cls(fund, "A"), "2025-01-01", 2_000_000, 20_000)
        forward = self.derivative(
            "forward", [self.leg("2025-12-31", self.eur, 1_000_000, self.czk, 25_000_000)], fund=fund, ref="FX-EUR", day=2025)
        forward.action_agree()
        valuation = self.computed("2025-10-31", fund)
        line = valuation.derivative_line_ids
        # 1 000 000 EUR − 25 000 000 CZK / 24,80 = −8 064,52 EUR; B0 = 0.
        self.assertEqual((line.used_value, line.change), (-8064.52, -8064.52))
        self.assertEqual(self.event_rows(valuation, "Přecenění derivátů"), [("313100", 0.0, 8064.52), ("619100", 8064.52, 0.0)])
        self.assertEqual(self.event_rows(valuation, "Přepočet podrozvahy"), [("954100", 0.0, 8064.52), ("992000", 8064.52, 0.0)])
        self.assert_capital_matches_ledger(valuation)

    # --- fond bez derivátů ----------------------------------------------------------------------------------------

    def test_fund_without_derivatives_is_untouched(self):
        valuation = self.computed("2025-10-31")
        self.assertFalse(valuation.derivative_line_ids)
        self.assertFalse(valuation.check_ids.filtered(lambda c: c.code.startswith("derivative_")))
        self.assertFalse(valuation.event_ids.filtered(lambda e: e.name.startswith(("Přecenění derivátů", "Přepočet podrozvahy"))))
        self.assertEqual(Decimal(str(valuation.fund_capital)), Decimal("50000000.00"))
