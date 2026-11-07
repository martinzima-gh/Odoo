<!-- Export z Claude Doc "Investra – architektura Odoo a IS" (https://claude.ai/artifact/YPQf7hVsbVDpGgRAxYH19w). Zdroj pravdy je Doc; soubor se přepisuje exportem, neupravovat ručně. Revize Doc: 222. -->

# Investra – architektura Odoo a IS

Nov 5, 2026 · @Martin Zíma

## Shrnutí

Odoo bude účetní základ pro společnosti, fondy a podfondy a ponese i portfolio, ocenění a výkazy ČNB. Samostatná aplikace IS bude řešit jen držitele podílů a investičních akcií, pokyny a jejich vypořádání.

Cílem je auditovatelný účetní a NAV základ pro Investru, která má spravovat fondy různých zakladatelů. Proto je většina pravidel parametrizovaná uživatelem, ne napsaná v kódu.

Návrh stojí na třech prvcích:

- **Jedna účetní kniha = jedna samostatná společnost v Odoo.** Každá má vlastní osnovu, funkční měnu a kurzy.
- **Významové role účtů.** Pravidla FX, alokace i výkazů se odkazují na roli, ne na číslo účtu, takže fungují nad různými osnovami.
- **Jediný účtovací modul.** Žádný fondový modul nezapisuje do účetnictví přímo. Každý zápis vzniká z události podle pravidla a jde dohledat zpět.

Nasazení začne ostrým účetnictvím Investra Services s.r.o., potom investiční společností a až nakonec fondy. Dokument je návrh k připomínkám. Nic z toho zatím není naprogramováno kromě prázdné kostry addonu.

## Přijatá rozhodnutí a předpoklady

Rozhodnutí jsou potvrzená zadavatelem. Návrhy a předpoklady se ještě mohou změnit.

| Oblast | Stanovisko | Stav |
| --- | --- | --- |
| Rozsah | Účetnictví a.s., s.r.o., SICAV, fondů a podfondů v Odoo | Rozhodnuto |
| Účetní rámec | CAS pro podnikatele, CAS pro finanční instituce nebo plné IFRS, pro každou jednotku zvlášť | Rozhodnuto |
| Souběh CAS a IFRS | Každá jednotka má jeden rámec: vyhláška 500/2002 Sb., vyhláška 501/2002 Sb. s IFRS pro finanční nástroje (§ 4a, znění ověřit), nebo plné IFRS. U rámce 501 nejde o souběh. V knize se rámec eviduje těmito třemi hodnotami; vyhláška 500 se týká i společností ve skupině a SPV | Rozhodnuto |
| Funkční měna | CZK nebo jiná, například EUR; kurzy ČNB i ECB; předpisy se upraví později | Rozhodnuto |
| FX přecenění | Uživatelsky definované skupiny účtů | Rozhodnuto |
| Třídy a alokace | Široce parametrizovatelné, kvůli různým zakladatelům | Rozhodnuto |
| Interval ocenění | Uživatelsky definovaný pro každý fond (například denně, týdně, měsíčně, čtvrtletně, ročně), možná jsou i ocenění mimo pravidelné běhy, s kontrolou proti statutu a zákonné lhůtě | Rozhodnuto |
| IS | Samostatná aplikace IS, jen vypořádání nákupů a prodejů a evidence držitelů | Rozhodnuto |
| Instrumenty a portfolio | Vlastníkem je Odoo | Rozhodnuto |
| Příchozí platby | Peníze investorů chodí na účet třídy pro úpisy, banka je v Odoo | Rozhodnuto |
| Výplaty odkupů | Platební příkazy vytváří IS | Rozhodnuto |
| Bankovní účty | Každá třída má samostatný účet pro úpisy a samostatný pro odkupy, fond má investiční účet, zvlášť pro každou měnu | Rozhodnuto |
| Převody mezi účty | Spouští IS, Odoo je páruje na výpisech | Rozhodnuto |
| Závěrka klientských transakcí | Vytváří IS | Rozhodnuto |
| Kurz úpisu v průběhu období | Poslední známý kurz, ruční úprava možná, řídí IS | Rozhodnuto |
| Univerzální fondový modul | Musí pokrýt i výplatu dividend z tříd | Rozhodnuto |
| Schvalování ocenění | Kontrola druhou osobou povinná u fondů Investry, stanovisko obhospodařovatele a depozitáře se eviduje v Odoo; ocenění schvaluje i administrátor podle parametru fondu | Rozhodnuto |
| Výpočet tříd | Pouze z rozvahy, přesuny mezi třídou a společným majetkem přes vnitřní zúčtování | Rozhodnuto, ověřit prototypem |
| Verze Odoo | Odoo 20, připnuté sestavení 20.0-20261102, aktualizace řízeně; výuková odoo\_cz zůstává na 19 | Rozhodnuto |
| Pořadí nasazení | Investra Services, investiční společnost, potom fondy | Rozhodnuto |
| Části SICAV | Jedna společnost, pole části na účetním řádku, výkazy po částech i za celek | Rozhodnuto |
| Převzetí fondů | Ke dni uzávěrky nebo ocenění, s paralelním během, historie jako archiv | Rozhodnuto |
| Účetní systém | Odoo je jediný účetní systém od začátku, včetně oběhu dokladů | Rozhodnuto |
| Databáze | Jedna databáze pro všechny zakladatele | Rozhodnuto |
| Vstup transakce do závěrky | Podle statutu fondu, parametr fondu | Rozhodnuto |
| Krytí výplat | Ověřuje se při autorizaci platby, Odoo nabídne přehled hotovosti | Rozhodnuto |
| Předání příkazů do banky | Soubor, autorizace dvěma osobami a kontrola depozitářem | Rozhodnuto |
| Výjimky u plateb | Přechodný účet a fronta k řešení, přeplatek se vrací, nedoplatek podle statutu | Rozhodnuto |
| Dividendy | Odoo účtuje hrubou dividendu za třídu, srážky a reinvestici počítá IS | Rozhodnuto |
| Ceny z Bloombergu | Import z Excelu, automatické napojení případně později | Rozhodnuto |
| Reálná hodnota | Poslední známá cena, Odoo eviduje cenu a podklad, FX a přecenění na reálnou hodnotu odděleně | Rozhodnuto |
| Pořizovací cena při částečném prodeji | Průměr u počítatelných nástrojů, jinak určí uživatel | Rozhodnuto |
| Odoo Mates | Ve vývoji se nepoužívají, zůstávají v testovací `odoo_cz` | Rozhodnuto |
| Kniha = společnost | Každá účetní kniha je hlavní společnost, ne pobočka | Rozhodnuto, ověřit v etapě zkušebních knih |
| Třída na účetním řádku | Vlastní pole, prázdné = společná položka | Návrh, ověřit prototypem |
| Číselník fondů a tříd | Vlastníkem je Odoo, IS dostává kopii | Rozhodnuto, lze změnit |
| Plán verzí | Vývoj na Community, Enterprise zůstává otevřené | Předpoklad |
| Katalog ČNB | Výkazy, položky, kontroly a číselníky v repozitáři (docs/cnb): CSV je zdroj, XLSX se generuje, verze podle metodiky | Rozhodnuto |
| Postup ocenění | Jeden záznam ocenění s kroky; návrhy dokladů (zaúčtování viz řádek Zaúčtování ocenění); typovaná pravidla poplatků | Návrh, k rozhodnutí |
| Mapování výkazů | Buňka výkazu je typované pravidlo s platností a vazbou na metodiku; deriváty po smlouvách brutto; stav sjednáno, nevypořádáno; ruční zásah jen se zdůvodněním | Rozhodnuto |
| Zaúčtování ocenění | Varianta B: schvaluje se kompletní finální ocenění se sumářem z nezaúčtovaných návrhů; zaúčtuje se jedním krokem k datu ocenění před odesláním depozitáři; vrácení před zaúčtováním je oprava návrhů a nová verze, vrácení depozitářem storno všech dokladů a nová verze; uzamčení až po stanovisku depozitáře | Rozhodnuto, ověřit prototypem |

## Hranice systémů a vlastnictví dat

IS řeší stranu investorů, Odoo stranu aktiv fondu a účetnictví. Každý údaj má jediného vlastníka a druhý systém dostává jen kopii nebo výsledek.

&#91;embedded content: IS a Odoo · odpovědnosti a 9 zpráv\]

| Oblast | Vlastník | Co dostane druhý systém |
| --- | --- | --- |
| Držitelé, AML, osobní údaje | IS | Odoo nic, jen agregace pro ČNB |
| Pokyny k nákupu a prodeji | IS | Odoo identifikátor pokynu pro párování |
| Kusy na držitele | IS | Odoo stav kusů za třídu |
| Závěrka klientských transakcí | IS | Odoo finalizovanou závěrku |
| Volba kurzu pro pokyn, ruční úprava | IS | Odoo cenu a příznak ruční úpravy |
| Odchozí platební příkazy na výplaty a převody | IS | Odoo identifikátor výplaty nebo převodu |
| Účetní knihy, osnovy, kurzy, FX | Odoo | IS kurz, pokud ho potřebuje |
| Fondy, podfondy, třídy (návrh) | Odoo | IS kopii číselníku |
| Instrumenty, ceny, portfolio | Odoo | IS nic |
| Ocenění, alokace, NAV | Odoo | IS schválený kurz a období platnosti |
| Výpisy a příchozí platby | Odoo | IS potvrzení přijaté platby |
| Výkazy ČNB | Odoo | IS dodá agregovaná data o držitelích |
| Výplata dividend držitelům | IS | Odoo souhrn za třídu a identifikátor výplaty |

Odoo tak nedrží žádné osobní údaje držitelů, ani čísla jejich účtů.

## Účetní knihy, osnovy a kurzy

Každá a.s., s.r.o., SICAV, fond i podfond bude samostatná hlavní společnost v Odoo. Hierarchii SICAV a podfondů povedeme ve vlastním modelu, ne jako pobočky.

Z kódu Odoo 20 Community (sestavení 20.0-20261102) je ověřeno:

- **Pobočky nestačí.** Kurzy se u pobočky berou z hlavní společnosti a část nastavení se na ni kopíruje. Podfond v EUR pod SICAV v CZK by tak nefungoval.
- **Vlastní osnova je možná.** Kód účtu je uložen zvlášť pro každou hlavní společnost a společnost má vlastní šablonu osnovy.
- **Kurzy lze vést po společnostech.** Jedna kniha může používat ČNB a jiná ECB.
- **Čisté Community nemá v menu finanční výkazy ani bankovní párování.** V naší instalaci je dodávaly Odoo Mates.

**Šablony osnov:** připravíme CAS pro podnikatele, CAS pro finanční instituce a IFRS. Osnovu zakladatele půjde upravit, aniž by se měnila pravidla, protože ta pracují s rolemi.

**Role účtů:** každý účet dostane roli, například „závazek z úpisu“, „kapitál třídy“ nebo „nerealizovaný FX zisk“. Seznam rolí vznikne v první etapě a je nejdůležitější specifikací celého návrhu.

**Kurzy:** kniha má nastavený zdroj (ČNB nebo ECB). Ukládá se i datum stažení a původ kurzu, aby šel každý výpočet zopakovat.

**Cena tohoto řešení:** desítky společností znamenají těžkopádnější přepínání v UI a vlastní souhrnné přehledy za SICAV.

**SICAV a podfondy:** SICAV má vlastní účetnictví jako samostatná společnost v Odoo a každý podfond také. V SICAV se investiční a neinvestiční část rozlišuje polem na účetním řádku, s výchozí hodnotou investiční. Neinvestiční část může mít vlastní bankovní účet a výsledek, proto se část dá nastavit i jako výchozí pro bankovní účet nebo deník. Výkazy se sestavují po částech i za celek a hodnota akcie se počítá jen z investiční části.

## Moduly

V Odoo vznikne sada vlastních addonů nad standardním účetním jádrem, bez úprav core a bez závislosti na Odoo Mates. Klíčové výpočty zůstávají ve verzovaném kódu s testy.

| Modul | Vrstva | Obsah | Závisí na |
| --- | --- | --- | --- |
| `investra_entity` | Základ | Registr knih: typ, rámec, funkční měna, zdroj kurzu, nadřazená jednotka, zakladatel | Odoo `account` |
| `investra_chart_*` | Základ | Šablony osnov a role účtů | `investra_entity` |
| `investra_rates` | Základ | Kurzy ČNB a ECB, zdroj a datum stažení | `investra_entity` |
| `investra_posting` | Základ | Událost, pravidlo podle rámce, účetní doklad, storno, ochrana proti dvojímu zaúčtování, vnitřní zúčtování tříd | role účtů |
| `investra_documents` | Základ | Oběh a schvalování dokladů na čtyři oči, práva podle účetních jednotek, rekonstrukce průběhu | `investra_entity` |
| `investra_fx_revaluation` | Účetní | Uživatelské skupiny účtů, protiúčty, metoda přecenění | `investra_posting`, `investra_rates` |
| `investra_fund` | Fond | Fondy, podfondy, třídy, kalendář ocenění, obchodní kalendář | `investra_entity` |
| `investra_instruments` | Fond | Instrumenty, ceny, portfoliové transakce, pozice | `investra_fund`, `investra_posting` |
| `investra_allocation` | Fond | Verzovaná alokační schémata a poměry tříd | `investra_fund` |
| `investra_is_bridge` | Integrace | Příjem závěrek, odesílání kurzů a číselníků, denní kontroly | `investra_fund`, `investra_posting` |
| `investra_nav` | Později | Ocenění, NAV, performance fee, publikace kurzu | vše výše |
| `investra_reporting` | Později | Neměnné snímky dat k datu | `investra_nav` |
| `investra_cnb` | Později | Výkazy ČNB | `investra_reporting` |
| `investra_limits` | Později | Investiční limity ze statutů, celková expozice závazkovou metodou, test základního investičního fondu | `investra_instruments` |
| `investra_annual_report` | Později | Výroční a pololetní zprávy fondů: export dat a číselných výstupů, finalizace zatím ve Wordu; u plného IFRS od 2027 struktura podle IFRS 18 | `investra_reporting` |

Hotová je jen kostra `investra_fx_revaluation` s jedním modelem a testem. V Odoo 20 se přístupová práva a záznamová pravidla sloučila do nového modelu ir.access (soubor security/ir.access.csv s operacemi crud a doménou), kostra je na to upravená. Práce na ní bude pokračovat až po `investra_entity` a `investra_posting`.

**Třídy:** každá má vlastní měnu (nezávislou na funkční měně fondu), parametry hurdle a performance a příjemce performance allocation. Performance allocation může přesouvat hodnotu mezi třídami, aniž by měnila celkové NAV podfondu. Třída může být růstová, nebo může vyplácet dividendy.

**Instrumenty:** Dluhopis, akcie, podíl ve společnosti, nemovitost, derivát a ostatní. Fondy často drží aktiva přes SPV jako majetkovou účast, takže pořizovací cena má složky (příplatek mimo základní kapitál, úvěr SPV). Hotovost instrument není, zůstává na bankovních účtech v hlavní knize. Evidence musí od začátku sbírat údaje pro ČNB, například LEI, CFI, sektor a zemi emitenta. U dluhopisů a derivátů také parametry pro ocenění: kupon, frekvenci, splácení, konvenci počítání dní, senioritu a rating.

**Pozice:** nezadávají se ručně, vypočtou se z transakcí k libovolnému datu. Provedená transakce se nepřepisuje, oprava je storno a nová transakce.

**Ceny:** mají historii, zdroj, autora a schválení. Oprava vznikne jako nová verze, aby šlo NAV zpětně zreprodukovat.

**Deriváty a podrozvaha:** deriváty jsou samostatný typ s oběma stranami obchodu a nominály. Fondy vykazují podrozvahové položky, například pohledávky a závazky z termínových operací a opcí a hodnoty předané k obhospodařování.

**Portfoliová transakce:** nese datum sjednání i vypořádání, okamžik zaúčtování určí účetní politika.

**Poplatky fondu:** výpočet úplat má vlastní parametry, například průměr fondového kapitálu za obchodní dny i při měsíčním NAV. Typy úplat ze statutů: fixní měsíční částka s pásmy podle objemu aktiv, procento z fondového kapitálu před výkonnostní odměnou poměrené délkou oceňovacího období, výkonnostní odměna s hurdle a DPH jako náklad. Výkonnostní odměna má dvě podoby: poplatek obhospodařovateli (závazek fondu) nebo alokace části zhodnocení na jinou třídu akcií (přesun mezi třídami). Model musí umět obě, s parametry sazba, hurdle, srovnávací období, high-water mark ano/ne a časové vážení toků. Výchozí pořadí je nejdřív úplaty, potom výkonnostní odměna; je to parametr fondu podle rozhodnutí o pořadí výpočtů. Vstupní a výstupní poplatky řeší IS.

**FX skupiny:** skupina = účty, protiúčty a metoda (storno, nebo jen rozdíl). Cenné papíry v cizí měně by měly být mimo FX skupiny a kurz řešit v ocenění, jinak hrozí dvojí započtení.

**Alokační schéma:** má platnost od data, základ (NAV, kusy, kapitál, pevná procenta), spouštěč, zaokrouhlení a účet zbytku. Doporučujeme typované volby místo volných vzorců kvůli auditu; specifika zakladatele řeší samostatné rozšíření.

## Procesy

Peníze investora nejdřív leží na závazku z úpisu v Odoo a kusy vznikají v IS. Ocenění smí začít až po závěrce klientských transakcí a jeho pořadí kroků je pevné.

### Úpis

1. Standardně úpis vzniká platbou: investor pošle peníze na účet třídy pro úpisy, s identifikátorem, který mu IS přidělilo předem. Peníze jsou na tomto účtu držené do úpisu a potom se převedou na investiční účet fondu. Alternativně investor zadá pokyn v IS ještě před platbou.
2. Odoo platbu spáruje podle identifikátoru. Účtuje se MD banka / D závazek z úpisu.
3. Odoo pošle IS potvrzení platby. Pokud IS pokyn ještě nemá, založí z něj úpis.
4. IS vydá kusy za poslední známý kurz, případně za ručně upravený. Rozhodující datum určuje nastavení fondu.
5. IS zahrne transakci do závěrky a Odoo ji zaúčtuje: MD závazek z úpisu / D kapitál třídy, případně poplatek.
6. IS spustí převod z účtu třídy pro úpisy na investiční účet fondu. Odoo ho na výpisech spáruje jako vnitřní převod.

Účty jsou ilustrační, konečné určí účetní politika a role účtů. Závazek z úpisu se vede s vazbou na platbu a identifikátor, aby šlo dohledat nevypořádanou platbu. Dokud proti penězům stojí závazek z úpisu, NAV se nemění.

**Podle statutů přibývá:** zbytek po zaokrouhlení počtu akcií dolů je výnosem fondu, vstupní přirážka a výstupní srážka jsou příjmem obhospodařovatele (závazek fondu vůči němu, ne výnos), a úpis může být i nepeněžitým vkladem oceněným znalcem. Závěrka z IS proto musí nést i zbytek částky, výši přirážky nebo srážky a typ vkladu.

### Odkup

Stejně jako u úpisu: peníze se při odkupu nejdřív převedou z investičního účtu fondu na účet třídy pro odkupy a z něj se posílají příjemci.

1. Provedený odkup přijde v závěrce. Odoo účtuje MD kapitál třídy / D závazek z odkupu.
2. IS spustí převod z investičního účtu fondu na účet třídy pro odkupy. Odoo ho na výpisech spáruje jako vnitřní převod.
3. IS vytvoří platební příkaz z účtu pro odkupy se stejným identifikátorem, jaký poslal do Odoo.
4. Odchozí platba se objeví na výpisu v Odoo. Účtuje se MD závazek z odkupu / D banka.

### Závěrka klientských transakcí

Závěrku vytváří IS pro každý fond zvlášť a v jednom oceňovacím období jich může být více.

- Závěrky na sebe chronologicky navazují a končí finalizací.
- Každá se v Odoo zaúčtuje samostatně, s vlastním datem, aby kapitál v účetnictví odpovídal počtu kusů.
- Ocenění převezme všechny závěrky od předchozího ocenění. Po použití jsou neměnné a IS se o tom dozví.
- Zrušit lze jen závěrky dosud nepoužité v ocenění, a to postupně od poslední. Zaúčtovaná závěrka se v Odoo stornuje.
- Závěrka k dnešku blokuje další realizace transakcí pro dnešek.

Sestavu pro depozitáře vytvoří IS ze závěrky, oceněná aktiva k ní dodá Odoo.

### Dividendy

Rozhodnutý je rámec: dividendu za třídu počítá a účtuje Odoo v hrubé výši, rozdělení držitelům, srážkovou daň a reinvestici řeší IS. Otevřené zůstávají podrobnosti (účet pro výplatu, dopad na kurz k rozhodnému dni).

1. Po schváleném ocenění Odoo připraví návrh dividendy na kus a rozhodný den. Zatím se nic neúčtuje.
2. Návrh schválí obhospodařovatel a depozitář a o výplatě rozhodne příslušný orgán podle stanov a statutu; stanovisko i rozhodnutí se evidují v Odoo. Teprve potom se účtuje MD kapitál třídy / D závazek z dividend k datu rozhodnutí.
3. Odoo pošle rozhodnutí do IS.
4. IS spočítá nárok podle držitelů k rozhodnému dni, srážkovou daň a reinvestici, spustí převod a vytvoří platební příkazy.
5. Odchozí platba se objeví na výpisu v Odoo. Účtuje se MD závazek z dividend / D banka.

### Ocenění a alokace (rámcově)

Alokační poměr vzniká před výpočty přecenění.

1. Kontrola: všechny závěrky k datu jsou přijaté.
2. Předběžný kapitál třídy a alokační poměr.
3. Přecenění aktiv a FX.
4. Výpočty za třídy v pořadí podle statutu, výchozí je: úplaty, performance fee, očekávaná daňová povinnost, dohadné položky. Performance fee se počítá z hodnot před daní, pořadí je parametr fondu.
5. Návrhy dokladů; zaúčtují se jedním krokem po schválení, před odesláním depozitáři (viz Postup ocenění v Odoo).
6. Finální kapitál tříd a kontrolní rovnice.
7. Kontrola shody cenných papírů fondu s evidencí v IS.
8. Kontrola shody majetku fondu s účetnictvím a změny vlastního kapitálu nad prahem (výchozí 5 %, parametr se zdrojem v předpisu).
9. Výpočet hodnoty na kus (FKCP), výchozí zaokrouhlení na 4 desetinná místa dolů, pokud statut neurčí jinak.
10. Kontrola druhou osobou, pro fondy Investry povinná; další schvalovatelé před zaúčtováním jsou parametr fondu.
11. Zaúčtování návrhů jedním krokem k datu ocenění.
12. Odeslání zaúčtovaného ocenění depozitáři a evidence jeho stanoviska.
13. Zveřejnění kurzu a uzamčení ocenění a období.

**Stanovisko obhospodařovatele a depozitáře:** v Odoo se eviduje verze ocenění, datum odeslání, kdo a kdy schválil nebo vrátil, způsob a příloha. Ocenění vrácené před zaúčtováním se opraví v návrzích jako nová verze, bez storen. Když ho vrátí depozitář po zaúčtování, stornují se všechny doklady ocenění a zaúčtuje se nová verze. Kurz jde do IS až po stanovisku depozitáře.

Předběžný kapitál třídy T ke dni D (pohyby za všechny závěrky od předchozího ocenění):

```latex
PFKT(D) = FKT(D-1) + IAVT(D-1) - IAOT(D-1)
```

U třídy vyplácející dividendy se předběžný kapitál sníží o dividendu přiznanou od předchozího ocenění. Poznámky k alokaci dividendy nepokrývaly, jde o náš návrh k ověření.

Finální kapitál třídy a kontrola, která je povinná vždy:

```latex
NFK(D) = FK(D) - \sum_{T} \Delta_{T}
```

```latex
FKT(D) = APT(D) \cdot NFK(D) + \Delta_{T}
```

```latex
FK(D) = \sum_{T} FKT(D)
```

APT je alokační poměr třídy, FK celková čistá aktiva fondu z rozvahy, ΔT změna rozvahových položek označených třídou T od předchozího ocenění (včetně řádků s třídou T na účtu vnitřního zúčtování) a NFK čistá aktiva bez těchto změn. Potvrzeno: APT = PFKT / PFK a IAV a IAO jsou vydané a odkoupené investiční akcie.

**Výpočet tříd vychází pouze z rozvahy.** Výsledkové účty do něj nevstupují. Rozhoduje změna za období, ne celkový stav, protože alokační poměr už starší specifické položky obsahuje.

**Vnitřní zúčtování tříd:** každý přesun mezi majetkem třídy a společným majetkem jde přes jeden účet s touto rolí. Zápis má řádek bez třídy a řádek s třídou, takže účet má za fond zůstatek vždy nula. Banka a aktiva tak zůstávají společné. Zápis vytváří automaticky `investra_posting`.

Příklad: třídy A a B po 100, performance fee třídy A 10.

| Krok | Zápis | ΔA | FK | NFK | Třída A | Třída B |
| --- | --- | --: | --: | --: | --: | --: |
| Výchozí stav |  |  | 200 | 200 | 100 | 100 |
| Zaúčtování fee | D závazek (třída A) 10 | −10 | 190 | 200 | 90 | 100 |
| Platba fee | MD závazek (A) / D banka 10; MD zúčtování / D zúčtování (A) 10 | −10 | 190 | 200 | 90 | 100 |
| Společný výnos 19 |  | −10 | 209 | 219 | 99,5 | 109,5 |

Platbou fee se ΔA nemění: závazek třídy A zanikne, ale stejná částka zůstane na účtu vnitřního zúčtování s třídou A. Společný výnos se dělí alokacím poměrem platným od začátku období (50 : 50), takže A = 0,5 · 219 − 10 = 99,5 a B = 109,5. Při dalším ocenění se ΔT promítne do předběžného kapitálu třídy a počítá se znovu od nuly. Příklad bude první automatický test modulu `investra_nav`.

V prototypu ověříme okamžik vzniku zápisu, průběžné uzavírání zůstatku za třídu a chování třídy v jiné měně, než je funkční měna fondu.

**Pohyby uvnitř období:** výchozí varianta je vstup všech pohybů do poměru najednou. Přesnější rozdělení na podobdobí bude volba alokačního schématu.

### Postup ocenění v Odoo (návrh)

Ocenění je v `investra_nav` jeden záznam pro fond, datum a verzi. Účetní jím prochází krok za krokem, každý krok má stav a další se otevře až po dokončení předchozího. Záznam si ukládá použité ceny, kurzy a parametry, takže výpočet půjde kdykoli zopakovat. Portfolio i účetnictví jsou v jednom systému, proto odpadá přenos souborů mezi systémy a rozdíly mezi nimi.

| Krok | Co se děje | Výstup |
| --- | --- | --- |
| 0. Příprava | Závěrky z IS, spárovaná banka, zaúčtované portfoliové transakce, kurzy, naběhlé úroky, opravné položky, nároky na dividendy a kupóny | Kontrola připravenosti, alokační poměr tříd |
| 1. Schválení cen | Import a ruční zadání cen, zvýraznění starých a posledních známých cen, ocenění SPV s podkladem, stanovisko depozitáře k cenám, pokud ho fond vyžaduje | Schválený seznam cen |
| 2. FX přecenění | Skupiny účtů mimo instrumenty, zvlášť banky a úvěry, možnost nést třídu | Návrh dokladu |
| 3. Reálná hodnota | Řádek na každou pozici: kusy, cena, kurz, změna RH a FX | Návrh dokladu, evidence RH |
| 4. Poplatky, dohady, daň | Pravidla fondu v pořadí podle statutu, rozpis výpočtu každé částky | Návrhy dokladů |
| 5. NAV a cena za kus | FK z rozvahy včetně návrhů, rozdělení na třídy, kusy z IS, zaokrouhlení podle třídy | Výpočet NAV |
| 6. Kontroly a sestava | Automatické kontroly se stavem OK, upozornění nebo stop | Sestava ke schválení |
| 7. Kontrola a schválení | Kompletní finální ocenění po poplatcích, dohadech a dani, sumář z nezaúčtovaných návrhů, zamčené návrhy a snímek. Kontrola druhou osobou je u fondů Investry povinná, schválení vedením fondu volitelné. Kdo a v jakém pořadí schvaluje před zaúčtováním, včetně administrátora a obhospodařovatele, je parametr fondu. Vrácení znamená opravu návrhů a novou verzi, bez storen | Schválený sumář |
| 8. Zaúčtování | Zaúčtování jedním krokem k datu ocenění s kontrolou shody se schváleným sumářem | Zaúčtované doklady |
| 9. Depozitář | Depozitář dostává finálně zaúčtované ocenění. Vrácení znamená storno všech dokladů ocenění a zaúčtování nové verze, ne rozdílový doklad | Stanovisko depozitáře |
| 10. Zveřejnění a uzamčení | Kurz do IS a zveřejnění až po stanovisku depozitáře; uzamčení ocenění i období až potom, aby šlo storno zaúčtovat k datu ocenění | Publikovaný kurz, uzamčené období |
| 11. Navazující kroky | Úhrada poplatků, snímek pro výkazy ČNB, výpočtový list pro řízení rizik | Podklady |

**Zaúčtování (rozhodnuto, varianta B):** na schválení jde kompletní finální ocenění, tedy po poplatcích, dohadech a dani. Kroky 2 až 4 vytvářejí návrhy dokladů a sumář vzniká z těchto nezaúčtovaných návrhů. Po schválení podle parametrů fondu se návrhy zaúčtují jedním krokem k datu ocenění a depozitář dostane finálně zaúčtované ocenění. Vrácení před zaúčtováním znamená opravu návrhů a novou verzi, bez storen. Vrácení depozitářem znamená storno všech dokladů ocenění a zaúčtování nové verze, ne rozdílový doklad. Oprava po zveřejnění se řídí částí Oprava chybného NAV.

**Požadavky na zajištění (ověřeno v kódu Odoo 20, prototypem zatím ne):**

- NAV a sumář počítají zaúčtovaný stav plus návrhy daného ocenění, protože standardní zůstatky berou jen zaúčtované doklady.
- Po odeslání ke schválení se návrhy zamknou a uloží se snímek; každá změna znamená novou verzi.
- Před zaúčtováním se zkontroluje, že stav odpovídá schválenému sumáři; jinak se ocenění vrací k přepočtu.
- Ocenění a období se uzamknou až po stanovisku depozitáře, aby šlo storno zaúčtovat k datu ocenění.
- Zamknuté návrhy chrání serverový zámek. Standardní \_post kontroluje jen účetní skupinu, proto modul musí bránit zaúčtování, změně i návratu do návrhu mimo schválený postup.
- Automatické účtování přijatých faktur je v šabloně společnosti vypnuté.

**Pravidla poplatků (doporučení, k rozhodnutí):** u fondu se vede sada typovaných pravidel s platností od data a odkazem na článek statutu. Pravidlo má typ, základ, sazbu nebo pásma, minimum a maximum, DPH, roční základ (365 nebo 366 dní), role účtů a třídu. Typy: pevná částka s pásmy, procento ze základu, výkonnostní odměna, daň, dohad a ruční položka s důvodem. Nový typ je malé rozšíření v kódu s testem. Volné vzorce ani tabulky mimo systém nedoporučujeme kvůli auditu.

**Kruhová závislost:** úplata může být procentem z FK po úplatě a daň závisí na úplatě. Výpočet to musí vyřešit sám, přímým vzorcem nebo opakováním do ustálení, s výsledkem a počtem kroků v rozpisu.

**Dohady:** částka se účtuje jako doúčtování proti tomu, co už je zaúčtované. Typy: pevná roční částka rozdělená na dny, skutečná částka, částka podle podkladu a částka podle NAV. Po přijetí faktury se dohad rozpustí a sleduje se rozdíl proti odhadu. U denních fondů půjde rozpis po dnech.

**Výkonnostní odměna:** účtuje se jen při splnění všech podmínek ze statutu, jako doplatek do potřebného zůstatku, tedy i se záporným pohybem. Sestavy před odměnou a po odměně se porovnají automaticky: změnit se smí jen očekávané účty.

**Parametry výkonnostní odměny:** vedou se po třídách: high-water mark, etalon a jeho kurz, sazba a základ průměrného počtu kusů. Výpočet ukáže odměnu, FK a cenu za kus po odměně a částku k zaúčtování.

**Daň:** výpočet vychází z výsledku před daní a z typovaných úprav základu (osvobozené výnosy, dividendy, nedaňové náklady, ztráta minulých let). Fond může mít víc základů s různou sazbou, například samostatný základ pro určitou účast. Záporný základ znamená nulovou daň a účtuje se rozdíl proti zaúčtované dani.

**Sražená daň z dividend:** jedna dividenda může mít víc sazeb podle země a držby. Nárok vzniká k rozhodnému dni, případný kurzový rozdíl k výplatě se dorovnává.

**Úvěry SPV a účasti:** ocenění SPV se zadává před výpočtem RH. U účasti se závazkem k dalším vkladům se platba vede jako pořízení a do investice se zařadí až s podkladem k ocenění; závazek je v podrozvaze a přeceňuje se kurzem. Účty určuje role podle nástroje, ne ruční úprava dokladu.

**Kontrola připravenosti:** před výpočtem portfolia se zkontrolují nedokončené položky k datu: budoucí účetní zápisy, obchody s cennými papíry, termínované vklady a REPO. Nedokončená položka ocenění zastaví, nebo ji účetní vědomě potvrdí.

**Kontroly v kroku 6:**

- zůstatek banky proti výpisu, technický účet peněz na cestě rovná se nule,
- bankovní účty pro úpisy a odkupy proti závazkům vůči držitelům,
- pozice proti saldu účtů, v měně i ve funkční měně,
- kusy proti IS a depozitáři, kolaterál proti potvrzení protistrany,
- nároky na kupóny a dividendy proti výpisům,
- přepočet úplat po změně FK, změna FK nad prahem, stáří cen,
- předběžné kontroly ČNB z katalogu `docs/cnb`: skok jednotkové ceny v RISIFI33, vazba přecenění v TISIFI10 na změny v RISIFI30, meziobdobní změny nad práh s komentářem.

**Sestava ke schválení:** přemostění FK (počáteční FK, úpisy a odkupy, FX, RH, úplaty, výkonnostní odměna, daň, konečný FK), pevné řádky aktiv a pasiv plněné ze seznamu rolí účtů, výpočet po třídách, změna ceny za kus, seznam cen a výjimky.

**Balíček pro audit:** jedno tlačítko za období: výpočty NAV, obchody, deriváty a předvaha.

### Reálná hodnota instrumentů

Ceny vstupují do Odoo podle oceňovací politiky fondu a do účetnictví se promítnou při ocenění, odděleně kurzový rozdíl a přecenění na reálnou hodnotu.

**Oceňovací politika:** platí pro fond a druh aktiva, s možností šablony. Určuje metodu, zdroj, kdo cenu dodává a zda se schvaluje.

| Aktivum | Typický zdroj | Vstup do Odoo |
| --- | --- | --- |
| Kotované akcie a dluhopisy | Tržní data, výpis depozitáře | Import, později napojení |
| Podíly v jiných fondech | NAV od správce | Import nebo ruční zadání |
| Neobchodované dluhopisy a úvěry | Model | Ruční zadání s přílohou |
| Podíly ve společnostech | Model, posudek | Ruční zadání s přílohou |
| Nemovitosti | Znalecký posudek | Ruční zadání s přílohou |
| Deriváty | Protistrana, model | Import nebo ruční zadání |
| REPO a reverzní REPO | Smlouva, potvrzení protistrany | Import nebo ruční zadání; samostatný druh nástroje s vlastními řádky výkazů |

Začínáme importem z Excelu a ručním zadáním. Odoo modely nepočítá, eviduje výslednou cenu a podklad k ní.

**Záznam ceny:** instrument, datum, cena, měna, u dluhopisů čistá cena a naběhlý úrok, zdroj, metoda, úroveň podle IFRS 13, autor a schválení. Podklad se přikládá k záznamu. U schválené ceny se ukládá otisk souboru, aby byla příloha neměnná, a soubory se zálohují spolu s databází. Vede se také evidence znalců a kontrola náležitostí posudku.

**Kontroly před oceněním:**

- Použije se vždy poslední známá cena. Výpočet zastaví jen instrument bez ceny.
- Stará cena nebo odchylka nad limit se zobrazí jako upozornění pro schvalovatele. U nelikvidních aktiv interní oceňovatel doloží, že poslední hodnota stále platí. U úrovně 3 je součástí ocenění citlivostní analýza.
- Počty kusů se porovnají s výpisem depozitáře.
- Ocenění si uloží použité ceny a kurzy, aby šlo zopakovat.

**Zaúčtování:** hodnota instrumentu je na třech účtech: pořizovací cena (u dluhových nástrojů naběhlá hodnota), kurzový rozdíl a přecenění na reálnou hodnotu. Každý má svou roli a protiúčet. Protiúčty určí klasifikace nástroje podle IFRS 9 podle matice níže. Kurz se bere vždy k datu ocenění, i když je cena starší.

```latex
FX = C_{m} \cdot (K_{D} - K_{0})
```

```latex
FV = (RH_{m} - C_{m}) \cdot K_{D}
```

Cm je pořizovací cena v měně instrumentu, RHm reálná hodnota v měně, K0 pořizovací kurz a KD kurz k datu ocenění. Příklad: nákup za 100 EUR při kurzu 25, k datu cena 110 EUR a kurz 24. FX je −100 Kč, FV +240 Kč, celkem +140 Kč.

Obě složky se účtují jako doplatek do potřebného zůstatku, takže opakovaný výpočet nic nezdvojí. Doklad má řádek na každou pozici a denně se porovná hodnota pozic s hlavní knihou.

**Částečný prodej:** u počítatelných nástrojů, například kusů cenných papírů, se použije průměr. Kde kusy nejsou, například částečná splátka investice do fondu bez cenných papírů, určí uživatel, jaká část pořizovací ceny se odúčtuje, a uvede důvod. S touto částí se poměrně odúčtuje i přecenění a kurzový rozdíl, ten na samostatné výsledkové účty. U nástrojů ve FVTPL vzniká realizovaný výsledek. U majetkových nástrojů ve FVOCI se do výsledku nic nepřeúčtovává, oceňovací rozdíl se převede v rámci vlastního kapitálu do nerozděleného zisku. U dluhových nástrojů ve FVOCI se oceňovací rozdíl z vlastního kapitálu recykluje do výsledku.

**Matice IFRS 9 a IAS 21** (k ověření s auditorem a v účetní politice):

| Kategorie | Přecenění na RH | Kurzový rozdíl | Při prodeji nebo splacení |
| --- | --- | --- | --- |
| FVTPL (akcie, dluhové nástroje, deriváty) | výsledek | výsledek | realizovaný výsledek |
| Majetkové nástroje ve FVOCI (neodvolatelná volba) | vlastní kapitál | vlastní kapitál (nepeněžní položka) | bez recyklace, převod do nerozděleného zisku; dividendy do výsledku |
| Dluhové nástroje ve FVOCI | vlastní kapitál | výsledek, z naběhlé hodnoty (peněžní položka) | recyklace z vlastního kapitálu do výsledku |
| Naběhlá hodnota (úvěry, dluhopisy držené do splatnosti) | nepřeceňuje se | výsledek, z naběhlé hodnoty | realizovaný výsledek |

U dluhových nástrojů ve FVOCI a v naběhlé hodnotě se úrok počítá efektivní úrokovou mírou a opravné položky (očekávané úvěrové ztráty) jdou do výsledku. Kurzový rozdíl se pak nepočítá z pořizovací ceny, ale z naběhlé hodnoty v měně nástroje, takže vzorec FX výše platí jen pro nástroje bez úročení. Zdroje: IFRS 9 odst. 5.7.1, 5.7.5, 5.7.10–5.7.11, B5.7.2–B5.7.3; IAS 21 odst. 23, 28 a 30. V příkladech fondů je zatím vše ve FVTPL nebo jako majetková účast ve FVOCI; dluhové FVOCI a naběhlou hodnotu musí model umět kvůli úvěrům do SPV a budoucím fondům.

### Evidence výpočtu NAV

Odoo povede evidenci výpočtu NAV. Pro každý fond a výpočet eviduje:

- identifikaci cenného papíru a periodicitu,
- základnu výpočtu a všechny použité údaje, včetně počtu kusů a rozdělení podle druhů,
- vypočtenou hodnotu,
- kdo vypočítal a kdo zkontroloval, s daty,
- datum stanoviska obhospodařovatele a schválení depozitářem,
- datum zveřejnění.

Výsledek se reportuje depozitáři, ČNB, investorům a u kotovaných cenných papírů burze. Výpočtový list dostává i řízení rizik pro investiční limity.

### Oprava chybného NAV

Oprava má pevný postup, protože může změnit už vydané kusy a vyplacené částky.

1. Odoo vytvoří novou verzi ocenění a provede znovu všechny kroky ocenění.
2. U složitější opravy se sepisuje protokol a informuje se depozitář.
3. Pokud mezitím proběhl úpis nebo odkup, Odoo pošle IS kurz s příznakem opravy.
4. IS určí dopad: dodatečnou emisi, opravu kusů, doplacení nebo narovnání s investorem.

Odchylka do prahu (dnes 0,5 % FK podle vnitřního předpisu pro oceňování) nevyžaduje opravu kusů ani zveřejnění opravené hodnoty. Práh je parametr; u každého prahu a lhůty se v nastavení eviduje zdroj (předpis nebo statut, článek, verze) a platnost od data.

### Platnost a zveřejnění kurzu

Každý fond má jeden ze dvou modelů.

- **Zpětná platnost:** kurz platí pro datum a daný počet dní zpět, s pravidly pro víkendy, svátky a pozastavené obchodování. Vhodné pro denní fondy.
- **Ručně definované období:** kurz platí od–do, s vyhlášeným datem a kontrolou překrytí období.

Záznam kurzu nese také plánované a skutečné zveřejnění a příznak technického kurzu, který se nezveřejňuje. Ocenění nejde poslat obhospodařovateli a depozitáři, dokud nejsou tyto parametry vyplněné.

## Rozhraní Odoo a IS

Systémy si vyměňují devět typů zpráv, hlavní je finalizovaná závěrka. Jde o pracovní minimum, které je potřeba ověřit proti možnostem IS.

| Zpráva | Směr | Obsah |
| --- | --- | --- |
| Číselník fondů a tříd | Odoo → IS | Fond, třída, ISIN, měna, stav, model kurzu |
| Identifikátory plateb a převodů | IS → Odoo | Investor nebo smlouva, fond, třída; u výplat a převodů také částka |
| Potvrzení platby | Odoo → IS | Identifikátor, částka, datum přijetí |
| Závěrka | IS → Odoo | Hlavička, transakce, součty za třídu |
| Kurz | Odoo → IS | Datum ocenění, platnost od–do, vyhlášené datum, zveřejnění, technický kurz, příznak opravy |
| Použití závěrky | Odoo → IS | Závěrka, ocenění, ve kterém byla použita |
| Denní stav kusů | IS → Odoo | Třída, datum, počet kusů |
| Agregace držitelů pro ČNB | IS → Odoo | Struktura podle sektoru a rezidence, bez osobních údajů |
| Rozhodnutí o dividendě | Odoo → IS | Třída, dividenda na kus, rozhodný den, den výplaty |

**Závěrka obsahuje:** fond, období od–do, pořadové číslo a návaznost na předchozí závěrku, kdo a kdy ji finalizoval. Za každou transakci identifikátor pokynu, třídu, typ, kusy, cenu, částku, poplatek, datum kurzu, datum obchodu a vypořádání a příznak ruční úpravy kurzu. Za třídu součty vydaných a odkoupených kusů a částek a koncový stav.

**Technická pravidla:**

- Zprávy jsou verzované a mají jednoznačné ID, aby opakované doručení nezpůsobilo dvojí zaúčtování.
- Při výpadku se zprávy uloží a doručí později se zachovaným pořadím.
- Storno v IS vyvolá storno v Odoo, nikdy ne přepsání.

**Kontroly v Odoo:**

- Závěrka nenavazující na předchozí se odmítne.
- Cena se porovná s posledním zveřejněným kurzem. Rozdíl bez příznaku je chyba, s příznakem se jen zobrazí v přehledu.
- Přijatá částka se porovná s hodnotou pokynu. Přeplatek nebo nedoplatek zůstane na závazku, dokud se nevyřeší.
- Denně se porovná stav kusů v IS s účetním kapitálem a peníze s účetnictvím. Rozdíl se ukáže jako výjimka.

## Detail dat pro výroční zprávy a ČNB

Každý údaj se uloží jednou, u kmenových dat nebo na účetním řádku, a všechna členění se odvodí až ve snímku k datu. Členění se nekóduje do účtové osnovy, protože osnovy se liší podle zakladatelů a účtů by bylo neudržitelně mnoho.

**Co vyžadují výroční zprávy a přílohy** (podle příkladů fondů):

- rozvaha a výsledovka ve formátu vyhlášky 501/2002, po částech fondu a za celek,
- členění podle kategorie IFRS 9 a úrovně hierarchie reálné hodnoty,
- měnová struktura aktiv a pasiv, zbytková splatnost a úroková pásma, zeměpisné členění, koncentrace podle protistran,
- detail úvěrů (dlužník, data, limit, jistina, reálná hodnota) a účastí (podíl, základní kapitál, pořizovací cena, příplatky, výsledek společnosti),
- rozpad správních nákladů, ostatních pasiv a dohadných položek podle účelu, úplaty obhospodařovateli, depozitáři, administrátorovi a auditorovi,
- přehled změn čistých aktiv (emise, odkupy, oceňovací rozdíly, výsledek) a vývoj počtu akcií a FK na akcii,
- citlivost a vstupy úrovně 3, podrozvaha, daňový výpočet, spřízněné osoby, majetek nad 1 % hodnoty fondu.

**Co vyžadují výkazy ČNB** (ověřeno ve veřejné metodice SDAT, rámec Fondy, metodika FOFI20261201 platná od 1. 12. 2026):

- stavy aktiv a pasiv v hrubé hodnotě (bez opravných položek a oprávek) podle druhu, země protistrany (ČR, eurozóna po jednotlivých státech, ostatní), sektoru ESA 2010 a původní splatnosti do a nad 1 rok (RISIFI30); u úvěrů navíc revolvingové úvěry a přečerpání a úvěry s pákovým efektem,
- cenné papíry jednotlivě (RISIFI33): s ISIN jen počet nebo nominál a reálná hodnota; bez ISIN i druh, měna, sektor, země emitenta, naběhlé příslušenství, jednotková cena, datum emise a splatnosti; vydané cenné papíry fondu po ISIN se zemí a sektorem držitele,
- změny z přecenění (cenou i kurzem) zvlášť pro deriváty s kladnou a zápornou reálnou hodnotou a pro nefinanční aktiva (TISIFI10),
- objem vydaných a odkoupených akcií za měsíc (RISIFI37); příjmy fondu a vyplacené dividendy na jednu akcii po kódu cenného papíru třídy a měně (VISIFI10); úplaty zaplacené investory fondu za rok (VISIFI20),
- rozvaha a výsledovka podle vyhlášky 501/2002 v kategoriích IFRS 9, čtvrtletně, výsledovka kumulativně od počátku roku (ROFOS10, VYFOS20); u SICAV bez podfondu ve sloupcích Investiční činnost, Ostatní činnost a Vzájemný zápočet; reálná hodnota v úrovních 1 až 3 podle druhu nástroje; deriváty podle rizika (úrokové, akciové, měnové, úvěrové) a podle OTC nebo burzy; zatížená aktiva; úrokové výnosy a dividendy podle kategorie IFRS 9 zdrojového aktiva,
- po třídách (ROFOS13): počty a objemy cenných papírů na začátku, vydané, odkoupené a na konci; FK třídy v CZK a v měně třídy; FK a počty investorů podle domicilu (ČR, EU, ESVO, ostatní), počty fyzických osob, PEP a právnických osob; použité nástroje řízení likvidity,
- po nástrojích (DOFOS31): pořizovací a reálná hodnota, způsob ocenění, vztah k investičnímu limitu podle NV 243/2013 a podíl na emisi emitenta; u OTC derivátů protistrana, podkladové aktivum a riziko protistrany; metoda výpočtu celkové expozice; měnová expozice a nominál měnových derivátů po měnách; kryptoaktiva,
- klasifikace fondu (KLISIFI10): distribuce zisku, převažující typ aktiv, geografické zaměření, investorská základna, ETF, PEF, frekvence odkupů a klasifikace podle SFDR.

### Kde bude detail uložený

| Úroveň | Atributy | Modul |
| --- | --- | --- |
| Účetní řádek | role účtu, část fondu, třída, protistrana, nástroj, měna a částka v měně, **typ pohybu** (transakce, přecenění cenou, přecenění kurzem, naběhlý úrok, úpis, odkup, dividenda, ostatní změna) | `investra_posting` |
| Protistrana | země a rezidence, institucionální sektor (ESA 2010), IČO, LEI, spřízněná osoba a typ vztahu (IAS 24), role (depozitář, obhospodařovatel, administrátor, auditor, znalec) | `investra_entity` |
| Nástroj | druh podle ČNB (vč. ETF, strukturovaný produkt, kryptoaktivum), kategorie IFRS 9, úroveň hierarchie RH, ISIN a CFI, emitent, měna, splatnost a původní splatnost, úročení, nominál, vztah k limitu podle NV 243/2013, burzovní nebo OTC, u derivátu riziko (úrokové, akciové, měnové, úvěrové) a opce ano/ne, u úvěru revolving a pákový efekt | `investra_instruments` |
| Registry nástrojů | úvěr (limit, čerpání, splátky), účast (podíl, ZK, příplatky, údaje společnosti), derivát (obě nohy, podkladové aktivum, protistrana), nemovitost (údaje pro DOFOS40), zatížení aktiva (zástava, zapůjčení cenných papírů) | `investra_instruments` |
| Účet a role | řádek rozvahy a výsledovky podle rámce jednotky (vyhláška 501/2002, nebo IFRS), řádek přílohy (druh nákladu, dohadu), daňový režim, položka ČNB; výnosové účty (úroky, dividendy) berou kategorii IFRS 9 z nástroje na řádku | `investra_chart_*` |
| Ocenění | vstupy a metoda, vstupy úrovně 3, citlivost | `investra_nav` |
| Snímek k datu | zbytková splatnost a úroková pásma, měnová a zeměpisná struktura, koncentrace, majetek nad 1 %, citlivost ±10 %, přehled změn čistých aktiv | `investra_reporting` |

**Typ pohybu je klíčový.** Bez něj nejde sestavit rozklad změn pro ČNB ani přehled změn čistých aktiv. Oddělení kurzového rozdílu a přecenění na reálnou hodnotu na různé účty, které už máme, ho zároveň výrazně usnadňuje.

**Strukturovaná pole, ne analytika.** Atributy pro výkazy budou pole s kontrolou. Analytika zůstane pro manažerské členění.

**Kontrola úplnosti:** role účtu určí povinné atributy (např. úvěr vyžaduje protistranu se sektorem a zemí a nástroj se splatností). Chybějící údaje se zastaví už při zaúčtování, nebo nejpozději jako výjimka před schválením ocenění a před odesláním výkazu.

**Převodové tabulky** (role → řádek vyhlášky a výkazu, druh nástroje a sektor → položka ČNB) budou nastavení s platností od data, ne kód. Výkazy se mění. Například nařízení ECB (EU) 2024/1988 (ECB/2024/17), přepracované znění statistiky investičních fondů, se používá od referenčního období prosinec 2025; podle vnitřního předpisu s ním souvisí nové výkazy KLISIFI10, VISIFI10 a VISIFI20 a úpravy RISIFI30 a RISIFI33 (vazbu ověřit v Knihovně SDAT). Převodové tabulky jsou pro každý účetní rámec zvlášť: výkazy ČNB mají pevnou strukturu, takže i jednotka na plném IFRS potřebuje převod svých rolí účtů na položky ČNB.

## Výroční zprávy

Výroční a pololetní zprávy fondů budou samostatný modul `investra_annual_report` nad vrstvou reportů. Je to dokument nad účetnictvím a fondovými daty, ne nová evidence, proto stojí až na nich.

**Co zpráva skládá:**

- **Účetní závěrku:** podle rámce jednotky. U CAS rozvahu a výsledovku ve formátu pro finanční instituce (vyhláška 501/2002), se sloupci investiční a neinvestiční část a celek, a přehled změn čistých aktiv držitelů. U jednotek na plném IFRS výkazy podle IAS 1, který pro období začínající od 1. 1. 2027 nahrazuje IFRS 18, přijatý EU v únoru 2026 (finanční pozice, výsledek a ostatní úplný výsledek, změny vlastního kapitálu nebo čistých aktiv, peněžní toky) a přílohu s povinnými IFRS zveřejněními (IFRS 7, IFRS 13). Modul musí umět i strukturu výkazů podle IFRS 18.
- **Přílohu závěrky:** účetní metody, členění portfolia, podrozvahu, úplaty, daň.
- **Profil fondu a vývoj FK a hodnoty akcie** po třídách.
- **Textové části:** činnost fondu, zpráva o vztazích, zpráva auditora (vkládá se).

**Proč samostatně:** formát určuje zákon a mění se, data berou všechny ostatní moduly a vystupuje z toho hotový dokument. Oddělení usnadní verzování šablon a audit. Textové části a přílohy, které nejsou v datech, se budou vkládat ručně nebo z předloh.

Základní číselné výstupy (rozvaha, výsledovka) mohou vzniknout i dřív ze standardních reportů podle zvolené edice. Modul `investra_annual_report` je složí do zákonné podoby zprávy. Zpráva se zatím finalizuje ve Wordu: Odoo vyexportuje data a číselné výstupy, dokument se dokončí ručně. Generování celé zprávy v Odoo přijde v úvahu později.

## Výkazy ČNB

Výkazy pro fondy jsou převážně měsíční, takže data musí být k dispozici i u fondů s delším intervalem ocenění. Zasílají se přes SDAT. Struktura, popisy a kontroly jsou převzaté z veřejné metodiky SDAT (sdat.cnb.cz/sdat\_ext, Metodické informace → Výkazy, rámec Fondy). Rámec má 22 výkazů; v tabulce jsou ty, které se nás týkají.

| Výkaz | Obsah | Frekvence u fondů | Hlavní zdroj dat |
| --- | --- | --- | --- |
| RISIFI30 | Bilance aktiv a pasiv | Měsíčně, do 25. dne | Hlavní kniha |
| RISIFI33 | Držené cenné papíry, účasti a vydané cenné papíry | Měsíčně, do 25. dne | Portfolio, IS |
| TISIFI10 | Změny v ocenění | Měsíčně, do 25. dne | Ocenění |
| RISIFI37 (FKI 5-12) | Objem vydaných a odkoupených cenných papírů | Měsíčně, do 30 dnů | Závěrky z IS |
| VISIFI10 | Příjmy fondu a vyplacené dividendy | Měsíčně, do 25. dne | Hlavní kniha, IS |
| VISIFI20 | Úplaty fondu | Ročně, do konce 4. měsíce | Hlavní kniha |
| KLISIFI10 | Klasifikační údaje fondu | Při vzniku nebo změně | Registr fondů |
| DOFOS31 | Struktura investičních nástrojů | Čtvrtletně | Portfolio |
| DOFOS40 | Údaje o nemovitostech | Čtvrtletně | Portfolio |
| ROFOS13 | Hlášení fondu kvalifikovaných investorů | Ročně | Registr fondů, ocenění |
| ROFOS11 | Hlášení fondu kolektivního investování (speciální fondy) | Ověřit v plánu výskytů SDAT | Registr fondů, ocenění, IS |
| VYFOS20 | Výkaz zisku a ztráty | Čtvrtletně, kumulativně od počátku roku | Hlavní kniha |
| ROFOS33, ROFOS35 | Hlášení obhospodařovatele | Do 30 dnů od konce období | Portfolio, rizika |

Za Investru jako administrátora a obhospodařovatele se podávají ROFOS10, VYFOS20 a hlášení obhospodařovatele (ROFOS33, DOFOS60). Údaje v cizí měně se pro výkazy přepočítávají kurzem ČNB.

**Účetní výkazy fondu.** ROFOS10 (rozvaha) a VYFOS20 (výsledovka) se podle metodiky nepodávají jen za společnost, ale i za obhospodařovaný fond. Podfond a podílový fond plní sloupec Investiční činnost, SICAV s podfondy za sebe sloupec Ostatní činnost. SICAV bez podfondu dělí částky do sloupců Investiční činnost, Ostatní činnost a Vzájemný zápočet. To přesně odpovídá poli část fondu a účtu vnitřního zúčtování: vzájemný zápočet jsou zůstatky na tomto účtu.

### Kontroly ČNB

SDAT u každého výkazu publikuje kontroly ve dvou skupinách: jednovýkazové (JVK, v rámci výkazu) a mezivýkazové (MVK, mezi výkazy a obdobími). Závažnost je *závažná* (výkaz neprojde), *varování* nebo *potvrzení* (nutné vysvětlení). Odoo bude stejné kontroly spouštět před exportem, aby se chyby našly u nás, ne až v SDAT. Příklady, které ovlivňují návrh:

- **Součty a souhrny:** součty podpoložek a zemských členění v RISIFI30 (34 JVK), aktiva celkem = pasiva celkem, v ROFOS10 aktiva = pasiva v každém sloupci.
- **Rozvaha proti rozpadu RH:** řádky kategorií IFRS 9 v ROFOS10 se musí rovnat součtům podle úrovní RH. Úroveň a kategorie proto musí být u každého nástroje.
- **NAV po třídách:** FK v ROFOS10 = součet FK tříd v ROFOS13; emitované akcie v RISIFI30 = hodnota tříd v ROFOS13; počty akcií v ROFOS13 = RISIFI33. Proto musí všechny výkazy vycházet z jednoho schváleného ocenění k datu.
- **Náváznost období:** počáteční stav počtu a objemu akcií = konečný stav minulého období. Snímek odeslaného výkazu se tedy musí uložit a oprava se řeší novým vydáním, ne přepisem.
- **Portfolio proti rozvaze:** součet RH cenných papírů v RISIFI33 = řádek v RISIFI30; měnová expozice v DOFOS31 = aktiva celkem bez derivátů v ROFOS10; zisk v ROFOS10 = VYFOS20.
- **Limity:** DOFOS31 kontroluje limity podle NV 243/2013 (5, 10, 20, 25, 30, 35 % majetku, min. 85 % u feeder fondů), u nemovitostních fondů 40 % na jednu nemovitostní společnost a 55 % na úvěry. Kontroly limitů v `investra_limits` mohou použít stejnou klasifikaci nástrojů.
- **Hodnoty k potvrzení:** záporné hodnoty v rozvaze, vysoké změny z přecenění (TISIFI10 proti RISIFI30), kryptoaktiva nad 10 % FK. V Odoo pole pro komentář, který se přenese do vydání.

**Kontroly nad rámec SDAT, před generováním výkazů:**

- aktiva v RISIFI30 proti aktivům v ROFOS35 a součet aktiv podle tříd aktiv v ROFOS35,
- NAV ve výkazech proti schválenému ocenění, výsledek před zdaněním ve VYFOS20 proti hlavní knize,
- u FKI shoda trhů a nástrojů mezi ROFOS33 a ROFOS35,
- změna reálné hodnoty derivátů v RISIFI30 proti TISIFI10,
- nástroj nebo protistrana bez trhu, podskupiny aktiv, sektoru, CFI nebo LEI,
- účet se zůstatkem, který žádné pravidlo výkazu nepokrývá.

**Co z metodiky plyne pro implementaci:** kódy položek (např. EAR2285 Aktiva celkem), číselníky (země, sektory ESA, druhy cenných papírů, měny) a převodníky jsou veřejně v části Knihovna. Mapovací tabulky v Odoo použijí přímo tyto kódy a číselníky, aby export do SDAT nepotřeboval další překlad. Metodika má verze s platností (aktuálně FOFI20261201), takže mapování se bude verzovat stejně. Katalog výkazů, položek, 705 kontrol a použitých číselníků je v repozitáři v `docs/cnb/`: CSV je zdroj, XLSX slouží ke čtení.

### Z účetnictví do výkazů

Každá buňka výkazu je pravidlo v `investra_cnb`. Pravidla mají platnost od data a vazbu na verzi metodiky, protože se mapování v čase mění často. Změna pravidla se eviduje a starý výkaz jde vždy vygenerovat podle pravidel svého období.

| Typ pravidla | Použití |
| --- | --- |
| Účet nebo skupina účtů podle role | Běžné řádky rozvahy a výsledovky |
| Jen kladný, nebo jen záporný zůstatek | Položky, které podle znaménka patří do aktiv nebo pasiv; test po nástroji nebo protistraně, ne po celém účtu |
| Výnos minus náklad | Čistý výsledek podle druhu nástroje |
| Součet jiných řádků | Souhrnné řádky |
| Údaj z portfolia | Reálná hodnota účastí a cenných papírů |
| Filtr podle atributu nástroje | Úroveň RH, kategorie IFRS 9, druh nástroje |
| Údaj mimo účetnictví | Viz tabulka zdrojů níže |

Cíl je, aby se výkaz nemusel po vygenerování ručně upravovat ani dorovnávat na bilanci nebo na 100 %. Ruční zásah je výjimka se zdůvodněním a zůstane ve vydání výkazu.

**Deriváty:** kladná a záporná reálná hodnota se vedou po smlouvách a brutto, aby výkazy seděly na rozvahu a výroční zprávu. Řádek výkazu plyne z účetního režimu: bez zajišťovacího účetnictví jde o deriváty k obchodování, i když ekonomicky zajišťují. TISIFI10 se počítá po smlouvách od posledního přecenění minulého měsíce do posledního přecenění v aktuálním měsíci: kladná část je změna MAX(RH; 0), záporná změna MIN(RH; 0) s opačným znaménkem. Vypořádání se od přecenění odděluje, proto musí mít pohyb nástroje typ.

**Sjednáno, nevypořádáno:** nástroj potřebuje tento stav, protože různé výkazy ho berou jinak. ROFOS10 vychází z účetnictví, tedy z data sjednání, pokud ho zvolí účetní politika. RISIFI33 potřebuje počet a další údaje, takže se investice do vypořádání vykáže v RISIFI30 v Ostatních aktivech a pak se přesune. Týká se to hlavně private equity a dlouhých upisovacích období. Mezi ROFOS10 a RISIFI30 ani RISIFI33 katalog mezivýkazovou kontrolu nemá. Před prvním použitím ověřit s ČNB.

**Účasti bez ISIN:** patří do samostatné oblasti RIS33\_13, měna a počet vycházejí ze základního kapitálu společnosti.

**Přepočet a zaokrouhlení:** částky pro výkazy se berou z hodnoty ve funkční měně nebo se přepočítají po řádcích, nikdy se nepřebírají z měny třídy. Objemy vydaných a odkoupených cenných papírů v ROFOS11 a ROFOS13 se přepočítají kurzem ČNB k rozhodnému dni transakce, u odkupu ke dni přijetí žádosti, a konečný stav je počáteční stav plus emise minus odkupy. IS proto musí předat datum žádosti. U fondu s funkční měnou EUR se výkazy v tisících Kč zaokrouhlují po řádcích, takže předem určíme pravidlo pro součty.

**Období výkazu:** datem je poslední ocenění v měsíci, ne vždy kalendářní konec. U fondů s delším intervalem ocenění platí pro pohyby období od prvního dne po posledním ocenění minulého měsíce.

**Vlastnosti s platností v čase:** sektor a země protistrany se mohou opravovat zpětně za více období, a výkaz se pak opraví novým vydáním. Zařazení podle ZISIF (např. § 46 a § 47) závisí na typu fondu držitele, takže patří na vazbu fondu a nástroje, ne jen na emisi. Emitentem podílového listu nebo akcie je pro výkazy fond nebo podfond. Změna ISIN má účinné datum a historii; je to technická změna bez dopadu na NAV. Výpadek ceny po změně musí vyvolat upozornění.

**Zdroje údajů mimo účetnictví:**

| Údaj | Výkaz | Zdroj |
| --- | --- | --- |
| Struktura a počty investorů po typech a zemích | ROFOS11, ROFOS13, ROFOS35 | IS |
| Datum žádosti o odkup, počty kusů | ROFOS11, ROFOS13, RISIFI37 | IS |
| Expozice, VaR, likvidita, stresové testy | DOFOS31, ROFOS35 | Řízení rizik |
| DV01 a další rizikové charakteristiky dluhopisů | ROFOS35 | Tržní data |
| Hrubá a čistá výkonnost po měsících | ROFOS35 | Ocenění |
| Trh, podskupina aktiv, CFI, LEI, sektor | RISIFI33, DOFOS31, ROFOS33, ROFOS35 | Číselník nástrojů a protistran |
| Nemovitosti, vlastní kapitál SPV | DOFOS40 | Podklad správce nebo SPV |
| Strategie fondu, textové části | ROFOS35, KLISIFI10 | Registr fondů |

**Hlášení obhospodařovatele:** ROFOS33 za obhospodařovatele agreguje fondy, takže potřebuje dotaz napříč společnostmi a jasný seznam, které fondy se započítávají. SICAV a FKI se vykazují také samostatně.

**Odeslání:** Odoo vytvoří soubor ve formátu pro import do SDAT (šablona Export pro import, desetinná tečka, u některých oblastí povinné nuly). Podpis zaručeným certifikátem s roční obnovou a odeslání zůstávají na pověřené osobě. Odoo uloží snímek, vydání a protokol o zpracování.

**Transakční výkazy a oznámení (mimo katalog):** `docs/cnb` obsahuje jen rámec Fondy. Hlášení obchodů (PERFIM30, REFFIM10, TRAFIM30, TRAFIM20, TRAFIM11) patří do jiného rámce: mají vlastní pořadí, lhůtu následujícího pracovního dne, časy v UTC, referenční údaje FIRDS, CFI, LEI a UTI a opravy přes storno. Oznámení o porušení limitu je samostatný výkaz. Zda se Investry týkají a zda je bude vytvářet Odoo, je otevřený bod.

### Kapitál obhospodařovatele (návrh)

Investiční společnost vykazuje kapitál a jeho požadavky v DOFOS60. Výkaz má tři části: strukturu kapitálu, kapitálové požadavky a aktiva podle likvidnosti. Výpočet bude v `investra_cnb` a poběží z dat Odoo, ne z tabulky mimo systém. Stejný výpočet poslouží i průběžnému sledování přebytku kapitálu.

| Část DOFOS60 | Co se počítá | Zdroj v Odoo |
| --- | --- | --- |
| Struktura kapitálu | Splacený základní kapitál, fondy, nerozdělený výsledek, použitelný výsledek běžného období, odpočet nehmotného majetku | Hlavní kniha společnosti, stav auditu nebo schválení výsledku |
| Počáteční kapitál a požadavek k fixním režijním nákladům | Minimální částka v EUR a čtvrtina fixních režijních nákladů (§ 29 a § 30 ZISIF) | Účty s příznakem fixních režijních nákladů, základ za předchozí rok, v prvním roce plán |
| Dodatečné požadavky | Z hodnoty majetku nad práh a k pokrytí odpovědnosti za škodu (§ 31 ZISIF) | AUM ze schválených ocenění všech fondů |
| Aktiva podle likvidnosti | Peněžní prostředky, cenné papíry a další likvidní hodnoty (§ 32 ZISIF) | Hlavní kniha společnosti, role účtů |

**Co musí Odoo umět:**

- u nákladových účtů příznak, zda patří do fixních režijních nákladů, s platností od data,
- rozlišit použitelný a nepoužitelný zisk běžného období, protože zisk se do kapitálu počítá jen za splnění podmínek,
- sečíst AUM ze schválených ocenění napříč společnostmi k jednomu datu a ukázat rezervu proti prahu pro dodatečný požadavek,
- přepočítat minimální částku v EUR kurzem podle metodiky, ne pevnou hodnotou v Kč,
- upozornit, když přebytek kapitálu nebo likvidita klesne pod vnitřní práh.

**Kontroly před odesláním:** aktiva v DOFOS60 proti ROFOS10 a zisk v DOFOS60 proti ROFOS10 (mezivýkazové kontroly), součty struktury kapitálu a požadavků, kapitál proti nejvyššímu požadavku.

Odkazy na ZISIF je před implementací potřeba ověřit proti aktuálnímu znění. Zařazení příplatku mimo základní kapitál do CET1 potvrdit s auditorem nebo ČNB.

## Audit, bezpečnost a provoz

Každý výpočet NAV a FX musí jít zopakovat ze stejných vstupů. Provoz dvou systémů zároveň zvyšuje nároky na zálohy, monitoring a evidenci ICT služeb.

- **Reprodukovatelnost:** ke každému výpočtu se ukládají vstupy, kurzy, ceny, parametry, verze pravidel a výsledné zápisy.
- **Neměnnost:** provedené transakce, závěrky a zaúčtovaná ocenění se nepřepisují. Oprava je storno a nový záznam.
- **Schvalování:** parametrizovatelné pro ocenění, ceny a ruční úpravy kurzu. Lze nastavit kontrolu čtyř očí, kdy schvaluje jiná osoba než zadavatel, nebo schvalování nepoužívat. Pro fondy Investry je kontrola druhou osobou povinná podle vnitřních předpisů. Stanovisko depozitáře je samostatný krok po zaúčtování, schválení obhospodařovatele a administrátora se řídí parametrem fondu.
- **Osobní údaje:** zůstávají v IS. Do Odoo jdou jen identifikátory a agregace.
- **Oddělení zakladatelů:** vychází z rozhodnutí o jedné databázi; přístup se omezí právy podle společnosti a zakladatele.
- **Kritická logika:** NAV a alokace patří do verzovaného kódu s testy, ne do Studia ani ručních vzorců.
- **DORA:** Enterprise ani Odoo.sh samy neznačí soulad. Odpovědnost za ICT rizika, smlouvy, incidenty, kontinuitu a exit zůstává na Investře.
- **Produkce:** oddělené produkční, testovací a vývojové prostředí; šifrování dat v klidu i při přenosu; role a oddělení povinností; MFA pro privilegované účty; přístup z řízených zařízení a přes VPN s vícefaktorovým ověřením; denní šifrované zálohy mimo primární lokalitu; pravidelné testy obnovy; monitoring; správa aktualizací. Současné lokální prostředí je jen prototyp.
- **Uchování a archivace:** matice uchování podle druhu záznamu. Obecně 5 let, účetní závěrka a výroční zpráva 10 let, daňové doklady podle daňových předpisů (zákon o účetnictví § 31, znění ověřit), lhůty ZISIF ověřit. Export archivu musí být čitelný bez Odoo.
- **Aktualizace Odoo:** vlastní addony je potřeba při každé nové verzi migrovat a otestovat, což je trvalý náklad.

**DORA (vnitřní dokumenty Investry):** Odoo bude nový ICT systém, takže se na něj vztahují jejich požadavky na schválení projektu, evidenci aktiv a dodavatelů, bezpečný vývoj, řízení přístupů, zálohy, obnovu a testovací data. Konkrétní hodnoty (lhůty, frekvence) zůstávají v dokumentech DORA a převezmou se při návrhu produkčního provozu.

Lokální Docker je jen pro vývoj. Ostrá data vyžadují produkční hosting. Zda se požadavky DORA vztahují i na Investra Services, je potřeba ověřit.

## Nasazení a převzetí fondů

Nasazení začne ostrým účetnictvím společností, fondy přijdou až po ověření provozu. Ostrý start vyžaduje produkční hosting a volbu edice Odoo, protože výkazy, DPH a bankovní párování jsou potřeba od prvního dne.

| Fáze | Jednotka | Rámec | Cíl |
| --- | --- | --- | --- |
| 1 | Investra Services s.r.o. | CAS pro podnikatele, CZK | Ostrý provoz s malým rizikem, ověření osnovy, banky, DPH, výkazů, záloh a práv |
| 2 | Investiční společnost, po vzniku | CAS pro finanční instituce, IFRS pro nástroje | Provoz plně podle DORA |
| 3 | Fondové moduly a pilotní fond | CAS pro finanční instituce nebo IFRS | Ověření celého cyklu včetně NAV |

### Převzetí knih existujících fondů

Fondy přecházejí ke dni uzávěrky nebo ocenění, ne migrací celé historie.

1. **Společný vstupní formát:** osnova, předvaha, otevřené položky, pozice, třídy, kusy a kurzy, včetně atributů pro výkazy (sektor a země protistran, kategorie IFRS 9, splatnosti). Pro každý zdrojový systém vznikne jen převodník.
2. **Mapování:** účty fondu se přiřadí k rolím, osnova fondu může zůstat.
3. **Počáteční stavy:** zůstatky účtů, otevřené pohledávky a závazky, kapitál podle tříd.
4. **Pozice po nástrojích:** pořizovací cena v měně, pořizovací kurz, kurzový rozdíl a přecenění.
5. **Údaje pro výpočty:** historie NAV, high-water mark a hurdle.
6. **Kontroly:** předvaha souhlasí, otevřené položky odpovídají účtům, pozice hlavní knize, kusy v IS a FK se zreprodukuje.
7. **Paralelní běh:** jedno až dvě ocenění v obou systémech, potom přepnutí se schválením.
8. **Historie:** zůstane jako archiv ze starého systému. Při přechodu v průběhu roku se doplní obraty po měsících.

## Plán prací

Začínáme ověřovacím prototypem NAV, potom přijdou na řadu role účtů a specifikace rozhraní, protože na nich stojí vše ostatní a vyvíjejí se podle nich oba systémy. Etapy popisují vývoj fondových modulů a mohou běžet souběžně s fázemi 1 a 2. Termíny doplníme, až bude jasný harmonogram úprav IS.

1. **Prototyp NAV (ověřovací etapa):** jeden fond, dvě třídy, CZK a EUR, celý cyklus včetně zámku návrhů, zaúčtování a storna od depozitáře.
2. **Specifikace:** rozhodnutí z otevřených bodů, seznam rolí účtů, účetní politika pro FX.
3. **Dvě zkušební knihy:** CZK a EUR, vlastní osnova, kurzy ČNB a ECB. Ověří návrh „kniha = společnost“.
4. **Specifikace rozhraní s IS:** podle aktuálního zadání, aby mohl začít vývoj IS.
5. **Účtování a FX:** `investra_posting` a FX skupiny, vyzkoušené na simulovaných událostech.
6. **Fondy a portfolio:** fond, třídy, instrumenty, ceny, pozice. Prototyp pole třídy na účetním řádku a vnitřního zúčtování.
7. **Napojení na IS:** závěrky, kurzy, párování plateb, denní kontroly.
8. **Alokace a ocenění:** plná verze po ověření prototypu.
9. **Výkazy:** snímky dat a první výkaz ČNB.

**Etapa Investra Services (fáze 1) navíc zahrnuje:** šablonu společnosti, neměnnost, oddělení rolí a čtyři oči i pro nastavení, zálohy a test obnovy.

Rozhodnutí Community, nebo Enterprise musí padnout před ostrým startem Investra Services.

Protože začínáme přímo na Odoo, musí od začátku pokrýt i oběh dokladů a finanční výkazy. Jejich rozsah závisí na volbě edice.

## Ověření na příkladech fondů

Návrh jsem porovnal se čtyřmi příklady fondů kvalifikovaných investorů, které účtují podle vyhlášky 501/2002 a IFRS. Žádný z nich zatím nevytvořil podfondy.

| Fond | Interval | Vydané třídy | Třídy ve statutu | Hlavní aktiva |
| --- | --- | --- | --- | --- |
| Fond A | měsíčně | jedna | jedna | ETF, akcie, měnové zajištění, opce |
| Fond B | čtvrtletně | jedna | několik | hmotná aktiva přes majetkovou účast |
| Fond C | — | — | několik v CZK i EUR | nemovitosti přes SPV |
| Fond D | — | — | několik | neuvedeno |

Co z toho pro návrh plyne:

- **Třídy v různých měnách jsou reálný požadavek.** Jeden fond může mít třídy v CZK i EUR. Model třídy musí mít vlastní měnu. Měna třídy je měna, ve které se vydávají a odkupují akcie a vyhlašuje kurz; funkční měnu fondu podle IAS 21 neurčuje. Fond s třídou v EUR může mít dál funkční měnu CZK: účetnictví a FK se vedou v CZK a kapitál třídy se do EUR přepočítává kurzem k datu ocenění.
- **Statut počítá s více třídami, i když je zatím vydaná jedna.** Model musí zvládnout víc tříd od začátku.
- **Aktiva bývají držená přes SPV.** Hmotná aktiva i nemovitosti jsou často majetková účast ve společnosti, ne přímý nástroj. Pořizovací cena má složky jako příplatek mimo základní kapitál a úvěr SPV. Ocenění je přes DCF nebo posudek.
- **Interval ocenění se liší** (měsíčně i čtvrtletně), což potvrzuje parametr fondu.
- **Alokace mezi třídami je ve statutu**, ne ve stanovách. Pro konkrétní vzorec budeme potřebovat statut daného fondu.

Analýza nestačí pro migraci, k té jsou potřeba statuty a data po pozicích.

**Performance fee potvrzuje náš model alokace.** Část zhodnocení portfolia se může alokovat na jiný druh akcií fondu. Je to přesně přesun hodnoty mezi třídami přes vnitřní zúčtování, který máme v návrhu. Potvrzuje také, že performance fee mění kapitál tříd, ne jen celkové NAV.

Vstupní a výstupní poplatky řeší IS, správu a performance fee účtuje Odoo.

### Požadavky ze stanov

- **Víc druhů investičních akcií**, ke společnosti nebo ke každému podfondu. Model musí zvládnout víc tříd a budoucí podfondy.
- **Zakladatelská třída.** Jejím vlastníkem může být jen držitel zakladatelských akcií. Může být příjemcem performance alokace. Performance třída bude v modelu parametr.
- **Oceňování:** reálná hodnota, nemovitosti a majetkové účasti pravidelně znalcem, mimořádné ocenění. Hodnota akcie = fondový kapitál / poměr podle statutu pro daný druh, bez účetní závěrky. Zaokrouhlení a lhůta vyhlášení jsou parametry fondu.
- **Úplata:** pevná částka, nebo procento z průměrného fondového kapitálu, nebo procento z výsledku hospodaření (performance). Výpočet úplat musí umět všechny tři varianty.
- **Podíl na zisku:** lze rozdělit do fondů, na jiné účely, členu správní rady nebo držitelům zakladatelských akcií; vyplácí se bankovním převodem. Potvrzuje dividendy i výplatu do zakladatelské části.
- **Investiční akcie mohou být bez hlasovacího práva**, s výjimkami ve vymezených případech.

**Z klíčových informací (KID):**

- **Růstová třída:** dividendy se nevyplácejí, reinvestují se. Potvrzuje, že třída může být růstová i dividendová, parametr třídy.
- **Performance fee s hurdle.** Poplatek se účtuje až při překročení stanoveného výnosu. Model performance fee musí mít hurdle jako parametr.
- **Výstupní poplatek může záviset na době držení**, řeší ho IS.

Poplatky i hurdle jsou parametry třídy, ne globální nastavení. Přesný alokační poměr mezi třídami určuje statut.

**Z výroční zprávy:**

- **Majetková účast může být ve FVOCI, ne ve FVTPL.** Přecenění účasti pak jde do oceňovacích rozdílů ve vlastním kapitálu, ne do výsledku. Při prodeji se nepřeúčtovává do výsledku, převádí se v rámci kapitálu do nerozděleného zisku. Kurzové rozdíly těchto nástrojů jdou také do kapitálu. Jiný fond může mít naopak vše ve FVTPL, takže **klasifikace podle IFRS 9 je vlastnost každého nástroje** a určuje protiúčty.
- **Rozvahový výpočet NAV je tím potvrzený.** Fondový kapitál zahrnuje i oceňovací rozdíly ve FVOCI, které výsledkovkou neprojdou. Výpočet přes výnosy a náklady by je minul.
- **Portfolio fondu může tvořit jen účast a úvěr do SPV.** Aktiva drží dceřiná společnost a účast se oceňuje substanční metodou z reálné hodnoty aktiv. Úroky z úvěru ve FVTPL se vykazují spolu s přeceněním ve „Zisku z finančních operací“.
- **Neinvestiční část má vlastní bankovní účet a výsledek.** Část se proto musí dát určit i výchozím nastavením bankovního účtu nebo deníku.
- **Výkazy:** rozvaha a výsledovka po částech a za celek, přehled změn vlastního kapitálu (neinvestiční část) a čistých aktiv (investiční část), podrozvaha „hodnoty předané k obhospodařování“ ve výši celkových aktiv, závazky vůči investorům z odkupů a dohadné položky (audit, posudek, FATCA/CRS, administrace, daň).
- **Zpráva o vztazích** potřebuje evidenci ovládajících a spřízněných osob (IAS 24), včetně sesterských fondů a SPV.

**Obecné požadavky na model:**

- Úplaty mohou kombinovat pevnou částku s pásmy podle velikosti majetku a procento z FK; základem může být FK před výkonnostní odměnou. Pořadí výpočtů (úplaty, výkonnostní poplatek, daň) je parametr fondu.
- Výkonnostní poplatek může být částí úplaty obhospodařovatele, ne alokací na jinou třídu. Model musí umět hurdle, variantu s high-water mark i bez ní, poměrné zohlednění pohybů v období a dohad při každém ocenění.
- Náklady může nést jen investiční část; výsledek a rozdělení zisku se schvaluje po částech.
- Hodnota akcie může platit zpětně pro celé období a datum ceny nástrojů se může lišit ode dne ocenění. Obojí je parametr fondu.
- Počet akcií se může zaokrouhlovat dolů se zbytkem ve prospěch fondu; přirážky a srážky mohou být příjmem obhospodařovatele, ne fondu.
- Odkupy mohou mít dlouhou lhůtu vypořádání a je možný úpis nepeněžitým vkladem oceněným znalcem.
- Investiční limity statutu (koncentrace, likvidita, páka, test základního investičního fondu) jsou vstupem pro `investra_limits`.
- Změna parametrů třídy musí mít platnost od data a vazbu na verzi statutu; KID a statut se mohou rozcházet.
- Zakladatelské akcie mohou být listinné bez ISIN a fondy běžně mění správce, takže převzetí knih je běžné.

**Statut není veřejný.** U fondů kvalifikovaných investorů je jen na kontaktním místě správce. Alokační vzorec konkrétního fondu tedy získáme jen ze statutu daného fondu, ne z veřejných zdrojů.

## Otevřené body a rizika

Největší otevřené otázky jsou možnosti IS, volba edice Odoo a pole výkazů ČNB. Bez nich nejde dokončit rozhraní ani datový model.

### Rozhodnutí

| Bod | Proč na tom záleží | Doporučení |
| --- | --- | --- |
| Community, nebo Enterprise | Chybí finanční výkazy, bankovní párování a oběh dokladů | Rozhodnout nejpozději po etapě zkušebních knih, před ostrým startem Investra Services. Kritéria: finanční výkazy, bankovní párování, oběh dokladů, cena licencí a hostingu, kompatibilita vlastních modulů. |
| Podrobnosti dividend | Účet pro výplatu, dopad na kurz k rozhodnému dni | Upřesnit |
| Zdroje cen | Jaká aktiva fondy drží, frekvence posudků | Upřesnit |
| Možnosti IS | Zda umí závěrku, identifikátory, příjem číselníku a kurzu, dividendy a API | Získat dokumentaci |
| Aktualizace předpisů | Funkční měna EUR, schvalování, střediska SICAV v předpisu 12; nyní se nemění | Projít později |
| Start Investra Services | Současné účetnictví, termín přechodu, plátcovství DPH, mzdy, hosting | Upřesnit |
| Zdrojové systémy fondů | Které systémy a zda mají údaje po pozicích a pořizovací kurzy | Upřesnit u prvních fondů |
| Podrozvaha v Odoo | Podpora ve standardním Odoo není ověřená, deriváty a opce jsou u fondů významné | Ověřit v prototypu |
| Okamžik zaúčtování obchodu | Datum sjednání, nebo vypořádání | Určit v účetní politice |
| Evidence aktiv uvnitř SPV | Zda Odoo má vést i aktiva dceřiných společností (např. jednotlivé automobily) pro ocenění, limity a výkazy, nebo jen účast a úvěr | Upřesnit |
| Pole výkazů ČNB | Katalog výkazů, položek, kontrol a číselníků je v docs/cnb/ (metodika FOFI20261201) | Doplnit ukazatele u položek bez kontroly a převodníky z Knihovny SDAT; ověřit termíny RISIFI37 a ROFOS13 |
| Hosting | Určuje provoz, zálohy, obnovu a dodavatelskou smlouvu | Rozhodnout před ostrým startem; posoudit proti závazkům v žádosti o povolení a DORA |
| Soulad s žádostí o povolení | Technický popis v žádosti se musí shodovat se skutečným provozem účetnictví a IT | Porovnat žádost s architekturou a s právníkem nebo compliance určit, zda a jak změnu oznámit ČNB |
| Termín startu a převzetí fondů | Vývoj fondových modulů musí stihnout první fondy, jinak je potřeba přechodné řešení | Určit termíny, připravit záložní postup |
| Dopad DORA | Rozsah pro investiční společnost, role Investra Services a dodavatelů, včetně AI | Určit rozsah a doplnit evidenci dodavatelů |
| Hesla a MFA | Délka hesla závisí na vícefaktorovém ověření; vynutit MFA | Řešit při návrhu produkce; požadavek ověřit v aktuálním NIST SP 800-63B |
| Lhůty uchování podle ZISIF | Zvláštní lhůty pro obhospodařovatele a administrátora nejsou ověřené | Ověřit v aktuálním znění a doplnit do matice uchování |
| Automatické testy (CI) | Testy modulů se zatím spouštějí ručně | Po prvním funkčním modulu nastavit automatickou instalaci modulu a testy |
| Transakční výkazy a oznámení | Katalog pokrývá jen rámec Fondy; hlášení obchodů mají krátkou lhůtu a vlastní data | Ověřit povinnost Investry, pak rozhodnout o rozsahu a doplnit katalog |
| TISIFI10 u nových smluv | Zda je bez vypořádání přeceněním celá změna RH, nebo se vychází z první známé RH; mění výsledek v měsíci sjednání | Počítat celou změnu; potvrdit s ČNB před implementací |
| Výkazy speciálních fondů | Speciální fondy mohou podávat jiné výkazy než FKI, například ROFOS11 a DOFOS70 | Ověřit v plánu výskytů SDAT a doplnit tabulku výkazů |
| Příplatek mimo základní kapitál | Zda se počítá do CET1 a na který řádek DOFOS60 patří; ovlivňuje vykázaný kapitál | Potvrdit s auditorem nebo ČNB |

### Chybějící podklady

- [ ] Dokumentace a API IS.
- [ ] Kdo a kdy zajistí úpravy IS.
- [ ] Oceňovací dokumentace, včetně „Výpočtu bonusů pro fondy s delší periodou“.
- [ ] Zbývající ukazatele u položek a převodníky ČNB z Knihovny SDAT (ostatní je v docs/cnb/).
- [ ] Ukázky nastavení tříd a alokací od zakladatelů.
- [ ] Účetní politika přecenění: účty, kurz, frekvence, protiúčty, metoda, P&L a OCI.
- [ ] Naběhlý úrok a klasifikace podle IFRS 9.

### Rizika

| Riziko | Dopad | Opatření |
| --- | --- | --- |
| Vzorce pokrývají jen zjednodušenou variantu | Nepočítá s převodem hodnoty mezi třídami; třídy v jiné měně už jsou potvrzené (fond může mít třídy v CZK i EUR) | Ověřit na ukázkách od zakladatelů |
| Vstup nových investorů za starší kurz | Možné zvýhodnění nebo poškození stávajících investorů | Nastavení podle statutu, přehled ručních úprav |
| Fondové moduly vyvíjené svépomocí | Trvalá práce na migracích a testech při nových verzích Odoo | Testy, omezit zásahy do core na minimum |
| Odoo jako NAV systém | Může se ukázat méně vhodné než specializovaný systém | Ověřit prototypem před produkcí |
| Velký počet společností | Pomalejší práce v UI, složitější souhrnné přehledy | Vlastní přehledy, ověřit v etapě zkušebních knih |
| Celé účetnictví v Odoo od začátku | Větší rozsah: oběh dokladů, výkazy, úprava předpisů a evidence pro DORA | Postup po fázích, start na Investra Services |
| Chybějící údaje při převzetí fondu | Bez pořizovacího kurzu nebo údajů po pozicích nejde oddělit FX a FV | Účetní postup pro stanovení hodnot ke dni přechodu |
