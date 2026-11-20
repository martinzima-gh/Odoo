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

Běh 2 dávky (Claude Sonnet 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`. Plán: oddíl 6 zadání dávky.

- **Změněné soubory:** nový `investra_nav/models/trade_position.py` (společná `_position_events` přesunutá z ocenění, `_average_cost`, pole
  `average_cost_price`, `derecognition_price`, `derecognition_manual`, `derecognition_reason`, kontroly, `_prepare_derecognition`);
  `models/valuation.py` (`_cost_walk`, `_realised_ccy` s podílem pořizovací ceny); test `investra_nav/tests/test_derecognition.py` (12).
- **Ověřeno:** `investra_fund+`: 987 testů, 0 selhání; snímek ocenění 35 po povýšení kopie shodný. Příklad 10 ks à 100 + 10 ks à 120,
  prodej 5 ks à 130, cena 125: průměrně realizace 100 + přecenění 225; ručně 100 za kus realizace 150 + přecenění 175; součet 325 v obou
  (shodně v účetní knize v samostatných fondech). Zbytek pozice 15 ks s pořizovací cenou 1 700; důvod povinný; záporná cena; cena nad pozici
  a prodej celé pozice s ruční cenou = chyba při zaúčtování; storno; portfolio třídy B (realizace nese třídu B).
- **Neověřeno:** náhled očekávaného výsledku prodeje s ruční cenou (používá stejné funkce, bez vlastního testu); snímek 39 samostatně
  (v `tools/snimek_na_kopii.sh` se přepočítává jen 35).
- **Odchylky od plánu:**
  1. `tracking=True` na polích ceny a důvodu vynecháno: obchod není `mail.thread` (nemá chatter) a po zaúčtování se nemění; cena
     i důvod zůstávají na záznamu. Zámek po zaúčtování řeší `write` v `trade_position.py`.
  2. Cena vyskladnění 0 nebo prázdná = průměrná cena (import a API prodeje bez pole se chovají jako dosud); při zaúčtování se průměrná
     cena uloží do pole a příznak „ruční“ se přepočítá z aktuální průměrky (ne ze staré uložené hodnoty).
  3. Prodej celé pozice s upravenou cenou nejde (celá pořizovací cena odchází; zbytková cena bez kusů by zkreslila další nákup) –
     doplněná kontrola, v plánu nebyla.
  4. `_average_cost(…)` vrací `(kusy, pořizovací cena)`; `_realised_ccy` si pořizovací cenu pozice k minulému ocenění bere z ní.
  5. Formulář prodeje (B5) a manuál jsou v běhu 6.
- **Otevřené otázky a návrhy mimo rozsah:** –

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
