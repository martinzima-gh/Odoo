# AG-017 Duplicitní popisky polí v tabulce tříd ocenění

Při každém upgradu `investra_nav` Odoo varuje (log 15. 11. 2026, `.test-logs/upgrade-vzhled-2026-11-15-nav29.log`):

    Two fields (class_code, class_id) of investra.valuation.class() have the same label: Třída.
    Two fields (price_display, price) of investra.valuation.class() have the same label: Kurz.

Neškodné, ale zanáší log a v Odoo se pak ve filtrech a exportu objeví dvě pole stejného jména.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen popisky polí, bez logiky); soubor je v modulu NAV, proto Claude při převzetí diff povinně reviduje |
| Výchozí větev | `feature/instrument-master` |
| Větev úkolu | `ag/AG-017-popisky-trid` (připraví Claude v `~/odoo-review`) |
| Řešitel | Antigravity nebo Copilot |
| Zadal, dne | Claude, 2026-11-15 (návrh, čeká na pokyn Martina) |

**Cíl:** varování zmizí, vzhled obrazovek zůstane stejný (záhlaví sloupců „Třída“ a „Kurz“ beze změny).

**Postup:**
1. `addons/custom/investra_nav/models/valuation.py`, třída `InvestraValuationClass`: jen parametr `string`
   - `class_code` → `string="Kód třídy"`,
   - `price_display` → `string="Kurz (zobrazení)"`.
   Nic jiného v souboru neměnit (červená zóna).
2. `addons/custom/investra_nav/views/nav_views.xml`, seznam tříd ocenění (řádek s `<field name="class_code" width="70px"/>`):
   doplnit `string="Třída"`, aby záhlaví sloupce zůstalo. U `price_display` už `string="Kurz"` je.
3. Ověření (Claude): upgrade `investra_nav` v testovací DB bez obou varování; snímek obrazovky tabulky tříd před a po.

**Nedělat:** měnit `class_id`, `price` ani jiná pole; měnit verzi modulu bez dohody s Claudem.

## Výsledek

## Převzetí
