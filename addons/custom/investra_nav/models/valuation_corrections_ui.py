"""Rozhraní oprav úplat v ocenění (ZJ-12 krok 5, C.3): pomocná pole a tlačítka pro formulář ocenění.

Výpočet ocenění (engine, `_apply_fees`, kontroly) tento soubor nemění; jen čte uložené řádky, detaily a opravy a volá
hotové metody (`end_correction`, `action_keep_difference`, `action_keep_result`, `action_copy_from_version`).
"""

import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class InvestraValuationCorrectionsUi(models.Model):
    _inherit = "investra.valuation"

    carried_correction_ids = fields.Many2many(
        "investra.valuation.external", compute="_compute_carried_corrections", string="Převzaté opravy",
        help="Opravy dřívějších ocenění „do konce období“, které tohle ocenění převzalo do výpočtu. Jen pro čtení; "
             "převzetí skončí tlačítkem Ukončit opravu.")
    has_corrections = fields.Boolean(compute="_compute_has_corrections", string="Má opravy")
    can_copy_from_version = fields.Boolean(compute="_compute_can_copy_from_version", string="Lze převzít z verze")

    @api.depends("fee_line_ids.detail", "external_fee_ids")
    def _compute_carried_corrections(self):
        for valuation in self:
            ids = set()
            for line in valuation.fee_line_ids:
                detail = json.loads(line.detail or "{}")
                ids.update(detail.get("carried_ids") or [])
                ids.update(detail.get("base_correction_ids") or [])
            entries = self.env["investra.valuation.external"].sudo().browse(sorted(ids)).exists()
            valuation.carried_correction_ids = entries.filtered(lambda e: e.valuation_id != valuation)

    @api.depends("external_fee_ids.corrects_rule_id", "carried_correction_ids")
    def _compute_has_corrections(self):
        for valuation in self:
            valuation.has_corrections = bool(
                valuation.external_fee_ids.filtered("corrects_rule_id") or valuation.carried_correction_ids)

    @api.depends("state", "external_fee_ids")
    def _compute_can_copy_from_version(self):
        for valuation in self:
            previous = valuation._previous_version() if valuation.id and valuation.state in ("draft", "computed") else False
            valuation.can_copy_from_version = bool(
                previous and previous.external_fee_ids - valuation.external_fee_ids.mapped("origin_id"))


class InvestraValuationFeeCorrectionsUi(models.Model):
    _inherit = "investra.valuation.fee"

    fix_kind = fields.Selection(
        [("none", "Bez opravy"), ("rule", "Pravidlo s opravou"), ("correction", "Oprava")], compute="_compute_fix",
        string="Druh opravy")
    fix_computed = fields.Float(digits=(20, 2), compute="_compute_fix", string="Vypočteno")
    fix_correction = fields.Float(digits=(20, 2), compute="_compute_fix", string="Oprava částky")
    fix_result = fields.Float(digits=(20, 2), compute="_compute_fix", string="Výsledek")
    fix_note = fields.Text(related="external_id.note", string="Zdůvodnění")
    fix_user_id = fields.Many2one("res.users", compute="_compute_fix", string="Zadal")
    fix_date = fields.Datetime(compute="_compute_fix", string="Kdy")
    correction_changed = fields.Boolean(compute="_compute_fix", string="Vypočtená částka se změnila")

    @api.depends("amount", "rule_id", "class_id", "external_id.amount", "external_id.computed_at_entry",
                 "external_id.computed_now", "external_id.corrects_rule_id", "external_id.correction_target",
                 "valuation_id.fee_line_ids.amount", "valuation_id.state")
    def _compute_fix(self):
        for line in self:
            line.fix_kind, line.fix_computed, line.fix_correction, line.fix_result = "none", 0.0, 0.0, 0.0
            line.fix_user_id, line.fix_date, line.correction_changed = False, False, False
            entry = line.external_id
            if entry.corrects_rule_id:
                line.fix_kind, line.fix_correction = "correction", line.amount
                line.fix_user_id, line.fix_date = entry.create_uid, entry.create_date
                line.correction_changed = bool(
                    entry.corrects_rule_id and entry.correction_target == "amount" and entry.computed_captured
                    and entry.ended_id.id is False
                    and round(entry.computed_now, 2) != round(entry.computed_at_entry, 2)
                    and line.valuation_id.state in ("draft", "computed"))
            elif line.rule_id:
                fixes = line.valuation_id.fee_line_ids.filtered(
                    lambda l: l.external_id.corrects_rule_id == line.rule_id and l.class_id == line.class_id
                    and l.external_id.correction_target == "amount")
                if fixes:
                    line.fix_kind, line.fix_computed = "rule", line.amount
                    line.fix_correction = sum(fixes.mapped("amount"))
                    line.fix_result = line.amount + line.fix_correction

    def action_keep_difference(self):
        self.ensure_one()
        return self.external_id.action_keep_difference()

    def action_keep_result(self):
        self.ensure_one()
        return self.external_id.action_keep_result()


class InvestraValuationExternalCorrectionsUi(models.Model):
    _inherit = "investra.valuation.external"

    rule_kind = fields.Selection(related="corrects_rule_id.kind", string="Druh opravovaného pravidla")
    target_amount = fields.Float(
        digits=(20, 2), compute="_compute_target_amount", inverse="_inverse_target_amount", string="Cílová částka",
        help="Částka pravidla po opravě = Vypočteno + Rozdíl. Zadejte rozdíl, nebo cílovou částku; druhá hodnota se dopočte.")
    zero_out = fields.Boolean(
        string="Vynulovat", store=False, help="Zkratka: cílová částka 0, rozdíl = −Vypočteno (zrušení úplaty jen pro toto ocenění).")
    is_ended = fields.Boolean(compute="_compute_is_ended", string="Ukončena")

    @api.depends("amount", "computed_at_entry")
    def _compute_target_amount(self):
        for entry in self:
            entry.target_amount = round(entry.computed_at_entry + entry.amount, 2)

    def _inverse_target_amount(self):
        for entry in self:
            entry.amount = round(entry.target_amount - entry.computed_at_entry, 2)

    @api.onchange("target_amount")
    def _onchange_target_amount(self):
        for entry in self:
            entry.amount = round(entry.target_amount - entry.computed_at_entry, 2)

    @api.onchange("zero_out")
    def _onchange_zero_out(self):
        for entry in self.filtered("zero_out"):
            entry.target_amount = 0.0
            entry.amount = round(-entry.computed_at_entry, 2)

    def _compute_is_ended(self):
        for entry in self:
            entry.is_ended = bool(entry.id and self.sudo().search_count([
                ("ended_id", "=", entry.id), ("valuation_id.state", "not in", ("returned", "reversed"))]))

    def action_end_correction(self):
        """Ukončit převzatou opravu: okno s povinnou poznámkou (ZJ-12 B.7); ocenění určuje kontext `ending_valuation_id`."""
        self.ensure_one()
        valuation = self.env["investra.valuation"].browse(self.env.context.get("ending_valuation_id"))
        if not valuation.exists():
            raise UserError(self.env._("Ukončit jde jen oprava převzatá do otevřeného ocenění."))
        return {
            "type": "ir.actions.act_window", "name": self.env._("Ukončit opravu"),
            "res_model": "investra.valuation.end.wizard", "view_mode": "form", "target": "new",
            "context": {"default_valuation_id": valuation.id, "default_entry_id": self.id},
        }


class InvestraValuationEndWizard(models.TransientModel):
    """Okno s povinnou poznámkou pro ukončení převzaté opravy; ukončení samo je `valuation.end_correction`."""

    _name = "investra.valuation.end.wizard"
    _description = "Ukončení opravy"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", string="Ocenění")
    entry_id = fields.Many2one("investra.valuation.external", required=True, ondelete="cascade", string="Ukončovaná oprava")
    amount = fields.Float(related="entry_id.amount", digits=(20, 2), string="Částka opravy")
    note = fields.Text(required=True, string="Poznámka",
                       help="Proč oprava končí (uloží se k ukončení opravy a do stopy ocenění).")

    def action_confirm(self):
        self.ensure_one()
        self.valuation_id.end_correction(self.entry_id, self.note)
        return {"type": "ir.actions.act_window_close"}
