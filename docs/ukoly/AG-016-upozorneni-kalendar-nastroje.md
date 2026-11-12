# AG-016 Upozornění na dluhopis bez kalendáře toků (formulář nástroje)

Dluhopis bez kalendáře toků má naběhlý úrok obchodu 0 a ocenění úrok pozice nepočítá. Formulář obchodu a ocenění
na to od 12. 11. upozorňují (provedl Claude, rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu a kalendář
dluhopisu“, návrh `docs/navrh-nahled-obchodu.md`). Tento úkol přidá totéž upozornění na formulář nástroje,
aby chyba byla vidět už při zakládání dluhopisu.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jednoduché neukládané pole, pohled, test) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-016-upozorneni-kalendar` (připravil Claude v `~/odoo-review`) |
| Řešitel | GitHub Copilot, režim Agent v okně na `~/odoo-review` |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-12 |
| Navazuje na | deník 2026-11-12 „Náhled zaúčtování obchodu a kalendář dluhopisu“, bod 3 návrhu |

**Cíl:** formulář nástroje druhu Dluhopis (`type_id.kind == 'bond'`) bez jediného toku na záložce Smluvní peněžní
toky ukáže nahoře žlutý pruh (`div class="alert alert-warning" role="alert"`) s textem:
„Dluhopis nemá kalendář toků: naběhlý úrok se v obchodech nepředvyplní a ocenění ho u pozice nepočítá.
Doplňte toky na záložce Smluvní peněžní toky.“
Pruh zmizí, jakmile nástroj má aspoň jeden tok (i jen jistinu: bezkupónový dluhopis je v pořádku).
Nic neblokuje, uložit jde vždy.

**Postup:**
1. V `addons/custom/investra_instruments/models/instrument.py`, třída `InvestraInstrument`: neukládané pole
   `calendar_missing = fields.Boolean(compute=…, string="Chybí kalendář toků")`, `@api.depends("type_id.kind", "cashflow_ids")`.
   Neměň nic jiného v souboru (třídu `InvestraTrade` a funkce účtování obchodu Claude právě upravil – červená zóna).
2. V `addons/custom/investra_instruments/views/instrument_views.xml`, záznam `view_instrument_form`: pruh jako první
   prvek uvnitř `<sheet>`, `invisible="not calendar_missing"`; pole `calendar_missing` přidej do formuláře neviditelné
   (`invisible="1"`), aby ho pruh mohl použít.
3. Test v `addons/custom/investra_instruments/tests/test_instrument.py`: dluhopis bez toků → `calendar_missing` True;
   po přidání toku Jistina → False; akcie bez toků → False. Styl převezmi z existujících testů v souboru.
4. `python3 tools/view_check/check_views.py` → „chyb: 0“. Testy Odoo nespouštěj (spouští Claude při převzetí).

**Rozsah souborů:** `addons/custom/investra_instruments/models/instrument.py` (jen nové pole a jeho výpočet ve třídě
`InvestraInstrument`), `addons/custom/investra_instruments/views/instrument_views.xml` (jen formulář nástroje),
`addons/custom/investra_instruments/tests/test_instrument.py` a sekce Výsledek v tomto souboru.

**Mimo rozsah:** verze v `__manifest__.py` (zvedá Claude), `investra_nav` (formulář obchodu, ocenění), třída
`InvestraTrade`, zakázané soubory podle `.agents/rules/10-zony.md`. Žádný zápis do databáze.

**Kritéria přijetí:**
- Pruh se ukáže jen u dluhopisu bez toků, zmizí po přidání toku; u jiných druhů nástroje nikdy.
- `check_views.py` bez chyb; nový test je v souboru a podle tvého posouzení projde (ověří Claude).
- Diff obsahuje jen soubory a části z Rozsahu.

## Výsledek

- **Změněné soubory:** `addons/custom/investra_instruments/models/instrument.py`, `addons/custom/investra_instruments/views/instrument_views.xml`, `addons/custom/investra_instruments/tests/test_instrument.py`.
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — zkontrolováno 15 souborů, chyb 0. Nový test ověřuje dluhopis bez toků, po přidání toku jistiny a akcii bez toků.
- **Neověřeno:** Testy Odoo nebyly spuštěny podle zadání; provede je Claude při převzetí.
- **Otevřené otázky a návrhy mimo rozsah:** Žádné.

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
