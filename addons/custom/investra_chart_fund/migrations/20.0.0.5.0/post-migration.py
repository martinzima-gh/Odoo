"""Převody mezi bankami, platby na cestě a bankovní poplatky (rozhodnutí 2026-11-12 „Role s více účty“
a „Převody mezi bankami a bankovní poplatky“).

1. Účty Odoo Outstanding Receipts/Payments (dosud 1311xx mezi bankami) dostanou kódy šablony 119100 a 119200.
2. Doplní se účet 612000 Bankovní poplatky, role expense_bank_fee a další účty rolí (bankovní deníky k roli bank,
   platby na cestě k roli cash_in_transit).
3. Modely párování: Internal Transfers na převodový účet knihy (119000; dosud archivovaný 322101), Bank Fees na 612000
   (dosud první nákladový účet, tj. ztráta z přecenění).
Mění se kód a název účtu, ne id; doklady zůstávají. Migrace je opakovatelná.
Pojistka jako 0.4.0: ocenění Ke schválení nebo Schváleno migraci zastaví (otisk obsahuje čísla účtů).
"""

import csv

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

from odoo.addons.investra_chart_fund.models.entity import TEMPLATE_CSV
from odoo.addons.investra_chart_fund.models.template_investra_fund import OUTSTANDING_ACCOUNTS

NOTE = "Původní číslo {old}, platby na cestě patří k penězům na cestě 119 (2026-11-12)."


def _busy(env, companies):
    if "investra.valuation" not in env:
        return []
    return env["investra.valuation"].search([
        ("fund_id.company_id", "in", companies.ids), ("state", "in", ("submitted", "approved")),
    ]).ids


def _set_reco_account(env, company, xmlid, account):
    model = env.ref(f"account.{company.id}_{xmlid}", raise_if_not_found=False)
    if model and account:
        model.line_ids.filtered(lambda line: line.account_id != account).write({"account_id": account.id})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "investra_fund")])
    busy = _busy(env, companies)
    if busy:
        raise UserError(
            "Migraci nejde spustit: ocenění ve stavu Ke schválení nebo Schváleno (id %s). "
            "Otisk ocenění obsahuje čísla účtů; ocenění nejdřív vraťte nebo zaúčtujte." % ", ".join(map(str, busy))
        )
    with TEMPLATE_CSV.open(encoding="utf-8") as handle:
        template = {row["id"]: row for row in csv.DictReader(handle)}
    for company in companies:
        chart = env["account.chart.template"].with_company(company)
        # 1. Platby na cestě: účet Odoo dostane kód a název šablony; doplnění účtů ho pak najde podle kódu.
        for field, ifa in OUTSTANDING_ACCOUNTS.items():
            account = env.ref(f"account.{company.id}_{field}", raise_if_not_found=False)
            row = template[ifa]
            if not account or chart.ref(ifa, raise_if_not_found=False):
                continue
            old = account.with_company(company).code
            account.with_company(company).write({"code": row["code"], "name": row["name"]})
            account.message_post(body=NOTE.format(old=old))
        # 2. Účet 612000, role a další účty rolí.
        entity = env["investra.entity"].search([("company_id", "=", company.id)], limit=1)
        if entity:
            entity._ensure_fund_accounts()
            entity._map_fund_roles()
        # 3. Modely párování.
        _set_reco_account(env, company, "internal_transfer_reco", company.transfer_account_id)
        _set_reco_account(env, company, "bank_fees_reco", chart.ref("ifa_612000", raise_if_not_found=False))
