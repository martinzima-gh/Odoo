from datetime import date
from decimal import Decimal

from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestFvoci(NavCase):
    """ZJ-18 G2 a G4: FVOCI do OCI (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 8, D8).

    Cílová rezerva = RH − základ (dluh: naběhlá hodnota, akcie: pořizovací cena); úrok efektivní mírou do výsledku, zbytek
    přecenění do OCI (564300); akcie bez recyklace (prodej → 571100), dluh s recyklací. Rok 2031 jako ostatní testy obchodů.
    Příklady G2: akcie 100 + poplatek 1 → RH 130 → OCI 29 → prodej 140 → OCI 0, realizované přecenění 39, výsledek 0;
    dluh 980 → naběhlá 985, RH 990 → úrok 5, OCI 5 → prodej 995 při naběhlé 987 → úrok 2, realizace 8, OCI 0.
    """

    def setUp(self):
        super().setUp()
        self.usd = self.env.ref("base.USD")
        self.usd.active = True
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")
        self.subscribe(self.a, "2031-03-01", 100000, 1000)
        self.subscribe(self.b, "2031-03-01", 100000, 1000)
        self.Role = self.env["investra.account.role"]

    # --- pomocné -------------------------------------------------------------------------------------------------

    def equity(self, currency=None, model="fair_value"):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie FVOCI {self.fund.id} {currency and currency.name} {model}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, self.fund))
        classification = self.classify(self.fund, instrument, model, designation="fvoci_equity",
                                       designation_note="Strategická investice")
        self.assertEqual(classification.ifrs9_category, "fvoci")
        return instrument

    def debt(self, currency=None):
        bond = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Dluhopis FVOCI {self.fund.id} {currency and currency.name}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "start_date": "2031-01-01",
        }, self.fund))
        bond.cashflow_ids = [(0, 0, {"date": "2034-01-01", "amount": 1000, "flow_type": "principal"})]
        bond.price_excludes_accrued = False
        classification = self.classify(self.fund, bond, "hold_collect_sell")
        self.assertEqual(classification.ifrs9_category, "fvoci")
        return bond

    def fake_amortised(self, values):
        """Naběhlá hodnota dluhu podle data (příklady G2 s přesnými čísly; efektivní míru testují testy naběhlé hodnoty)."""
        def accrued(instrument, fund, day, portfolio=None, weights=None):
            if weights is not None and not any(weights.values()):
                return Decimal(0)
            return Decimal(str(values[str(day)]))
        self.patch(type(self.env["investra.instrument"]), "_accrued_value", accrued)

    def trade(self, instrument, quantity=1, price=100, day="2031-03-02", fx=1, **vals):
        portfolio = instrument.classification_ids.filtered(lambda c: c.fund_id == self.fund)[:1].portfolio_id
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": instrument.id, "trade_date": day,
            "settlement_date": vals.pop("settle", day), "quantity": quantity, "price": price, "fx_rate": fx, **vals,
        })
        trade.with_user(self.preparer).action_book()
        return trade

    def price(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()

    def post(self, day):
        return self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))

    def account(self, code):
        return self.env["account.account"].search([("code", "=", code), ("company_ids", "in", self.fund.company_id.ids)])

    def balance(self, accounts, day="2031-12-31"):
        if isinstance(accounts, str):
            accounts = self.Role.accounts_for(self.fund.company_id, accounts) if not accounts.isdigit() else self.account(accounts)
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "in", accounts.ids), ("parent_state", "=", "posted"), ("date", "<=", day)])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def pnl(self, day="2031-12-31"):
        lines = self.env["account.move.line"].sudo().search([
            ("company_id", "=", self.fund.company_id.id), ("parent_state", "=", "posted"), ("date", "<=", day),
            "|", ("account_id.account_type", "=like", "income%"), ("account_id.account_type", "=like", "expense%")])
        return -Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def row(self, valuation, instrument):
        return valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == instrument)

    def stops(self, valuation):
        return valuation.check_ids.filtered(lambda c: c.status == "stop").mapped("name")

    # --- akcie ---------------------------------------------------------------------------------------------------

    def test_equity_czk_oci_and_realisation_without_recycling(self):
        equity = self.equity()
        trade = self.trade(equity, price=100, fee_amount=1, fee_currency_id=self.czk.id)
        self.assertEqual(trade.fee_treatment, "capitalise")
        self.price(equity, "2031-03-31", 130)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        row = self.row(march, equity)
        self.assertEqual((row.cost, row.fair_value, row.oci), (101, 130, 29))
        self.assertEqual(self.balance("564300"), -29)
        self.assertEqual(self.pnl(), 0)
        self.assertEqual(march.fund_capital, 200029)
        self.trade(equity, quantity=-1, price=140, day="2031-04-10")
        april = self.post("2031-04-30")
        self.assertEqual(self.stops(april), [])
        self.assertEqual(self.balance("564300"), 0)
        self.assertEqual(self.balance("571100"), -39)
        self.assertEqual(self.balance("instrument"), 0)
        self.assertEqual(self.pnl(), 0)
        self.assertEqual(april.fund_capital, 200039)

    def test_equity_usd_currency_goes_to_oci(self):
        self.rate("2031-03-31", 22, "USD")
        equity = self.equity(self.usd)
        self.trade(equity, price=100, fx=20)
        self.price(equity, "2031-03-31", 130)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        row = self.row(march, equity)
        self.assertEqual((row.cost, row.fair_value, row.oci), (2000, 2860, 860))
        self.assertEqual(self.balance("564300"), -860)
        self.assertEqual((self.balance("gain_fair_value"), self.balance("gain_fx")), (0, 0))
        reserve = self.env["account.move.line"].sudo().search([("account_id", "=", self.account("564300").id),
                                                                ("parent_state", "=", "posted")])
        self.assertEqual(sum(reserve.mapped("amount_currency")), -30)

    def test_closed_position_at_carrying_value_releases_reserve(self):
        """Prodej přesně za účetní hodnotu: účet nástroje je nulový, rezerva se přesto převede do realizovaného přecenění."""
        equity = self.equity()
        self.trade(equity, price=100)
        self.price(equity, "2031-03-31", 130)
        self.post("2031-03-31")
        self.trade(equity, quantity=-1, price=130, day="2031-04-10")
        self.post("2031-04-30")
        self.assertEqual(self.balance("564300"), 0)
        self.assertEqual(self.balance("571100"), -30)
        self.assertEqual(self.pnl(), 0)

    def test_manual_ecl_does_not_change_target_reserve(self):
        """Ruční ECL (MD 667500 / D 564500) je výsledek; cílová rezerva na hlavním účtu se nemění."""
        equity = self.equity()
        self.trade(equity, price=100)
        self.price(equity, "2031-03-31", 130)
        self.post("2031-03-31")
        self.book(self.fund, "ecl", date(2031, 4, 15), [
            {"role": "expense_other", "amount": "5", "extra": {"account_id": self.account("667500").id}},
            {"role": "revaluation_reserve", "amount": "-5", "extra": {"account_id": self.account("564500").id}},
        ])
        self.price(equity, "2031-04-30", 130)
        april = self.post("2031-04-30")
        self.assertEqual(self.row(april, equity).oci, 30)
        self.assertEqual(self.balance("564300"), -30)
        self.assertEqual(self.balance("564500"), -5)
        self.assertEqual(self.pnl(), -5)

    def test_class_portfolio_oci_stays_in_class(self):
        """Portfolio třídy B: řádek nástroje (aktivum) nese B, rezerva je kapitál → kapitál A beze změny (A2)."""
        portfolio = self.portfolio(self.fund, "hold_collect_sell")
        portfolio.class_id = self.b
        equity = self.equity(model="hold_collect_sell")
        self.trade(equity, price=100)
        self.price(equity, "2031-03-31", 130)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        self.assertEqual((self.result(march, "A").capital, self.result(march, "B").capital), (100000, 100030))
        reserve = self.env["account.move.line"].sudo().search([("account_id", "=", self.account("564300").id),
                                                                ("parent_state", "=", "posted")])
        self.assertEqual(reserve.investra_class_id, self.b)

    def test_unsettled_trade_change_goes_to_oci(self):
        """Nevypořádaný nákup FVOCI: změna RH do vypořádání jde do OCI; po vypořádání drží rezervu pozice."""
        self.fund.trade_recognition = "settlement_date"
        equity = self.equity()
        trade = self.trade(equity, quantity=10, price=100, day="2031-03-30", settle="2031-04-05")
        self.price(equity, "2031-03-31", 110)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        self.assertEqual(self.balance("unsettled_fair_value"), 100)
        self.assertEqual(self.balance("564300"), -100)
        self.assertEqual(self.pnl(), 0)
        trade._settle()
        self.price(equity, "2031-04-30", 115)
        april = self.post("2031-04-30")
        self.assertEqual(self.stops(april), [])
        self.assertEqual(self.balance("unsettled_fair_value"), 0)
        self.assertEqual(self.balance("564300"), -150)
        self.assertEqual(self.row(april, equity).oci, 150)
        self.assertEqual(self.pnl(), 0)

    # --- dluh ----------------------------------------------------------------------------------------------------

    def test_debt_czk_interest_oci_and_recycling(self):
        bond = self.debt()
        self.fake_amortised({"2031-03-31": 985, "2031-04-10": 987})
        self.trade(bond, price=980)
        self.price(bond, "2031-03-31", 990)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        self.assertEqual(self.row(march, bond).oci, 5)
        self.assertEqual(self.balance("income_interest"), -5)
        self.assertEqual(self.balance("564300"), -5)
        self.trade(bond, quantity=-1, price=995, day="2031-04-10")
        april = self.post("2031-04-30")
        self.assertEqual(self.stops(april), [])
        self.assertEqual(self.balance("income_interest"), -7)
        self.assertEqual(self.balance("gain_realised"), -8)
        self.assertEqual(self.balance("564300"), 0)
        self.assertEqual(self.balance("instrument_debt"), 0)
        self.assertEqual(self.pnl(), 15)

    def test_debt_usd_fx_on_amortised_value_to_pnl(self):
        """Dluh je peněžní položka: kurz z naběhlé hodnoty do výsledku, kurz z rezervy do OCI."""
        self.rate("2031-03-31", 22, "USD")
        bond = self.debt(self.usd)
        self.fake_amortised({"2031-03-31": 985})
        self.trade(bond, price=980, fx=20)
        self.price(bond, "2031-03-31", 990)
        march = self.post("2031-03-31")
        self.assertEqual(self.stops(march), [])
        self.assertEqual(self.row(march, bond).oci, 110)                # (990 − 985) × 22
        self.assertEqual(self.balance("564300"), -110)
        self.assertEqual(self.balance("income_interest"), -110)         # 5 USD × 22
        self.assertEqual(self.balance("gain_fx"), -1960)                # 980 × (22 − 20)
        self.assertEqual(self.balance("instrument_debt"), 21780)

    def test_debt_real_amortised_value(self):
        """Bez náhrady: rezerva = RH − naběhlá hodnota efektivní mírou, výsledek = změna účetní hodnoty − OCI."""
        bond = self.debt()
        self.trade(bond, quantity=10, price=900)
        self.price(bond, "2031-06-30", 950)
        june = self.post("2031-06-30")
        self.assertEqual(self.stops(june), [])
        amortised = bond._accrued_value(self.fund, date(2031, 6, 30), self.portfolio(self.fund, "hold_collect_sell"))
        self.assertEqual(Decimal(str(self.row(june, bond).oci)), 9500 - amortised)
        self.assertEqual(-self.balance("income_interest"), amortised - 9000)

    def test_fvtpl_unchanged(self):
        """FVTPL (D7): přecenění do výsledku jako dosud, rezerva prázdná."""
        equity = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie FVTPL {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, self.fund))
        self.classify(self.fund, equity)
        self.trade(equity, price=100)
        self.price(equity, "2031-03-31", 130)
        march = self.post("2031-03-31")
        self.assertFalse(self.row(march, equity).oci)
        self.assertEqual(self.pnl(), 30)
        self.assertEqual(self.balance("564300"), 0)

    # --- daň (G3, G4) ---------------------------------------------------------------------------------------------

    def tax_setup(self):
        """ZIF 5 % a běžné výjimky; fond se zařazením FVOCI dostane i odloženou daň z 564300 a splatnou z 571100 (D9–D11)."""
        self.fund_tax(self.fund, rule=self.env.ref("investra_nav.tax_rule_zif_5"))
        self.fund.action_add_common_tax_exceptions()
        rules = {e.account_id.code: e.tax_rule_id for e in self.fund.tax_exception_ids}
        self.assertEqual(rules["564300"], self.env.ref("investra_nav.tax_rule_deferred_fvoci_5"))
        self.assertEqual(rules["571100"], self.fund.tax_rule_id)

    def test_tax_equity_deferred_then_current_on_realisation(self):
        """Akcie: OCI 29 → odložená 5 % = 1,45 (564400 / 348000), splatná 0; prodej za 140 → odložená 0, splatná 5 % × 39 = 1,95."""
        equity = self.equity()
        self.tax_setup()
        self.trade(equity, price=100, fee_amount=1, fee_currency_id=self.czk.id)
        self.price(equity, "2031-03-31", 130)
        self.post("2031-03-31")
        self.assertEqual((self.balance("564400"), self.balance("348000")), (Decimal("1.45"), Decimal("-1.45")))
        self.assertEqual(self.balance("681000"), 0)
        self.trade(equity, quantity=-1, price=140, day="2031-04-10")
        self.post("2031-04-30")
        self.assertEqual((self.balance("564400"), self.balance("348000")), (0, 0))
        self.assertEqual((self.balance("681000"), self.balance("347000")), (Decimal("1.95"), Decimal("-1.95")))

    def test_tax_debt_recycled_gain_in_current_tax(self):
        """Dluh: úrok 5 → splatná 0,25, OCI 5 → odložená 0,25; prodej: úrok 2 + realizace 8 → splatná celkem 5 % × 15 = 0,75,
        odložená 0."""
        bond = self.debt()
        self.tax_setup()
        self.fake_amortised({"2031-03-31": 985, "2031-04-10": 987})
        self.trade(bond, price=980)
        self.price(bond, "2031-03-31", 990)
        self.post("2031-03-31")
        self.assertEqual((self.balance("681000"), self.balance("348000")), (Decimal("0.25"), Decimal("-0.25")))
        self.trade(bond, quantity=-1, price=995, day="2031-04-10")
        self.post("2031-04-30")
        self.assertEqual((self.balance("681000"), self.balance("348000")), (Decimal("0.75"), 0))

    def test_tax_fvtpl_taxed_at_once(self):
        """FVTPL (D7): přecenění +30 je v základu hned → splatná 1,50, odložená 0."""
        self.fund_tax(self.fund, rule=self.env.ref("investra_nav.tax_rule_zif_5"))
        equity = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie FVTPL daň {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, self.fund))
        self.classify(self.fund, equity)
        self.trade(equity, price=100)
        self.price(equity, "2031-03-31", 130)
        self.post("2031-03-31")
        self.assertEqual((self.balance("681000"), self.balance("348000")), (Decimal("1.50"), 0))
