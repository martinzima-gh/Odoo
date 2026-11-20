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

Běh 2 dávky (Claude Sonnet 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`. Plán: oddíl 4 zadání dávky.

- **Změněné soubory:** `investra_fund/models/fund.py` (`_fiscal_year_dates`, `_fiscal_year_start`); `investra_nav/models/valuation.py`
  (`_year_start`, začátek roku daně v `_tax_item`, krystalizace „ročně“, texty chyb), `models/fee_rule.py` (kontrola archivace pravidla,
  nápovědy), `models/fee_scheme.py` (model náhledu na účetní období), `engine.py` (jen komentáře); `investra_cnb/models/cnb_map.py`
  (výkaz „od začátku účetního období“); testy `investra_nav/tests/test_fiscal_year.py` (7), `investra_cnb/tests/test_cnb_map.py` (1).
- **Ověřeno:** `tools/run_tests.sh investra_fund+` (alokace, ČNB, deriváty, instrumenty, NAV …): 959 testů, 0 selhání (po oddílu 4),
  987 / 0 po oddílech 5 a 6. Snímek ocenění 35 po povýšení kopie `investra` (`tools/snimek_na_kopii.sh`) shodný se snímkem před dávkou.
  Testy: kniha s obdobím 1. 7. – 30. 6.: daň se v novém období nuluje (ztráta od 1. 7. neuvolní daň minulého období, přes Nový rok
  uvnitř období se počítá kumulativně), krystalizace „ročně“ až 30. 6., průměrný FK od začátku období a bez úplat z minulého období,
  ČNB řádek od začátku období; kalendářní kniha beze změny.
- **Neověřeno:** referenční scénáře s fondem s nekalendářním obdobím neexistují (jen testy výše); XML pohledy a manuál (běh 6).
- **Odchylky od plánu:**
  1. Odoo 20 Community nemá záznamy `account.fiscal.year` (jen Enterprise); zdrojem je `res.company.fiscalyear_last_day/month`
     (`compute_fiscalyear_dates`). První zkrácené nebo prodloužené období se tím nepodporuje.
  2. Krystalizace „měsíčně“ a „čtvrtletně“ zůstala kalendářní (čtvrtletí 3/6/9/12): plán mění jen „ročně“ (poslední den účetního období).
  3. `engine.year_fraction` beze změny podle plánu. Výkaz ČNB: ověřeno v `docs/cnb` (pole „Zisk nebo ztráta za běžné účetní období“).
  4. F3 (texty) hotové v Pythonu; texty v XML (pohledy, nápovědy), F4 (pole Konec účetního období na fondu) a manuál
     (`docs/manual/04`, `09`) jsou v běhu 6; sloupec výjimek daně „Pohyb od začátku období“ vznikne s modelem výjimek (běh 4 a 6).
- **Otevřené otázky a návrhy mimo rozsah:** změna konce účetního období po zaúčtovaném ocenění (zatím nic nehlídá; nastavení účetnictví).

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
