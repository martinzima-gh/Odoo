# CP-2026-11-13 – vzhled obrazovek (souhrn pro převzetí)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená; návrhy nových polí jsou pro Clauda |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `cp/vzhled` |
| Zadal, dne | uživatel, 2026-11-13 |
| Pravidla | `docs/vzhled/zasady-obrazovek.md` |

**Cíl:** Promítnout uživatelem schválené návrhy do rozvržení XML/SCSS a připravit všechny obrazovky k jednomu převzetí Claudem. Návrhy používají pouze smyšlená data.

## Schválené návrhy

- Detaily: fond, nástroj, obchod, úpis/odkup a splátka.
- Seznamy: fondy, nástroje, obchody, úpisy/odkupy, splátky, ocenění, obchodní modely, zařazení nástrojů, typy nástrojů, ceny, schvalovací matice, žádosti ke schválení, úkony bez druhé osoby a výjimky z uzamčení.
- HTML náhledy jsou v `docs/vzhled/navrh-*.html`. Detail fondu má také původní záznam `docs/ukoly/CP-2026-11-13-fond.md`.
- Přehled fondů: jeden fond na kartu; FK, výsledek za období, datum a stav posledního i dalšího ocenění, vykázání ČNB a upozornění kontrol. Schválený návrh je v `docs/vzhled/navrh-prehledu-fondu.html`. Kurzy tříd nejsou na kartě, zůstávají v detailu ocenění.

## Provedení v této větvi

- XML: souhrnné řádky údajů a pásy existujících čísel v detailech; beze změny podmínek polí, stavů, akcí a jejich chování.
- XML: pořadí sloupců a výchozí řazení podle schválených návrhů; počet osob ve schvalovací matici zůstává dostupný jako volitelný, skrytý sloupec.
- SCSS: souhrnné řádky a pásy čísel; široké seznamy umožňují vodorovné posouvání a dlouhý text se nezkracuje. Dekorace růstu/poklesu používají Lagoon/Ember.
- V seznamu pohybů se existující kladná částka barví podle typu úpis/odkup. Textové znaménko není implementováno, protože zdrojové pole je podle modelu vždy kladné.
- Kód nástroje a ISIN nebyly přidány do seznamu cen: nyní nejsou poli modelu ceny.
- Přehled fondů je zatím pouze schválený vizuální návrh; změny dashboardových dat ani logiky Copilot neimplementoval.

**Mimo rozsah:** Python, JavaScript/OWL, výpočty, účetní logika, oprávnění, data, stavy a akce. Grafy se nemění.

## Požadavky k rozhodnutí Clauda

1. **Kód a ISIN v cenách:** posoudit read-only zobrazovací pole převzatá z nástroje pro pořadí datum, kód, ISIN, název. Zachovat stávající cenu jako záznam ceny; vyjasnit dopad, pokud by se identifikátory nástroje později změnily.
2. **Znaménko změny kapitálu:** navrhnout zobrazovací hodnotu s `+` pro úpis a `−` pro odkup a navázané Lagoon/Ember zabarvení. Pole `capital_amount` je podle `addons/custom/investra_nav/models/movement.py` vždy kladné; zobrazovací pole nesmí měnit účetní hodnoty ani výpočty ocenění.
3. **Přehled fondů – data a stavy:** implementaci nejprve navrhnout a potvrdit vůči existujícím stavům a účetním zdrojům. V kartě zobrazit poslední a další ocenění včetně data a stavu, výkaz/období ČNB se stavem a termínem, FK a samostatný „Výsledek za období“. Nepřidávat souhrny napříč fondy ani kurzy tříd.
   - V `investra_dashboard/models/dashboard.py` je `dashboard_next_valuation` pouze datum kalendářní položky bez zveřejněného ocenění; průběžný stav dalšího ocenění dashboard neurčuje. Claude musí odvodit a zdokumentovat mapování stavů z existujících dat; chybějící stav nesmí odhadovat.
   - `dashboard_next_deadline` nyní vybírá pouze termíny ČNB se stavem `open`; test `test_submitted_deadline_is_ignored` potvrzuje, že podané výkazy se nezobrazují. Návrh potřebuje zobrazit jak „Otevřeno“, tak „Podáno“ a rozlišit otevřený termín po lhůtě podle ověřené existující logiky. Model neobsahuje datum podání, proto ho nevymýšlet.
   - Na dashboardu nyní není „Výsledek za období“. Detail ocenění ho aktuálně zobrazuje jako součet `shared_result` („Změna společná“) a `delta` („Specifická změna“) přes řádky tříd; součet je v `investra_nav/static/src/valuation_summary/valuation_summary.js`. U prvního ocenění bez předchozího období zobrazuje pomlčku, ne nulu. Jde o existující zdroj pro konzistenci UI, ne automatické potvrzení úplné účetní definice výsledku. Claude ověří, zda má dashboard převzít stejný výsledek a zda nezahrnuje další složky; výpočet nesmí být v XML/OWL šabloně ani zaměněn se změnou FK. Při nejasnosti účetní definici vrátí uživateli k rozhodnutí.
   - Všechny částky a stavy zobrazovat pro příslušný fond a jeho měnu, bez převodu či agregace mezi fondy. Respektovat přístupová práva a oddělení společností. Rozšíření modelu a výpočtové zdroje patří Claudovi, mimo XML/SCSS-only rozsah Copilota.

## Ověření

- `python3 tools/view_check/check_views.py` nad pěti změněnými XML soubory: 5 souborů, 0 chyb.
- Inventář polí formulářů porovnán s `HEAD`: fond 41, nástroj 43, obchod 26, pohyb 32 a splátka 23 polí zachováno.
- `git diff --check` — bez chyb.
- HTML návrhy s upraveným řazením byly znovu otevřeny v prohlížeči.
- `docs/vzhled/navrh-prehledu-fondu.html` se otevřel v prohlížeči; kontrola potvrdila čtyři samostatné karty, schválené popisky a český formát dat.
- Sass CLI není instalováno, proto SCSS kompilace neproběhla. Změny nebyly načteny v běžícím Odoo; upgrade modulu ani restart instance se bez souhlasu neprovádí.
- Databázové testy nebyly spuštěny; nejprve je nutné ověřit izolovanou testovací databázi.

## Převzetí

- Čeká na společnou kontrolu a převzetí Claudem jako jeden celek. Přehled fondů byl schválen jako vizuální návrh; jeho datová a stavová logika zůstává otevřeným bodem pro Clauda.
