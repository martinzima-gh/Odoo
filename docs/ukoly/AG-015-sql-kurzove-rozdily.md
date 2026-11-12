# AG-015 Ukázkové SQL: realizovaný a nerealizovaný kurzový rozdíl

Rozhodnutí 2026-11-12 „Realizovaný kurzový rozdíl“ oddělilo v ocenění realizovaný kurzový rozdíl prodaných
a splacených jednotek od nerealizovaného. Účty jsou stejné (role `gain_fx`/`loss_fx`), liší se jen druh pohybu.
Uživatel chce rozpad vidět v DBeaveru po nástrojích.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `docs/sql/*.sql`, jen `SELECT`) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-015-sql-kurzove-rozdily` (připravil Claude v `~/odoo-review`) |
| Řešitel | GitHub Copilot, režim Agent v okně na `~/odoo-review` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-12 |
| Navazuje na | deník 2026-11-12 „Realizovaný kurzový rozdíl“; zvyklost „Ukázkové SQL“ (soubory 01–21) |

**Cíl:** nový soubor `docs/sql/22-kurzove-rozdily.sql` se 3–5 dotazy, každý s krátkým českým komentářem:

1. **Rozpad po nástrojích:** kniha, nástroj, měna nástroje, realizovaný a nerealizovaný kurzový rozdíl
   ve funkční měně a jejich součet. Zdroj: zaúčtované řádky (`account_move_line.parent_state = 'posted'`)
   na účtech rolí `gain_fx` a `loss_fx`, rozlišené sloupcem `investra_movement_type`:
   `fx_realised` = realizovaný, `fx_revaluation` = nerealizovaný. Výnos má na těchto účtech záporný `balance`;
   ve výstupu ho ukaž jako kladný zisk (`-sum(balance)`) a v komentáři to napiš.
2. **Totéž po měsících** (podle `account_move_line.date`) pro jednu knihu.
3. **Kontrolní součet:** po knize a roli součet řádků obou druhů pohybu proti celkovému zůstatku účtů rolí
   `gain_fx`/`loss_fx`. Rozdíl = kurzové rozdíly jiného druhu pohybu (např. ruční doklady); vypsat i ten.
4. (volitelně) Řádky s druhem `fx_realised` jednotlivě: datum, doklad, nástroj, popis řádku, částka.

**Jak najít účty role (důležité):**
- Mapování je `investra_role_account` (`company_id`, `role_id`, `account_id` = hlavní účet) a další účty role
  v tabulce `investra_role_account_extra_rel` (`mapping_id`, `account_id`). Zůstatek role = hlavní **i** další účty,
  takže spoj obojí (např. `union` hlavního a dalších účtů v `with`). Kód role je `investra_account_role.code`.
- Nástroj je v `account_move_line.investra_instrument_id` → `investra_instrument` (`name`, `currency_id`).
- Stejný druh pohybu `fx_revaluation` mají i řádky přecenění bank a nevypořádaných obchodů (bez nástroje).
  V dotazu 1 je nech jako řádek „bez nástroje“ (`left join`), neztrácej je.
- Styl a hlavičku převezmi z `docs/sql/17-urok-rh-realizace.sql` (dotaz 2 tam ukazuje spojení rolí, ale jen
  přes hlavní účet; tady použij i další účty). Kniha jako parametr: dosazené id společnosti v `where`
  s komentářem „dosaďte id společnosti“; jako ukázku použij 244.

**Postup:**
1. Pole ověř v modelech: `addons/custom/investra_posting/models/event.py` (druhy pohybu),
   `addons/custom/investra_entity/models/account_role.py` (mapování rolí). Kód neměň.
2. Dotazy spouštěj jen čtením nad testovací databází:
   `docker exec -i odoo-investra-db-1 psql -U odoo -d investra_test -c "begin read only;" -c "SELECT …" -c "rollback;"`
   (když se uživatel `odoo` nepřipojí, zastav se a napiš to; heslo nehledej ani nevypisuj).
3. Očekávaný stav dat: `fx_revaluation` mají knihy 244 a 410 (po 4 řádcích, 1 nástroj),
   `fx_realised` v `investra_test` **není** (chybí prodej i splátka v cizí měně). Dotazy na realizovaný kurz
   proto vrátí nuly nebo 0 řádků. To je v pořádku, jen to uveď ve Výsledku. Data nezakládej.

**Rozsah souborů:** jen nový `docs/sql/22-kurzove-rozdily.sql` a sekce Výsledek v tomto souboru.

**Mimo rozsah:** jakékoli úpravy kódu a existujících souborů v `docs/sql/`, zakázané soubory podle
`.agents/rules/10-zony.md`. V SQL ani v databázi nic jiného než `SELECT` (případně `WITH … SELECT`);
žádné `INSERT`, `UPDATE`, `DELETE`, `CREATE`, transakce se zápisem. Do souboru nekopíruj řádková data, jen dotazy
a obecné komentáře. Obchodní význam, který není v kódu nebo v tomto zadání, nevymýšlej; nejasnosti napiš do Otevřených otázek.

**Kritéria přijetí:**
- Každý dotaz proběhne nad `investra_test` bez chyby; ve Výsledku uveď počet vrácených řádků u každého.
- Dotaz 1 pro knihu 244 ukáže nerealizovaný kurzový rozdíl nástroje a realizovaný 0 (nebo prázdný).
- Kontrolní součet (dotaz 3) pro knihy 244 a 410 sedí na celkový zůstatek rolí; případný rozdíl je vysvětlený.
- Zůstatky rolí počítají hlavní i další účty.
- Soubor obsahuje jen `SELECT`, komentáře česky a stručně.

**Převzetí (Claude):** kromě běžné revize ověří dotazy 1 a 3 na kopii `investra_test` s prodejem v cizí měně
(dočasná databáze `investra_ci_*`, po ověření smazat), protože realizovaný kurz testovací data nemají.

## Výsledek

- **Změněné soubory:** `docs/sql/22-kurzove-rozdily.sql`.
- **Ověřeno (příkaz a výsledek):** Každý dotaz byl samostatně spuštěn přes `docker exec -i odoo-investra-db-1 psql -U odoo -d investra_test` v transakci `BEGIN TRANSACTION READ ONLY` a následně `ROLLBACK`; všechny proběhly bez chyby.
  - Dotaz 1 vrátil 2 řádky; v knize 244 je realizovaný kurzový rozdíl 0 a nerealizovaný nenulový.
  - Dotaz 2 vrátil 2 řádky.
  - Dotaz 3 vrátil 4 řádky; pro knihy 244 a 410 se součet řádků obou kurzových druhů shoduje s celkovým zůstatkem rolí, rozdíl je 0.
  - Dotazy započítávají hlavní i další účty rolí; soubor obsahuje pouze `WITH ... SELECT`.
- **Neověřeno:** Nenulový realizovaný kurzový rozdíl; v `investra_test` nejsou odpovídající řádky. Ověření s prodejem v cizí měně je součástí převzetí Claudem podle zadání.
- **Otevřené otázky a návrhy mimo rozsah:** Žádné.

## Převzetí

- **Datum:** 2026-11-12, převzal Claude.
- **Revize:** jen `docs/sql/22-kurzove-rozdily.sql` a Výsledek zadání; v souboru jen `WITH … SELECT`, role s hlavními
  i dalšími účty, znaménka podle zadání. Nálezy žádné.
- **Kontrola dotazů:** dočasná kopie `investra_test` (`investra_ci_ag015`), na ní přes ORM zaúčtován zkušební doklad
  s druhem `fx_realised` (zisk 1 000, ztráta 300 u akcie v EUR, kniha 244). Dotaz 1 ukázal realizovaný 700 u nástroje,
  dotaz 2 v měsíci 2027-03, dotaz 3 rozdíl 0 u obou rolí. Kopie smazána.
- **Testy Odoo:** nespouštěny, úkol nemění kód.
- **Sloučení:** 2026-11-12 do `feature/nav-prototyp`.
