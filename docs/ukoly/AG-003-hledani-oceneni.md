# AG-003 Vyhledávání a filtry v seznamu ocenění

První úkol Antigravity v režimu Auto s bezpečnostním hookem. Pravidla příkazů jsou v `.agents/rules/20-postup-ukolu.md`.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledu) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-003-hledani-oceneni` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-09 |
| Navazuje na | AG-001 a AG-002 (formulář a seznam ocenění) |

**Postup s větvemi:** `git switch -c ag/AG-003-hledani-oceneni feature/nav-prototyp` (hook se zeptá uživatele).

**Cíl:** Ocenění zatím nemá vlastní vyhledávací pohled, takže v seznamu nejde rychle najít rozpracovaná ocenění,
ocenění čekající na schválení nebo ocenění jednoho fondu, ani je seskupit. Po úkolu půjde seznam filtrovat podle stavu
a seskupit podle fondu, stavu a měsíce data ocenění.

**Rozsah souborů:** jen `addons/custom/investra_nav/views/nav_views.xml` (nový záznam vyhledávacího pohledu a odkaz na něj v akci `action_valuation`) a sekce Výsledek v tomto souboru.

**Co udělat:**
1. Přidat záznam `view_valuation_search` (model `investra.valuation`, element `<search>`) hned za `view_valuation_list`.
2. Pole pro hledání: `fund_id` a `date`.
3. Filtry podle stavu (`state`), ve dvou skupinách oddělených `<separator/>`:
   - „Rozpracovaná“: `draft`, `computed`, `returned`; „Ke schválení“: `submitted`;
   - „Schválená a zaúčtovaná“: `approved`, `posted`; „U depozitáře“: `sent`, `confirmed`;
     „Zveřejněná“: `published`; „Stornovaná“: `reversed`.
4. Filtr data ocenění: `<filter name="filter_date" date="date" string="Datum ocenění"/>`.
5. Seskupení (`context="{'group_by': …}"`): „Fond“ (`fund_id`), „Stav“ (`state`), „Měsíc ocenění“ (`date:month`).
6. V akci `action_valuation` doplnit `<field name="search_view_id" ref="view_valuation_search"/>`. Výchozí filtr
   (`context` s `search_default_…`) nepřidávat; o výchozím zobrazení rozhodne uživatel.

**Mimo rozsah:** modely, Python, testy, formulář a seznam ocenění, ostatní akce a nabídky.

**Kritéria přijetí:**
- XML je platné (kontrola XML z pravidel).
- Diff proti `feature/nav-prototyp` mění jen `nav_views.xml` a tento soubor.
- Každá hodnota `state` z modelu je právě v jednom filtru; názvy hodnot odpovídají `Selection` v
  `addons/custom/investra_nav/models/valuation.py` (jen čtení).
- Při převzetí Claude ověří aktualizaci modulu, testy `investra_nav` a filtry v `investra_test`.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_nav/views/nav_views.xml`:
    - Přidán záznam vyhledávacího pohledu `view_valuation_search` (model `investra.valuation`) za `view_valuation_list`.
    - Doplněna vyhledávací pole `fund_id` a `date`.
    - Doplněny filtry podle stavu (`state`) rozdělené do 2 skupin oddělených `<separator/>`:
      - 1. skupina: „Rozpracovaná“ (`draft`, `computed`, `returned`), „Ke schválení“ (`submitted`).
      - 2. skupina: „Schválená a zaúčtovaná“ (`approved`, `posted`), „U depozitáře“ (`sent`, `confirmed`), „Zveřejněná“ (`published`), „Stornovaná“ (`reversed`).
      - Všech 10 stavů z modelu je pokryto právě jednou.
    - Doplněn časový filtr data ocenění: `<filter name="filter_date" date="date" string="Datum ocenění"/>`.
    - Doplněny filtry seskupení: „Fond“ (`fund_id`), „Stav“ (`state`), „Měsíc ocenění“ (`date:month`).
    - V akci `action_valuation` doplněn odkaz `<field name="search_view_id" ref="view_valuation_search"/>` (bez výchozích filtrů).
- **Ověřeno (příkaz a výsledek):**
  - Kontrola syntaxe XML: `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" addons/custom/investra_nav/views/nav_views.xml` (OK).
  - Kontrola referenčního výpočtu NAV: `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` (55 testů OK).
  - Kontrola rozsahu změn: `git diff` zasahuje výhradně `nav_views.xml` a tento soubor zadání (zelená zóna).
- **Neověřeno:**
  - Vizuální chování vyhledávání a filtrů v běžícím Odoo klientu a běh Odoo integračních testů (dle pravidel provádí Claude při převzetí).
- **Otevřené otázky a návrhy mimo rozsah:**
  - Žádné.

## Převzetí

- **Datum:** 2026-11-09
- **Výsledek:** při prvním převzetí (commit `b6490cf`) neprošla aktualizace modulu: Odoo 20 nepovoluje u `<group>`
  ve vyhledávacím pohledu atributy `expand` a `string`. Nic se nezačlenilo; oprava zadána jako AG-004.
- **Sloučení:** spolu s AG-004 do `feature/nav-prototyp` (rychlé převinutí na `79b9899`), viz převzetí AG-004.
