"""Přečíslování knih fondů podle přílohy č. 4 vyhlášky 501/2002 Sb. (docs/osnova-fondu.md, rozhodnutí 2026-11-11).

Mění se jen kód účtu, účty (id), doklady, role a výpočty zůstávají. Původní číslo se zapíše do historie účtu.
Pojistka: otisk ocenění obsahuje číslo účtu, proto migrace skončí chybou, když je ocenění Ke schválení nebo Schváleno.
"""

import csv

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

from odoo.addons.investra_chart_fund.models.entity import TEMPLATE_CSV

# Pomocné účty, které založilo Odoo (xmlid account.<kniha>_<pole společnosti>), dostanou kód z šablony.
UTILITY = {
    "default_cash_difference_income_account_id": "761901",
    "default_cash_difference_expense_account_id": "661901",
    "account_journal_early_pay_discount_gain_account_id": "761902",
    "account_journal_early_pay_discount_loss_account_id": "661902",
}
# Účty založené podle prefixu (bankovní, pokladní, převodové): prefix starý → nový, zbytek kódu zůstává.
PREFIXES = {"2211": "1311", "2111": "1111", "2611": "3221"}
COMPANY_PREFIXES = {
    "bank_account_code_prefix": "1311", "cash_account_code_prefix": "1111", "transfer_account_code_prefix": "3221",
}


def _valuations_in_progress(env, companies):
    if "investra.valuation" not in env:
        return env["res.company"]
    return env["investra.valuation"].search([
        ("fund_id.company_id", "in", companies.ids), ("state", "in", ("submitted", "approved")),
    ])


def _rename(account, company, code, name=None):
    account = account.with_company(company)
    old = account.code
    if old == code and not name:
        return
    values = {"code": code}
    if name:
        values["name"] = name
    account.write(values)
    account.message_post(body=f"Původní číslo {old}, přečíslováno podle osnovy vyhlášky 501/2002 Sb. (2026-11-11).")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "investra_fund")])
    busy = _valuations_in_progress(env, companies)
    if busy:
        raise UserError(
            "Přečíslování osnovy nejde spustit: ocenění ve stavu Ke schválení nebo Schváleno (id %s). "
            "Otisk ocenění obsahuje čísla účtů; ocenění nejdřív vraťte nebo zaúčtujte." % ", ".join(map(str, busy.ids))
        )
    with TEMPLATE_CSV.open(encoding="utf-8") as handle:
        template = list(csv.DictReader(handle))
    Data = env["ir.model.data"]
    for company in companies:
        # 1. Účty šablony podle interního identifikátoru (ifa_*), před doplněním chybějících účtů, které hledá podle kódu.
        for row in template:
            account = env.ref(f"account.{company.id}_{row['id']}", raise_if_not_found=False)
            if account:
                _rename(account, company, row["code"], row["name"] if row["id"] == "ifa_256000" else None)
        # 2. Pomocné účty Odoo (999xxx) do skupin 76 a 66.
        for field, code in UTILITY.items():
            account = env.ref(f"account.{company.id}_{field}", raise_if_not_found=False)
            if account:
                _rename(account, company, code)
        # 3. Bankovní, pokladní a převodové účty podle prefixu.
        Account = env["account.account"].with_company(company)
        for account in Account.search([("company_ids", "in", company.id)]):
            prefix = account.code[:4]
            if prefix in PREFIXES and not Data.search_count([
                ("model", "=", "account.account"), ("res_id", "=", account.id), ("name", "like", f"{company.id}_ifa_%"),
            ]):
                _rename(account, company, PREFIXES[prefix] + account.code[4:])
        company.write(COMPANY_PREFIXES)
    # 4. Nové účty šablony (ifa_212000, ifa_411000, ifa_761901 …) a mapování nových rolí. Pomocné účty už mají nové
    #    kódy, takže je doplnění najde podle kódu a jen jim přidá identifikátor šablony.
    Mapping = env["investra.role.account"]
    participation = env.ref("investra_entity.role_participation")
    for entity in env["investra.entity"].search([("company_id", "in", companies.ids)]):
        entity._ensure_fund_accounts()
        company = entity.company_id
        chart = env["account.chart.template"].with_company(company)
        # Účet ifa_256000 nese účasti v reálné hodnotě (participation_fv); role participation dostane nový účet 41.
        mapping = Mapping.search([("company_id", "=", company.id), ("role_id", "=", participation.id)])
        if mapping and mapping.account_id == chart.ref("ifa_256000"):
            mapping.account_id = chart.ref("ifa_411000")
        entity._map_fund_roles()
        defaults = {field: chart.ref(f"ifa_{code}") for field, code in UTILITY.items()}
        company.write({field: account.id for field, account in defaults.items() if not company[field]})
