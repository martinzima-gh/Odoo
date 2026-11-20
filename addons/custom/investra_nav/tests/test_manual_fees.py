"""ZJ-03: ručně doložené úplaty bez pravidla, souběh pravidel úplat a poplatky jen na třídě (rozhodnutí 2026-11-17)."""

from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NavCase

DAY = date(2027, 1, 31)


@tagged("post_install", "-at_install")
class TestManualFees(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def two_class_fund(self, a=1000, b=1000):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", a, 100)
        self.subscribe(self.cls(fund, "B"), "2027-01-01", b, 100)
        return fund

    def manual_event(self, valuation):
        return valuation.event_ids.filtered(lambda e: ":fee:manual:" in e.key)

    def move_lines(self, event):
        return sorted(
            (line.account_id.code, round(line.balance, 2), line.currency_id.name, round(line.amount_currency, 2),
             line.investra_class_id.code or "")
            for line in event.move_id.line_ids
        )

    # --- výpočet a zaúčtování -----------------------------------------------------------------------------------

    def test_fund_fee_is_shared_by_ratio_on_chosen_account(self):
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        account = self.expense_account(fund, "expense_management")
        self.manual_fee(valuation, 100, note="Audit 2026\nfaktura 12", account_id=account.id)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 1900, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 950, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 950, places=2)
        self.assertEqual(valuation.fee_line_ids.name, "Ručně doložená úplata: Audit 2026")
        self.assertFalse(valuation.fee_line_ids.rule_id)
        payable = self.expense_account(fund, "fee_payable")
        self.assertEqual(
            self.move_lines(self.manual_event(valuation)),
            sorted([(account.code, 100.0, "CZK", 100.0, ""), (payable.code, -100.0, "CZK", -100.0, "")]),
        )

    def test_class_fee_hits_only_that_class(self):
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        self.manual_fee(valuation, 100, class_id=self.cls(fund, "A").id)
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "A").capital, 900, places=2)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1000, places=2)
        self.assertEqual(set(self.manual_event(valuation).move_id.line_ids.investra_class_id.mapped("code")), {"A"})

    def test_negative_fee_reduces_cost(self):
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        self.manual_fee(valuation, -40, note="Dobropis úplaty")
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 2040, places=2)

    def test_negative_amount_on_income_account_books_income(self):
        """ZJ-24: výnosový účet a záporná částka = výnos (kredit účtu, debet závazku z úplat), FK vzroste."""
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        income = self.expense_account(fund, "income_other")
        payable = self.expense_account(fund, "fee_payable")
        self.manual_fee(valuation, -300, note="Vratka od správce", account_id=income.id)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 2300, places=2)
        self.assertEqual(
            self.move_lines(self.manual_event(valuation)),
            sorted([(income.code, -300.0, "CZK", -300.0, ""), (payable.code, 300.0, "CZK", 300.0, "")]),
        )

    def test_sign_hint_warns_on_opposite_sign(self):
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        income, expense = self.expense_account(fund, "income_other"), self.expense_account(fund)
        wrong = self.manual_fee(valuation, 300, account_id=income.id)
        self.assertIn("Výnos zadejte zápornou", wrong.valuation_id.external_fee_ids.sign_hint or "")
        valuation.external_fee_ids.unlink()
        self.manual_fee(valuation, -300, account_id=income.id)
        self.manual_fee(valuation, 100, account_id=expense.id)
        self.assertFalse(any(valuation.external_fee_ids.mapped("sign_hint")))

    def test_foreign_currency_at_valuation_rate_and_preview_equals_posted(self):
        # CZK fond, úplata 4 EUR, kurz ČNB k datu ocenění 25,000 → 100 CZK; závazek nese i 4 EUR pro FX přecenění.
        fund = self.two_class_fund()
        self.rate("2027-01-29", 24)
        self.rate("2027-01-31", 25)
        valuation = self.valuation(fund, DAY)
        self.manual_fee(valuation, 4, currency_id=self.eur.id)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 1900, places=2)
        event = self.manual_event(valuation)
        expense, payable = self.expense_account(fund), self.expense_account(fund, "fee_payable")
        expected = sorted([(expense.code, 100.0, "EUR", 4.0, ""), (payable.code, -100.0, "EUR", -4.0, "")])
        self.assertEqual(self.move_lines(event), expected)
        self.assertEqual(event.move_id.state, "draft")
        # Náhled (návrh dokladu z výpočtu) je tentýž doklad, který se zaúčtuje.
        move = event.move_id
        # Bez přepočtu (run_to_posted počítá znovu a založí nový návrh): odeslat, schválit, zaúčtovat.
        valuation.action_submit()
        valuation.with_user(self.approver).action_approve()
        valuation.action_post()
        self.assertEqual(event.move_id, move)
        self.assertEqual(move.state, "posted")
        self.assertEqual(self.move_lines(event), expected)
        self.assertEqual(move.date, DAY)

    def test_manual_fee_is_booked_before_performance_fee(self):
        # Jako TestFees.test_performance_with_hurdle_on_class_capital (odměna 75,34 z hrubých 1 100); ruční úplata
        # třídy A 10 sníží hrubou hodnotu na 1 090 před odměnou, odměna je proto 65,34 a třída A končí na cíli 1 024,66.
        fund = self.two_class_fund()
        self.common_result(fund, "v", "2027-06-15", 200)
        self.Rule.create({"fund_id": fund.id, "name": "Odměna", "kind": "performance",
                          "class_ids": [(6, 0, self.cls(fund, "A").ids)], "expense_role": "expense_performance",
                          "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 1.0, "initial_reference": 0,
                                                  "perf_use_hwm": False, "hurdle_kind": "fixed", "hurdle_rate": 0.05})]})
        valuation = self.valuation(fund, date(2027, 6, 30))
        self.manual_fee(valuation, 10, class_id=self.cls(fund, "A").id)
        valuation.action_compute()
        performance = valuation.fee_line_ids.filtered("rule_id")
        self.assertAlmostEqual(performance.amount, 65.34, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1024.66, places=2)
        self.assertLess(valuation.fee_line_ids.filtered("external_id").id, performance.id)

    def test_entry_validation(self):
        fund = self.two_class_fund()
        valuation = self.valuation(fund, DAY)
        for vals in ({"amount": 0}, {"note": " "}, {"account_id": self.expense_account(fund, "fee_payable").id}):
            with self.assertRaises(ValidationError):
                with self.cr.savepoint():
                    self.manual_fee(valuation, **{"amount": 5, **vals})
        self.assertFalse(valuation.external_fee_ids)

    # --- souběh pravidel ----------------------------------------------------------------------------------------

    def periodic(self, fund, name, classes=(), role="expense_management"):
        return self.Rule.create({
            "fund_id": fund.id, "name": name, "kind": "periodic", "expense_role": role,
            "class_ids": [(6, 0, [c.id for c in classes])],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
        })

    def test_overlap_warns_but_does_not_stop(self):
        fund = self.two_class_fund()
        a = self.cls(fund, "A")
        whole = self.periodic(fund, "Celý fond")
        on_a = self.periodic(fund, "Třída A", [a])
        other_role = self.periodic(fund, "Depozitář", [a], role="expense_depositary")
        self.assertIn("Celý fond", whole.overlap_warning)
        self.assertIn("Třída A", on_a.overlap_warning)
        self.assertFalse(other_role.overlap_warning)
        valuation = self.valuation(fund, DAY)
        valuation.action_compute()
        self.assertEqual(valuation.state, "computed")
        check = valuation.check_ids.filtered(lambda c: c.code == "fee_overlap")
        self.assertEqual(check.status, "warning")
        self.assertTrue(valuation.fee_line_ids.filtered(lambda l: l.rule_id == whole))
        self.assertTrue(valuation.fee_line_ids.filtered(lambda l: l.rule_id == on_a))

    def test_two_rules_on_one_class_warn(self):
        fund = self.two_class_fund()
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        first = self.periodic(fund, "První", [a])
        second = self.periodic(fund, "Druhá", [a, b], role="expense_management")
        self.assertIn("třída A", first.overlap_warning)
        self.assertIn("třída A", second.overlap_warning)
        second.active = False
        first.invalidate_recordset(["overlap_warning"])
        self.assertFalse(first.overlap_warning)

    def test_no_overlap_check_is_ok(self):
        fund = self.two_class_fund()
        self.periodic(fund, "Celý fond")
        valuation = self.valuation(fund, DAY)
        valuation.action_compute()
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "fee_overlap").status, "ok")

    # --- poplatky jen na třídě ----------------------------------------------------------------------------------

    def test_class_fee_settings_without_fund_defaults(self):
        fund = self.make_fund()
        for name in ("entry_fee_rate", "exit_fee_rate", "entry_fee_recipient", "exit_fee_recipient"):
            self.assertNotIn(name, fund._fields)
        fund_class = self.env["investra.fund.class"].create({
            "fund_id": fund.id, "code": "N", "name": "N", "currency_id": self.czk.id,
        })
        self.assertEqual(
            (fund_class.entry_fee_rate, fund_class.exit_fee_rate, fund_class.entry_fee_recipient, fund_class.exit_fee_recipient),
            (0.0, 0.0, "manager", "manager"),
        )
        fund_class.write({"entry_fee_rate": 1.5, "entry_fee_statute_ref": "čl. 9", "exit_fee_recipient": "manager"})
        messages = self.env["mail.message"].sudo().search([("model", "=", fund_class._name), ("res_id", "=", fund_class.id)])
        body = " ".join(str(m.body) for m in messages)
        self.assertIn("Vstupní poplatek (%): 0 % → 1.5 %", body)
        self.assertIn("Vstupní poplatek – článek statutu: – → čl. 9", body)
        self.assertNotIn("Příjemce výstupního poplatku", body)  # beze změny se nezapisuje

    def test_fund_form_shows_fee_rules(self):
        fund = self.two_class_fund()
        rule = self.periodic(fund, "Obhospodařování")
        self.assertEqual(fund.fee_rule_ids, rule)
        self.assertNotIn("external", [key for key, _label in self.Rule._fields["kind"].selection])
