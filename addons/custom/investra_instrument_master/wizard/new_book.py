from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.investra_counterparty.models.counterparty import lei_is_valid
from odoo.addons.investra_entity.models.entity import ICO_KEY, ico_is_valid

# Předvyplněný kód sektoru ESA podle druhu jednotky (rozhodnutí Martina 16. 11. 2026): fond, SICAV a podfond
# „soukromé národní“, investiční společnost „soukromé národní“; servisní společnost bez kódu. Kód se hledá v číselníku
# podle hodnoty (ne podle id) a uživatel ho může přepsat.
ESA_CODE_BY_TYPE = {
    "sicav": "1240200",
    "fund": "1240200",
    "subfund": "1240200",
    "manager": "1260200",
}


class InvestraNewBookWizard(models.TransientModel):
    """Identifikace společnosti v průvodci: kontakt, IČO, DIČ, LEI a kód sektoru ESA (MN-06)."""

    _inherit = "investra.new.book.wizard"

    partner_id = fields.Many2one(
        "res.partner", string="Existující kontakt", ondelete="set null",
        domain=lambda self: self._partner_domain(),
        help="Nepovinné. Vybraný kontakt převezme nová společnost; IČO, DIČ, LEI a kód sektoru se předvyplní z kontaktu.")
    partner_profile_id = fields.Many2one(
        "investra.counterparty.profile", compute="_compute_partner_profile", string="Údaje protistrany kontaktu")
    same_name_partner_id = fields.Many2one(
        "res.partner", compute="_compute_same_name_partner", string="Kontakt stejného jména")
    company_registry = fields.Char(string="IČO")
    vat = fields.Char(string="DIČ")
    lei = fields.Char(string="LEI")
    esa_code_id = fields.Many2one("investra.esa.code", string="Kód sektoru ESA", ondelete="set null")

    @api.model
    def _partner_domain(self):
        """Kontakty, které smí nová společnost převzít: samostatné kontakty (ne osoby pod firmou), které ještě nejsou
        kontaktem žádné společnosti. Odchylka od zadání („kontakty-firmy“): v Odoo 20 je is_company vypočtené a pravdivé
        jen u kontaktu s DIČ, fond bez DIČ by se nenabídl."""
        taken = self.env["res.company"].sudo().search([]).partner_id
        return [("parent_id", "=", False), ("id", "not in", taken.ids)]

    # --- odvozené hodnoty a předvyplnění -----------------------------------------------------------------------------

    @api.depends("partner_id")
    def _compute_partner_profile(self):
        for wizard in self:
            wizard.partner_profile_id = wizard.partner_id._counterparty_profile() if wizard.partner_id else False

    @api.depends("name", "partner_id")
    def _compute_same_name_partner(self):
        domain = self._partner_domain()
        for wizard in self:
            found = self.env["res.partner"]
            if wizard.name and not wizard.partner_id:
                found = self.env["res.partner"].sudo().search(domain + [("name", "=ilike", wizard.name.strip())], limit=1)
            wizard.same_name_partner_id = found

    @api.model
    def _default_esa_code(self, entity_type):
        """Kód sektoru ESA podle druhu jednotky (viz ESA_CODE_BY_TYPE), jen rezidentský a jen když je v číselníku
        právě jeden; jinak prázdný."""
        # Číselník se čte jako superuživatel: průvodce smí použít jen správce a ten nemusí mít práva k číselníkům.
        Code = self.env["investra.esa.code"].sudo()
        value = ESA_CODE_BY_TYPE.get(entity_type)
        if not value:
            return Code
        codes = Code.search([("code", "=", value), ("residency", "=", "r")])
        return codes if len(codes) == 1 else Code.browse()

    @api.onchange("entity_type")
    def _onchange_entity_type(self):
        super()._onchange_entity_type()
        if not self.partner_id:
            self.esa_code_id = self._default_esa_code(self.entity_type)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        partner = self.partner_id
        if not partner:
            return
        self.name = partner.name
        self.company_registry = partner._get_additional_identifier(ICO_KEY)
        self.vat = partner.vat
        if partner.country_id:
            self.country_id = partner.country_id
        profile = self.partner_profile_id
        self.lei = profile.lei
        self.esa_code_id = profile.esa_code_id

    @api.onchange("company_registry", "country_id")
    def _onchange_company_registry(self):
        """DIČ u země Česko předvyplní „CZ“ + IČO, když je prázdné nebo je to dřívější předvyplnění; lze přepsat."""
        registry = (self.company_registry or "").strip()
        if self.country_id.code == "CZ" and ico_is_valid(registry):
            if not self.vat or (self.vat.startswith("CZ") and len(self.vat) == 10):
                self.vat = f"CZ{registry}"

    def action_use_same_name_partner(self):
        """Přepne průvodce na kontakt stejného jména (nabídka z upozornění)."""
        self.ensure_one()
        self.partner_id = self.same_name_partner_id
        self._onchange_partner_id()
        return {
            "type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id,
            "view_mode": "form", "views": [(False, "form")], "target": "new",
        }

    # --- kontroly a založení -----------------------------------------------------------------------------------------

    def _check_before_create(self):
        super()._check_before_create()
        registry = (self.company_registry or "").strip()
        if registry and self.country_id.code == "CZ" and not ico_is_valid(registry):
            raise UserError(self.env._("Neplatné IČO %s: musí mít 8 číslic se správnou kontrolní číslicí.", registry))
        if self.partner_id and self.env["res.company"].sudo().search_count(
                [("partner_id", "=", self.partner_id.id)], limit=1):
            raise UserError(self.env._("Kontakt %s je už kontaktem jiné společnosti.", self.partner_id.display_name))
        if not self.partner_profile_id and (self.lei or self.esa_code_id):
            self._check_new_profile()

    def _check_new_profile(self):
        """Údaje nového profilu se ověří před založením, ať kniha nevznikne bez profilu."""
        if not self.esa_code_id:
            raise UserError(self.env._("K LEI doplňte kód sektoru ESA; profil protistrany ho potřebuje."))
        code = self.esa_code_id.sudo()
        if not code.esa2010_sector_id:
            raise UserError(self.env._(
                "ESA kód %s nemá přiřazený sektor ESA 2010; vyberte jiný kód.", code.code))
        if not code.any_country and self.country_id:
            is_cz = self.country_id.code == "CZ"
            if (code.residency == "r" and not is_cz) or (code.residency == "nr" and is_cz):
                raise UserError(self.env._(
                    "ESA kód %s nesouhlasí se zemí %s (rezidentství kódu).", code.code, self.country_id.name))
        lei = (self.lei or "").strip()
        if lei:
            if not lei_is_valid(lei):
                raise UserError(self.env._("Neplatný LEI: %s.", lei))
            other = self.env["investra.counterparty.profile"].sudo().search([("lei", "=", lei)], limit=1)
            if other:
                raise UserError(self.env._("LEI %s už má protistrana %s.", lei, other.partner_id.display_name))

    def _extra_book_values(self):
        values = super()._extra_book_values()
        if self.partner_id:
            values["partner"] = self.partner_id
        return values

    def _after_book_created(self, entity):
        super()._after_book_created(entity)
        company = entity.company_id.sudo()
        registry, vat = (self.company_registry or "").strip(), (self.vat or "").strip()
        if registry and registry != company.partner_id._get_additional_identifier(ICO_KEY):
            company.partner_id._set_additional_identifier(ICO_KEY, registry)
        if vat and vat != company.vat:
            company.vat = vat
        if not self.partner_profile_id and (self.lei or self.esa_code_id):
            self.env["investra.counterparty.profile"].sudo().create({
                "partner_id": company.partner_id.id,
                "country_id": self.country_id.id,
                "esa_code_id": self.esa_code_id.id,
                "lei": (self.lei or "").strip() or False,
            })
