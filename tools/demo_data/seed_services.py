"""Ukázka servisní organizace Investra Services s.r.o. v pracovní databázi `investra` (úkol IM-13).

Spouští se po seed.py přes tools/demo_data/run_seed.sh (vloží obsah services_config.json).

Rámec: vyhláška č. 500/2002 Sb. (podnikatel), osnova `cz` z l10n_cz upravená podle services_config.json – to je
export nastavení z investra_dev (services_export.sh, jen čtení: účty, daně, fiskální pozice, deníky, datum otevření).
Doklady a partneři jsou smyšlení, částky smyšlené; z investra_dev se nepřebírá žádný doklad, partner ani DIČ.
Zápis jen přes ORM a metody, které volá UI (Potvrdit, Spárovat). Bankovní výpis: Community nemá párovací okno,
proto řádek výpisu nese protiúčet partnera (standardní volba counterpart_account_id modulu account, jakou používají
importy výpisů) a s fakturou se spáruje jako akcí Spárovat v seznamu účetních položek.
Opakované spuštění nad naplněnou databází skončí hláškou a nic nezmění.
"""
import json
from datetime import date

DB = env.cr.dbname
if DB != "investra" and not DB.startswith("investra_ci_"):
    raise SystemExit(f"Ukázková data patří jen do databáze investra nebo dočasné investra_ci_*, ne do {DB}.")

NAME = "Investra Services s.r.o."
if env["res.company"].search_count([("name", "=", NAME)]):
    raise SystemExit(f"{NAME} už v databázi je; nic se nezměnilo.")
# Obsah services_config.json vloží na začátek vstupu tools/demo_data/run_seed.sh (složka tools/ není v kontejneru).
try:
    CONFIG = json.loads(CONFIG_JSON)  # noqa: F821
except NameError:
    raise SystemExit("Chybí services_config.json – spouštějte přes tools/demo_data/run_seed.sh; nic se nezměnilo.") from None

CZK, EUR = env.ref("base.CZK"), env.ref("base.EUR")
(CZK | EUR).active = True
env["res.lang"]._activate_lang("cs_CZ")
NOTE = "Ukázková data (smyšlená)"

# --- kniha a nastavení podle investra_dev ------------------------------------------------------------------------
book = env["investra.entity"].create_book(NAME, "service", "cas500", CZK, "cz")
company = book.company_id
env.invalidate_all()
if company.currency_id != CZK or company.chart_template != "cz":
    raise SystemExit(f"{NAME}: měna {company.currency_id.name}, osnova {company.chart_template}; zastaveno.")
cid = company.id
company.account_opening_date = CONFIG["opening_date"]

admin = env.ref("base.user_admin")
# Bankovní transakce smí v Community vytvářet jen skupina account.group_account_basic (Účetnictví, základní funkce).
admin.write({"company_ids": [(4, cid)], "group_ids": [(4, env.ref("account.group_account_basic").id)]})
UA = env(user=admin.id, context=dict(env.context, lang="cs_CZ", tz="Europe/Prague", allowed_company_ids=[cid]))
Account = UA["account.account"].with_company(company).with_context(active_test=False)


def ref(xml):
    return env.ref(f"account.{cid}_{xml}", raise_if_not_found=False)


DIFF = []  # rozdíly proti investra_dev, vypíšou se v souhrnu
seen = Account
for spec in CONFIG["accounts"]:
    account = (ref(spec["template"]) if spec["template"] else None) or Account.search(
        [*Account._check_company_domain(company), ("code", "=", spec["code"])], limit=1)
    if not account:
        account = Account.create({"code": spec["code"], "name": spec["name"], "account_type": spec["account_type"],
                                  "reconcile": spec["reconcile"], "company_ids": [(6, 0, [cid])]})
        DIFF.append(f"účet doplněn: {spec['code']} {spec['name']}")
    values = {k: spec[k] for k in ("code", "name", "account_type", "reconcile", "active")}
    account = account.with_company(company)
    if any(account[k] != v for k, v in values.items()):
        account.write(values)
    seen |= account
for extra in Account.search(Account._check_company_domain(company)) - seen:
    DIFF.append(f"účet je v osnově navíc proti investra_dev: {extra.code} {extra.name}")

company._setup_identified_vat_taxes()
for spec in CONFIG["taxes"]:
    tax = ref(spec["template"]) if spec["template"] else UA["account.tax"].with_context(active_test=False).search(
        [("company_id", "=", cid), ("name", "=", spec["name"])], limit=1)
    if not tax:
        DIFF.append(f"daň chybí: {spec['name']}")
    elif tax.active != spec["active"]:
        tax.active = spec["active"]
for spec in CONFIG["fiscal_positions"]:
    fpos = ref(spec["template"]) if spec["template"] else UA["account.fiscal.position"].with_context(
        active_test=False).search([("company_id", "=", cid), ("name", "=", spec["name"])], limit=1)
    if not fpos:
        DIFF.append(f"fiskální pozice chybí: {spec['name']}")
    elif fpos.active != spec["active"]:
        fpos.active = spec["active"]
for spec in CONFIG["journals"]:
    journal = ref(spec["template"])
    if not journal:
        DIFF.append(f"deník chybí: {spec['code']} {spec['name']}")
        continue
    values = {"code": spec["code"], "name": spec["name"], "active": spec["active"]}
    if spec["default_account"]:
        values["default_account_id"] = Account.search(
            [*Account._check_company_domain(company), ("code", "=", spec["default_account"])], limit=1).id
    journal.write(values)

ACC = {a.code: a for a in Account.search(Account._check_company_domain(company))}
JOURNAL = {j.code: j for j in UA["account.journal"].search([("company_id", "=", cid)])}
IO_EU_21 = UA["account.tax"].search([("company_id", "=", cid), ("name", "=", "21 % IO přijatá služba z EU")], limit=1)


# --- partneři (smyšlení) -----------------------------------------------------------------------------------------
def partner(name, country="cz", **values):
    return UA["res.partner"].create({"name": name, "is_company": True, "country_id": env.ref(f"base.{country}").id,
                                     "company_id": cid, "comment": NOTE, **values})


ALFA = partner("Alfa Správa aktiv s.r.o. (smyšlená)")
BETA = partner("Beta Family Office a.s. (smyšlená)")
KANCELARE = partner("Kanceláře Karlín s.r.o. (smyšlené)")
SOFTWARE = partner("Účetní software CZ s.r.o. (smyšlený)")
# Dodavatel z EU s DIČ: fiskální pozice „Identifikovaná osoba – EU s DIČ“ se přiřadí automaticky.
CLOUD = partner("Cloudware Solutions GmbH (smyšlená)", "de", vat="DE123456788")  # vzorové číslo z nápovědy formátu Odoo, ne skutečný subjekt


# --- faktury -----------------------------------------------------------------------------------------------------
def invoice(move_type, who, day, lines, currency=CZK, ref=None):
    move = UA["account.move"].create({
        "move_type": move_type, "partner_id": who.id, "invoice_date": day, "date": day, "currency_id": currency.id,
        "ref": ref, "narration": NOTE, "journal_id": JOURNAL["FA" if move_type == "out_invoice" else "FP"].id,
        "invoice_line_ids": [(0, 0, {"name": text, "quantity": 1, "price_unit": amount,
                                     "account_id": ACC[code].id, "tax_ids": [(6, 0, taxes.ids if taxes else [])]})
                             for text, code, amount, taxes in lines],
    })
    move.action_post()
    return move


INV = {}
for month, day in ((8, 31), (9, 30), (10, 31)):
    INV[f"alfa{month}"] = invoice("out_invoice", ALFA, date(2026, month, day), [
        ("Vedení účetnictví a správa (smyšlené)", "602100", 85000, None)])
for month, day in ((9, 30), (10, 31)):
    INV[f"beta{month}"] = invoice("out_invoice", BETA, date(2026, month, day), [
        ("Výpočet NAV – služby (smyšlené)", "602100", 40000, None)])
for month in (8, 9, 10):
    INV[f"najem{month}"] = invoice("in_invoice", KANCELARE, date(2026, month, 1), [
        ("Nájem kanceláře (smyšlený)", "518300", 30000, None)], ref=f"NAJ-2026-{month:02d} (smyšlené)")
INV["software"] = invoice("in_invoice", SOFTWARE, date(2026, 9, 12), [
    ("Licence účetního software (smyšlená)", "518810", 4900, None)], ref="US-2026-0917 (smyšlené)")
# Přijatá služba z EU v režimu identifikované osoby: daň k úhradě bez odpočtu zvyšuje náklad (investra_vat_identified).
INV["cloud"] = invoice("in_invoice", CLOUD, date(2026, 9, 10), [
    ("Cloudové služby září (smyšlené)", "518810", 450, IO_EU_21)], currency=EUR, ref="CW-2026-0910 (smyšlené)")

# --- interní doklad: dohadná položka na audit ----------------------------------------------------------------------
accrual = UA["account.move"].create({
    "move_type": "entry", "journal_id": JOURNAL["MISC"].id, "date": date(2026, 10, 31),
    "ref": "Dohadná položka – audit 2026 (smyšlená)", "narration": NOTE,
    "line_ids": [(0, 0, {"name": "Audit účetní závěrky 2026 – odhad (smyšlený)", "account_id": ACC["518950"].id,
                         "debit": 60000}),
                 (0, 0, {"name": "Audit účetní závěrky 2026 – odhad (smyšlený)", "account_id": ACC["389000"].id,
                         "credit": 60000})],
})
accrual.action_post()

# --- bankovní výpisy (BNK1) s úhradami ---------------------------------------------------------------------------
BANK = JOURNAL["BNK1"]
RECEIVABLE = ALFA.with_company(company).property_account_receivable_id
PAYABLE = ALFA.with_company(company).property_account_payable_id


def eur_rate(day):
    return UA["res.currency"]._get_conversion_rate(EUR, CZK, company, day)


STATEMENTS = {
    8: [("2026-08-03", "Příplatek společníka mimo ZK (smyšlený)", 300000, None, "413000"),
        ("2026-08-05", "Úhrada nájmu 08", -30000, "najem8", None),
        ("2026-08-31", "Poplatek za vedení účtu", -150, None, "568000")],
    9: [("2026-09-05", "Úhrada nájmu 09", -30000, "najem9", None),
        ("2026-09-14", "Platba Alfa za 08", 85000, "alfa8", None),
        ("2026-09-18", "Úhrada Cloudware CW-2026-0910", "eur", "cloud", None),
        ("2026-09-22", "Úhrada licence software", -4900, "software", None),
        ("2026-09-30", "Poplatek za vedení účtu", -150, None, "568000")],
    10: [("2026-10-05", "Úhrada nájmu 10", -30000, "najem10", None),
         ("2026-10-14", "Platba Alfa za 09", 85000, "alfa9", None),
         ("2026-10-20", "Platba Beta za 09", 40000, "beta9", None),
         ("2026-10-31", "Poplatek za vedení účtu", -150, None, "568000")],
}
balance = 0.0
for month, rows in STATEMENTS.items():
    lines = UA["account.bank.statement.line"]
    for day, label, amount, key, account_code in rows:
        move = INV.get(key)
        values = {"journal_id": BANK.id, "date": day, "payment_ref": label, "narration": NOTE}
        if move:
            values["partner_id"] = move.partner_id.id
            values["counterpart_account_id"] = (RECEIVABLE if move.move_type == "out_invoice" else PAYABLE).id
        else:
            values["counterpart_account_id"] = ACC[account_code].id
        if amount == "eur":
            # Platba v CZK z korunového účtu, dluh v EUR; kurzový rozdíl zaúčtuje Odoo při spárování.
            values.update({"foreign_currency_id": EUR.id, "amount_currency": -move.amount_total,
                           "amount": -round(move.amount_total * eur_rate(date.fromisoformat(day)), 2)})
        else:
            values["amount"] = amount
        counterpart = values["counterpart_account_id"]  # create() klíč z values odebere
        line = UA["account.bank.statement.line"].create(values)
        if move:
            open_lines = (line.move_id.line_ids | move.line_ids).filtered(lambda l: l.account_id.id == counterpart)
            open_lines.filtered(lambda l: not l.reconciled).reconcile()
        lines |= line
    start = balance
    balance = round(start + sum(lines.mapped("amount")), 2)
    UA["account.bank.statement"].create({
        "name": f"Výpis BNK1 2026/{month:02d} (smyšlený)", "journal_id": BANK.id, "date": lines[-1].date,
        "balance_start": start, "balance_end_real": balance, "line_ids": [(6, 0, lines.ids)],
    })

env.cr.commit()

# --- souhrn a kontroly -------------------------------------------------------------------------------------------
Line = UA["account.move.line"]
posted = [("company_id", "=", cid), ("parent_state", "=", "posted")]
debit = sum(Line.search(posted).mapped("debit"))
credit = sum(Line.search(posted).mapped("credit"))
moves = UA["account.move"].search([("company_id", "=", cid)])
accounts = Account.search(Account._check_company_domain(company))
taxes = UA["account.tax"].with_context(active_test=False).search([("company_id", "=", cid)])
print("SERVICES", company.name, "| osnova", company.chart_template, "| měna", company.currency_id.name,
      "| otevření", company.account_opening_date)
print("  účty aktivní/archivované:", len(accounts.filtered("active")), "/", len(accounts.filtered(lambda a: not a.active)),
      "| v investra_dev:", sum(a["active"] for a in CONFIG["accounts"]), "/", sum(not a["active"] for a in CONFIG["accounts"]))
print("  daně aktivní/archivované:", len(taxes.filtered("active")), "/", len(taxes.filtered(lambda t: not t.active)),
      "| v investra_dev:", sum(t["active"] for t in CONFIG["taxes"]), "/", sum(not t["active"] for t in CONFIG["taxes"]))
print("  doklady:", len(moves), "| nezaúčtované:", len(moves.filtered(lambda m: m.state != "posted")),
      "| předvaha MD", round(debit, 2), "D", round(credit, 2), "| vyrovnaná:", abs(debit - credit) < 0.005)
print("  faktury:", [(m.name, m.payment_state) for m in moves.filtered(lambda m: m.is_invoice())])
print("  IO faktura:", INV["cloud"].fiscal_position_id.name,
      [(l.account_id.code, l.debit, l.credit) for l in INV["cloud"].line_ids])
print("  banka zůstatek:", balance, "| rozdíly proti investra_dev:", DIFF or "žádné")
print("HOTOVO")
