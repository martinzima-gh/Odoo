from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraClassMovement(models.Model):
    """Úpis nebo odkup ze závěrky IS. Do napojení IS se pořizuje ručně a ve testech."""

    _name = "investra.class.movement"
    _description = "Pohyb kapitálu třídy"
    _order = "date, id"

    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict", index=True)
    fund_id = fields.Many2one(related="class_id.fund_id", store=True, index=True)
    company_id = fields.Many2one(related="class_id.company_id", store=True, index=True)
    date = fields.Date(required=True)
    movement_type = fields.Selection([("subscription", "Úpis"), ("redemption", "Odkup")], required=True)
    amount = fields.Float(digits=(20, 2), required=True)
    units = fields.Float(digits=(20, 6), required=True)
    event_id = fields.Many2one("investra.accounting.event", readonly=True)

    @api.constrains("amount", "units")
    def _check_positive(self):
        for movement in self:
            if movement.amount <= 0 or movement.units <= 0:
                raise ValidationError(self.env._("Částka i kusy musí být kladné."))

    @property
    def signed_amount(self):
        return self.amount if self.movement_type == "subscription" else -self.amount

    @property
    def signed_units(self):
        return self.units if self.movement_type == "subscription" else -self.units

    def _book(self):
        for movement in self:
            amount = movement.signed_amount
            event = self.env["investra.accounting.event"]._create_event(
                movement.company_id, f"movement:{movement.id}", f"{movement.movement_type} {movement.class_id.code}",
                movement.date, "class_movement",
                [
                    {"role": "bank", "amount": amount, "movement_type": movement.movement_type},
                    {"role": "class_capital", "amount": -amount, "class_id": movement.class_id.id,
                     "movement_type": movement.movement_type},
                ],
            )
            event._lock_events()
            event._post_events()
            movement.sudo().event_id = event
