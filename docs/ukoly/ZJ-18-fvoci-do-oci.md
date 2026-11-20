# ZJ-18 FVOCI do OCI a daň z OCI

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, ocenění, NAV); plán schválil Martin 19. 11. 2026 |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (z `main` po sloučení ZJ-13, ZJ-14, AG-019 až AG-022) |
| Větev úkolu | `ukol/ZJ-07-dane-a-tridy` (celá dávka ZJ-07 až ZJ-19) |
| Zadal, dne | Claude (hlavní relace) podle dávky ze 19. 11. 2026, založeno 20. 11. 2026 |
| Navazuje na | `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`; deník 2026-11-19 (dávka ZJ-07 až ZJ-19) |
| Model | běh 5 (Opus 5.5), viz `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md` |

**Cíl:** Pozice FVOCI: úrok efektivní mírou a ECL do výsledku (ECL ručním dokladem), zbylé přecenění do OCI (role `revaluation_reserve`); akcie bez recyklace (převod do „Realizované přecenění FVOCI“), dluh s recyklací. Odložená daň z OCI a splatná daň z realizace akcií přes daňová pravidla ZJ-07 (D8–D11). Uzavírá otevřený bod „Účtování FVOCI“.

**Rozsah souborů:** `investra_entity` (role), `investra_chart_fund` (účty, migrace), `investra_nav` (valuation, nevypořádané obchody, list portfolia, testy), `investra_cnb` (mapování), manuál.

**Mimo rozsah:** Poziční přechodný rozdíl (původní C10, zrušen); automatický výpočet ECL.

**Kritéria přijetí:** Test `test_fvoci.py` (příklady G2 akcie i dluh, CZK i USD; nevypořádaný obchod; portfolio třídy B; ruční ECL; daň 1,45 / 1,95); fond bez FVOCI beze změny; před oddílem zjistit pozice FVOCI v `investra` a zastavit se s jejich výčtem.

**Schválený plán:** `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 8 (s „Přednostmi“ a oddílem 1). Obsah se sem nekopíruje;
odchylky od něj se zapisují do Výsledku.

## Výsledek

Běh 4 (Sonnet 5.5): role `revaluation_reserve`, `revaluation_reserve_tax`, účty 564300, 564400, 564500, 571100, 667500, mapování ČNB
(viz ZJ-07, Výsledek běhu 4). Běh 5 (Claude Opus 5.5, 20. 11. 2026): ocenění a daň.

- **Před oddílem G:** SELECT v `investra` – 0 zařazení FVOCI (amortised 7, fvtpl 12) → bez zastávky.
- **Změněné soubory:** `investra_nav/models/valuation.py` (`_fvoci_position`, `_fvoci_debt`, `_fvoci_reserve`, `_fvoci_accounts`,
  `_portfolio_row`, uzavřená pozice se zbylou rezervou v `_closed_positions`, nevypořádaný obchod FVOCI do OCI, pole `oci` na řádku listu
  portfolio), `models/instrument_accrual.py` (`_accrued_value(…, weights)`), testy `test_fvoci.py` (nový, 13), `test_trade_recognition.py`
  (nevypořádaný FVOCI: dřív stop, teď OCI), `test_accrual.py` (dluhopis s přepsanou kategorií FVOCI dostal kalendář).
- **Ověřeno:** `test_fvoci.py` – příklady G2 akcie (101 → 130 → OCI 29 → prodej 140 → 571100 39, výsledek 0) a dluh (985/990 → úrok 5,
  OCI 5 → prodej 995 při 987 → úrok 2, realizace 8, OCI 0), USD akcie (kurz do OCI) a dluh (kurz z naběhlé hodnoty 1 960 do výsledku,
  OCI 110), skutečná naběhlá hodnota efektivní mírou, nevypořádaný obchod, portfolio třídy B, ruční ECL, FVTPL beze změny, daň
  1,45 → 0 a 1,95, dluh 0,25/0,25 → 0,75/0, FVTPL 1,50. Snímek 35/39 shodný. Výsledky testů v předávce běhu 5.
- **Neověřeno:** pozice FVOCI na skutečných datech (v `investra` žádná není); částečný prodej dluhu FVOCI s více nákupy a splátkami
  jistiny jen výpočtem (váhy nákupů), bez testu.
- **Odchylky od plánu:**
  1. Rezerva nese u cizoměnové pozice i částku v měně nástroje (`amount_currency`), aby se u dluhu oddělila změna v měně od kurzu:
     kurz z naběhlé hodnoty do výsledku, kurz z rezervy do OCI. Akcie: základ je pořizovací cena ve funkční měně → celý kurz do OCI.
  2. Úrok dluhu FVOCI = zbytek − realizace − kurz (žádný samostatný řádek `_fair_value_interest`); naběhlý úrok se počítá jen do hodnoty
     dluhopisu s cenou bez úroku. Realizace = výnos prodeje včetně naběhlého úroku − podíl naběhlé hodnoty prodaných kusů ke dni prodeje.
  3. Naběhlá hodnota po prodeji: `_accrued_value` s váhami nákupů (prodej průměrem snižuje každý nákup stejným podílem). Bez vah dál platí
     „po prodeji není podporovaná“ (naběhlá hodnota AC).
  4. Dluh FVOCI potřebuje kalendář toků; bez něj ocenění skončí chybou „Nástroj nemá smluvní peněžní toky“ (jako AC).
  5. Pozice bez kusů se zbylou rezervou (prodej přesně za účetní hodnotu) se bere jako uzavřená a rezervu převede.
  6. Nevypořádaný obchod: protiúčet změny RH je rezerva; ocenění portfolia od zůstatku rezervy pozice odečte zůstatek účtu změny RH
     nevypořádaných obchodů, aby se nevypořádaná část nepočítala dvakrát.
  7. Sloupec „Oceňovací rozdíl (OCI)“ (`oci`) = cílová rezerva pozice k datu (kumulativně), ne pohyb.
  8. Přemostění tříd a XLS beze změny kódu: OCI je v řádku nástroje (aktivum), proto je součást společné / ostatní specifické změny.
- **Otevřené otázky a návrhy mimo rozsah:** ČNB rozdělení ř. 35/40 (z běhu 4); daň z realizace akcií FVOCI ve výsledku vs. kapitálu
  (IAS 12.61A); test částečného prodeje dluhu FVOCI s více nákupy (návrh běh 7).

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
