# ZJ-16 Poplatek obchodu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, ocenění, NAV); plán schválil Martin 19. 11. 2026 |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (z `main` po sloučení ZJ-13, ZJ-14, AG-019 až AG-022) |
| Větev úkolu | `ukol/ZJ-07-dane-a-tridy` (celá dávka ZJ-07 až ZJ-19) |
| Zadal, dne | Claude (hlavní relace) podle dávky ze 19. 11. 2026, založeno 20. 11. 2026 |
| Navazuje na | `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`; deník 2026-11-19 (dávka ZJ-07 až ZJ-19) |
| Model | běh 2 (Sonnet 5.5), viz `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md` |

**Cíl:** Obchod nese poplatek v libovolné měně: nákup FVTPL a každý prodej = náklad (nový analytický účet role `expense_bank_fee`), nákup v naběhlé hodnotě nebo FVOCI = součást pořizovací ceny (IFRS 9.5.1.1). Poplatek patří do kroku sjednání.

**Rozsah souborů:** `investra_instruments` (instrument.py), `investra_nav` (náhled, `_position_events`, naběhlá hodnota, testy), `investra_chart_fund` (účet + migrace), formulář obchodu (běh 6), `docs/sql`.

**Mimo rozsah:** Poplatky splátek (už existují), poplatky derivátů.

**Kritéria přijetí:** Test `test_trade_fee.py` (FVTPL USD s poplatkem v CZK, dluhopis AC s poplatkem v EUR – kapitalizace a průměrka, prodej, odložené vypořádání, storno, portfolio třídy B); obchod bez poplatku má stejný otisk dokladu; zastavit, když naběhlá hodnota nejde napojit na kapitalizovaný poplatek (E4).

**Schválený plán:** `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 5 (s „Přednostmi“ a oddílem 1). Obsah se sem nekopíruje;
odchylky od něj se zapisují do Výsledku.

## Výsledek

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Odchylky od plánu:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
