# ZJ-17 Účetní (hospodářský) rok fondu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, ocenění, NAV); plán schválil Martin 19. 11. 2026 |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (z `main` po sloučení ZJ-13, ZJ-14, AG-019 až AG-022) |
| Větev úkolu | `ukol/ZJ-07-dane-a-tridy` (celá dávka ZJ-07 až ZJ-19) |
| Zadal, dne | Claude (hlavní relace) podle dávky ze 19. 11. 2026, založeno 20. 11. 2026 |
| Navazuje na | `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`; deník 2026-11-19 (dávka ZJ-07 až ZJ-19) |
| Model | běh 2 (Sonnet 5.5), viz `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md` |

**Cíl:** Výpočty, které dnes začínají 1. 1. (daň, roční úplaty, období výkonnostní odměny, výkaz ČNB „od počátku roku“), začínají od začátku účetního období fondu podle knihy (`fund._fiscal_year_start`). Zdaňovací období = účetní období.

**Rozsah souborů:** `investra_fund` (fund.py), `investra_nav` (valuation.py, fee_rule.py, fee_scheme.py, pohledy, testy), `investra_cnb` (cnb_map.py), manuál.

**Mimo rozsah:** Změna konce účetního období po prvním zaúčtovaném ocenění (jen přes `account.fiscal.year` účetní); část roku jako ZIF.

**Kritéria přijetí:** Test `test_fiscal_year.py` (kniha 1. 7.–30. 6.: ocenění 31. 8. od 1. 7., daň se k 1. 7. nuluje, přechod 30. 6. → 31. 7.); kalendářní fondy beze změny (referenční scénáře, snímek 35 a 39); texty „od 1. 1.“ nahrazené; formulář fondu ukazuje Konec účetního období.

**Schválený plán:** `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 4 (s „Přednostmi“ a oddílem 1). Obsah se sem nekopíruje;
odchylky od něj se zapisují do Výsledku.

## Výsledek

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Odchylky od plánu:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
