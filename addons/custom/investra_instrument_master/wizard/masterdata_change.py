from odoo import api, fields, models
from odoo.exceptions import UserError

# Pole potvrzené klasifikace, která průvodce mění, a popisky pro historii.
FIELDS = ("ba0088_id", "cfi_code", "isin", "issuer_id")


class InvestraMasterdataChangeWizard(models.TransientModel):
    _name = "investra.masterdata.change.wizard"
    _description = "Změnit klasifikaci nástroje"

    instrument_id = fields.Many2one("investra.instrument", "Nástroj", required=True, readonly=True, ondelete="cascade")
    ba0088_id = fields.Many2one("investra.ba0088.code", "Druh ČNB (BA0088)", domain="[('selectable', '=', True)]")
    cfi_code = fields.Char("CFI")
    isin = fields.Char("ISIN")
    issuer_id = fields.Many2one("res.partner", "Emitent")
    effective_date = fields.Date("Účinnost od", required=True, default=fields.Date.context_today)
    reason = fields.Char("Důvod změny", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        instrument = self.env["investra.instrument"].browse(res.get("instrument_id"))
        if instrument:
            res.update({
                "ba0088_id": instrument.ba0088_id.id, "cfi_code": instrument.cfi_code, "isin": instrument.isin,
                "issuer_id": instrument.issuer_id.id})
        return res

    def _text(self, instrument, name, value):
        field = instrument._fields[name]
        if field.type == "many2one":
            return value.display_name if value else "–"
        return value or "–"

    def action_apply(self):
        self.ensure_one()
        instrument = self.instrument_id
        new_vals = {
            "ba0088_id": self.ba0088_id.id or False, "cfi_code": (self.cfi_code or "").strip().upper() or False,
            "isin": "".join((self.isin or "").split()).upper() or False, "issuer_id": self.issuer_id.id or False}
        def current(name):
            return (instrument[name].id if name.endswith("_id") else instrument[name]) or False

        changed = [name for name in FIELDS if current(name) != new_vals[name]]
        if not changed:
            raise UserError(self.env._("Nic se nezměnilo."))
        old_text = {name: self._text(instrument, name, instrument[name]) for name in changed}
        # Zápis jako superuživatel obchází zámek potvrzené klasifikace; uživatel zůstává původní (sledování změn).
        instrument.sudo().write({name: new_vals[name] for name in changed})
        history = self.env["investra.masterdata.change"].sudo()
        for name in changed:
            history.create({
                "res_model": instrument._name, "res_id": instrument.id, "record_name": instrument.display_name,
                "field_name": instrument._fields[name].string, "old_value": old_text[name],
                "new_value": self._text(instrument, name, instrument[name]),
                "effective_date": self.effective_date, "reason": self.reason, "user_id": self.env.user.id})
        instrument.sudo().message_post(author_id=self.env.user.partner_id.id, body=self.env._(
            "Změna klasifikace od %(date)s: %(fields)s. Důvod: %(reason)s",
            date=self.effective_date, fields=", ".join(instrument._fields[n].string for n in changed), reason=self.reason))
        return {"type": "ir.actions.act_window_close"}
