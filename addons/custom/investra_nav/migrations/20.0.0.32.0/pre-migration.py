"""ZJ-01 (rozhodnutí 2026-11-17): kroky schválení ocenění mají roli (`role_id`); dřívější nejnižší role
zůstává v `min_role` jako text (název role místo kódu)."""

from odoo.addons.investra_fund.zj01_migration import role_codes_to_text


def migrate(cr, version):
    role_codes_to_text(cr, "investra_valuation_approval", "min_role")
