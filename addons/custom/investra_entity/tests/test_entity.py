from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEntity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.eur = cls.env.ref("base.EUR")
        (cls.czk | cls.eur).active = True
        cls.Entity = cls.env["investra.entity"]

    def test_rate_source_follows_currency(self):
        self.assertEqual(self.Entity.create_book("Fond CZK", "fund", "cas501", self.czk, "cz").rate_source, "cnb")
        self.assertEqual(self.Entity.create_book("Fond EUR zdroj", "fund", "cas501", self.eur, "cz").rate_source, "ecb")

    def test_wrong_rate_source_is_refused(self):
        entity = self.Entity.create_book("Fond zdroj", "fund", "cas501", self.czk, "cz")
        with self.assertRaises(ValidationError):
            entity.rate_source = "ecb"

    def test_eur_fund_keeps_functional_currency_after_chart(self):
        entity = self.Entity.create_book("Fond EUR", "fund", "cas501", self.eur, "cz")
        self.assertEqual(entity.company_id.currency_id, self.eur)

    def test_fund_book_has_mandatory_settings(self):
        company = self.Entity.create_book("Fond", "fund", "cas501", self.czk, "cz").company_id
        self.assertTrue(company.restrictive_audit_trail)
        self.assertFalse(company.autopost_bills)
        general = self.env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")])
        self.assertTrue(general)
        self.assertTrue(all(general.mapped("restrict_mode_hash_table")))

    def test_service_book_has_no_hash(self):
        company = self.Entity.create_book("Služby", "service", "cas500", self.czk, "cz").company_id
        general = self.env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")])
        self.assertFalse(any(general.mapped("restrict_mode_hash_table")))

    def test_subfund_requires_sicav_parent(self):
        fund = self.Entity.create_book("Fond", "fund", "cas501", self.czk, "cz")
        with self.assertRaises(ValidationError):
            self.Entity.create_book("Podfond", "subfund", "cas501", self.czk, "cz", parent_id=fund.id)

    def test_missing_role_is_error(self):
        company = self.Entity.create_book("Fond", "fund", "cas501", self.czk, "cz").company_id
        with self.assertRaises(UserError):
            self.env["investra.account.role"].account_for(company, "bank")

    def test_framework_locked_after_posting(self):
        entity = self.Entity.create_book("Služby", "service", "cas500", self.czk, "cz")
        company = entity.company_id
        env = self.env(context=dict(self.env.context, allowed_company_ids=[company.id]))
        accounts = env["account.account"].search([("company_ids", "in", company.id)], limit=2)
        journal = env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")], limit=1)
        env["account.move"].create({
            "journal_id": journal.id,
            "line_ids": [
                (0, 0, {"account_id": accounts[0].id, "debit": 1}),
                (0, 0, {"account_id": accounts[1].id, "credit": 1}),
            ],
        }).action_post()
        with self.assertRaises(UserError):
            entity.framework = "ifrs"
