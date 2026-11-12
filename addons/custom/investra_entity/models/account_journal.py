from odoo import api, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model_create_multi
    def create(self, vals_list):
        """Účet nového bankovního deníku se přidá k roli bank jako další účet (rozhodnutí 2026-11-12
        „Role s více účty“), aby jeho zůstatek viděly výkazy ČNB a kontroly ocenění. Účtuje se dál na hlavní účet role."""
        journals = super().create(vals_list)
        Role = self.env["investra.account.role"]
        for journal in journals.filtered(lambda j: j.type == "bank" and j.default_account_id):
            Role.add_extra_account(journal.company_id, "bank", journal.default_account_id)
        return journals
