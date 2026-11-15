from odoo import fields, models


class InvestraMasterdataChange(models.Model):
    """Historie změn potvrzené klasifikace; řádky zakládá jen průvodce (plán 3.4), uživatelé je jen čtou."""

    _name = "investra.masterdata.change"
    _description = "Změna kmenových dat"
    _order = "create_date desc, id desc"

    res_model = fields.Char("Model", required=True, readonly=True, index=True)
    res_id = fields.Integer("ID záznamu", required=True, readonly=True, index=True)
    record_name = fields.Char("Záznam", readonly=True)
    field_name = fields.Char("Pole", readonly=True)
    old_value = fields.Char("Původní hodnota", readonly=True)
    new_value = fields.Char("Nová hodnota", readonly=True)
    effective_date = fields.Date("Účinnost od", readonly=True)
    reason = fields.Char("Důvod", required=True, readonly=True)
    user_id = fields.Many2one("res.users", "Změnil", readonly=True, default=lambda self: self.env.user)
