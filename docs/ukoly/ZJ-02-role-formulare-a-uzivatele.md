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

## Převzetí
