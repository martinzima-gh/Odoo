from odoo import models
from odoo.exceptions import UserError

# Pole, která mění obsah nebo připojení přílohy. Ostatní (např. přístupový token ke stažení) Odoo zapisuje samo.
CONTENT_FIELDS = {
    "raw", "db_datas", "store_fname", "url", "type", "name", "mimetype", "checksum", "file_size",
    "res_model", "res_id", "res_field", "company_id",
}
OPEN_STATES = ("draft", "computed")


class IrAttachment(models.Model):
    """Přílohy ocenění se po odeslání ke schválení nemění ani nemažou (rozhodnutí 2026-11-10).

    Odoo dovolí změnit přílohu každému, kdo smí zapisovat do připojeného záznamu, a nedívá se na stav ocenění.
    Zamčené jsou přílohy připojené k ocenění, které už není v návrhu, a přílohy ručně doložených úplat takového
    ocenění. Balíček pro depozitáře vzniká až po zaúčtování, je tedy zamčený vždy. Nová příloha jde přidat;
    nový balíček se sestaví jako nová příloha.
    """

    _inherit = "ir.attachment"

    def _investra_locked(self):
        if self.env.su or not self.ids:
            return self.browse()
        Valuation = self.env["investra.valuation"].sudo()
        rows = self.sudo().read(["res_model", "res_id"])
        valuation_ids = {row["res_id"] for row in rows if row["res_model"] == "investra.valuation" and row["res_id"]}
        closed = Valuation.browse(valuation_ids).exists().filtered(lambda v: v.state not in OPEN_STATES)
        locked = self.filtered(lambda a: a.sudo().res_model == "investra.valuation" and a.sudo().res_id in closed.ids)
        locked |= Valuation.search([("package_id", "in", self.ids)]).package_id & self
        locked |= self.env["investra.valuation.external"].sudo().search([
            ("attachment_id", "in", self.ids), ("valuation_id.state", "not in", OPEN_STATES),
        ]).attachment_id & self
        return locked

    def write(self, vals):
        if CONTENT_FIELDS & set(vals) and self._investra_locked():
            raise UserError(self.env._("Příloha ocenění po odeslání ke schválení nejde změnit."))
        return super().write(vals)

    def unlink(self):
        if self._investra_locked():
            raise UserError(self.env._("Příloha ocenění po odeslání ke schválení nejde smazat."))
        return super().unlink()
