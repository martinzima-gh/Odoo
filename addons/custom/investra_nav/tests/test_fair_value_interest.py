from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFairValueInterest(NavCase):
    """Úrok v RH a realizovaný výsledek (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).

    Dluhopis: nominál 1000 na kus, kupón 30 pololetně (1. 7. 2029 a 1. 1. 2030), 30E/360, úročení od 1. 1. 2029.
    Úrok vydělaný na kus k datu = 30 × dny / 180 v běžném období. Roky 2029–2030 se nepřekrývají s jinými testy.
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

    def bond(self):
        bond = self.instrument("bond", start_date="2029-01-01", day_count="thirty360_eu")
        bond.cashflow_ids = [
            (0, 0, {"date": "2029-07-01", "amount": 30, "flow_type": "interest"}),
            (0, 0, {"date": "2030-01-01", "amount": 30, "flow_type": "interest"}),
            (0, 0, {"date": "2030-01-01", "amount": 1000, "flow_type": "principal"}),
        ]
        return bond

    def trade(self, instrument, day, quantity, price, **vals):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": instrument.id,
            "trade_date": day, "quantity": quantity, "price": price, **vals,
        })
        trade._book()
        return trade

    def price(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()

    def value(self, instrument, day, price):
        self.price(instrument, day, price)
        valuation = self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))
        return valuation, valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == instrument)

    def balance(self, role):
        Role = self.env["investra.account.role"]
        accounts = Role.accounts_for(self.fund.company_id, role)
        lines = self.env["account.move.line"].sudo().search([("account_id", "in", accounts.ids), ("parent_state", "=", "posted")])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    # --- naběhlý úrok u obchodu --------------------------------------------------------------------------

    def test_trade_prefills_accrued_coupon_only_for_bonds(self):
        bond = self.bond()
        self.assertTrue(bond.price_excludes_accrued)
        self.assertFalse(self.instrument("deposit").price_excludes_accrued)
        with Form(self.env["investra.trade"]) as form:
            form.fund_id = self.fund
            form.instrument_id = bond
            form.portfolio_id = self.portfolio(self.fund)
            form.trade_date = date(2029, 3, 1)
            form.units = 10
            form.price = 990
            # 60 dní z 180: 10 kusů × 30 × 60 / 180 = 100.
            self.assertEqual(form.accrued_interest, 100)
        equity = self.instrument("equity")
        with self.assertRaises(ValidationError):
            self.env["investra.trade"].create({
                "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": equity.id,
                "trade_date": "2029-03-01", "quantity": 1, "price": 10, "accrued_interest": 1,
            })

    def test_trade_books_accrued_interest_on_instrument_account(self):
        bond = self.bond()
        trade = self.trade(bond, "2029-03-01", 10, 990, accrued_interest=100)
        role = trade._classification().role_id.code
        self.assertEqual(self.balance(role), 10000)
        self.assertEqual(self.balance("bank"), Decimal("40000"))
        self.assertIn("Naběhlý úrok", " ".join(trade.event_id.move_id.line_ids.mapped("name")))

    # --- kupónový dluhopis: úrok lineárně, realizace průměrem ---------------------------------------------

    def test_coupon_bond_interest_revaluation_and_realisation(self):
        bond = self.bond()
        trade = self.trade(bond, "2029-03-01", 10, 990, accrued_interest=100)
        role = trade._classification().role_id.code
        # 1. 5.: vydělaný úrok 10 × (20 − 10) = 100, naběhlý úrok 100 zaplacený + 100 = 200; hodnota 10 × 1000 + 200.
        valuation, line = self.value(bond, "2029-05-01", 1000)
        self.assertEqual((line.fair_value, line.accrued_interest_currency, line.realised), (10200, 200, 0))
        self.assertEqual(self.balance("income_interest"), -100)
        self.assertEqual(self.balance("gain_fair_value"), -100)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")
        # 1. 7. kupón 300, 1. 8. prodej 4 kusů za 1010 s naběhlým úrokem 4 × 5 = 20.
        repayment = self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "portfolio_id": self.portfolio(self.fund).id,
            "date": "2029-07-01", "kind": "scheduled", "principal_amount": 0, "interest_amount": 300,
        })
        repayment._book()
        self.trade(bond, "2029-08-01", -4, 1010, accrued_interest=20)
        # 1. 8.: vydělaný úrok celkem 10 × (35 − 10) = 250, tj. +150; naběhlý úrok 6 × 5 = 30.
        # Realizace: 4 × 1010 − 4 × 1000 (účetní hodnota bez úroku k 1. 5.) = 40; přecenění zbytku 6 × 10 = 60.
        valuation, line = self.value(bond, "2029-08-01", 1010)
        self.assertEqual((line.quantity, line.fair_value, line.accrued_interest_currency), (6, 6090, 30))
        self.assertEqual((line.realised, line.cost), (40, 5940))
        self.assertEqual(self.balance("income_interest"), -250)
        self.assertEqual(self.balance("gain_fair_value"), -160)
        self.assertEqual(self.balance("gain_realised"), -40)
        self.assertEqual(self.balance(role), 6090)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")

    def test_repeated_compute_does_not_double_interest_or_realisation(self):
        bond = self.bond()
        self.trade(bond, "2029-03-01", 10, 990, accrued_interest=100)
        self.value(bond, "2029-05-01", 1000)
        self.trade(bond, "2029-06-01", -10, 1005, accrued_interest=250)
        self.price(bond, "2029-06-01", 1005)
        valuation = self.valuation(self.fund, date(2029, 6, 1))
        valuation.action_compute()
        valuation.action_compute()
        self.run_to_posted(valuation)
        # Do 1. 6. vydělaný úrok 10 × (25 − 10) = 150; realizace 10 × 1005 − 10 × 1000 = 50; pozice uzavřená.
        self.assertEqual(self.balance("income_interest"), -150)
        self.assertEqual(self.balance("gain_realised"), -50)
        self.assertEqual(self.balance("gain_fair_value"), -100)
        self.assertFalse(valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == bond))

    # --- akcie: realizace průměrem, i v cizí měně -------------------------------------------------------

    def test_equity_partial_sale_realises_against_average_carrying(self):
        equity = self.instrument("equity")
        self.trade(equity, "2029-01-01", 10, 100)
        self.value(equity, "2029-02-01", 110)
        self.trade(equity, "2029-03-01", -4, 120)
        _valuation, line = self.value(equity, "2029-03-01", 120)
        # Realizace 4 × (120 − 110) = 40, přecenění 6 × (120 − 110) = 60; pořizovací cena 6 × 100.
        self.assertEqual((line.realised, line.cost, line.fair_value), (40, 600, 720))
        self.assertEqual(self.balance("gain_realised"), -40)
        self.assertEqual(self.balance("gain_fair_value"), -160)
        self.assertEqual(self.balance("income_interest"), 0)

    def test_equity_loss_goes_to_realised_loss(self):
        equity = self.instrument("equity")
        self.trade(equity, "2029-01-01", 10, 100)
        self.value(equity, "2029-02-01", 110)
        self.trade(equity, "2029-03-01", -10, 90)
        self.value(equity, "2029-03-01", 90)
        # Účetní hodnota 1100, výnos 900: realizovaná ztráta 200; dřívější přecenění +100 zůstává.
        self.assertEqual(self.balance("loss_realised"), 200)
        self.assertEqual(self.balance("gain_fair_value"), -100)

    def test_foreign_equity_realises_in_instrument_currency(self):
        self.rate("2029-02-01", 25)
        self.rate("2029-03-01", 26)
        equity = self.instrument("equity", currency=self.eur)
        self.trade(equity, "2029-01-01", 10, 100, fx_rate=25)
        self.value(equity, "2029-02-01", 110)
        self.trade(equity, "2029-03-01", -4, 120, fx_rate=26)
        _valuation, line = self.value(equity, "2029-03-01", 120)
        # Realizace v EUR 4 × (120 − 110) = 40, kurzem dne 26 = 1040; přecenění 2500 (1. 2.) + 60 × 26 = 1560.
        self.assertEqual(line.realised, 1040)
        self.assertEqual(self.balance("gain_realised"), -1040)
        self.assertEqual(self.balance("gain_fair_value"), -4060)

    # --- kontroly zadání (2026-11-12, zkouška v UI) ---------------------------------------------------------

    def test_cashflow_must_follow_interest_start(self):
        bond = self.bond()
        with self.assertRaises(ValidationError):
            bond.cashflow_ids = [(0, 0, {"date": "2029-01-01", "amount": 30, "flow_type": "interest"})]
        with self.assertRaises(ValidationError):
            bond.maturity_date = "2029-12-31"
        bond.maturity_date = "2030-01-01"

    def test_sale_offers_only_held_instruments_and_prefills_interest(self):
        bond = self.bond()
        other = self.bond()
        self.trade(bond, "2029-03-01", 10, 990, accrued_interest=100)
        with Form(self.env["investra.trade"]) as form:
            form.fund_id = self.fund
            form.trade_date = date(2029, 8, 1)
            form.side = "sell"
            self.assertIn(bond, form.held_instrument_ids)
            self.assertNotIn(other, form.held_instrument_ids)
            form.instrument_id = bond
            form.units = 4
            form.price = 1010
            self.assertEqual(form.held_quantity, 10)
            # 30 dní z 180 po kupónu 1. 7.: 4 × 30 × 30 / 180 = 20.
            self.assertEqual(form.accrued_interest, 20)
        sale = form.record
        self.assertEqual((sale.quantity, sale.side, sale.portfolio_id), (-4, "sell", self.portfolio(self.fund)))

    def test_sale_above_holdings_is_refused_on_save(self):
        equity = self.instrument("equity")
        self.trade(equity, "2029-01-01", 10, 100)
        with self.assertRaises(UserError):
            self.env["investra.trade"].create({
                "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": equity.id,
                "trade_date": "2029-02-01", "side": "sell", "quantity": 11, "price": 100,
            })
        sale = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": equity.id,
            "trade_date": "2029-02-01", "side": "sell", "quantity": 4, "price": 100,
        })
        self.assertEqual(sale.quantity, -4)

    def test_bond_trade_without_interest_gets_it_from_calendar(self):
        bond = self.bond()
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "trade_date": "2029-03-01", "quantity": 10, "price": 990,
        })
        self.assertEqual(trade.accrued_interest, 100)

    # --- generátor kupónového kalendáře (rozhodnutí 2026-11-12 „Generátor kupónového kalendáře“) --------------

    def flows(self, instrument):
        return [(f.date, f.flow_type, f.amount) for f in instrument.cashflow_ids.sorted(lambda f: (f.date, f.flow_type))]

    def test_semiannual_schedule(self):
        bond = self.instrument("bond", principal=1000, coupon_rate=6, day_count="thirty360_eu", coupon_frequency="semiannual",
                               start_date="2029-01-01", maturity_date="2031-01-01")
        bond.action_generate_schedule()
        self.assertEqual(self.flows(bond), [
            (date(2029, 7, 1), "interest", 30), (date(2030, 1, 1), "interest", 30), (date(2030, 7, 1), "interest", 30),
            (date(2031, 1, 1), "interest", 30), (date(2031, 1, 1), "principal", 1000),
        ])

    def test_quarterly_schedule_has_short_first_period(self):
        bond = self.instrument("bond", principal=1000, coupon_rate=4, day_count="thirty360_eu", coupon_frequency="quarterly",
                               start_date="2029-02-15", maturity_date="2030-01-01")
        bond.action_generate_schedule()
        # 15. 2. – 1. 4. je 46 dní 30E/360: 1000 × 4 % × 46 / 360 = 5,11111111; další čtvrtletí 10.
        self.assertEqual(self.flows(bond), [
            (date(2029, 4, 1), "interest", 5.11111111), (date(2029, 7, 1), "interest", 10), (date(2029, 10, 1), "interest", 10),
            (date(2030, 1, 1), "interest", 10), (date(2030, 1, 1), "principal", 1000),
        ])

    def test_annual_coupon_accrues_in_valuation(self):
        bond = self.instrument("bond", principal=1000, coupon_rate=6, day_count="thirty360_eu", coupon_frequency="annual",
                               start_date="2029-01-01", maturity_date="2031-01-01")
        bond.action_generate_schedule()
        self.trade(bond, "2029-01-01", 10, 1000)
        # Půl roku ročního kupónu 60: 10 × 30 = 300 do úroku, hodnota 10 × 1000 + 300.
        _valuation, line = self.value(bond, "2029-07-01", 1000)
        self.assertEqual((line.accrued_interest_currency, line.fair_value), (300, 10300))
        self.assertEqual(self.balance("income_interest"), -300)
        self.assertEqual(self.balance("gain_fair_value"), 0)
