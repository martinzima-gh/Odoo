from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestPortfolioClass(NavCase):
    """ZJ-09 A7: portfolio třídy (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 2).

    Fond se třídami A a B 50/50 (po 100 000 Kč), sdílené portfolio „Hlavní“ (Řízení na reálnou hodnotu) a portfolio
    „Obchodování“ jen třídy B. Rok 2031 jako v testech zachycení obchodu.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")
        self.subscribe(self.a, "2031-03-01", 100000, 1000)
        self.subscribe(self.b, "2031-03-01", 100000, 1000)
        self.shared = self.portfolio(self.fund)
        self.class_b = self.portfolio(self.fund, "trading")
        self.class_b.class_id = self.b

    # --- pomocné -------------------------------------------------------------------------------------------------

    def instrument(self, code="equity", currency=None, models=("fair_value", "trading"), **vals):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Nástroj {self.fund.id} {code} {len(self.fund.portfolio_ids)}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        }, self.fund))
        for model in models:
            self.classify(self.fund, instrument, model)
        return instrument

    def trade(self, instrument, portfolio, quantity=10, price=100, day="2031-03-02", settle=None, fx=1):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": instrument.id, "trade_date": day,
            "settlement_date": settle or day, "quantity": quantity, "price": price, "fx_rate": fx,
        })
        trade.with_user(self.preparer).action_book()
        return trade

    def price(self, instrument, day, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Test",
        })
        price.with_user(self.approver).action_approve()

    def post(self, day):
        return self.run_to_posted(self.valuation(self.fund, day))

    def capitals(self, valuation):
        return {code: Decimal(str(self.result(valuation, code).capital)) for code in ("A", "B")}

    def clearing(self, fund_class=None, moves=None):
        account = self.env["investra.account.role"].account_for(self.fund.company_id, "internal_clearing")
        domain = [("account_id", "=", account.id), ("parent_state", "=", "posted"),
                  ("investra_class_id", "=", fund_class.id if fund_class else False)]
        if moves is not None:
            domain.append(("move_id", "in", moves.ids))
        return Decimal(str(round(sum(self.env["account.move.line"].sudo().search(domain).mapped("balance")), 2)))

    # --- testy ---------------------------------------------------------------------------------------------------

    def test_result_of_class_portfolio_only_in_class(self):
        """Nákup do portfolia B kapitál tříd nezmění; zisk z B jde jen do B, zisk ze sdíleného 50/50 (A6: Ostatní specifické)."""
        equity = self.instrument()
        shared_trade = self.trade(equity, self.shared)
        b_trade = self.trade(equity, self.class_b)
        self.assertFalse(shared_trade.event_id.move_id.line_ids.investra_class_id)
        lines = b_trade.event_id.move_id.line_ids
        instrument_line = lines.filtered(lambda l: l.investra_instrument_id)
        self.assertEqual(instrument_line.investra_class_id, self.b)
        self.assertEqual(self.clearing(self.b, b_trade.event_id.move_id), -1000)
        self.assertEqual(self.clearing(None, b_trade.event_id.move_id), 1000)
        self.assertFalse(lines.filtered(lambda l: l.account_id.account_type == "asset_cash").investra_class_id)
        self.price(equity, "2031-03-31", 100)
        march = self.post("2031-03-31")
        self.assertEqual(self.capitals(march), {"A": 100000, "B": 100000})
        self.price(equity, "2031-04-30", 110)
        april = self.post("2031-04-30")
        self.assertEqual(self.capitals(april), {"A": 100050, "B": 100150})
        self.assertEqual(april.fund_capital, 200200)
        b_line = self.result(april, "B")
        self.assertAlmostEqual(b_line.shared_result, 50, places=2)
        self.assertAlmostEqual(b_line.other_amount, 100, places=2)
        self.assertAlmostEqual(self.result(april, "A").other_amount, 0, places=2)
        self.assertEqual(april.check_ids.filtered(lambda c: c.status == "stop"), self.env["investra.valuation.check"])

    def test_two_average_costs(self):
        """Stejný nástroj ve sdíleném a v portfoliu B: dvě pozice a dvě průměrné pořizovací ceny."""
        equity = self.instrument()
        self.trade(equity, self.shared)
        self.trade(equity, self.class_b)
        self.trade(equity, self.class_b, price=120, day="2031-03-10")
        self.trade(equity, self.class_b, quantity=-5, price=130, day="2031-03-20")
        self.price(equity, "2031-03-31", 110)
        march = self.post("2031-03-31")
        rows = {row.portfolio_id: row for row in march.portfolio_line_ids if row.kind != "bank"}
        self.assertEqual((rows[self.shared].quantity, rows[self.shared].cost), (10, 1000))
        self.assertEqual((rows[self.class_b].quantity, rows[self.class_b].cost), (15, 1650))
        # Realizace prodeje z B (5 × (130 − 110)) a přecenění B (15 × (110 − 110)) nese jen B; sdílené +100 dělí 50/50.
        self.assertEqual(self.capitals(march), {"A": 100050, "B": 100150})

    def test_reversal_of_class_trade_returns_clearing(self):
        equity = self.instrument()
        trade = self.trade(equity, self.class_b)
        trade.with_user(self.preparer).action_reverse("Chybný obchod")
        self.assertEqual(trade.state, "reversed")
        self.assertEqual(self.clearing(self.b), 0)
        self.assertEqual(self.clearing(), 0)
        march = self.post("2031-03-31")
        self.assertEqual(self.capitals(march), {"A": 100000, "B": 100000})

    def test_repayment_fee_in_class_portfolio(self):
        """Splátka s poplatkem v portfoliu B: poplatek i úrok nese B."""
        collect = self.portfolio(self.fund, "hold_to_collect")
        collect.class_id = self.b
        deposit = self.instrument(code="deposit", models=("hold_to_collect",))
        deposit.cashflow_ids = [(0, 0, {"date": "2031-06-01", "amount": 1, "flow_type": "principal"})]
        self.trade(deposit, collect, quantity=1000, price=1)
        repayment = self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": collect.id, "instrument_id": deposit.id,
            "date": "2031-06-01", "principal_amount": 1000, "interest_amount": 30, "fee_amount": 5,
        })
        repayment.with_user(self.preparer).action_book()
        lines = repayment.event_id.move_id.line_ids
        fee = lines.filtered(lambda l: l.investra_movement_type == "fee")
        self.assertEqual((fee.balance, fee.investra_class_id), (5, self.b))
        self.assertEqual(self.clearing(self.b, repayment.event_id.move_id), 1025)
        june = self.post("2031-06-30")
        self.assertEqual(self.capitals(june), {"A": 100000, "B": 100025})

    def test_unsettled_fx_in_class_portfolio(self):
        """Nevypořádaný nákup v EUR v portfoliu B: pohledávka/závazek nese B, kurzové přecenění zůstane v B."""
        equity = self.instrument(currency=self.eur, models=("trading",))
        trade = self.trade(equity, self.class_b, settle="2031-04-05", fx=25)
        payable = trade.event_id.move_id.line_ids.filtered(lambda l: not l.investra_instrument_id and l.balance < 0
                                                           and l.investra_movement_type == "transaction")
        self.assertEqual(payable.investra_class_id, self.b)
        self.rate("2031-03-31", 26)
        self.price(equity, "2031-03-31", 100)
        march = self.post("2031-03-31")
        fx_lines = march.event_ids.filtered(lambda e: ":unsettled_fx" in e.key).move_id.line_ids
        self.assertTrue(fx_lines)
        self.assertEqual(fx_lines.investra_class_id, self.b)
        # Nástroj +1 000 (kurz) a závazek −1 000 (kurz): B beze změny, A beze změny.
        self.assertEqual(self.capitals(march), {"A": 100000, "B": 100000})

    def test_shared_portfolio_lines_unchanged(self):
        """Sdílené portfolio: řádky dokladu beze změny (otisk dřívějších dokladů stejný)."""
        equity = self.instrument(models=("fair_value",))
        classification = equity.classification_ids.filtered(lambda c: c.portfolio_id == self.shared)
        lines = [{"role": "instrument", "amount": "100", "extra": {"investra_classification_id": classification.id}},
                 {"role": "bank", "amount": "-100"}]
        Event = self.env["investra.accounting.event"]
        self.assertEqual(Event._portfolio_class_lines(self.fund.company_id, lines), lines)
        self.assertEqual(Event._fingerprint("2031-03-02", Event._portfolio_class_lines(self.fund.company_id, lines)),
                         Event._fingerprint("2031-03-02", lines))

    def test_class_lock_and_fund(self):
        other = self.make_fund(classes=[{"code": "X"}])
        foreign_class = self.cls(other, "X")
        # make_fund přepne firmu uživatelů na nový fond; zpět na fond testu.
        company = self.fund.company_id
        self.preparer.company_id = company
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=[company.id, other.company_id.id]))
        with self.assertRaises(ValidationError):
            self.class_b.class_id = foreign_class
        self.class_b.class_id = False
        self.class_b.class_id = self.b
        self.trade(self.instrument(), self.class_b)
        with self.assertRaises(UserError):
            self.class_b.class_id = self.a
        with self.assertRaises(UserError):
            self.class_b.class_id = False
        self.class_b.name = "Obchodování B"  # jiná pole zámek nedrží

    def test_preview_shows_class_and_clearing(self):
        equity = self.instrument()
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.class_b.id, "instrument_id": equity.id, "trade_date": "2031-03-02",
            "settlement_date": "2031-03-02", "quantity": 10, "price": 100, "fx_rate": 1,
        })
        preview = trade._preview_documents()
        trade.with_user(self.preparer).action_book()
        booked = trade._booked_documents()
        as_set = lambda docs: sorted((float(r[1]), float(r[2]), r[4]) for _c, _d, rows in docs for r in rows)
        self.assertEqual(as_set(preview), as_set(booked))
        self.assertIn((1000.0, 0.0, "B"), as_set(preview))
        self.assertIn((0.0, 1000.0, "B"), as_set(preview))
