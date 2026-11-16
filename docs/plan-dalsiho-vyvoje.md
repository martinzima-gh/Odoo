# Plán dalšího vývoje (od 2026-11-15)

Navazuje na evidenci nástrojů (IM-01 až IM-13). Pořadí schválil Martin 15. 11. 2026 (deriváty nahoru kvůli FX swapům);
body označené „doporučení“ rozhodl Claude podle svého návrhu a Martin je může změnit.

## Společná pravidla

- Jedna verze aplikace (`CLAUDE.md`): větev pro etapu z `main`, databáze `investra` na 8071, testy jen na `investra_ci_*`.
- Každá etapa začíná **krokem návrhu** (Opus): ověří předpisy a kód, sepíše `docs/navrh-<téma>.md` (nejvýš 100 řádků,
  varianty a doporučení, číselný příklad, seznam testů) a rozepíše zadání kroků do `docs/ukoly/<ID>-*.md`. Pak se zastaví.
  Martin návrh schválí a teprve potom běží implementace, každý krok v nové relaci.
- Modely: návrh a červená zóna (účtování, ocenění, NAV, migrace) **Opus**; modely, formuláře, importy, sestavy podle
  přesného zadání **Sonnet**; dokumentace a SELECTy **Haiku**; vzhled **Copilot nebo Antigravity** v `~/odoo-review`.
  Fable jen při sporu o architekturu nebo účetní logiku a pro tento plán.
- Každá operace s účetním dopadem má náhled zaúčtování a záložku dokladů (`investra.posting.preview`).
- Odkazy na předpisy uvádět přesně a jen ověřené; neověřené označit. Rámce nemíchat (fondy 501/2002 Sb., Services 500/2002 Sb.).
- Po etapě: instalace do `investra` se zálohou, ukázka v ukázkových datech (`tools/demo_data/seed.py`), sloučení do `main`
  na Martinovu výzvu.

## Pořadí etap

| # | Etapa | ID | Proč v tomto pořadí |
|---|---|---|---|
| 0 | Stabilizace | ST | čistý základ: `main`, automatické testy, převzetí IM |
| 1 | Deriváty: FX forward a FX swap | DE | fondy je budou mít; zajištění tříd v cizí měně |
| 2 | Převzetí fondu (počáteční stavy) | PF | bez něj nenaběhne žádný skutečný fond; cíl Q1 2027 |
| 3 | Výkazy ČNB | CN | měsíční lhůty 25–30 dnů (`docs/cnb/lhuty.md`) |
| 4 | ECL | EC | dopad jen u AC a FVOCI; fond je převážně FVTPL |
| 5 | FVOCI do kapitálu | FO | dokončení IFRS 9; ECL u FVOCI na něm závisí |
| 6 | Výroční zprávy | VZ | využije sestavy z etapy 3 |
| 7 | Provozní pohodlí | UX | přání z otevřených bodů, průběžně |

## Etapa 0 – Stabilizace (ST)

| Krok | Obsah | Model |
|---|---|---|
| ST-01 | Sekce Převzetí IM-01 až IM-13, sloučení `feature/instrument-master` → `feature/nav-prototyp` → `main` (souhlas Martina v promptu), smazání sloučených větví po dotazu | Sonnet |
| ST-02 | GitHub Actions: instalace všech modulů `investra_*` a testy na čisté databázi při každém pushi; bez tajných údajů v repozitáři | Sonnet |
| ST-03 | Chyba nabídky Přehled: šablona `FundTodo` čte `items` bez `this.` (zadání `docs/ukoly/ST-03-chyba-prehledu-fundtodo.md`) | Sonnet |
| ST-04 | Pravidla Copilota a Antigravity: společná instance 8072 podle `CLAUDE.md` | Sonnet |

Prompt ST-01 (`/model sonnet`), zadání `docs/ukoly/ST-01-slouceni-do-main.md`:

    Přečti CLAUDE.md, docs/ukoly/ST-01-slouceni-do-main.md a docs/predavky/2026-11-15-im13-hotovo.md. Celý projekt
    neprocházej. Proveď ST-01 přesně podle zadání. Souhlasím se sloučením feature/instrument-master do
    feature/nav-prototyp a do main bez --force (Martin). Větve nemaž, jen navrhni. Soubor .env nečti ani nevypisuj.
    Doplň Výsledek, deník a předávku, napiš mi, co šlo ven, a zastav se.

ST-02 až ST-04: stejný prompt s číslem kroku, bez věty o sloučení; větev `ukol/ST-0X` z `main`.

## Etapa 1 – Deriváty: FX forward a FX swap (DE)

Zjednodušené řešení podle `docs/navrh-fx-derivaty.md` (zásady schválil Martin 15. 11. 2026): nominály v podrozvaze,
reálná hodnota ze spotu s rovnoměrně rozpouštěnými forwardovými body (varianta B), ruční hodnota z banky, vypořádání
tlačítkem. Bez zajišťovacích derivátů a přiřazení třídě, bez diskontování a sazeb měn. Větev `etapa/derivaty`.

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| DE-01 | Návrh – hotovo (hlavní relace) | Fable | návrh |
| DE-02 | Modul `investra_derivative`: smlouva, nohy, ruční hodnota, formuláře, práva, kontroly | Sonnet | oranžová |
| DE-03 | Role a účty (podrozvaha, záporná RH, výsledek), sjednání, vypořádání, storno, náhled; ověření předpisů | Opus | červená |
| DE-04 | Ocenění: výpočet RH, ruční hodnota, přepočet podrozvahy, doklady, kontroly | Opus | červená |
| DE-05 | Ukázka v `seed.py`, nasazení do `investra`, SELECTy, README, návrh mapování ČNB | Sonnet | oranžová |

Kroky jdou po sobě, každý v nové relaci. Prompt DE-02 (`/model sonnet`):

    Přečti CLAUDE.md, docs/plan-dalsiho-vyvoje.md (Společná pravidla), docs/ukoly/DE-02-evidence-fx-derivatu.md
    a z docs/navrh-fx-derivaty.md jen oddíly uvedené v úkolu. Celý projekt neprocházej. Pracuj ve větvi etapa/derivaty.
    Soubor .env nečti ani nevypisuj. Proveď úkol, pusť testy na dočasné databázi, doplň Výsledek, commitni, pushni
    do origin etapa/derivaty:etapa/derivaty a zastav se.

Prompt DE-03 a DE-04 (`/model opus`): stejný s číslem úkolu a větou „Plán v úkolu DE-0X schvaluji (červená zóna, Martin).“;
u DE-03 navíc „Čísla účtů mi předlož ke schválení a počkej.“ Prompt DE-05 (`/model sonnet`): stejný jako DE-02 s větou
„Souhlasím s instalací a povýšením modulů v databázi investra se zálohou do zalohy/ (Martin).“

## Etapa 2 – Převzetí fondu (PF)

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| PF-01 | Návrh: den přechodu, počáteční rozvaha, pozice po nástrojích a portfoliích s pořizovací cenou a kurzem, naběhlé úroky, třídy a počty podílů, poslední kurz, co dělat s chybějícím pořizovacím kurzem; formát importu (Excel) a kontroly proti rozvaze předchozího administrátora | Opus | návrh |
| PF-02 | Šablony importu a průvodce s náhledem a konflikty (vzor: import číselníků IM-02) | Sonnet | oranžová |
| PF-03 | Zaúčtování počátečních stavů a založení pozic; první ocenění navazuje na převzatý kurz | Opus | červená |
| PF-04 | Odsouhlasení: sestava rozdílů převzato × Odoo, protokol o převzetí | Sonnet | oranžová |

Prompt PF-01: jako DE-01, s oddílem Etapa 2, výstup `docs/navrh-prevzeti-fondu.md`, větev `etapa/prevzeti-fondu`.

## Etapa 3 – Výkazy ČNB (CN)

Dnes: katalog FOFI20261201 v `docs/cnb/`, modul `investra_cnb` s převodovou tabulkou. Odeslání do SDAT je mimo rozsah,
dokud není přístup do testovacího SDAT (`docs/navrh-sdat.md`).

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| CN-01 | Návrh: které výkazy podává FKI a v jakém pořadí je stavět (podle `docs/cnb/lhuty.md` a `vykazy-*.csv`), model výkazu (fond, období, stav, hodnoty, ruční úpravy s důvodem), zdroje dat (účty přes převodovou tabulku, pozice, emitenti), kontroly z `kontroly-*.csv`, export | Opus | návrh |
| CN-02 | Jádro: model výkazu a hodnot, plnění z účetnictví, stavy a schválení, náhled | Sonnet | oranžová |
| CN-03 | Rozvahové a výsledkové výkazy (první sada podle CN-01) | Sonnet | oranžová |
| CN-04 | Výkazy po pozicích (DOFOS31 a příbuzné): BA0088, ESA, země, měna, kategorie | Sonnet | oranžová |
| CN-05 | Kontroly ČNB před schválením, přehled chyb | Sonnet | oranžová |
| CN-06 | Export do souboru podle metodiky; ověření proti ukázkovým datům | Opus | oranžová |

Prompt CN-01: jako DE-01, s oddílem Etapa 3 a soubory `docs/cnb/README.md`, `lhuty.md`, `prevodova-tabulka.md`;
výstup `docs/navrh-vykazy-cnb.md`, větev `etapa/vykazy-cnb`. Katalog číst jen cíleně (grep), ne celý.

## Etapa 4 – ECL (EC)

Rozhodnutí Martina 15. 11. 2026: ECL se zadává **zjednodušeně jako procento** z expozice. Procento je na protistraně
(klientovi), s možnou výjimkou na konkrétním nástroji. PD, LGD, ratingy a scénáře se nezavádějí.

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| EC-01 | Návrh (krátký): rozsah (dluhové AC a FVOCI; FVTPL ne), ověření opory (501/2002 Sb. a IFRS 9 část 5.5) a toho, jak zjednodušení zdůvodnit v účetní politice; výpočet ECL = expozice × %; role účtů a řádky ČNB; zda evidovat stupeň 1–3 jen informativně pro přílohu a výkazy | Opus | návrh |
| EC-02 | Protistrana: procento ECL verzované podle data (platí od, %, zdůvodnění, zadal); nástroj: vlastní procento s povinným důvodem, má přednost; formuláře a práva | Sonnet | oranžová |
| EC-03 | Výpočet při ocenění (naběhlá hodnota před opravnou položkou × %), účtování změny proti minulému ocenění s náhledem a storny, upozornění na pozici bez procenta | Opus | červená |
| EC-04 | Přehled ECL podle fondu a protistrany; ukázka v `seed.py` | Sonnet | oranžová |

Prompt EC-01: jako DE-01, s oddílem Etapa 4 a `docs/navrh-klasifikace-ifrs9.md`; výstup `docs/navrh-ecl.md`
(nejvýš 60 řádků), větev `etapa/ecl`.

## Etapa 5 – FVOCI do kapitálu (FO)

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| FO-01 | Návrh: přecenění dluhových FVOCI do kapitálu, úrok EIR do výsledku, recyklace při prodeji, kapitálové FVOCI bez recyklace, ECL u FVOCI, dopad na NAV a výkazy | Opus | návrh |
| FO-02 | Implementace v ocenění a účtování | Opus | červená |

## Etapa 6 – Výroční zprávy (VZ)

Doporučení: vlastní sestavy v Community (potřebuje je i etapa 3); výstupem jsou tabulky do Excelu, text zprávy se píše ručně.

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| VZ-01 | Návrh: požadavky na obsah výroční zprávy fondu ověřit v ZISIF a prováděcích předpisech; seznam tabulek, zdroje dat | Opus | návrh |
| VZ-02 | Rozvaha, výkaz zisku a ztráty, přehled o změnách vlastního kapitálu, podrozvaha | Sonnet | oranžová |
| VZ-03 | Tabulky přílohy: skladba majetku, vývoj kurzu a fondového kapitálu, úplaty, obchody | Sonnet | oranžová |
| VZ-04 | Export do Excelu, kontrola na ukázkových datech | Haiku | zelená |

## Etapa 7 – Provozní pohodlí (UX)

Přehled operací ke zpracování; zařazení nástroje vzniká prvním nákupem; výchozí maximální stáří ceny podle typu;
pořadí stavů ocenění v čase. Zadání píše Claude jednotlivě do `docs/ukoly/`, provádí Sonnet, vzhled Copilot nebo Antigravity.

## Manuál a pročištění (MN, zadal Martin 16. 11. 2026, přednost před etapou 2)

Martin zakládá v `investra` novou společnost a fond s více třídami; nálezy se opravují samostatnými úkoly MN-03 a dál.
Manuál v `docs/manual/`, kapitola na soubor. Větev `ukol/MN-manual`.

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| MN-01 | Průvodce „Nová účetní kniha“ nad `create_book` (`docs/ukoly/MN-01-pruvodce-nova-kniha.md`) | Opus | oranžová |
| MN-02 | Manuál kap. 1–3: společnost a kniha, fond, třídy (`docs/ukoly/MN-02-manual-zalozeni-fondu.md`) | Sonnet | zelená |
| MN-03+ | Opravy z Martinova průchodu a další kapitoly (zadání píše hlavní relace) | podle zóny | |

## Nezařazené úkoly (zadal Martin 15. 11. 2026)

Zatím bez etapy a pořadí; oba začínají návrhem (Opus), který ověří předpisy v aktuálním znění, a teprve pak se zařadí.

| Krok | Obsah | Model | Zóna |
|---|---|---|---|
| PO-01 | Podrozvaha – počet podílových listů / investičních akcií: návrh, jak evidovat a účtovat počet vydaných kusů po třídách v podrozvaze (podrozvahové účty, účtování při úpisu a odkupu, vazba na evidenci kusů v ocenění a na IS, výkazy ČNB a výroční zpráva). Návrh nejdřív ověří ve vyhlášce č. 501/2002 Sb. a českých účetních standardech pro finanční instituce, zda a v jaké položce se počet kusů v podrozvaze vykazuje (podrozvaha se vede v peněžních částkách; evidence v kusech může být jen analytika nebo samostatná evidence) – výklad potvrdit s auditorem | Opus | návrh, pak červená (účtování) |
| DA-01 | Daně fondu – daňové a nedaňové účty: návrh označení účtů (daňově účinný / neúčinný náklad a výnos), účtů a výnosů podléhajících jiné sazbě daně nebo samostatnému základu, výpočtu splatné daně, dohadu na daň v průběhu roku (dopad do NAV při každém ocenění) a odložené daně. Návrh nejdřív určí daňový režim fondu (základní investiční fond × ostatní) podle zákona č. 586/1992 Sb. v aktuálním znění a pravidla pro odloženou daň podle vyhlášky č. 501/2002 Sb. a ČÚS; rámce se nemíchají (Services podle 500/2002 Sb. zvlášť). Výklad potvrdit s daňovým poradcem a auditorem | Opus | návrh, pak červená (účtování, NAV) |
| OZ-01 | Oprava zveřejněného ocenění – rozhodnutí: Martin vybere variantu podle `docs/navrh-oprava-zverejneneho-oceneni.md` (doporučení C ve dvou krocích) a odpoví na pět otázek „K rozhodnutí“; před tím ověřit předpisy z oddílu „Opora v předpisech“ (ZISIF, statut, Pravidla oceňování, vyhláška č. 501/2002 Sb.) s compliance a auditorem | Opus | návrh |
| OZ-02 | Oprava zveřejněného ocenění – krok 1: záznam „Zjištěná chyba ocenění“ (varianta A) a omezené stažení posledního zveřejněného ocenění s novou verzí (činnost matice, náhled, storna, zámek, testy) podle rozsahu v návrhu; až po OZ-01 | Opus | červená |
| OZ-03 | Oprava zveřejněného ocenění – krok 2: plné stažení s řetězem pozdějších ocenění, práh významnosti a podklad pro kompenzace; až s napojením na IS a prvním skutečným fondem | Opus | červená |

## Šablona promptu pro implementační krok

    Přečti CLAUDE.md, docs/plan-dalsiho-vyvoje.md (Společná pravidla) a docs/ukoly/<ID>-….md a z návrhu etapy jen oddíly
    uvedené v úkolu. Celý projekt neprocházej. Pracuj ve větvi etapy. [U červené zóny: Plán v úkolu <ID> schvaluji
    (červená zóna, Martin).] Soubor .env existuje, nečti ho ani nevypisuj. Proveď úkol, pusť testy na dočasné databázi
    investra_ci_* a po testech ji smaž, doplň sekci Výsledek, commitni, pushni do origin s výslovným cílem a zastav se.

## Mimo plán (čeká na podklady nebo rozhodnutí)

Napojení na IS (chybí dokumentace), odeslání do SDAT (chybí přístup), bankovní výpisy a párování (Community × Enterprise),
ostatní deriváty, příprava produkce (hosting, zálohy, vícefaktorové přihlášení, DORA), nezávislý výpočet NAV.
