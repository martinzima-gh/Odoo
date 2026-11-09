# AG-005 Vyhledávání ve zbývajících seznamech

Druhá dávka vyhledávacích pohledů podle vzoru AG-004 (převzato bez nálezů). Pokrývá devět seznamů, se kterými se
v prototypu pracuje nejčastěji.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `ag/AG-005-hledani-zbyvajici-seznamy` (připravil Claude z `feature/nav-prototyp`) |
| Větev úkolu | stejná; dočasně bez gitu, změny nech v pracovní kopii |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-09 |
| Navazuje na | AG-004 |

**Cíl:** Fondy, účetní knihy, události, kurzy, termíny ČNB, přecenění cizích měn, protistrany, pravidla úplat a splátky
půjde filtrovat a seskupit podle hlavních údajů.

**Rozsah souborů:**
`addons/custom/investra_fund/views/fund_views.xml`, `addons/custom/investra_entity/views/entity_views.xml`,
`addons/custom/investra_posting/views/posting_views.xml`, `addons/custom/investra_rates/views/rate_views.xml`,
`addons/custom/investra_dashboard/views/dashboard_views.xml`, `addons/custom/investra_fx_revaluation/views/fx_views.xml`,
`addons/custom/investra_counterparty/views/counterparty_views.xml`, `addons/custom/investra_nav/views/nav_views.xml`
a sekce Výsledek v tomto souboru.

**Společná pravidla (stejná jako u AG-004):**
- Nový záznam `view_<model>_search` (element `<search>`) dej hned za seznam (`<list>`) téhož modelu; když seznam
  v souboru není, dej ho před akci. V akci doplň `<field name="search_view_id" ref="…"/>`.
- Seskupení dej do holého `<group>` bez atributů. Každý `<filter>` má atribut `name`.
- Výchozí filtry (`search_default_…`) nepřidávej.
- Hodnoty výběrů ber přesně ze `Selection` v modelu (soubory modelů jen čti). U stavu je každá hodnota v právě
  jednom filtru.
- Nic jiného v souborech neměň (ani formátování existujících záznamů).
- `id` záznamu musí být v modulu jedinečné; když `view_<model>_search` už existuje, zastav se a napiš to do výsledku.

**1. Fondy (`fund_views.xml`, model `investra.fund`, akce `action_fund`):**
- hledání: `name`, `entity_id`
- seskupení: „Frekvence ocenění“ (`valuation_frequency`), „Zaúčtování obchodů“ (`trade_recognition`)
- Akci `action_fund_dashboard` v `investra_dashboard` neměň (výchozí vyhledávací pohled modelu se použije sám).

**2. Účetní knihy (`entity_views.xml`, model `investra.entity`, akce `action_entity`):**
- hledání: `name`, `parent_id`, `founder_id`
- seskupení: „Typ“ (`entity_type`), „Účetní rámec“ (`framework`), „Nadřazená kniha“ (`parent_id`)

**3. Účetní události (`posting_views.xml`, model `investra.accounting.event`, akce `action_event`):**
- hledání: `name`, `event_type`, `key`, `date`
- filtry: „Návrh“ (`draft`), „Zamčený návrh“ (`locked`), „Zaúčtováno“ (`posted`), „Stornováno“ (`reversed`),
  „Zrušený návrh“ (`discarded`); oddělovač; filtr data `date` „Datum“
- seskupení: „Kniha“ (`company_id`), „Typ“ (`event_type`), „Stav“ (`state`), „Měsíc“ (`date:month`)

**4. Vyhlášené kurzy (`rate_views.xml`, model `investra.rate`, akce `action_rate`):**
- hledání: `currency_id`, `date`
- filtry: „ČNB“ (`source` = `cnb`), „ECB“ (`ecb`); oddělovač; filtr data `date` „Datum kurzu“
- seskupení: „Měna“ (`currency_id`), „Zdroj“ (`source`), „Měsíc“ (`date:month`)

**5. Termíny ČNB (`dashboard_views.xml`, model `investra.regulatory.deadline`, akce `action_deadline`):**
- hledání: `fund_id`, `report`
- filtry: „Otevřeno“ (`state` = `open`), „Podáno“ (`submitted`); oddělovač; filtr data `due_date` „Termín“
- seskupení: „Fond“ (`fund_id`), „Výkaz“ (`report`), „Stav“ (`state`), „Měsíc termínu“ (`due_date:month`)

**6. Přecenění cizích měn (`fx_views.xml`, model `investra.fx.run`, akce `action_fx_run`):**
- hledání: `profile_id`, `date`
- filtr data `date` „Datum přecenění“
- seskupení: „Profil“ (`profile_id`), „Společnost“ (`company_id`), „Měsíc“ (`date:month`)
- Podle `move_state` neseskupuj ani nefiltruj (je to neuložené související pole).

**7. Protistrany (`counterparty_views.xml`, model `investra.counterparty.profile`, akce `action_profile`):**
- hledání: `partner_id`, `lei`, `country_id`, `sector_id`
- seskupení: „Země“ (`country_id`), „Sektor ESA 2010“ (`sector_id`)

**8. Pravidla úplat (`nav_views.xml`, model `investra.fee.rule`, akce `action_fee_rule`):**
- hledání: `name`, `fund_id`, `statute_ref`
- filtry: „Časově rozlišená úplata“ (`kind` = `periodic`), „Výkonnostní odměna“ (`performance`),
  „Očekávaná daň“ (`tax`), „Výpočet mimo Odoo“ (`external`); oddělovač; „Archivováno“ (`active` = `False`)
- seskupení: „Fond“ (`fund_id`), „Druh“ (`kind`)

**9. Splátky nástrojů (`nav_views.xml`, model `investra.instrument.repayment`, akce `action_repayment`):**
- hledání: `fund_id`, `instrument_id`, `date`
- filtry: „Nezaúčtováno“ (`event_id` = `False`), „Zaúčtováno“ (`event_id` != `False`); oddělovač;
  filtr data `date` „Datum“
- seskupení: „Fond“ (`fund_id`), „Nástroj“ (`instrument_id`), „Měsíc“ (`date:month`)

**Mimo rozsah:** modely, Python, testy, formuláře a seznamy, ostatní akce a nabídky (včetně `action_fund_dashboard`,
`action_fx_profile`, `action_scheme`, `action_cnb_map`, `action_instrument_type`), ostatní moduly.

**Kritéria přijetí:**
- `python3 tools/view_check/check_views.py` skončí „chyb: 0“.
- Diff proti výchozí větvi mění jen soubory z Rozsahu a tento soubor.
- Při převzetí Claude ověří aktualizaci modulů, testy Odoo a uložení pohledů v `investra_test`.

## Výsledek

Úkol provedl Copilot.

- **Změněné soubory:** osm XML pohledů uvedených v Rozsahu souborů a tento soubor.
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — Zkontrolováno souborů: 11, chyb: 0; `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` — 55 testů, OK; `git diff --check` — bez chyb.
- **Neověřeno:** vzhled a chování pohledů v běžícím Odoo; Docker ani databáze nebyly použity.
- **Otevřené otázky a návrhy mimo rozsah:** žádné.

## Převzetí

- **Datum:** 2026-11-09
- **Provedl:** GitHub Copilot (režim Agent v okně na `~/odoo-review`) místo Antigravity, která byla na limitu
  (rozhodnutí 2026-11-09 „Copilot jako náhradní vývojář“). Commit `e1a1102` s autorem „Copilot“ udělal Claude v klonu.
- **Sloučení:** `550ca30` do `feature/nav-prototyp`.
- **Revize:** diff mění jen osm souborů pohledů z Rozsahu a tento soubor (zelená zóna). Pole a hodnoty výběrů
  odpovídají modelům. Jediná odchylka: filtr „Archivováno“ u pravidel úplat má navíc `context="{'active_test': False}"`;
  je to obvyklý zápis v Odoo a chování nemění, ponecháno. Nálezy: žádné.
- **Testy:** `check_views.py` – chyb: 0; `-u` devíti dotčených modulů s jejich testy nad `investra_test` –
  0 failed, 0 error(s) of 259 tests. Řádka ERROR „Stažení kurzů selhalo“ v logu pochází z existujícího testu
  `test_cron_publishes_downloaded_rates` (podvržený text ČNB nejde načíst jako ECB, chyba se podle návrhu jen zaloguje);
  s úkolem nesouvisí.
- **Databáze `investra_test`:** všech 14 vyhledávacích pohledů Investry je uloženo a akce na ně odkazují.
- **Neověřeno:** vzhled filtrů v UI.
