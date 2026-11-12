# Předávka 2026-11-12: splátky nástrojů – jistina, mimořádná splátka, návrhy podle kalendáře

**Cíl:** jeden mechanismus splátky pro naběhlou i reálnou hodnotu, mimořádná splátka a kalendářní splátky bez ručního zadání.

**Stav:** větev `feature/nav-prototyp`, poslední commit s kódem a dokumentací viz `git log -1`; `investra_test` má
`investra_entity`, `investra_chart_fund`, `investra_cnb` 0.6.0 a `investra_nav` 0.14.0, web 8071 restartován.

**Hotovo (návrhy `docs/navrh-splatky-jistiny.md`, `docs/navrh-mimoradna-splatka.md`, deník 12. 11.):**
- Splátka: jistina, úrok, poplatek (MD 612000); MD 119100 Inkasa na cestě (nová role) / D nástroj; výpis 119100 vynuluje.
- Výběr jen držených nástrojů, model z nákupu (`force_save`), zbývající jistina před/po, předvyplnění z kalendáře
  (změna data nepřepíše ručně zadané částky). Jistina snižuje kusy; ocenění doúčtuje na nulu i pozici bez kusů.
- Druhy Podle kalendáře / Mimořádná; mimořádná = poměrné snížení (koeficient, původní EIR), se zaškrtnutým
  Uzavírá pozici ukončí pozici (upozornění na neuhrazenou jistinu, zbytek zatím do úroků).
- Denní úloha + tlačítko „Návrhy podle kalendáře“ zakládají návrhy splátek; ocenění upozorní na splatný tok bez
  zaúčtované splátky („v návrhu“ / „chybí“). Testy na čisté DB `investra_nav` 240, 0 chyb; v `investra_test` 8 známých
  chyb testů matice (řádky 81 a 82 platné od 12. 11.).
- Zálohy v `zalohy/investra_test-2026-11-12-pred-*.dump` (poslední `pred-navrhy-splatek`, 12:00). Doc rev 318.

- 0.14.0: tlačítko Návrhy podle kalendáře má okno s datem Návrhy do (návrhy i předem; deník „Návrhy splátek předem“),
  241 testů 0 chyb, záloha `pred-navrhy-predem`, předvaha po upgradu shodná. Doc rev 319.

**Zbývá – první krok:** uživatel zkouší v UI na 8071 (fond Delta, vklad: všechny splátky stornované, návrh do 15. 12.
vyjde 5 000 000 + 45 500). Návrh etapy 2 (část A naběhlý úrok v RH, B realizovaný výsledek, 5 otázek) je v chatu
12. 11.; čeká na odpovědi, pak zapsat do `docs/navrh-splatky-jistiny.md`. Pak etapa 2 z `docs/navrh-splatky-jistiny.md`: naběhlý úrok u úročených nástrojů v RH
v ocenění a realizovaný výsledek při splacení/prodeji v RH.

**Otevřené body:** nový splátkový kalendář s uloženou EIR; ověřit citace IFRS 9 / IAS 1 a prezentaci zbytku při ukončení
(auditor); poplatek placený fondu (výnos); vypořádání obchodů přes peníze na cestě; přehled operací ke zpracování
(dashboard, zatím jen evidovat zdroje).

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-splatky-jistiny.md` (Etapy, Provedení)
4. `addons/custom/investra_nav/models/instrument_accrual.py`
5. `addons/custom/investra_nav/models/valuation.py` (`_compute_portfolio`, `_closed_positions`)
