"""Zámek ocenění, vrstva 1 (rozhodnutí „Zámek ocenění ve třech vrstvách“, 2026-11-11).

Od stavu Ke schválení do Potvrzeno depozitářem nejde do fondové knihy zaúčtovat, stornovat ani vrátit do návrhu
doklad s datem ≤ datu ocenění, kromě dokladů samotného ocenění. Úpis ani odkup s takovým datem nejde zadat,
změnit ani smazat. Zámek zruší vrácení ocenění. Po zveřejnění platí zámek Odoo (vrstva 2 a 3).
"""

from odoo import api, models
from odoo.exceptions import UserError

LOCK_STATES = ("submitted", "approved", "posted", "sent", "confirmed")


class InvestraValuation(models.Model):
    _inherit = "investra.valuation"

    @api.model
    def _locking(self, company, day):
        """Ocenění knihy, která zamykají datum `day` (stav Ke schválení až Potvrzeno, datum ocenění ≥ day)."""
        return self.sudo().search([
            ("company_id", "=", company.id), ("state", "in", LOCK_STATES), ("date", ">=", day),
        ], order="date desc, version desc")

    @api.model
    def _raise_locked(self, locking, day, what):
        valuation = locking[0]
        state = dict(valuation._fields["state"]._description_selection(self.env))[valuation.state]
        raise UserError(self.env._(
            "%(what)s s datem %(day)s nejde provést: ocenění %(valuation)s je ve stavu %(state)s. "
            "Nejdřív ocenění vraťte, nebo použijte datum po %(date)s.",
            what=what, day=day, valuation=valuation.display_name, state=state, date=valuation.date,
        ))


class AccountMove(models.Model):
    _inherit = "account.move"

    def _investra_check_valuation_lock(self, what):
        Valuation = self.env["investra.valuation"]
        for move in self:
            if not move.date:
                continue
            locking = Valuation._locking(move.company_id, move.date)
            if not locking:
                continue
            # Doklady samotného ocenění (zaúčtování i storno při vrácení depozitářem) zámek nezastaví.
            if move.investra_event_id and move.investra_event_id in locking.sudo().event_ids:
                continue
            Valuation._raise_locked(locking, move.date, what)

    def _post(self, soft=True):
        self._investra_check_valuation_lock(self.env._("Zaúčtování dokladu"))
        return super()._post(soft=soft)

    def button_draft(self):
        self._investra_check_valuation_lock(self.env._("Vrácení dokladu do návrhu"))
        return super().button_draft()


class InvestraClassMovement(models.Model):
    _inherit = "investra.class.movement"

    def _check_valuation_lock(self, company, day, what):
        locking = self.env["investra.valuation"]._locking(company, day)
        if locking:
            self.env["investra.valuation"]._raise_locked(locking, day, what)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for movement in records:
            movement._check_valuation_lock(movement.company_id, movement.date, self.env._("Zadání úpisu nebo odkupu"))
        return records

    def write(self, vals):
        # Vazbu na událost, stav a ocenění s cenou zapisuje zaúčtování; to hlídá zámek dokladu.
        if set(vals) - {"event_id", "state", "valuation_id"}:
            for movement in self:
                movement._check_valuation_lock(movement.company_id, movement.date, self.env._("Změna úpisu nebo odkupu"))
        result = super().write(vals)
        if set(vals) & {"date", "class_id"}:
            for movement in self:
                movement._check_valuation_lock(movement.company_id, movement.date, self.env._("Změna úpisu nebo odkupu"))
        return result

    def unlink(self):
        for movement in self:
            movement._check_valuation_lock(movement.company_id, movement.date, self.env._("Smazání úpisu nebo odkupu"))
        return super().unlink()
