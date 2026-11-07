from datetime import timedelta

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_rates(self, company, date):
        """Kurz platí už v den, ke kterému je vyhlášený. Odoo 20 hledá ostře před datem, proto den navíc."""
        return super()._get_rates(company, fields.Date.to_date(date) + timedelta(days=1))
