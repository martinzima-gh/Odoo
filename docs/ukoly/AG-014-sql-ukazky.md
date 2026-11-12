# AG-014 Ukázkové SQL pro protistrany, knihy, alokace a DPH

Složka `docs/sql/` slouží uživateli k poznávání datového modelu v DBeaveru. Čtyři moduly zatím žádné
ukázky nemají. Úkol je doplní.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `docs/sql/*.sql`, jen `SELECT`) |
| Výchozí větev | `feature/nav-prototyp` (commit a188eea) |
| Větev úkolu | `ag/AG-014-sql-ukazky` (připravil Claude v `~/odoo-review`) |
| Řešitel | GitHub Copilot, režim Agent v okně na `~/odoo-review` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-12 |
| Navazuje na | zvyklost „Ukázkové SQL“ (soubory 01–16) |

**Cíl:** čtyři nové soubory s 3–6 dotazy, každý s krátkým českým komentářem, co ukazuje:

| Soubor | Modul | Co ukázat |
|---|---|---|
| `docs/sql/18-protistrany.sql` | `investra_counterparty` | sektory ESA, profily protistran a jejich vazba na partnera, protistrana u nástroje, rozšíření klasifikace portfolia |
| `docs/sql/19-knihy-a-role.sql` | `investra_entity` | knihy (`investra.entity`) a jejich společnost, role účtů a přiřazené účty (`investra.account.role`, `investra.role.account`), rozšíření deníku; **bez** `record_guard` |
| `docs/sql/20-alokace.sql` | `investra_allocation` | schémata alokace a jejich řádky, kontrola součtu podílů na schéma |
| `docs/sql/21-dph-identifikovana-osoba.sql` | `investra_vat_identified` | pole přidaná ke společnosti, daně a štítky přiznání, které modul zakládá |

**Postup:**
1. Z modelů (`addons/custom/<modul>/models/*.py`) zjisti pole; názvy tabulek = `_name` s tečkami nahrazenými `_`.
2. Dotazy ověř jen čtením nad testovací databází:
   `docker exec -i odoo-investra-db-1 psql -U odoo -d investra_test -c "SELECT …"`
   (když se uživatel `odoo` nepřipojí, zastav se a napiš to; heslo nehledej ani nevypisuj).
3. Styl převezmi z `docs/sql/10-ceny.sql` a `15-prevody-bank.sql`: hlavička (modul, „Jen čtení, spouštět po jednom“,
   na které databázi ověřeno), číslované dotazy, JSON názvy přes `->>`.

**Rozsah souborů:** jen čtyři nové soubory výše a sekce Výsledek v tomto souboru.

**Mimo rozsah:** `investra_nav` a splátky (souběžně na nich pracuje Claude), jakékoli úpravy kódu,
existující soubory v `docs/sql/`, zakázané soubory podle `.agents/rules/10-zony.md`.
V SQL ani v databázi nic jiného než `SELECT` (žádné `INSERT`, `UPDATE`, `DELETE`, `CREATE`, transakce se zápisem).
Do souborů nekopíruj řádková data (jména partnerů, IČO, účty); jen dotazy a obecné komentáře.

**Kritéria přijetí:**
- Každý dotaz v souborech proběhne nad `investra_test` bez chyby (ve Výsledku uveď počet vrácených řádků u každého).
- Soubory obsahují jen `SELECT` (případně `WITH … SELECT`).
- Komentáře česky, stručně, bez obchodního významu, který není v kódu (nejasnosti napiš do Otevřených otázek).

## Výsledek

- **Změněné soubory:** `docs/sql/18-protistrany.sql`, `docs/sql/19-knihy-a-role.sql`, `docs/sql/20-alokace.sql`, `docs/sql/21-dph-identifikovana-osoba.sql`.
- **Ověřeno (příkaz a výsledek):** Dotazy ze souborů 18–20 byly samostatně spuštěny jako poddotazy počítající řádky přes `docker exec -i odoo-investra-db-1 psql -U odoo -d investra_test`. Tři dotazy z `21-dph-identifikovana-osoba.sql` byly stejným read-only způsobem ověřeny nad `investra_dev`; všechny skončily bez chyby.
  - `18-protistrany.sql`: dotazy 1–4 vrátily 33, 1, 1 a 7 řádků.
  - `19-knihy-a-role.sql`: dotazy 1–4 vrátily 5, 225, 11 a 7 řádků.
  - `20-alokace.sql`: dotazy 1–3 vrátily 0, 0 a 0 řádků.
  - `21-dph-identifikovana-osoba.sql` (`investra_dev`): dotazy 1–3 vrátily 1, 4 a 12 řádků.
  - Všechny dotazy v souborech jsou `SELECT`; názvy JSON polí čteny přes `->>`.
- **Neověřeno:** Dotazy ze souborů 18–20 nad `investra_dev`; dotazy z `21-dph-identifikovana-osoba.sql` nad `investra_test`.
- **Otevřené otázky a návrhy mimo rozsah:** Zadání zmiňuje pole přidaná modulem k `res.company`, ale `investra_vat_identified` žádná pole tohoto modelu nedefinuje; přidává metody pro založení daní a fiskálních pozic. Ukázka proto zobrazuje společnosti a související záznamy. Potvrdit, zda se očekával jiný modul či konkrétní pole.

## Převzetí

- **Datum:** 2026-11-12, převzal Claude.
- **Revize:** jen 4 nové soubory a zadání, mimo rozsah nic; v souborech jen `SELECT`.
- **Kontrola dotazů:** všechny soubory spuštěny v transakci jen pro čtení. 18–20 nad `investra_test` (počty sedí s Výsledkem),
  21 nad `investra_dev` (1, 4 a 12 řádků). Alokace v `investra_test` nemají data, výstup na záznamech neověřen.
- **Nález (opraven Copilotem):** popis daně je uložen jako HTML (`<div>…</div>`), původní vzor `LIKE '%… osoba'` nenašel žádnou daň;
  opraveno na `'%DPH, identifikovaná osoba%'`. Nepřesnost v zadání (pole u `res.company`) šla za Claudem.
- **Testy Odoo:** nespouštěny, úkol nemění kód.
- **Sloučení:** 2026-11-12 do `feature/nav-prototyp`; soubory přečíslovány na 18–21, protože číslo 17 mezitím obsadil `17-urok-rh-realizace.sql`.
