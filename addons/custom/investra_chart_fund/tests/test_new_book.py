from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_chart_fund.models.template_investra_fund import ROLE_ACCOUNTS


@tagged("post_install", "-at_install")
class TestNewBookWizard(TransactionCase):
    """Průvodce Nová účetní kniha (MN-01): výsledek stejný jako create_book ze seedu."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.czk = cls.env.ref("base.CZK")
        cls.admin = cls.env.ref("base.user_admin")
        cls.Wizard = cls.env["investra.new.book.wizard"].with_user(cls.admin)

    def _create(self, **values):
        wizard = self.Wizard.create(values)
        action = wizard.action_create()
        # Po založení průvodce vrátí hlášku a v ní následný formulář knihy (MN-05).
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn("přepínači firem", action["params"]["message"])
        action = action["params"]["next"]
        entity = self.env["investra.entity"].browse(action["res_id"])
        self.assertEqual(action["res_model"], "investra.entity")
        self.assertIn(entity.company_id.id, action["context"]["allowed_company_ids"])
        return entity

    def _general_hashed(self, company):
        journals = self.env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")])
        self.assertTrue(journals)
        return set(journals.mapped("restrict_mode_hash_table"))

    def _assert_fund_book(self, entity, currency, rate_source):
        company = entity.company_id
        self.assertEqual(company.currency_id, currency)
        self.assertEqual(entity.rate_source, rate_source)
        self.assertEqual(company.chart_template, "investra_fund")
        self.assertTrue(company.restrictive_audit_trail)
        self.assertEqual(self._general_hashed(company), {True})
        Role = self.env["investra.account.role"]
        for code in ROLE_ACCOUNTS:
            self.assertTrue(Role.account_for(company, code), code)
        self.assertIn(company, self.admin.company_ids)

    def test_fund_czk(self):
        entity = self._create(name="Průvodce fond CZK", entity_type="fund", framework="cas501", currency_id=self.czk.id)
        self._assert_fund_book(entity, self.czk, "cnb")
        self.assertEqual((entity.entity_type, entity.framework), ("fund", "cas501"))

    def test_fund_eur(self):
        entity = self._create(name="Průvodce fond EUR", entity_type="fund", framework="cas501", currency_id=self.eur.id)
        self._assert_fund_book(entity, self.eur, "ecb")

    def test_manager_book(self):
        entity = self._create(name="Průvodce IS", entity_type="manager", framework="cas501")
        company = entity.company_id
        self.assertEqual(company.chart_template, "cz")
        self.assertEqual(company.currency_id, self.czk)
        self.assertTrue(company.restrictive_audit_trail)
        self.assertEqual(self._general_hashed(company), {False})
        self.assertIn(company, self.admin.company_ids)

    def test_browser_context_without_new_company(self):
        """Prohlížeč posílá allowed_company_ids jen s aktuální firmou a uživatel má víc firem (MN-05, bod 1)."""
        self.admin.company_ids |= self.env["res.company"].create({"name": "Druhá firma testu"})
        wizard = self.Wizard.with_context(allowed_company_ids=[self.admin.company_id.id]).create(
            {"name": "Průvodce prohlížeč", "entity_type": "fund", "framework": "cas501"})
        action = wizard.action_create()["params"]["next"]
        entity = self.env["investra.entity"].browse(action["res_id"])
        self.assertTrue(entity.exists())
        self.assertEqual(entity.entity_type, "fund")

    def test_founder_is_gone(self):
        self.assertNotIn("founder_id", self.env["investra.entity"]._fields)
        self.assertNotIn("founder_id", self.env["investra.new.book.wizard"]._fields)

    def test_parent_visible_and_required_only_for_subfund(self):
        from lxml import etree
        for model in ("investra.new.book.wizard", "investra.entity"):
            arch = etree.fromstring(self.env[model].get_view(view_type="form")["arch"])
            field = arch.xpath("//field[@name='parent_id']")[0]
            self.assertIn("subfund", field.get("invisible", ""), model)
            self.assertIn("subfund", field.get("required", ""), model)
            self.assertIn("sicav", self.env[model]._fields["parent_id"].domain, model)

    def test_subfund_under_sicav(self):
        sicav = self._create(name="Průvodce SICAV", entity_type="sicav", framework="cas501")
        sub = self._create(name="Průvodce podfond", entity_type="subfund", framework="cas501", parent_id=sicav.id)
        self.assertEqual(sub.parent_id, sicav)
        self.assertEqual(sub.company_id.chart_template, "investra_fund")

    def test_default_framework_by_type(self):
        wizard = self.Wizard.new({"entity_type": "service"})
        wizard._onchange_entity_type()
        self.assertEqual(wizard.framework, "cas500")
        self.assertEqual(wizard.template, "cz")
        wizard.entity_type = "fund"
        wizard._onchange_entity_type()
        self.assertEqual(wizard.framework, "cas501")
        self.assertEqual(wizard.template, "investra_fund")

    def test_mixed_framework_refused(self):
        companies = self.env["res.company"].search_count([])
        for entity_type, framework in (("fund", "cas500"), ("service", "cas501"), ("fund", "ifrs")):
            wizard = self.Wizard.create({"name": f"Zakázaná {entity_type} {framework}", "entity_type": entity_type,
                                         "framework": framework})
            with self.assertRaises(UserError):
                wizard.action_create()
        self.assertEqual(self.env["res.company"].search_count([]), companies)

    def test_subfund_needs_sicav(self):
        wizard = self.Wizard.create({"name": "Podfond bez SICAV", "entity_type": "subfund", "framework": "cas501"})
        with self.assertRaises(UserError):
            wizard.action_create()

    def test_duplicate_name_refused(self):
        self._create(name="Průvodce dvojí", entity_type="fund", framework="cas501")
        wizard = self.Wizard.create({"name": "Průvodce dvojí", "entity_type": "fund", "framework": "cas501"})
        with self.assertRaises(UserError):
            wizard.action_create()

    def test_only_system_admin(self):
        user = self.env["res.users"].create({
            "name": "Účetní průvodce", "login": "ucetni_pruvodce",
            "group_ids": [(6, 0, [self.env.ref("account.group_account_manager").id])],
        })
        with self.assertRaises(AccessError):
            self.env["investra.new.book.wizard"].with_user(user).create({"name": "X", "entity_type": "fund",
                                                                          "framework": "cas501"})
