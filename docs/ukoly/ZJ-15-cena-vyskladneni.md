# ZJ-15 Cena vyskladnění na prodeji

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, ocenění, NAV); plán schválil Martin 19. 11. 2026 |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (z `main` po sloučení ZJ-13, ZJ-14, AG-019 až AG-022) |
| Větev úkolu | `ukol/ZJ-07-dane-a-tridy` (celá dávka ZJ-07 až ZJ-19) |
| Zadal, dne | Claude (hlavní relace) podle dávky ze 19. 11. 2026, založeno 20. 11. 2026 |
| Navazuje na | `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`; deník 2026-11-19 (dávka ZJ-07 až ZJ-19) |
| Model | běh 2 (Sonnet 5.5), viz `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md` |

**Cíl:** Prodej ukazuje průměrnou pořizovací cenu k datu sjednání a nese cenu vyskladnění za kus (předvyplněná průměrem, přepsatelná s důvodem). Ocenění bere pořizovací cenu prodaných kusů z ní; součet realizace a přecenění za pozici se nemění.

**Rozsah souborů:** `investra_instruments` / `investra_nav` (pole prodeje, společná průměrka, `_cost_walk`, `_realised_ccy`, testy), formulář prodeje (běh 6), manuál.

**Mimo rozsah:** Jiné metody než průměr (FIFO apod.).

**Kritéria přijetí:** Test `test_derecognition.py` (výchozí cena = dnešní výsledek; ruční cena → jiná realizace i přecenění, stejný součet; cena nad pozici → chyba; důvod povinný; storno; portfolio třídy); bez ruční úpravy snímek 35 a 39 beze změny.

**Schválený plán:** `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 6 (s „Přednostmi“ a oddílem 1). Obsah se sem nekopíruje;
odchylky od něj se zapisují do Výsledku.

## Výsledek

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Odchylky od plánu:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
