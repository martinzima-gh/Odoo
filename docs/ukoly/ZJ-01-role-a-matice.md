# ZJ-01 Role a schvalovací matice bez fondů

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (schvalovací matice, oprávnění, migrace) – plán níže schvaluje Martin |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Větev úkolu | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace) podle zadání Martina, 17. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-17 „Role a schvalovací matice zjednodušeny“ (`docs/rozhodnuti.md`) |
| Model | Opus |

**Cíl:** role si zakládá oprávněný uživatel sám a skládá je z činností; uživatel má rolí více. Matice platí pro celou
aplikaci (bez obhospodařovatele a zpřísnění fondu) a určuje jen počet osob (1 / čtyři oči / kroky).

**Postup:**
1. Model `investra.role` (v `investra_fund` nebo `investra_entity`, podle závislostí): název, **úroveň přístupu**
   (Čtení / Zpracování / Správa), řádky činností (`ACTIVITIES`) s příznaky **Provádí** a **Schvaluje**, uživatelé (M2M),
   aktivní, sledování změn. Zakládá a mění jen úroveň Správa (nebo `base.group_system`).
2. **Skupiny Odoo se odvozují z rolí** (uživatel je ručně nenastavuje): Čtení → nová `investra_entity.group_investra_read`
   (implikuje `account.group_account_readonly`); Zpracování → `group_valuation_preparer` (ověřit, zda pro „účtuje i ručně
   v hlavní knize“ má implikovat `account.group_account_user`); Správa → nová `group_investra_admin`; kdo má v některé roli
   „Schvaluje“, dostane `group_valuation_approver`. Synchronizace při změně role i přiřazení uživatele. Tím zůstanou
   stávající odkazy na skupiny ve formulářích a `ir.access.csv` (105 míst) beze změny – ověřit grepem, že žádný nepředpokládá
   pořadí rolí.
3. Přepis `investra_fund/models/approval_matrix.py`: místo `ROLES`/`ROLE_RANK` kontrola „uživatel má roli s činností
   a příznakem Provádí, resp. Schvaluje“. Krok matice má volitelně **roli** (`investra.role`); prázdná = kdokoli se
   Schvaluje u činnosti. Odstranit `manager_id`, `fund_id`, `performer_role`, `performer_user_ids`, `user_ids` u kroků,
   `Rule.covers` a kontrolu zpřísnění. Unikátnost `(activity, valid_from)`. Pravidlo „každý krok jiný člověk“ a `_gate`,
   `_approve_step`, žádosti, zápis úkonů jednoho člověka zůstávají.
4. Migrace (`investra_fund`, nová verze): řádky obhospodařovatele převést na globální (konflikt data = ponechat novější id
   a ohlásit), zpřísnění fondu nejsou (ověřit SELECTem, jinak zastavit). Pole `role` v řádcích žádostí převést na text.
   Odstranit `group_valuation_preparer/approver` z uživatelů nesmí – vzniknou ze synchronizace rolí.
5. `BUILTIN`: výchozí počty osob beze změny (bez rolí).
6. Testy: role s činností provádí/neprovádí, schvalovatel ≠ žadatel, kroky s rolí, odvození skupin (přidání a odebrání role),
   migrace řádku obhospodařovatele. Upravit stávající testy matice, které používají `performer_role`.

**Mimo rozsah:** formuláře a nabídky (ZJ-02), uživatelé a seed (ZJ-02), manuál (ZJ-04), nasazení do `investra`.

**Kritéria přijetí:** `tools/run_tests.sh all` zelené; žádný odkaz na `ROLE_RANK`, `manager_id` matice ani `fund_id` matice;
sekce Výsledek s přehledem změněných souborů a tím, co zbývá pro ZJ-02.

**Schválený plán:** body 1–6 výše; schválení Martin v promptu („Plán v úkolu ZJ-01 schvaluji (červená zóna, Martin).“).

## Výsledek

Provedl Claude (Opus) 17. 11. 2026 ve větvi `ukol/ZJ-zjednoduseni`; do `investra` se nenasazovalo (ZJ-04).

**Co se změnilo**

| Soubor | Změna |
|---|---|
| `investra_entity/security/groups.xml` (verze 0.13.0) | nové skupiny `group_investra_read` (Čtení) a `group_investra_admin` (Správa, implikuje přípravu); příprava i schvalování implikují Čtení |
| `investra_fund/models/role.py` | `investra.role` (název, úroveň přístupu, činnosti s Provádí / Schvaluje, uživatelé, aktivní, historie), `investra.role.line`, pole `res.users.investra_role_ids`; zakládá a mění jen Správa nebo `base.group_system`; synchronizace skupin při změně role, činnosti, archivaci i přiřazení z uživatele (mění jen 4 skupiny Investry) |
| `investra_fund/models/approval_matrix.py` | bez `ROLES`, `ROLE_RANK`, `manager_id`, `fund_id`, `company_id`, `performer_role`, `performer_user_ids`, `user_ids` kroků, `Rule.covers`/`key`; kontrola `user_can`/`check_user` podle rolí; krok má volitelně `role_id`; unikátnost `(activity, valid_from)`; `_rule(activity, day)`, `_gate(...)` a `_approve_step(...)` bez parametru fondů; `BUILTIN` = počet schvalovatelů (počty beze změny); řádek žádosti: `role_id` + `role` jako text |
| `investra_fund` data, formuláře, `fund.py`, `ir.access.csv` | výchozí řádky bez rolí; z formulářů matice a fondu odstraněna zrušená pole a záložka „Zpřísnění matice“ (jen nutné minimum, plné formuláře ZJ-02); práva k rolím |
| `investra_nav` (verze 0.32.0): `valuation.py` (i kontrola „změna matice“ bez filtru fondu), `movement.py`, `trade_reverse.py`, `instrument_accrual.py`, `lock_exception.py`, `nav_views.xml` | volání matice bez fondů; krok schválení ocenění má `role_id`, `min_role` je text, `allowed_user_ids` zrušeno; krok „bez druhé osoby“ vyžaduje Provádí, ostatní Schvaluje (případně roli kroku) |
| `investra_instruments` (cena, ruční kategorie), `investra_derivative`, `investra_dashboard` | volání matice bez fondů; „můj krok“ v dashboardu podle rolí |
| `investra_fund/zj01_migration.py`, `migrations/20.0.0.10.0`, `investra_nav/migrations/20.0.0.32.0` | pre-migrace: řádek fondu převod zastaví; řádky obhospodařovatele → globální, kolize (činnost, den) → ponechán novější id, odkazy převedeny, ohlášeno; kódy rolí v žádostech a krocích ocenění → text |
| `investra_nav/migrations/20.0.0.6.0` | historický převod kroků fondu jen ohlásí (všechny databáze jsou za touto verzí) |
| `tools/demo_data/seed.py` | jen odstraněna zrušená pole matice (seed jako celek upraví ZJ-02) |
| testy | nové `investra_fund/tests/test_role.py` (skupiny z rolí, Provádí/Schvaluje, schvalovatel ≠ žadatel, kroky s rolí, text role v žádosti, migrace); `investra_fund/tests/common.py` – testové role napodobující skupiny před ZJ-01, použité v testech nav, instrumentů a dashboardu; upraveny testy matice (místo zpřísnění fondu a jmenovitých uživatelů krok s rolí) |

**Ověření**

- Testy: `tools/run_tests.sh all` na dočasné `investra_ci_20261117_113150` (po testu smazána): 824 testů, 0 failed, 0 error.
  První běh odhalil zbylý filtr podle fondu v kontrole „změna matice“ (`valuation._matrix_changes`, opraveno) a chybějící
  testovou roli v `investra_rates/tests/test_protection.py` (při instalaci s `investra_nav`, doplněno podmíněně).
- Zkouška migrace na dočasné kopii `investra` (`investra_ci_mig_*`, pg_dump → restore → `-u investra_entity,investra_fund`, pak smazána): rc 0;
  10 řádků obhospodařovatele (id 11–20, od 16. 11.) převedeno na globální, kolize data žádná; unikátnost `UNIQUE (activity, valid_from)`;
  35 kroků schválení ocenění má text „Příprava ocenění“; skupiny uživatelů beze změny. Odoo 20 zrušené sloupce matice samo odstraní,
  proto převod běží v pre-migraci.
- SELECTem v `investra` před změnou: řádky zpřísnění fondu 0, jmenovití uživatelé 0, čekající žádosti 0.
- Grep: `ROLE_RANK`, `manager_id` ani `fund_id` matice v kódu nezůstaly (jen v migraci a jejím testu); 94 odkazů na skupiny
  přípravy a schvalování kontroluje skupinu přímo, pořadí rolí předpokládal jen odstraněný `ROLE_RANK`.

**Odchylky a upozornění**

- `account.group_account_user` (ruční účtování v hlavní knize) se z rolí **neodvozuje**. Ověřeno v Odoo 20: skupina přípravy
  implikuje jen `group_account_readonly`, ruční doklad v hlavní knize vyžaduje `group_account_user`. Automatické přidělení
  by dalo všem se Zpracováním plné účtování mimo náhled a matici, proto je to rozhodnutí pro Martina (návrh: ZJ-02 jako
  samostatný příznak role „Účtuje ručně v hlavní knize“, nebo ručně jen uživateli `ucetni`).
- Po nasazení (ZJ-04) nikdo nemá roli, takže úkony podle matice nikdo neprovede, dokud se nepřiřadí role. Skupiny uživatelů
  zůstávají, ale samy úkon matice nepovolí.
- Sloučení řádků obhospodařovatele mění chování v `investra`: např. `subscription_manual` měl u obhospodařovatele od 16. 11.
  „jeden člověk“, globální řádek od 17. 11. „čtyři oči“; po sloučení platí novější globální řádek (čtyři oči).
- Matici dál mění skupina schvalování (beze změny); jestli ji má měnit jen Správa, rozhodne Martin v ZJ-02.

**Zbývá pro ZJ-02:** formuláře a nabídka rolí (řádky činností s Provádí / Schvaluje), pole Role u kroku matice, záložka
rolí u uživatele (`investra_role_ids`), ukázkové role a uživatelé `admin` / `ucetni` / `schvalovatel` / `view`, úprava seedu
(řádky matice „jeden člověk“ už bez obhospodařovatele), rozhodnutí o `group_account_user` a o tom, kdo mění matici.

## Převzetí
