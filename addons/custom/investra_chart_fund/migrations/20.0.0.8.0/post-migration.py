"""Pracovní účty poplatků ve prospěch fondu nebo třídy (rozhodnutí 2026-11-13 „Příjemce vstupního a výstupního poplatku“).

Doplní účty 564100, 564200, 767200, 767300 a mapování nových rolí entry/exit_fee_income a entry/exit_fee_capital;
stávající účty, mapování ani doklady se nemění. Migrace je opakovatelná. Pojistka jako 0.6.0.
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
