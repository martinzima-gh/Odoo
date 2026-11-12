import csv
from pathlib import Path

from odoo import api, models

from .template_investra_fund import EXTRA_ROLE_ACCOUNTS, ROLE_ACCOUNTS

TEMPLATE_CSV = Path(__file__).parent.parent / "data" / "template" / "account.account-investra_fund.csv"


class InvestraEntity(models.Model):
    _inherit = "investra.entity"

    @api.model
    def create_book(self, name, entity_type, framework, currency, template, country=None, **values):
        entity = super().create_book(name, entity_type, framework, currency, template, country, **values)
        if template == "investra_fund":
            entity._map_fund_roles()
        return entity

    def _ensure_fund_accounts(self):
        """Doplní do knihy účty šablony, které v ní chybějí (nové účty po aktualizaci modulu).

        Účet dostane stejné xmlid jako při načtení šablony (`account.<kniha>_<id>`); stávající účty se nemění.
        """
        self.ensure_one()
        company = self.company_id
        chart = self.env["account.chart.template"].sudo().with_company(company)
        Data = self.env["ir.model.data"].sudo()
        Account = self.env["account.account"].sudo().with_company(company)
        with TEMPLATE_CSV.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if chart.ref(row["id"], raise_if_not_found=False):
                    continue
                account = Account.search([("code", "=", row["code"]), ("company_ids", "in", company.id)], limit=1)
                account = account or Account.create({
                    "name": row["name"], "code": row["code"], "account_type": row["account_type"],
                    "reconcile": row["reconcile"] == "True", "company_ids": [(6, 0, company.ids)],
                })
                Data.create({
                    "module": "account", "name": f"{company.id}_{row['id']}", "model": "account.account",
                    "res_id": account.id, "noupdate": True,
                })

    def _map_fund_roles(self):
        """Mapování rolí na účty šablony; existující mapování se nemění."""
        self.ensure_one()
        chart = self.env["account.chart.template"].sudo().with_company(self.company_id)
        Mapping = self.env["investra.role.account"].sudo()
        mapped = Mapping.search([("company_id", "=", self.company_id.id)]).role_id
        roles = self.env["investra.account.role"].search([("code", "in", list(ROLE_ACCOUNTS))]) - mapped
        Mapping.create([
            {
                "company_id": self.company_id.id,
                "role_id": role.id,
                "account_id": chart.ref(ROLE_ACCOUNTS[role.code]).id,
            }
            for role in roles
        ])
        self._assign_extra_accounts()

    def _assign_extra_accounts(self):
        """Další účty rolí: platby na cestě k roli cash_in_transit, účty bankovních deníků k roli bank.

        Opakovatelné; účet, který už v knize nějakou roli má, se nemění (rozhodnutí 2026-11-12 „Role s více účty“).
        """
        self.ensure_one()
        company = self.company_id
        chart = self.env["account.chart.template"].sudo().with_company(company)
        Role = self.env["investra.account.role"].sudo()
        for code, ifas in EXTRA_ROLE_ACCOUNTS.items():
            for ifa in ifas:
                account = chart.ref(ifa, raise_if_not_found=False)
                if account:
                    Role.add_extra_account(company, code, account)
        journals = self.env["account.journal"].sudo().search([("company_id", "=", company.id), ("type", "=", "bank")])
        for account in journals.default_account_id:
            Role.add_extra_account(company, "bank", account)
