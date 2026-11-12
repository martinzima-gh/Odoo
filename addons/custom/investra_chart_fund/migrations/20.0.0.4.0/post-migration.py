"""Syntetické účty šablony fondů podle vnitřního standardu rámce 501 (docs/osnova-501-syntetika.md, rozhodnutí 2026-11-12).

Mění se jen kód účtu; účty (id), doklady, role a výpočty zůstávají. Původní číslo se zapíše do historie účtu.
Současně se oddělí neidentifikované platby (nový účet 229000, role unidentified_payment) od peněz na cestě (119000),
které jsou nově i převodovým účtem Odoo. Migrace je opakovatelná: co už je hotové, přeskočí.
Pojistka: otisk ocenění obsahuje číslo účtu, proto migrace skončí chybou, když je ocenění Ke schválení nebo Schváleno.
"""

import csv

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

from odoo.addons.investra_chart_fund.models.entity import TEMPLATE_CSV

NOTE = "Původní číslo {old}, přečíslováno podle syntetických účtů rámce 501 (2026-11-12)."
TRANSFER_OLD, TRANSFER_NEW = "3221", "1191"


def _busy(env, companies):
    if "investra.valuation" not in env:
        return []
    return env["investra.valuation"].search([
        ("fund_id.company_id", "in", companies.ids), ("state", "in", ("submitted", "approved")),
    ]).ids


def _set_code(account, company, code):
    account.with_company(company).write({"code": code})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "investra_fund")])
    busy = _busy(env, companies)
    if busy:
        raise UserError(
            "Přečíslování osnovy nejde spustit: ocenění ve stavu Ke schválení nebo Schváleno (id %s). "
            "Otisk ocenění obsahuje čísla účtů; ocenění nejdřív vraťte nebo zaúčtujte." % ", ".join(map(str, busy))
        )
    with TEMPLATE_CSV.open(encoding="utf-8") as handle:
        template = list(csv.DictReader(handle))
    Line = env["account.move.line"].sudo()
    for company in companies:
        # 1. Účty šablony podle identifikátoru. Některé nové kódy dnes nese jiný účet (384000, 714000, 133000),
        #    proto nejdřív dočasný kód, potom konečný.
        changes = []
        for row in template:
            account = env.ref(f"account.{company.id}_{row['id']}", raise_if_not_found=False)
            if account and account.with_company(company).code != row["code"]:
                changes.append((account, account.with_company(company).code, row["code"]))
        for account, _old, new in changes:
            _set_code(account, company, f"TMP{new}")
        for account, old, new in changes:
            _set_code(account, company, new)
            account.message_post(body=NOTE.format(old=old))
        chart = env["account.chart.template"].with_company(company)
        transit = chart.ref("ifa_261000")
        if not transit.reconcile:
            transit.reconcile = True  # převodový účet Odoo musí být párovatelný
        # 2. Nový účet 229000 a mapování nové role (doplní chybějící účty šablony a role, stávající nemění).
        entity = env["investra.entity"].search([("company_id", "=", company.id)], limit=1)
        if entity:
            entity._ensure_fund_accounts()
            entity._map_fund_roles()
        suspense = chart.ref("ifa_229000")
        # 3. Neidentifikované platby: účet nevyjasněných položek na společnosti i na denících, které měly peníze na cestě.
        company.account_journal_suspense_account_id = suspense
        journals = env["account.journal"].search([
            ("company_id", "=", company.id), ("suspense_account_id", "=", transit.id),
        ])
        journals.write({"suspense_account_id": suspense.id})
        # 4. Převody mezi bankami přes peníze na cestě. Dosavadní převodové účty 3221xx bez dokladů se archivují.
        #    Účet s doklady by po přečíslování neměl roli a zmizel by z výkazů ČNB, proto migrace skončí chybou.
        Account = env["account.account"].with_company(company)
        old_transfers = Account.search([("company_ids", "in", company.id)]).filtered(
            lambda a: (a.code or "").startswith(TRANSFER_OLD)
        )
        used = old_transfers.filtered(lambda a: Line.search_count([("account_id", "=", a.id)], limit=1))
        if used:
            raise UserError(
                "Kniha %s: převodový účet %s má doklady. Zůstatek převeďte na peníze na cestě (119000) "
                "a migraci spusťte znovu." % (company.name, ", ".join(used.with_company(company).mapped("code")))
            )
        company.write({"transfer_account_code_prefix": TRANSFER_NEW, "transfer_account_id": transit.id})
        for account in old_transfers:
            account.message_post(body="Archivováno: převody mezi bankami jdou přes účet peněz na cestě "
                                      f"{transit.with_company(company).code} (rozhodnutí 2026-11-12).")
            account.active = False
