"""Ukázkové role a uživatelé Investry (úkol ZJ-02, rozhodnutí 2026-11-17).

Spouští se přes tools/demo_data/run_seed.sh (po seed.py a seed_services.py), jen v `investra` nebo `investra_ci_*`.
Role (úroveň přístupu, činnosti Provádí / Schvaluje, příznak „Účtuje ručně v hlavní knize“):
  Admin        Správa,      všechny činnosti Provádí i Schvaluje, účtuje ručně
  Účetní       Zpracování,  všechny činnosti Provádí,             účtuje ručně
  Schvalovatel Zpracování,  všechny činnosti Provádí i Schvaluje, účtuje ručně
  Náhled       Čtení,       bez činností,                         neúčtuje
Uživatelé: admin (existující base.user_admin: Admin + správce systému; heslo se nemění), ucetni, schvalovatel, view
(přístup ke všem účetním knihám). Heslo ukázkových uživatelů je jen z proměnné prostředí INVESTRA_DEMO_USER_PASSWORD
(run_seed.sh ji převezme z .env); bez ní skript skončí chybou a nic nezmění. Heslo se nikam nevypisuje.
Idempotentní: existující role a uživatel se aktualizuje (činnosti rolí se sesynchronizují, role se uživateli doplní).
"""
import os

from odoo.addons.investra_fund.models.approval_matrix import ACTIVITIES

DB = env.cr.dbname
if DB != "investra" and not DB.startswith("investra_ci_"):
    raise SystemExit(f"Ukázkoví uživatelé patří jen do databáze investra nebo dočasné investra_ci_*, ne do {DB}.")
PASSWORD = os.environ.get("INVESTRA_DEMO_USER_PASSWORD", "")
if not PASSWORD:
    raise SystemExit("Chybí proměnná INVESTRA_DEMO_USER_PASSWORD (nastavte ji v .env); nic se nezměnilo.")

ALL = [activity for activity, _label in ACTIVITIES]
ROLES = {
    "Admin": ("admin", True, {a: (True, True) for a in ALL}),
    "Účetní": ("process", True, {a: (True, False) for a in ALL}),
    "Schvalovatel": ("process", True, {a: (True, True) for a in ALL}),
    "Náhled": ("read", False, {}),
}
USERS = {  # login: (jméno, role, správce systému)
    "admin": (None, "Admin", True),
    "ucetni": ("Účetní (ukázka)", "Účetní", False),
    "schvalovatel": ("Schvalovatel (ukázka)", "Schvalovatel", False),
    "view": ("Náhled (ukázka)", "Náhled", False),
}

Role = env["investra.role"].sudo()
role = {}
for name, (level, manual, lines) in ROLES.items():
    rec = Role.with_context(active_test=False).search([("name", "=", name)], limit=1)
    vals = {"name": name, "access_level": level, "manual_posting": manual, "active": True}
    if rec:
        rec.write(vals)
        rec.line_ids.unlink()
    else:
        rec = Role.create(vals)
    rec.write({"line_ids": [(0, 0, {"activity": a, "perform": p, "approve": s}) for a, (p, s) in lines.items()]})
    role[name] = rec
    print(f"  role {name}: {level}, činností {len(lines)}")

companies = env["res.company"].sudo().search([])
Users = env["res.users"].sudo().with_context(active_test=False)
internal = env.ref("base.group_user")
system = env.ref("base.group_system")
for login, (full_name, role_name, is_system) in USERS.items():
    user = Users.search([("login", "=", login)], limit=1)
    if login == "admin" and not user:
        raise SystemExit("Uživatel admin v databázi není; nic dalšího se nezměnilo.")
    if not user:
        user = Users.create({
            "name": full_name, "login": login, "password": PASSWORD, "lang": "cs_CZ", "tz": "Europe/Prague",
            "company_id": companies[0].id, "company_ids": [(6, 0, companies.ids)],
            "group_ids": [(4, internal.id)],
        })
        state = "založen"
    else:
        vals = {"active": True, "company_ids": [(6, 0, (user.company_ids | companies).ids)]}
        if login != "admin":  # existující ukázkový uživatel dostane znovu heslo z proměnné; admin si ponechá své
            vals["password"] = PASSWORD
        user.write(vals)
        state = "aktualizován"
    if is_system:
        user.write({"group_ids": [(4, system.id)]})
    user.write({"investra_role_ids": [(6, 0, [role[role_name].id])]})
    print(f"  uživatel {login}: {state}, role {role_name}, knih {len(user.company_ids)}")
env.cr.commit()
print("HOTOVO: role a ukázkoví uživatelé.")
