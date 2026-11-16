"""Účty a role FX spotu, forwardu a swapu (DE-03, rozhodnutí 2026-11-16 „Účty FX spotu, forwardu a swapu“).

Doplní účty 313100–313300, 358100, 358200, 619100, 619200, 719100, 719200, 616100, 716100 a podrozvahové účty
943000, 944000, 953100, 953200, 954100, 954200, 992000 a mapování nových rolí. Účet 313000 se z „Deriváty“ přejmenuje
na „FX forward – kladná reálná hodnota“, jen pokud má dosud původní název. Stávající mapování ani doklady se nemění.
Migrace je opakovatelná. Pojistka jako 0.6.0.
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
        account = env["account.chart.template"].with_company(company).ref("ifa_257000", raise_if_not_found=False)
        if account and account.with_context(lang="cs_CZ").name == "Deriváty":
            account.with_context(lang="cs_CZ").name = "FX forward – kladná reálná hodnota"
