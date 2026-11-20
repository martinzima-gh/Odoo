"""Dividendy a ex-kupón (ZJ-19), dávka ZJ-07 až ZJ-19.

Do profilů přecenění stávajících fondů přidá účty pohledávek z dividend (341210) a ze zahraniční daně k vrácení (341220), pokud
je kniha má (účty doplňuje migrace investra_chart_fund 20.0.0.13.0, která běží dřív). Nový fond je dostane při založení profilu.
Doklady ani dřívější ocenění se nemění. Opakovatelné. Další kroky migrace této verze (sazby daně) doplní běh 5 dávky.
"""
from odoo import SUPERUSER_ID, api

DIVIDEND_RECEIVABLE_CODES = ("341210", "341220")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Mapping = env["investra.role.account"]
    for profile in env["investra.fx.profile"].with_context(active_test=False).search([("fund_id", "!=", False)]):
        mapping = Mapping.search([("company_id", "=", profile.company_id.id), ("role_id.code", "=", "receivable_other")], limit=1)
        accounts = mapping.extra_account_ids.filtered(lambda a: a.code in DIVIDEND_RECEIVABLE_CODES) - profile.account_ids
        if accounts:
            profile.with_context(tracking_disable=True).account_ids = [(4, account.id) for account in accounts]
