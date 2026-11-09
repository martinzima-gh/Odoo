# AG-002 Opravy formuláře ocenění po převzetí AG-001

Navazuje na AG-001. Při převzetí AG-001 Claude našel tři nálezy. První (nečitelný název předchozího ocenění) opravil Claude
v modelu (červená zóna); ocenění má teď název „fond – datum – v1“. Zbylé dva jsou v tomto úkolu.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledu) |
| Výchozí větev | `feature/nav-prototyp` (obsahuje opravu názvu a toto zadání) |
| Větev úkolu | `ag/AG-002-formular-oceneni-opravy` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-09 |
| Navazuje na | AG-001, krok A42 revize |

**Postup s větvemi:**
1. `git switch -c ag/AG-002-formular-oceneni-opravy feature/nav-prototyp`
2. `git merge --no-ff ag/AG-001-formular-oceneni` (převezme tvou práci z AG-001 do nové větve; slučuješ jen do vlastní `ag/*` větve).
   Konflikt se nečeká; kdyby nastal, zastav se a napiš to.
3. Proveď úpravy níže.

**Rozsah souborů:** jen `addons/custom/investra_nav/views/nav_views.xml` (záznam `view_valuation_form`)
a sekce Výsledek v tomto souboru.

**Co udělat:**
1. Ve skupině „Ocenění“ odstranit pole `fund_id` a `date`. Zůstávají jen v nadpisu (`<h1>`), kde jsou editovatelná
   ve stavu Návrh. Ve skupině zůstane `version`, `previous_id` a `preparer_id`.
2. V záložce Třídy nechat `pre_capital` a `delta` ve výchozím stavu zobrazené (`optional="show"`) a skrýt jen `ratio`
   (`optional="hide"`). Pořadí sloupců neměnit.

**Mimo rozsah:** modely, Python, ostatní záložky a seznam ocenění.

**Kritéria přijetí:**
- XML je platné.
- Diff proti `feature/nav-prototyp` mění jen `nav_views.xml`, `docs/ukoly/AG-001-formular-oceneni.md` (z AG-001) a tento soubor.
- `fund_id` a `date` jsou ve formuláři ocenění každé právě jednou.
- Při převzetí Claude ověří aktualizaci modulu, testy `investra_nav` a formulář v `investra_test`.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_nav/views/nav_views.xml`:
    - Ve skupině „Ocenění“ formuláře `view_valuation_form` odstraněna pole `fund_id` a `date`, zůstávají jen v nadpisu `<h1>`. Ve skupině zůstala pole `version`, `previous_id` a `preparer_id`.
    - V záložce Třídy upravena viditelnost sloupců: `pre_capital` a `delta` jsou ve výchozím stavu zobrazeny (`optional="show"`), `ratio` je skryto (`optional="hide"`). Pořadí sloupců neměněno.
- **Ověřeno (příkaz a výsledek):**
  - Syntaktická validace XML:
    - `python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons/custom/investra_nav/views/nav_views.xml')"` (OK)
  - Ověření jedinečnosti polí `fund_id` a `date` ve formuláři ocenění (každé pole přítomno právě 1×).
  - Běh referenčních testů NAV:
    - `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` (55 testů OK)
  - Kontrola diffu: `git diff feature/nav-prototyp...HEAD` mění výhradně `nav_views.xml`, `AG-001-formular-oceneni.md` a `AG-002-formular-oceneni-opravy.md` (zelená zóna).
- **Neověřeno:**
  - Vizuální podoba v běžícím Odoo a Odoo testy (dle pravidel provede Claude při převzetí).
- **Otevřené otázky a návrhy mimo rozsah:**
  - Žádné.

## Převzetí

- **Datum:** 2026-11-09, Claude. Sloučeno do `feature/nav-prototyp` commitem „Převzít AG-001 a AG-002: přehlednější formulář a seznam ocenění“.
- **Zóna a rozsah:** dodržené; změna přesně odpovídá zadání.
- **Nálezy z revize:** v práci Antigravity žádné. Při ověření se ukázalo, že hledání ocenění podle názvu nefiltruje (chyba v Claudově opravě názvu); opravil Claude v `387d6bb` s testem před sloučením.
- **Testy Odoo (`investra_test`):** `investra_nav` a závislý `investra_dashboard` po sloučení 133 testů, 0 selhání, 0 chyb; moduly aktualizované.
- **Ověřeno v běžícím Odoo (8071, po restartu testovací instance):** formulář má nadpis s fondem a datem (každé pole jednou), skupiny „Ocenění“ (verze, předchozí ocenění, zadal) a „Výsledek“; Třídy ukazují `pre_capital` a `delta`, `ratio` je skrytý; seznam má stav jako odznak a volitelný sloupec předchozího ocenění; 8 ocenění se načte, záznam i nový formulář se otevřou; názvy ocenění a předchozích ocenění jsou ve tvaru „fond – datum – v1“, hledání podle části názvu fondu filtruje správně.
- **Neověřeno:** vzhled na obrazovce (šířka tabulek bez posuvníku) – ověří uživatel v prohlížeči. Datum je v testovací databázi v americkém formátu, protože má jen angličtinu.
