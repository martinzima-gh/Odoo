from odoo import api, fields, models
from odoo.exceptions import UserError


class InvestraMeasurementCategory(models.Model):
    _name = "investra.measurement.category"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Oceňovací kategorie IFRS 9"

    help_text = fields.Text("Nápověda")
    ifrs9_category = fields.Selection([
        ("fvtpl", "FVTPL"), ("fvoci", "FVOCI"), ("amortised", "Naběhlá hodnota"),
    ], "Kategorie IFRS 9", required=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise UserError(self.env._("Oceňovací kategorie zakládá jen modul; uživatel je může jen upravit."))
        return super().create(vals_list)


class InvestraClassificationReason(models.Model):
    _name = "investra.classification.reason"
    _inherit = ["investra.codelist.mixin", "mail.thread"]
    _description = "Důvod klasifikace"

    help_text = fields.Text("Nápověda")
    requires_note = fields.Boolean("Vyžaduje vysvětlení", tracking=True)
