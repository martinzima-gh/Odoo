from datetime import date

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from . import test_trade_recognition as base
from .common import NavCase


@tagged("post_install", "-at_install")
class TestTradeReverse(NavCase):
    """Storno vypořádání, storno a oprava obchodu, pojistka kurzu (rozhodnutí 2026-11-12 „Storno a oprava obchodu“).

    Sjednání 2. 3., vypořádání 5. 4. 2031 jako v testech zachycení obchodu.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2031-03-01", 100000, 1000)

    instrument = base.TestTradeRecognition.instrument
    trade = base.TestTradeRecognition.trade
    balance = base.TestTradeRecognition.balance
    price = base.TestTradeRecognition.price
    settlement_mode = base.TestTradeRecognition.settlement_mode

    def booked(self, *args, **kwargs):
        trade = self.trade(*args, **kwargs)
        trade.with_user(self.preparer).action_book()
        return trade

    def settled(self, *args, **kwargs):
        trade = self.booked(*args, **kwargs)
        if trade.state == "unsettled":  # Vypořádání v den sjednání je hotové už zaúčtováním.
            trade.with_user(self.preparer).action_settle()
        return trade

    def holdings(self, day="2031-12-31"):
        return self.env["investra.trade"].sudo()._holdings(self.fund, date.fromisoformat(day))

    # --- storno vypořádání -----------------------------------------------------------------------------------

    def test_settlement_reversal_and_new_settlement(self):
        trade = self.settled(self.instrument())
        self.assertEqual(self.balance("bank"), 100000 - 1000)
        old = trade.settlement_event_id
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).action_reverse_settlement(" ")
        result = trade.with_user(self.preparer).action_reverse_settlement("Chybné datum vypořádání")
        self.assertEqual(result, trade)
        self.assertEqual((trade.state, trade.settlement_event_id.id), ("unsettled", False))
        self.assertEqual(trade.settlement_reversal_reason, "Chybné datum vypořádání")
        self.assertEqual(old.state, "reversed")
        self.assertEqual(old.reversal_move_id.date, date(2031, 4, 5))
        self.assertEqual(self.balance("bank"), 100000)
        self.assertEqual(self.balance("unsettled_payable"), -1000)
        self.assertEqual(self.balance("instrument_debt"), 1000)
        log = self.env["investra.approval.log"].sudo().search([("res_model", "=", trade._name), ("res_id", "=", trade.id)])
        self.assertEqual(log.activity, "trade_reverse")
        # Oprava data a nové vypořádání.
        trade.with_user(self.preparer).write({"settlement_date": "2031-04-06"})
        trade.with_user(self.preparer).action_settle()
        self.assertEqual(trade.state, "settled")
        self.assertNotEqual(trade.settlement_event_id, old)
        self.assertEqual(trade.settlement_event_id.date, date(2031, 4, 6))
        self.assertEqual(self.balance("bank"), 100000 - 1000)
        self.assertEqual(self.balance("unsettled_payable"), 0)
        # Záložka Zaúčtování ukáže i stornované vypořádání.
        self.assertEqual(len(trade._booked_documents()), 3)
        self.assertIn("stornováno", str(trade.posting_preview))

    def test_settlement_reversal_settlement_date_recognition(self):
        self.settlement_mode()
        trade = self.settled(self.instrument(code="equity"))
        self.assertEqual(self.balance("instrument"), 1000)
        trade.with_user(self.preparer).action_reverse_settlement("Chybný kurz")
        self.assertEqual(trade.state, "unsettled")
        self.assertFalse(trade.event_id)
        self.assertFalse(trade.settlement_event_id)
        self.assertEqual(self.balance("instrument"), 0)
        trade.with_user(self.preparer).action_settle()
        self.assertEqual(self.balance("instrument"), 1000)
        self.assertEqual(trade.event_id, trade.settlement_event_id)

    def test_settlement_reversal_needs_deferred_settlement(self):
        trade = self.settled(self.instrument(), settle="2031-03-02")
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).action_reverse_settlement("Chyba")
        unsettled = self.booked(self.instrument(code="equity"))
        with self.assertRaises(UserError):
            unsettled.with_user(self.preparer).action_reverse_settlement("Chyba")

    # --- storno a oprava obchodu -----------------------------------------------------------------------------

    def test_reverse_trade_removes_position_and_postings(self):
        trade = self.settled(self.instrument())
        self.assertTrue(self.holdings())
        result = trade.with_user(self.preparer).action_reverse("Obchod nebyl uzavřen")
        self.assertEqual(result, trade)
        self.assertEqual((trade.state, trade.reversal_reason), ("reversed", "Obchod nebyl uzavřen"))
        self.assertEqual((trade.event_id.state, trade.settlement_event_id.state), ("reversed", "reversed"))
        for role in ("instrument_debt", "unsettled_payable"):
            self.assertEqual(self.balance(role), 0)
        self.assertEqual(self.balance("bank"), 100000)
        self.assertFalse(self.holdings())
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).action_reverse("Podruhé")
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).write({"settlement_date": "2031-04-07"})
        with self.assertRaises(UserError):
            trade.sudo().unlink()
        # Ocenění po stornu: pozice i kniha nulové, kontrola sedí.
        valuation = self.valuation(self.fund, date(2031, 3, 31))
        valuation.with_user(self.preparer).action_compute()
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")

    def test_reverse_unsettled_trade_without_event(self):
        self.settlement_mode()
        trade = self.booked(self.instrument(code="equity"))
        trade.with_user(self.preparer).action_reverse("Zrušeno protistranou")
        self.assertEqual(trade.state, "reversed")
        self.assertFalse(self.holdings())

    def test_correct_makes_linked_draft(self):
        trade = self.settled(self.instrument())
        correction = trade.with_user(self.preparer).action_correct("Cena 101")
        self.assertNotEqual(correction, trade)
        self.assertEqual((correction.state, correction.replaced_id), ("draft", trade))
        self.assertFalse(correction.event_id or correction.settlement_event_id or correction.reversal_reason)
        self.assertEqual((correction.quantity, correction.price, correction.trade_date), (10, 100, date(2031, 3, 2)))
        correction.with_user(self.preparer).write({"price": 101})
        correction.with_user(self.preparer).action_book()
        correction.with_user(self.preparer).action_settle()
        self.assertEqual(self.balance("instrument_debt"), 1010)
        self.assertEqual(self.balance("bank"), 100000 - 1010)

    def test_reverse_buy_blocked_by_later_sale(self):
        instrument = self.instrument()
        buy = self.booked(instrument, settle=False)
        sale = self.booked(instrument, quantity=-4)
        with self.assertRaises(UserError):
            buy.with_user(self.preparer).action_reverse("Chyba")
        self.assertEqual(buy.state, "settled")
        sale.with_user(self.preparer).action_reverse("Prodej se nekonal")
        buy.with_user(self.preparer).action_reverse("Chyba")
        self.assertFalse(self.holdings())

    def test_reverse_blocked_by_valuation_in_approval(self):
        trade = self.settled(self.instrument())
        self.price(trade.instrument_id, date(2031, 3, 31), 100)
        self.run_to_posted(self.valuation(self.fund, date(2031, 3, 31)))
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).action_reverse("Chyba")
        # Vypořádání 5. 4. je po ocenění 31. 3.: storno vypořádání projde.
        trade.with_user(self.preparer).action_reverse_settlement("Chybné datum")
        self.assertEqual(trade.state, "unsettled")
        self.assertEqual(trade.event_id.state, "posted")

    def test_reverse_after_publication_needs_lock_exception(self):
        trade = self.settled(self.instrument(), settle="2031-03-02")
        self.price(trade.instrument_id, date(2031, 3, 31), 100)
        self.run_to_published(self.valuation(self.fund, date(2031, 3, 31)))
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).action_reverse("Chyba")
        self.assertEqual(trade.state, "settled")
        request = self.env["investra.lock.exception.request"].with_user(self.approver).create({
            "company_id": self.fund.company_id.id, "user_id": self.preparer.id, "lock_date": "2031-03-01",
            "end_datetime": "2099-01-01 00:00:00", "reason": "Storno chybného obchodu",
        })
        request.with_user(self.approver2).action_confirm()
        trade.with_user(self.preparer).action_reverse("Chyba")
        self.assertEqual(trade.state, "reversed")

    def test_reverse_with_second_person_goes_through_request(self):
        self.env["investra.approval.matrix"].create({
            "activity": "trade_reverse", "second_person": "yes", "performer_role": "preparer",
            "valid_from": "2001-01-01", "step_ids": [(0, 0, {"sequence": 0, "name": "Kontrola", "role": "approver"})],
        })
        trade = self.settled(self.instrument())
        request = trade.with_user(self.preparer).action_reverse_settlement("Chybný kurz")
        self.assertEqual(request._name, "investra.approval.request")
        self.assertEqual(trade.state, "settled")
        request.with_user(self.approver).action_approve()
        self.assertEqual(trade.state, "unsettled")

    def test_wizard_modes(self):
        trade = self.settled(self.instrument())
        Wizard = self.env["investra.trade.reverse.wizard"].with_user(self.preparer)
        action = Wizard.create({"trade_id": trade.id, "mode": "settlement", "reason": "Datum"}).action_confirm()
        self.assertEqual((action["res_model"], action["res_id"]), ("investra.trade", trade.id))
        self.assertEqual(trade.state, "unsettled")
        action = Wizard.create({"trade_id": trade.id, "mode": "correct", "reason": "Cena"}).action_confirm()
        self.assertEqual(self.env["investra.trade"].browse(action["res_id"]).replaced_id, trade)
        self.assertEqual(trade.state, "reversed")

    def test_reversal_requires_preparer(self):
        trade = self.settled(self.instrument())
        plain = self.env["res.users"].create({
            "name": "plain", "login": "trade_reverse_plain", "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            trade.with_user(plain).action_reverse("Chyba")
        self.assertEqual(trade.state, "settled")

    # --- pojistka kurzu --------------------------------------------------------------------------------------

    def test_home_currency_rate_forced_to_one(self):
        instrument = self.instrument()
        with self.assertRaises(ValidationError):
            self.trade(instrument, fx=2)
        with self.assertRaises(ValidationError):
            self.trade(instrument, settlement_fx_rate=10070)
        trade = self.booked(instrument)
        with self.assertRaises(ValidationError):
            trade.with_user(self.preparer).write({"settlement_fx_rate": 100})
        self.assertFalse(trade.foreign_currency)
        self.assertFalse(trade.settlement_fx_note)

    def test_foreign_settlement_rate_warning(self):
        instrument = self.instrument(self.eur)
        trade = self.trade(instrument, fx=25, settlement_fx_rate=26.5)
        self.assertTrue(trade.foreign_currency)
        self.assertFalse(trade.settlement_fx_note)  # 6 %: běžný pohyb kurzu
        trade.settlement_fx_rate = 28
        self.assertIn("12", trade.settlement_fx_note)  # 12 % nad hranicí 10 %
        trade.with_user(self.preparer).action_book()  # upozornění neblokuje
        self.assertEqual(trade.state, "unsettled")
