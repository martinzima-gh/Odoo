# Předávka 2026-11-11: testy přecenění v investra_test

**Cíl:** zjistit, proč v `investra_test` padá příprava testů přecenění, a databázi uvést do pořádku.

**Stav:** větev `feature/nav-prototyp`, poslední commit je ten s touto předávkou (pushnuto).

**Hotovo:**
- Příčina 1: čítač `res_company_id_seq` přerostl 10000 (testy zakládají společnosti, sekvence se nevrací);
  Odoo skládá id mapování kódu účtu jako účet × 10000 + společnost → MissingError. Čítač vrácen na 3363 (souhlas uživatele).
- Příčina 2: moduly byly v `investra_test` v 10:49 aktualizovány starším kódem, sloupec `max_rate_age_days`
  zůstal NOT NULL. Aktualizovány `investra_rates`, `investra_nav`, `investra_fx_revaluation` (souhlas uživatele).
- Testy: všech 363 testů modulů Investry v `investra_test` prošlo (post_install, bez `-u`).
- `investra_test_kontrola` smazána na pokyn uživatele; záloha `zalohy/investra_test-2026-11-11-pred-platnosti-kurzu.dump` zůstává.
- Postup kontroly čítače doplněn do `docs/prototyp-nav.md` (Spuštění testů); bod uzavřen v deníku.

**Zbývá – první krok:** plán bodu 15 (pak 8, 14, 16, 5.3, 3) z `docs/otevrene-body.md`.

**Dodatek:** na pokyn uživatele smazána složka příloh `investra_test_kontrola`; v `investra_dev` aktualizovány
`investra_rates` a `investra_fx_revaluation` (záloha před aktualizací v `zalohy/`). Otevřené otázky z této relace nezbývají.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (bod 15 a následující)
