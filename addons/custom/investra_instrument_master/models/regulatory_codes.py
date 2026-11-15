from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraBa0088Group(models.Model):
    _name = "investra.ba0088.group"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Skupina druhů cenných papírů BA0088"


class InvestraBa0088Code(models.Model):
    _name = "investra.ba0088.code"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Druh cenného papíru ČNB (BA0088)"

    selectable = fields.Boolean("Nabízet u nástroje", tracking=True)
    asset_family = fields.Selection([
        ("debt", "Dluhový nástroj"), ("equity", "Akcie a majetkové CP"), ("fund", "Podíl ve fondu"),
        ("certificate", "Investiční certifikát"), ("bill", "Směnka"), ("coupon", "Kupón"),
        ("direct_equity", "Majetkový podíl"), ("derivative", "Derivát"), ("other", "Ostatní"),
    ], "Rodina", tracking=True)
    parent_code = fields.Char("Nadřazený kód")
    group_id = fields.Many2one("investra.ba0088.group", "Skupina", ondelete="restrict", tracking=True)
    requires_issuer = fields.Boolean("Vyžaduje emitenta", tracking=True)
    requires_maturity = fields.Boolean("Vyžaduje splatnost", tracking=True)
    requires_justification = fields.Boolean("Vyžaduje zdůvodnění", tracking=True)
    leverage_rule = fields.Selection([
        ("none", "Bez pravidla"), ("must_true", "Páka povinná"), ("must_false", "Páka zakázaná"),
    ], "Pravidlo páky", default="none", required=True, tracking=True)

    @api.constrains("selectable", "asset_family")
    def _check_family(self):
        for rec in self:
            if rec.selectable and not rec.asset_family:
                raise ValidationError(self.env._("Druh nabízený u nástroje musí mít vyplněnou rodinu."))


class InvestraEsaAggregateSector(models.Model):
    _name = "investra.esa.aggregate.sector"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Typ emitenta"

    help_text = fields.Text("Nápověda")


class InvestraEsaCode(models.Model):
    _name = "investra.esa.code"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Kód sektoru ESA (D_S_RNBD_4)"

    aggregate_sector_id = fields.Many2one(
        "investra.esa.aggregate.sector", "Typ emitenta", required=True, ondelete="restrict", tracking=True)
    residency = fields.Selection([("r", "Rezident"), ("nr", "Nerezident")], "Rezidentství", required=True, tracking=True)
    residency_warning = fields.Char("Upozornění na rezidentství", compute="_compute_residency_warning")
    esa2010_sector_id = fields.Many2one("investra.esa.sector", "Sektor ESA 2010", ondelete="restrict")
    any_country = fields.Boolean("Libovolná země")

    @api.depends("code", "residency")
    def _compute_residency_warning(self):
        for rec in self:
            first = (rec.code or "")[:1]
            warning = False
            if first == "1" and rec.residency != "r":
                warning = self.env._("Kód začíná 1 (rezident), ale rezidentství je nastaveno jinak.")
            elif first == "2" and rec.residency != "nr":
                warning = self.env._("Kód začíná 2 (nerezident), ale rezidentství je nastaveno jinak.")
            rec.residency_warning = warning


class InvestraCountryGroupMembership(models.Model):
    _name = "investra.country.group.membership"
    _inherit = ["mail.thread"]
    _description = "Členství země ve skupině EU/EHP"
    _order = "group, country_id, valid_from"

    country_id = fields.Many2one("res.country", "Země", required=True, ondelete="restrict", tracking=True)
    group = fields.Selection([("eu", "EU"), ("eea", "EHP mimo EU")], "Skupina", required=True, tracking=True)
    valid_from = fields.Date("Platí od", required=True, tracking=True)
    valid_to = fields.Date("Platí do", tracking=True)
    source = fields.Char("Zdroj")

    @api.constrains("country_id", "group", "valid_from", "valid_to")
    def _check_period(self):
        for rec in self:
            if rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(self.env._("Platnost do nesmí být před platností od."))
            others = self.search([("country_id", "=", rec.country_id.id), ("group", "=", rec.group), ("id", "!=", rec.id)])
            for other in others:
                if (not other.valid_to or other.valid_to >= rec.valid_from) and (
                        not rec.valid_to or rec.valid_to >= other.valid_from):
                    raise ValidationError(self.env._(
                        "Období členství země %(country)s ve skupině se překrývá s jiným záznamem.",
                        country=rec.country_id.name))
