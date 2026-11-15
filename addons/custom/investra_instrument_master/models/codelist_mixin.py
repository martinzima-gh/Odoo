from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class InvestraCodelistMixin(models.AbstractModel):
    """Společný základ číselníků: kód, název, platnost, zdroj metodiky a ochrana kódu."""

    _name = "investra.codelist.mixin"
    _inherit = ["mail.thread"]
    _description = "Základ číselníku"
    _order = "sequence, code"
    _rec_names_search = ["code", "name"]

    code = fields.Char("Kód", required=True, index=True, tracking=True)
    name = fields.Char("Název", required=True, tracking=True)
    active = fields.Boolean("Aktivní", default=True, tracking=True)
    sequence = fields.Integer("Pořadí", default=10)
    valid_from = fields.Date("Platí od", tracking=True)
    valid_to = fields.Date("Platí do", tracking=True)
    source_methodology = fields.Char("Zdroj metodiky", tracking=True)
    note = fields.Text("Poznámka")
    locally_modified = fields.Boolean("Upraveno lokálně", readonly=True, copy=False)

    _code_uniq = models.Constraint("unique(code)", "Kód v číselníku musí být jedinečný.")

    @api.depends("code", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} {rec.name}" if rec.code else (rec.name or "")

    @api.constrains("valid_from", "valid_to")
    def _check_validity(self):
        for rec in self:
            if rec.valid_from and rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(self.env._("Platnost do nesmí být před platností od."))

    def write(self, vals):
        if "code" in vals and not self.env.su and any(rec.code != vals["code"] for rec in self):
            raise UserError(self.env._("Kód v číselníku nejde po založení změnit; založte nový záznam."))
        # Ruční úprava se označí; import číselníku a načítání dat modulu ne.
        if (not self.env.context.get("investra_codelist_import") and not self.env.context.get("install_mode")
                and set(vals) - {"locally_modified"}):
            vals = dict(vals, locally_modified=True)
        return super().write(vals)
