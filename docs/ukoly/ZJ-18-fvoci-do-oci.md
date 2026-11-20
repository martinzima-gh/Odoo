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

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Odchylky od plánu:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
