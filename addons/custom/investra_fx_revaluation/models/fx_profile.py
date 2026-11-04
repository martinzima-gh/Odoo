from odoo import fields, models


class InvestraFxProfile(models.Model):
    _name = "investra.fx.profile"
    _description = "Profil přecenění cizích měn"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
