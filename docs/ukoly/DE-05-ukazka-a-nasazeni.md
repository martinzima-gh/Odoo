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

Provedla hlavní relace 16. 11. 2026 (Sonnet), větev `etapa/derivaty`. **Nasazení hotové, ukázka v `investra` NEdoplněna** (viz Otevřené).

- **Změněné soubory:** `tools/demo_data/seed.py`, `tools/demo_data/README.md`, `docs/sql/25-derivaty.sql` (nový),
  `addons/custom/investra_derivative/README.md` (nový), `docs/otevrene-body.md`, tento soubor, předávka.
- **Ověřeno (příkaz a výsledek):**
  - Záloha `investra` → `zalohy/investra-2026-11-16-pred-DE05.dump` (8,7 MB, `pg_restore -l` 10 742 položek).
  - Zkouška migrace na dočasné kopii ze zálohy: `-u investra_chart_fund,investra_entity -i investra_derivative` → konec 0,
    moduly `installed` (chart_fund 20.0.0.9.0, entity 20.0.0.9.0, derivative 20.0.0.3.0); jediný ERROR v logu je starý
    formát popisu `investra_instrument_master` (rst), ne z těchto modulů.
  - Stejný příkaz na `investra` (instance zastavena a znovu spuštěna): konec 0, bez chyb z modulů, http://127.0.0.1:8071 → 200,
    15 rolí derivátů a podrozvahy v `investra_account_role`. Logy `.test-logs/de05-*.log`.
  - Ukázka: seed na nové dočasné databázi (základ = seed před úpravou, nový = po úpravě), obě smazány. Fondy B–E mají
    shodné FK i výsledek SQL 24; u A přibylo zařazení swapu a změnila se aktiva, výsledek a FK (30. 9.: 103 426 061,64 → 103 427 672,55).
  - Swap `FX-SWAP-A-001`: RH vzdálené nohy 30. 9. 31 112,90 (zveřejněné ocenění), 31. 10. spočtená 120 612,90, ruční z banky
    123 112,90 (rozdíl 2 500,00 v toleranci), změna do výsledku 92 000,00. Zisk 30. 9. 1 612,90 = −29 500 (blízká noha) + 31 112,90.
  - `docs/sql/25-derivaty.sql`: všech 8 dotazů běží (na `investra` pod `dbeaver_ro`, na dočasné kopii se swapem pod vlastníkem);
    MD = D (0 nevyrovnaných dokladů), součet podrozvahy 0,00, FK = aktiva − závazky u všech 5 fondů (rozdíl 0,00).
- **Neověřeno:** swap v prohlížeči (v `investra` není); testy Odoo jsem po úpravě seedu nespouštěl (kód modulů beze změny,
  poslední běh 733 testů bez chyb); dotaz 3 u zveřejněného 30. 9. ukazuje „zaúčtováno před“ = RH, protože RH smlouvy
  zaúčtoval už doklad vypořádání blízké nohy – změna v ocenění je 0 (chování modulu, ne chyba).
- **Otevřené otázky a návrhy mimo rozsah:**
  - **Rozhodnutí Martina:** ukázka v `investra` – swap přes dvě ocenění nejde doplnit bez znovuotevření zveřejněných ocenění
    fondu A (zveřejněné je jen do 30. 9., rozpracované jen 31. 10.). Varianty: (a) nové založení `investra` přes
    `run_seed.sh` po záloze (doporučuji; zruší ruční změny v `investra`, nové ukázky se pak vezmou ze seedu),
    (b) swap zadat ručně v UI s jediným oceněním 31. 10. Zapsáno v `docs/otevrene-body.md`.
  - Seznam k projití v prohlížeči (po volbě a): Portfolio → Deriváty → FX-SWAP-A-001 (nohy, stav Sjednáno, blízká Vypořádaná,
    záložka dokladů); Fond A → ocenění 30. 9. a 31. 10. (záložka Deriváty, ruční hodnota, kontroly `derivative_*`, náhled
    zaúčtování); Nastavení fondu: tolerance 0,10 %; účty 313200, 719200, 953200, 954200, 992000 v knize fondu A.
  - **Návrh mapování do výkazů ČNB** (`cnb_map.xml` neměněn, rozhodne etapa CN; řádky ověřeny v `polozky-FOFI20261201.csv`):

| Role | List a řádek ČNB (navrhuji) | Poznámka |
|---|---|---|
| `derivative`, `derivative_swap` (kladná RH) | ROFO10_11 ř. 5 „Finanční aktiva k obchodování“; RIS30_01 ř. 17 „Finanční deriváty – kladná reálná hodnota“ | stejně jako stávající `derivative`; FX swap a forward jsou k obchodování |
| `derivative_liability`, `derivative_swap_liability` (záporná RH) | ROFO10_21 ř. 4 „Deriváty k obchodování“; RIS30_03 ř. 7 „Finanční deriváty – záporná reálná hodnota“ | znaménko −1 jako ostatní pasiva; dnes pro deriváty žádný řádek nemapujeme |
| `gain_derivative`, `gain_derivative_swap`, `loss_derivative`, `loss_derivative_swap` | VYFO20_11 ř. 29 „Zisk nebo (-) ztráta z finančních aktiv a závazků k obchodování“ | konzistentní s řádkem 5 aktiv; výklad u nových derivátů bez vypořádání je v `mapovani.md` označen k potvrzení u ČNB |
| `fx_spot_asset`, `fx_spot_liability` | ROFO10_11 ř. 24 „Ostatní aktiva“ a ROFO10_21 ř. 26 „Ostatní závazky“; RIS30_01 ř. 18 / RIS30_03 ř. 8 | spot do 2 dnů není derivát (ČÚS 110 bod 1 c)) |
| `gain_fx_spot`, `loss_fx_spot` | VYFO20_11 ř. 33 „Kurzové rozdíly – zisk nebo (-) ztráta“ | ČÚS 105 bod 3 |
| role Podrozvaha (`offbalance_*`) | **neurčeno**: ROFO10_31 má jen poskytnuté přísliby a záruky (sloupec jmenovitá hodnota podrozvahových nástrojů) | jmenovitá hodnota FX derivátů v ROFO10_31 nepatří; hledat v DOFO31_22 (sloupce o reálné hodnotě, ne nominále) nebo potvrdit u ČNB; do té doby mimo výkaz |

  - Neověřeno u mapování: shoda řádků s věcným výkladem metodiky (jen názvy položek), mapování podrozvahy a to, zda se FX swap
    vykazuje v DOFO31_22 (po smlouvách) – navazuje na otevřený bod mapování rolí v předávce. Po schválení zrušit výjimku v
    `addons/custom/investra_cnb/tests/test_cnb_map.py` (`test_every_chart_role_is_mapped`).

## Převzetí
