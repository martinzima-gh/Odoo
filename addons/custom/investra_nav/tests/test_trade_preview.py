from datetime import date
from decimal import Decimal

from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestTradePreview(NavCase):
    """Náhled zaúčtování obchodu a kalendář dluhopisu (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“).

    Náhled dokladu musí sedět na doklad z Zaúčtovat a Vypořádat, odhad výsledku na výsledek zaúčtovaný oceněním.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 50000, 500)

    def instrument(self, code, currency=None, **vals):
        instrument = self.env["investra.instrument"].create({
            "name": f"{code} {self.fund.id}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })
        self.classify(self.fund, instrument)
        return instrument

    def draft(self, instrument, day, quantity, price, **vals):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": instrument.id,
            "trade_date": day, "quantity": quantity, "price": price, **vals,
        })

    def trade(self, instrument, day, quantity, price, **vals):
        trade = self.draft(instrument, day, quantity, price, **vals)
        trade._book()
        return trade

    def value(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        return self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))

    def balance(self, role, movement=None):
        Role = self.env["investra.account.role"]
        domain = [("account_id", "in", Role.accounts_for(self.fund.company_id, role).ids), ("parent_state", "=", "posted")]
        if movement:
            domain += [("investra_movement_type", "=", movement), ("investra_instrument_id", "!=", False)]
        return Decimal(str(round(sum(self.env["account.move.line"].sudo().search(domain).mapped("balance")), 2)))

    def preview_rows(self, trade):
        return [(caption, day, sorted((acc, float(dr), float(cr)) for acc, dr, cr, _ccy in rows))
                for caption, day, rows in trade._preview_documents()]

    @staticmethod
    def move_rows(move):
        return sorted((l.account_id.display_name + (f" ({l.name})" if l.name and l.name.startswith("Naběhlý") else ""),
                       l.debit, l.credit) for l in move.line_ids)

    # --- doklad obchodu ------------------------------------------------------------------------------------

    def test_preview_matches_immediate_booking(self):
        equity = self.instrument("equity")
        trade = self.draft(equity, "2029-02-01", 10, 100)
        preview = self.preview_rows(trade)
        self.assertEqual(len(preview), 1)
        trade._book()
        self.assertEqual(preview[0][2], self.move_rows(trade.event_id.move_id))
        self.assertEqual(preview[0][1], date(2029, 2, 1))

    def test_preview_matches_deferred_booking_and_settlement(self):
        self.rate("2029-02-03", 26)
        equity = self.instrument("equity", currency=self.eur)
        trade = self.draft(equity, "2029-02-01", 10, 100, fx_rate=25, settlement_date="2029-02-03", settlement_fx_rate=26)
        preview = self.preview_rows(trade)
        self.assertEqual([p[1] for p in preview], [date(2029, 2, 1), date(2029, 2, 3)])
        trade._book()
        trade._settle()
        self.assertEqual(preview[0][2], self.move_rows(trade.event_id.move_id))
        self.assertEqual(preview[1][2], self.move_rows(trade.settlement_event_id.move_id))

    def test_unsettled_trade_previews_only_settlement(self):
        self.rate("2029-02-03", 26)
        equity = self.instrument("equity", currency=self.eur)
        trade = self.trade(equity, "2029-02-01", 10, 100, fx_rate=25, settlement_date="2029-02-03")
        self.assertEqual(trade.state, "unsettled")
        trade.settlement_fx_rate = 26
        preview = self.preview_rows(trade)
        self.assertEqual([p[1] for p in preview], [date(2029, 2, 3)])
        html = str(trade.posting_preview)
        self.assertIn("Vypořádat", html)
        self.assertNotIn("Očekávaný výsledek prodeje", html)
        trade._settle()
        self.assertEqual(preview[0][2], self.move_rows(trade.settlement_event_id.move_id))
        # Po vypořádání obě zaúčtované nohy, žádný náhled.
        html = str(trade.posting_preview)
        self.assertIn(trade.event_id.move_id.name, html)
        self.assertIn(trade.settlement_event_id.move_id.name, html)
        self.assertNotIn("Náhled", html)
        booked = [sorted((acc, float(dr), float(cr)) for acc, dr, cr, _c in rows) for _cap, _day, rows in trade._booked_documents()]
        self.assertEqual(booked, [self.move_rows(trade.event_id.move_id), self.move_rows(trade.settlement_event_id.move_id)])

    def test_preview_settlement_date_recognition_has_one_document(self):
        self.fund.trade_recognition = "settlement_date"
        equity = self.instrument("equity")
        trade = self.draft(equity, "2029-02-01", 10, 100, settlement_date="2029-02-03")
        preview = self.preview_rows(trade)
        self.assertEqual([p[1] for p in preview], [date(2029, 2, 3)])
        trade._book()
        self.assertEqual(trade.state, "unsettled")
        self.assertFalse(trade.event_id)
        trade._settle()
        self.assertEqual(preview[0][2], self.move_rows(trade.event_id.move_id))

    # --- očekávaný výsledek prodeje ------------------------------------------------------------------------

    def test_expected_result_matches_valuation(self):
        equity = self.instrument("equity")
        self.trade(equity, "2029-01-01", 10, 100)
        self.value(equity, "2029-02-01", 110)
        sale = self.draft(equity, "2029-03-01", -4, 120)
        result = sale._expected_result()
        # Výnos 480, účetní hodnota 4 × 110 = 440, realizace 40; pořizovací cena 400, proti ní +80.
        self.assertEqual((result["proceeds"], result["carrying"], result["realised"]), (480, 440, 40))
        self.assertEqual((result["realised_fx"], result["cost_sold"], result["against_cost"]), (0, 400, 80))
        sale._book()
        self.value(equity, "2029-03-01", 120)
        self.assertEqual(-self.balance("gain_realised"), result["realised"])

    def test_expected_result_foreign_matches_valuation(self):
        self.rate("2029-02-01", 25)
        self.rate("2029-03-01", 26)
        equity = self.instrument("equity", currency=self.eur)
        self.trade(equity, "2029-01-01", 10, 100, fx_rate=25)
        self.value(equity, "2029-02-01", 110)
        sale = self.draft(equity, "2029-03-01", -4, 120, fx_rate=26)
        result = sale._expected_result()
        # Realizace 40 EUR × 26 = 1040, realizovaný kurz 4 × 100 × (26 − 25) = 400.
        self.assertEqual((result["realised"], result["realised_fx"], result["total"]), (1040, 400, 1440))
        self.assertEqual((result["cost_sold"], result["against_cost"]), (10000, 2480))
        sale._book()
        self.value(equity, "2029-03-01", 120)
        self.assertEqual(-self.balance("gain_realised"), result["realised"])
        fx = self.balance("gain_fx", "fx_realised") + self.balance("loss_fx", "fx_realised")
        self.assertEqual(-fx, result["realised_fx"])

    def test_form_preview_of_unsaved_sale_with_loss_warning(self):
        equity = self.instrument("equity")
        self.trade(equity, "2029-01-01", 10, 100)
        self.value(equity, "2029-02-01", 100)
        with Form(self.env["investra.trade"]) as form:
            form.fund_id = self.fund
            form.side = "sell"
            form.instrument_id = equity
            form.portfolio_id = self.portfolio(self.fund)
            form.trade_date = date(2029, 3, 1)
            form.units = 4
            form.price = 10
            html = str(form.posting_preview)
            self.assertIn("Očekávaný výsledek prodeje", html)
            self.assertIn("Ztráta přesahuje 10 %", html)
            form.price = 100
            self.assertNotIn("Ztráta přesahuje", str(form.posting_preview))

    def test_purchase_preview_has_no_result(self):
        equity = self.instrument("equity")
        trade = self.draft(equity, "2029-02-01", 10, 100)
        self.assertIsNone(trade._expected_result())
        self.assertNotIn("Očekávaný výsledek prodeje", str(trade.posting_preview))
        trade._book()
        html = str(trade.posting_preview)
        self.assertIn(trade.event_id.move_id.name, html)
        self.assertNotIn("Jen náhled", html)

    # --- kalendář dluhopisu -------------------------------------------------------------------------------

    def test_calendar_note(self):
        bare = self.instrument("bond")
        self.assertIn("nemá kalendář", self.draft(bare, "2029-02-01", 10, 1000).calendar_note)
        zero = self.instrument("bond", start_date="2029-01-01")
        zero.cashflow_ids = [(0, 0, {"date": "2030-01-01", "amount": 1000, "flow_type": "principal"})]
        self.assertFalse(self.draft(zero, "2029-02-01", 10, 900).calendar_note)
        coupon = self.instrument("bond", start_date="2029-01-01")
        coupon.cashflow_ids = [
            (0, 0, {"date": "2029-07-01", "amount": 30, "flow_type": "interest"}),
            (0, 0, {"date": "2030-01-01", "amount": 1030, "flow_type": "interest"}),
        ]
        inside = self.draft(coupon, "2029-02-01", 10, 1000)
        self.assertFalse(inside.calendar_note)
        self.assertIn("mimo kupónová období", self.draft(coupon, "2030-02-01", 10, 1000).calendar_note)
        inside._book()
        self.assertFalse(inside.calendar_note)

    def test_valuation_warns_about_bond_without_calendar(self):
        bare = self.instrument("bond")
        self.trade(bare, "2029-01-01", 10, 1000)
        valuation = self.value(bare, "2029-02-01", 1000)
        check = valuation.check_ids.filtered(lambda c: c.code == "bond_calendar")
        self.assertEqual(check.status, "warning")
        self.assertIn(bare.name, check.detail)
