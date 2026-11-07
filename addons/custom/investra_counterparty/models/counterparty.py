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

    code = fields.Char(required=True)
    name = fields.Char(required=True)

    _code_uniq = models.Constraint("unique(code)", "Kód sektoru musí být jedinečný.")

    @api.depends("code", "name")
    def _compute_display_name(self):
        for sector in self:
            sector.display_name = f"{sector.code} {sector.name}"


class InvestraCounterpartyProfile(models.Model):
    """Vlastnosti protistrany platné od data; sektor se opravuje i zpětně, proto s historií změn."""

    _name = "investra.counterparty.profile"
    _inherit = ["mail.thread"]
    _description = "Údaje protistrany"
    _order = "partner_id, valid_from desc"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True, string="Protistrana")
    valid_from = fields.Date(required=True, string="Platí od", tracking=True)
    country_id = fields.Many2one("res.country", required=True, ondelete="restrict", string="Země", tracking=True)
    sector_id = fields.Many2one("investra.esa.sector", required=True, ondelete="restrict", string="Sektor ESA 2010", tracking=True)
    lei = fields.Char(string="LEI", tracking=True)

    _partner_date_uniq = models.Constraint("unique(partner_id, valid_from)", "Údaje protistrany k datu už existují.")

    @api.constrains("lei")
    def _check_lei(self):
        for profile in self:
            if profile.lei and not lei_is_valid(profile.lei):
                raise ValidationError(self.env._("Neplatný LEI: %s.", profile.lei))


class ResPartner(models.Model):
    _inherit = "res.partner"

    investra_profile_ids = fields.One2many("investra.counterparty.profile", "partner_id", string="Údaje protistrany")

    def _counterparty_profile(self, day):
        """Údaje platné k datu; prázdné, pokud k datu žádné nejsou."""
        self.ensure_one()
        return self.env["investra.counterparty.profile"].sudo().search(
            [("partner_id", "=", self.id), ("valid_from", "<=", day)], order="valid_from desc", limit=1
        )


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    issuer_id = fields.Many2one("res.partner", string="Emitent", ondelete="restrict", tracking=True)

    def _issuer_profile(self, day):
        self.ensure_one()
        return self.issuer_id._counterparty_profile(day) if self.issuer_id else self.env["investra.counterparty.profile"]
