# CP-2026-11-13 Graf kurzů tříd v detailu ocenění

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (JavaScript a šablona OWL; umístění grafu do detailu ocenění schváleno uživatelem) |
| Výchozí větev | `cp/vzhled` |
| Větev úkolu | `cp/vzhled` (`~/odoo-review`) |
| Zadal, dne | uživatel a Claude, 2026-11-13 |
| Navazuje na | rozhodnutí 2026-11-13 „Historie kurzů tříd pro grafy“, vzor `docs/vzhled/nahled-investra.html` |

**Cíl:** v hlavním detailu jednoho ocenění zobrazit kartu s čárovým grafem zveřejněných kurzů tříd daného fondu, přímo nad
stávajícími záložkami. Historie končí datem otevřeného ocenění. Třídy v různých měnách mají každá svou osu (levá a pravá).

**Rozsah souborů:**
- nové: `addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.js`, `class_price_chart.xml`, `class_price_chart.scss`
- `addons/custom/investra_nav/__manifest__.py` – jen tyto tři soubory do `assets` → `web.assets_backend` (verze, `depends` a `data` beze změny)
- `addons/custom/investra_nav/views/nav_views.xml` – jen zděděný pohled formuláře ocenění; karta před jeho existujícími záložkami

**Mimo rozsah:** Python, modely a pole (zdroj dat je hotový), `security/`, data, testy s očekávanými hodnotami, Odoo core,
jiné moduly, výpočty. Nic se nepřepočítává mezi měnami, žádný index ani výkonnost, chybějící body se nedopočítávají.

**Kritéria přijetí:**
- Na http://127.0.0.1:8072 je graf viditelný přímo v hlavním formuláři ocenění, nad záložkami, nikoli ve formuláři fondu.
- Graf ukáže zveřejněné kurzy otevřeného ocenění fondu a žádné body s datem pozdějším než datum tohoto ocenění.
- Přepínač období 3M / 6M / 1R / Max filtruje již načtenou historii relativně k datu otevřeného ocenění; výchozí je Max.
- Legenda „A · CZK“, „B · EUR“ (kód třídy · měna). Jedna měna = jedna osa; dvě měny = levá a pravá osa, popsané přímo kódem měny
  a obarvené stejně jako jejich čáry. Víc než dvě měny: graf se nekreslí, místo něj věta „Fond má kurzy ve více než dvou měnách,
  graf s vedlejší osou je neukáže.“
- Tooltip: datum (d. M. RRRR), třída, kurz v české notaci se všemi uloženými desetinnými místy a kódem měny.
- Neuložené ocenění: věta „Uložte ocenění.“ Bez odpovídající zveřejněné historie: „Zatím žádné zveřejněné ocenění.“
- Vybrané období bez bodů: věta „V tomto období nejsou zveřejněné kurzy.“
- Pod grafem drobným písmem: „Zveřejněné kurzy v měně třídy. Osy mají různé stupnice – sklon čar nesrovnávejte.“
- Jen barvy z palety (viz Schválený plán), žádné stíny, přechody ani průhlednost.

**Schválený plán** (Claude, 2026-11-13; uživatel schválil vlastní graf s vedlejší osou a jeho umístění v detailu ocenění):

1. **Kontext a data:** z `investra.valuation` načíst podle `record.resId` aktuální `fund_id` a `date`. Poté v modelu
   `investra.valuation.price.history` (jen pro čtení, jen zveřejněná ocenění) načíst `date`, `class_id`, `currency_id`, `price`
   pro tento fond s podmínkou `date <= valuation.date`. Hodnoty nepřepočítávat ani nezaokrouhlovat.
2. **Komponenta:** OWL `Component`, registrace `registry.category("view_widgets").add("investra_class_price_chart", { component })`,
   props `record` (standard view widgetu). U nového neuloženého ocenění nic nenačítat a ukázat „Uložte ocenění.“ Data načíst
   v `onWillStart` a znovu při aktualizaci props; zastaralá asynchronní odpověď nesmí přepsat výsledek novějšího požadavku.
3. **Graf:** `useChart` z `@web/core/utils/chart_hook` (načte `web.chartjs_lib`, vytvoří a ruší graf). Typ `line`.
   Osa X: datumy ocenění jako kategorie (sjednocení datumů všech tříd, vzestupně). Chybějící kurz třídy k datu = `null`,
   `spanGaps: false` (mezera, nic se nedokresluje). Měny seřadit podle prvního výskytu: první → osa `y` vlevo, druhá → `y1` vpravo
   (`position: "right"`, `grid.drawOnChartArea: false`). Každá datová řada má `yAxisID` podle své měny. Osy `beginAtZero: false`.
   Období 3M / 6M / 1R filtrují body od data ocenění minus zvolený počet kalendářních měsíců; Max ukazuje celou dostupnou historii.
4. **Barvy** (kontrast grafiky na bílé aspoň 3 : 1): řady na levé ose Petroleum `#112e3c`, Petroleum 2 `#596e78`, Graphite `#2c2927`;
   řady na pravé ose Lagoon `#0b5156`, Ember `#eb5b1f`, Graphite 2 `#6a6967`. Popisky a čárky osy v barvě její první řady.
   Mřížka Petroleum 4 `#e8ebec`. Písmo grafu Montserrat (`Chart.defaults.font.family` nenastavovat globálně, jen v `options`).
   Body `pointRadius: 3`, čára `borderWidth: 2`, bez výplně (`fill: false`).
5. **Formát:** datum přes `luxon` (`DateTime.fromISO(...).toFormat("d. M. yyyy")`), kurz `toLocaleString("cs-CZ", { maximumFractionDigits: 8 })` + kód měny.
6. **Šablona a styl:** karta s nadpisem a vysvětlením omezení historie, přepínače období, kontejner s pevnou výškou (360 px),
   `canvas` s `t-ref` ze `useChart`, poznámka pod grafem v Graphite 2.
7. **Pohled:** v `nav_views.xml` záznam `ir.ui.view` dědící `investra_nav.view_valuation_form`; vložit
   `<widget name="investra_class_price_chart"/>` před `//sheet/notebook`.
8. **Ověření Copilotem:** `tools/view_check`, prohlížeč na 8072 po upgradu modulu (asset a pohled vyžadují upgrade `investra_nav`
   v `investra_vzhled` – řekni uživateli, ať o něj požádá Clauda). Ověřit otevřené ocenění Lyry, Vegy a Orionu; testy Odoo spouští Claude.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.js` — widget načítá fond a datum aktuálního ocenění, následně pouze zveřejněnou historii do tohoto data; skládá řady, zachovává chybějící body jako `null`, filtruje období 3M/6M/1R/Max bez dalšího volání ORM a odmítá zastaralé odpovědi.
  - `addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.xml` — karta grafu v detailu ocenění, přepínače období a stavy nenačteného ocenění, načítání, prázdné historie a více než dvou měn.
  - `addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.scss` — vzhled nadpisu a přepínačů, výška grafu a drobná poznámka v Graphite 2.
  - `addons/custom/investra_nav/__manifest__.py` — registrace tří schválených assetů v `web.assets_backend`.
  - `addons/custom/investra_nav/views/nav_views.xml` — zděděný pohled `investra.valuation`; graf je před existujícími záložkami, nikoli ve formuláři fondu.
- **Ověřeno (příkaz a výsledek):**
  - `python3 tools/view_check/check_views.py` — 15 souborů, 0 chyb.
  - `xmllint --noout addons/custom/investra_nav/views/nav_views.xml addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.xml` — bez chyb XML.
  - `git diff --check` — bez chyb.
  - API `useChart` a předávání `record` standardnímu view widgetu ověřeny proti zdroji Odoo 20.
- **Neověřeno:**
  - Prohlížeč na Odoo 8072 — nové assety a pohled vyžadují upgrade `investra_nav`.
  - Samostatná kontrola syntaxe JS pomocí Node — `node` v prostředí není dostupný.
  - Odoo testy a upgrade — mimo rozsah Copilota, provede Claude.
- **Otevřené otázky a návrhy mimo rozsah:**
  - Po upgradu Claudem ověřit kartu v detailu ocenění Lyry a Vegy (leden–září) a Orionu (leden–červen), včetně omezení podle data, legendy, os, tooltipu, prázdného stavu a případného stavu více než dvou měn.
  - Předpoklad dat widgetu: `class_id` a `currency_id` se vrací jako standardní relace Many2one a jejich zobrazovaný název je kód třídy / měny.
  - Graf nic nepřepočítává; numerické kurzy předává Chart.js přímo a formátuje je jen pro zobrazení.

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
