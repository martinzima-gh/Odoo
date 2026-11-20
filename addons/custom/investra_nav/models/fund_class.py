from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import UserError

# MN-07: po prvním zaúčtovaném pohybu třídy (úpis, odkup) nejde změnit kód a měnu zveřejnění kurzu: změna by zpětně
# změnila význam zaúčtovaných pohybů. MN-12 (rozhodnutí 2026-11-16, Poznámky z průchodu 2, bod 3): zaokrouhlení
# a desetinná místa kurzu a kusů jdou měnit dál; platí pro další pohyby a ocenění, zaúčtované pohyby a uložená
# ocenění se nepřepočítají (kusy a kurz jsou na nich uložené). Místa kusů jdou snížit jen do přesnosti zaúčtovaných
# pohybů (`_check_unit_digits_not_below_posted`).
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
        if "unit_digits" in vals:
            self._check_unit_digits_not_below_posted(vals["unit_digits"])
        if "shares_common" in vals:
            # ZJ-08 D1: změna by zpětně změnila rozdělení zaúčtovaných ocenění.
            for record in self.filtered(lambda r: r.shares_common != bool(vals["shares_common"])):
                if record._fund_has_posted_valuation():
                    raise UserError(self.env._(
                        "Fond %s už má zaúčtované ocenění; změna „Podílí se na společných položkách“ u třídy %s by přepsala "
                        "historii. Založte novou třídu.", record.fund_id.display_name, record.code))
        return super().write(vals)

    def _fund_has_posted_valuation(self):
        self.ensure_one()
        return bool(self.env["investra.valuation"].sudo().search_count([
            ("fund_id", "=", self.fund_id.id), ("state", "in", ("posted", "sent", "confirmed", "published", "reversed")),
        ], limit=1))

    def _check_unit_digits_not_below_posted(self, new_digits):
        """MN-12 (rozhodnutí Martina 2026-11-16): desetinná místa kusů nejde snížit pod přesnost zaúčtovaných pohybů.

        Kontrola při zaúčtování platí i pro odkup; po snížení by kusy s více místy nešly odkoupit a stav třídy
        by nešel vynulovat. Stornované pohyby se nepočítají, pohyby v návrhu zkontroluje zaúčtování.
        """
        Movement = self.env["investra.class.movement"].sudo()
        for record in self:
            if new_digits is None or new_digits >= record.unit_digits:
                continue
            for movement in Movement.search([("class_id", "=", record.id), ("state", "=", "posted")], order="date, id"):
                used = _unit_places(movement.units)
                if used > new_digits:
                    raise UserError(self.env._(
                        "Třída %(class)s: desetinná místa kusů nejde snížit na %(new)s. Zaúčtovaný pohyb %(movement)s "
                        "má kusy %(units)s (%(used)s míst); po snížení by je nešlo odkoupit. Zvýšit místa nebo změnit "
                        "zaokrouhlení jde.",
                        **{"class": record.display_name, "new": new_digits, "movement": movement.display_name,
                           "units": movement.units, "used": used}
                    ))


def _unit_places(units):
    """Počet desetinných míst kusů; kusy se ukládají na 6 míst (pole `units`, digits 20,6)."""
    value = Decimal(str(round(units, 6))).normalize()
    return max(0, -value.as_tuple().exponent)


def _differs(record, name, new):
    """Mění zápis hodnotu pole? Měna je vazba, porovnává se podle id."""
    if name == "currency_id":
        return record.currency_id.id != (new or False)
    return record[name] != new
