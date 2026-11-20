from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestDerecognition(NavCase):
    """ZJ-15: cena vyskladnění na prodeji (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 6).

    Nákup 10 ks à 100 (2. 3.) a 10 ks à 120 (3. 3.) → průměrná cena 110; prodej 5 ks à 130 (10. 3.); cena 125 k 31. 3. 2031.
    Průměrně: realizace 650 − 550 = 100, přecenění 15 × 125 − 1 650 = 225. Ručně 100 za kus: odchází 500, realizace 150,
    přecenění 1 875 − 1 700 = 175; součet 325 v obou případech.
    """

    def setUp(self):
        super().setUp()
        self.new_fund()

    def new_fund(self, classes=(("A",),)):
        self.fund = self.make_fund(classes=[{"code": c[0]} for c in classes])
        self.subscribe(self.cls(self.fund, "A"), "2031-03-01", 100000, 1000)
        self.equity = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, self.fund))
        self.classify(self.fund, self.equity)
        return self.fund

    def trade(self, quantity, price, day, portfolio=None, book=True, **vals):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": (portfolio or self.portfolio(self.fund)).id,
            "instrument_id": self.equity.id, "trade_date": day, "quantity": quantity, "price": price, **vals,
        })
        if book:
            trade.with_user(self.preparer).action_book()
        return trade

    def buy_two(self, **kw):
        self.trade(10, 100, "2031-03-02", **kw)
        self.trade(10, 120, "2031-03-03", **kw)

    def balance(self, role):
        Role = self.env["investra.account.role"]
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "in", Role.accounts_for(self.fund.company_id, role).ids), ("parent_state", "=", "posted"),
        ])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def value(self):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": self.equity.id, "date": "2031-03-31", "price": 125, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        return self.run_to_posted(self.valuation(self.fund, date(2031, 3, 31)))

    def results(self):
        return -self.balance("gain_realised"), -self.balance("gain_fair_value")

    # --- výchozí cena = dnešní výsledek ----------------------------------------------------------------------------

    def test_default_price_is_average_and_result_unchanged(self):
        self.buy_two()
        sale = self.trade(-5, 130, "2031-03-10")
        self.assertEqual(sale.derecognition_price, 110)  # při zaúčtování se uloží průměrná cena
        self.assertFalse(sale.derecognition_manual)
        self.value()
        self.assertEqual(self.results(), (100, 225))

    def test_average_cost_price_and_onchange(self):
        self.buy_two()
        draft = self.trade(-5, 130, "2031-03-10", book=False)
        self.assertEqual(draft.average_cost_price, 110)
        draft._onchange_derecognition_price()
        self.assertEqual(draft.derecognition_price, 110)
        self.assertFalse(draft.derecognition_manual)
        buy = self.trade(1, 100, "2031-03-11", book=False)
        self.assertEqual(buy.average_cost_price, 0)  # jen prodej

    # --- ruční cena ------------------------------------------------------------------------------------------------

    def test_manual_price_changes_split_not_total(self):
        self.buy_two()
        sale = self.trade(-5, 130, "2031-03-10", derecognition_price=100, derecognition_reason="Podle statutu: nejstarší nákup")
        self.assertTrue(sale.derecognition_manual)
        self.value()
        realised, revaluation = self.results()
        self.assertEqual((realised, revaluation), (150, 175))
        self.assertEqual(realised + revaluation, 325)

    def test_manual_price_total_equals_average_total_in_ledger(self):
        # Stejný scénář s průměrnou cenou v samostatném fondu: součet realizace a přecenění se nezmění.
        self.buy_two()
        self.trade(-5, 130, "2031-03-10")
        self.value()
        average_total = sum(self.results())
        self.new_fund()
        self.buy_two()
        self.trade(-5, 130, "2031-03-10", derecognition_price=100, derecognition_reason="Test")
        self.value()
        self.assertEqual(sum(self.results()), average_total)

    def test_remaining_position_carries_remaining_cost(self):
        self.buy_two()
        self.trade(-5, 130, "2031-03-10", derecognition_price=100, derecognition_reason="Test")
        valuation = self.value()
        row = valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == self.equity)
        self.assertEqual((row.quantity, row.cost), (15, 1700))
        # Další prodej po ručním: průměrná cena zbytku je 1 700 / 15.
        units, cost = self.env["investra.trade"]._average_cost(self.fund, self.equity, self.portfolio(self.fund), date(2031, 4, 1))
        self.assertEqual((units, cost), (15, 1700))

    # --- kontroly --------------------------------------------------------------------------------------------------

    def test_manual_price_needs_reason(self):
        self.buy_two()
        with self.assertRaises(ValidationError):
            self.trade(-5, 130, "2031-03-10", derecognition_price=100)

    def test_negative_price_is_rejected(self):
        self.buy_two()
        with self.assertRaises(ValidationError):
            self.trade(-5, 130, "2031-03-10", derecognition_price=-1, derecognition_reason="Test")

    def test_cost_above_position_is_rejected(self):
        self.buy_two()
        # 10 × 250 = 2 500 > pořizovací cena pozice 2 200.
        sale = self.trade(-10, 130, "2031-03-10", derecognition_price=250, derecognition_reason="Test", book=False)
        with self.assertRaises(UserError):
            sale.with_user(self.preparer).action_book()

    def test_full_sale_with_manual_price_is_rejected(self):
        self.buy_two()
        sale = self.trade(-20, 130, "2031-03-10", derecognition_price=100, derecognition_reason="Test", book=False)
        with self.assertRaises(UserError):
            sale.with_user(self.preparer).action_book()
        average_sale = self.trade(-20, 130, "2031-03-10", derecognition_price=110)  # průměrná cena celé pozice jde
        self.assertFalse(average_sale.derecognition_manual)

    def test_booked_price_is_locked(self):
        self.buy_two()
        sale = self.trade(-5, 130, "2031-03-10")
        with self.assertRaises(UserError):
            sale.with_user(self.preparer).write({"derecognition_price": 100, "derecognition_reason": "Pozdě"})

    # --- storno a třída --------------------------------------------------------------------------------------------

    def test_reversal_of_manual_sale_restores_average(self):
        self.buy_two()
        sale = self.trade(-5, 130, "2031-03-10", derecognition_price=100, derecognition_reason="Test")
        sale.with_user(self.preparer).action_reverse("Chybný prodej")
        units, cost = self.env["investra.trade"]._average_cost(self.fund, self.equity, self.portfolio(self.fund), date(2031, 3, 31))
        self.assertEqual((units, cost), (20, 2200))
        self.value()
        self.assertEqual(self.results(), (0, 20 * 125 - 2200))

    def test_class_portfolio_realisation_carries_class(self):
        self.new_fund(classes=(("A",), ("B",)))
        class_b = self.portfolio(self.fund, "trading")
        class_b.class_id = self.cls(self.fund, "B")
        self.classify(self.fund, self.equity, "trading")
        self.buy_two(portfolio=class_b)
        self.trade(-5, 130, "2031-03-10", portfolio=class_b, derecognition_price=100, derecognition_reason="Test")
        self.value()
        Role = self.env["investra.account.role"]
        lines = self.env["account.move.line"].sudo().search([
            ("account_id", "in", Role.accounts_for(self.fund.company_id, "gain_realised").ids), ("parent_state", "=", "posted"),
        ])
        self.assertEqual(-sum(lines.mapped("balance")), 150)
        self.assertEqual(lines.investra_class_id, self.cls(self.fund, "B"))
