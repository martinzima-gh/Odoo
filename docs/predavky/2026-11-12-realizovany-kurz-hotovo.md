# Předávka 2026-11-12: realizovaný kurzový rozdíl – hotovo

**Cíl:** při prodeji a splátce nástroje v cizí měně oddělit realizovaný kurzový rozdíl od nerealizovaného.

**Stav:** větev `feature/nav-prototyp`, poslední commit viz `git log -1`. `investra_test` povýšena:
`investra_posting` 0.3.0, `investra_nav` 0.18.0 (záloha `zalohy/investra_test-2026-11-12-pred-realizovanym-kurzem.dump`,
předvaha a počet dokladů shodné), web 8071 restartován. Claude Doc rev 323.

**Hotovo (deník 12. 11. „Realizovaný kurzový rozdíl“):**
- Realizovaný kurz **proti pořizovací ceně**: průměrná pořizovací cena prodaných jednotek v měně nástroje ×
  (kurz prodeje − průměrný kurz nákupu); `valuation._cost_walk`. Potvrzeno uživatelem jako fakt.
- Varianta A: stejné role `gain_fx`/`loss_fx`, nový druh pohybu `fx_realised` (`investra_posting`); nerealizovaný kurz
  = zbytek kurzového rozdílu. Realizace ceny dál proti účetní hodnotě, nově kurzem prodeje či splátky
  (zrušena odchylka č. 4 v `docs/navrh-splatky-jistiny.md`). Pole v portfoliu ocenění uživatel nechce.
- Rozpad nevyžaduje vyhláška 501 ani ČNB (VYFO20_11 ř. 33 jeden řádek) – potvrdil uživatel; jen vnitřní informace.
- Testy: čistá DB, všechny vlastní moduly 484 testů 0 chyb (4 nové v `test_fair_value_interest.py`).
  `investra_test`: 289 testů, 8 známých chyb matice a workflow (řádky matice platné od 12. 11.), ostatní prošly.
- V `investra_test` není prodej ani splátka v cizí měně – na datech ověřeno jen testy.

**Zbývá – první krok:** SELECT realizovaného a nerealizovaného kurzu po nástrojích do `docs/sql`
(zelená zóna, může Antigravity přes zadání v `docs/ukoly/`).

**Otevřené body (výběr dalšího):** vypořádání obchodů přes peníze na cestě; nový kalendář s EIR; pohyblivá
sazba a PIK; poplatek placený fondu; přehled operací ke zpracování. Testovací dluhopis ve fondu Beta (tok 1. 1. 2029)
uživatel podle vlastních slov ověřil v UI.

**Otevřené otázky:** žádné nové.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (vybraný bod)
4. `addons/custom/investra_nav/models/valuation.py` (`_compute_portfolio`, `_cost_walk`, `_realised_ccy`)
