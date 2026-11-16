from odoo import api, fields, models
from odoo.exceptions import UserError

# MN-07: po prvním zaúčtovaném pohybu třídy (úpis, odkup) nejde změnit kód a měnu zveřejnění kurzu: změna by zpětně
# změnila význam zaúčtovaných pohybů. MN-12 (rozhodnutí 2026-11-16, Poznámky z průchodu 2, bod 3): zaokrouhlení
# a desetinná místa kurzu a kusů jdou měnit dál; platí pro další pohyby a ocenění, zaúčtované pohyby a uložená
# ocenění se nepřepočítají (kusy a kurz jsou na nich uložené).
LOCKED_FIELDS = ("code", "currency_id")


class InvestraFundClass(models.Model):
    _inherit = "investra.fund.class"

    movement_locked = fields.Boolean(compute="_compute_movement_locked", string="Parametry uzamčeny")

    def _compute_movement_locked(self):
        # Zaúčtovaný pohyb = pohyb, který už není v návrhu; stornovaný pohyb byl zaúčtován také a zámek drží dál.
        locked = {
            group[0].id
            for group in self.env["investra.class.movement"].sudo()._read_group(
                [("class_id", "in", self.ids), ("state", "!=", "draft")], ["class_id"], []
            )
        } if self.ids else set()
        for record in self:
            record.movement_locked = record.id in locked

    def write(self, vals):
        touched = [name for name in LOCKED_FIELDS if name in vals]
        if touched:
            for record in self:
                changed = [record._fields[name].string for name in touched if _differs(record, name, vals[name])]
                if changed and record.movement_locked:
                    raise UserError(self.env._(
                        "Třída %(class)s má zaúčtovaný úpis nebo odkup, proto nejde změnit: %(fields)s. "
                        "Poplatky, příjemce, zaokrouhlení a desetinná místa změnit jde; zaúčtované pohyby se nepřepočítají.",
                        **{"class": record.display_name, "fields": ", ".join(changed)}
                    ))
        return super().write(vals)


def _differs(record, name, new):
    """Mění zápis hodnotu pole? Měna je vazba, porovnává se podle id."""
    if name == "currency_id":
        return record.currency_id.id != (new or False)
    return record[name] != new
