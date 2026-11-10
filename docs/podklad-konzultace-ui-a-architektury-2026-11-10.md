# Podklad pro konzultaci rozvržení obrazovek a architektury

**Stav podkladu:** 9. 11. 2026

**Projekt:** Investra – účetnictví, portfolio a NAV na Odoo

**Pracovní větev při přípravě:** `feature/nav-prototyp`

Tento dokument je samostatný kontext pro AI, které nemá přístup k repozitáři ani dosavadní konverzaci. Shrnuje cíle, skutečný stav prototypu, hlavní architektonická rozhodnutí a otázky k UX. Neobsahuje důvěrné podklady, přihlašovací údaje ani skutečná data investorů.

## Zadání pro AI, které tento dokument dostane

Jsi nezávislý produktový a technický konzultant. Uživatel je finančník a účetní metodik, Odoo se učí; komunikuj česky a stručně, ale složité vazby v Odoo vysvětli.

Pomoz posoudit **informační architekturu a rozvržení obrazovek** pro níže popsaný projekt. Uvažuj nad každodenní prací rolí (účetní, oceňovatel, kontrolor, schvalovatel, správce), nad přehledem napříč mnoha fondy a společnostmi, nad pracovním postupem ocenění, výjimkami a dohledatelností od NAV k účetnímu zápisu.

- Jasně odděluj hotové funkce, současné obrazovky, návrhy a vlastní doporučení.
- Nevymýšlej současné schopnosti Odoo ani existující obrazovky. Současný prototyp používá převážně standardní seznamy, formuláře, záložky a stavové akce; uživatel je ještě vizuálně neověřil.
- Nenavrhuj druhý výpočet NAV ani paralelní fondový účetní systém. Výpočet NAV má zůstat v `investra_nav`; obrazovka je jeho pracovní rozhraní.
- Nepředpokládej účetní pravidla, fondovou metodiku, role ani oprávnění, které zde nejsou výslovně popsány. Nejasnosti označ jako otázky k metodikovi.
- Navrhni nejprve principy a varianty, výhody/nevýhody a doporučení. Zatím nic neimplementuj ani neměň.
- Pokud navrhuješ vlastní UI nad Odoo, vysvětli, co má zůstat v Odoo ORM a standardních účetních modelech a co by byla pouze prezentační/workflow vrstva.

## 1. Co je projekt

Investra připravuje platformu pro účetnictví skupiny a později pro administraci účetnictví fondů, portfolia, ocenění a NAV. Základním účetním a provozním systémem je Odoo 20 Community rozšířené vlastními moduly. Cílem je auditovatelný systém, který umí obsluhovat fondy různých zakladatelů a jejich odlišná statuta, účetní rámce a třídy.

Skupina zahrnuje Investra Services s.r.o., budoucí investiční společnost a v dalších etapách SICAV, fondy a podfondy přebírané od jiných administrátorů.

**Samostatný informační systém (IS)** je mimo Odoo. Vlastní evidenci držitelů podílů/investičních akcií, pokyny investorů, vydávání a rušení kusů a související vypořádání. Odoo je vlastníkem účetnictví, číselníku fondů a tříd, instrumentů, portfolia, cen, ocenění, NAV a výkazových dat. IS dostává potřebné číselníky a předává zejména finalizované závěrky klientských transakcí. Konkrétní technické rozhraní IS zatím není dodané ani implementované.

Odoo nebylo nahrazeno iÚčtem. Varianta iÚčto + nová vlastní fondová aplikace byla prozkoumána samostatně, ale rozhodnutí projektu k 9. 11. 2026 říká pokračovat v Odoo; k iÚčtu se vrátit jen při potvrzení vedením. Jde o průzkum, ne o změnu architektury.

## 2. Odoo vysvětlené pro člověka, který ho nezná

- **Odoo** je modulární podnikový systém. Jeho funkce se skládají z aplikací a addonů.
- **Addon/modul** je instalovatelná jednotka funkcí. Má závislosti, Python modely (datový model a obchodní logiku), XML pohledy/menu a oprávnění. Vlastní moduly projektu jsou v `addons/custom/`; Odoo core ani zdrojový kód třetích stran se neupravují.
- **ORM** je aplikační vrstva Odoo pro práci s databázovými záznamy. Vlastní moduly mají vytvářet a měnit záznamy přes ORM, nikoli přímým SQL zápisem do PostgreSQL.
- **Model** je typ záznamu, například fond, nástroj, ocenění nebo účetní doklad. Záznamy standardního účetnictví jsou hlavně `account.move` (doklad) a `account.move.line` (řádky MD/D).
- **View/pohled** určuje, jak se model zobrazuje a upravuje: typicky seznam (`list`), formulář (`form`), vyhledávání, kanban nebo záložky. **Action/akce** otevře pohled. **Menu** akci zpřístupní uživateli. XML pohled tedy není samotná účetní logika.
- Standardní Odoo poskytuje účetní jádro; vlastní moduly doplňují významové entity, workflow a kontroly. Vlastní řešení se má držet standardních účetních záznamů, aby šly využít účetní deníky, hlavní kniha, standardní oprávnění a další účetní funkce.
- **Společnosti v Odoo jsou účetní jednotky a hranice účetních knih.** Uživatel může přepínat jednu nebo více společností. Oprávnění a pravidla přístupu určují, které knihy uvidí. U velkého počtu fondů může přepínání společností zhoršovat UX; dashboard a kontextové filtry jsou proto důležité.
- **Účetní událost** je doménový původ zápisu. Jediný modul `investra_posting` má z události vytvářet účetní doklad. Fondové moduly nemají účetnictví obcházet přímým zápisem.
- Formulář může zobrazovat stavový pruh a tlačítka. Stisknutí tlačítka může změnit stav workflow, vytvořit návrh dokladu nebo doklad zaúčtovat. Návrh není totéž co zaúčtovaný doklad; rozhraní to musí výrazně rozlišovat.

## 3. Základní účetní a organizační model

1. **Jedna účetní kniha = jedna samostatná společnost Odoo.** Každá kniha má vlastní účetní osnovu, účetní rámec, funkční měnu a zdroj kurzů. Rozhodnutí je přijato, ověření praktického provozu s více knihami zůstává důležité.
2. Účetní rámec se volí pro každou jednotku samostatně: české účetní předpisy pro podnikatele (vyhláška 500), finanční instituce (vyhláška 501 s příslušným IFRS režimem) nebo plné IFRS. Nesmí se předpokládat, že všechny jednotky mají stejný rámec.
3. SICAV je jedna účetní společnost; podfondy jsou samostatné účetní společnosti/knihy. Investiční a ostatní činnost SICAV se rozlišuje údajem na účetním řádku a vykazuje po částech i za celek.
4. Fond má jednu nebo více **tříd**. Třídy mají vlastní kapitál, počet kusů a zveřejňovaný kurz, případně měnu zveřejnění. Měna třídy neurčuje funkční měnu fondu. Fond může mít funkční měnu CZK a třídu s kurzem v EUR.
5. Každý účet může mít významovou **roli účtu** (např. kapitál třídy, investice, FX zisk/ztráta). Moduly mají používat role, ne natvrdo čísla účtů. To umožňuje různé účtové osnovy.
6. Účetní řádky mohou nést fondovou třídu a další strukturované atributy potřebné pro výkazy. Prázdná třída znamená společnou položku fondu. Analytické dimenze se nemají používat místo strukturovaných regulačních atributů.
7. Významová dimenze účetní jednotky, fondu, podfondu, třídy, nástroje, obchodu, ceny a ocenění musí být v obrazovkách srozumitelná; uživatel nemá omylem pracovat ve špatné společnosti nebo období.

## 4. Rozhraní systémů a pracovní tok

### IS ↔ Odoo

IS spravuje držitele, příkazy a jejich vypořádání. Odoo posílá nebo zpřístupňuje IS například číselník fondů/tříd, zveřejněné kurzy a potvrzení plateb; IS předává uzavřené závěrky. Jedno oceňovací období může mít více závěrek, které na sebe chronologicky navazují.

Odoo má zachovat dohledatelnost mezi závěrkou, účetním dokladem a oceněním. Závěrku použitou v ocenění nelze tiše změnit; oprava je řízený postup. Rozhraní a odpovědnosti obou systémů jsou zatím specifikace/otevřená práce, nikoli hotová integrace.

### Účetní událost → doklad → hlavní kniha

Událost v `investra_posting` vytváří účetní doklad v Odoo podle role účtů. Je chráněna jedinečným klíčem proti dvojímu vytvoření a otiskem obsahu. Doklad má standardní účetní řádky, s vlastními fondovými poli pro třídu a typ pohybu. Ocenění má vazbu na vytvořené události a doklady; uživatel má být schopen přejít z výsledku NAV až na původní řádek hlavní knihy a zpět.

Uživatel musí vždy vědět, zda vidí výpočet, návrh dokladu, schválený stav, nebo zaúčtovaný záznam. Zásah s účetním dopadem musí mít jasné potvrzení a auditní stopu. Oprava již zaúčtovaného záznamu se řeší stornem/opravou, nikoli tichou změnou.

### Ocenění a NAV

Zjednodušený plánovaný cyklus:

1. Ověřit, že závěrky klientských transakcí jsou kompletní, a vybrat fond a datum ocenění.
2. Sestavit počáteční kapitál tříd a alokační poměry.
3. Načíst pozice, ceny a kurzy a provést ocenění; chybějící cena zastaví výpočet, stará či odchýlená cena je upozornění/ke schválení.
4. Vypočítat dopady podle tříd: úplaty, případná výkonnostní odměna, daň a další položky podle parametrů a statutu fondu.
5. Provést kontroly a vytvořit návrhy účetních dokladů. Ocenění se schvaluje jako celek a zaúčtuje se jedním řízeným krokem, ne automaticky po každém dílčím výpočtu.
6. Evidovat schválení druhou osobou a případná stanoviska obhospodařovatele/depozitáře.
7. Vytvořit podklady pro depozitáře, zaznamenat jeho stanovisko, zveřejnit kurz a uzamknout ocenění podle příslušného stavu.
8. Umožnit řízené vrácení a novou verzi. Před zaúčtováním se opravují návrhy; po zaúčtování se stornují příslušné doklady a vytvoří nová verze.

Přesné parametry a pořadí výpočtů jsou nastavitelné podle fondu a statutu. Účetní metodika musí být potvrzena odpovědnými lidmi; AI ji nesmí domýšlet.

### Portfolio a instrumenty

Instrumenty jsou vlastněny Odoo. Obchody mají datum sjednání i vypořádání a fond volí způsob zachycení (trade-date nebo settlement-date). Pozice se odvozují z transakcí, nikoli ručním přepisem. Ceny mají historii, zdroj, autora/podklad a schvalování, aby šel výpočet zpětně reprodukovat.

Rozhodnutí z 9. 11. 2026 říká, že klasifikace IFRS 9, metoda ocenění a role účtu musí vycházet z obchodního modelu konkrétního fondu/pozice. Tentýž instrument může být v různých fondech nebo při různých nákupech klasifikován odlišně. **Současná implementace má tato nastavení ještě na instrumentu; jejich přesun na úroveň fondu/portfolia je známá mezera.**

## 5. Co je skutečně implementováno

Stav je vývojový prototyp na Odoo 20 Community, nikoli produkční systém. Testovací databáze `investra_test` má smyšlená data. Prototyp je v samostatné větvi; sloučení do `main` není samo o sobě potvrzením produkční připravenosti.

### Vlastní moduly

| Modul | Současná odpovědnost |
|---|---|
| `investra_entity` | Evidence účetních knih/jednotek, rámce, měny, vazby |
| `investra_chart_fund` | Pracovní osnova fondu a mapování rolí účtů |
| `investra_rates` | Kurzy ČNB/ECB, zdroj a historie, promítnutí do Odoo |
| `investra_fund` | Fondy, třídy, kalendář ocenění a pravidla kurzu |
| `investra_posting` | Účetní události, ochrana dokladů, třída na řádku, storno |
| `investra_instruments` | Typy/nástroje, ceny, obchody a pozice |
| `investra_allocation` | Verzovaná alokační schémata |
| `investra_dashboard` | Přehled fondů, výjimky a termíny ČNB |
| `investra_counterparty` | Protistrany/emitenti, platnost údajů, sektor ESA a LEI |
| `investra_cnb` | Katalogová/převodová data ČNB a kontrola nepokrytých rolí |
| `investra_fx_revaluation` | Profily cizoměnových účtů a návrhy přecenění |
| `investra_nav` | Ocenění, poplatky, výpočty tříd, schvalování a balíček pro depozitáře |
| `investra_vat_identified` | Daně identifikované osoby pro přijaté služby (samostatná účetní oblast) |
| `investra_env_banner` | Označení testovacího prostředí, aby se nepletlo s ostrým |

### Příklady hotových funkčních částí prototypu

- Fondy/třídy a NAV ve více třídách, včetně třídy s měnou zveřejněného kurzu odlišnou od funkční měny.
- Workflow ocenění: výpočet, kontroly, schválení druhou osobou, zaúčtování, depozitář, zveřejnění/uzamčení, verze a storno.
- Účetní události s vazbou na běžné Odoo doklady a s ochranou proti opakovanému zaúčtování.
- Ceny nástrojů se stavem/schválením; instrumenty a obchody; u části nástrojů výpočet naběhlé hodnoty a termínovaný vklad.
- Přecenění cizoměnových zůstatků dle profilu: výpočet připraví návrh dokladu, účetní jej zaúčtuje.
- Přehled fondů jako karty/kanban nebo seznam, s NAV, stavem, výjimkami a termíny.
- Exportní balíček pro depozitáře v Excelu; zaznamenané výpočty mimo Odoo lze k ocenění doplnit s odůvodněním/přílohou.
- Pracovní mapování účetních rolí na řádky vybraných výkazů ČNB.

Dokumentace k 9. 11. uvádí 252 testů ve 12 hlavních NAV/prototypových addonech a dalších 55 testů v samostatném referenčním výpočtu; vedle toho existují testy dalších modulů. Jde o počty popsané v dokumentaci, ne o tvrzení, že byly všechny testy v rámci přípravy tohoto podkladu právě spuštěny. Referenční výpočet není nezávislou kontrolou, protože jej vytvořil stejný autor.

### Současné rozvržení obrazovek podle kódu

- `Investra → Přehled fondů`: karty s výsledným stavem (v pořádku, upozornění, vyžaduje zásah, bez ocenění), FK, datem/stavem ocenění, kurzem, příštím termínem ocenění a ČNB, výjimkami a odkazem na ocenění.
- `Investra → Ocenění`: seznam a formulář ocenění. Formulář má stavový pruh a stavová tlačítka. Záložky: Třídy, Portfolio, Úplaty, Výpočty mimo Odoo, Kontroly, Schválení, Doklady. Je to hlavní existující pracovní obrazovka NAV.
- `Investra → Úpisy a odkupy`: evidence pohybů tříd; nejde o evidenci investorů.
- `Portfolio → Nástroje`, `Typy nástrojů`, `Ceny`, `Obchody`, `Splátky nástrojů`.
- `Investra → Účetní události`: původ účetního dokladu a vazba na standardní `account.move`.
- `Účetnictví → Konfigurace → Profily přecenění`: účty, ziskové/ztrátové protiúčty, deník a kurzová pravidla.
- `Účetnictví → Účetní zápisy → Přecenění cizích měn`: běh přecenění a návrh dokladu.
- `Investra → Nastavení`: účetní knihy, role účtů, mapování ČNB, kurzy, alokační schémata a pravidla úplat podle příslušného modulu.

Toto je popis XML pohledů/menu, ne uživatelsky ověřený popis chování na obrazovce. Standardní účetní deníky a hlavní kniha jsou součástí Odoo účetnictví; vlastní obrazovka fondu je zatím neagreguje do nové „hlavní knihy fondu“. Uživatel musí mít možnost přejít z NAV na standardní účetní doklady/řádky.

## 6. Co zatím není hotové nebo potvrzené

- Skutečné výkazy ČNB se nesestavují a neodesílají. Katalog v repozitáři a pracovní převodová tabulka nejsou hotovým podacím systémem.
- Rozhraní na IS není implementované; dokumentace a technické možnosti IS chybí.
- Úplné pokrytí portfoliových aktiv není hotové. Kupóny/dividendy dluhopisů, repo, úvěry, deriváty a ostatní podíly jsou chybějící nebo jen částečně podpořené. Termínovaný vklad je pokryt jen základní variantou.
- Bankovní automatizace, párování, uživatelská oprávnění podle fondů a produkční oběh dokladů potřebují další práci. Dostupnost bankovních funkcí závisí i na volbě Odoo Community/Enterprise.
- Klasifikace/metoda ocenění/role účtu se mají přesunout z instrumentu na fond/obchodní model.
- Výstupní obrazovky dosud uživatel vizuálně neověřil; bezpečnostní revize a testy na reálném objemu nejsou hotové.
- Hosting, produkční bezpečnost, zálohování/obnova, DORA, role dodavatelů, archivace, přístup do testovacího SDAT a nezávislá kontrola výpočtu vyžadují rozhodnutí a ověření.
- Harmonogram pro převzetí fondů ke konci Q1 2027 je podle statusu těsný a bez dostatečné rezervy; záložní plán je potřeba.
- Implementace zatím obsahuje konkrétní pracovní předpoklady. Účetní politika fondu a statut mají přednost; návrhy metodiky musí potvrdit účetní metodik, auditor či compliance podle otázky.

Hlavní otevřené body jsou vedeny v `docs/otevrene-body.md`; rozhodnutí v `docs/rozhodnuti.md`; souhrnný technický stav v `docs/prototyp-nav.md` a `docs/status-2026-11-09.md`. Architektura je export z Claude Doc a není sama o sobě důkazem, že je vše implementováno.

## 7. Prostředí a hranice bezpečného testování

| Instance | Účel | URL na vývojovém Macu | Databáze |
|---|---|---|---|
| Odoo 20 | Nová vývojová instance Investra | `http://127.0.0.1:8070` | `investra_dev` |
| Odoo 20 test | Prototyp NAV, smyšlená data | `http://localhost:8071` (pokud je testovací web spuštěný) | `investra_test` |
| Odoo 19 | Oddělená výuková instance s Odoo Mates | `http://localhost:8069` | `odoo_cz` |

URL `localhost` nebo `127.0.0.1` fungují jen na počítači, kde instance běží; na jiném počítači se na ně AI ani kolega nedostane. Testovací a vývojová databáze, Odoo 19 a Odoo 20 jsou oddělené. Neslučovat jejich data, verze, moduly ani volumes. Do testovacího NAV nepoužívat skutečná data investorů.

## 8. Doporučený rozsah UX konzultace

Zaměř se zejména na tyto návrhy:

1. **Navigace podle práce a rolí:** jak oddělit denní agendu (přehled, úkoly, výjimky) od konfigurace a technických číselníků; jak snížit počet kliknutí při desítkách knih.
2. **Přehled fondů:** řazení podle zásahu a termínu, filtr společnosti/fondu/stavu, srozumitelné výjimky, možnost otevřít konkrétní pracovní krok. Nepřehlcovat kartu množstvím účetních detailů.
3. **Pracovní prostor ocenění:** nahoře fond, datum, verze a stav; jasný průchod kroků a odpovědná osoba; souhrn FK a kapitálu tříd; zřetelně oddělené bloky Portfolio, Kontroly, Úplaty, Schválení a Doklady; přímé odkazy na zdrojová data a účetní zápisy.
4. **Schválení a výjimky:** co má vidět připravovatel, co nezávislý kontrolor a co schvalovatel; zakázat vlastní schválení tam, kde se vyžadují čtyři oči; dát přednost pracovní frontě před ručním hledáním záznamu.
5. **Konfigurace:** jak spravovat účetní rámce, role účtů, pravidla fondu a platnosti od data bez omylů; oddělit vzácná nastavení od běžné denní práce.
6. **Účetní drill-down:** z částky NAV přes třídu/portfolio a událost až na účetní doklad a řádek hlavní knihy; viditelné datum, měna, zdroj kurzu/ceny a stav zaúčtování.
7. **Více společností a oprávnění:** explicitní kontext aktuální knihy, možnost bezpečných přehledů napříč povolenými fondy, prevence práce ve špatné společnosti.
8. **Postupné zavádění:** začíná se účetnictvím Services, až poté investiční společností a fondy. Nenavrhovat všechna fondová workflow jako podmínku prvního účetního nasazení.

U každého návrhu uveď, zda jde o standardní schopnost Odoo, úpravu existujícího pohledu, nový vlastní addon, nebo změnu datového modelu. Preferuj malá zlepšení pohledů a pracovních toků před stavbou nového front-endu. Pokud navrhuješ novou aplikaci, popiš náklady, upgrade kompatibilitu, přístupová práva, auditní stopu a dopad na testování.

## 9. Výchozí otázky k diskusi

- Kdo jsou hlavní uživatelské role a co každý z nich dělá každý den, na konci období a při opravě?
- Má být výchozí obrazovkou dashboard s výjimkami, nebo pracovní fronta konkrétního kroku?
- Jaké informace musí uživatel vidět bez otevření ocenění a které mají být až v detailu?
- Jak vizuálně odlišit návrh, čekající schválení, zaúčtování, stanovisko depozitáře, zveřejnění a uzamčení?
- Má mít ocenění jednu dlouhou stránku se záložkami, nebo průvodce po krocích? Jak se udržuje kontext a přehled o celku?
- Jak zobrazit mnoho společností a fondů tak, aby uživatel poznal aktuální účetní knihu a nepřepnul omylem kontext?
- Které tabulky potřebují export, filtrování, seskupení, hromadnou akci a auditní historii?
- Jak umožnit rychlý drill-down do deníku a hlavní knihy, aniž by se účetní záznam duplikoval ve fondu?
- Jaké tři obrazovky mají být první, které si uživatel ověří v prototypu, a podle jakých úloh se budou testovat?

## Zdroje v repozitáři

- `README.md` – stručný popis a instance.
- `CLAUDE.md` – aktuální pravidla, hranice systémů, role agentů a bezpečnostní omezení.
- `docs/architektura.md` – rozsáhlý export návrhu systémové architektury; může obsahovat rozhodnutí i starší návrhy, stav vždy porovnat s kódem a deníkem.
- `docs/rozhodnuti.md` – potvrzená rozhodnutí a jejich stav.
- `docs/otevrene-body.md` – nevyřešená rozhodnutí a rizika.
- `docs/prototyp-nav.md` – moduly, testy, ověřený rozsah, mezery a spuštění prototypu.
- `docs/status-2026-11-09.md` – shrnutí stavu a ukázkový scénář.
- `addons/custom/` – implementace vlastních modulů.

**Upozornění k časové platnosti:** tento podklad je snímek stavu k 9. 11. 2026. Při další práci ověř novější změny; pracovní dokumentace ani tento handoff nenahrazují kontrolu aktuálního kódu, schválené účetní metodiky nebo právního posouzení.
