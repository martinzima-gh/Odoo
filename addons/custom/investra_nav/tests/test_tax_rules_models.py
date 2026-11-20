from datetime import date

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestTaxRulesModels(NavCase):
    """ZJ-07 (běh 4): daňová pravidla, výjimky a pole fondu (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 9.3 C2)."""

    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.tax.rule"]
        self.Exception = self.env["investra.fund.tax.exception"]
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.company = self.fund.company_id
        self.Role = self.env["investra.account.role"]

    def rule(self, xmlid):
        return self.env.ref(f"investra_nav.{xmlid}")

    def account(self, code):
        return self.env["account.account"].search([("code", "=", code), ("company_ids", "in", self.company.ids)])

    def new_rule(self, **vals):
        values = {"name": "Zkušební", "kind": "general", "method": "current", "tax_account_code": "681000",
                  "balance_account_code": "347000",
                  "version_ids": [(0, 0, {"valid_from": "2024-01-01", "rate": 0.1})], **vals}
        return self.Rule.create(values)

    # --- data a účty šablony ---------------------------------------------------------------------------------------

    def test_default_rules(self):
        self.assertEqual(self.rule("tax_rule_21").rate_now, 0.21)
        self.assertEqual(self.rule("tax_rule_zif_5").rate_now, 0.05)
        separate = self.rule("tax_rule_separate_15")
        self.assertEqual((separate.kind, separate.rate_now, separate.credit_account_code), ("separate", 0.15, "681400"))
        exempt = self.rule("tax_rule_exempt")
        self.assertEqual((exempt.kind, exempt.version_ids, exempt.tax_account_code), ("exempt", self.env["investra.tax.rule.version"], False))
        for xmlid, rate in (("tax_rule_deferred_fvoci_21", 0.21), ("tax_rule_deferred_fvoci_5", 0.05)):
            rule = self.rule(xmlid)
            self.assertEqual((rule.method, rule.tax_account_code, rule.balance_account_code, rule.recognise_asset, rule.rate_now),
                             ("deferred", "564400", "348000", False, rate))

    def test_template_accounts_and_roles(self):
        for role, code in (("income_dividend", "714100"), ("income_dividend", "714200"), ("income_dividend", "714300"),
                           ("expense_other", "667300"), ("expense_other", "667400"), ("expense_other", "667500"),
                           ("expense_tax", "681100"), ("expense_tax", "681200"), ("expense_tax", "681300"),
                           ("expense_tax", "681400"), ("expense_tax", "682000"), ("tax_payable", "347300"),
                           ("tax_payable", "348000"), ("receivable_other", "341210"), ("receivable_other", "341220"),
                           ("revaluation_reserve", "564500"), ("retained_result", "571100")):
            self.assertIn(code, self.Role.accounts_for(self.company, role).mapped("code"), (role, code))
        self.assertEqual(self.Role.account_for(self.company, "revaluation_reserve").code, "564300")
        self.assertEqual(self.Role.account_for(self.company, "revaluation_reserve_tax").code, "564400")

    def test_book_accounts_resolve_and_check_roles(self):
        accounts = self.rule("tax_rule_separate_15")._book_accounts(self.company)
        self.assertEqual({key: account.code for key, account in accounts.items()},
                         {"tax": "681300", "balance": "347300", "credit": "681400"})
        deferred = self.rule("tax_rule_deferred_fvoci_21")._book_accounts(self.company)
        self.assertEqual((deferred["tax"].code, deferred["balance"].code), ("564400", "348000"))
        with self.assertRaises(UserError):
            self.new_rule(tax_account_code="999999")._book_accounts(self.company)
        with self.assertRaises(UserError):  # rozvahový účet bez role tax_payable
            self.new_rule(balance_account_code="221100")._book_accounts(self.company)

    # --- kontroly pravidla a sazeb ---------------------------------------------------------------------------------

    def test_rule_setup_checks(self):
        with self.assertRaises(ValidationError):  # Mimo základ nemá účty
            self.Rule.create({"name": "X", "kind": "exempt", "tax_account_code": "681000"})
        with self.assertRaises(ValidationError):  # základ bez účtu
            self.new_rule(balance_account_code=False)
        with self.assertRaises(ValidationError):  # zápočet jen u splatné
            self.new_rule(method="deferred", credit_account_code="681400")
        with self.assertRaises(ValidationError):  # pohledávka jen u odložené
            self.new_rule(recognise_asset=True)
        with self.assertRaises(ValidationError):  # bez sazby
            self.new_rule(version_ids=[])

    def test_version_checks(self):
        rule = self.new_rule()
        with self.assertRaises(ValidationError):
            self.env["investra.tax.rule.version"].create({"rule_id": rule.id, "valid_from": "2025-01-01", "rate": 21})
        self.env["investra.tax.rule.version"].create({"rule_id": rule.id, "valid_from": "2025-01-01", "rate": 0.2})
        self.assertEqual(rule._version_at(date(2024, 6, 1)).rate, 0.1)
        self.assertEqual(rule._version_at(date(2025, 6, 1)).rate, 0.2)
        with self.assertRaises(UserError):
            rule._version_at(date(2023, 1, 1))

    # --- výjimky ---------------------------------------------------------------------------------------------------

    def exception(self, code, xmlid, **vals):
        return self.Exception.create({"fund_id": self.fund.id, "account_id": self.account(code).id,
                                      "tax_rule_id": self.rule(xmlid).id, **vals})

    def test_exception_checks(self):
        self.exception("714100", "tax_rule_exempt", nondeductible_pct=5)
        with self.assertRaises(Exception), mute_logger("odoo.sql_db"):  # unikátní (fond, účet)
            with self.cr.savepoint():
                self.exception("714100", "tax_rule_exempt")
        with self.assertRaises(ValidationError):
            self.exception("714200", "tax_rule_exempt", share=0)
        with self.assertRaises(ValidationError):
            self.exception("714200", "tax_rule_exempt", share=1.5)
        with self.assertRaises(ValidationError):  # neuznatelné jen u výnosu
            self.exception("667300", "tax_rule_exempt", nondeductible_pct=5)
        with self.assertRaises(ValidationError):  # účet daně se nikdy nepočítá
            self.exception("681000", "tax_rule_exempt")
        with self.assertRaises(ValidationError):  # výsledkový účet s odloženým pravidlem
            self.exception("714200", "tax_rule_deferred_fvoci_21")

    def test_balance_account_may_have_current_rule_d10(self):
        # D10: rozvahový účet smí mít i splatné pravidlo (realizované přecenění FVOCI); odložené pravidlo také.
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        self.exception("571100", "tax_rule_21")
        self.exception("564300", "tax_rule_deferred_fvoci_21")
        with self.assertRaises(ValidationError):  # Mimo základ na rozvahovém účtu nemá smysl
            self.exception("564500", "tax_rule_exempt")

    def test_movement_since_period_start(self):
        account = self.account("714100")
        exception = self.exception("714100", "tax_rule_exempt")
        self.assertEqual(exception.movement_ytd, 0)
        today = fields.Date.context_today(self.fund)
        self.book(self.fund, "div", today, [
            {"role": "bank", "amount": "1000"},
            {"role": "income_dividend", "amount": "-1000", "extra": {"account_id": account.id}},
        ])
        exception.invalidate_recordset()
        self.assertEqual(exception.movement_ytd, 1000)  # kredit výnosu = +

    # --- pole fondu a nosič ----------------------------------------------------------------------------------------

    def test_default_rule_creates_and_archives_carrier(self):
        Fee = self.env["investra.fee.rule"].with_context(active_test=False)
        self.assertFalse(self.fund.tax_fee_rule_id)
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        carrier = self.fund.tax_fee_rule_id
        self.assertEqual((carrier.kind, carrier.active, carrier.base_step), ("tax", True, "3"))
        self.assertEqual(self.fund.tax_rate_now, 0.21)
        self.fund.tax_base_step = "2"
        self.assertEqual(carrier.base_step, "2")
        self.fund.tax_rule_id = self.rule("tax_rule_zif_5")  # změna pravidla nezakládá druhý nosič
        self.assertEqual(Fee.search_count([("fund_id", "=", self.fund.id), ("kind", "=", "tax")]), 1)
        self.fund.tax_rule_id = False
        self.assertFalse(self.fund.tax_fee_rule_id)
        self.assertFalse(Fee.search([("fund_id", "=", self.fund.id), ("kind", "=", "tax")]).active)
        self.fund.tax_rule_id = self.rule("tax_rule_21")  # znovu aktivní, stejný nosič
        self.assertEqual(self.fund.tax_fee_rule_id, carrier)
        self.assertTrue(carrier.active)

    def test_default_rule_must_be_current_general(self):
        for xmlid in ("tax_rule_separate_15", "tax_rule_exempt", "tax_rule_deferred_fvoci_21"):
            with self.subTest(xmlid=xmlid), self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.fund.tax_rule_id = self.rule(xmlid)

    def test_used_rules_must_not_share_accounts(self):
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        self.exception("714200", "tax_rule_separate_15")  # jiné účty daně, rozvahy i zápočtu: v pořádku
        with self.assertRaises(ValidationError):  # 5 % ZIF sdílí 681000/347000 s výchozím 21 %
            self.exception("667300", "tax_rule_zif_5")

    # --- běžné výjimky ---------------------------------------------------------------------------------------------

    def test_add_common_exceptions(self):
        with self.assertRaises(UserError):
            self.fund.action_add_common_tax_exceptions()
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        self.fund.action_add_common_tax_exceptions()
        rows = {e.account_id.code: e for e in self.fund.tax_exception_ids}
        self.assertEqual(set(rows), {"714100", "714200", "714300", "667300", "667400"})
        self.assertEqual((rows["714100"].tax_rule_id, rows["714100"].nondeductible_pct), (self.rule("tax_rule_exempt"), 5))
        self.assertEqual((rows["714200"].tax_rule_id, rows["714200"].nondeductible_pct), (self.rule("tax_rule_separate_15"), 5))
        self.assertEqual(rows["714300"].nondeductible_pct, 0)
        rows["714100"].tax_rule_id = self.rule("tax_rule_separate_15")  # ruční změna se nepřepíše
        self.fund.action_add_common_tax_exceptions()
        self.assertEqual(len(self.fund.tax_exception_ids), 5)
        self.assertEqual(rows["714100"].tax_rule_id, self.rule("tax_rule_separate_15"))

    def fvoci_fund(self, rate_rule):
        fund = self.make_fund(classes=[{"code": "A"}])
        fund.tax_rule_id = self.rule(rate_rule)
        bond = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Dluhopis {fund.id}", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id,
        }, fund))
        self.classify(fund, bond, "hold_collect_sell")
        return fund

    def test_fvoci_adds_deferred_tax_and_realisation_exceptions(self):
        for rate_rule, deferred in (("tax_rule_21", "tax_rule_deferred_fvoci_21"), ("tax_rule_zif_5", "tax_rule_deferred_fvoci_5")):
            with self.subTest(rate_rule=rate_rule):
                fund = self.fvoci_fund(rate_rule)
                fund.action_add_common_tax_exceptions()
                rows = {e.account_id.code: e.tax_rule_id for e in fund.tax_exception_ids}
                self.assertEqual(rows["564300"], self.rule(deferred))  # D9 podle sazby výchozího pravidla
                self.assertEqual(rows["571100"], self.rule(rate_rule))  # D10 splatné výchozí pravidlo
                self.assertEqual(len(rows), 7)
        # Bez FVOCI se nic nepřidá a ECL výjimku tlačítko nepřidává (D12).
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        self.fund.action_add_common_tax_exceptions()
        self.assertNotIn("564300", self.fund.tax_exception_ids.account_id.mapped("code"))
        self.assertNotIn("667500", self.fund.tax_exception_ids.account_id.mapped("code"))

    # --- oprava daně -----------------------------------------------------------------------------------------------

    def correction(self, valuation, **vals):
        return self.env["investra.valuation.external"].create({
            "valuation_id": valuation.id, "corrects_rule_id": self.fund.tax_fee_rule_id.id, "amount": 10, "note": "Oprava",
            "correction_target": "base", **vals})

    def test_tax_correction_needs_rule_used_in_fund(self):
        self.fund.tax_rule_id = self.rule("tax_rule_21")
        self.exception("714200", "tax_rule_separate_15")
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        with self.assertRaises(ValidationError):  # povinné u fondu s daňovým pravidlem
            self.correction(valuation)
        with self.assertRaises(ValidationError):  # Mimo základ ani nepoužité pravidlo se neopravuje
            self.correction(valuation, tax_rule_id=self.rule("tax_rule_zif_5").id)
        row = self.correction(valuation, tax_rule_id=self.rule("tax_rule_separate_15").id)
        self.assertEqual(row.tax_rule_id, self.rule("tax_rule_separate_15"))
        row2 = self.correction(valuation, tax_rule_id=self.rule("tax_rule_21").id)
        self.assertTrue(row2)
        with self.assertRaises(ValidationError):  # pravidlo se vyplňuje jen u opravy daně
            self.env["investra.valuation.external"].create({
                "valuation_id": valuation.id, "amount": 5, "note": "x", "account_id": self.account("667000").id,
                "tax_rule_id": self.rule("tax_rule_21").id})
