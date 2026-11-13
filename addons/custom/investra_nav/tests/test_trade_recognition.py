from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestTradeRecognition(NavCase):
    """Sjednání 2. 3., vypořádání 5. 4. 2031, ocenění 31. 3. a 30. 4.; rok 2031 je jen pro tyto testy."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2031-03-01", 100000, 1000)

    def instrument(self, currency=None, code="bond", model="fair_value", **vals):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Nástroj {self.fund.id} {code}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        }, self.fund))
        self.classify(self.fund, instrument, model)
        return instrument

    def trade(self, instrument, quantity=10, price=100, fx=1, settle="2031-04-05", **vals):
        portfolio = instrument.classification_ids.filtered(lambda c: c.fund_id == self.fund).portfolio_id
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": instrument.id, "trade_date": "2031-03-02",
            "settlement_date": settle, "quantity": quantity, "price": price, "fx_rate": fx, **vals,
        })

    def balance(self, role, day="2031-12-31"):
        account = self.env["investra.account.role"].account_for(self.fund.company_id, role)
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "=", account.id), ("parent_state", "=", "posted"), ("date", "<=", day),
        ])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def price(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()

    def settlement_mode(self):
        self.fund.trade_recognition = "settlement_date"

    def post(self, day):
        valuation = self.valuation(self.fund, day)
        self.run_to_posted(valuation)
        return valuation

    def test_default_is_trade_date(self):
        self.assertEqual(self.fund.trade_recognition, "trade_date")

    def test_trade_events_carry_source_fund_and_type(self):
        """Bod 15: obchod a vypořádání mají zdroj obchod, fond a vlastní druh."""
        trade = self.trade(self.instrument())
        trade._book()
        trade._settle()
        for event, kind in ((trade.event_id, "trade"), (trade.settlement_event_id, "trade_settlement")):
            self.assertEqual(event.event_type, kind)
            self.assertEqual((event.res_model, event.res_id), ("investra.trade", trade.id))
            self.assertEqual(event.fund_id, self.fund)
            self.assertEqual(event.amount, 1000)

    def test_settlement_mode_event_is_trade(self):
        self.settlement_mode()
        trade = self.trade(self.instrument(code="equity"))
        trade._book()
        trade._settle()
        self.assertEqual(trade.event_id, trade.settlement_event_id)
        self.assertEqual(trade.event_id.event_type, "trade")

    def test_foreign_trade_event_has_original_amount(self):
        trade = self.trade(self.instrument(currency=self.eur), fx=25, settle="2031-03-02")
        trade._book()
        self.assertEqual(trade.event_id.amount, 25000)
        self.assertEqual(trade.event_id.foreign_currency_id, self.eur)
        self.assertEqual(trade.event_id.amount_currency, 1000)

    def test_valuation_events_carry_source_and_fund(self):
        instrument = self.instrument()
        self.trade(instrument)._book()
        self.price(instrument, date(2031, 3, 31), 110)
        valuation = self.post(date(2031, 3, 31))
        self.assertTrue(valuation.event_ids)
        for event in valuation.event_ids:
            self.assertEqual((event.res_model, event.res_id, event.fund_id), ("investra.valuation", valuation.id, self.fund))
            self.assertEqual(event.event_type, "valuation")

    def test_trade_date_books_payable_then_bank(self):
        trade = self.trade(self.instrument())
        trade._book()
        self.assertEqual(trade.state, "unsettled")
        self.assertEqual(self.balance("instrument_debt"), 1000)
        self.assertEqual(self.balance("unsettled_payable"), -1000)
        trade._settle()
        self.assertEqual(trade.state, "settled")
        self.assertEqual(self.balance("unsettled_payable"), 0)
        self.assertEqual(self.balance("instrument_debt"), 1000)
        self.assertEqual(self.balance("bank"), 100000 - 1000)

    def test_trade_date_sale_uses_receivable(self):
        instrument = self.instrument()
        self.trade(instrument, settle=False)._book()
        sale = self.trade(instrument, quantity=-4)
        sale._book()
        self.assertEqual(self.balance("unsettled_receivable"), 400)
        sale._settle()
        self.assertEqual(self.balance("unsettled_receivable"), 0)
        self.assertEqual(self.balance("instrument_debt"), 600)

    def test_same_day_goes_straight_to_bank(self):
        trade = self.trade(self.instrument(), settle="2031-03-02")
        trade._book()
        self.assertEqual(trade.state, "settled")
        self.assertEqual(self.balance("unsettled_payable"), 0)
        self.assertEqual(self.balance("bank"), 100000 - 1000)

    def test_settlement_date_books_nothing_until_settled(self):
        self.settlement_mode()
        trade = self.trade(self.instrument(code="equity"))
        trade._book()
        self.assertEqual(trade.state, "unsettled")
        self.assertFalse(trade.event_id)
        self.assertEqual(self.balance("instrument"), 0)
        trade._settle()
        self.assertEqual(self.balance("instrument"), 1000)
        self.assertEqual(self.balance("bank"), 100000 - 1000)

    def test_positions_follow_setting(self):
        trade_mode = self.instrument()
        self.trade(trade_mode)._book()
        Trade = self.env["investra.trade"]
        self.assertEqual(Trade._positions(self.fund, date(2031, 3, 31)), {trade_mode: 10})

    def test_settlement_mode_position_starts_at_settlement(self):
        self.settlement_mode()
        instrument = self.instrument()
        trade = self.trade(instrument)
        trade._book()
        Trade = self.env["investra.trade"]
        self.assertEqual(Trade._positions(self.fund, date(2031, 3, 31)), {})
        # Do pozice jde až s dokladem vypořádání (rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“).
        self.assertEqual(Trade._positions(self.fund, date(2031, 4, 5)), {})
        trade._settle()
        self.assertEqual(Trade._positions(self.fund, date(2031, 4, 5)), {instrument: 10})

    def test_settlement_mode_fair_value_change_before_settlement(self):
        """B3.1.6: změna RH do vypořádání jde do výsledku; celkový výsledek je stejný jako při trade date."""
        self.settlement_mode()
        instrument = self.instrument()
        trade = self.trade(instrument)
        trade._book()
        self.price(instrument, date(2031, 3, 31), 110)
        first = self.post(date(2031, 3, 31))
        self.assertEqual(self.balance("unsettled_fair_value"), 100)
        self.assertEqual(self.balance("gain_fair_value"), -100)
        self.assertEqual(first.fund_capital, 100100)
        trade._settle()
        self.price(instrument, date(2031, 4, 30), 115)
        second = self.post(date(2031, 4, 30))
        self.assertEqual(self.balance("unsettled_fair_value"), 0)
        self.assertEqual(self.balance("instrument_debt"), 1150)
        self.assertEqual(second.fund_capital, 100150)
        check = second.check_ids.filtered(lambda c: c.code == "positions_ledger")
        self.assertEqual(check.status, "ok")

    def test_both_methods_give_same_capital(self):
        instrument = self.instrument()
        self.trade(instrument)._book()
        self.price(instrument, date(2031, 3, 31), 110)
        valuation = self.post(date(2031, 3, 31))
        self.assertEqual(valuation.fund_capital, 100100)
        self.assertEqual(self.balance("unsettled_fair_value"), 0)

    def test_foreign_payable_is_revalued_and_settlement_difference_clears(self):
        self.rate("2031-03-31", 26)
        self.rate("2031-04-30", 26)
        instrument = self.instrument(self.eur)
        trade = self.trade(instrument, fx=25, settlement_fx_rate=26.5)
        trade._book()
        self.price(instrument, date(2031, 3, 31), 100)
        self.post(date(2031, 3, 31))
        self.assertEqual(self.balance("unsettled_payable"), -26000)
        self.assertEqual(self.balance("instrument_debt"), 26000)
        trade._settle()
        self.assertEqual(self.balance("unsettled_payable"), 500)
        self.price(instrument, date(2031, 4, 30), 100)
        self.post(date(2031, 4, 30))
        self.assertEqual(self.balance("unsettled_payable"), 0)

    def test_overdue_settlement_warns(self):
        trade = self.trade(self.instrument(), settle="2031-03-20")
        trade._book()
        self.price(trade.instrument_id, date(2031, 3, 31), 100)
        valuation = self.valuation(self.fund, date(2031, 3, 31))
        valuation.with_user(self.preparer).action_compute()
        check = valuation.check_ids.filtered(lambda c: c.code == "trades_settled")
        self.assertEqual(check.status, "warning")

    def test_fvoci_before_settlement_stops(self):
        self.settlement_mode()
        instrument = self.instrument(model="hold_collect_sell")
        self.trade(instrument)._book()
        self.price(instrument, date(2031, 3, 31), 110)
        with self.assertRaises(UserError):
            self.valuation(self.fund, date(2031, 3, 31)).with_user(self.preparer).action_compute()

    def test_setting_locked_after_first_trade(self):
        self.trade(self.instrument())
        with self.assertRaises(UserError):
            self.fund.trade_recognition = "settlement_date"

    def test_settlement_before_trade_is_rejected(self):
        with self.assertRaises(Exception):
            self.trade(self.instrument(), settle="2031-03-01")

    def test_booked_trade_cannot_change(self):
        trade = self.trade(self.instrument())
        trade.with_user(self.preparer).action_book()
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).write({"price": 120})
        trade.with_user(self.preparer).write({"settlement_fx_rate": 1})
        trade.with_user(self.preparer).action_settle()
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).write({"settlement_fx_rate": 2})

    def test_state_cannot_be_written_directly(self):
        trade = self.trade(self.instrument())
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).write({"state": "settled"})

    def test_settle_requires_unsettled(self):
        trade = self.trade(self.instrument())
        with self.assertRaises(UserError):
            trade._settle()

    def test_booking_requires_preparer(self):
        trade = self.trade(self.instrument())
        with self.assertRaises(AccessError):
            trade.with_user(self.approver).action_book()

    # --- rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“ (varianta B): pozice jen z obchodů s dokladem,
    # ocenění se zastaví kontrolou trades_booked

    def test_draft_trade_not_in_position(self):
        trade = self.trade(self.instrument(), settle=False)
        Trade = self.env["investra.trade"]
        self.assertNotIn(trade.instrument_id, Trade._positions(self.fund, date(2031, 3, 31)))
        trade._book()
        self.assertEqual(Trade._positions(self.fund, date(2031, 3, 31))[trade.instrument_id], 10)

    def test_draft_trade_stops_valuation(self):
        trade = self.trade(self.instrument(), settle=False)
        self.price(trade.instrument_id, date(2031, 3, 31), 100)
        valuation = self.valuation(self.fund, date(2031, 3, 31))
        valuation.with_user(self.preparer).action_compute()
        check = valuation.check_ids.filtered(lambda c: c.code == "trades_booked")
        self.assertEqual(check.status, "stop")
        self.assertIn(trade.instrument_id.name, check.detail)
        # Pozice bez návrhu souhlasí s knihou; ocenění zastaví jen nová kontrola.
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")
        with self.assertRaises(UserError):
            valuation.with_user(self.preparer).action_submit()

    def test_settlement_mode_unsettled_after_settlement_date_stops(self):
        self.settlement_mode()
        trade = self.trade(self.instrument(code="equity"))
        trade._book()
        self.price(trade.instrument_id, date(2031, 4, 30), 100)
        valuation = self.valuation(self.fund, date(2031, 4, 30))
        valuation.with_user(self.preparer).action_compute()
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "trades_booked").status, "stop")

    def test_draft_after_valuation_date_passes(self):
        self.trade(self.instrument(), trade_date="2031-04-10", settle=False)
        valuation = self.valuation(self.fund, date(2031, 3, 31))
        valuation.with_user(self.preparer).action_compute()
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "trades_booked").status, "ok")

    def test_sale_needs_booked_purchase(self):
        """Prodej proti návrhu nákupu nejde ani uložit (kontrola prodeje při uložení, rozhodnutí 2026-11-12)."""
        instrument = self.instrument()
        purchase = self.trade(instrument, settle=False)
        with self.assertRaises(UserError):
            self.trade(instrument, quantity=-5, trade_date="2031-03-10", settle=False)
        purchase._book()
        sale = self.trade(instrument, quantity=-5, trade_date="2031-03-10", settle=False)
        self.assertEqual(sale.held_quantity, 10)
        sale._book()
        self.assertEqual(self.env["investra.trade"]._positions(self.fund, date(2031, 3, 31))[instrument], 5)

    def test_settlement_mode_sale_against_unsettled_purchase(self):
        """Kontrole prodeje stačí stisknuté Zaúčtovat; doklad nákupu vznikne až vypořádáním."""
        self.settlement_mode()
        instrument = self.instrument(code="equity")
        self.trade(instrument)._book()
        sale = self.trade(instrument, quantity=-5, trade_date="2031-03-10", settle="2031-04-10")
        sale._book()
        self.assertEqual(sale.state, "unsettled")
