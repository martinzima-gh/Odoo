# Běh 2 – Sonnet 5.5 (úsilí high): účetní období, poplatek obchodu, cena vyskladnění (logika)

```
Přečti CLAUDE.md, předávku běhu 1 a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen „Přednosti“ a oddíly 4, 5 a 6.
Větev ukol/ZJ-07-dane-a-tridy. Schváleno; návrhy kódu nespuštěné – převezmi, uprav, otestuj, odchylky do Výsledku ZJ-17/16/15.
POŘADÍ: 4 (F1, F2, F3 jen texty v Pythonu, F5 testy; období odměny podle účetního období) → 5 (E1 pole a kontroly, E2–E4
zaúčtování a průměrka, nový účet poplatků v šabloně + migrace chart_fund, E6 testy) → 6 (B1 sdílená průměrka – přesun
_position_events na investra.trade, B2 pole prodeje a kontroly, B3 ocenění, B4 testy).
MIMO ROZSAH (Copilot v běhu 6): F4 pole na formuláři fondu, F3 popisky v XML, E5 formulář/seznam obchodu, B5 formulář prodeje, manuál, SQL.
OVĚŘ podle zadání (E4 naběhlá hodnota s kapitalizovaným poplatkem – když nejde čistě, zastav se).
Po každém oddílu testy investra_fund+, investra_instruments+, investra_nav+, investra_cnb+ a snímek 35/39 = beze změny. Když stejný
test dvakrát po opravě neprojde, nezkoušej dál: commitni hotové, popiš problém a skonči (převezme Opus).
Commit po bodech, push, předávka …-davka-beh-2.md se seznamem nových polí pro Copilota. V relaci 2 pokračuj rovnou dalším během; zprávu (commity, odchylky, testy) napiš až na konci relace.
```
