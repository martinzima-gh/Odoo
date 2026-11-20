from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestDividend(NavCase):
    """ZJ-19 H1: dividenda (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 7).

    Fond drží 1 000 akcií (nákup 2. 3. 2031); ex-datum 10. 4., výplata 20. 4. 2031. Nárok má držitel k večeru dne před ex-datem.
    """

    def setUp(self):
        super().setUp()
        self.usd = self.env.ref("base.USD")
        self.usd.active = True
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")
        self.subscribe(self.a, "2031-03-01", 100000, 1000)
        self.subscribe(self.b, "2031-03-01", 100000, 1000)

    # --- pomocné -------------------------------------------------------------------------------------------------

    def instrument(self, currency=None, model="fair_value", **vals):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie {self.fund.id} {currency and currency.name} {model}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref("investra_instruments.type_equity").id, **vals,
        }, self.fund))
        self.classify(self.fund, instrument, model)
        return instrument

    def buy(self, instrument, quantity=1000, price=100, day="2031-03-02", portfolio=None, fx=1):
        portfolio = portfolio or self.portfolio(self.fund)
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": instrument.id, "trade_date": day,
            "quantity": quantity, "price": price, "fx_rate": fx,
        })
        trade.with_user(self.preparer).action_book()
        return trade

    def dividend(self, instrument, portfolio=None, book=True, **vals):
        values = {"fund_id": self.fund.id, "instrument_id": instrument.id, "portfolio_id": (portfolio or self.portfolio(self.fund)).id,
                  "ex_date": "2031-04-10", "pay_date": "2031-04-20", "per_share": 10, **vals}
        dividend = self.env["investra.dividend"].create(values)
        if book:
            dividend.with_user(self.preparer).action_book()
        return dividend

    def account(self, code):
        return self.env["account.account"].search([("code", "=", code), ("company_ids", "in", self.fund.company_id.ids)])

    def balance(self, account_or_role, day="2031-12-31"):
        if isinstance(account_or_role, str) and not account_or_role.isdigit():
            account = self.env["investra.account.role"].account_for(self.fund.company_id, account_or_role)
        elif isinstance(account_or_role, str):
            account = self.account(account_or_role)
        else:
            account = account_or_role
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "=", account.id), ("parent_state", "=", "posted"), ("date", "<=", day),
        ])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def lines(self, event):
        return {line.account_id.code: line for line in event.move_id.line_ids}

    # --- česká dividenda -----------------------------------------------------------------------------------------

    def test_domestic_dividend_10000_with_15_percent(self):
        stock = self.instrument()
        self.buy(stock)
        dividend = self.dividend(stock, kind="domestic")
        self.assertEqual((dividend.units, dividend.gross_amount, dividend.withholding_rate, dividend.withheld_amount), (1000, 10000, 15, 1500))
        self.assertEqual((dividend.creditable_amount, dividend.excess_amount, dividend.net_amount), (1500, 0, 8500))
        lines = self.lines(dividend.event_id)
        self.assertEqual(lines["714100"].balance, -10000)
        self.assertEqual(lines["681100"].balance, 1500)
        self.assertEqual(lines["341210"].balance, 8500)
        self.assertEqual(sum(line.balance for line in lines.values()), 0)
        self.assertEqual(dividend.event_id.date, date(2031, 4, 10))
        self.assertEqual(dividend.state, "booked")
        dividend.with_user(self.preparer).action_pay()
        self.assertEqual(dividend.state, "paid")
        self.assertEqual(self.balance("341210"), 0)
        self.assertEqual(self.balance("681100"), 1500)
        payment = self.lines(dividend.pay_event_id)
        self.assertEqual(payment["341210"].balance, -8500)
        self.assertEqual((self.balance("gain_fx"), self.balance("loss_fx")), (0, 0))

    def test_kind_default_follows_country_of_isin(self):
        czech = self.instrument(isin="CZ0005112300")
        foreign = self.instrument(isin="AT0000743059")
        self.buy(czech, quantity=10)
        self.buy(foreign, quantity=10)
        self.assertEqual(self.dividend(czech, book=False).kind, "domestic")
        austrian = self.dividend(foreign, book=False)
        self.assertEqual((austrian.kind, austrian.withholding_rate, austrian.treaty_rate), ("foreign", 0, 15))

    # --- zahraniční dividenda se zápočtem, přeplatkem a kurzovým rozdílem ------------------------------------------

    def test_foreign_dividend_with_credit_excess_and_fx_difference(self):
        # 700 ks × 10 EUR = 7 000 EUR; sraženo 27,5 % = 1 925; smluvní 10 % → započitatelných 700, přeplatek 1 225; kurz 25.
        stock = self.instrument(currency=self.eur)
        self.buy(stock, quantity=700, fx=25)
        dividend = self.dividend(stock, kind="foreign", withholding_rate=27.5, treaty_rate=10, fx_rate=25, pay_fx_rate=24)
        self.assertEqual((dividend.gross_amount, dividend.withheld_amount, dividend.creditable_amount, dividend.excess_amount),
                         (7000, 1925, 700, 1225))
        lines = self.lines(dividend.event_id)
        self.assertEqual(lines["714200"].balance, -175000)
        self.assertEqual((lines["681400"].balance, lines["681400"].currency_id.name), (17500, "CZK"))
        self.assertEqual((lines["341220"].balance, lines["341220"].amount_currency), (30625, 1225))
        self.assertEqual((lines["341210"].balance, lines["341210"].amount_currency, lines["341210"].currency_id), (126875, 5075, self.eur))
        dividend.with_user(self.preparer).action_pay()
        payment = self.lines(dividend.pay_event_id)
        # Banka 5 075 EUR × 24 = 121 800; pohledávka 126 875 → ztráta z kurzu 5 075.
        bank = self.env["investra.account.role"].account_for(self.fund.company_id, "bank")
        self.assertEqual(sum(l.balance for l in dividend.pay_event_id.move_id.line_ids if l.account_id == bank), 121800)
        self.assertEqual(self.balance("loss_fx"), 5075)
        self.assertEqual(self.balance("341210"), 0)

    def test_usd_dividend_exchange_gain(self):
        stock = self.instrument(currency=self.usd)
        self.buy(stock, quantity=100, fx=20)
        dividend = self.dividend(stock, kind="foreign", per_share=10, withholding_rate=15, treaty_rate=15, fx_rate=20, pay_fx_rate=21)
        self.assertEqual((dividend.gross_amount, dividend.excess_amount), (1000, 0))
        lines = self.lines(dividend.event_id)
        self.assertNotIn("341220", lines)
        self.assertEqual((lines["681400"].balance, lines["341210"].balance), (3000, 17000))
        dividend.with_user(self.preparer).action_pay()
        self.assertEqual(self.balance("gain_fx"), -850)  # 850 USD × (21 − 20)

    def test_excess_as_expense(self):
        stock = self.instrument()
        self.buy(stock, quantity=100)
        dividend = self.dividend(stock, kind="foreign", per_share=10, withholding_rate=25, treaty_rate=15, excess_treatment="expense")
        lines = self.lines(dividend.event_id)
        self.assertNotIn("341220", lines)
        self.assertEqual((lines["681400"].balance, lines["667000"].balance, lines["341210"].balance), (150, 100, 750))

    # --- nárok k ex-datu − 1 -----------------------------------------------------------------------------------------

    def test_entitlement_is_holding_on_evening_before_ex_date(self):
        stock = self.instrument()
        self.buy(stock, quantity=1000, day="2031-03-02")
        self.buy(stock, quantity=500, day="2031-04-10")  # v ex-datu: už bez nároku
        sale = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": stock.id,
            "trade_date": "2031-04-10", "quantity": -400, "price": 100})
        sale.with_user(self.preparer).action_book()  # prodej v ex-datu nárok neubere
        dividend = self.dividend(stock, kind="domestic", book=False)
        self.assertEqual(dividend.units, 1000)
        with self.assertRaises(UserError):
            self.dividend(stock, kind="domestic", book=False, units=1200).action_book()
        dividend.units = 800  # nárok jde snížit
        self.assertEqual(dividend.gross_amount, 8000)

    def test_not_held_before_ex_date_is_rejected(self):
        stock = self.instrument()
        self.buy(stock, day="2031-04-10")
        dividend = self.dividend(stock, kind="domestic", book=False)
        self.assertEqual(dividend.units, 0)
        with self.assertRaises(UserError):
            dividend.with_user(self.preparer).action_book()

    # --- portfolio třídy, storno, kontroly ---------------------------------------------------------------------------

    def test_class_portfolio_dividend_is_borne_by_class(self):
        class_b = self.portfolio(self.fund, "trading")
        class_b.class_id = self.b
        stock = self.instrument(model="trading")
        self.buy(stock, portfolio=class_b)
        dividend = self.dividend(stock, portfolio=class_b, kind="domestic")
        lines = self.lines(dividend.event_id)
        for code in ("714100", "681100", "341210"):
            self.assertEqual(lines[code].investra_class_id, self.b, code)
        dividend.with_user(self.preparer).action_pay()
        self.assertEqual(self.lines(dividend.pay_event_id)["341210"].investra_class_id, self.b)

    def test_reversal_of_paid_dividend(self):
        stock = self.instrument()
        self.buy(stock)
        dividend = self.dividend(stock, kind="domestic")
        dividend.with_user(self.preparer).action_pay()
        with self.assertRaises(UserError):
            dividend.with_user(self.preparer).action_reverse(" ")
        dividend.with_user(self.preparer).action_reverse("Chybná dividenda")
        self.assertEqual(dividend.state, "reversed")
        for code in ("714100", "681100", "341210"):
            self.assertEqual(self.balance(code), 0, code)

    def test_booked_dividend_is_locked_and_validated(self):
        stock = self.instrument()
        self.buy(stock)
        dividend = self.dividend(stock, kind="domestic")
        with self.assertRaises(UserError):
            dividend.with_user(self.preparer).write({"per_share": 11})
        with self.assertRaises(UserError):
            dividend.unlink()

    def test_dividend_validation_errors(self):
        stock = self.instrument()
        self.buy(stock)
        with self.assertRaises(ValidationError):
            self.dividend(stock, kind="domestic", book=False, pay_date="2031-04-01")
        with self.assertRaises(ValidationError):
            self.dividend(stock, kind="domestic", book=False, withholding_rate=120)
        with self.assertRaises(UserError):  # sražená daň vyšší než dividenda: kontrola při zaúčtování
            self.dividend(stock, kind="domestic", withheld_amount=20000)

    def test_only_preparer_books(self):
        stock = self.instrument()
        self.buy(stock)
        dividend = self.dividend(stock, kind="domestic", book=False)
        outsider = self.env["res.users"].create({"name": "bez role", "login": "bez_role_div",
                                                 "group_ids": [(6, 0, [self.env.ref("base.group_user").id])]})
        with self.assertRaises(AccessError):
            dividend.with_user(outsider).action_book()

    # --- ocenění ---------------------------------------------------------------------------------------------------

    def test_valuation_counts_dividend_receivable_in_nav(self):
        stock = self.instrument()
        self.buy(stock)
        self.dividend(stock, kind="domestic")
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": stock.id, "date": "2031-04-30", "price": 100, "source": "Test"})
        price.with_user(self.approver).action_approve()
        valuation = self.run_to_posted(self.valuation(self.fund, date(2031, 4, 30)))
        # 200 000 vloženo, dividenda po srážce 8 500 zvýší NAV; akcie se nepřeceňuje.
        self.assertAlmostEqual(valuation.fund_capital, 208500, places=2)
        self.assertFalse(valuation.check_ids.filtered(lambda c: c.status == "stop"))

    def test_foreign_receivable_is_in_fx_profile(self):
        profile = self.env["investra.fx.profile"].search([("fund_id", "=", self.fund.id)])
        self.assertTrue({"341210", "341220"} <= set(profile.account_ids.mapped("code")))

    def test_posting_preview_shows_documents(self):
        stock = self.instrument()
        self.buy(stock)
        dividend = self.dividend(stock, kind="domestic", book=False)
        self.assertIn("Dividendy tuzemské", dividend.posting_preview)
        self.assertIn("Pohledávky z dividend a kupónů", dividend.posting_preview)
        dividend.with_user(self.preparer).action_book()
        self.assertIn("Zaúčtované doklady dividendy", dividend.posting_preview)
