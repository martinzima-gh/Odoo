# AG-018 Přehled fondů: ovládání karty, filtry a tabulka

Zadání pro Copilota (zastupuje Antigravity) v okně nad klonem `~/odoo-review`. Pravidla: `.github/copilot-instructions.md`,
zóny `.agents/rules/10-zony.md`. Bez commitu a pushe; převezme Claude.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (pohledy a styly) |
| Výchozí větev | `etapa/derivaty` (stav s tímto zadáním) |
| Větev úkolu | `cp/prehled-ovladani` (v klonu ji založil Claude) |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-15 „Přehled fondů – můj krok podle matice, pořadí a sbalení“ |

**Cíl:** Z karty Přehledu jde jedním kliknutím otevřít fond, kontroly ocenění a termíny ČNB; přibudou filtry a sloupec
„Můj krok“. Model už všechno potřebné má (hotovo a otestováno), doplňují se jen pohledy a styl.

**Co model nabízí (neměnit, jen použít):**

| Prvek | Použití v pohledu |
|---|---|
| `action_open_fund` | `<a type="object" name="action_open_fund">` – formulář fondu |
| `action_open_checks` | seznam kontrol ocenění, které nejsou v pořádku (rozpracované další ocenění, jinak poslední) |
| `action_open_deadlines` | termíny ČNB fondu |
| `dashboard_next_late` | nově jde hledat: `[('dashboard_next_late', '=', True)]` |
| `dashboard_deadline_state` | nově jde hledat operátory `=` a `in` (hodnoty `overdue`, `open`, `submitted`) |
| `dashboard_my_todo` | pole Boolean, hledat šlo už dřív |

**Kroky** (vše v `addons/custom/investra_dashboard/views/dashboard_views.xml`, není-li uvedeno jinak):

1. **Název fondu** na kartě obalit odkazem na `action_open_fund`. Vzhled názvu se nemění (třída `o_investra_fund_name`
   zůstává; odkaz bez podtržení, podtržení jen při najetí).
2. **Kontroly:** když `dashboard_exception_count` > 0, je text výjimek odkaz na `action_open_checks`; „bez výjimky“ odkazem není.
3. **ČNB:** název výkazu (`dashboard_next_deadline`) je odkaz na `action_open_deadlines`; „bez termínu“ odkazem není.
4. **Seznam kontrol:** nový pohled `view_valuation_check_dashboard_list` pro model `investra.valuation.check`
   (`create="false"`, sloupce `valuation_id`, `name`, `status` jako štítek: `stop` červeně, `warning` oranžově, `ok` zeleně, `detail`).
   Model zatím žádný samostatný seznam nemá, akce ho použije sama.
5. **Filtry** ve `view_fund_dashboard_search`, za stávající, oddělené `<separator/>`:
   `filter_next_late` „Ocenění po termínu“; `filter_deadline_overdue` „Termín ČNB po lhůtě“ (`= 'overdue'`);
   `filter_deadline_open` „Termín ČNB otevřený“ (`in ['open', 'overdue']`); `filter_none` „Bez ocenění“
   (`[('dashboard_status', '=', 'none')]`). Seskupení nepřidávat: pole se neukládají, seskupit podle nich nejde.
6. **Tabulka** (`view_fund_dashboard_list`): za sloupec „Ke zpracování“ přidat `dashboard_my_todo` s popiskem „Můj krok“,
   `widget="boolean"`, `optional="show"`.
7. **Styl** v `static/src/fund_dashboard.scss`: třída `o_investra_todo_more` (odkaz „+N dalších“ / „méně“ pod blokem
   Ke zpracování; widget ji už vykresluje): malé písmo jako `o_investra_todo_turn`, barva `$investra-lagoon`, bez horního
   odsazení většího než 4 px. Styl odkazů z kroků 1–3 sem také. Jen stávající barvy motivu.

**Rozsah souborů:** `addons/custom/investra_dashboard/views/dashboard_views.xml`,
`addons/custom/investra_dashboard/static/src/fund_dashboard.scss`, tento soubor (sekce Výsledek).

**Mimo rozsah:** `models/dashboard.py`, `static/src/fund_todo.js`, `fund_todo.xml`, `__manifest__.py`, testy, jiné moduly,
rozvržení a pořadí pásů karty (rozhodnutí „Vzhled aplikace zachovat“: jen přidávat, nic nepřesouvat).

**Kritéria přijetí:**

- `python3 tools/view_check/check_views.py` → „chyb: 0“.
- V diffu jsou jen dva soubory z Rozsahu a tento soubor.
- Každý nový odkaz používá jednu ze tří akcí výše; žádná nová pole ani `t-if` s výpočtem.
- Testy Odoo Copilot nespouští; spustí je Claude při převzetí (`test_views_load` ověří načtení pohledů).
- V prohlížeči (8072, pokud ji Martin spustí) Neověřeno uvést výslovně.

## Výsledek

Doplní Copilot.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
