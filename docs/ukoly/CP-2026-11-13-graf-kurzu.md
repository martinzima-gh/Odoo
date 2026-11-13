# CP-2026-11-13 Graf kurzů tříd s vedlejší osou (formulář fondu)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (JavaScript a šablona OWL; plán od Clauda, výjimka pro Copilota schválená uživatelem 2026-11-13) |
| Výchozí větev | `cp/vzhled` |
| Větev úkolu | `cp/vzhled` (`~/odoo-review`) |
| Zadal, dne | uživatel a Claude, 2026-11-13 |
| Navazuje na | rozhodnutí 2026-11-13 „Historie kurzů tříd pro grafy“, vzor `docs/vzhled/nahled-investra.html` |

**Cíl:** ve formuláři fondu záložka **Kurzy tříd** s čárovým grafem zveřejněných kurzů všech tříd fondu v čase.
Třídy v různých měnách mají každá svou osu (levá a pravá), aby byly vidět obě najednou.

**Rozsah souborů:**
- nové: `addons/custom/investra_nav/static/src/class_price_chart/class_price_chart.js`, `class_price_chart.xml`, `class_price_chart.scss`
- `addons/custom/investra_nav/__manifest__.py` – jen tyto tři soubory do `assets` → `web.assets_backend` (verze, `depends` a `data` beze změny)
- `addons/custom/investra_nav/views/nav_views.xml` – jen nový zděděný pohled formuláře fondu (`investra_fund.view_fund_form`) se záložkou

**Mimo rozsah:** Python, modely a pole (zdroj dat je hotový), `security/`, data, testy s očekávanými hodnotami, Odoo core,
jiné moduly, výpočty. Nic se nepřepočítává mezi měnami, žádný index ani výkonnost, chybějící body se nedopočítávají.

**Kritéria přijetí:**
- Na http://127.0.0.1:8072, fond „Fond Vzhled Orion / Lyra / Vega (smyšlený)“, záložka Kurzy tříd ukáže čáru pro každou třídu.
- Legenda „A · CZK“, „B · EUR“ (kód třídy · měna). Jedna měna = jedna osa; dvě měny = levá a pravá osa, popsané kódem měny
  a obarvené stejně jako jejich čáry. Víc než dvě měny: graf se nekreslí, místo něj věta „Fond má kurzy ve více než dvou měnách,
  graf s vedlejší osou je neukáže.“
- Tooltip: datum (d. M. RRRR), třída, kurz v české notaci se všemi uloženými desetinnými místy a kódem měny.
- Bez zveřejněného ocenění: věta „Zatím žádné zveřejněné ocenění.“
- Pod grafem drobným písmem: „Zveřejněné kurzy v měně třídy. Osy mají různé stupnice – sklon čar nesrovnávejte.“
- Jen barvy z palety (viz Schválený plán), žádné stíny, přechody ani průhlednost.

**Schválený plán** (Claude, 2026-11-13; uživatel schválil variantu „vlastní graf s vedlejší osou“ a provedení Copilotem):

1. **Data:** model `investra.valuation.price.history` (jen pro čtení, jen zveřejněná ocenění): `date`, `fund_id`, `class_id`,
   `currency_id`, `price` (číslo v měně třídy). Načíst přes službu `orm`:
   `searchRead("investra.valuation.price.history", [["fund_id", "=", id]], ["date", "class_id", "currency_id", "price"], { order: "date asc, class_id asc" })`.
   Hodnoty nepřepočítávat ani nezaokrouhlovat.
2. **Komponenta:** OWL `Component`, registrace `registry.category("view_widgets").add("investra_class_price_chart", { component })`,
   props `record` (standard view widgetu). Id fondu z `this.props.record.resId`; u nového neuloženého fondu nic nenačítat
   a ukázat „Uložte fond.“ Data načíst v `onWillStart` a znovu v `onWillUpdateProps`, když se změní `resId`.
3. **Graf:** `useChart` z `@web/core/utils/chart_hook` (načte `web.chartjs_lib`, vytvoří a ruší graf). Typ `line`.
   Osa X: datumy ocenění jako kategorie (sjednocení datumů všech tříd, vzestupně). Chybějící kurz třídy k datu = `null`,
   `spanGaps: false` (mezera, nic se nedokresluje). Měny seřadit podle prvního výskytu: první → osa `y` vlevo, druhá → `y1` vpravo
   (`position: "right"`, `grid.drawOnChartArea: false`). Každá datová řada má `yAxisID` podle své měny. Osy `beginAtZero: false`.
4. **Barvy** (kontrast grafiky na bílé aspoň 3 : 1): řady na levé ose Petroleum `#112e3c`, Petroleum 2 `#596e78`, Graphite `#2c2927`;
   řady na pravé ose Lagoon `#0b5156`, Ember `#eb5b1f`, Graphite 2 `#6a6967`. Popisky a čárky osy v barvě její první řady.
   Mřížka Petroleum 4 `#e8ebec`. Písmo grafu Montserrat (`Chart.defaults.font.family` nenastavovat globálně, jen v `options`).
   Body `pointRadius: 3`, čára `borderWidth: 2`, bez výplně (`fill: false`).
5. **Formát:** datum přes `luxon` (`DateTime.fromISO(...).toFormat("d. M. yyyy")`), kurz `toLocaleString("cs-CZ", { maximumFractionDigits: 8 })` + kód měny.
6. **Šablona a styl:** kontejner s pevnou výškou (např. 360 px), `canvas` s `t-ref` ze `useChart`, poznámka pod grafem v Graphite 2.
7. **Pohled:** v `nav_views.xml` záznam `ir.ui.view` dědící `investra_fund.view_fund_form`, `xpath` na `//notebook` → nová `page`
   „Kurzy tříd“ s `<widget name="investra_class_price_chart"/>`.
8. **Ověření Copilotem:** `tools/view_check`, prohlížeč na 8072 po upgradu modulu (nové soubory a pohled vyžadují upgrade `investra_nav`
   v `investra_vzhled` – řekni uživateli, ať o něj požádá Clauda). Testy Odoo spouští Claude.

## Výsledek

Doplní Copilot.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
