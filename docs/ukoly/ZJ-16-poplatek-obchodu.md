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

Běh 2 dávky (Claude Sonnet 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`. Plán: oddíl 5 zadání dávky.

- **Změněné soubory:** `investra_instruments/models/instrument.py` (pole `fee_amount`, `fee_currency_id`, `fee_fx_rate`, `fee_treatment`,
  kontrola, `_fee_amounts`, `_capitalised_fee_ccy`, `_fee_account`, `_fee_lines`, `_fee_settlement_lines`, `_event_lines(with_fee)`,
  `_planned_postings`); `investra_nav/models/instrument_accrual.py` (`_accrued_value` z pořizovací ceny s poplatkem),
  `models/trade_position.py` (průměrka s poplatkem); `investra_chart_fund` (účet 615200 v šabloně, `EXTRA_ROLE_ACCOUNTS`,
  migrace `20.0.0.13.0`), `docs/osnova-fondu.md`; test `investra_nav/tests/test_trade_fee.py` (16).
- **Ověřeno:** `investra_fund+`: 987 testů, 0 selhání; snímek ocenění 35 po povýšení kopie shodný. Testy: FVTPL USD akcie s poplatkem v CZK
  (náklad, banka), poplatek v měně nástroje (kurz obchodu), poplatek ve třetí měně (kurz povinný), kapitalizace u vkladu v naběhlé
  hodnotě (poplatek v EUR; naběhlá hodnota vychází z ceny 1 000, ne 950; ocenění poplatek neodepíše – účet 615200 nulový), prodej s poplatkem
  (náklad, realizace beze změny), odložené vypořádání (poplatek proti nevypořádaným, vypořádání v bance včetně EUR), vypořádání ke dni
  vypořádání, storno, oprava, portfolio třídy B, obchod bez poplatku beze změny řádků.
- **Neověřeno:** poplatek u FVOCI (kapitalizace je v kódu, ocenění FVOCI je až v běhu 5); migrace `20.0.0.13.0` na kopii ze zálohy
  (zkouška až při povýšení v běhu 7, verze modulu se zatím nezvedla).
- **Odchylky od plánu:**
  1. Účet nákladů: **615200** „Poplatky za obchody s investičními nástroji“ jako další účet role `expense_bank_fee` (osnova 615,
     ČNB VYFO20_11 ř. 23 sčítá hlavní i další účty role – ověřeno v `cnb_map.xml` a `docs/cnb`). Chybějící účet v knize = chyba s návodem.
  2. Řádek nákladu poplatku je ve funkční měně; platba v cizí měně poplatku je řádek protiúčtu (banka / nevypořádané) s měnou.
  3. Částka kapitalizovaného poplatku v měně nástroje: je-li poplatek v měně nástroje, zadaná částka; jinak funkční částka / kurz obchodu.
     Při jiném kurzu poplatku než obchodu se průměrka počítá kurzem obchodu (rozdíl nejvýš v haléřích kurzové části pořizovací ceny).
  4. Vypořádání poplatku při odloženém vypořádání používá stejné funkční částky jako sjednání (bez kurzového rozdílu poplatku).
  5. E5 (formulář, seznam, náhled kolonky, XLS, SQL) je v běhu 6; náhled zaúčtování řádky poplatku už ukazuje (stejná funkce).
- **Otevřené otázky a návrhy mimo rozsah:** FVOCI poplatek se po ocenění do OCI „rozpustí“ do přecenění (běh 5, G).

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
