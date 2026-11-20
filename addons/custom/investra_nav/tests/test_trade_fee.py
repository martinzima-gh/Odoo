from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestTradeFee(NavCase):
    """ZJ-16: poplatek obchodu (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 5).

    Nákup FVTPL a každý prodej = náklad (účet 615200), nákup v naběhlé hodnotě a FVOCI = součást pořizovací ceny.
    Rok 2031 (obchody) a 2029 (vklad) jako v ostatních testech obchodů.
    """

    def setUp(self):
        super().setUp()
        self.usd = self.env.ref("base.USD")
        self.usd.active = True
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")
        self.subscribe(self.a, "2029-01-01", 100000, 1000)
        self.subscribe(self.b, "2029-01-01", 100000, 1000)
        self.bank0 = self.balance("bank")  # banka po úpisech; testy porovnávají změnu

    # --- pomocné -------------------------------------------------------------------------------------------------

    def instrument(self, code="equity", currency=None, model="fair_value", **vals):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"{code} {self.fund.id} {model}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        }, self.fund))
        self.classify(self.fund, instrument, model)
        return instrument

    def trade(self, instrument, quantity=10, price=100, day="2031-03-02", portfolio=None, book=True, **vals):
        portfolio = portfolio or instrument.classification_ids.filtered(lambda c: c.fund_id == self.fund)[:1].portfolio_id
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": instrument.id, "trade_date": day,
            "quantity": quantity, "price": price, **vals,
        })
        if book:
            trade.with_user(self.preparer).action_book()
        return trade

    def balance(self, account_or_role, day="2031-12-31"):
        if isinstance(account_or_role, str):
            account = self.env["investra.account.role"].account_for(self.fund.company_id, account_or_role)
        else:
            account = account_or_role
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "=", account.id), ("parent_state", "=", "posted"), ("date", "<=", day),
        ])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def fee_account(self):
        return self.env["account.account"].search([("code", "=", "615200"), ("company_ids", "in", self.fund.company_id.ids)])

    def price(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()

    def lines(self, trade, event=None):
        return (event or trade.event_id).move_id.line_ids

    # --- účet a role ---------------------------------------------------------------------------------------------

    def test_fee_account_is_extra_account_of_bank_fee_role(self):
        account = self.fee_account()
        self.assertTrue(account)
        self.assertIn(account, self.env["investra.account.role"].accounts_for(self.fund.company_id, "expense_bank_fee"))

    # --- nákup FVTPL: náklad -------------------------------------------------------------------------------------

    def test_fvtpl_usd_purchase_with_czk_fee_is_expense(self):
        equity = self.instrument(currency=self.usd)
        trade = self.trade(equity, quantity=10, price=100, fx_rate=22, fee_amount=150, fee_currency_id=self.czk.id)
        self.assertEqual(trade.fee_treatment, "expense")
        lines = self.lines(trade)
        fee = lines.filtered(lambda l: l.account_id == self.fee_account())
        self.assertEqual((fee.balance, fee.investra_movement_type), (150, "fee"))
        instrument_line = lines.filtered(lambda l: l.account_id == self.env["investra.account.role"].account_for(
            self.fund.company_id, "instrument"))
        self.assertEqual((instrument_line.balance, instrument_line.amount_currency), (22000, 1000))
        bank = lines.filtered(lambda l: l.account_id == self.env["investra.account.role"].account_for(self.fund.company_id, "bank"))
        self.assertEqual(sorted(bank.mapped("balance")), [-22000, -150])
        self.assertEqual(sum(lines.mapped("balance")), 0)
        self.assertEqual(self.balance(self.fee_account()), 150)

    def test_fee_in_instrument_currency_defaults_to_trade_rate(self):
        equity = self.instrument(currency=self.usd)
        trade = self.trade(equity, quantity=10, price=100, fx_rate=22, fee_amount=5, fee_currency_id=self.usd.id)
        fee = self.lines(trade).filtered(lambda l: l.account_id == self.fee_account())
        # Náklad je ve funkční měně; platba poplatku v USD je řádek banky.
        self.assertEqual(fee.balance, 110)
        bank_usd = self.lines(trade).filtered(lambda l: l.currency_id == self.usd and l.amount_currency == -5)
        self.assertEqual(bank_usd.balance, -110)

    def test_fee_in_third_currency_needs_rate(self):
        equity = self.instrument(currency=self.usd)
        with self.assertRaises(ValidationError):
            self.trade(equity, fx_rate=22, fee_amount=2, fee_currency_id=self.eur.id, book=False)
        trade = self.trade(equity, fx_rate=22, fee_amount=2, fee_currency_id=self.eur.id, fee_fx_rate=25)
        self.assertEqual(self.balance(self.fee_account()), 50)
        bank_eur = self.lines(trade).filtered(lambda l: l.currency_id == self.eur)
        self.assertEqual((bank_eur.balance, bank_eur.amount_currency), (-50, -2))

    def test_negative_fee_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.trade(self.instrument(), fee_amount=-1, book=False)

    # --- nákup v naběhlé hodnotě: kapitalizace ---------------------------------------------------------------------

    def deposit_trade(self, **vals):
        deposit = self.instrument("deposit", model="hold_to_collect")
        deposit.cashflow_ids = [(0, 0, {"date": "2030-01-01", "amount": 1100})]
        return deposit, self.trade(deposit, quantity=1, price=950, day="2029-01-01", **vals)

    def test_capitalised_fee_in_eur_goes_to_cost(self):
        # Poplatek 2 EUR × 25 = 50 Kč jde do pořizovací ceny: 950 + 50 = 1 000; platba poplatku je v EUR z banky.
        deposit, trade = self.deposit_trade(fee_amount=2, fee_currency_id=self.eur.id, fee_fx_rate=25)
        self.assertEqual(trade.fee_treatment, "capitalise")
        self.assertEqual(self.balance("deposit"), 1000)
        self.assertFalse(self.lines(trade).filtered(lambda l: l.account_id == self.fee_account()))
        self.assertEqual(self.balance("bank") - self.bank0, -950 - 50)
        eur = self.lines(trade).filtered(lambda l: l.currency_id == self.eur)
        self.assertEqual((eur.balance, eur.amount_currency), (-50, -2))
        self.assertEqual(deposit._accrued_value(self.fund, date(2029, 1, 1)), Decimal("1000.00"))

    def test_amortised_purchase_capitalises_fee_and_valuation_does_not_write_it_off(self):
        # Poplatek 50 Kč jde do pořizovací ceny: 950 + 50 = 1 000, výnos do splatnosti 1 100.
        deposit, trade = self.deposit_trade(fee_amount=50)
        self.assertEqual(trade.fee_treatment, "capitalise")
        self.assertEqual(self.balance("deposit"), 1000)
        self.assertEqual(self.balance("bank") - self.bank0, -950 - 50)
        self.assertEqual(deposit._accrued_value(self.fund, date(2029, 1, 1)), Decimal("1000.00"))
        valuation = self.run_to_posted(self.valuation(self.fund, date(2029, 1, 31)))
        row = valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == deposit)
        # Pořizovací cena zbývajících kusů včetně poplatku; hodnota = naběhlá hodnota z ceny 1 000 (ne z 950).
        self.assertEqual(row.cost, 1000)
        self.assertEqual(row.fair_value, float(deposit._accrued_value(self.fund, date(2029, 1, 31))))
        self.assertGreater(row.fair_value, 1000)
        self.assertLess(row.fair_value, 1010)
        # Poplatek nezůstal v nákladech ani se po ocenění neodepsal: účet 615200 je nulový.
        self.assertEqual(self.balance(self.fee_account(), "2029-12-31"), 0)

    def test_amortised_purchase_without_fee_unchanged(self):
        deposit, trade = self.deposit_trade()
        self.assertEqual(self.balance("deposit"), 950)
        self.assertEqual(len(self.lines(trade)), 2)
        self.assertEqual(deposit._accrued_value(self.fund, date(2029, 1, 1)), Decimal("950.00"))

    # --- prodej: vždy náklad ---------------------------------------------------------------------------------------

    def test_sale_fee_is_expense_and_realisation_unchanged(self):
        equity = self.instrument()
        self.trade(equity, quantity=10, price=100, day="2031-03-02")
        sale = self.trade(equity, quantity=-5, price=110, day="2031-03-10", fee_amount=20)
        self.assertEqual(sale.fee_treatment, "expense")
        self.assertEqual(self.balance(self.fee_account()), 20)
        # Banka: −1 000 + 550 − 20 (poplatek zmenšuje příjem z prodeje).
        self.assertEqual(self.balance("bank") - self.bank0, -1000 + 550 - 20)
        self.price(equity, "2031-03-31", 110)
        valuation = self.run_to_posted(self.valuation(self.fund, date(2031, 3, 31)))
        row = valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == equity)
        self.assertAlmostEqual(row.realised, 50, places=2)  # 5 × (110 − 100); poplatek výnos z prodeje nesnižuje

    # --- odložené vypořádání ---------------------------------------------------------------------------------------

    def test_deferred_settlement_fee_against_unsettled_then_bank(self):
        Role = self.env["investra.account.role"]
        unsettled = Role.account_for(self.fund.company_id, "unsettled_payable")
        for fee, currency, rate, czk, ccy_amount in ((30, self.czk, 0, 30, 0), (2, self.eur, 25, 50, 2)):
            with self.subTest(currency=currency.name):
                fee_before, unsettled_before, bank_before = (
                    self.balance(self.fee_account()), self.balance(unsettled), self.balance("bank"))
                equity = self.instrument()
                trade = self.trade(equity, day="2031-03-02", settlement_date="2031-03-05", fee_amount=fee,
                                   fee_currency_id=currency.id, fee_fx_rate=rate)
                self.assertEqual(self.balance(self.fee_account()) - fee_before, czk)
                # Sjednání: nákup 1 000 i poplatek proti nevypořádaným, banka se nemění.
                self.assertEqual(self.balance(unsettled) - unsettled_before, -(1000 + czk))
                self.assertEqual(self.balance("bank"), bank_before)
                trade.with_user(self.preparer).action_settle()
                self.assertEqual(self.balance(unsettled), unsettled_before)
                self.assertEqual(self.balance("bank"), bank_before - 1000 - czk)
                if ccy_amount:
                    bank = Role.account_for(self.fund.company_id, "bank")
                    settle_bank = self.lines(trade, trade.settlement_event_id).filtered(
                        lambda l: l.account_id == bank and l.currency_id == currency)
                    self.assertEqual(settle_bank.amount_currency, -ccy_amount)

    def test_settlement_date_accounting_books_fee_in_single_document(self):
        self.fund.trade_recognition = "settlement_date"
        equity = self.instrument()
        trade = self.trade(equity, day="2031-03-02", settlement_date="2031-03-05", fee_amount=30)
        trade.with_user(self.preparer).action_settle()
        self.assertEqual(self.balance(self.fee_account()), 30)
        self.assertEqual(self.balance("bank") - self.bank0, -1030)

    # --- storno, třída, otisk --------------------------------------------------------------------------------------

    def test_reversal_returns_fee(self):
        trade = self.trade(self.instrument(), fee_amount=30)
        trade.with_user(self.preparer).action_reverse("Chybný obchod")
        self.assertEqual(self.balance(self.fee_account()), 0)
        self.assertEqual(self.balance("bank"), self.bank0)

    def test_class_portfolio_fee_is_borne_by_class(self):
        class_b = self.portfolio(self.fund, "trading")
        class_b.class_id = self.b
        equity = self.instrument(model="trading")
        trade = self.trade(equity, portfolio=class_b, fee_amount=30)
        fee = self.lines(trade).filtered(lambda l: l.account_id == self.fee_account())
        self.assertEqual(fee.investra_class_id, self.b)
        self.assertFalse(self.lines(trade).filtered(lambda l: l.account_id.account_type == "asset_cash").investra_class_id)

    def test_trade_without_fee_has_no_fee_lines(self):
        trade = self.trade(self.instrument(), book=False)
        (_step, _key, _name, _day, lines, _kind), = trade._planned_postings()
        self.assertEqual([line["role"] for line in lines], ["instrument", "bank"])
        self.assertEqual(trade._capitalised_fee_ccy(), 0.0)

    def test_corrected_trade_keeps_fee(self):
        trade = self.trade(self.instrument(), fee_amount=30)
        trade.with_user(self.preparer).action_correct("Oprava ceny")
        corrected = self.env["investra.trade"].search([("replaced_id", "=", trade.id)])
        self.assertEqual(corrected.fee_amount, 30)

    def test_booked_trade_fee_is_locked(self):
        trade = self.trade(self.instrument(), fee_amount=30)
        with self.assertRaises(UserError):
            trade.with_user(self.preparer).write({"fee_amount": 40})
