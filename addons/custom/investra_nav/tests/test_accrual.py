from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
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
        instrument = self.env["investra.instrument"].create({
            "name": f"{code} {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })
        # Vklad a repo v modelu Držet pro inkaso (naběhlá hodnota), dluhopis v portfoliu Hlavní (FVTPL).
        self.classify(self.fund, instrument, "hold_to_collect" if code in ("deposit", "repo") else "fair_value")
        return instrument

    def held_in(self, instrument):
        return instrument.classification_ids.filtered(lambda c: c.fund_id == self.fund).portfolio_id

    def trade(self, instrument, price, quantity=1, day="2029-01-01"):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.held_in(instrument).id, "instrument_id": instrument.id,
            "trade_date": day, "quantity": quantity, "price": price,
        })

    def repayment(self, instrument, day, amount):
        return self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.held_in(instrument).id, "instrument_id": instrument.id,
            "date": day, "amount": amount,
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

    def deposit_position(self):
        self.purchase.unlink()
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 2000, 20)
        self.trade(self.deposit, 950)._book()

    def balance(self, role):
        account = self.env["investra.account.role"].account_for(self.fund.company_id, role)
        lines = self.env["account.move.line"].sudo().search([("account_id", "=", account.id), ("parent_state", "=", "posted")])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def test_valuation_accrues_interest_to_income(self):
        self.deposit_position()
        valuation = self.valuation(self.fund, date(2029, 7, 1))
        self.run_to_posted(valuation)
        self.assertEqual(self.balance("deposit"), Decimal("974.47"))
        self.assertEqual(self.balance("income_interest"), Decimal("-24.47"))
        self.assertEqual(self.balance("gain_fair_value"), 0)
        lines = valuation.event_ids.move_id.line_ids.filtered(lambda l: l.investra_instrument_id == self.deposit)
        self.assertEqual(set(lines.mapped("investra_movement_type")), {"accrued_interest"})
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")
        self.assertEqual(valuation.portfolio_line_ids.filtered("instrument_id").price_source, "Naběhlá hodnota")

    def test_repayment_closes_position_and_keeps_full_interest(self):
        self.deposit_position()
        self.run_to_posted(self.valuation(self.fund, date(2029, 7, 1)))
        repayment = self.repayment(self.deposit, "2030-01-01", 1000)
        repayment.with_user(self.preparer).action_book()
        valuation = self.valuation(self.fund, date(2030, 1, 31))
        self.run_to_posted(valuation)
        self.assertEqual(self.balance("deposit"), 0)
        self.assertEqual(self.balance("income_interest"), -50)
        self.assertEqual(self.balance("bank"), 2000 - 950 + 1000)
        self.assertFalse(valuation.portfolio_line_ids.filtered("instrument_id"))

    def test_repayment_event_has_own_type_and_source(self):
        """Bod 15: splátka má druh Splátka (dříve Obchod), zdroj a fond."""
        self.deposit_position()
        repayment = self.repayment(self.deposit, "2030-01-01", 1000)
        repayment.with_user(self.preparer).action_book()
        event = repayment.event_id
        self.assertEqual(event.event_type, "repayment")
        self.assertEqual((event.res_model, event.res_id, event.fund_id), ("investra.instrument.repayment", repayment.id, self.fund))
        self.assertEqual(event.amount, 1000)

    def test_repeated_compute_does_not_double_interest(self):
        self.deposit_position()
        valuation = self.valuation(self.fund, date(2029, 7, 1))
        valuation.with_user(self.preparer).action_compute()
        valuation.with_user(self.preparer).action_compute()
        self.run_to_posted(valuation)
        self.assertEqual(self.balance("income_interest"), Decimal("-24.47"))

    def test_schedule_from_rate_and_day_count(self):
        deposit = self.instrument("deposit", principal=1000000, start_date="2029-01-01", maturity_date="2029-04-01",
                                  coupon_rate=4, day_count="act360")
        deposit.action_generate_schedule()
        self.assertEqual(sum(deposit.cashflow_ids.mapped("amount")), 1010000)
        self.assertEqual(set(deposit.cashflow_ids.mapped("flow_type")), {"principal", "interest"})

    def test_schedule_needs_terms(self):
        with self.assertRaises(UserError):
            self.instrument("repo").action_generate_schedule()

    def test_schedule_locked_after_repayment(self):
        self.deposit_position()
        self.deposit.write({"principal": 950, "start_date": "2029-01-01", "maturity_date": "2030-01-01"})
        self.repayment(self.deposit, "2030-01-01", 1000)._book()
        with self.assertRaises(UserError):
            self.deposit.action_generate_schedule()

    def test_interest_and_principal_on_same_day_stay_one_payment_for_linear(self):
        deposit = self.instrument("deposit", accrual_method="linear", accrual_note="Krátký vklad")
        deposit.cashflow_ids = [(0, 0, {"date": "2030-01-01", "amount": 950}), (0, 0, {"date": "2030-01-01", "amount": 50, "flow_type": "interest"})]
        self.trade(deposit, 950)
        self.assertEqual(deposit._accrued_value(self.fund, date(2029, 7, 1)), Decimal("974.79"))

    def test_repayment_only_for_amortised(self):
        bond = self.instrument("bond")
        with self.assertRaises(ValidationError):
            self.repayment(bond, "2030-01-01", 1000)

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

    def test_same_deposit_in_two_models_values_separately(self):
        """Tentýž vklad v naběhlé hodnotě (Držet pro inkaso) a v FVTPL (Hlavní): dvě pozice, oddělená účetní hodnota."""
        self.deposit_position()
        main = self.portfolio(self.fund)
        self.classify(self.fund, self.deposit)
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": main.id, "instrument_id": self.deposit.id,
            "trade_date": "2029-01-01", "quantity": 1, "price": 950,
        })._book()
        day = date(2029, 7, 1)
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": self.deposit.id, "date": day, "price": 980, "source": "Model",
        })
        price.with_user(self.approver).action_approve()
        valuation = self.valuation(self.fund, day)
        self.run_to_posted(valuation)
        lines = valuation.portfolio_line_ids.filtered("instrument_id")
        values = {line.ifrs9_category: Decimal(str(line.fair_value)) for line in lines}
        self.assertEqual(values, {"amortised": Decimal("974.47"), "fvtpl": Decimal("980")})
        self.assertEqual(self.balance("deposit"), Decimal("1954.47"))
        self.assertEqual(self.balance("income_interest"), Decimal("-24.47"))
        self.assertEqual(self.balance("gain_fair_value"), -30)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")

    def test_manual_override_warns_in_valuation(self):
        """Ruční přepsání kategorie se ukáže v kontrolách ocenění jako upozornění."""
        self.purchase.unlink()
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 2000, 20)
        bond = self.env["investra.instrument"].create({
            "name": f"Přepsaný {self.fund.id}", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id,
        })
        self.classify(self.fund, bond, category_override="fvoci", override_note="Test přepsání")
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "trade_date": "2029-01-01", "quantity": 1, "price": 500,
        })._book()
        day = date(2029, 1, 31)
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "date": day, "price": 500, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        valuation = self.valuation(self.fund, day)
        valuation.with_user(self.preparer).action_compute()
        check = valuation.check_ids.filtered(lambda c: c.code == "classification_override")
        self.assertEqual(check.status, "warning")
        self.assertIn("Přepsaný", check.detail)
