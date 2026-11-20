# CP-2026-11-20-ZJ-07-19-formulare – formuláře a manuál

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` |
| Větev úkolu | `cp/ZJ-07-19-formulare` |
| Zadal, dne | uživatel, 2026-11-20 |
| Navazuje na | dávka ZJ-07 až ZJ-19, běh 6; předávky běhu 4 a 5 |

**Cíl:** Doplnit požadované pohledy, nabídky, kapitoly manuálu a SQL ukázky podle zadání běhu 6 a polí uvedených v předávkách.

**Rozsah souborů:** Pohledy `investra_fund`, `investra_instruments` a `investra_nav`; `investra_nav/__manifest__.py` pouze o novou XML položku v `data`; `docs/manual/*.md`; `docs/sql/05-prehled-fondu.sql`; tento záznam.

**Mimo rozsah:** Python, modely, oprávnění, data, migrace, verze modulů, provozní databáze, Odoo testy, commit a push.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_fund/views/fund_views.xml`
  - `addons/custom/investra_instruments/views/instrument_views.xml`
  - `addons/custom/investra_nav/__manifest__.py`
  - `addons/custom/investra_nav/views/nav_views.xml`
  - `addons/custom/investra_nav/views/tax_views.xml`
  - `addons/custom/investra_nav/views/dividend_views.xml`
  - `docs/manual/02-fond.md`, `06-portfolia-a-nastroje.md`, `09-uplaty-a-opravy.md`, `10-rozdeleni-mezi-tridy.md`, `11-dan.md`, `README.md`
  - `docs/sql/05-prehled-fondu.sql`
  - `docs/ukoly/CP-2026-11-20-ZJ-07-19-formulare.md`
- **Ověřeno (příkaz a výsledek):** XML parserem načteny všechny změněné XML soubory; `ast.parse` ověřil syntaxi manifestu; `git diff --check` bez nálezu.
- **Neověřeno:** Načtení/povýšení pohledů v Odoo, chování v prohlížeči a Odoo testy. Tyto kontroly provede Claude při převzetí.
- **Otevřené otázky a návrhy mimo rozsah:**
  1. **Náhled zaúčtování – sloupec Třída:** `posting_preview.py` předává kód třídy do řádků, ale `_documents_html` ho zahazuje a nevytváří sloupec. Oprava vyžaduje Python mimo rozsah.
  2. **Konec účetního období:** fond nemá pole pro zobrazení `company_id.fiscalyear_last_day/month`; XML nemůže bezpečně zobrazit odvozenou hodnotu bez nového pole nebo pomocného modelového prvku. Manuál proto uvádí zdroj nastavení a upozorňuje, že pole ve formuláři chybí.
  3. **Storno dividendy:** `action_reverse(reason)` vyžaduje důvod, ale neexistuje průvodce storna dividendy. Tlačítko bez průvodce by volalo metodu chybně; doplnění vyžaduje nový wizard/model a Python.
  4. **Doména Daňové pravidlo u opravy:** pohled vylučuje pravidlo Mimo základ daně, ale nemá k dispozici seznam pravidel použitých fondem pro přesnou doménu. Model při uložení použití pravidla ověřuje; přesná doména potřebuje pomocný kontext/pole mimo rozsah.
- Změna se necommitovala ani neposílala. Při kontrole stavu byla nalezena předchozí neovlivněná neznámá složka `.vscode/`; zůstala nedotčená.

## Převzetí

Doplní Claude: výsledek revize, doplnění mimo rozsah, testy Odoo a případné sloučení.
