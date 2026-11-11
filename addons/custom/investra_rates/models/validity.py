from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .rate import APPROVER


class InvestraRateValidity(models.Model):
    """Nejvyšší stáří kurzu podle kurzovního lístku a měny (rozhodnutí 2026-11-11 „Platnost kurzů a smíšené kurzy“).

    Řádek bez měny je výchozí pro lístek, řádek s měnou je výjimka. Jediné místo nastavení pro ocenění,
    přecenění cizích měn a úpisy a odkupy; doklady Odoo počítají kurz standardně a tabulkou se neřídí
    (rozhodnutí 2026-11-11 „Riziko 4 akceptováno, standard Odoo“). Mění jen skupina schvalování ocenění,
    změny sleduje chatter, řádky se nemažou, jen archivují.
    """

    _name = "investra.rate.validity"
    _description = "Platnost kurzu"
    _inherit = ["mail.thread"]
    _order = "source, periodicity, currency_id nulls first, id"

    source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], required=True, string="Zdroj", tracking=True)
    periodicity = fields.Selection(
        [("daily", "Denní"), ("monthly", "Měsíční")], required=True, default="daily", string="Vyhlašování", tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency", ondelete="restrict", string="Měna", tracking=True,
        help="Prázdná = výchozí hodnota pro lístek; vyplněná = výjimka pro měnu.",
    )
    max_age_days = fields.Integer(
        required=True, string="Nejvyšší stáří (dny)", tracking=True,
        help="Kalendářní dny mezi datem kurzu a datem, ke kterému se kurz použije.",
    )
    active = fields.Boolean(default=True, tracking=True, string="Aktivní")

    @api.depends("source", "periodicity", "currency_id")
    def _compute_display_name(self):
        sources = dict(self._fields["source"].selection)
        periods = dict(self._fields["periodicity"].selection)
        for rec in self:
            name = f"{sources.get(rec.source, '')} {periods.get(rec.periodicity, '').lower()}"
            rec.display_name = f"{name} – {rec.currency_id.name}" if rec.currency_id else name

    @api.constrains("source", "periodicity", "currency_id", "max_age_days", "active")
    def _check_row(self):
        for rec in self:
            if rec.max_age_days < 0:
                raise ValidationError(self.env._("Nejvyšší stáří kurzu nesmí být záporné."))
            if rec.source == "ecb" and rec.periodicity != "daily":
                raise ValidationError(self.env._("ECB vyhlašuje jen denní kurzy."))
            if not rec.active:
                continue
            twins = self.search_count([
                ("id", "!=", rec.id), ("source", "=", rec.source), ("periodicity", "=", rec.periodicity),
                ("currency_id", "=", rec.currency_id.id),
            ])
            if twins:
                raise ValidationError(self.env._("Platnost pro tento lístek a měnu už existuje."))

    def _check_approver(self):
        if not self.env.su and not self.env.user.has_group(APPROVER):
            raise AccessError(self.env._("Platnost kurzů smí měnit jen uživatel se skupinou schvalování ocenění."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_approver()
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) - {"message_main_attachment_id"}:
            self._check_approver()
        return super().write(vals)

    def unlink(self):
        raise UserError(self.env._("Platnost kurzu nejde smazat; řádek archivujte."))

    @api.model
    def max_age(self, source, periodicity, currency):
        """Nejvyšší stáří kurzu: výjimka pro měnu, jinak výchozí řádek lístku; bez nastavení chyba."""
        rows = self.sudo().search([
            ("source", "=", source), ("periodicity", "=", periodicity), ("currency_id", "in", (currency.id, False)),
        ])
        row = rows.filtered("currency_id")[:1] or rows[:1]
        if not row:
            raise UserError(self.env._(
                "Chybí nastavení platnosti kurzu pro zdroj %(zdroj)s (%(vyhlaseni)s); "
                "doplňte ho v Investra → Nastavení → Účtování → Platnost kurzů.",
                zdroj=source.upper(), vyhlaseni=periodicity,
            ))
        return row.max_age_days
