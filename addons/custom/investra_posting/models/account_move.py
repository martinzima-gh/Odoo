from odoo import api, fields, models
from odoo.exceptions import UserError

from .event import MOVEMENT_TYPES, SERVICE

# Pole dokladu, která se u dokladu z události mění jen službou.
MOVE_PROTECTED = {
    "date", "journal_id", "line_ids", "state", "name", "ref", "narration", "partner_id", "auto_post",
    "currency_id", "investra_event_id", "investra_locked", "invoice_line_ids",
}
# Pole řádku, která ovlivňují NAV tříd a výkazy.
LINE_INVESTRA = {"investra_class_id", "investra_part", "investra_movement_type"}
LINE_PROTECTED = LINE_INVESTRA | {
    "account_id", "debit", "credit", "balance", "amount_currency", "currency_id", "name", "partner_id",
    "analytic_distribution", "move_id", "date",
}


def _is_service(env):
    return env.context.get("investra_service") is SERVICE


class AccountMove(models.Model):
    _inherit = "account.move"

    investra_event_id = fields.Many2one(
        "investra.accounting.event", readonly=True, copy=False, index="btree_not_null", ondelete="restrict",
        string="Účetní událost Investra",
    )
    investra_locked = fields.Boolean(readonly=True, copy=False, string="Zamčený návrh")

    def _investra_guarded(self):
        return self.filtered(lambda m: m.investra_event_id or m.investra_locked)

    def write(self, vals):
        if not _is_service(self.env) and MOVE_PROTECTED & set(vals) and self._investra_guarded():
            raise UserError(self.env._("Doklad z účetní události nejde ručně měnit."))
        return super().write(vals)

    def unlink(self):
        if not _is_service(self.env) and self._investra_guarded():
            raise UserError(self.env._("Doklad z účetní události nejde ručně smazat."))
        return super().unlink()

    def _is_draft_disabled(self):
        return super()._is_draft_disabled() or bool(self.investra_event_id)

    def button_cancel(self):
        if not _is_service(self.env) and self._investra_guarded():
            raise UserError(self.env._("Doklad z účetní události nejde ručně zrušit."))
        return super().button_cancel()

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if not _is_service(self.env) and self._investra_guarded():
            raise UserError(self.env._("Doklad z účetní události se stornuje jen přes jeho událost."))
        return super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)

    def _investra_strict_date(self):
        """Doklady, kterým se nesmí tiše posunout datum: události a interní doklady fondových knih."""
        books = self.env["investra.entity"].sudo().search([
            ("company_id", "in", self.company_id.ids),
            ("entity_type", "in", ("sicav", "fund", "subfund")),
        ]).company_id
        return self.filtered(lambda m: m.investra_event_id or (m.company_id in books and m.move_type == "entry"))

    def _post(self, soft=True):
        if not _is_service(self.env) and self._investra_guarded():
            raise UserError(self.env._("Doklad z účetní události se zaúčtuje jen ve schváleném postupu."))
        strict = self._investra_strict_date()
        for move in strict:
            if move._get_violated_lock_dates(move.date, move._affect_tax_report()):
                raise UserError(self.env._(
                    "Doklad %(name)s s datem %(day)s spadá do uzamčeného období.",
                    name=move.ref or move.id, day=move.date,
                ))
        dates = {move.id: move.date for move in strict}
        result = super()._post(soft=soft)
        for move in strict:
            if move.date != dates[move.id]:
                raise UserError(self.env._("Zaúčtování by změnilo datum dokladu %s.", move.ref or move.id))
        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    investra_class_id = fields.Many2one("investra.fund.class", string="Třída", ondelete="restrict", index="btree_not_null")
    investra_part = fields.Selection(
        [("investment", "Investiční"), ("non_investment", "Neinvestiční")], default="investment", string="Část fondu"
    )
    investra_movement_type = fields.Selection(MOVEMENT_TYPES, string="Typ pohybu")

    def _get_integrity_hash_fields(self):
        base = super()._get_integrity_hash_fields()
        return base + sorted(LINE_INVESTRA) if "name" in base else base

    def write(self, vals):
        touched = set(vals)
        if touched & LINE_INVESTRA and self.filtered(lambda l: l.parent_state == "posted"):
            raise UserError(self.env._("Třídu, část ani typ pohybu nejde po zaúčtování změnit."))
        if not _is_service(self.env) and touched & LINE_PROTECTED and self.move_id._investra_guarded():
            raise UserError(self.env._("Řádek dokladu z účetní události nejde ručně měnit."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_service(self.env):
            moves = self.env["account.move"].browse({v["move_id"] for v in vals_list if v.get("move_id")})
            if moves._investra_guarded():
                raise UserError(self.env._("Do dokladu z účetní události nejde přidat řádek."))
        return super().create(vals_list)

    def unlink(self):
        if not _is_service(self.env) and self.move_id._investra_guarded():
            raise UserError(self.env._("Řádek dokladu z účetní události nejde smazat."))
        return super().unlink()
