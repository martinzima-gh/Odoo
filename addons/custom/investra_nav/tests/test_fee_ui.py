"""ZJ-12 krok 5: rozhraní – schéma výpočtu fondu, pole Základ podle druhu, sloupce oprav, dialog Opravit, Ukončit opravu."""

import json
from datetime import date

from odoo.tests import Form, tagged

from .common import NavCase

JANUARY, FEBRUARY = date(2027, 1, 31), date(2027, 2, 28)


@tagged("post_install", "-at_install")
class TestFeeSchemeUi(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, classes=("A",)):
        fund = self.make_fund(classes=[{"code": c} for c in classes])
        for code in classes:
            self.subscribe(self.cls(fund, code), "2027-01-01", 1000000, 1000)
        return fund

    def periodic(self, fund, step="1", rate=0.012, source="fk"):
        return self.Rule.create({"fund_id": fund.id, "name": "Obhospodařování", "kind": "periodic", "base_step": step,
                                 "base_source": source, "expense_role": "expense_management",
                                 "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": rate})]})

    def performance(self, fund, code="A", step="2"):
        return self.Rule.create({
            "fund_id": fund.id, "name": "Odměna", "kind": "performance", "crystallisation": "none", "base_step": step,
            "class_ids": [(6, 0, self.cls(fund, code).ids)], "expense_role": "expense_performance",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "initial_reference": 0})]})

    def tax(self, fund, step="3"):
        return self.fund_tax(fund, 0.05, step)

    # --- pole Základ podle druhu -----------------------------------------------------------------------------------

    def test_base_step_views_by_kind(self):
        fund = self.fund()
        fee, perf, tax = self.periodic(fund), self.performance(fund), self.tax(fund)
        self.assertEqual((fee.base_step_fee, perf.base_step_performance, tax.base_step_tax), ("1", "2", "3"))
        self.assertFalse(fee.base_step_performance or fee.base_step_tax or perf.base_step_fee or tax.base_step_fee)
        perf.base_step_performance = "4"
        tax.base_step_tax = "1"
        fee.base_step_fee = "4"
        self.assertEqual((fee.base_step, perf.base_step, tax.base_step), ("4", "4", "1"))
        # Přípustné volby odměny jsou jen 1, 2 a 4 (3 v nabídce není).
        self.assertEqual([v for v, _ in self.Rule._fields["base_step_performance"].selection], ["1", "2", "4"])
        self.assertEqual([v for v, _ in self.Rule._fields["base_step_tax"].selection], ["1", "2", "3"])

    def test_rule_form_writes_base_step_and_warns(self):
        fund = self.fund()
        perf = self.performance(fund)
        with Form(perf) as form:
            form.base_step_performance = "1"
        self.assertEqual(perf.base_step, "1")
        def draft(rule, **values):
            step = next(iter(values.values()))
            return self.Rule.new({"kind": rule.kind, "base_source": rule.base_source, "base_step": step, **values}, origin=rule)

        self.assertIn("doúčtuje v dalším ocenění",
                      draft(perf, base_step_performance="4")._onchange_base_step_warning()["warning"]["message"])
        self.assertTrue(draft(self.tax(fund), base_step_tax="1")._onchange_base_step_warning())
        # Běžná úplata ze stavu k datu varování nemá, průměrný FK ano.
        fee = self.periodic(fund)
        self.assertIsNone(draft(fee, base_step_fee="2")._onchange_base_step_warning())
        average = self.periodic(fund, source="average_fk")
        self.assertTrue(draft(average, base_step_fee="2")._onchange_base_step_warning())

    # --- schéma výpočtu fondu --------------------------------------------------------------------------------------

    def test_presets(self):
        fund = self.fund()
        fee, perf, tax = self.periodic(fund), self.performance(fund, step="1"), self.tax(fund, step="1")
        fund.action_scheme_standard()
        self.assertEqual((fee.base_step, perf.base_step, tax.base_step), ("1", "2", "3"))
        # Rozhodnutí 2026-11-19: souhrn předvolby v chatteru fondu (jen změněná pravidla); bez změny se nic nezapíše.
        def notes():
            return fund.message_ids.filtered(lambda m: "Použita předvolba" in (m.body or ""))
        self.assertEqual(len(notes()), 1)
        self.assertIn("„Standardní fond“", notes().body)
        self.assertIn(f"{perf.name} 1 → 2", notes().body)
        self.assertIn(f"{tax.name} 1 → 3", notes().body)
        self.assertNotIn(fee.name, notes().body)
        fund.action_scheme_standard()
        self.assertEqual(len(notes()), 1)
        fund.action_scheme_net_fk()
        self.assertEqual((fee.base_step, perf.base_step, tax.base_step), ("4", "2", "2"))
        # Úplata ze základu Bez základu volbu nemá a předvolba ji nemění.
        none = self.periodic(fund, source="none")
        fund.action_scheme_net_fk()
        self.assertEqual(none.base_step, "1")

    def test_cycle_info(self):
        fund = self.fund()
        fee, tax = self.periodic(fund), self.tax(fund, step="3")
        self.assertFalse(fund.fee_scheme_cycle_info)
        fee.base_step = "4"
        fund.invalidate_recordset(["fee_scheme_cycle_info"])
        self.assertIn("Vzájemný dopočet", fund.fee_scheme_cycle_info)
        self.assertIn("Obhospodařování", fund.fee_scheme_cycle_info)
        self.assertIn("Není to chyba", fund.fee_scheme_cycle_info)
        # Úplata po kroku 4 a daň po kroku 1 (daň úplatu nezahrnuje) se nezacyklí.
        tax.base_step = "1"
        fund.invalidate_recordset(["fee_scheme_cycle_info"])
        self.assertFalse(fund.fee_scheme_cycle_info)  # úplata závisí na dani, daň (krok 1) na úplatě ne
        fee.base_step = "1"
        fund.invalidate_recordset(["fee_scheme_cycle_info"])
        self.assertFalse(fund.fee_scheme_cycle_info)

    def test_preview_uses_solver(self):
        # Úplata 1,2 % p. a. z FK 1 000 000 po kroku 1 za rok = 12 000; daň 5 % z (50 000 − 12 000) po kroku 2 = 1 900.
        fund = self.fund()
        self.periodic(fund)
        self.tax(fund, step="2")
        html = str(fund.fee_scheme_preview)
        self.assertIn("12 000,00", html)
        self.assertIn("1 900,00", html)
        self.assertIn("986 100,00", html)  # FK po úplatách a dani: 1 000 000 − 12 000 − 1 900
        self.assertIn("stejná funkce jako ocenění", html)

    def test_preview_matches_valuation_engine_for_net_fk(self):
        # Úplata po kroku 4 (z výsledného FK) a daň po kroku 2: společný dopočet, není to chyba; náhled se ustálí.
        fund = self.fund()
        self.periodic(fund, step="4")
        self.tax(fund, step="2")
        self.assertIn("Vzájemný dopočet", fund.fee_scheme_cycle_info)
        self.assertIn("<table", str(fund.fee_scheme_preview))

    # --- ocenění: sloupce oprav, dialog, ukončení --------------------------------------------------------------------

    def january(self, fund):
        valuation = self.valuation(fund, JANUARY)
        valuation.action_compute()
        return valuation

    def dialog(self, line, **values):
        """Dialog Opravit: stejný postup jako tlačítko na řádku."""
        action = line.action_correct()
        view = self.env["ir.ui.view"].browse(action["views"][0][0])
        form = Form(self.env["investra.valuation.external"].with_user(self.preparer).with_context(**action["context"]),
                    view=view)
        for name, value in values.items():
            setattr(form, name, value)
        return form

    def test_columns_appear_only_with_correction(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        self.assertFalse(valuation.has_corrections)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.assertEqual(line.fix_kind, "none")
        form = self.dialog(line, amount=-100, note="Faktura")
        form.save()
        valuation.invalidate_recordset()
        self.assertTrue(valuation.has_corrections)
        valuation.action_compute()
        rule_line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        fix = valuation.fee_line_ids.filtered(lambda l: l.external_id.corrects_rule_id == rule)
        self.assertEqual((rule_line.fix_kind, fix.fix_kind), ("rule", "correction"))
        self.assertAlmostEqual(rule_line.fix_computed, rule_line.amount, places=2)
        self.assertAlmostEqual(rule_line.fix_correction, -100, places=2)
        self.assertAlmostEqual(rule_line.fix_result, rule_line.amount - 100, places=2)
        self.assertEqual((fix.fix_note, fix.fix_user_id), ("Faktura", self.preparer))
        self.assertTrue(fix.fix_date)

    def test_dialog_target_amount_and_zero_out(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        computed = line.amount
        form = self.dialog(line)
        form.target_amount = 10
        self.assertAlmostEqual(form.amount, 10 - computed, places=2)
        form.amount = -5
        self.assertAlmostEqual(form.target_amount, computed - 5, places=2)
        form.zero_out = True
        self.assertAlmostEqual(form.amount, -computed, places=2)
        self.assertAlmostEqual(form.target_amount, 0, places=2)
        form.note = "Zrušeno dohodou"
        entry = form.save()
        self.assertAlmostEqual(entry.amount, -computed, places=2)
        valuation.action_compute()
        self.assertAlmostEqual(sum(valuation.fee_line_ids.filtered(
            lambda l: l.rule_id == rule or l.external_id.corrects_rule_id == rule).mapped("amount")), 0, places=2)

    def test_correct_button_for_performance_and_tax(self):
        fund = self.fund()
        perf, tax = self.performance(fund), self.tax(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        valuation = self.january(fund)
        for rule in (perf, tax):
            line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
            self.assertTrue(line.can_correct)
            form = self.dialog(line, amount=-10, note="Dohoda")
            self.assertEqual(form.validity, "period")
            form.validity = "valuation"
            form.save()
        valuation.action_compute()
        self.assertEqual(valuation.external_fee_ids.mapped("validity"), ["valuation", "valuation"])

    def test_keep_buttons_on_changed_correction(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.dialog(line, amount=-100, note="Faktura").save()
        valuation.action_compute()
        fix = valuation.fee_line_ids.filtered(lambda l: l.external_id.corrects_rule_id == rule)
        self.assertFalse(fix.correction_changed)
        self.common_result(fund, "v1", "2027-01-20", 1000000)
        valuation.action_compute()
        fix = valuation.fee_line_ids.filtered(lambda l: l.external_id.corrects_rule_id == rule)
        self.assertTrue(fix.correction_changed)
        fix.with_user(self.preparer).action_keep_difference()
        valuation.invalidate_recordset()
        fix = valuation.fee_line_ids.filtered(lambda l: l.external_id.corrects_rule_id == rule)
        self.assertFalse(fix.correction_changed)

    def test_carried_corrections_list_and_end_wizard(self):
        fund = self.fund()
        perf = self.performance(fund)
        self.common_result(fund, "v1", "2027-01-20", 100000)
        january = self.valuation(fund, JANUARY)
        january.action_compute()
        line = january.fee_line_ids.filtered(lambda l: l.rule_id == perf)
        entry = self.dialog(line, amount=-1000, note="Dohoda").save()
        self.run_to_posted(january)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        self.assertEqual(february.carried_correction_ids, entry)
        self.assertTrue(february.has_corrections)
        self.assertFalse(entry.is_ended)
        action = entry.with_context(ending_valuation_id=february.id).with_user(self.preparer).action_end_correction()
        wizard = self.env["investra.valuation.end.wizard"].with_user(self.preparer).with_context(**action["context"]).create(
            {"note": "Dohoda skončila"})
        wizard.action_confirm()
        february.action_compute()
        entry.invalidate_recordset(["is_ended"])
        self.assertTrue(entry.is_ended)
        self.assertEqual(february.external_fee_ids.ended_id, entry)
        detail = json.loads(february.fee_line_ids.filtered(lambda l: l.rule_id == perf).detail)
        self.assertEqual(float(detail["carried"]), -1000)

    def test_copy_from_version_flag(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        self.assertFalse(valuation.can_copy_from_version)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.dialog(line, amount=-100, note="Faktura").save()
        valuation.action_compute()
        valuation.action_submit()
        second = valuation.with_user(self.approver).action_return("Chyba")
        self.assertTrue(second.can_copy_from_version)
        second.with_user(self.preparer).action_copy_from_version()
        second.invalidate_recordset(["can_copy_from_version"])
        self.assertFalse(second.can_copy_from_version)

    # --- rozhodnutí 2026-11-19: jeden řádek na pravidlo, upozornění na základ třídy ---------------------------------

    def test_fee_tab_shows_one_row_per_rule(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        computed = line.amount
        self.dialog(line, amount=-100, note="Faktura").save()
        self.dialog(line, amount=-1, note="Zaokrouhlení").save()
        valuation.action_compute()
        valuation.invalidate_recordset()
        shown = valuation.fee_rule_line_ids
        self.assertFalse(shown.filtered("is_correction"))
        self.assertEqual(len(valuation.fee_line_ids) - len(shown), 2)
        row = shown.filtered(lambda l: l.rule_id == rule)
        self.assertAlmostEqual(row.fix_computed, computed, places=2)
        self.assertAlmostEqual(row.fix_correction, -101, places=2)
        self.assertAlmostEqual(row.fix_amount, computed - 101, places=2)
        self.assertEqual(row.fix_note, "Faktura; Zaokrouhlení")
        self.assertEqual(row.fix_user_id, self.preparer)
        # Součet sloupce Částka = součet celého rozpisu (pravidla + opravy).
        self.assertAlmostEqual(sum(shown.mapped("fix_amount")), sum(valuation.fee_line_ids.mapped("amount")), places=2)

    def test_keep_buttons_on_rule_row(self):
        fund = self.fund()
        rule = self.periodic(fund)
        valuation = self.january(fund)
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.dialog(line, amount=-100, note="Faktura").save()
        valuation.action_compute()
        self.common_result(fund, "v1", "2027-01-20", 1000000)
        valuation.action_compute()
        valuation.invalidate_recordset()
        row = valuation.fee_rule_line_ids.filtered(lambda l: l.rule_id == rule)
        self.assertTrue(row.correction_changed)
        row.with_user(self.preparer).action_keep_result()
        valuation.invalidate_recordset()
        row = valuation.fee_rule_line_ids.filtered(lambda l: l.rule_id == rule)
        self.assertFalse(row.correction_changed)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "correction_changed").status, "ok")

    def test_class_base_without_classes_warns(self):
        fund = self.fund()
        rule = self.periodic(fund)
        rule.base_source = "class_fk"
        self.assertIn("pole Třídy je prázdné", rule.class_base_warning)
        rule.class_ids = fund.class_ids[:1]
        self.assertFalse(rule.class_base_warning)

    def test_tax_has_no_classes_or_recipients(self):
        from odoo.exceptions import ValidationError
        fund = self.fund()
        tax = self.tax(fund)
        with self.assertRaisesRegex(ValidationError, "daň je náklad celého fondu"):
            tax.class_ids = fund.class_ids[:1]
        with self.assertRaisesRegex(ValidationError, "daň je náklad celého fondu"):
            tax.recipient_share = 0.5

    def test_setup_warnings_for_unused_fields(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        rule = self.periodic(fund, source="average_fk")
        self.assertFalse(rule.class_base_warning)
        # ZJ-14: průměrný FK s třídami se počítá po třídách, upozornění zrušeno.
        rule.class_ids = self.cls(fund, "A")
        self.assertFalse(rule.class_base_warning)
        rule.class_ids = False
        rule.recipient_share = 0.5
        self.assertIn("nejsou zvolené přijímající třídy", rule.class_base_warning)
        rule.write({"recipient_share": 0, "recipient_class_ids": [(6, 0, self.cls(fund, "B").ids)]})
        self.assertIn("podíl příjemcům je 0", rule.class_base_warning)

