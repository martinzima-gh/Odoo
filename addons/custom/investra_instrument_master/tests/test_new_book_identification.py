from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

LEI = "5493001KJTIIGC8Y1R12"
ICO = "45274649"


@tagged("post_install", "-at_install")
class TestNewBookIdentification(TransactionCase):
    """Identifikace v průvodci Nová účetní kniha: IČO, DIČ, LEI, kód ESA a existující kontakt (MN-06)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.CZK").active = True
        cls.admin = cls.env.ref("base.user_admin")
        cls.Wizard = cls.env["investra.new.book.wizard"].with_user(cls.admin)
        cls.code = cls.env["investra.esa.code"].search([("code", "=", "1240200")])
        cls.cz = cls.env.ref("base.cz")

    def _create(self, **values):
        values.setdefault("entity_type", "fund")
        values.setdefault("framework", "cas501")
        action = self.Wizard.create(values).action_create()
        return self.env["investra.entity"].browse(int(action["url"].rsplit("/", 1)[1]))

    def test_identification_creates_profile(self):
        entity = self._create(name="Fond s identifikací", company_registry=ICO, vat=f"CZ{ICO}", lei=LEI,
                              esa_code_id=self.code.id)
        company = entity.company_id
        self.assertEqual(
            (company.partner_id._get_additional_identifier("CZ_EN"), company.vat), (ICO, f"CZ{ICO}"))
        profile = company.partner_id._counterparty_profile()
        self.assertEqual((profile.lei, profile.esa_code_id, profile.country_id), (LEI, self.code, self.cz))
        self.assertEqual(profile.sector_id, self.code.esa2010_sector_id)
        self.assertEqual((entity.lei, entity.esa_sector_id), (LEI, profile.sector_id))

    def test_without_identification_no_profile(self):
        entity = self._create(name="Fond bez identifikace")
        self.assertFalse(entity.company_id.partner_id._counterparty_profile())
        self.assertFalse(entity.company_registry or entity.vat)

    def test_invalid_ico_lei_and_missing_code_are_refused_before_creating(self):
        companies = self.env["res.company"].search_count([])
        partners = self.env["res.partner"].search_count([])
        for values in (
                {"company_registry": "45274648"},
                {"lei": "5493001KJTIIGC8Y1R13", "esa_code_id": self.code.id},
                {"lei": LEI},  # LEI bez kódu: profil by neměl sektor
                {"esa_code_id": self.env["investra.esa.code"].search([("residency", "=", "nr")], limit=1).id},
        ):
            with self.assertRaises(UserError, msg=str(values)):
                self._create(name="Chybná identifikace", **values)
        self.assertEqual(self.env["res.company"].search_count([]), companies)
        self.assertEqual(self.env["res.partner"].search_count([]), partners)

    def test_lei_of_other_counterparty_is_refused(self):
        other = self.env["res.partner"].create({"name": "Má LEI"})
        self.env["investra.counterparty.profile"].create({
            "partner_id": other.id, "country_id": self.cz.id, "esa_code_id": self.code.id, "lei": LEI})
        with self.assertRaises(UserError):
            self._create(name="Fond LEI obsazené", lei=LEI, esa_code_id=self.code.id)

    def test_vat_is_prefilled_from_czech_ico_and_can_be_overwritten(self):
        wizard = self.Wizard.new({"country_id": self.cz.id, "company_registry": ICO})
        wizard._onchange_company_registry()
        self.assertEqual(wizard.vat, f"CZ{ICO}")
        wizard.vat = "CZ699001234"
        wizard.company_registry = "27082440"
        wizard._onchange_company_registry()
        self.assertEqual(wizard.vat, "CZ699001234")
        german = self.Wizard.new({"country_id": self.env.ref("base.de").id, "company_registry": ICO})
        german._onchange_company_registry()
        self.assertFalse(german.vat)

    def test_default_code_is_only_set_when_unique(self):
        """Kód se hledá v číselníku; odpovídá-li víc kódů, zůstane prázdný."""
        Code = self.env["investra.esa.code"]
        sector = self.env.ref("investra_counterparty.esa_1240000")
        matching = Code.search([("residency", "=", "r"), ("esa2010_sector_id", "=", sector.id)])
        expected = matching if len(matching) == 1 else Code
        self.assertEqual(self.Wizard._default_esa_code("fund"), expected)
        self.assertEqual(self.Wizard._default_esa_code("service"), Code)
        extra = Code.search([("residency", "=", "r"), ("esa2010_sector_id", "=", sector.id)], limit=1)
        others = matching - extra
        others.write({"active": False})
        self.assertEqual(self.Wizard._default_esa_code("fund"), extra)

    def test_partner_domain_excludes_company_contacts(self):
        company = self.env["res.company"].create({"name": "Cizí společnost"})
        free = self.env["res.partner"].create({"name": "Volný kontakt"})
        domain = self.env["investra.new.book.wizard"]._fields["partner_id"].domain(self.Wizard)
        found = self.env["res.partner"].search(domain)
        self.assertIn(free, found)
        self.assertNotIn(company.partner_id, found)
        person = self.env["res.partner"].create({"name": "Osoba kontaktu", "parent_id": free.id})
        self.assertNotIn(person, self.env["res.partner"].search(domain))

    def test_existing_partner_is_taken_over_without_second_contact_or_profile(self):
        partner = self.env["res.partner"].create({
            "name": "Fond z kontaktu", "additional_identifiers": {"CZ_EN": ICO}, "vat": f"CZ{ICO}",
            "country_id": self.cz.id})
        profile = self.env["investra.counterparty.profile"].create({
            "partner_id": partner.id, "country_id": self.cz.id, "esa_code_id": self.code.id, "lei": LEI})
        wizard = self.Wizard.new({"entity_type": "fund", "partner_id": partner.id})
        wizard._onchange_partner_id()
        self.assertEqual(
            (wizard.name, wizard.company_registry, wizard.vat, wizard.lei, wizard.esa_code_id),
            ("Fond z kontaktu", ICO, f"CZ{ICO}", LEI, self.code))
        partners, profiles = self.env["res.partner"].search_count([]), self.env["investra.counterparty.profile"].search_count([])
        entity = self._create(
            name="Fond z kontaktu", partner_id=partner.id, company_registry=ICO, vat=f"CZ{ICO}", lei=LEI,
            esa_code_id=self.code.id)
        self.assertEqual(entity.company_id.partner_id, partner)
        self.assertFalse(partner.company_id)
        self.assertEqual(self.env["res.partner"].search_count([]), partners)
        self.assertEqual(self.env["investra.counterparty.profile"].search_count([]), profiles)
        self.assertEqual(entity.lei, profile.lei)

    def test_partner_without_profile_gets_one_from_wizard(self):
        partner = self.env["res.partner"].create({"name": "Kontakt bez údajů"})
        entity = self._create(name="Kontakt bez údajů", partner_id=partner.id, lei=LEI, esa_code_id=self.code.id)
        self.assertEqual(partner._counterparty_profile().lei, LEI)
        self.assertEqual(entity.company_id.partner_id, partner)

    def test_company_contact_cannot_be_reused(self):
        other = self.env["res.company"].create({"name": "Jiná kniha kontakt"})
        with self.assertRaises(UserError):
            self._create(name="Jiná kniha kontakt", partner_id=other.partner_id.id)

    def test_same_name_contact_is_offered(self):
        partner = self.env["res.partner"].create({"name": "Stejné jméno s.r.o."})
        wizard = self.Wizard.create({"name": "stejné jméno s.r.o.", "entity_type": "fund", "framework": "cas501"})
        self.assertEqual(wizard.same_name_partner_id, partner)
        action = wizard.action_use_same_name_partner()
        self.assertEqual(wizard.partner_id, partner)
        self.assertEqual(action["res_id"], wizard.id)
        self.assertFalse(self.Wizard.create({"name": "Jiné jméno", "entity_type": "fund", "framework": "cas501"}).same_name_partner_id)

    def test_wizard_form_has_identification_group(self):
        arch = etree.fromstring(self.env["investra.new.book.wizard"].get_view(view_type="form")["arch"])
        for name in ("partner_id", "company_registry", "vat", "lei", "esa_code_id"):
            self.assertTrue(arch.xpath(f"//field[@name='{name}']"), name)
        self.assertTrue(arch.xpath("//field[@name='name' and @readonly='partner_id']"))
