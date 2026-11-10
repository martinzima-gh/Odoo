from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_rates(self, company, date):
        """Kurz platí už v den, ke kterému je vyhlášený. Odoo 20 hledá ostře před datem, proto den navíc."""
        return super()._get_rates(company, fields.Date.to_date(date) + timedelta(days=1))


class ResCurrencyRate(models.Model):
    """Kurzy Odoo zapisuje jen evidence kurzů Investra (rozhodnutí 2026-11-10 „Ochrana kurzů“).

    Ruční zápis v nastavení měn by dal dokladům jiný kurz, než s jakým počítá ocenění. Evidence zapisuje
    jako systém (sudo); každý jiný zápis se odmítne s odkazem na ruční kurz v evidenci.
    """

    _inherit = "res.currency.rate"

    def _check_investra_source(self):
        if not self.env.su:
            raise UserError(self.env._(
                "Kurzy měn se zadávají jen v Investra → Nastavení → Účtování → Kurzy měn "
                "(ruční kurz nebo přepis s důvodem)."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_investra_source()
        return super().create(vals_list)

    def write(self, vals):
        self._check_investra_source()
        return super().write(vals)

    def unlink(self):
        self._check_investra_source()
        return super().unlink()
