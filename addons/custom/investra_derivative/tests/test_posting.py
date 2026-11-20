from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from ..models.posting import CLEARING, ROLES
from .common import DerivativeCase

FWD = ROLES["forward"]


@tagged("post_install", "-at_install")
class TestDerivativePosting(DerivativeCase):
    """Sjednání, vypořádání nohy a storna (DE-03) podle příkladu v docs/navrh-fx-derivaty.md (rok 2025)."""

    def setUp(self):
        super().setUp()
        self.example_rates()
        self.subscribe(self.cls(self.fund, "A"), "2025-01-01", 50_000_000, 500_000)

    def agreed(self, factory, **kwargs):
        derivative = factory(year=2025, **kwargs)
        derivative.action_agree()
        return derivative

    def assert_balanced(self, derivative):
        events = self.env["investra.accounting.event"].sudo().search(
            [("res_model", "=", "investra.derivative"), ("res_id", "=", derivative.id)])
        self.assertTrue(events)
        for move in events.move_id | events.reversal_move_id:
            self.assertEqual(round(sum(move.line_ids.mapped("debit")), 2), round(sum(move.line_ids.mapped("credit")), 2))

    # --- sjednání ---------------------------------------------------------------------------------------------------

    def test_agree_books_off_balance_only(self):
        before = self.net_assets()
        forward = self.forward(year=2025)
        preview = forward._preview_documents()
        forward.action_agree()
        self.assertEqual(forward.state, "agreed")
        move = forward.event_id.move_id
        self.assertEqual(move.date.isoformat(), "2025-09-30")
        # Příklad: MD pohledávka 24 900 000; D závazek 25 000 000; MD vyrovnávací 100 000.
        self.assertEqual(self.move_rows(move), [
            ("953100", 24_900_000.0, 0.0), ("954100", 0.0, 25_000_000.0), ("992000", 100_000.0, 0.0)])
        self.assertEqual(set(move.line_ids.account_id.mapped("account_type")), {"off_balance"})
        payable = move.line_ids.filtered(lambda l: l.account_id.code == "954100")
        self.assertEqual((payable.currency_id, payable.amount_currency), (self.eur, -1_000_000.0))
        self.assertEqual(self.net_assets(), before)
        leg = forward.leg_ids
        self.assertAlmostEqual(leg.b0, -100_000.0, places=2)
        self.assertEqual((leg.buy_rate0, leg.sell_rate0), (1.0, 25.0))
        # Náhled je ze stejné funkce jako doklad.
        self.assertEqual(sorted((dr, cr) for _acc, dr, cr, _ccy, *_ in preview[0][2]),
                         sorted((Decimal(str(l.debit)), Decimal(str(l.credit))) for l in move.line_ids))
        self.assertTrue(self.env["investra.portfolio.classification"]._valid(
            forward.portfolio_id, forward.instrument_id, forward.trade_date))
        self.assert_balanced(forward)

    def test_agree_needs_rate_and_preparer(self):
        forward = self.forward(year=2024, ref="FX-OLD")
        with self.assertRaises(UserError):
            forward.action_agree()  # chybí kurz EUR k 30. 9. 2024
        self.assertEqual(forward.state, "draft")
        with self.assertRaises(AccessError):
            self.forward(year=2025).with_user(self.approver).action_agree()

    def test_swap_and_spot_use_their_own_accounts(self):
        swap = self.agreed(self.swap, ref="SWAP-1")
        codes = set(swap.event_id.move_id.line_ids.account_id.mapped("code"))
        self.assertEqual(codes, {"953200", "954200", "992000"})
        spot = self.derivative("spot", [self.leg("2025-10-02", self.eur, 1_000_000, self.czk, 25_050_000)],
                               ref="SPOT-1", day=2025)
        spot.action_agree()
        self.assertEqual(self.move_rows(spot.event_id.move_id), [
            ("943000", 25_000_000.0, 0.0), ("944000", 0.0, 25_050_000.0), ("992000", 50_000.0, 0.0)])
        spot.leg_ids.action_settle()
        # Kurz 2. 10. je 25,00: fond zaplatil o 50 000 víc, než je hodnota eur → náklad na devizové operace spotu.
        self.assertEqual(self.role_balance("loss_fx_spot"), Decimal("50000.00"))
        self.assertEqual(self.role_balance("fx_spot_asset") + self.role_balance("fx_spot_liability"), Decimal("0.00"))
        self.assertEqual(spot.state, "settled")

    # --- vypořádání -------------------------------------------------------------------------------------------------

    def test_forward_settlement_without_valuation(self):
        """Bez mezilehlého ocenění jde celý výsledek −300 000 do dne vypořádání; zápisy toků podle příkladu."""
        before = self.net_assets()
        forward = self.agreed(self.forward)
        leg = forward.leg_ids
        preview = forward._preview_documents()
        leg.action_settle()
        move = leg.settlement_event_id.move_id
        self.assertEqual(move.date.isoformat(), "2025-12-31")
        self.assertEqual(self.move_rows(move), sorted([
            ("313100", 0.0, 300_000.0), ("619100", 300_000.0, 0.0),             # dopočet RH na V = −300 000
            ("131100", 24_900_000.0, 0.0), ("131100", 0.0, 25_200_000.0),       # banka CZK a EUR (1 000 000 EUR)
            ("313100", 300_000.0, 0.0),                                         # zrušení RH
        ]))
        self.assertEqual(self.move_rows(leg.offbalance_event_id.move_id), [
            ("953100", 0.0, 24_900_000.0), ("954100", 25_000_000.0, 0.0), ("992000", 0.0, 100_000.0)])
        eur = move.line_ids.filtered(lambda l: l.account_id.code == "131100" and l.currency_id == self.eur)
        self.assertEqual(eur.amount_currency, -1_000_000.0)
        self.assertEqual(sorted((dr, cr) for _acc, dr, cr, _ccy, *_ in preview[0][2]),
                         sorted((Decimal(str(l.debit)), Decimal(str(l.credit))) for l in move.line_ids))
        self.assertEqual(len(preview), 2)
        self.assertEqual((forward.state, leg.state), ("settled", "settled"))
        self.assertEqual(self.net_assets() - before, Decimal("-300000.00"))
        for role in (FWD["asset"], FWD["liability"], FWD["receivable"], FWD["payable"], CLEARING):
            self.assertEqual(self.role_balance(role), Decimal("0.00"), role)
        self.assert_balanced(forward)

    def test_swap_legs_settle_in_order(self):
        swap = self.agreed(self.swap)
        near, far = swap.leg_ids.sorted("settlement_date")
        with self.assertRaises(UserError):
            far.action_settle()
        near.action_settle()
        self.assertEqual((swap.state, near.state, far.state), ("agreed", "settled", "open"))
        # Blízká noha při kurzu 25,00 je prostá směna; zůstává RH vzdálené nohy ke 2. 10. (kurz 25,00, zbývá 90 z 92 dnů).
        expected = Decimal("-100000") + Decimal("100000") * 90 / 92
        booked = self.role_balance("derivative_swap") + self.role_balance("derivative_swap_liability")
        self.assertEqual(booked, expected.quantize(Decimal("0.01")))
        self.assertEqual(self.role_balance("offbalance_swap_receivable"), Decimal("24900000.00"))
        far.action_settle()
        self.assertEqual(swap.state, "settled")
        for role in ("derivative_swap", "derivative_swap_liability", "offbalance_swap_receivable",
                     "offbalance_swap_payable", CLEARING):
            self.assertEqual(self.role_balance(role), Decimal("0.00"), role)
        # Celkový výsledek swapu: blízká noha 0, vzdálená 24 900 000 − 1 000 000 × 25,20.
        self.assertEqual(self.role_balance("loss_derivative_swap") + self.role_balance("gain_derivative_swap"),
                         Decimal("300000.00"))
        self.assert_balanced(swap)

    def test_settlement_not_before_settlement_date(self):
        self.rate("2026-09-30", 25)
        forward = self.forward(year=2026, ref="FX-FUTURE")
        forward.action_agree()
        with self.assertRaises(UserError) as error:
            forward.leg_ids.action_settle()
        self.assertIn("nejdřív v den vypořádání", str(error.exception))

    def test_settlement_bank_account_must_be_fund_bank(self):
        forward = self.agreed(self.forward)
        other = self.env["investra.account.role"].account_for(self.fund.company_id, "income_other")
        with self.assertRaises(UserError):
            forward.leg_ids.action_settle(buy_account=other)

    def test_settle_wizard_preview_and_confirm(self):
        forward = self.agreed(self.forward)
        wizard = self.env["investra.derivative.settle.wizard"].with_user(self.preparer).create({"leg_id": forward.leg_ids.id})
        self.assertEqual(wizard.buy_account_id.code, "131100")
        self.assertIn("300", wizard.preview)
        wizard.action_confirm()
        self.assertEqual(forward.state, "settled")

    # --- storna -----------------------------------------------------------------------------------------------------

    def test_reverse_agreed_contract(self):
        forward = self.agreed(self.forward)
        with self.assertRaises(UserError):
            forward.action_reverse(" ")
        forward.action_reverse("Chybně zadaná částka")
        self.assertEqual((forward.state, forward.reversal_reason), ("reversed", "Chybně zadaná částka"))
        self.assertEqual(forward.event_id.state, "reversed")
        for role in (FWD["receivable"], FWD["payable"], CLEARING):
            self.assertEqual(self.role_balance(role), Decimal("0.00"), role)
        self.assertIn("stornováno", forward.posting_preview)
        self.assert_balanced(forward)

    def test_reverse_settlement_and_settle_again(self):
        before = self.net_assets()
        forward = self.agreed(self.forward)
        leg = forward.leg_ids
        leg.action_settle()
        forward.action_reverse_settlement("Vypořádáno na špatný účet")
        self.assertEqual((forward.state, leg.state), ("agreed", "open"))
        self.assertFalse(leg.settlement_event_id)
        self.assertEqual(self.net_assets(), before)
        self.assertEqual(self.role_balance(FWD["receivable"]), Decimal("24900000.00"))
        leg.action_settle()
        self.assertEqual(forward.state, "settled")
        self.assertEqual(self.net_assets() - before, Decimal("-300000.00"))

    def test_reverse_settled_contract_clears_everything(self):
        before = self.net_assets()
        swap = self.agreed(self.swap)
        for leg in swap.leg_ids.sorted("settlement_date"):
            leg.action_settle()
        swap.action_reverse("Smlouva nebyla uzavřena")
        self.assertEqual(swap.state, "reversed")
        self.assertEqual(self.net_assets(), before)
        for role in list(ROLES["swap"].values()) + [CLEARING]:
            self.assertEqual(self.role_balance(role), Decimal("0.00"), role)
        self.assert_balanced(swap)

    def test_reversal_respects_valuation_lock(self):
        forward = self.agreed(self.forward)
        valuation = self.valuation(self.fund, "2025-10-31")
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError) as error:
            forward.action_reverse("Pokus")
        self.assertIn("ocenění", str(error.exception))
        self.assertEqual(forward.state, "agreed")

    # --- fond v EUR ------------------------------------------------------------------------------------------------

    def test_fund_in_eur(self):
        """Fond s funkční měnou EUR prodává 25 000 000 CZK za 1 000 000 EUR; kurz CZK/EUR = 1 / kurz ČNB."""
        # Kniha v EUR bere kurzy z ECB (jednotky měny za 1 EUR).
        for day, value in (("2025-09-30", "25.00"), ("2025-12-31", "25.20")):
            self.env["investra.rate"]._store("ecb", date.fromisoformat(day), {"CZK": (Decimal(1), Decimal(value))}, f"ecb{day}")
        fund = self.make_fund(currency=self.eur, launch="2024-12-31", classes=[{"code": "A", "currency_id": self.eur.id}])
        self.subscribe(self.cls(fund, "A"), "2025-01-01", 2_000_000, 20_000)
        before = self.net_assets(fund)
        forward = self.derivative(
            "forward", [self.leg("2025-12-31", self.eur, 1_000_000, self.czk, 25_000_000)], fund=fund, ref="FX-EUR", day=2025)
        forward.action_agree()
        # Při sjednání (25,00): pohledávka 1 000 000 EUR, závazek 25 000 000 CZK = 1 000 000 EUR, body 0.
        self.assertEqual(self.role_balance(FWD["receivable"], fund), Decimal("1000000.00"))
        self.assertEqual(self.role_balance(FWD["payable"], fund), Decimal("-1000000.00"))
        self.assertAlmostEqual(forward.leg_ids.b0, 0.0, places=2)
        forward.leg_ids.action_settle()
        # Vypořádání při 25,20: 25 000 000 CZK = 992 063,49 EUR; fond získal 1 000 000 − 992 063,49.
        self.assertEqual(self.net_assets(fund) - before, Decimal("7936.51"))
        self.assertEqual(self.role_balance("gain_derivative", fund), Decimal("-7936.51"))
        for role in (FWD["asset"], FWD["liability"], FWD["receivable"], FWD["payable"], CLEARING):
            self.assertEqual(self.role_balance(role, fund), Decimal("0.00"), role)
