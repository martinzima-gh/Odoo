from odoo import api, models

from .template_investra_fund import ROLE_ACCOUNTS


class InvestraEntity(models.Model):
    _inherit = "investra.entity"

    @api.model
    def create_book(self, name, entity_type, framework, currency, template, country=None, **values):
        entity = super().create_book(name, entity_type, framework, currency, template, country, **values)
        if template == "investra_fund":
            entity._map_fund_roles()
        return entity

    def _map_fund_roles(self):
        self.ensure_one()
        chart = self.env["account.chart.template"].sudo().with_company(self.company_id)
        roles = self.env["investra.account.role"].search([("code", "in", list(ROLE_ACCOUNTS))])
        self.env["investra.role.account"].sudo().create([
            {
                "company_id": self.company_id.id,
                "role_id": role.id,
                "account_id": chart.ref(ROLE_ACCOUNTS[role.code]).id,
            }
            for role in roles
        ])
