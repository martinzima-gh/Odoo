"""ZJ-11: oprava vypočtené úplaty ruční úplatou s polem „Opravuje úplatu“ (rozhodnutí 2026-11-18)."""

import json
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
        # ZJ-12 krok 3 (schváleno 2026-11-18, příklad C8): úplata po kroku 2, oprava −100 ve dvou průchodech.
        # Vypočteno bez opravy S = 0,01 × (1 000 000 − S) = 9 900,99; výsledek = vypočteno + oprava = 9 800,99;
        # FK = 1 000 000 − 9 800,99 = 990 199,01. Dřív oprava posunula základ: 9 901,98 a FK 990 198,02.
        fund = self.fund()
        rule = self.rule(fund, base_step="2")
        valuation = self.valuation(fund, YEAR_END)
        self.correction(valuation, rule, -100)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fee_line_ids.filtered("rule_id").amount, 9900.99, places=2)
        self.assertAlmostEqual(sum(valuation.fee_line_ids.mapped("amount")), 9800.99, places=2)
        self.assertAlmostEqual(valuation.fund_capital, 990199.01, places=2)

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

    # --- váhy přijímajících tříd (revize CP-2026-11-19, rozhodnutí 2026-11-19) ---------------------------------------

    def recipient_fund(self, recipients, subscribed=("A",)):
        fund = self.make_fund(classes=[{"code": c} for c in ("A",) + recipients])
        for code in subscribed:
            self.subscribe(self.cls(fund, code), "2027-01-01", 1000, 1000)
        rule = self.rule(fund, rate=1.0, name="Dělená", base_source="class_fk",
                         class_ids=[(6, 0, self.cls(fund, "A").ids)], recipient_share=0.5, expense_role="expense_other",
                         recipient_class_ids=[(6, 0, [self.cls(fund, c).id for c in recipients])])
        return fund, rule

    def transfers(self, valuation, rule):
        """Přesuny podílu příjemcům na dokladu úplaty podle třídy (účet vnitřního zúčtování)."""
        clearing = self.expense_account(valuation.fund_id, "internal_clearing").code
        event = valuation.event_ids.filtered(lambda e: f":fee:{rule.id}:" in e.key)
        return {code: amount for (account, code), amount in self.balances(event).items() if account == clearing}

    def test_single_recipient_with_zero_capital_gets_whole_share(self):
        # Třída B (jen přijímá odměnu) zatím bez kapitálu: celý podíl 42,47 dostane B; dopočet = doklad = rozpad.
        fund, rule = self.recipient_fund(("B",))
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered("rule_id")
        to_b = round(line.amount * 0.5, 2)
        self.assertEqual(self.transfers(valuation, rule).get("B"), to_b)
        self.assertAlmostEqual(self.result(valuation, "B").capital, to_b, places=2)
        detail = json.loads(line.detail)
        self.assertAlmostEqual(float(detail["borne"][str(self.cls(fund, "B").id)]), -to_b, places=2)
        self.assertAlmostEqual(float(detail["expense"]), line.amount - to_b, places=2)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "clearing_zero").status, "ok")

    def test_two_recipients_nonpositive_gets_nothing(self):
        # B s kapitálem, C bez kapitálu: celý podíl dostane B, C nic (jako dosud).
        fund, rule = self.recipient_fund(("B", "C"), subscribed=("A", "B"))
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered("rule_id")
        transfers = self.transfers(valuation, rule)
        self.assertEqual(transfers.get("B"), round(line.amount * 0.5, 2))
        self.assertFalse(transfers.get("C"))
        self.assertAlmostEqual(self.result(valuation, "C").capital, 0, places=2)

    def test_two_recipients_without_positive_value_stop(self):
        fund, rule = self.recipient_fund(("B", "C"))
        valuation = self.valuation(fund, YEAR_END)
        with self.assertRaisesRegex(UserError, "Pravidlo Dělená: žádná přijímající třída nemá kladnou hodnotu"):
            valuation.action_compute()

    def test_average_fk_recipients_in_solver_like_posting(self):
        # Rozhodnutí 2026-11-19: průměrný FK s příjemci – dopočet zná příjemce, náklad = částka − podíl jako na dokladu.
        fund = self.make_fund(classes=[{"code": c} for c in ("A", "B")])
        for code in ("A", "B"):
            self.subscribe(self.cls(fund, code), "2027-01-01", 1000, 1000)
        rule = self.rule(fund, rate=0.12, name="Průměr", base_source="average_fk", recipient_share=0.5,
                         recipient_class_ids=[(6, 0, self.cls(fund, "B").ids)], expense_role="expense_other")
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered("rule_id")
        to_b = round(line.amount * 0.5, 2)
        self.assertTrue(to_b)
        self.assertEqual(self.transfers(valuation, rule).get("B"), to_b)
        detail = json.loads(line.detail)
        self.assertAlmostEqual(float(detail["expense"]), line.amount - to_b, places=2)
        # B nese polovinu úplaty (poměr) a dostane podíl stejné výše: nesená částka 0 se do detailu neukládá.
        self.assertAlmostEqual(float(detail["borne"].get(str(self.cls(fund, "B").id), 0)), line.amount / 2 - to_b, delta=0.01)
        self.assertAlmostEqual(float(detail["borne"][str(self.cls(fund, "A").id)]), line.amount / 2, delta=0.01)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "fee_consistency").status, "ok")
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "classes_sum").status, "ok")

    def test_fund_fee_with_recipients_posts(self):
        # Úplata celého fondu (bez Platí třídy) s příjemcem B: dřív pád při zaúčtování (plátce None).
        fund = self.make_fund(classes=[{"code": c} for c in ("A", "B")])
        for code in ("A", "B"):
            self.subscribe(self.cls(fund, code), "2027-01-01", 1000, 1000)
        rule = self.rule(fund, rate=0.12, name="Fondová", recipient_share=0.5,
                         recipient_class_ids=[(6, 0, self.cls(fund, "B").ids)], expense_role="expense_other")
        valuation = self.valuation(fund, YEAR_END)
        valuation.action_compute()
        line = valuation.fee_line_ids.filtered("rule_id")
        to_b = round(line.amount * 0.5, 2)
        self.assertEqual(self.transfers(valuation, rule), {"": -to_b, "B": to_b})
        # A nese polovinu úplaty, B polovinu a dostane podíl: A = 1000 − amount/2, B = 1000 − amount/2 + podíl.
        self.assertAlmostEqual(self.result(valuation, "A").capital, 1000 - line.amount / 2, delta=0.01)
        self.assertAlmostEqual(self.result(valuation, "B").capital, 1000 - line.amount / 2 + to_b, delta=0.01)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "clearing_zero").status, "ok")

    def test_effect_detail_splits_recipients_like_posting(self):
        # Nález 1: úplata 0,01, celý podíl třem příjemcům se stejnou vahou → doklad 0,01 / 0 / 0, rozpad stejně.
        from decimal import Decimal
        fund, rule = self.recipient_fund(("B", "C", "D"), subscribed=("A", "B", "C", "D"))
        rule.recipient_share = 1.0
        valuation = self.valuation(fund, YEAR_END)
        classes = {c: self.cls(fund, c) for c in ("A", "B", "C", "D")}
        values = {cls: Decimal(1000) for cls in classes.values()}
        item = {"rule": rule, "payer": classes["A"].id, "share": Decimal(1),
                "recipients": {cls.id: Decimal(1) for code, cls in classes.items() if code != "A"}}
        ratios = {cls.id: Decimal("0.25") for cls in classes.values()}
        posted = valuation._recipient_parts(rule, Decimal("0.01"), values)
        self.assertEqual(sorted(str(v) for v in posted.values()), ["0.00", "0.00", "0.01"])
        detail = valuation._effect_detail(item, Decimal("0.01"), ratios, values)
        expected = {str(cls.id): -part for cls, part in posted.items() if part}
        expected[str(classes["A"].id)] = Decimal("0.01")
        self.assertEqual({k: Decimal(v) for k, v in detail["borne"].items()}, expected)
        self.assertEqual(detail["expense"], Decimal("0.00"))

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
