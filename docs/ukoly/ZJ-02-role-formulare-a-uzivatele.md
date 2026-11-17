# ZJ-02 Role: formuláře, nabídka a ukázkoví uživatelé

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (formuláře, data, skript ukázkových dat) |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-01) |
| Větev úkolu | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Navazuje na | ZJ-01, rozhodnutí 2026-11-17 „Ukázkoví uživatelé“ |
| Model | Sonnet |

**Rozhodnutí Martina 17. 11. 2026 po ZJ-01** (deník: „Ruční účtování a správa matice“):
- Role dostane příznak **Účtuje ručně v hlavní knize**; zapnutý odvodí `account.group_account_user` (synchronizace jako
  ostatní skupiny v `investra_fund/models/role.py`, odebrání jen pokud ho nedává jiná role a uživatel není admin).
  Zapnout rolím Admin, Účetní a Schvalovatel; Náhled ne.
- **Schvalovací matici i role mění jen úroveň Správa** (nebo `base.group_system`); změnit kontrolu v `approval_matrix.py`
  (`create`, `_check_editable`) a pravidla v `ir.access.csv`; upravit testy, které matici mění skupinou schvalování.

**Postup:**
1. Nabídka **Nastavení → Uživatelé a role → Role** (seznam, formulář: úroveň přístupu, tabulka činností s Provádí /
   Schvaluje, uživatelé). Ve formuláři uživatele Odoo záložka **Role Investra** (M2M rolí). Zápis jen úroveň Správa.
2. Formulář matice podle ZJ-01: bez obhospodařovatele, zpřísnění a jmenovitých uživatelů; kroky s rolí. Ve formuláři
   fondu odstranit záložku Zpřísnění matice (MN-17).
3. `tools/demo_data/seed.py` (nebo samostatný `seed_users.py` volaný z `run_seed.sh`): role **Admin** (Správa, všechny
   činnosti Provádí i Schvaluje), **Účetní** (Zpracování, vše Provádí), **Schvalovatel** (Zpracování, vše Provádí
   i Schvaluje), **Náhled** (Čtení, bez činností). Uživatelé `admin` (Admin + `base.group_system`), `ucetni`, `schvalovatel`,
   `view`, přístup ke všem knihám. **Heslo jen z proměnné `INVESTRA_DEMO_USER_PASSWORD` v `.env`**; bez ní skript skončí
   chybou. Heslo nikdy do kódu, logu ani výstupu. Skript idempotentní (uživatel nebo role existuje → aktualizuje).
4. Testy formulářů a přístupu: `view` nic nezapíše, `ucetni` nevidí nabídku Role, `schvalovatel` potvrdí žádost `ucetni`.

**Mimo rozsah:** logika matice (ZJ-01), manuál (ZJ-04), spuštění skriptu nad `investra` (ZJ-04).

**Kritéria přijetí:** `tools/run_tests.sh all` zelené; skript ověřen na dočasné `investra_ci_*`; sekce Výsledek.

## Výsledek

Provedl Claude (Sonnet) 17. 11. 2026 ve větvi `ukol/ZJ-zjednoduseni`; do `investra` se nenasazovalo (ZJ-04).

**Co se změnilo**

| Soubor | Změna |
|---|---|
| `investra_fund/models/role.py` | příznak `manual_posting` („Účtuje ručně v hlavní knize“) odvozuje `account.group_account_user`; odebere se jen když ho nedává jiná role uživatele a uživatel není správce systému ani správce účetnictví (ti si ho ponechají, mají-li ho přidělený; oprava při převzetí: skupiny ho v Odoo 20 neimplikují) |
| `investra_fund/models/approval_matrix.py`, `security/ir.access.csv` | matici a její kroky mění jen úroveň Správa nebo `base.group_system` (`_check_manage` v `create` i `_check_editable`); práva crud pro skupinu správy a správce systému místo skupiny schvalování |
| `investra_fund/views/role_views.xml` (nový, verze 0.11.0) | Nastavení → Uživatelé a role → Role (seznam, hledání, formulář s úrovní, příznakem účtování, tabulkou činností Provádí / Schvaluje, uživateli, poznámkou, chatter); záložka Role Investra ve formuláři uživatele Odoo; nabídka i záložka jen pro Správu a správce systému |
| formulář matice a fondu | beze změny: bez obhospodařovatele, zpřísnění a jmenovitých uživatelů, záložka Zpřísnění matice ve fondu už po ZJ-01 není |
| `tools/demo_data/seed_users.py` (nový), `run_seed.sh` | role Admin, Účetní, Schvalovatel, Náhled a uživatelé `admin`, `ucetni`, `schvalovatel`, `view` s přístupem ke všem knihám; heslo jen z `INVESTRA_DEMO_USER_PASSWORD` (proměnná prostředí, jinak jedna řádka z `.env`; do kontejneru `-e NÁZEV`), bez ní skript skončí chybou; nikam se nevypisuje; idempotentní (role a činnosti se synchronizují, existujícímu `admin` se heslo nemění) |
| testy | nové `investra_fund/tests/test_role_access.py` (9 testů: příznak účtování, `view` nic nezapíše, `ucetni` a `schvalovatel` nemění role a matici, nabídka Role jen pro Správu, formulář role a záložka uživatele, schvalovatel potvrdí žádost `ucetni`); `investra_nav/tests`: nový `admin_user` (Správa), testy změn matice ho používají a ověřují, že schvalovatel matici nezmění |

**Ověření**

- `tools/run_tests.sh all` na dočasné `investra_ci_20261117_120628` (po testu smazána): 833 testů, 0 failed, 0 error. První běh měl 2 selhání
  v testech matice (měnil ji schvalovatel); opraveno v testech.
- Seed: `run_seed.sh investra_ci_zj02` (heslo jednorázové náhodné z proměnné; `.env` se nečetlo) naplnil fondy A–E, Services i role a uživatele;
  SELECT potvrdil skupiny: `admin` čtení + příprava + schvalování + správa + správce systému + účetnictví, `schvalovatel` a `ucetni` čtení + příprava + účetnictví
  (schvalovatel i schvalování), `view` jen čtení. Opakované spuštění `seed_users.py` (před fondy a po nich) uživatele aktualizovalo bez chyby; v logu heslo není. Databáze smazána.
- Neověřeno: větev čtení hesla z `.env` (v testu šlo heslo z prostředí); formuláře jen testy a Form, ne ručně v prohlížeči.

**Odchylky a upozornění**

- `seed_users.py` se musí spustit i **před** `seed.py`: ruční úpis v seedu už podle matice vyžaduje roli s činností (jinak seed padal na AccessError). `run_seed.sh` ho proto volá před fondy i po nich (po nich doplní přístup ke všem knihám).
- Správce účetnictví (`group_account_manager`) o `group_account_user` příznakem nepřijde (implikuje ho); jiná interpretace „uživatel není admin“ než správce systému nebo účetnictví.
- Uživatele upravuje jen ten, kdo má i přístup do Nastavení (`base.group_system`); úroveň Správa sama formulář uživatele neotevře.

**Zbývá pro ZJ-04:** nasazení do `investra` se zálohou, spuštění `run_seed.sh investra` (role a uživatelé; `seed.py` nad naplněnou databází nic nezmění), nový řádek matice „jeden člověk“ pro ruční úpis.

## Převzetí

Převzal Claude (Opus, hlavní relace) 17. 11. 2026; práce je už ve větvi `ukol/ZJ-zjednoduseni` (commit `fb15797`).

- **Zóna:** oranžová podle zadání; revize diffu provedena (`role.py`, `approval_matrix.py`, `ir.access.csv`, `role_views.xml`,
  `seed_users.py`, `run_seed.sh`, testy). Kód odpovídá rozhodnutím 2026-11-17, nálezy, které by bránily převzetí, žádné.
- **Doověřeno:** čtení hesla z `.env` v `run_seed.sh` (pod `set -euo pipefail`) dává neprázdnou hodnotu; hodnota se nevypisovala.
- **Opraveno při převzetí:** docstring `seed_users.py` uváděl spuštění jen po seed.py, ve skutečnosti běží před i po.
- **Potvrdil Martin 17. 11. 2026** (deník: „Ruční účtování: správci“): skupinu účtování si ponechá i správce účetnictví
  (`account.group_account_manager`), nejen správce systému. Dvojí spuštění `seed_users.py` v `run_seed.sh` je technická nutnost.
- **Pro ZJ-04 (nasazení do `investra`):**
  - `seed_users.py` nastaví uživateli `admin` jen roli Admin (`(6, …)`); jiné role, které mu tam případně přiřadilo ZJ-01, odebere.
  - Synchronizace rolí nově odebírá `account.group_account_user` uživatelům, jejichž role nemají příznak ručního účtování
    (kromě správce systému a správce účetnictví). Před nasazením vypsat uživatele `investra` s rolí a se skupinou účtování.
  - Formuláře ručně v prohlížeči zkontrolovat po nasazení (zatím jen testy a `Form`).
