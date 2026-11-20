"""Nové analytické účty šablony fondů v existujících knihách (dávka ZJ-07 až ZJ-19, rozhodnutí 2026-11-19).

Doplní účty z CSV šablony, které v knize chybí (615200 Poplatky za obchody s investičními nástroji – ZJ-16; další účty
dividend, daní, pohledávek a FVOCI přibývají v dalších bězích dávky) a přidá je jako další účty rolí podle
`EXTRA_ROLE_ACCOUNTS`. Stávající účty, mapování ani doklady se nemění. Migrace je opakovatelná. Pojistka jako 0.9.0.
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
        if not entity:
            continue
        entity._ensure_fund_accounts()
        entity._map_fund_roles()
