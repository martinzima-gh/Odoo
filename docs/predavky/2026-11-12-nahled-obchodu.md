# Předávka 2026-11-12: náhled zaúčtování obchodu a kalendář dluhopisu

**Cíl:** ve formuláři obchodu ukázat očekávané zaúčtování a výsledek prodeje; upozornit na dluhopis bez kalendáře.

**Stav:** větev `feature/nav-prototyp`, poslední commit viz `git log -1`. `investra_test` povýšena:
`investra_instruments` 0.11.0, `investra_nav` 0.19.0 (záloha `zalohy/investra_test-2026-11-12-pred-nahledem-obchodu.dump`,
předvaha a počet dokladů shodné), web 8071 (`investra-test-web`) restartován. Claude Doc rev 324.

**Hotovo (deník 12. 11. „Náhled zaúčtování obchodu a kalendář dluhopisu“, návrh `docs/navrh-nahled-obchodu.md`):**
- Záložka Očekávané zaúčtování (návrh obchodu): doklady z `_planned_postings` (společná funkce se zaúčtováním)
  a u prodeje v RH odhad výsledku výpočtem ocenění s obchodem a bez něj (`investra_nav/models/trade_preview.py`).
- Upozornění na dluhopis bez kalendáře: formulář obchodu, kontrola ocenění `bond_calendar`, formulář nástroje (AG-016).
- AG-015 (SQL kurzových rozdílů, `docs/sql/22-kurzove-rozdily.sql`) a AG-016 převzaty od Copilota.
- Testy: čistá DB 494 testů, 0 chyb.
- Vypořádání obchodů přes peníze na cestě odloženo do pořízení Enterprise (otevřené body).
- Záložka Zaúčtování (deník „Zaúčtování ve formuláři obchodu“): obě zaúčtované nohy a náhled vypořádání,
  `investra_nav` 0.20.0, v `investra_test` povýšeno (záloha `zalohy/investra_test-2026-11-12-pred-zalozkou-zauctovani.dump`, předvaha shodná). Čistá DB 495 testů, 0 chyb.

**Data:** dluhopis Beta a návrh prodeje 5348 jsou zkusmo zadaná uživatelem naslepo – neřešit.

**Zbývá – první krok:** projít s uživatelem otázky v `docs/navrh-storno-obchodu.md` (storno a oprava obchodu,
pojistka kurzu vypořádání), po schválení provést. Podnět: obchod 5348 vypořádán s kurzem 10 070 (CZK) – neobnovovat,
opravit až stornem vypořádání.

**Otevřené body (výběr dalšího):** nový kalendář s EIR; pohyblivá sazba a PIK; poplatek placený fondu;
přehled operací ke zpracování.

**Otevřené otázky:** žádné nové.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-storno-obchodu.md`
4. `addons/custom/investra_instruments/models/instrument.py` (`InvestraTrade`: `write`, `_book`, `_settle`, `_planned_postings`)
5. `addons/custom/investra_nav/models/instrument_accrual.py` (storno splátky: `action_reverse`, `_do_reverse`, okno)
