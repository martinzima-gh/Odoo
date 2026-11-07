from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestAccrual(NavCase):
    """Diskontní nástroj 950 -> 1000 za rok; rok 2029 se nepřekrývá s jinými daty."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.deposit = self.instrument("deposit")
        self.deposit.cashflow_ids = [(0, 0, {"date": "2030-01-01", "amount": 1000})]
        self.purchase = self.trade(self.deposit, 950)

    def instrument(self, code, **vals):
        return self.env["investra.instrument"].create({
            "name": f"{code} {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })

    def trade(self, instrument, price, quantity=1, day="2029-01-01"):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "trade_date": day, "quantity": quantity, "price": price,
        })

    def test_eir_is_fund_default(self):
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2029, 7, 1)), Decimal("974.47"))

    def test_linear_on_fund(self):
        self.fund.write({"accrual_method": "linear", "accrual_note": "Nevýznamný rozdíl"})
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2029, 7, 1)), Decimal("974.79"))

    def test_instrument_overrides_fund(self):
        self.deposit.write({"accrual_method": "linear", "accrual_note": "Krátká doba"})
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2029, 7, 1)), Decimal("974.79"))

    def test_value_is_zero_after_maturity_in_both_methods(self):
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2030, 1, 1)), 0)
        self.deposit.write({"accrual_method": "linear", "accrual_note": "Krátká doba"})
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2030, 1, 1)), 0)

    def test_each_purchase_has_own_rate(self):
        self.trade(self.deposit, 950, quantity=2)
        self.assertEqual(self.deposit._accrued_value(self.fund, date(2029, 7, 1)), Decimal("2923.42"))

    def test_linear_with_more_flows_stops(self):
        self.deposit.cashflow_ids = [(0, 0, {"date": "2029-07-01", "amount": 10, "flow_type": "interest"})]
        self.deposit.write({"accrual_method": "linear", "accrual_note": "Krátká doba"})
        with self.assertRaises(UserError):
            self.deposit._accrued_value(self.fund, date(2029, 3, 1))

    def test_missing_cashflows_stop(self):
        other = self.instrument("repo")
        self.trade(other, 100)
        with self.assertRaises(UserError):
            other._accrued_value(self.fund, date(2029, 3, 1))

    def test_valuation_stops_on_amortised_position(self):
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 1000, 10)
        self.trade(self.deposit, 950, day="2029-01-02")._book()
        with self.assertRaises(UserError):
            self.valuation(self.fund, date(2029, 1, 31)).action_compute()

    def test_bond_books_to_own_role_and_position_check_holds(self):
        self.purchase.unlink()
        self.subscribe(self.cls(self.fund, "A"), "2029-02-01", 1000, 10)
        bond = self.instrument("bond")
        self.trade(bond, 500, day="2029-02-02")._book()
        day = date(2029, 2, 28)
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "date": day, "price": 520, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        valuation = self.valuation(self.fund, day)
        valuation.with_user(self.preparer).action_compute()
        check = valuation.check_ids.filtered(lambda c: c.code == "positions_ledger")
        self.assertEqual(check.status, "ok")
