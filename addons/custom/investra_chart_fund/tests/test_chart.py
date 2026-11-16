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
            expected = {"asset": "asset", "liability": "liability", "equity": "equity", "income": "income", "expense": "expense",
                        "off_balance": "off_balance"}
            self.assertTrue(account.account_type.startswith(expected[role.category]), role.code)

    def test_no_czech_trade_taxes_loaded(self):
        self.assertFalse(self.env["account.tax"].search_count([("company_id", "=", self.company.id)]))

    def test_codes_follow_decree_501(self):
        """Syntetické účty rámce 501 (docs/osnova-501-syntetika.md, převodová tabulka v docs/osnova-fondu.md)."""
        Role = self.env["investra.account.role"]
        expected = {
            "bank": "131100", "cash_in_transit": "119000", "cash_in_transit_receipt": "119100", "unidentified_payment": "229000", "deposit": "132000",
            "repo": "133000", "repo_client": "214000", "loan_given": "218000", "derivative": "313000",
            "internal_clearing": "341900", "fee_payable": "342300", "tax_payable": "347000", "accrual": "354000",
            "unsettled_payable": "371200", "subscription_payable": "376100", "instrument": "384000",
            "instrument_debt": "383000", "other_holding": "385000", "participation_fv": "413100", "participation": "413200",
            "class_capital": "564000", "loss_fair_value": "615000", "loss_fx": "616000", "expense_management": "636100",
            "expense_other": "667000", "expense_bank_fee": "612000", "expense_tax": "681000", "income_interest": "711000", "income_dividend": "714000",
            "gain_fair_value": "715000", "gain_realised": "715100", "loss_realised": "615100", "gain_fx": "716000", "income_other": "767000",
        }
        for role, code in expected.items():
            self.assertEqual(Role.with_company(self.company).account_for(self.company, role).with_company(self.company).code, code, role)
        Account = self.env["account.account"].with_company(self.company)
        codes = Account.search([("company_ids", "in", self.company.id)]).mapped("code")
        # Třída 9 je podle vyhlášky 501 podrozvaha: smí v ní být jen podrozvahové účty (FX spot, forward, swap – DE-03).
        class9 = Account.search([("company_ids", "in", self.company.id), ("code", "=like", "9%")])
        self.assertEqual(set(class9.mapped("account_type")), {"off_balance"})
        fx = {
            "derivative_liability": "313100", "derivative_swap": "313200", "derivative_swap_liability": "313300",
            "fx_spot_asset": "358100", "fx_spot_liability": "358200", "gain_derivative": "719100", "loss_derivative": "619100",
            "gain_derivative_swap": "719200", "loss_derivative_swap": "619200", "gain_fx_spot": "716100", "loss_fx_spot": "616100",
            "offbalance_forward_receivable": "953100", "offbalance_forward_payable": "954100",
            "offbalance_swap_receivable": "953200", "offbalance_swap_payable": "954200",
            "offbalance_spot_receivable": "943000", "offbalance_spot_payable": "944000", "offbalance_clearing": "992000",
        }
        for role, code in fx.items():
            self.assertEqual(Role.account_for(self.company, role).with_company(self.company).code, code, role)
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

    def test_outstanding_accounts_are_cash_in_transit(self):
        """Platby na cestě (Outstanding Receipts/Payments) jsou 119100/119200, ne mezi bankami 1311. Platby na cestě
        patří k roli peněz na cestě jako další účet (rozhodnutí 2026-11-12 „Role s více účty“), inkasa na cestě mají
        vlastní roli, na kterou účtují splátky nástrojů (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“)."""
        Role = self.env["investra.account.role"]
        chart = self.env["account.chart.template"].with_company(self.company)
        receipts = chart.ref("account_journal_payment_debit_account_id")
        payments = chart.ref("account_journal_payment_credit_account_id")
        self.assertEqual(receipts.with_company(self.company).code, "119100")
        self.assertEqual(payments.with_company(self.company).code, "119200")
        self.assertEqual(receipts, chart.ref("ifa_119100"))
        self.assertTrue(receipts.reconcile and payments.reconcile)
        transit = Role.accounts_for(self.company, "cash_in_transit")
        self.assertEqual(transit, Role.account_for(self.company, "cash_in_transit") | payments)
        self.assertEqual(Role.accounts_for(self.company, "cash_in_transit_receipt"), receipts)

    def test_bank_journals_belong_to_bank_role(self):
        """Účet každého bankovního deníku (i později založeného) patří k roli bank; účtuje se na hlavní účet role."""
        Role = self.env["investra.account.role"]
        journals = self.env["account.journal"].search([("company_id", "=", self.company.id), ("type", "=", "bank")])
        self.assertTrue(journals)
        bank = self.env["account.journal"].create({
            "name": "Druhá banka", "code": "BNK9", "type": "bank", "company_id": self.company.id,
        })
        accounts = Role.accounts_for(self.company, "bank")
        self.assertLessEqual(journals.default_account_id | bank.default_account_id, accounts)
        self.assertTrue(bank.default_account_id.with_company(self.company).code.startswith("1311"))
        self.assertEqual(Role.account_for(self.company, "bank").with_company(self.company).code, "131100")

    def test_reconcile_models(self):
        """Internal Transfers na převodový účet (peníze na cestě), Bank Fees na 612000 Bankovní poplatky."""
        chart = self.env["account.chart.template"].with_company(self.company)
        transfer = chart.ref("internal_transfer_reco")
        fees = chart.ref("bank_fees_reco")
        self.assertEqual(transfer.line_ids.account_id, self.company.transfer_account_id)
        self.assertEqual(fees.line_ids.account_id, chart.ref("ifa_612000"))
        self.assertEqual(fees.line_ids.account_id.with_company(self.company).code, "612000")

    def test_account_in_one_role_only(self):
        """Účet nesmí být ve dvou rolích, jinak by se ve výkazu započetl dvakrát."""
        from odoo.exceptions import ValidationError
        Role = self.env["investra.account.role"]
        mapping = self.env["investra.role.account"].search([
            ("company_id", "=", self.company.id), ("role_id.code", "=", "deposit"),
        ])
        with self.assertRaises(ValidationError):
            mapping.extra_account_ids = [(4, Role.account_for(self.company, "bank").id)]
        self.assertFalse(Role.add_extra_account(self.company, "deposit", Role.account_for(self.company, "bank")))


@tagged("post_install", "-at_install")
class TestRoleStandard(TransactionCase):
    """MN-04: značka odchylky mapování rolí od standardu."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.fund = cls.env["investra.entity"].create_book("Fond MN04", "fund", "cas501", cls.eur, "investra_fund").company_id
        cls.Mapping = cls.env["investra.role.account"].with_context(allowed_company_ids=cls.env["res.company"].search([]).ids)
        cls.chart = cls.env["account.chart.template"].with_company(cls.fund)

    def _mapping(self, company, code):
        return self.Mapping.search([("company_id", "=", company.id), ("role_id.code", "=", code)])

    def test_new_book_all_standard(self):
        mappings = self.Mapping.search([("company_id", "=", self.fund.id)])
        self.assertEqual(set(mappings.mapped("standard_state")), {"standard"})
        self.assertEqual(self.Mapping.search_count([("company_id", "=", self.fund.id), ("standard_state", "=", "deviation")]), 0)

    def test_manual_change_is_deviation(self):
        mapping = self._mapping(self.fund, "expense_other")
        other = self.chart.ref("ifa_661901")
        mapping.account_id = other
        self.assertEqual(mapping.standard_state, "deviation")
        self.assertEqual(mapping.standard_account_id, self.chart.ref(ROLE_ACCOUNTS["expense_other"]))
        found = self.Mapping.search([("standard_state", "=", "deviation")])
        self.assertIn(mapping, found)
        self.assertNotIn(self._mapping(self.fund, "bank"), found)
        self.assertNotIn(mapping, self.Mapping.search([("standard_state", "!=", "deviation")]))

    def test_extra_accounts_are_not_deviation(self):
        self.assertTrue(self._mapping(self.fund, "cash_in_transit").extra_account_ids)
        self.assertEqual(self._mapping(self.fund, "cash_in_transit").standard_state, "standard")

    def test_other_template_has_no_standard(self):
        company = self.env["investra.entity"].create_book("Společnost MN04", "manager", "cas501", self.eur, "cz").company_id
        role = self.env["investra.account.role"].search([("code", "=", "bank")], limit=1)
        account = self.env["account.account"].with_company(company).search([("company_ids", "in", company.id)], limit=1)
        mapping = self.Mapping.create({"company_id": company.id, "role_id": role.id, "account_id": account.id})
        self.assertEqual(mapping.standard_state, "none")
        self.assertFalse(mapping.standard_account_id)
        self.assertIn(mapping, self.Mapping.search([("standard_state", "=", "none")]))

    def test_apply_standard_role(self):
        """Po změně standardu se převede kniha bez odchylky; kniha s odchylkou zůstane a je vrácena."""
        other = self.env["investra.entity"].create_book("Fond MN04 b", "fund", "cas501", self.eur, "investra_fund").company_id
        old_xmlid, new_xmlid = "ifa_661901", ROLE_ACCOUNTS["expense_other"]
        for company in (self.fund, other):  # oba fondy měly dřív standard = starý účet
            self._mapping(company, "expense_other").account_id = self.env["account.chart.template"].with_company(company).ref(old_xmlid)
        # druhý fond má opravdovou odchylku (jiný účet než starý standard)
        deviant = self._mapping(other, "expense_other")
        deviant.account_id = self.env["account.chart.template"].with_company(other).ref("ifa_661902")
        result = self.Mapping._apply_standard_role("expense_other", old_xmlid=old_xmlid)
        self.assertEqual(self._mapping(self.fund, "expense_other").account_id, self.chart.ref(new_xmlid))
        self.assertEqual(self._mapping(self.fund, "expense_other").standard_state, "standard")
        self.assertEqual(deviant.account_id, self.env["account.chart.template"].with_company(other).ref("ifa_661902"))
        self.assertIn(deviant, result)
        self.assertNotIn(self._mapping(self.fund, "expense_other"), result)
