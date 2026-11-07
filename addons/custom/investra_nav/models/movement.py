from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    def _fx_at(self, currency, day):
        """Funkční měna za jednotku měny, jen z vyhlášeného kurzu k datu."""
        self.ensure_one()
        if currency == self.currency_id:
            return Decimal(1)
        Rate = self.env["investra.rate"].sudo()
        source = self.entity_id.rate_source
        age = self.max_rate_age_days
        return Rate.get_rate(source, currency, day, age) / Rate.get_rate(source, self.currency_id, day, age)


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
    currency_id = fields.Many2one(related="class_id.currency_id", string="Měna kurzu")
    amount_class = fields.Float(digits=(20, 2), string="Částka v měně kurzu", help="U třídy v jiné než funkční měně je to částka úpisu nebo odkupu.")
    fx_rate = fields.Float(digits=(16, 6), string="Kurz", help="Funkční měna za jednotku měny kurzu; bez zadání platí vyhlášený kurz k datu.")
    amount = fields.Float(digits=(20, 2), string="Částka ve funkční měně")
    units = fields.Float(digits=(20, 6), required=True)
    event_id = fields.Many2one("investra.accounting.event", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("amount_class"):
                fund_class = self.env["investra.fund.class"].browse(vals["class_id"])
                rate = vals.get("fx_rate") or float(fund_class.fund_id._fx_at(fund_class.currency_id, fields.Date.to_date(vals["date"])))
                vals.update({"fx_rate": rate, "amount": fund_class.fund_id.currency_id.round(vals["amount_class"] * rate)})
        return super().create(vals_list)

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

    def _bank_currency(self):
        """Bankovní řádek v měně kurzu, pokud je úpis nebo odkup zadaný v ní."""
        self.ensure_one()
        sign = 1 if self.movement_type == "subscription" else -1
        if self.amount_class and self.currency_id != self.fund_id.currency_id:
            return {"currency_id": self.currency_id.id, "amount_currency": sign * self.amount_class}
        return {}

    def _book(self):
        for movement in self:
            amount = movement.signed_amount
            event = self.env["investra.accounting.event"]._create_event(
                movement.company_id, f"movement:{movement.id}", f"{movement.movement_type} {movement.class_id.code}",
                movement.date, "class_movement",
                [
                    {"role": "bank", "amount": amount, "movement_type": movement.movement_type, **movement._bank_currency()},
                    {"role": "class_capital", "amount": -amount, "class_id": movement.class_id.id,
                     "movement_type": movement.movement_type},
                ],
            )
            event._lock_events()
            event._post_events()
            movement.sudo().event_id = event
