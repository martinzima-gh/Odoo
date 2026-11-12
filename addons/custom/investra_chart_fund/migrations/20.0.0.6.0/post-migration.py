"""Inkasa na cestě jako vlastní role (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“).

Účet 119100 (Odoo Outstanding Receipts) byl dalším účtem role cash_in_transit; nově je hlavním účtem role
cash_in_transit_receipt, na kterou účtují splátky nástrojů. Účet ani doklady se nemění, mění se jen mapování rolí;
zůstatky ve výkazech ČNB zůstávají ve stejných řádcích (mapování v investra_cnb). Migrace je opakovatelná.
Pojistka jako 0.5.0: ocenění Ke schválení nebo Schváleno migraci zastaví (kontroly a výkazy berou mapování rolí).
"""

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "investra_fund")])
    if "investra.valuation" in env:
        busy = env["investra.valuation"].search([
            ("fund_id.company_id", "in", companies.ids), ("state", "in", ("submitted", "approved")),
        ]).ids
        if busy:
            raise UserError(
                "Migraci nejde spustit: ocenění ve stavu Ke schválení nebo Schváleno (id %s); "
                "ocenění nejdřív vraťte nebo zaúčtujte." % ", ".join(map(str, busy))
            )
    Mapping = env["investra.role.account"]
    for company in companies:
        receipts = env["account.chart.template"].with_company(company).ref("ifa_119100", raise_if_not_found=False)
        if not receipts:
            continue
        transit = Mapping.search([("company_id", "=", company.id), ("role_id.code", "=", "cash_in_transit")])
        if receipts in transit.extra_account_ids:
            transit.extra_account_ids = [(3, receipts.id)]
        entity = env["investra.entity"].search([("company_id", "=", company.id)], limit=1)
        if entity:
            entity._map_fund_roles()
