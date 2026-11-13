# Zásady obrazovek Investra

Platí od 2026-11-13 (schválil uživatel). Hotový vzor je **detail ocenění**: návrh `docs/vzhled/navrh-detail-oceneni.html`,
kód `investra_nav/static/src/valuation_summary/` a zděděný pohled `view_valuation_form_class_price_chart` v
`investra_nav/views/nav_views.xml`. Rozhodnutí v `docs/rozhodnuti.md`: „Detail ocenění – souhrn a karty tříd“,
„Formát data v aplikaci“, „Příjemce poplatku jedním výběrem“.

## Proč jsme detail ocenění předělali

- **Pro uživatele jsou důležitá čísla, ne grafika.** Velký graf s vedlejší osou zabíral půl obrazovky a u více měn
  nešel číst. Nahradil ho malý graf v kartě každé třídy (12 měsíců, bez přepínačů, vlastní stupnice).
- **Méně rámečků, víc pořádku.** Čtyři samostatné dlaždice s tlustým pruhem a panel „Základní údaje“ s prázdným místem
  nahradil jeden řádek údajů pod nadpisem a jeden pás tří čísel s děliči.
- **Změna musí být vidět.** Uživatel chce u kurzu i kapitálu hned vidět změnu od minula (▲/▼, absolutně a v %).
- **Žádný klamný údaj.** Změna FK obsahuje úpisy a odkupy, proto pás ukazuje i „z toho úpisy − odkupy“ a „Výsledek za
  období“; nic se neoznačuje jako výkonnost. NFK (mezivýsledek výpočtu) je na stránce Kontroly, ne v souhrnu.
- **Tabulky bez ořezu.** Úzké textové sloupce mají pevnou šířku, aby čísla měla místo; bez prázdných výplňových řádků.

## Rozvržení detailu (formulář)

1. Hlavička Odoo beze změny (tlačítka akcí vlevo, stavový řádek vpravo).
2. Nadpis: hlavní záznam (např. fond) velkým písmem Petroleum; pod ním **jeden řádek údajů** šedě (datum, verze,
   předchozí záznam jako odkaz, kdo zadal). Žádný samostatný panel „Základní údaje“.
3. **Pás klíčových čísel**: jeden rámeček Petroleum 4, uvnitř 2–4 buňky oddělené svislou čarou. Buňka = štítek velkými
   písmeny (11 px, 600, Graphite 2), číslo (26 px, 600, Petroleum, `tabular-nums`), pod ním vysvětlení (12 px, Graphite 2).
4. **Karty** pro opakované položky (třídy, případně nástroje), mřížka `minmax(300px, 1fr)`: název, štítek měny, hlavní
   číslo, změna se znaménkem, malý graf, patička s doplňkovými čísly nad tenkou čarou.
5. Záložky Odoo a tabulky pod tím. Široké tabulky: list formuláře do 2200 px (`o_form_sheet_bg`).

## Barvy a typografie

- Jen paleta `$investra-*` z `investra_theme/static/src/scss/primary_variables.scss`. Bez stínů, přechodů a průhlednosti.
- Růst **Lagoon** `#0b5156` se ▲ a „+“; pokles **Ember** `#eb5b1f` se ▼; nula bez barvy. Platí v kartách i tabulkách
  (`decoration-success/danger` přebarvit na Lagoon/Ember, ne zelená/červená Odoo).
- Stavový řádek (všechny formuláře, `theme.scss`): samostatné zaoblené bubliny, hotové kroky Lagoon, aktuální Petroleum,
  budoucí bílé s rámečkem Petroleum 4.
- Písmo Montserrat z tématu; čísla `font-variant-numeric: tabular-nums`, zarovnaná doprava (i nadpisy jejich sloupců).
- **Datum všude 30.09.2026** (dd.MM.yyyy), i ve vlastních widgetech.

## Co se nesmí

- Nepřepočítávat ani nedopočítávat údaje ve vzhledu: widget jen zobrazuje, co uložil výpočet. Měny se nemíchají.
- Neměnit pořadí ani chování stavů a akcí. Nemazat pole z formuláře: méně důležitá přesunout (záložka, volitelný sloupec).
- Ilustrativní čísla z návrhů nepřebírat do kódu ani dat.

## Technické poučení (Odoo 20, OWL 3)

Opravy z převzetí CP-2026-11-13, aby se neopakovaly:

- OWL 3 nemá `useState` – stav je `proxy({...})`; v šablonách vždy `this.` (`this.state.x`, `this.props.record`).
- `luxon` není modul: `const { DateTime } = luxon;`. ORM přes `useService("orm")`, akce přes `useService("action")`.
- Neuložené změny: `record.dirty` (synchronní), ne `isDirty()`.
- Chyba widgetu nesmí zablokovat formulář: `try/catch`, místo obsahu krátká věta „… nelze zobrazit“.
- Načítat data jen při změně záznamu nebo po uložení, ne při každém poli; zastaralou odpověď zahodit.
- Zobrazovaný název many2one obsahuje často i nadřazený záznam („Fond / A“): kód brát z vlastního pole.
- SCSS v modulu, který nezávisí na `investra_theme`, potřebuje záložní proměnné `$investra-x: … !default;`.
- Widget je obalený `div`em Odoo – selektory psát jako potomka, ne `> div >`.
- Nové pole (i jen zobrazovací) je Python = červená/oranžová zóna: navrhnout v záznamu CP, udělá Claude.
