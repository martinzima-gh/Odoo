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
