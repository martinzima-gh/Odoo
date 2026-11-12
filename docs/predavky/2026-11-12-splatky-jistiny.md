# Předávka 2026-11-12: splátky jistiny nástrojů – etapa 1

**Cíl:** jeden mechanismus splátky pro naběhlou i reálnou hodnotu (návrh `docs/navrh-splatky-jistiny.md`, schválen 12. 11.).

**Stav:** větev `feature/nav-prototyp`, commit `7b1c27b` (kód) + tato předávka.

**Hotovo:**
- Role Inkasa na cestě 119100 (`investra_entity` 0.6.0, `investra_chart_fund` 0.6.0 s migrací, `investra_cnb` 0.6.0).
- `investra_nav` 0.10.0: jistina + úrok, MD 119100 / D nástroj; výběr jen držených nástrojů, model z nákupu,
  zbývající jistina před/po, předvyplnění z kalendáře; přeplacení a mimořádná splátka v naběhlé hodnotě odmítnuty.
  Jistina snižuje kusy (`_holdings`), ocenění doúčtuje na nulu i pozici bez kusů se zůstatkem.
- Bod 5 bez migrace obchodů (jistina na jednotku z kalendáře). Testy: čistá DB `investra_ci_jistina` 455 testů,
  `investra_nav` 229, 0 chyb. Migrace ověřena na kopii `investra_ci_migrace` (předvaha a doklady shodné).
- Záloha `zalohy/investra_test-2026-11-12-pred-splatkami-jistiny.dump` (10:11). Deník, otevřené body, Doc rev 313.

**Provedeno po předávce (souhlas uživatele):** nová záloha `zalohy/investra_test-2026-11-12-pred-splatkami-jistiny.dump`
(10:15); upgrade `investra_test` (entity, chart_fund, cnb 0.6.0, nav 0.10.0) – předvaha a doklady shodné, změnilo se jen
mapování 119100 na roli Inkasa na cestě; web 8071 restartován; smazány DB a přílohy `investra_ci_jistina`, `investra_ci_migrace`.

**Zbývá – první krok:** zkouška splátky v UI na 8071 (fond Delta, vklad: splátky 239, 240, 242 jsou stornované).
Pak etapa 2: naběhlý úrok u úročených nástrojů v RH v ocenění a realizovaný výsledek při splacení/prodeji v RH.

**Otevřené otázky:** mimořádná splátka v naběhlé hodnotě (auditor); vypořádání obchodů přes peníze na cestě.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-splatky-jistiny.md` (Rozhodnutí, Etapy, Provedení)
4. `addons/custom/investra_nav/models/instrument_accrual.py`
5. `docs/sql/16-splatky.sql`
