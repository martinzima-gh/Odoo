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

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
