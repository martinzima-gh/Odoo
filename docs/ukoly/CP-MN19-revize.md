# CP-MN19 Nezávislá revize manuálu kap. 8 (úpis, odkup, převzetí fondu)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | revize (jen čtení) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením; poslední commit s kap. 8 je a38c7b2) |
| Větev úkolu | žádná; Copilot nic neupravuje, jen zapíše nálezy do tohoto souboru |
| Model | GitHub Copilot, režim Agent, nejvyšší dostupný model (revize věcné správnosti; psal ji Claude, proto jiný agent) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Navazuje na | MN-19 (první verzi Copilota Claude vrátil, kap. 8 přepsal) |

**Cíl:** nezávisle ověřit, že každé tvrzení v `docs/manual/08-prvni-upis-a-prevzeti-fondu.md` odpovídá kódu; chybějící a nadbytečné tvrzení jsou nález.

**Co zkontrolovat** (kód: `investra_nav/models/movement.py`, `valuation.py` funkce `_run_movement_checks`, `valuation_lock.py`, `investra_nav/views/nav_views.xml` pohled pohybu, `investra_fund/models/approval_matrix.py`, `investra_fund/models/fund.py`):
1. Tabulka polí: názvy, povinnost, výchozí hodnoty, které pole jsou jen pro čtení a kdy (`readonly="state != 'draft'"`), předvyplnění poplatku a příjemce.
2. Vzorce a kontroly: úpis i odkup, zbytek 0,01, kontrola kusů (jen úpis), kontrola ceny a Důvod odlišné ceny včetně případu bez zveřejněného ocenění, hlášky doslovně.
3. Zaúčtování: kdy jde pohyb přes matici (`subscription_manual`, jen ruční zdroj), co doklad obsahuje (`_book_lines`, `_fee_line`), znaménka a role.
4. Storno a oprava: `action_reverse`, `action_correct`, `_do_reverse`; matice platí i pro zdroj IS; co nese kopie při opravě; zámek ocenění.
5. Vazba na ocenění: které pohyby vstupují (období, stav), kontroly `movements_posted`, `movement_fee_rate`, `movement_price`; hranice období (`date >` začátek).
6. Příklad „první úpis“: přepočítej čísla (kusy, kapitál, doklad) a ověř, že by kontroly při zaúčtování prošly (kusy podle zaokrouhlení třídy, cena bez zveřejněného ocenění).
7. Oddíl „Převzetí fondu“: tvrzení o stavu funkce (v kódu není), o účtování úpisu (banka proti kapitálu) a odkazy na plán a otevřené body; není-li něco opřeno, je to nález.
8. Jazyk a srozumitelnost pro účetního: jen věcné chyby a nejasnosti, ne styl.

**Mimo rozsah:** úpravy souborů mimo tento záznam; spouštění testů Odoo (čistý Python smíš); návrh nové funkce převzetí.

**Kritéria přijetí:** do Výsledku u každého z 8 bodů „v pořádku“ nebo nález (soubor, řádek, scénář, závažnost); seznam „neověřeno“.

## Výsledek

Doplní Copilot.

## Převzetí

Doplní Claude.
