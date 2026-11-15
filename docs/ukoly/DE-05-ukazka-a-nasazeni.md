# DE-05 FX derivát: ukázka v datech, nasazení, SELECTy, návrh mapování ČNB

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (ukázková data, dokumentace); nasazení do `investra` jen se souhlasem Martina v promptu |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Sonnet |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Evidence, Příklad, Neověřeno a otevřené), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** v pracovní databázi je vidět FX swap přes dvě ocenění a je k němu dokumentace.

**Plán (od Clauda):**

1. `tools/demo_data/seed.py`: fond A (CZK) sjedná FX swap podle příkladu návrhu (data posunout tak, aby blízká noha
   byla vypořádaná a vzdálená otevřená přes dvě poslední ocenění); u jednoho ocenění ruční hodnota z banky s důvodem.
   Výsledky ostatních fondů se nesmí změnit (porovnat `docs/sql/24-pracovni-databaze.sql` před a po).
2. Nasazení: záloha `investra` do `zalohy/`, instalace `investra_derivative` a povýšení dotčených modulů, kontrola
   logu. Ukázku do stávající databáze doplnit přes ORM skriptem jen pro fond A; pokud by to znamenalo znovu otevřít
   zveřejněná ocenění, **zastavit se** a navrhnout Martinovi nové založení databáze (`run_seed.sh`).
3. `docs/sql/25-derivaty.sql`: smlouvy a nohy, RH po oceněních, zůstatky podrozvahy, kontrola MD = D (otestované SELECTy).
4. README modulu a `tools/demo_data/README.md`; uživatelský postup (sjednat, ocenit, zadat ruční hodnotu, vypořádat).
5. **Návrh** mapování rolí `derivative_liability`, `gain_derivative`, `loss_derivative` a podrozvahy do výkazů ČNB:
   hledat cíleně v `docs/cnb/` (grep), sepsat tabulku do Výsledku; `cnb_map.xml` neměnit (rozhodne etapa CN).

**Rozsah souborů:** `tools/demo_data/`, `docs/sql/25-derivaty.sql`, README, `docs/otevrene-body.md`, tento soubor, předávka.

**Mimo rozsah:** kód modulů, `cnb_map.xml`, mazání nebo nové založení databáze bez Martinova pokynu, SQL zápisy.

**Kritéria přijetí:** v `investra` je u fondu A swap s RH ve dvou oceněních; FK = aktiva − závazky u všech fondů
(SELECT); ostatní fondy beze změny; SELECTy běží pod `dbeaver_ro`; Martin dostane seznam, co projít v prohlížeči.

## Výsledek

Doplní provádějící relace.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí
