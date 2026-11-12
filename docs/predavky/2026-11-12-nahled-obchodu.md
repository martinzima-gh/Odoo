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

**Zjištěno na datech (neopraveno, testovací data uživatele):** dluhopis Beta (id 466) má kalendář s jistinou
100 000 na kus, úrokem Ve splatnosti a úročením od 1. 1. 2019, nákupy jsou ale za 10 000 a 10 060 za kus.
Návrh prodeje 5348 (200 ks za 1 060) proto předvyplnil naběhlý úrok 7 868 493,15 a náhled ukazuje ztrátu −1 686 191,78.
Kalendář ovlivní i příští ocenění Bety (úrok pozice).

**Zbývá – první krok:** s uživatelem opravit kalendář a cenu dluhopisu Beta před zaúčtováním prodeje 5348 a před dalším oceněním.

**Otevřené body (výběr dalšího):** nový kalendář s EIR; pohyblivá sazba a PIK; poplatek placený fondu;
přehled operací ke zpracování.

**Otevřené otázky:** jistina na kus a výplata úroku dluhopisu Beta (rozhodne uživatel).

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-nahled-obchodu.md`
4. `addons/custom/investra_nav/models/trade_preview.py`
