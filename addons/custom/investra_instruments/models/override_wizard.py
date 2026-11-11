from odoo import fields, models

from .instrument import IFRS9_CATEGORY


class InvestraClassificationOverrideWizard(models.TransientModel):
    """Okno pro ruční kategorii IFRS 9; zápis jde přes schvalovací matici (rozhodnutí 2026-11-11)."""

    _name = "investra.classification.override.wizard"
    _description = "Ruční kategorie IFRS 9"

    classification_id = fields.Many2one("investra.portfolio.classification", required=True, ondelete="cascade", string="Zařazení")
    category_override = fields.Selection(IFRS9_CATEGORY, required=True, string="Ruční kategorie")
    override_note = fields.Char(required=True, string="Zdůvodnění přepsání")

    def action_confirm(self):
        self.ensure_one()
        return self.classification_id.request_category_override(self.category_override, self.override_note)
