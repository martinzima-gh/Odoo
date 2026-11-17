"""Testovací role se stejným chováním jako skupiny před ZJ-01.

Před ZJ-01 rozhodovala matice podle nejnižší role (skupina přípravy < skupina schvalování; vyšší role splnila
i nižší požadavek). Stávající testy proto dostávají dvě role, které to chování napodobují:

- „Test: příprava“ (Zpracování) provádí činnosti, které dřív prováděla příprava (BUILTIN před ZJ-01),
- „Test: schvalování“ (Čtení) provádí i schvaluje všechny činnosti.

Nové testy rolí (`test_role.py`) zakládají role samy.
"""

from odoo.addons.investra_fund.models.approval_matrix import ACTIVITIES

PREPARER_ACTIVITIES = (
    "valuation_approve", "price_approve", "subscription_manual", "classification_override",
    "repayment_reverse", "trade_reverse",
)
PREPARER_GROUP = "investra_entity.group_valuation_preparer"
APPROVER_GROUP = "investra_entity.group_valuation_approver"


def legacy_roles(env):
    """Vrátí (role přípravy, role schvalování); založí je při prvním volání."""
    Role = env["investra.role"].sudo()
    prep = Role.search([("name", "=", "Test: příprava")])
    if not prep:
        prep = Role.create({
            "name": "Test: příprava", "access_level": "process",
            "line_ids": [(0, 0, {"activity": a, "perform": True}) for a in PREPARER_ACTIVITIES],
        })
    appr = Role.search([("name", "=", "Test: schvalování")])
    if not appr:
        appr = Role.create({
            "name": "Test: schvalování", "access_level": "read",
            "line_ids": [(0, 0, {"activity": a, "perform": True, "approve": True}) for a, _label in ACTIVITIES],
        })
    return prep, appr


def grant_legacy(env, users, preparer=None, approver=None):
    """Přiřadí uživatelům testové role. Bez `preparer`/`approver` podle jejich současných skupin."""
    prep, appr = legacy_roles(env)
    for user in users:
        if preparer if preparer is not None else user.has_group(PREPARER_GROUP):
            prep.sudo().user_ids = [(4, user.id)]
        if approver if approver is not None else user.has_group(APPROVER_GROUP):
            appr.sudo().user_ids = [(4, user.id)]
    return users
