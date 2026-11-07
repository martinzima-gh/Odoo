from odoo import api, models
from odoo.exceptions import UserError


class InvestraRecordGuard(models.AbstractModel):
    """Ochrana záznamů knihy před zápisem přes API.

    Odoo kontroluje přístup při zápisu jen podle stavu před změnou, proto záznam nesmí změnit vazbu na knihu.
    Hodnoty default_* z kontextu se doplňují až uvnitř create, proto se u systémových polí odstraní.
    """

    _name = "investra.record.guard"
    _description = "Ochrana záznamu knihy"

    _book_fields = ()
    _system_fields = frozenset()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self._system_fields:
            blocked = {f"default_{name}" for name in self._system_fields}
            self = self.with_context({key: value for key, value in self.env.context.items() if key not in blocked})
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            for name in self._book_fields:
                if name in vals and self.filtered(lambda record: record[name].id != vals[name]):
                    raise UserError(self.env._("Záznam nejde přesunout do jiného fondu. Smažte ho a založte znovu."))
        return super().write(vals)
