"""Reverzní repo s nebankovní protistranou dostane roli repo_client (osnova podle vyhlášky 501, rozhodnutí 2026-11-11).

Změna role mění účet, proto jen u zařazení bez řádků v hlavní knize; ostatní zůstávají a kontrola ocenění je ukáže
jako odchylku od návrhu (přeúčtování zůstatku je samostatný účetní krok)."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    repo, client = env.ref("investra_entity.role_repo"), env.ref("investra_entity.role_repo_client")
    Line = env["account.move.line"]
    for record in env["investra.portfolio.classification"].search([("role_id", "=", repo.id)]):
        proposal = record._proposal(
            record.instrument_id, record.portfolio_id, record.instrument_nature, record.sppi, record.designation,
            record.category_override, record.valid_from,
        )
        if proposal["role_id"] == client.id and not Line.search_count([("investra_classification_id", "=", record.id)]):
            record.role_id = client
