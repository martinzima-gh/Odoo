from unittest.mock import patch

from odoo.addons.base.models.res_company import ResCompany as BaseCompany
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_entity.models.entity import ico_is_valid


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

    def test_book_survives_deferred_chart_loading(self):
        """Mimo testy Odoo při založení společnosti se zemí odloží načtení osnovy na commit.

        V testech základní install_l10n_modules vrací False, proto se běh mimo testy simuluje
        a odložené kroky se spustí jako při commitu. Odhad šablony je pevně cz (v holé databázi by
        patřil neinstalovanému modulu). Měna ani osnova se nesmí přepsat.
        """
        template_model = type(self.env["account.chart.template"])
        with (
            patch.object(BaseCompany, "install_l10n_modules", lambda self: True),
            patch.object(template_model, "_guess_chart_template", lambda self, country: "cz"),
        ):
            fund = self.Entity.create_book("Fond EUR commit", "fund", "cas501", self.eur, "cz")
            services = self.Entity.create_book("Servis commit", "service", "cas500", self.czk, "cz")
        self.env.cr.precommit.run()
        self.env.invalidate_all()
        self.assertEqual(fund.company_id.currency_id, self.eur)
        self.assertEqual(fund.company_id.chart_template, "cz")
        self.assertEqual(services.company_id.chart_template, "cz")

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

    def test_new_book_defaults_to_active_company(self):
        other = self.env["res.company"].create({"name": "Fond výchozí firma"})
        self.env.user.company_ids |= other
        Entity = self.Entity.with_context(allowed_company_ids=[other.id, self.env.company.id])
        self.assertEqual(Entity.default_get(["company_id"])["company_id"], other.id)
        field = self.Entity._fields["company_id"]
        self.assertEqual(field.domain, "[('id', 'in', allowed_company_ids)]")


@tagged("post_install", "-at_install")
class TestEntityIdentification(TransactionCase):
    """IČO, DIČ a existující kontakt (MN-06)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.Entity = cls.env["investra.entity"]

    def test_ico_check_digit(self):
        for valid in ("45274649", "00006947", "27082440"):
            self.assertTrue(ico_is_valid(valid), valid)
        for invalid in ("45274648", "4527464", "452746490", "abcdefgh", "", None, "٤٥٢٧٤٦٤٩"):
            self.assertFalse(ico_is_valid(invalid), invalid)

    def test_entity_edits_company_identification(self):
        entity = self.Entity.create_book("Fond IČO", "fund", "cas501", self.czk, "cz")
        entity.write({"company_registry": "45274649", "vat": "CZ45274649"})
        partner = entity.company_id.partner_id
        self.assertEqual(partner._get_additional_identifier("CZ_EN"), "45274649")
        self.assertEqual(partner.vat, "CZ45274649")

    def test_invalid_ico_is_refused_for_czech_company(self):
        entity = self.Entity.create_book("Fond IČO chyba", "fund", "cas501", self.czk, "cz")
        with self.assertRaises(ValidationError):
            entity.company_registry = "45274648"

    def test_create_book_takes_existing_partner(self):
        partner = self.env["res.partner"].create({
            "name": "Kontakt fondu", "additional_identifiers": {"CZ_EN": "45274649"},
            "company_id": self.env.company.id, "country_id": self.env.ref("base.cz").id})
        partners = self.env["res.partner"].search_count([])
        entity = self.Entity.create_book("Kontakt fondu", "fund", "cas501", self.czk, "cz", partner=partner)
        self.assertEqual(entity.company_id.partner_id, partner)
        self.assertFalse(partner.company_id)
        self.assertEqual(entity.company_registry, "45274649")
        self.assertEqual(self.env["res.partner"].search_count([]), partners)

    def test_create_book_without_partner_is_unchanged(self):
        entity = self.Entity.create_book("Fond bez kontaktu", "fund", "cas501", self.czk, "cz")
        self.assertEqual(entity.company_id.partner_id.name, "Fond bez kontaktu")
