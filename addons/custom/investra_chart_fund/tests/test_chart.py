from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_chart_fund.models.template_investra_fund import ROLE_ACCOUNTS


@tagged("post_install", "-at_install")
class TestChart(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.entity = cls.env["investra.entity"].create_book("Fond", "fund", "cas501", cls.eur, "investra_fund")
        cls.company = cls.entity.company_id

    def test_every_role_has_account(self):
        Role = self.env["investra.account.role"]
        all_roles = Role.search([])
        self.assertEqual(set(all_roles.mapped("code")), set(ROLE_ACCOUNTS))
        for role in all_roles:
            self.assertTrue(Role.account_for(self.company, role.code))

    def test_currency_survives_chart(self):
        self.assertEqual(self.company.currency_id, self.eur)

    def test_role_category_matches_account_type(self):
        Role = self.env["investra.account.role"]
        for role in Role.search([]):
            account = Role.account_for(self.company, role.code)
            expected = {"asset": "asset", "liability": "liability", "equity": "equity", "income": "income", "expense": "expense"}
            self.assertTrue(account.account_type.startswith(expected[role.category]), role.code)

    def test_no_czech_trade_taxes_loaded(self):
        self.assertFalse(self.env["account.tax"].search_count([("company_id", "=", self.company.id)]))

    def test_codes_follow_decree_501(self):
        """Syntetické účty rámce 501 (docs/osnova-501-syntetika.md, převodová tabulka v docs/osnova-fondu.md)."""
        Role = self.env["investra.account.role"]
        expected = {
            "bank": "131100", "cash_in_transit": "119000", "unidentified_payment": "229000", "deposit": "132000",
            "repo": "133000", "repo_client": "214000", "loan_given": "218000", "derivative": "313000",
            "internal_clearing": "341900", "fee_payable": "342300", "tax_payable": "347000", "accrual": "354000",
            "unsettled_payable": "371200", "subscription_payable": "376100", "instrument": "384000",
            "instrument_debt": "383000", "other_holding": "385000", "participation_fv": "413100", "participation": "413200",
            "class_capital": "564000", "loss_fair_value": "615000", "loss_fx": "616000", "expense_management": "636100",
            "expense_other": "667000", "expense_tax": "681000", "income_interest": "711000", "income_dividend": "714000",
            "gain_fair_value": "715000", "gain_fx": "716000", "income_other": "767000",
        }
        for role, code in expected.items():
            self.assertEqual(Role.with_company(self.company).account_for(self.company, role).with_company(self.company).code, code, role)
        Account = self.env["account.account"].with_company(self.company)
        codes = Account.search([("company_ids", "in", self.company.id)]).mapped("code")
        self.assertFalse([code for code in codes if code.startswith("9")], "Třída 9 je podle vyhlášky 501 podrozvaha.")
        self.assertIn("590000", codes)
        self.assertEqual(self.company.bank_account_code_prefix, "1311")
        self.assertFalse([code for code in codes if code.startswith(("999", "3221"))])

    def test_transit_and_unidentified_payments_split(self):
        """Převody mezi bankami jdou přes peníze na cestě, nevyjasněné položky výpisu na neidentifikované platby."""
        Role = self.env["investra.account.role"]
        transit = Role.account_for(self.company, "cash_in_transit")
        unidentified = Role.account_for(self.company, "unidentified_payment")
        self.assertEqual(self.company.transfer_account_id, transit)
        self.assertTrue(transit.reconcile)
        self.assertEqual(self.company.account_journal_suspense_account_id, unidentified)
        self.assertEqual(unidentified.account_type, "liability_current")
        bank = self.env["account.journal"].create({
            "name": "Banka testu", "code": "BTST", "type": "bank", "company_id": self.company.id,
        })
        self.assertEqual(bank.suspense_account_id, unidentified)
