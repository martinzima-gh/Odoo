"""Nové účty a role pro úpisy a odkupy (poplatek, rozdíl vůči investorovi, rozdíly ze zaokrouhlení) do existujících
knih fondů. Jen doplňuje chybějící účty a mapování; stávající účty, mapování a doklady se nemění."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "investra_fund")])
    for entity in env["investra.entity"].search([("company_id", "in", companies.ids)]):
        entity._ensure_fund_accounts()
        entity._map_fund_roles()
