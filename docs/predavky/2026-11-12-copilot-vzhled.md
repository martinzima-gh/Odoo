# Předávka 2026-11-12: Copilot smí upravovat vzhled; další krok náhled zaúčtování

**Cíl:** uklidit cizí změny v `~/odoo-dev`, povolit Copilotovi vzhled v zelené zóně, vybrat další otevřený bod.

**Stav:** větev `feature/nav-prototyp`, commit „Copilot smí upravovat vzhled…“ (pushnuto). Moduly beze změny
(`investra_nav` 0.21.0). Claude Doc rev 327 (řádek v Přijatých rozhodnutích), `docs/architektura.md` zatím neexportován.

**Hotovo:**
- Necommitované změny vzhledu karet v `investra_dashboard` udělal Copilot v okně na `~/odoo-dev`; na pokyn uživatele smazány.
- Rozhodnutí „Copilot smí upravovat vzhled“ (deník + Claude Doc): jen zelená zóna (views, styly SCSS/CSS, `assets`
  v manifestu), jen `~/odoo-review`, bez commitu a pushe; každou úpravu zapíše do `docs/ukoly/CP-RRRR-MM-DD-tema.md`
  a řekne uživateli, ať ji Claude převezme. Upraveno `CLAUDE.md`, `.github/copilot-instructions.md`,
  `.agents/rules/10-zony.md` (styly do zelené zóny); testy guardu 29 OK.
- Návrh náhledu zaúčtování u splátek a úpisů/odkupů předložen (v chatu, viz níže), neprogramováno.

**Zbývá – první krok:** uživatel rozhodne o návrhu náhledu zaúčtování:
1. Varianta A (doporučeno): společný abstraktní model náhledu (tabulka dokladů, skutečné doklady se storny) pro obchod,
   splátku i úpis/odkup; B: kopie u každého modelu.
2. Splátky i úpisy/odkupy v jedné verzi `investra_nav` 0.22.0 (dva commity), nebo nejdřív jen splátky.
Podstata: splátka skládá řádky přímo v `_book()` (`instrument_accrual.py`) → vyjmout 1:1 do `_book_lines()`, kterou volá
zaúčtování i náhled; úpis/odkup už má `_book_lines()` (`movement.py`). Jen vypočítaná pole, bez migrace. Červená zóna.

**Otevřené otázky:** viz body 1 a 2. Případný záznam CP od Copilota převzít podle paměti „Převzetí Antigravity“.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `addons/custom/investra_nav/models/trade_preview.py`
4. `addons/custom/investra_nav/models/instrument_accrual.py` (třída `investra.instrument.repayment`, `_book`)
5. `addons/custom/investra_nav/models/movement.py` (`_book_lines`, `_book`)
