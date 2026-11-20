from datetime import date
from decimal import Decimal

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestExCoupon(NavCase):
    """ZJ-19 H2: ex-kupón dluhopisu (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 7).

    Dluhopis nominál 1 000, kupón 50 ročně (5 %) k 30. 6. 2031 a 30. 6. 2032, 30E/360, úročení od 30. 6. 2030; ex-kupónová lhůta 30 dní:
    ex-datum 31. 5. 2031. Kupón dostane ten, kdo drží k večeru dne před ex-datem (30. 5.). Roky 2030–2032 jen pro tento test.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}], launch="2030-06-30")
        self.subscribe(self.cls(self.fund, "A"), "2030-07-01", 1000000, 1000)

    # --- pomocné -------------------------------------------------------------------------------------------------

    def bond(self, days=30):
        bond = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Dluhopis {self.fund.id} {days}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_bond").id,
            "start_date": "2030-06-30", "day_count": "thirty360_eu", "ex_coupon_days": days,
        }, self.fund))
        bond.cashflow_ids = [
            (0, 0, {"date": "2031-06-30", "amount": 50, "flow_type": "interest"}),
            (0, 0, {"date": "2032-06-30", "amount": 50, "flow_type": "interest"}),
            (0, 0, {"date": "2032-06-30", "amount": 1000, "flow_type": "principal"}),
        ]
        self.classify(self.fund, bond)
        return bond

    def trade(self, bond, quantity, day, price=1000, **vals):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "trade_date": day, "quantity": quantity, "price": price, **vals,
        })
        trade.with_user(self.preparer).action_book()
        return trade

    def price(self, bond, day, value=1000):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "date": day, "price": value, "source": "Test"})
        price.with_user(self.approver).action_approve()

    def value(self, bond, day):
        self.price(bond, day)
        return self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))

    def balance(self, role):
        accounts = self.env["investra.account.role"].accounts_for(self.fund.company_id, role)
        lines = self.env["account.move.line"].sudo().search([("account_id", "in", accounts.ids), ("parent_state", "=", "posted")])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def repayment(self, bond, day, interest, principal=0):
        repayment = self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id, "date": day,
            "principal_amount": principal, "interest_amount": interest})
        repayment.with_user(self.preparer).action_book()
        return repayment

    # --- ex-datum na toku ------------------------------------------------------------------------------------------

    def test_ex_date_follows_instrument_days_and_can_be_overwritten(self):
        bond = self.bond()
        flows = bond.cashflow_ids
        interest = flows.filtered(lambda f: f.flow_type == "interest").sorted("date")
        self.assertEqual(interest.mapped("ex_date"), [date(2031, 5, 31), date(2032, 5, 31)])
        self.assertFalse(flows.filtered(lambda f: f.flow_type == "principal").ex_date)
        interest[0].ex_date = date(2031, 6, 2)  # nepravidelný kupón
        self.assertEqual(interest[0].ex_date, date(2031, 6, 2))
        self.assertEqual(self.bond(days=0).cashflow_ids.mapped("ex_date"), [False, False, False])

    # --- nákup v ex-lhůtě --------------------------------------------------------------------------------------------

    def test_buyer_in_window_gets_negative_accrued_interest_and_no_jump(self):
        bond = self.bond()
        buy = self.trade(bond, 10, "2031-06-10")
        # Vydělaný kupón k 10. 6. (30E/360: 340 / 360) 47,2222 − celý kupón 50 = −2,7778 na kus.
        self.assertEqual(buy.accrued_interest, -27.78)
        self.assertEqual(self.balance("instrument_debt"), Decimal("9972.22"))
        twenty = self.value(bond, "2031-06-20")
        row = twenty.portfolio_line_ids.filtered(lambda l: l.instrument_id == bond)
        # K 20. 6. zbývá do výplaty 10 dní z 20: naběhlý úrok na kupónu −13,89, hodnota 10 000 − 13,89.
        self.assertAlmostEqual(row.fair_value, 9986.11, places=2)
        thirty = self.value(bond, "2031-06-30")
        row = thirty.portfolio_line_ids.filtered(lambda l: l.instrument_id == bond)
        self.assertAlmostEqual(row.fair_value, 10000, places=2)
        # Kupón dostal prodávající: kupující splátku nemá, úrok od nákupu je výnos (27,78) a přecenění je 0.
        self.assertEqual(self.balance("instrument_debt"), Decimal("10000.00"))
        self.assertAlmostEqual(-float(self.balance("income_interest")), 27.78, places=2)
        self.assertEqual(self.balance("gain_fair_value"), 0)
        Repayment = self.env["investra.instrument.repayment"]
        self.assertEqual(Repayment._missing_scheduled(self.fund, date(2031, 6, 30)), [])

    def test_buy_before_window_is_unchanged(self):
        bond = self.bond()
        buy = self.trade(bond, 10, "2031-05-20")
        self.assertGreater(buy.accrued_interest, 0)
        missing = self.env["investra.instrument.repayment"]._missing_scheduled(self.fund, date(2031, 6, 30))
        self.assertEqual([(m[2], m[3], m[4]) for m in missing], [(date(2031, 6, 30), Decimal(0), Decimal("500.00"))])

    # --- prodej v ex-lhůtě --------------------------------------------------------------------------------------------

    def test_seller_in_window_receives_coupon_after_position_is_closed(self):
        bond = self.bond()
        self.trade(bond, 10, "2031-02-01")
        sale = self.trade(bond, -10, "2031-06-10")
        self.assertEqual(sale.accrued_interest, -27.78)
        after_sale = self.value(bond, "2031-06-20")
        # Pozice je prodaná, ale kupón 500 ještě nepřišel: zůstává na účtu nástroje a ocenění ho nepřepíše do výsledku.
        # (Naběhlé úroky obchodů jsou zaokrouhlené na haléře, proto zbytek do 2 haléřů.)
        self.assertAlmostEqual(float(self.balance("instrument_debt")), 500, delta=0.02)
        self.assertEqual(self.balance("loss_fair_value"), 0)
        self.assertEqual(self.balance("loss_realised"), 0)
        row = after_sale.portfolio_line_ids.filtered(lambda l: l.instrument_id == bond)
        self.assertEqual(row.quantity, 0)  # řádek bez kusů nese jen nevyplacený kupón
        self.assertAlmostEqual(row.fair_value, 500, delta=0.02)
        # Návrh splátky podle kalendáře vznikne i pro prodanou pozici: jistina 0, kupón 10 × 50.
        Repayment = self.env["investra.instrument.repayment"]
        missing = Repayment._missing_scheduled(self.fund, date(2031, 6, 30))
        self.assertEqual([(m[2], m[3], m[4]) for m in missing], [(date(2031, 6, 30), Decimal(0), Decimal("500.00"))])
        repayment = Repayment.create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "date": "2031-06-30", "principal_amount": 0, "interest_amount": 500})
        self.assertIn(self.portfolio(self.fund), repayment.allowed_portfolio_ids)
        repayment.with_user(self.preparer).action_book()
        self.assertAlmostEqual(float(self.balance("instrument_debt")), 0, delta=0.02)
        self.assertEqual(self.balance("cash_in_transit_receipt"), 500)
        final = self.value(bond, "2031-06-30")
        self.assertAlmostEqual(float(self.balance("loss_fair_value")), 0, delta=0.02)
        self.assertAlmostEqual(float(self.balance("instrument_debt")), 0, delta=0.02)
        self.assertEqual(final.check_ids.filtered(lambda c: c.status == "stop"), self.env["investra.valuation.check"])

    def test_repayment_prefill_for_seller(self):
        bond = self.bond()
        self.trade(bond, 10, "2031-02-01")
        self.trade(bond, -10, "2031-06-10")
        repayment = self.env["investra.instrument.repayment"].new({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "date": date(2031, 6, 30)})
        self.assertEqual(repayment._expected(), (Decimal(0), Decimal("500.00")))

    # --- kontrola znaménka a lhůta 0 -----------------------------------------------------------------------------------

    def test_accrued_sign_in_and_out_of_window(self):
        bond = self.bond()
        with self.assertRaises(ValidationError):
            self.trade(bond, 10, "2031-06-10", accrued_interest=27.78)  # v ex-lhůtě kladný
        with self.assertRaises(ValidationError):
            self.trade(bond, 10, "2031-05-20", accrued_interest=-5)  # mimo lhůtu záporný

    def test_no_window_keeps_todays_behaviour(self):
        bond = self.bond(days=0)
        buy = self.trade(bond, 10, "2031-06-10")
        self.assertEqual(buy.accrued_interest, 472.22)
        with self.assertRaises(ValidationError):
            self.trade(bond, 10, "2031-06-11", accrued_interest=-1)
        self.trade(bond, -10, "2031-06-12")
        self.value(bond, "2031-06-20")
        # Bez ex-lhůty uzavřená pozice naběhlý úrok neudrží: prodej prodal i kupón.
        self.assertEqual(self.balance("instrument_debt"), 0)
        self.assertEqual(self.env["investra.instrument.repayment"]._missing_scheduled(self.fund, date(2031, 6, 30)), [])
