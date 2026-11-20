# AG-025 Diagnostika chyby: záložka Daň ve formuláři fondu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (pohledy); jiná příčina se jen popíše |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` |
| Větev úkolu | `ag/AG-025-zalozka-dan` |
| Zadal, dne | Martin (poznámky) / Claude, 2026-11-20 |
| Navazuje na | `docs/ukoly/ZJ-20-poznamky-zpracovani.md`, bod 5; `CP-2026-11-20-ZJ-07-19-formulare.md` |

**Cíl:** Zjistit, proč se formulář fondu chová divně, když se na záložce **Daň** klikne na řádek tabulky **Výjimky**, a opravit to,
je-li příčina v pohledu.

**Postup:**
1. Odtud: reprodukce na instanci 8072 (kopie `investra`) – nezapisuj do pracovní databáze. Martin popíše přesně, co se děje (chybí
   v zadání; zeptej se ho, než začneš hádat).
2. Zkontroluj pohled `view_fund_form_tax` v `addons/custom/investra_nav/views/nav_views.xml` (jen `<list editable="bottom">` v
   `tax_exception_ids`): `domain` s `parent.company_id`, `options`, pole `movement_ytd` jen pro čtení, `context="{'default_fund_id': id}"`,
   neplatné výrazy v `invisible`.
3. Podívej se do konzole prohlížeče (chyba JavaScriptu) a do logu Odoo. Příčinu zapiš.
4. Oprava jen v pohledu. Je-li příčina v modelu (např. `onchange`, `compute`), nic neopravuj a popiš ji.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml` (jen záložka Daň ve formuláři fondu).

**Mimo rozsah:** Python, výpočet daně, jiné pohledy.

**Kritéria přijetí:** příčina popsaná ve Výsledku (s textem chyby); po opravě klik na řádek výjimky funguje bez chyby
v konzoli; modul se povýší bez chyby.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
