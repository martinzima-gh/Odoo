# ZJ-09 Portfolio a bankovní účet společné, nebo jen pro třídu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování obchodů, ocenění, úroků, derivátů, kurzové přecenění, alokace); nejdřív plán, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-08) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Opus 5.5 |

**Kontext:** obchody, pozice ani smlouvy derivátů dnes třídu nenesou, takže položky jen pro třídu (např. měnové zajištění třídy) se do ΔT nedostanou.
Pole `class_id` na `investra.instrument` je ve formuláři, ale nic ho při účtování nepoužívá. Pozice se už vedou po dvojici nástroj a portfolio
(`investra.trade._holdings`); ocenění, naběhlé úroky i uzavírání pozic pracují po této dvojici; smlouva derivátu má portfolio.

**Rozhodnuto 17. 11. 2026 (Martin), deník „Třída portfolia“:** portfolio fondu má pole **Třída** – prázdné = společné portfolio (dělí se mezi třídy
podílející se na výsledku, viz ZJ-08), vyplněné = portfolio jen této třídy. Stejný nástroj může být ve společném portfoliu i v portfoliu třídy.
Nahrazuje varianty A, A2 a B z otevřeného bodu „Obchody a pozice na třídu“.
Martin potvrdil 17. 11. 2026 a doplnil: **i bankovní účet může být specifický pro třídu** (deník „Bankovní účet třídy“). Bankovní deník fondu má pole Třída
se stejným významem; řádky na jeho účtu nesou třídu. Platba mezi bankou třídy a společným majetkem (nebo portfoliem jiné třídy) jde přes vnitřní zúčtování.
Portfolio i bankovní účet jsou **buď společné pro všechny třídy, nebo pro jednu třídu**; přiřazení skupině tříd není (pole Třída je jedna hodnota).

**Plán má obsahovat:**
1. Pole Třída na `investra.fund.portfolio` (doména na třídy fondu), zámek po prvním obchodu (`_has_trades`) a po prvním dokladu derivátu.
2. Doplnění `class_id` na rozvahové řádky: obchod (nákup, prodej, vypořádání), storno a oprava obchodu, ocenění pozic, naběhlý úrok, splátky,
   deriváty (forward, swap, spot, obě nohy, podrozvaha). Peníze přes vnitřní zúčtování (`internal_clearing`); banka bez třídy zůstává společná (bod 2b).
2b. Bankovní účet třídy: pole Třída na bankovním deníku fondu (`account.journal`, typ banka), zámek po prvním pohybu; třída na řádcích bankovního účtu
   z plateb, výpisů a vypořádání obchodů; automatické vnitřní zúčtování, když se třída banky liší od třídy protistrany (společné portfolio, jiná třída);
   úpisy a odkupy třídy z IS (vypořádání na banku třídy i na společnou banku); párování výpisů. Varianty a doporučení, kde vnitřní zúčtování vzniká
   (při zaúčtování dokladu obecně, nebo v každém zdroji zvlášť).
2c. Každý bankovní účet = vlastní analytický účet hlavní knihy (deník banky, `default_account_id`). Dnes obchody, úpisy a odkupy účtují vždy na hlavní
   účet role `bank` (221100), jen deriváty vybírají podle měny. Nově: obchod, úpis, odkup, vypořádání derivátu a platba úplaty mají pole Bankovní účet
   (deník), předvyplněné podle třídy a měny – obchod podle třídy portfolia, úpis a odkup podle upisované třídy; účet třídy v měně, jinak společný účet
   v měně; víc kandidátů → první podle pořadí deníků, před zaúčtováním jde změnit. IS číslo účtu fondu posílat nemusí. Třída bankovního řádku = třída deníku.
3. Kurzové přecenění (`investra_fx_revaluation`) po třídách, aby se třída na zůstatcích neztratila.
4. Náhled zaúčtování (`investra.posting.preview`) ukazuje třídu na řádcích.
5. Zrušení pole Třída na nástroji (data v `investra` ověřit SELECTem; při zrušení pole Odoo sloupec smaže).
6. Výkazy ČNB a přehledy portfolia: součet přes portfolia beze změny – ověřit.
7. Manuál: portfolio = obchodní model IFRS 9 a zároveň „kapsa“ třídy; třída se dvěma obchodními modely má dvě portfolia.
8. Testy: zajištění třídy B forwardem (přecenění jen do ΔT třídy B), stejný nástroj ve společném portfoliu a v portfoliu třídy,
   storno obchodu v portfoliu třídy, úrok a splátka, kurzové přecenění, nákup do společného portfolia placený z banky třídy, úpis třídy na banku třídy, výběr účtu podle třídy a měny, dva účty fondu ve stejné měně (zůstatky po účtech odpovídají pohybům); referenční scénáře beze změny.

## Technický plán

Schváleno Martinem 19. 11. 2026: `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 2 (2.1 plán, 2.2 postup a kód, 2.3 doplnění deriváty, nevypořádané a kurzové
přecenění), s „Přednostmi“ a oddílem 1. Obsah se sem nekopíruje.

- Teď (dávka ZJ-07 až ZJ-19, běh 1, Opus 5.5): body 1, 2, 3, 5, 8 a logika bodu 4 (třída na řádcích náhledu); A6 přemostění.
- Později: **2b** bankovní účet třídy, **2c** analytický účet za každý bankovní účet (zůstávají v tomto zadání, neprogramují se).
- Běh 6 (Copilot): formulář portfolia (Třída), text třídy u obchodu, sloupec Třída v náhledu zaúčtování, manuál (bod 7).
- Odchylky od plánu se zapisují do Výsledku.

## Výsledek

Běh 1 dávky (Claude Opus 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`. Plán: oddíl 2 zadání dávky.

- **Změněné soubory:** `investra_instruments/models/portfolio.py` (pole Třída, kontrola, zámek), `models/accounting_event.py` (nový,
  `_portfolio_class_lines`), `models/instrument.py` a `views/instrument_views.xml` (zrušená třída nástroje); `investra_derivative/models/posting.py`
  (zařazení u portfolia třídy, náhled); `investra_fx_revaluation/models/fx_profile.py` (`extra_groupby`); `investra_nav/models/valuation.py`
  (kurzové přecenění a nevypořádané po třídách), `models/posting_preview.py` (náhled = doklad, třída na řádku); testy
  `investra_nav/tests/test_portfolio_class.py`, `investra_derivative/tests/test_portfolio_class.py`, úprava rozbalení řádků náhledu ve třech testech.
- **Ověřeno:** A5 `SELECT count(*) FROM investra_instrument WHERE class_id IS NOT NULL` v `investra` = 0. Testy A7 (stejný nástroj ve sdíleném
  a v portfoliu B, dvě průměrky, storno, splátka s poplatkem, nevypořádaný obchod v EUR, náhled, zámek, forward v portfoliu B: A 25 000 000,
  B 24 700 000 po vypořádání). `investra_instruments+`, `investra_fx_revaluation+`, `investra_allocation+`: 891 testů, 0 selhání.
  Snímek 35 a 39 na povýšené kopii `investra` s přepočtem 35 shodný se snímkem před dávkou (`tools/snimek_na_kopii.sh`).
- **Odchylky od plánu:**
  1. Pravidlo (2) v A2: třídu řádkům bez zařazení dává **zdroj dokladu s portfoliem třídy** (obchod, splátka, derivát), ne „jediná třída
     v dokladu“. Doklad ocenění obsahuje všechny pozice; řádky bez zařazení ze sdíleného portfolia (např. přecenění derivátu sdíleného
     portfolia, které zařazení nemá kvůli otisku) by jinak dostaly třídu B. Ocenění portfolio nemá, platí v něm jen pravidlo (1).
  2. Peněžní role třídu nedostanou ani podle zařazení; řádek, kde volající uvedl klíč `class_id` (i prázdný), se nemění.
  3. Zámek třídy (`_has_postings`): řádek dokladu se zařazením portfolia **nebo** sjednaný derivát portfolia (derivát sdíleného portfolia
     zařazení na řádcích nemá). Zámek platí i pod `sudo`.
  4. A4: náhled zaúčtování bere řádky ze stejné transformace jako `_create_event` (ukáže i vnitřní zúčtování); řádek náhledu má jako 5. údaj
     kód třídy (u zaúčtovaných dokladů z `investra_class_id`). Sloupec Třída v tabulce doplní běh 6 (`_documents_html`).
  5. A2(d) `_compute_portfolio` beze změny (řádky zařazení mají), A2(c) poplatek splátky dostane třídu podle zdroje (test).
  6. ČNB a přehled portfolia: výkazy berou zůstatky podle rolí, vnitřní zúčtování je za fond nulové; samostatný test ČNB s portfoliem třídy
     není, ověřeno stávajícími testy `investra_cnb` beze změny.
  7. Verze modulů se v běhu 1 nezvedají (oddíl 11: na konci dávky podle dotčených modulů).
- **Neověřeno:** formulář portfolia a text třídy u obchodu (běh 6); ruční zkouška v UI.
- **Otevřené otázky a návrhy mimo rozsah:** body 2b a 2c (bankovní účet třídy) později; rozpad „Ostatní specifické“ podle rolí zůstává otevřený.

## Převzetí
