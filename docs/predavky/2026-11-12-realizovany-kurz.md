# Předávka 2026-11-12: realizovaný kurzový rozdíl zvlášť (zadání pro Claude)

**Cíl:** při prodeji a splátce nástroje v cizí měně oddělit realizovaný kurzový rozdíl od nerealizovaného,
aby výroční zpráva a výsledovka ukázaly po nástrojích realizovaný a nerealizovaný výsledek včetně kurzu.

**Stav:** větev `feature/nav-prototyp`, výchozí commit `36179a6`. Červená zóna (`investra_nav/models/valuation.py`) → dělá Claude,
plán schvaluje Martin. Antigravity až potom: SELECT do `docs/sql` (zelená zóna).

**Zjištění (kód, test; v `investra_test` není prodej v cizí měně, na datech neověřeno):**
- `_realised_ccy` počítá realizaci v měně nástroje, `valuation.py` ji násobí **kurzem dne ocenění** → `gain/loss_realised`.
- Kurzová složka prodaných kusů zůstává v `fx_effect` → jeden řádek `gain_fx`/`loss_fx`, druh pohybu „Přecenění kurzem“,
  smíchaná s nerealizovaným kurzem zbylých kusů. Nástroj a zařazení na řádku jsou.
- Vědomá odchylka č. 4 v `docs/navrh-splatky-jistiny.md` (řádek 199); návrh (ř. 168) chtěl realizovaný kurz na `gain_fx`/`loss_fx`.
- Příklad z `test_foreign_equity_realises_in_instrument_currency`: kurzový efekt 1 100 Kč = realizovaný 440
  (4 ks × 110 EUR × (26 − 25)) + nerealizovaný 660 (6 × 110 × 1). Dnes jeden řádek 1 100.
- Je-li kurz prodeje ≠ kurz ocenění, realizace kurzem ocenění přesouvá rozdíl mezi realizací a kurzem.

**Varianty (rozhoduje Martin, nejdřív se zeptat):**
- A) Nový druh pohybu „Realizovaný kurzový rozdíl“, stejné role `gain_fx`/`loss_fx` (616/716); výkazy ČNB beze změny.
  Realizaci přepočítat kurzem zaúčtování prodeje (`_position_events` už kurz vrací). **Doporučeno.**
- B) Nové role realizovaného kurzu (nové účty a mapování ČNB) – jen pokud to vyžaduje výkaz nebo auditor.
- C) Účtování beze změny, rozpad jen informativně v řádku portfolia ocenění (nové pole) a v SELECTu.

**Zbývá – první krok:** přečíst `valuation.py` ř. 340–520 a návrh část B, předložit Martinovi plán s variantou,
dopadem na doklady (druhy pohybu, částky na příkladu výše) a na existující testy; bez schválení neprogramovat.
Pak: změna + nové testy (cizí měna, kurz prodeje ≠ kurz ocenění, splátka jistiny, ztráta), `tools/run_tests.sh investra_nav`,
deník rozhodnutí + Claude Doc, ukázkový SELECT (může Antigravity podle zadání v `docs/ukoly/`).

**Otevřené otázky:** vyžaduje VYFO20_11 nebo příloha (IFRS 7) rozpad realizovaný/nerealizovaný kurz? Neověřeno – metodika
v `docs/cnb/`, citace IFRS v EUR-Lex, případně auditor.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `addons/custom/investra_nav/models/valuation.py` (ř. 340–520)
4. `docs/navrh-splatky-jistiny.md` (část B a Provedení)
5. `addons/custom/investra_nav/tests/test_fair_value_interest.py` (ř. 97–176)
