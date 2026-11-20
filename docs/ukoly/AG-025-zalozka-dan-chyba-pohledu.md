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
1. Reprodukce na instanci 8072 (kopie `investra`) – nezapisuj do pracovní databáze. **Příznak (Martin, 2026-11-20):** po kliknutí na
   řádek tabulky Výjimky na záložce Daň začne tabulka blikat, jako by se chtěla rozšiřovat (smyčka překreslování).
   Hypotézy ke kontrole: editovatelný seznam (`<list editable="bottom">`) uvnitř `<group string="Výjimky" invisible="not tax_rule_id">`
   (seznam v seskupení s podmíněnou viditelností) – zkus přesunout pole mimo `group` a podmínku dát na `invisible` samotného pole;
   `domain` s `parent.company_id`; `movement_ytd` (počítané pole) přepočítávané při každé změně řádku; `context` s `id`.
2. Zkontroluj pohled `view_fund_form_tax` v `addons/custom/investra_nav/views/nav_views.xml` (jen `<list editable="bottom">` v
   `tax_exception_ids`): `domain` s `parent.company_id`, `options`, pole `movement_ytd` jen pro čtení, `context="{'default_fund_id': id}"`,
   neplatné výrazy v `invisible`.
3. Podívej se do konzole prohlížeče (chyba JavaScriptu) a do logu Odoo. Příčinu zapiš.
4. Oprava jen v pohledu. Je-li příčina v modelu (např. `onchange`, `compute`), nic neopravuj a popiš ji.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml` (jen záložka Daň ve formuláři fondu).

**Mimo rozsah:** Python, výpočet daně, jiné pohledy.

**Kritéria přijetí:** příčina popsaná ve Výsledku (s textem chyby); po opravě klik na řádek výjimky funguje bez chyby
v konzoli; modul se povýší bez chyby.

**Upřesnění příznaku (Martin, 2026-11-20):** po kliknutí na řádek se tabulka snaží donekonečna rozšiřovat, přidává sloupce, a stále to běží
(nekonečné překreslování seznamu). Kontrola po povýšení: Copilot přesunul seznam mimo podmíněně skrytou skupinu; pokud blikání zůstane,
další hypotézy: pevné šířky sloupců (`width`) u polí Podíl, Neuznatelné a Pohyb, Monetary pole `movement_ytd` bez sloupce měny (`currency_id`),
`optional` sloupce; získat chybu z konzole prohlížeče.

## Výsledek

- **Změněné soubory:** `addons/custom/investra_nav/views/nav_views.xml` – pole `tax_exception_ids` je mimo rodičovský `<group invisible=...>`; viditelnost se nyní řídí polem samotným. Podmínění zobrazení tabulky zůstalo zachováno.
- **Příčina / důkazy:** předchozí pohled vkládal editovatelný one2many seznam do podmíněně skrytého skupinového kontejneru; to odpovídá ověřované hypotéze zadané v úkolu, ale není potvrzenou příčinou blikání. V modelu je `movement_ytd` počítané podle `fund_id` a `account_id`, ne přes onchange; nenalezl jsem důkaz, že by se spouštělo každým kliknutím. Doména s `parent.company_id` a kontext `default_fund_id` zůstaly beze změny.
- **Ověřeno:** instance `http://127.0.0.1:8072` při otevření vrátila `ERR_CONNECTION_REFUSED`; na UI proto nebylo možné blikání zreprodukovat ani po úpravě ověřit. Text chyby z konzole stránky Odoo není k dispozici. Prohlédnut model výjimky a zdrojové XML.
- **Neověřeno:** chování po kliknutí na řádek, chyba v konzoli prohlížeče, log Odoo a upgrade modulu.
- **Otevřené otázky a návrhy mimo rozsah:** po spuštění instance 8072 ověřit, zda úprava odstranila blikání; pokud ne, získat skutečnou chybu z konzole a logu a předat příčinu Claudovi. Instanci jsem nespouštěl.

## Převzetí

Převzato 2026-11-20 (`14c751e`). Oprava je jen hypotéza (seznam mimo podmíněně skrytou skupinu); blikání nešlo reprodukovat, ověřit v prohlížeči po povýšení. Záložka přejmenována na „Daňová pravidla“.
