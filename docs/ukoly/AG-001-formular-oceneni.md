# AG-001 Přehlednější formulář ocenění

První zkušební úkol pro Antigravity. Ověřuje celý postup: zadání, větev, výsledek, převzetí.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledu) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-001-formular-oceneni` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-09 |
| Navazuje na | krok A42 revize (obrazovka ocenění O1), rozhodnutí 2026-11-09 „Návrh obrazovky NAV od vedoucího“ |

**Cíl:** formulář ocenění (`investra.valuation`) má být čitelný na první pohled jako návrh vedoucího:
velký nadpis, pojmenované sekce a tabulky, které se vejdou na šířku. Výpočet ani model se nemění.

**Rozsah souborů:** jen `addons/custom/investra_nav/views/nav_views.xml`, záznamy `view_valuation_form`
a `view_valuation_list`. Plus sekce Výsledek v tomto souboru.

**Co udělat:**
1. Nahoru do `<sheet>` dát nadpis (`<div class="oe_title"><h1>…</h1></div>`) s fondem a datem ocenění
   (pole `fund_id` a `date`, pole zůstanou editovatelná jen ve stavu Návrh jako dnes).
2. Pole pod nadpisem rozdělit do pojmenovaných skupin (`<group string="…">`):
   - **Ocenění:** fond, datum, verze, předchozí ocenění (`previous_id`), zadal (`preparer_id`),
   - **Výsledek:** FK (`fund_capital`), NFK (`neutral_capital`), balíček pro depozitáře (`package_id`).
3. V záložkách Třídy a Portfolio označit méně důležité sloupce jako volitelné (`optional="show"` nebo `optional="hide"`),
   aby se tabulka vešla bez vodorovného posuvníku. V Portfoliu skrýt ve výchozím stavu `cost` a `fair_value_currency`.
4. V seznamu ocenění (`view_valuation_list`) přidat `previous_id` jako volitelný skrytý sloupec a stav zobrazit
   jako odznak (`widget="badge"`).

**Mimo rozsah:**
- změny modelů a Python kódu (nová pole jako počet dní v období nebo přemostění po třídách přijdou v samostatném úkolu
  od Clauda, protože jsou v červené zóně),
- historie změn (chatter) – vyžaduje změnu modelu,
- tlačítka a stavy v hlavičce formuláře neměnit.

**Kritéria přijetí:**
- XML je platné (kontrola XML projde).
- Diff mění jen `nav_views.xml` a tento soubor.
- Všechny popisky jsou česky.
- Při převzetí Claude ověří: aktualizace modulu `investra_nav` v testovací databázi projde, testy `investra_nav`
  projdou a formulář v `investra_test` ukazuje nadpis, dvě pojmenované skupiny a tabulky bez posuvníku.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_nav/views/nav_views.xml`:
    - `view_valuation_form`:
      - Doplněn nadpis `<div class="oe_title"><h1>...</h1></div>` s fondem a datem ocenění (`readonly="state != 'draft'"`).
      - Pole pod nadpisem rozdělena do dvou pojmenovaných skupin:
        - `Ocenění`: `fund_id`, `date`, `version`, `previous_id`, `preparer_id` (s českým popiskem `string="Zadal"`).
        - `Výsledek`: `fund_capital`, `neutral_capital`, `currency_id` (`invisible="1"`), `package_id`.
      - V záložce Třídy nastaveno `optional="hide"` pro mezikroky alokace (`pre_capital`, `ratio`, `delta`), hlavní sloupce (`class_id`, `capital`, `units`, `price`) zůstávají přímo viditelné.
      - V záložce Portfolio nastaveno ve výchozím stavu skrytí pro `cost` a `fair_value_currency` (`optional="hide"`) a doplňkové sloupce označeny jako volitelné (`optional="show"` pro `isin`, `currency_id`, `fx_rate`).
    - `view_valuation_list`:
      - Přidán volitelný skrytý sloupec `previous_id` (`optional="hide"`).
      - Doplněn widget odznaku ke stavu: `<field name="state" widget="badge"/>`.
- **Ověřeno (příkaz a výsledek):**
  - Kontrola validity XML:
    - `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" addons/custom/investra_nav/views/nav_views.xml` (OK)
    - `python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons/custom/investra_nav/views/nav_views.xml')"` (OK)
  - Běh referenčních testů NAV:
    - `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` (55 testů OK)
  - Kontrola diffu a zóny: změny omezeny výhradně na `nav_views.xml` a tento soubor zadání (zelená zóna).
- **Neověřeno:**
  - Vykreslení formuláře a responzivita přímo ve webovém klientu Odoo (vyžaduje Odoo server).
  - Běh testů Odoo a upgrade modulu v databázi (dle pravidel provádí Claude při převzetí).
- **Otevřené otázky a návrhy mimo rozsah:**
  - Pole `fund_id` a `date` jsou podle zadání jak v nadpisu `<h1>`, tak ve skupině `Ocenění`. Pokud by v budoucnu stačilo mít je pouze v nadpisu, lze je ze skupiny odebrat.

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
