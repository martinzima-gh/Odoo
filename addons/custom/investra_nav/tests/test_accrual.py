from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

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

    def repayment(self, instrument, day, amount, **vals):
        return self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.held_in(instrument).id, "instrument_id": instrument.id,
            "date": day, "principal_amount": amount, **vals,
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
        # Splátka jde na inkasa na cestě, banku vyrovná až výpis (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“).
        self.assertEqual(self.balance("bank"), 2000 - 950)
        self.assertEqual(self.balance("cash_in_transit_receipt"), 1000)
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

    # --- zámek, storno a oprava splátky (rozhodnutí 2026-11-12 „Zámek a storno splátky“) ----------

    def booked_repayment(self, amount=1000):
        self.deposit_position()
        repayment = self.repayment(self.deposit, "2030-01-01", amount)
        repayment.with_user(self.preparer).action_book()
        return repayment

    def test_draft_repayment_can_be_changed(self):
        self.deposit_position()
        repayment = self.repayment(self.deposit, "2030-01-01", 1000)
        repayment.with_user(self.preparer).write({"principal_amount": 999})
        self.assertEqual((repayment.amount, repayment.state), (999, "draft"))

    def test_posted_repayment_cannot_be_changed_or_deleted(self):
        repayment = self.booked_repayment()
        self.assertEqual(repayment.state, "posted")
        for vals in ({"principal_amount": 900}, {"fx_rate": 2}, {"date": "2030-01-02"}):
            with self.assertRaises(UserError):
                repayment.with_user(self.preparer).write(vals)
        with self.assertRaises(UserError):
            repayment.sudo().unlink()
        self.assertEqual(repayment.amount, 1000)

    def test_state_and_event_only_from_booking(self):
        self.deposit_position()
        with self.assertRaises(UserError):
            self.env["investra.instrument.repayment"].with_user(self.preparer).create({
                "fund_id": self.fund.id, "portfolio_id": self.held_in(self.deposit).id, "instrument_id": self.deposit.id,
                "date": "2030-01-01", "principal_amount": 1000, "state": "posted",
            })
        repayment = self.repayment(self.deposit, "2030-01-01", 1000)
        for vals in ({"state": "posted"}, {"event_id": False}, {"reversal_reason": "x"}):
            with self.assertRaises(UserError):
                repayment.with_user(self.preparer).write(vals)

    def test_reverse_reopens_position_and_unlocks_schedule(self):
        self.deposit_position()
        before = (self.balance("deposit"), self.balance("cash_in_transit_receipt"))
        repayment = self.repayment(self.deposit, "2030-01-01", 1000)
        repayment.with_user(self.preparer).action_book()
        self.assertEqual(self.balance("deposit"), before[0] - 1000)
        with self.assertRaises(UserError):
            repayment.with_user(self.preparer).action_reverse(" ")
        result = repayment.with_user(self.preparer).action_reverse("Chybná částka")
        self.assertEqual(result, repayment)
        self.assertEqual((repayment.state, repayment.reversal_reason), ("reversed", "Chybná částka"))
        event = repayment.event_id.sudo()
        self.assertEqual(event.state, "reversed")
        self.assertEqual(event.reversal_move_id.date, date(2030, 1, 1))
        self.assertEqual((self.balance("deposit"), self.balance("cash_in_transit_receipt")), before)
        # Storno doklad nese nástroj, pozice nástroje je zase otevřená.
        lines = self.env["account.move.line"].sudo().search([
            ("investra_instrument_id", "=", self.deposit.id), ("parent_state", "=", "posted"),
        ])
        self.assertEqual(Decimal(str(round(sum(lines.mapped("balance")), 2))), Decimal("950"))
        log = self.env["investra.approval.log"].sudo().search([("res_model", "=", repayment._name), ("res_id", "=", repayment.id)])
        self.assertEqual(log.activity, "repayment_reverse")
        with self.assertRaises(UserError):
            repayment.with_user(self.preparer).action_reverse("Podruhé")
        with self.assertRaises(UserError):
            repayment.sudo().unlink()
        self.deposit.write({"principal": 950, "start_date": "2029-01-01", "maturity_date": "2030-01-01"})
        self.deposit.action_generate_schedule()

    def test_correct_makes_linked_draft_and_books_new_amount(self):
        repayment = self.booked_repayment(amount=990)
        bank = self.balance("cash_in_transit_receipt")
        correction = repayment.with_user(self.preparer).action_correct("Banka připsala 1 000")
        self.assertNotEqual(correction, repayment)
        self.assertEqual((correction.state, correction.replaced_id, correction.amount), ("draft", repayment, 990))
        self.assertFalse(correction.event_id)
        self.assertEqual(repayment.state, "reversed")
        correction.with_user(self.preparer).write({"principal_amount": 1000})
        correction.with_user(self.preparer).action_book()
        self.assertEqual(correction.state, "posted")
        self.assertEqual(self.balance("cash_in_transit_receipt"), bank - 990 + 1000)
        self.assertEqual(self.balance("deposit"), 950 - 1000)

    def test_reverse_with_second_person_goes_through_request(self):
        self.env["investra.approval.matrix"].create({
            "activity": "repayment_reverse", "second_person": "yes", "performer_role": "preparer",
            "valid_from": "2001-01-01", "step_ids": [(0, 0, {"sequence": 0, "name": "Kontrola", "role": "approver"})],
        })
        repayment = self.booked_repayment()
        request = repayment.with_user(self.preparer).action_reverse("Chybná částka")
        self.assertEqual(request._name, "investra.approval.request")
        self.assertEqual(repayment.state, "posted")
        with self.assertRaises(UserError):
            request.with_user(self.preparer).action_approve()
        request.with_user(self.approver).action_approve()
        self.assertEqual(repayment.state, "reversed")

    def test_locked_period_blocks_repayment_entry_and_reverse(self):
        repayment = self.booked_repayment()
        self.run_to_posted(self.valuation(self.fund, date(2030, 1, 31)))
        with self.assertRaises(UserError):
            repayment.with_user(self.preparer).action_reverse("Chybná částka")
        self.assertEqual(repayment.state, "posted")
        with self.assertRaises(UserError):
            self.repayment(self.deposit, "2030-01-15", 10)

    def test_reverse_wizard_reverses_and_correct_opens_new_draft(self):
        repayment = self.booked_repayment()
        Wizard = self.env["investra.instrument.repayment.reverse.wizard"].with_user(self.preparer)
        action = Wizard.create({"repayment_id": repayment.id, "mode": "correct", "reason": "Překlep"}).action_confirm()
        self.assertEqual(action["res_model"], "investra.instrument.repayment")
        self.assertEqual(self.env["investra.instrument.repayment"].browse(action["res_id"]).replaced_id, repayment)

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

    # --- splátky jistiny (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“) ------------------------------

    def loan(self):
        """Úvěr v reálné hodnotě bez kalendáře: kusy = jistina (1 000 ks × 1,00)."""
        self.purchase.unlink()
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 2000, 20)
        loan = self.instrument("bond", principal=1)
        self.trade(loan, 1, quantity=1000)._book()
        return loan

    def approve_price(self, instrument, day, price):
        record = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": day, "price": price, "source": "Test",
        })
        record.with_user(self.approver).action_approve()

    def test_repayment_needs_held_position(self):
        bond = self.instrument("bond")
        with self.assertRaises(ValidationError):
            self.repayment(bond, "2030-01-01", 1000)

    def test_repayment_books_to_receipts_with_principal_and_interest(self):
        loan = self.loan()
        repayment = self.repayment(loan, "2029-03-01", 400)
        repayment.interest_amount = 15
        self.assertEqual(repayment.amount, 415)
        repayment.with_user(self.preparer).action_book()
        lines = repayment.event_id.move_id.line_ids
        receipt = self.env["investra.account.role"].account_for(self.fund.company_id, "cash_in_transit_receipt")
        self.assertEqual(lines.filtered(lambda l: l.account_id == receipt).balance, 415)
        self.assertEqual(sorted(lines.filtered("investra_instrument_id").mapped("balance")), [-400, -15])
        self.assertEqual(self.balance("bank"), 2000 - 1000)

    def test_principal_reduces_units_and_overpayment_is_refused(self):
        loan = self.loan()
        first = self.repayment(loan, "2029-03-01", 400)
        self.assertEqual((first.remaining_before, first.remaining_after), (1000, 600))
        first._book()
        Trade = self.env["investra.trade"]
        self.assertEqual(Trade._holdings(self.fund, date(2029, 3, 1))[(loan, self.held_in(loan))], 600)
        self.assertEqual(Trade._holdings(self.fund, date(2029, 2, 28))[(loan, self.held_in(loan))], 1000)
        with self.assertRaises(ValidationError):
            self.repayment(loan, "2029-04-01", 601)
        last = self.repayment(loan, "2029-04-01", 600)
        self.assertEqual(last.remaining_after, 0)
        last._book()
        self.assertNotIn((loan, self.held_in(loan)), Trade._holdings(self.fund, date(2029, 4, 1)))
        # Storno vrací kusy.
        last.with_user(self.preparer).action_reverse("Zkouška")
        self.assertEqual(Trade._holdings(self.fund, date(2029, 4, 1))[(loan, self.held_in(loan))], 600)

    def test_fair_value_partial_repayment_values_only_remaining_units(self):
        loan = self.loan()
        self.repayment(loan, "2029-03-01", 400)._book()
        day = date(2029, 3, 31)
        self.approve_price(loan, day, 1.02)
        valuation = self.valuation(self.fund, day)
        self.run_to_posted(valuation)
        line = valuation.portfolio_line_ids.filtered("instrument_id")
        self.assertEqual((line.quantity, line.fair_value), (600, 612))
        self.assertEqual(self.position_balance(loan), Decimal("612"))
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")

    def test_fully_repaid_fair_value_position_is_trued_up_to_zero(self):
        loan = self.loan()
        day = date(2029, 2, 28)
        self.approve_price(loan, day, 1.05)
        self.run_to_posted(self.valuation(self.fund, day))
        self.repayment(loan, "2029-03-01", 1000)._book()
        valuation = self.valuation(self.fund, date(2029, 3, 31))
        self.run_to_posted(valuation)
        self.assertEqual(self.position_balance(loan), 0)
        self.assertFalse(valuation.portfolio_line_ids.filtered("instrument_id"))

    def position_balance(self, instrument):
        """Zůstatek účtu nástroje podle role jeho zařazení ve fondu."""
        role = instrument.classification_ids.filtered(lambda c: c.fund_id == self.fund)[:1].role_id.code
        account = self.env["investra.account.role"].account_for(self.fund.company_id, role)
        lines = self.env["account.move.line"].sudo().search([
            ("investra_instrument_id", "=", instrument.id), ("parent_state", "=", "posted"), ("account_id", "=", account.id),
        ])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def test_amortised_allows_only_scheduled_principal(self):
        self.deposit_position()
        with self.assertRaises(ValidationError):
            self.repayment(self.deposit, "2029-06-30", 500)
        self.assertTrue(self.repayment(self.deposit, "2030-01-01", 1000))

    def test_form_saves_prefilled_portfolio_like_web_client(self):
        """Model doplněný do pole jen pro čtení se musí uložit (force_save); Form posílá hodnoty jako webový klient."""
        self.deposit_position()
        form = Form(self.env["investra.instrument.repayment"].with_user(self.preparer))
        form.fund_id = self.fund
        form.date = date(2030, 1, 1)
        form.instrument_id = self.deposit
        repayment = form.save()
        self.assertEqual(repayment.portfolio_id, self.held_in(self.deposit))
        self.assertEqual((repayment.principal_amount, repayment.interest_amount), (1000, 0))

    def test_date_change_keeps_manual_amounts_instrument_change_prefills(self):
        self.deposit_position()
        form = Form(self.env["investra.instrument.repayment"].with_user(self.preparer))
        form.fund_id = self.fund
        form.date = date(2030, 1, 1)
        form.instrument_id = self.deposit
        self.assertEqual(form.principal_amount, 1000)
        form.principal_amount = 600
        form.interest_amount = 5
        form.date = date(2030, 1, 2)
        self.assertEqual((form.principal_amount, form.interest_amount), (600, 5))
        form.instrument_id = self.env["investra.instrument"]
        form.instrument_id = self.deposit
        self.assertEqual((form.principal_amount, form.interest_amount), (1000, 0))

    # --- mimořádná splátka (rozhodnutí 2026-11-12 „Mimořádná splátka nástroje“) ----------------------------

    def test_early_termination_closes_position_fee_to_bank_fees_rest_to_interest(self):
        self.deposit_position()
        self.run_to_posted(self.valuation(self.fund, date(2029, 7, 1)))
        repayment = self.repayment(self.deposit, "2029-10-01", 950, kind="early_termination", interest_amount=20, fee_amount=5)
        self.assertEqual((repayment.amount, repayment.remaining_after), (965, 0))
        repayment.with_user(self.preparer).action_book()
        self.assertEqual(self.balance("cash_in_transit_receipt"), 965)
        self.assertEqual(self.balance("expense_bank_fee"), 5)
        self.assertNotIn((self.deposit, self.held_in(self.deposit)), self.env["investra.trade"]._holdings(self.fund, date(2029, 10, 1)))
        self.run_to_posted(self.valuation(self.fund, date(2029, 10, 31)))
        # Zbytek naběhlé hodnoty (974,47 − 970) jde zatím do úroků (rozhodnutí uživatele 12. 11. 2026).
        self.assertEqual(self.balance("deposit"), 0)
        self.assertEqual(self.balance("income_interest"), -20)

    def test_prorata_scales_remaining_flows_and_prefills_reduced_rest(self):
        self.deposit_position()
        with self.assertRaises(ValidationError):
            self.repayment(self.deposit, "2029-04-01", 400)
        full = self.deposit._accrued_value(self.fund, date(2029, 7, 1))
        self.repayment(self.deposit, "2029-04-01", 400, kind="prorata")._book()
        reduced = self.deposit._accrued_value(self.fund, date(2029, 7, 1))
        self.assertAlmostEqual(float(reduced), float(full) * 0.6, delta=0.01)
        self.run_to_posted(self.valuation(self.fund, date(2029, 7, 1)))
        form = Form(self.env["investra.instrument.repayment"].with_user(self.preparer))
        form.fund_id = self.fund
        form.date = date(2030, 1, 1)
        form.instrument_id = self.deposit
        self.assertEqual((form.principal_amount, form.remaining_before), (600, 600))
        form.save()._book()
        self.run_to_posted(self.valuation(self.fund, date(2030, 1, 31)))
        self.assertEqual(self.balance("deposit"), 0)
        self.assertEqual(self.balance("income_interest"), -50)

    def test_scheduled_check_follows_prorata_reduction(self):
        """Dva toky jistiny 500 + 500; mimořádně 200 (koeficient 0,8) → k prvnímu toku je splatných 400, ne 500."""
        self.purchase.unlink()
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 2000, 20)
        loan = self.instrument("deposit")
        loan.cashflow_ids = [(0, 0, {"date": "2029-07-01", "amount": 500}), (0, 0, {"date": "2030-01-01", "amount": 500})]
        self.trade(loan, 1000)._book()
        self.repayment(loan, "2029-03-01", 200, kind="prorata")._book()
        with self.assertRaises(ValidationError):
            self.repayment(loan, "2029-07-01", 401)
        self.assertEqual(self.repayment(loan, "2029-07-01", 400).remaining_after, 400)

    def test_form_offers_held_instruments_and_prefills_from_schedule(self):
        self.deposit_position()
        self.instrument("bond")  # zařazený, ale nedržený
        form = self.env["investra.instrument.repayment"].new({"fund_id": self.fund.id, "date": "2030-01-05"})
        self.assertEqual(form.allowed_instrument_ids._origin, self.deposit)
        form.instrument_id = self.deposit
        form._onchange_instrument()
        self.assertEqual(form.portfolio_id, self.held_in(self.deposit))
        self.assertEqual((form.principal_amount, form.interest_amount), (1000, 0))
        self.assertEqual((form.remaining_before, form.remaining_after), (1000, 0))

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
