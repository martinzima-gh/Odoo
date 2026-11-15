# ST-03 Chyba Přehledu fondů: blok „Ke zpracování“

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (šablona widgetu, bez výpočtu a účtování) |
| Výchozí větev | `feature/instrument-master` (ST-01 ještě neproběhlo; změna 15. 11. 2026) |
| Větev úkolu | `ukol/ST-03` |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/plan-dalsiho-vyvoje.md` (Etapa 0), hlášení Martina z 8071 (15. 11. 2026 13:21) |

**Chyba (text z prohlížeče):** `TypeError: undefined is not an object (evaluating 'ctx['items'].length')`
v šabloně `investra_dashboard.FundTodo`, při vykreslení karet nabídky Přehled.

**Příčina (zjištěno čtením kódu, v prohlížeči neověřeno):** `addons/custom/investra_dashboard/static/src/fund_todo.xml`
čte `items` bez `this.` (`t-if="!items.length"`, `t-foreach="items"`). Odoo 20 v šablonách vyžaduje `this.`:
jádro tak píše všechny šablony (např. `web.Ribbon`: `this.classes`, `this.props.text`) a stejně i náš funkční widget
`investra_nav/static/src/valuation_summary/valuation_summary.xml`. Proměnné smyčky (`item`) zůstávají bez `this.`.

**Cíl:** Přehled se načte bez chyby a blok „Ke zpracování“ ukáže položky nebo „nic nečeká“.

**Postup:**

1. V `fund_todo.xml` nahradit obě čtení `items` za `this.items`. Logiku ani model neměnit.
2. Projít ostatní šablony ve `addons/custom/*/static/src/**/*.xml` na stejnou chybu (čtení člena komponenty bez `this.`).
3. Pokud to jde jednoduše, doplnit do `tools/view_check` kontrolu, která takové čtení v šablonách najde; jinak jen
   popsat návrh ve Výsledku.
4. `tools/run_tests.sh investra_dashboard` (dočasná databáze, sama se smaže).
5. Ověření na 8071: statický soubor se načte znovu po obnovení stránky (Cmd+Shift+R). Kdyby prohlížeč dál dostával
   starý balík skriptů, nic nerestartovat ani nepovyšovat a napsat to Martinovi (restart a upgrade jsou na jeho souhlas).

**Rozsah souborů:** `addons/custom/investra_dashboard/static/src/fund_todo.xml`, případně jiné šablony se stejnou
chybou, `tools/view_check/`, tento soubor (Výsledek), předávka.

**Sloučení:** po Martinově potvrzení v prohlížeči sloučit `ukol/ST-03` do `feature/instrument-master` (fast-forward),
pushnout a krátkou větev smazat místně i na origin; oprava se pak do `main` dostane s ST-01.

**Mimo rozsah:** `dashboard.py` a výpočet položek, vzhled karet, verze modulu, databáze, restart služeb.

**Kritéria přijetí:** v `fund_todo.xml` žádné čtení `items` bez `this.`; testy modulu bez selhání; seznam prověřených
šablon ve Výsledku; Martin potvrdí v prohlížeči, že Přehled funguje (model to sám neověří – uvést jako Neověřeno).

## Výsledek

- **Změněné soubory:** `addons/custom/investra_dashboard/static/src/fund_todo.xml` (`this.items` ve dvou místech),
  nově `tools/view_check/check_templates.py` a `test_check_templates.py`, tento soubor.
- **Ověřeno (příkaz a výsledek):**
  - Prověřené šablony (celkem 2): `investra_dashboard/static/src/fund_todo.xml` (chyba opravena),
    `investra_nav/static/src/valuation_summary/valuation_summary.xml` (v pořádku, vše přes `this.`).
  - `python3 tools/view_check/check_templates.py`: před opravou 2 chyby (obě `items`), po opravě 0.
  - `python3 -m unittest test_check_templates test_check_views` (v `tools/view_check`): 7 testů OK.
  - `tools/run_tests.sh investra_dashboard`: 0 failed, 0 error z 24 testů, dočasná DB smazána.
- **Neověřeno:** že se Přehled na 8071 načte bez chyby (po Cmd+Shift+R) – ověří Martin v prohlížeči.
  Kontrola šablon je heuristika (první identifikátor ve výrazech); těla šipkových funkcí a `t-on-*` nekontroluje.
- **Otevřené otázky a návrhy mimo rozsah:** kontrolu šablon lze později zařadit do CI (ST-02).

## Převzetí
