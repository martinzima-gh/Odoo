# AG-004 Oprava AG-003 a vyhledávání v dalších seznamech

Dávka pěti vyhledávacích pohledů. Navazuje na AG-003: ten při převzetí neprošel aktualizací modulu, protože Odoo 20
nepovoluje u `<group>` ve vyhledávacím pohledu atributy `expand` a `string`. Proto teď platí povinná kontrola
`python3 tools/view_check/check_views.py` (viz `.agents/rules/20-postup-ukolu.md`).

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `ag/AG-004-hledani-dalsi-seznamy` (připravil Claude: `feature/nav-prototyp` + práce z AG-003) |
| Větev úkolu | stejná; dočasně bez gitu, změny nech v pracovní kopii |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-09 |
| Navazuje na | AG-003 |

**Cíl:** Seznamy ocenění, úpisů a odkupů, nástrojů, obchodů a cen půjde filtrovat podle stavu a seskupit podle
hlavních údajů.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml`, `addons/custom/investra_instruments/views/instrument_views.xml` a sekce Výsledek v tomto souboru.

**Společná pravidla pro všechny pohledy:**
- Nový záznam `view_<model>_search` (element `<search>`) dej hned za seznam (`<list>`) téhož modelu; když seznam
  v souboru není, dej ho před akci. V akci doplň `<field name="search_view_id" ref="…"/>`.
- Seskupení dej do holého `<group>` bez atributů. Každý `<filter>` má atribut `name`.
- Výchozí filtry (`search_default_…`) nepřidávej; o výchozím zobrazení rozhodne uživatel.
- Názvy stavů ber přesně ze `Selection` v modelu (soubory modelů jen čti). Každá hodnota stavu je v právě jednom filtru.
- Nic jiného v souborech neměň (ani formátování existujících záznamů).

**1. Ocenění (`nav_views.xml`, `view_valuation_search`) – oprava AG-003:** u `<group>` odstraň `expand` a `string`.
Nic dalšího neměň.

**2. Úpisy a odkupy (`nav_views.xml`, model `investra.class.movement`, akce `action_movement`):**
- hledání: `class_id`, `fund_id`, `date`
- filtry: „Úpisy“ (`movement_type` = `subscription`), „Odkupy“ (`redemption`); oddělovač; filtr data `date` „Datum“
- seskupení: „Fond“ (`fund_id`), „Třída“ (`class_id`), „Typ“ (`movement_type`), „Měsíc“ (`date:month`)

**3. Nástroje (`instrument_views.xml`, model `investra.instrument`, akce `action_instrument`):**
- hledání: `name`, `isin`, `type_id`, `currency_id`, `fund_id`
- seskupení: „Typ“ (`type_id`), „Měna“ (`currency_id`), „Fond“ (`fund_id`)
- Filtr podle kategorie IFRS 9 nepřidávej: klasifikace se bude přesouvat z nástroje na fond (rozhodnutí 2026-11-09).

**4. Obchody (`instrument_views.xml`, model `investra.trade`, akce `action_trade`):**
- hledání: `fund_id`, `instrument_id`, `trade_date`
- filtry: „Návrh“ (`draft`), „Sjednáno, nevypořádáno“ (`unsettled`), „Vypořádáno“ (`settled`); oddělovač;
  filtr data `trade_date` „Datum obchodu“
- seskupení: „Fond“, „Nástroj“, „Stav“, „Měsíc obchodu“ (`trade_date:month`)

**5. Ceny nástrojů (`instrument_views.xml`, model `investra.instrument.price`, akce `action_price`):**
- hledání: `instrument_id`, `fund_id`, `date`, `source`
- filtry: „Ke schválení“ (`state` = `draft`), „Schválené“ (`approved`); oddělovač; filtr data `date` „Datum ceny“
- seskupení: „Fond“, „Nástroj“, „Stav“, „Měsíc“ (`date:month`)

**Mimo rozsah:** modely, Python, testy, formuláře a seznamy, ostatní akce a nabídky, ostatní moduly.

**Kritéria přijetí:**
- `python3 tools/view_check/check_views.py` skončí „chyb: 0“.
- Diff proti výchozí větvi mění jen dva soubory pohledů a tento soubor.
- Při převzetí Claude ověří aktualizaci modulů, testy Odoo a filtry v `investra_test`.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
