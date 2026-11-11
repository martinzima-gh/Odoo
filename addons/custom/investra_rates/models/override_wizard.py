from odoo import api, fields, models


class InvestraRateOverrideWizard(models.TransientModel):
    """Okno pro ruční přepis kurzu nebo ruční kurz; zápis dělá evidence kurzů s kontrolami."""

    _name = "investra.rate.override.wizard"
    _description = "Ruční kurz"

    origin = fields.Selection(
        [("override", "Ruční přepis vyhlášeného kurzu"), ("manual", "Ruční kurz (zdroj ho nevyhlásil)")],
        required=True, default="override", string="Druh",
    )
    source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], required=True, default="cnb", string="Zdroj")
    currency_id = fields.Many2one("res.currency", required=True, string="Měna")
    date = fields.Date(required=True, string="Datum")
    quantity = fields.Float(required=True, default=1, digits=(12, 0), string="Množství")
    rate = fields.Float(required=True, digits=(16, 6), string="Kurz", help="Základní měna zdroje za množství (ČNB: CZK; ECB: jednotky měny za 1 EUR).")
    reason = fields.Text(required=True, string="Důvod")
    current_id = fields.Many2one("investra.rate", compute="_compute_current", string="Platný záznam kurzu")
    current_rate = fields.Float(related="current_id.rate", string="Platný kurz", digits=(16, 6))
    current_origin = fields.Selection(related="current_id.origin", string="Druh platného kurzu")

    @api.depends("source", "currency_id", "date")
    def _compute_current(self):
        Rate = self.env["investra.rate"]
        for wizard in self:
            current = Rate.browse()
            if wizard.source and wizard.currency_id and wizard.date:
                current = Rate.search([
                    ("source", "=", wizard.source), ("currency_id", "=", wizard.currency_id.id), ("date", "=", wizard.date),
                ]) and Rate._effective(wizard.source, wizard.currency_id, wizard.date)
            wizard.current_id = current

    def action_confirm(self):
        self.ensure_one()
        record = self.env["investra.rate"].create_manual(
            self.origin, self.source, self.currency_id, self.date, self.quantity, self.rate, self.reason,
        )
        return {
            "type": "ir.actions.act_window",
            # Podle schvalovací matice může místo kurzu vzniknout žádost ke schválení.
            "res_model": record._name,
            "res_id": record.id,
            "view_mode": "form",
            "target": "current",
        }
