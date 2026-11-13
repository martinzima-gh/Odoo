# Předávka 2026-11-13: náhled zaúčtování u splátek, úpisů a odkupů

**Cíl:** náhled zaúčtování a záložka se skutečnými doklady i u splátky nástroje a úpisu/odkupu (varianta A, 0.22.0).

**Stav:** větev `feature/nav-prototyp`, commity 1b94276 (společný model, splátka) a 81837d2 (úpis/odkup), pushnuto.
`investra_nav` 20.0.0.22.0 bez migrace. `investra_test` **není povýšená** (čeká na souhlas uživatele). Claude Doc rev 330.

**Hotovo:**
- Abstraktní model `investra.posting.preview` (`models/posting_preview.py`): tabulka dokladů, skutečné doklady se storny,
  kostra záložky; přesun 1:1 z `trade_preview.py`, obchod ho dědí beze změny chování.
- Splátka: `_book_lines()` vyjmuta 1:1 z `_book()`; náhled volá i `_validate()` (chyba = upozornění v záložce).
- Úpis/odkup: kontroly z `_check_booking` přesunuté do `_booking_valuation()` bez zápisu; zápis vazby na ocenění zůstal.
- Oprava zobrazení: sloupec v cizí měně u zaúčtovaného dokladu jen u řádků v cizí měně (dřív i CZK řádky).
- Testy `tests/test_posting_preview.py` (10). Čistá DB, všechny vlastní moduly: 522 testů, 0 chyb; DB smazána.
  ERROR v logu je z `investra_rates` (`test_cron_publishes_downloaded_rates`, očekávaný log), ne regrese.
- Deník rozhodnutí, Claude Doc, otevřené body (bod uzavřen), `CLAUDE.md`.

**Zbývá – první krok:** se souhlasem uživatele povýšit `investra_test` na 0.22.0 (záloha, pak `ALLOW_UPGRADE=1
tools/run_tests.sh investra_nav`) a ověřit záložku Zaúčtování v UI u splátky a úpisu.
Pak: přepsat `docs/architektura.md` novým exportem Claude Doc (odloženo, zatím jen nový řádek rozhodnutí).

**Pozor:** ve stejné větvi souběžně commituje jiná relace (vzhled, `investra_vzhled`, 785b471, 8a86b4c).
Před commitem zkontrolovat `git log` a nesahat na její soubory.

**Otevřené otázky:** žádné.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `addons/custom/investra_nav/models/posting_preview.py`
4. `addons/custom/investra_nav/tests/test_posting_preview.py`
