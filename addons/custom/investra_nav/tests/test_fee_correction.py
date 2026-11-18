"""ZJ-11: oprava vypočtené úplaty ruční úplatou s polem „Opravuje úplatu“ (rozhodnutí 2026-11-18)."""

from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase

YEAR_END = date(2027, 12, 31)


@tagged("post_install", "-at_install")
class TestFeeCorrection(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, capital=1000000, classes=("A",)):
        fund = self.make_fund(classes=[{"code": c} for c in classes])
        for code in classes:
            self.subscribe(self.cls(fund, code), "2027-01-01", capital, 1000)
        return fund

    def rule(self, fund, rate=0.01, **values):
        return self.Rule.create({
            "fund_id": fund.id, "name": values.pop("name", "Obhospodařování"), "kind": "periodic",
            "expense_role": "expense_management", **values,
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})],
        })

    def correction(self, valuation, rule, amount, **vals):
        vals = {"note": "Zaokrouhlení podle faktury", "account_id": False, "corrects_rule_id": rule.id, **vals}
        return self.manual_fee(valuation, amount, **vals)

    def correction_event(self, valuation, entry):
        return valuation.event_ids.filtered(lambda e: e.key.endswith(f":manual:{entry.id}"))

    def balances(self, event):
        """Zůstatky dokladu podle účtu a třídy."""
        result = {}
        for line in event.move_id.line_ids:
            key = (line.account_id.code, line.investra_class_id.code or "")
            result[key] = round(result.get(key, 0) + line.balance, 2)
        return result

    # --- účtování ----------------------------------------------------------------------------------------------

    def test_negative_correction_before_on_rule_role(self):
        # Úplata „před“ 1 % z 1 000 000 = 10 000; faktura obhospodařovatele 9 999,60 → oprava −0,40.
        fund = self.fund()
        rule = self.rule(fund)
        valuation = self.valuation(fund, YEAR_END)
        entry = self.correction(valuation, rule, -0.40)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.filtered("rule_id").amount, 10000.00, places=2)
        line = valuation.fee_line_ids.filtered("external_id")
        self.assertAlmostEqual(line.amount, -0.40, places=2)
        self.assertFalse(line.rule_id)  # bez pravidla: průměrný FK ji neodečítá
        self.assertEqual(line.name, "Oprava úplaty Obhospodařování: Zaokrouhlení podle faktury")
        self.assertAlmostEqual(valuation.fund_capital, 990000.40, places=2)
        # Bez příjemců stejné doklady jako úplata pravidla: nákladová role pravidla proti závazku z úplat.
        expense, payable = self.expense_account(fund, "expense_management"), self.expense_account(fund, "fee_payable")
        self.assertEqual(self.balances(self.correction_event(valuation, entry)),
                         {(expense.code, ""): -0.40, (payable.code, ""): 0.40})
        self.assertEqual(self.correction_event(valuation, entry).name, f"Oprava úplaty Obhospodařování ({YEAR_END})")

    def test_correction_lowers_cost_before_after_fees(self):
        # Úplata „po“ 1 %: oprava −100 zvýší základ před dopočtem → S = 0,01 × (1 000 100 − S) = 9 901,98.
        # FK = 1 000 100 − 9 901,98 = 990 198,02 (čistý výpočet z opravené částky).
        fund = self.fund()
        rule = self.rule(fund, base_step="2")
        valuation = self.valuation(fund, YEAR_END)
        self.correction(valuation, rule, -100)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.filtered("rule_id").amount, 9901.98, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 990198.02, places=2)

    def test_average_fk_does_not_true_up_correction(self):
        # Jako TestFees.test_average_fk_with_true_up: leden 3 100, oprava −0,50 (FK leden 996 900,50).
        # Únor: průměr (996 900,50 + 1 996 900,50) / 2 × 0,0365 × 59/365 = 8 831,71; doúčtování 8 831,71 − 3 100
        # = 5 731,71. Opravu ocenění neodečítá (řádek bez pravidla), rozdíl −0,50 zůstává trvale.
        fund = self.fund()
        rule = self.rule(fund, rate=0.0365, base_source="average_fk")
        january = self.valuation(fund, date(2027, 1, 31))
        self.correction(january, rule, -0.50)
        self.run_to_posted(january)
        self.assertAlmostEqual(january.fund_capital, 996900.50, places=2)
        self.subscribe(self.cls(fund, "A"), "2027-02-10", 1000000, 1000)
        february = self.valuation(fund, date(2027, 2, 28))
        february.action_compute()
        self.assertAlmostEqual(february.fee_line_ids.filtered(lambda l: l.rule_id == rule).amount, 5731.71, places=2)

    def test_correction_with_recipients_splits_like_fee(self):
        # Jako TestFees.test_half_to_classes_half_to_manager: úplata třídy A 84,93, polovina třídě B.
        # Oprava −0,93: náklad mimo fond + přesun třídě B = −0,93; třída A končí na 1 000 − 84,00 = 916,00.
        fund = self.fund(1000, classes=("A", "B"))
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        rule = self.rule(fund, rate=1.0, name="Dělená", base_source="class_fk", class_ids=[(6, 0, a.ids)],
                         recipient_share=0.5, recipient_class_ids=[(6, 0, b.ids)], expense_role="expense_other")
        valuation = self.valuation(fund, date(2027, 1, 31))
        entry = self.correction(valuation, rule, -0.93, class_id=a.id)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.filtered("rule_id").amount, 84.93, places=2)
        self.assertAlmostEqual(self.result(valuation, "A").capital, 916.00, places=2)
        balances = self.balances(self.correction_event(valuation, entry))
        expense = self.expense_account(fund, "expense_other").code
        clearing = self.expense_account(fund, "internal_clearing").code
        external = balances.get((expense, "A"), 0)
        to_b = balances.get((clearing, "B"), 0)
        self.assertAlmostEqual(external + to_b, -0.93, places=2)
        self.assertAlmostEqual(balances.get((clearing, "A"), 0), -to_b, places=2)
        self.assertNotEqual(to_b, 0)
        # FK klesne jen o náklad mimo fond; třídy dohromady = FK.
        self.assertAlmostEqual(self.result(valuation, "B").capital - 1000 + 2000 - valuation.fund_capital, 84.00, places=2)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "clearing_zero").status, "ok")

    # --- zámek a přepočet -------------------------------------------------------------------------------------

    def test_recompute_keeps_correction_and_submit_locks_it(self):
        fund = self.fund()
        rule = self.rule(fund)
        valuation = self.valuation(fund, YEAR_END)
        entry = self.correction(valuation, rule, -0.40)
        valuation.action_compute()
        valuation.action_compute()
        self.assertEqual(valuation.external_fee_ids, entry)
        self.assertEqual(len(valuation.fee_line_ids.filtered("external_id")), 1)
        self.assertAlmostEqual(valuation.fund_capital, 990000.40, places=2)
        valuation.action_submit()
        with self.assertRaises(UserError):
            entry.with_user(self.preparer).write({"amount": -0.50})

    # --- kontrola ---------------------------------------------------------------------------------------------

    def test_correction_validation(self):
        fund = self.fund(classes=("A", "B"))
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        whole = self.rule(fund, name="Celý fond")
        on_a = self.rule(fund, name="Třída A", class_ids=[(6, 0, a.ids)])
        performance = self.Rule.create({
            "fund_id": fund.id, "name": "Odměna", "kind": "performance", "class_ids": [(6, 0, a.ids)],
            "expense_role": "expense_performance",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "initial_reference": 0})],
        })
        valuation = self.valuation(fund, YEAR_END)
        invalid = (
            (whole, {"note": " "}),                                                  # poznámka povinná
            (whole, {"amount": 0}),                                                  # nula
            (on_a, {"class_id": b.id}),                                              # třída mimo pravidlo
            (on_a, {}),                                                              # bez třídy u pravidla tříd
            (whole, {"class_id": a.id}),                                             # třída u úplaty celého fondu
            (whole, {"account_id": self.expense_account(fund, "expense_management").id}),  # účet se nezadává
            (whole, {"currency_id": self.eur.id}),                                   # jen měna fondu
            (performance, {}),                                                       # bez třídy u odměny tříd
            (whole, {"validity": "valuation"}),                                      # úplata platí trvale
        )
        for rule, vals in invalid:
            with self.subTest(rule=rule.name, vals=vals), self.assertRaises(ValidationError):
                with self.cr.savepoint():
                    self.correction(valuation, rule, vals.pop("amount", -1), **vals)
        self.assertFalse(valuation.external_fee_ids)
        self.correction(valuation, on_a, -1, class_id=a.id)
        self.correction(valuation, whole, 1)
        self.assertEqual(len(valuation.external_fee_ids), 2)

    # --- tlačítko Opravit na řádku úplaty (krok 2) -----------------------------------------------------------------

    def test_correct_button_context_and_save(self):
        fund = self.fund(classes=("A", "B"))
        a = self.cls(fund, "A")
        rule = self.rule(fund, class_ids=[(6, 0, [a.id])])
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered("rule_id")
        self.assertTrue(line.can_correct)
        action = line.action_correct()
        ctx = action["context"]
        self.assertEqual(action["res_model"], "investra.valuation.external")
        self.assertEqual(action["target"], "new")
        self.assertEqual(ctx["default_valuation_id"], valuation.id)
        self.assertEqual(ctx["default_corrects_rule_id"], rule.id)
        self.assertEqual(ctx["default_class_id"], line.class_id.id)
        self.assertEqual(ctx["default_currency_id"], fund.currency_id.id)
        # Uložení z formuláře s předvyplněnými hodnotami: jen částka a poznámka.
        view = self.env.ref("investra_nav.view_valuation_external_correction_form")
        self.assertEqual(action["views"], [(view.id, "form")])
        entry = self.env["investra.valuation.external"].with_user(self.preparer).with_context(**ctx).create({
            "amount": -0.40, "note": "Faktura"})
        self.assertEqual(entry.corrects_rule_id, rule)
        self.assertEqual(entry.class_id, line.class_id)
        # ZJ-12 A.3: snímek vypočtené částky při zadání opravy (porovná ho krok 4).
        self.assertAlmostEqual(ctx["default_computed_at_entry"], line.amount, places=2)
        self.assertAlmostEqual(entry.computed_at_entry, line.amount, places=2)
        self.assertEqual((entry.correction_target, entry.validity), ("amount", "period"))

    def test_correction_sorted_under_original(self):
        fund = self.fund()
        first = self.rule(fund, name="Obhospodařování")
        second = self.rule(fund, name="Administrace", rate=0.002)
        valuation = self.valuation(fund, YEAR_END)
        self.manual_fee(valuation, 5)
        self.correction(valuation, first, -0.40)
        valuation.action_compute()
        # Pořadí dává _order modelu (jak ho čte formulář), ne cache One2many po vytvoření.
        lines = self.env["investra.valuation.fee"].search([("valuation_id", "=", valuation.id)])
        names = [(l.rule_id or l.external_id.corrects_rule_id).id for l in lines
                 if l.rule_id or l.external_id.corrects_rule_id]
        self.assertEqual(names, [first.id, first.id, second.id])
        self.assertTrue(lines[1].is_correction)
        self.assertFalse(lines[-1].rule_id)  # ruční úplata bez opravy na konci

    def test_correct_button_refused_outside_draft(self):
        fund = self.fund()
        self.rule(fund)
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        self.manual_fee(valuation, 5)
        valuation.action_compute()  # přepočet řádky rozpisu založí znovu
        self.assertFalse(valuation.fee_line_ids.filtered("external_id").can_correct)
        line = valuation.fee_line_ids.filtered("rule_id")
        valuation.sudo().state = "submitted"
        self.assertFalse(line.can_correct)
        with self.assertRaises(UserError):
            line.action_correct()
