# Předávka 2026-11-13: návrhy obchodů v pozicích

**Cíl:** do pozice fondu jen obchody s dokladem, ocenění se zastaví na obchodu bez dokladu (varianta B, závažnost stop).

**Stav:** větev `feature/nav-prototyp`, commit e7c3cf5 (pushnuto). `investra_instruments` 0.13.0, `investra_nav` 0.23.0,
bez migrace. Claude Doc rev 331, `docs/architektura.md` je jeho export.

**Hotovo:**
- `_recognised()` v `investra_instruments/models/instrument.py`: podmínka `event_id != False`; stejně `_holdings_without_self()`.
- `_check_sale()`: jen obchody po Zaúčtovat (`state not in draft, reversed`), úmyslně jinak než pozice (fond s pozicí
  od data vypořádání má doklad nákupu až při vypořádání). Kontrola běží při uložení, prodej proti návrhu nejde uložit.
- Kontrola ocenění `trades_booked` „Obchody k datu jsou zaúčtované“ (stop) ve `valuation.py` za `trades_settled`.
- Testy: 6 nových v `test_trade_recognition.py`; 5 stávajících testů zaúčtuje obchod před prodejem/splátkou/pozicí.
  Čistá DB, všechny vlastní moduly: 528 testů, 0 chyb (ERROR `investra_rates` je očekávaný log); DB `investra_ci_navrhy` smazána.
- Deník rozhodnutí, otevřené body (bod uzavřen, „Přehled operací“ doplněn), Claude Doc.
- Mezitím relace vzhledu převzala CP-2026-11-13 (commit 5e15343, jen `investra_theme`); nic dalšího k převzetí.

- `investra_test` povýšena se souhlasem (záloha `zalohy/investra_test-2026-11-13-pred-navrhy-obchodu.dump`):
  doklady 78, řádky 192, součty MD/D, obchody a stavy ocenění shodné před a po; testy 359, selhání jen známá
  (5× „cannot approve“ ceny kvůli ručnímu řádku matice 82, 3× `TestApprovalMatrix` kvůli řádku 83). Web 8071 restartován,
  přechodná chyba registru při startu (websocket), pak log čistý.

**Zbývá – první krok:** navrhnout uživateli další otevřený bod z `docs/otevrene-body.md` s doporučením
(např. „Sdílené nástroje bez pravidla společnosti“, „Oddělení uživatelů podle fondů“ nebo „Přehled operací ke zpracování“);
zeptat se, pak plán. Případné nálezy uživatele z UI (záložka Zaúčtování, kontrola trades_booked) opravit jako první.

**Rozhodnutí:** 2026-11-13 „Návrhy obchodů v pozicích“ (varianta B, stop).

**Otevřené otázky:** žádné.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `addons/custom/investra_instruments/models/instrument.py` (jen `_check_sale`, `_recognised`)
4. `addons/custom/investra_nav/tests/test_trade_recognition.py` (konec souboru)
