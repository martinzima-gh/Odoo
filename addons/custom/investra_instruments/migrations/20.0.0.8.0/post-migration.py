"""Účasti v reálné hodnotě do výsledku dostanou roli participation_fv (osnova podle vyhlášky 501, rozhodnutí 2026-11-11).

Bez dopadu na zůstatky: role participation_fv se v knihách mapuje na stávající účet ifa_256000, na kterém účasti dosud byly
(migrace investra_chart_fund 20.0.0.3.0)."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    participation = env.ref("investra_entity.role_participation")
    fair_value = env.ref("investra_entity.role_participation_fv")
    env["investra.portfolio.classification"].search([
        ("role_id", "=", participation.id), ("ifrs9_category", "=", "fvtpl"),
    ]).write({"role_id": fair_value.id})
