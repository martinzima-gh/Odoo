"""Upozornění na formuláři záznamu, u kterého čeká žádost podle schvalovací matice (MN-18, nález MN-13 č. 8, varianta B).

Úkon se čtyřma očima (storno, oprava, zveřejnění, ruční kategorie…) založí žádost `investra.approval.request`
a potvrzuje se v Žádostech ke schválení, ne na záznamu. Model, který volá `investra.approval.matrix._gate`
s vlastním záznamem, dědí tento mixin a formulář zobrazí upozornění s odkazem na žádost.
Jen čtení: nic se neukládá, stavy ani účtování se nemění.
"""

from odoo import fields, models


class InvestraApprovalPendingMixin(models.AbstractModel):
    _name = "investra.approval.pending.mixin"
    _description = "Upozornění na čekající žádost ke schválení"

    pending_request_id = fields.Many2one(
        "investra.approval.request", compute="_compute_pending_request_id", string="Čekající žádost",
    )

    def _compute_pending_request_id(self):
        ids = [i for i in (r._origin.id or r.id for r in self) if isinstance(i, int) and i]
        found = {}
        if ids:
            # sudo: upozornění vidí každý, kdo záznam otevře; žádost je stejné společnosti jako záznam.
            requests = self.env["investra.approval.request"].sudo().search(
                [("res_model", "=", self._name), ("res_id", "in", ids), ("state", "=", "pending")], order="id",
            )
            for request in requests:
                found[request.res_id] = request  # při více žádostech platí nejnovější
        for record in self:
            record.pending_request_id = found.get(record._origin.id or record.id) or False

    def action_open_pending_request(self):
        self.ensure_one()
        return self.pending_request_id._action_open() if self.pending_request_id else False
