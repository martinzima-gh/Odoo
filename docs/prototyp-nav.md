# Prototyp NAV: stav a spuštění

Stav 2026-11-07, větev `feature/nav-prototyp`, databáze `investra_test`, smyšlená data. Vývojový návrh, není schválený k ostrému použití.
Technická zjištění jsou v `analyza-odoo20-nav.md`, varianty úplat v `poplatky-varianty.md`.

## Moduly

| Modul | Hotovo | Testů |
|---|---|--:|
| `investra_entity` | Kniha, založení s povinným nastavením, role účtů, skupiny | 6 |
| `investra_chart_fund` | Pracovní osnova fondu a mapování rolí | 4 |
| `investra_rates` | Kurzy ČNB a ECB, neměnný záznam se zdrojem, promítnutí do Odoo | 15 |
| `investra_fund` | Fondy, třídy, kalendář, zaokrouhlení kurzu | 10 |
| `investra_posting` | Události, ochrana dokladů, třída na řádku, hash, storno | 22 |
| `investra_instruments` | Typy nástrojů, nástroje, ceny se schválením, obchody, pozice | 25 |
| `investra_allocation` | Verzovaná schémata, poměr a pořadí nároků | 3 |
| `investra_dashboard` | Přehled fondů, výjimky, termíny ČNB | 11 |
| `investra_counterparty` | Registr protistran a emitentů s platností, sektor ESA 2010, LEI | 8 |
| `investra_cnb` | Převodová tabulka rolí na řádky výkazů ČNB, kontrola úplnosti | 10 |
| `investra_fx_revaluation` | Profily přecenění, doplňkové přecenění, návrh dokladu, kontrola kurzu | 29 |
| `investra_nav` | Úplaty, ocenění, schvalování, depozitář, zveřejnění, balíček, naběhlá hodnota, zaúčtování obchodu, měna kurzu, přístup podle společnosti, termínovaný vklad | 109 |

Výpočetní jádro a referenční výpočet mají dalších 55 testů mimo Odoo (`tools/nav_reference`).

## Co je ověřené

- Pět scénářů: Odoo z účetních řádků dojde ke stejnému FK, kapitálu tříd, kusům a kurzům jako referenční výpočet.
- Akceptace prototypu z `harmonogram.md`: opakovaný výpočet nic nezdvojí, součet tříd rovná se FK, pozice se rovnají hlavní knize, zadavatel si neschválí vlastní ocenění, vrácení před zaúčtováním je bez storen, vrácení depozitářem stornuje a vzniká nová verze.
- Referenční výpočet není nezávislá kontrola: má stejného autora. Scénáře musí ověřit člověk.

## Odchylky od architektury

- `investra_posting` závisí na `investra_fund`, protože třída je pole na řádku.
- Role účtů jsou v `investra_entity`, šablona osnovy v `investra_chart_fund`.
- Pravidlo podle účetního rámce zatím není: řádky dokladu určuje kód ocenění. Doplnit, až bude víc rámců.
- Rozdělení mezi třídy podle pořadí nároků se zaúčtuje jako přesun přes vnitřní zúčtování. Do architektury doplnit jako nový způsob alokace.

## Co chybí

Poplatky obchodů; dohadné položky; kupóny a dividendy; repo, kupóny dluhopisů, úvěry, deriváty a ostatní podíly v portfoliu; platnost kurzu;
hranice kontrol; UI ověřené člověkem; bezpečnostní revize; test na reálném objemu.

## Typy nástrojů

Menu Portfolio → Typy nástrojů. Typ jen předvyplní kategorii IFRS 9, způsob ocenění, roli účtu a list ČNB; platí hodnota na nástroji.
Účetní ji může změnit, formulář ukáže odchylku od návrhu a změna se zapíše do historie nástroje. Po prvním obchodu jsou typ, klasifikace,
způsob ocenění a role neměnné. Aktualizace modulu úpravy číselníku nepřepíše.

| Typ | Skupina | IFRS 9 | Ocenění | Role účtu | List ČNB |
|---|---|---|---|---|---|
| Akcie | Kótované | FVTPL | Cena × kusy | `instrument` | DOFO31_11 |
| Podílový list nebo ETF | Kótované | FVTPL | Cena × kusy | `instrument` | DOFO31_11 |
| Dluhopis | Dluhové | FVTPL | Cena × kusy | `instrument_debt` | DOFO31_12 |
| Termínovaný vklad | Peněžní trh | Naběhlá hodnota | Naběhlá hodnota | `deposit` | Neurčeno |
| Reverzní repo | Peněžní trh | Naběhlá hodnota | Naběhlá hodnota | `repo` | Neurčeno |
| Poskytnutý úvěr | Úvěry a účasti | FVTPL | Model nebo znalec | `loan_given` | RIS30_02 |
| Účast | Úvěry a účasti | FVTPL | Model nebo znalec | `participation` | RIS33_13 |
| Burzovní derivát | Deriváty | FVTPL | Cena × kusy | `derivative` | DOFO31_21 |
| Mimoburzovní derivát | Deriváty | FVTPL | Podle smlouvy | `derivative` | DOFO31_22 |
| Ostatní podíl (fond bez ISIN) | Ostatní podíly | FVTPL | Zadaná hodnota pozice | `other_holding` | RIS33_13 |

Návrhy jsou pracovní, stejně jako čísla účtů; potvrdí je účetní politika fondu. Záporná hodnota derivátu zatím nemá vlastní pasivní roli.

**Úročení:** fond má výchozí EIR, lineární úročení je volba fondu nebo nástroje a musí mít zdůvodnění. Nástroj má smluvní toky na jednotku,
každý nákup má vlastní efektivní úrokovou míru. `_accrued_value` hodnotu jen spočítá, nic neúčtuje. Lineárně umí zatím jednu splátku,
prodej není podporovaný. Ocenění doúčtuje úrok do naběhlé hodnoty typem pohybu Naběhlý úrok proti úrokovým výnosům. Kalendář vkladu s jednou splátkou vygeneruje tlačítko na nástroji z jistiny, sazby a konvence, splátka se zaúčtuje v menu Splátky nástrojů.

**Ostatní podíly:** investice do fondů bez ISIN, zpravidla s upisovacím závazkem. Nástroj patří jednomu fondu, případně třídě, a nese
upisovací závazek, typ investice (cenné papíry, nebo podíly, kvůli různému daňovému režimu) a zakázku. Hotový je jen číselník a karta nástroje;
zaúčtování obchodu se zastaví. Zbývá:

- platba a vypořádání zvlášť: po platbě je částka na účtu pořízení, přeceňuje se jen kurzem, po vypořádání přejde na účet investice,
- prodej: přijatá platba je závazek do vypořádání, snížení pořizovací ceny zadá uživatel, realizovaný výsledek a kurz jdou zvlášť,
- změna závazku nemusí odpovídat celé platbě, protože platba může obsahovat příplatky a vratky,
- reálná hodnota se zadává za vypořádanou investovanou částku, ne za kus,
- podrozvaha v měně se přeceňuje jen v podrozvaze, bez dopadu do výsledku,
- RIS33_13 má místo nominální hodnoty upisovací závazek.

Odoo nedovolí podrozvahové a rozvahové účty v jednom dokladu (`_check_off_balance`). Podrozvaha proto potřebuje vlastní doklad.
Stejný postup bude platit pro další závazky a přísliby.

## Přehled fondů

Modul `investra_dashboard`, menu Investra → Přehled fondů, jako karty, nebo seznam. Fond ukazuje poslední ocenění, FK, kurzy tříd, poslední
zveřejnění, další plánované ocenění, další termín ČNB a výjimky. Přehled nic neúčtuje ani neschvaluje a nic neukládá. Ukáže fondy společností
vybraných v přepínači společností, proto je pro přehled napříč fondy potřeba vybrat všechny.

| Stav | Kdy |
|---|---|
| Vyžaduje zásah | Ocenění po termínu, vrácené ocenění, kontrola se stopem, termín ČNB po lhůtě |
| Upozornění | Kontrola s upozorněním, termín ČNB do 7 dnů, obchod po termínu vypořádání, cena čekající na schválení |
| Bez ocenění | Fond zatím nemá ocenění |

Termíny a výkazy bude zveřejňovat ČNB v SDAT a budou se stahovat odtud; zatím jsou v menu Termíny ČNB jen obecné příklady se zdrojem Příklad. Počet dnů upozornění je pracovní.
Ukázku stavů vytvoří `tools/nav_demo/demo_prehled.py`: Beta vyžaduje zásah, Gama má upozornění.

## Zaúčtování obchodu

Parametr fondu podle IFRS 9 odst. 3.1.2; výchozí je Trade date accounting. Po prvním obchodu fondu nejde změnit.

| Situace | Trade date accounting | Settlement date accounting |
|---|---|---|
| Sjednání | Nástroj proti závazku nebo pohledávce z nevypořádaného obchodu | Bez dokladu, stav Sjednáno, nevypořádáno |
| Ocenění před vypořádáním | Nástroj se přecení, závazek v cizí měně přecení kurz | Změna RH na zvláštní účet proti výsledku (B3.1.6); u naběhlé hodnoty se neúčtuje, u FVOCI se ocenění zastaví |
| Vypořádání | Závazek nebo pohledávka proti bance | Nástroj proti bance |
| Po vypořádání | Kurzový rozdíl doúčtuje nejbližší ocenění | Zůstatek změny RH se rozpustí, přecenění jde přes nástroj |

Bez data vypořádání, nebo se stejným datem, jde obchod rovnou proti bance. Obchod po termínu bez vypořádání je upozornění v kontrolách ocenění.
Kurzový rozdíl z vypořádání se účtuje až při ocenění, ne v den platby. Změna RH před vypořádáním je u cizí měny jedna částka, bez rozdělení na cenu a kurz.

## Registr protistran a převod na výkazy

Protistrana má zemi, sektor ESA 2010 a LEI s platností od data, změny jsou v historii. Nástroj má emitenta. Převodová tabulka v Nastavení převádí role účtů na řádky listů ROFO10_11, ROFO10_21, VYFO20_11, RIS30_01 a RIS30_03, s platností a podle kategorie IFRS 9.
Řádky jsou pracovní návrh, potvrdí je metodik. Sloupce podle zemí, členění splatností a seznam úvěrů zatím nejsou; výkaz se nesestavuje ani neodesílá, tabulka dává hodnoty řádků a kontrolu nepokrytých rolí.

## Přecenění cizích měn

Profil určí přeceňované účty, oddělené účty zisku a ztráty, deník, zdroj kurzu a nejvyšší stáří kurzu. Přecenění doúčtuje rozdíl do potřebného zůstatku po účtu, měně a partnerovi a vytvoří návrh dokladu; zaúčtuje ho účetní. Doklad zavalutovaný zpětně se řeší novým přeceněním ke stejnému datu; souběžný nezaúčtovaný návrh profilu a uzamčené období výpočet zastaví, pozdější zaúčtované přecenění vyvolá upozornění. Kurz se čte z `investra.rate`, ručně zadané kurzy v Odoo se nepoužijí. Návrh politiky je v `docs/politika-preceneni.md`.

Měření výkonu: test s tagem `nav_benchmark` se spouští jen výslovně. Ocenění s 200 nástroji trvalo 0,76 s, s 30 třídami 1,10 s, optimalizace zatím není potřeba.

## Spuštění testů

```
python3 -m unittest discover -s tools/nav_reference -p 'test_*.py'
python3 tools/nav_reference/nav_reference.py
docker compose -f docker-compose.investra.yml run --rm --no-deps -T odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d investra_test -u investra_nav --test-enable --test-tags /investra_nav \
  --stop-after-init --no-http --max-cron-threads=0
```

Pozor: `-i` u už nainstalovaného modulu testy nespustí, zpráva „0 tests“ není úspěch.
Kurzy jsou v databázi společné a neměnné: testy s kurzy nesmí používat stejné období jako ukázková data.

## Ukázka

Data vytvoří `tools/nav_demo/demo.py` (všechno smyšlené). Web nad testovací databází se spustí na portu 8071, vývojové instance se to nedotkne:

```
docker compose -f docker-compose.investra.yml run -d --rm --no-deps --name investra-test-web -p 127.0.0.1:8071:8069 odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d investra_test --db-filter='^investra_test$' --max-cron-threads=0
docker stop investra-test-web
```

V DBeaveru použij stejné připojení jako k `investra_dev` (`127.0.0.1:5433`, účet `dbeaver_ro`), jen databázi `investra_test`.

Testovací databáze má výchozí přihlášení správce. Slouží jen na tomto počítači a nesmí obsahovat reálná data.
