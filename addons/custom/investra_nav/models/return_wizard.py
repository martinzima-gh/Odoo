from odoo import api, fields, models
from odoo.exceptions import UserError

MODES = [
    ("return", "Vrátit k přepracování"),
    ("depositary", "Vrácení depozitářem"),
    ("reverse", "Stornovat a přepracovat"),
]
# Co se při potvrzení stane; uživatel to vidí v okně před potvrzením.
EFFECTS = {
    "return": "Návrhy dokladů zaniknou bez storna. Ocenění dostane stav Vráceno a vznikne nová verze v návrhu.",
    "depositary": "Zaúčtované doklady ocenění se stornují k datu ocenění. Ocenění dostane stav Stornováno "
                  "a vznikne nová verze v návrhu.",
    "reverse": "Zaúčtované doklady ocenění se stornují k datu ocenění. Ocenění dostane stav Stornováno "
               "a vznikne nová verze v návrhu.",
}


class InvestraValuationReturnWizard(models.TransientModel):
    """Okno pro důvod vrácení nebo storna; volá postup ocenění, sám nic neúčtuje."""

    _name = "investra.valuation.return.wizard"
    _description = "Vrácení ocenění"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", string="Ocenění")
    mode = fields.Selection(MODES, required=True, string="Krok")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    reason = fields.Text(string="Důvod", required=True)

    @api.depends("mode")
    def _compute_effect(self):
        for wizard in self:
            wizard.effect = EFFECTS.get(wizard.mode, "")

    def action_confirm(self):
        self.ensure_one()
        methods = {
            "return": "action_return",
            "depositary": "action_depositary_return",
            "reverse": "action_reverse",
        }
        if self.mode not in methods:
            raise UserError(self.env._("Neznámý krok."))
        new = getattr(self.valuation_id, methods[self.mode])(self.reason)
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.valuation",
            "res_id": new.id,
            "view_mode": "form",
            "target": "current",
        }
