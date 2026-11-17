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

## Převzetí
