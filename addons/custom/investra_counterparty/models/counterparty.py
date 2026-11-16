from odoo import api, fields, models
from odoo.exceptions import ValidationError


def lei_is_valid(lei):
    """LEI podle ISO 17442: 20 znaků a kontrolní číslice mod 97."""
    if len(lei) != 20 or not lei.isalnum() or lei != lei.upper():
        return False
    return int("".join(str(int(char, 36)) for char in lei)) % 97 == 1


class InvestraEsaSector(models.Model):
    _name = "investra.esa.sector"
    _description = "Sektor ESA 2010"
    _order = "code"
    _rec_names_search = ["code", "name"]

    code = fields.Char(required=True, string="Kód")
    name = fields.Char(required=True, string="Název")

    _code_uniq = models.Constraint("unique(code)", "Kód sektoru musí být jedinečný.")

    @api.depends("code", "name")
    def _compute_display_name(self):
        for sector in self:
            sector.display_name = f"{sector.code} {sector.name}"


class InvestraCounterpartyProfile(models.Model):
    """Údaje protistrany: jeden záznam na kontakt bez platnosti od data; změna se přepíše a stopu drží historie
    záznamu (tracking). Rozhodnutí 2026-11-16 „Údaje protistrany bez historie“, úkol MN-09."""

    _name = "investra.counterparty.profile"
    _inherit = ["mail.thread"]
    _description = "Údaje protistrany"
    _order = "partner_id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="restrict", index=True, string="Protistrana", tracking=True)
    country_id = fields.Many2one("res.country", required=True, ondelete="restrict", string="Země", tracking=True)
    sector_id = fields.Many2one("investra.esa.sector", required=True, ondelete="restrict", string="Sektor ESA 2010", tracking=True)
    lei = fields.Char(string="LEI", tracking=True)

    _partner_uniq = models.Constraint(
        "unique(partner_id)", "Kontakt už má údaje protistrany; změňte stávající záznam.")

    @api.depends("partner_id.display_name")
    def _compute_display_name(self):
        for profile in self:
            profile.display_name = (
                self.env._("Údaje protistrany – %s", profile.partner_id.display_name)
                if isinstance(profile.id, int) and profile.partner_id else self.env._("Nové údaje protistrany"))

    @api.constrains("lei")
    def _check_lei(self):
        for profile in self:
            if profile.lei and not lei_is_valid(profile.lei):
                raise ValidationError(self.env._("Neplatný LEI: %s.", profile.lei))


class ResPartner(models.Model):
    _inherit = "res.partner"

    investra_profile_ids = fields.One2many("investra.counterparty.profile", "partner_id", string="Údaje protistrany")

    def _counterparty_profile(self, day=None):
        """Jediný záznam údajů kontaktu, nebo prázdný. Datum se nepoužívá (údaje nemají platnost od data, MN-09);
        parametr zůstává, aby se nemuseli měnit volající."""
        self.ensure_one()
        return self.env["investra.counterparty.profile"].sudo().search([("partner_id", "=", self.id)], limit=1)


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    issuer_id = fields.Many2one("res.partner", string="Emitent", ondelete="restrict", tracking=True)

    def _issuer_profile(self, day=None):
        self.ensure_one()
        return self.issuer_id._counterparty_profile(day) if self.issuer_id else self.env["investra.counterparty.profile"]


class InvestraEntity(models.Model):
    """LEI a sektor ESA knihy se berou z údajů protistrany kontaktu společnosti (MN-05, rozhodnutí 2026-11-16)."""

    _inherit = "investra.entity"

    lei = fields.Char(compute="_compute_counterparty_profile", string="LEI")
    esa_sector_id = fields.Many2one("investra.esa.sector", compute="_compute_counterparty_profile", string="Sektor ESA 2010")

    @api.depends("company_id.partner_id.investra_profile_ids.lei", "company_id.partner_id.investra_profile_ids.sector_id")
    def _compute_counterparty_profile(self):
        for entity in self:
            profile = entity.company_id.partner_id._counterparty_profile() if entity.company_id else None
            entity.lei = profile.lei if profile else False
            entity.esa_sector_id = profile.sector_id if profile else False

    def action_open_counterparty_profiles(self):
        """Jediný záznam údajů protistrany kontaktu společnosti; když chybí, nový s předvyplněným kontaktem a zemí."""
        self.ensure_one()
        partner = self.company_id.partner_id
        profile = partner._counterparty_profile()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Údaje protistrany"),
            "res_model": "investra.counterparty.profile",
            "view_mode": "form",
            "views": [(False, "form")],
            "res_id": profile.id or False,
            "context": {
                "default_partner_id": partner.id,
                "default_country_id": (partner.country_id or self.company_id.country_id).id,
            },
        }
