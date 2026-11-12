"""Účty realizovaného výsledku 715100 a 615100 (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).

Doplní nové účty šablony a mapování nových rolí gain_realised / loss_realised; stávající účty, mapování ani doklady
se nemění. Migrace je opakovatelná. Pojistka jako 0.6.0: ocenění Ke schválení nebo Schváleno migraci zastaví.
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
    for company in companies:
        entity = env["investra.entity"].search([("company_id", "=", company.id)], limit=1)
        if entity:
            entity._ensure_fund_accounts()
            entity._map_fund_roles()
