# Deník rozhodnutí

Každé rozhodnutí: datum, oblast, rozhodnutí, důvod nebo poznámka, stav.
Stav: **R** = rozhodnuto, **R+P** = rozhodnuto, ověřit prototypem, **N** = návrh, **Př** = předpoklad.
Podrobnosti a zdůvodnění jsou v Claude Doc „Investra – architektura Odoo a IS“ (tabulka Přijatá rozhodnutí).
Nové rozhodnutí přidat na konec a zároveň zapsat do Doc.

| Datum | Oblast | Rozhodnutí | Poznámka | Stav |
|---|---|---|---|---|
| 2026-11-04 | Rozsah | Účetnictví a.s., s.r.o., SICAV, fondů a podfondů v Odoo | | R |
| 2026-11-04 | Účetní rámec | CAS pro podnikatele, CAS pro finanční instituce nebo plné IFRS, pro každou jednotku zvlášť | | R |
| 2026-11-04 | Souběh CAS a IFRS | Není třeba, každá jednotka účtuje jen v jednom rámci; multi-ledger se nepoužívá | | R |
| 2026-11-04 | Funkční měna | CZK nebo jiná (např. EUR); kurzy ČNB i ECB | Předpisy se upraví později, nyní do nich nezasahovat. Měna třídy funkční měnu neurčuje: fond s třídou v EUR může mít funkční měnu CZK (upřesněno 2026-11-05) | R |
| 2026-11-04 | FX přecenění | Uživatelsky definované skupiny účtů | | R |
| 2026-11-04 | Třídy a alokace | Široce parametrizovatelné | Různí zakladatelé | R |
| 2026-11-04 | Interval ocenění | Uživatelsky definovaný pro fond, i mimořádná ocenění; kontrola proti statutu a zákonné lhůtě | | R |
| 2026-11-04 | IS | Samostatná aplikace IS: jen vypořádání nákupů a prodejů a evidence držitelů | | R |
| 2026-11-04 | Instrumenty a portfolio | Vlastníkem je Odoo | IS evidenci portfolia nemá | R |
| 2026-11-04 | Příchozí platby | Na účet třídy pro úpisy, banka je v Odoo | | R |
| 2026-11-04 | Výplaty odkupů | Platební příkazy vytváří IS | | R |
| 2026-11-04 | Bankovní účty | Třída má účet pro úpisy a pro odkupy, fond investiční účet; zvlášť pro každou měnu | | R |
| 2026-11-04 | Převody mezi účty | Spouští IS, Odoo je páruje na výpisech | | R |
| 2026-11-04 | Závěrka klientských transakcí | Vytváří IS; více závěrek v jednom oceňovacím období | | R |
| 2026-11-04 | Kurz úpisu v průběhu období | Poslední známý kurz, ruční úprava možná, řídí IS | Do Odoo přichází počet a cena | R |
| 2026-11-04 | Fondový modul | Univerzální, včetně výplaty dividend z tříd | | R |
| 2026-11-04 | Schvalování ocenění | Parametrizovatelné; u fondů Investry povinná druhá osoba; stanovisko obhospodařovatele a depozitáře se eviduje v Odoo | Ocenění schvaluje i administrátor podle parametru fondu | R |
| 2026-11-04 | Výpočet tříd | Pouze z rozvahy; přesuny mezi třídou a společným majetkem přes vnitřní zúčtování | | R+P |
| 2026-11-04 | Účetní systém | Odoo je jediný účetní systém od začátku, včetně oběhu dokladů | | R |
| 2026-11-04 | Databáze | Jedna databáze pro všechny zakladatele | | R |
| 2026-11-04 | Vstup transakce do závěrky | Podle statutu fondu, parametr fondu | | R |
| 2026-11-04 | Krytí výplat | Ověřuje se při autorizaci platby, Odoo nabídne přehled hotovosti | | R |
| 2026-11-04 | Předání příkazů do banky | Soubor, autorizace dvěma osobami, kontrola depozitářem | | R |
| 2026-11-04 | Výjimky u plateb | Přechodný účet a fronta k řešení; přeplatek se vrací, nedoplatek podle statutu | | R |
| 2026-11-04 | Dividendy | Odoo účtuje hrubou dividendu za třídu, srážky a reinvestici počítá IS; závazek se účtuje až po schválení a rozhodnutí o výplatě | Rámec rozhodnut; podrobnosti otevřené (účet pro výplatu, dopad na kurz). Pořadí opraveno 2026-11-05 (nález 6) | R |
| 2026-11-04 | Ceny z Bloombergu | Import z Excelu, automatické napojení případně později | | R |
| 2026-11-04 | Reálná hodnota | Poslední známá cena; Odoo eviduje cenu a podklad; FX a přecenění na RH odděleně; protiúčty podle matice IFRS 9 / IAS 21 (majetkové FVOCI bez recyklace, dluhové FVOCI s recyklací a FX do výsledku, naběhlá hodnota FX do výsledku) | Doplněno 2026-11-05 podle kontroly (nález 5); ověřit s auditorem | R |
| 2026-11-04 | Částečný prodej | Pořizovací cena průměrem u počítatelných nástrojů, jinak určí uživatel; kurzový rozdíl se odúčtuje na samostatné P&L účty | | R |
| 2026-11-04 | Odoo Mates | Ve vývoji se nepoužívají, zůstávají ve výukové `odoo_cz` | | R |
| 2026-11-04 | Kniha = společnost | Každá účetní kniha je hlavní společnost, ne pobočka; SICAV i podfondy jsou samostatné společnosti | | R (ověřit v etapě zkušebních knih) |
| 2026-11-04 | Třída na účetním řádku | Vlastní pole, prázdné = společná položka | | N |
| 2026-11-04 | Číselník fondů a tříd | Vlastníkem je Odoo, IS dostává kopii | Lze změnit | R |
| 2026-11-04 | Plán verzí | Vývoj na Community, Enterprise zůstává otevřené | | Př |
| 2026-11-05 | Pořadí nasazení | Investra Services, investiční společnost, potom fondy | | R |
| 2026-11-05 | Části SICAV | Jedna společnost, pole části na účetním řádku, výkazy po částech i za celek | Potvrzeno metodikou ČNB: ROFOS10/VYFOS20 mají sloupce Investiční / Ostatní činnost / Vzájemný zápočet | R |
| 2026-11-05 | Převzetí fondů | Ke dni uzávěrky nebo ocenění, paralelní běh, historie jako archiv | | R |
| 2026-11-05 | Výroční zprávy | Samostatný modul `investra_annual_report`; zatím export a dokončení ve Wordu | | R |
| 2026-11-05 | Verze Odoo | Odoo 20 Community, připnuté sestavení `20.0-20261102`, aktualizace řízeně; výuková `odoo_cz` zůstává na 19 | | R |
| 2026-11-05 | Detail dat pro výkazy | Atributy pro ČNB a výroční zprávy jako strukturovaná pole (ne analytika) na řádku, protistraně a nástroji; typ pohybu na řádku; převodové tabulky s platností | Ověřeno proti metodice SDAT FOFI20261201 | R |
| 2026-11-05 | Paměť projektu | Sdílená paměť v repozitáři (`CLAUDE.md`, `docs/`), soukromý GitHub pod osobním účtem; kontrola AI agentem (týdně a na vyžádání) i člověkem; jen naše závěry, ne texty předpisů | | R |
| 2026-11-05 | Pořadí výpočtů za třídy | Výchozí pořadí úplaty → performance fee → daň → dohady; parametr fondu podle statutu | Kontrola, nález 4 | R |
| 2026-11-05 | Definice ΔT | ΔT zahrnuje i řádky s třídou na účtu vnitřního zúčtování; příklad performance fee přepočten a bude prvním testem `investra_nav` | Kontrola, nález 3 | R+P |
| 2026-11-06 | Katalog ČNB | Výkazy, položky, kontroly a číselníky uložené v `docs/cnb/`: CSV je zdroj, XLSX se z nich generuje; verze podle metodiky | Veřejná data SDAT, aby se nemusela znovu dohledávat a mohlo je načíst Odoo | R |
| 2026-11-06 | Postup ocenění | Jeden záznam ocenění s kroky a uloženými vstupy; návrhy dokladů (zaúčtování viz řádek Zaúčtování ocenění); typovaná pravidla poplatků s řešením kruhové závislosti | Doporučení, čeká na rozhodnutí; popis v Doc | N |
| 2026-11-06 | Mapování výkazů | Buňka výkazu je typované pravidlo s platností a vazbou na metodiku; deriváty po smlouvách brutto; stav sjednáno, nevypořádáno; ruční zásah jen se zdůvodněním | Mapování se v čase mění, výkazy mají vznikat bez ručního dorovnání; popis v Doc (Z účetnictví do výkazů) | R |
| 2026-11-06 | Zaúčtování ocenění | Varianta B: schvaluje se kompletní finální ocenění po poplatcích, dohadech a dani, se sumářem z nezaúčtovaných návrhů; druhá osoba povinná, vedení fondu volitelné, další schvalovatelé a pořadí jsou parametr fondu; zaúčtuje se jedním krokem k datu ocenění před odesláním depozitáři; vrácení před zaúčtováním je oprava návrhů a nová verze, vrácení depozitářem storno všech dokladů ocenění a nová verze; kurz, zveřejnění a uzamčení ocenění i období až po stanovisku depozitáře | NAV a sumář počítají zaúčtovaný stav plus návrhy; návrhy se po odeslání zamknou se snímkem; kontrola proti sumáři před zaúčtováním. Ověřeno v kódu Odoo 20, prototypem zatím ne | R+P |
| 2026-11-07 | Rámce jednotek | Každá jednotka má jeden rámec: vyhláška 500/2002 Sb., vyhláška 501/2002 Sb. s IFRS pro finanční nástroje, nebo plné IFRS | U rámce 501 nejde o souběh; znění § 4a ověřit | R |
| 2026-11-07 | IFRS 18 | Jednotky na plném IFRS používají IFRS 18 místo IAS 1 pro období od 1. 1. 2027 | Přijato EU v únoru 2026 | R |
| 2026-11-07 | Ochrana zaúčtování | Zamčené návrhy ocenění chrání serverová kontrola; automatické účtování přijatých faktur je v šabloně společnosti vypnuté | Standardní zaúčtování kontroluje jen účetní skupinu | R+P |
| 2026-11-07 | Pravidla archivace | Pravidla podle druhu záznamu a export archivu čitelný bez Odoo | Lhůty ZISIF ověřit | R |
| 2026-11-07 | Prototyp NAV | Ověřit celý cyklus na jednom fondu před plným vývojem fondových modulů | Největší riziko se má ověřit brzy | R |
| 2026-11-07 | Bankovní tok | Výpisy se načítají automaticky a párování se připraví jako návrh; účetní ho vždy schválí, automatické zaúčtování je budoucí volba, zatím vypnutá | | R |
| 2026-11-07 | Dashboard | Přehled napříč fondy se stavem ocenění, výjimkami a termíny ČNB | | R |
| 2026-11-07 | Registrace uživatelů | V produkci vypnutá, účty zakládá správce | | R |
| 2026-11-07 | Třídy fondů | Fondy jsou vícetřídové, model i prototyp s tím počítají od začátku | | R |
| 2026-11-07 | Příprava před fondy | Napojení IS a mapa DORA jsou součástí přípravy před převzetím fondů | | R |
| 2026-11-07 | Cílový termín | Start a převzetí fondů reálně ke konci Q1 2027 | Upřesnit podle harmonogramu | Př |
| 2026-11-07 | Rozdělení vývoje | Záměr: Jan Polan hlavně česká lokalizace; fondové moduly Martin Zíma s Claude | Rozsah práce Jana Polana zatím není rozhodnutý; nezávislou kontrolu fondového kódu určit | N |
| 2026-11-07 | IFRS 9 | Systém je univerzální a podporuje všechny modely podle IFRS 9; klasifikace a model jsou na nástroji s platností, převzatý fond si zachová nastavení | Rozsah implementace podle prvních fondů | R |
| 2026-11-07 | Kontinuita | Náhradní aplikace nebude; kontinuitu zajistí zálohy, obnova a bezpečnost Odoo | Požadavky DORA zůstávají | R |
| 2026-11-07 | Provozní manuál | Před převzetím fondů vznikne manuál pro účetní včetně zastupování | | R |
| 2026-11-07 | Fakturace úplat | Úplaty mezi společnostmi vznikají automaticky u obou stran | Ověřit prototypem | R+P |
| 2026-11-07 | Harmonogram a akceptace | Termíny a akceptace podle `docs/harmonogram.md` | Bez rezervy, znovu posoudit po bráně 22. 1. | R |
| 2026-11-07 | Začátek prací | Začíná se účetnictvím Investra Services s.r.o., prototyp NAV navazuje souběžně | Community, nebo Enterprise se domluví s Janem Polanem a Martinem Olivou | R |
| 2026-11-07 | Mzdy | Vede je externí dodavatel, do Odoo se importuje jen účetní zápis | Formát domluvit | R |
| 2026-11-07 | Osnova Investra Services | Vychází ze standardní české osnovy pro podnikatele; úpravy podle `docs/osnova-investra-services.md` | Návrh, čeká na potvrzení | N |
| 2026-11-07 | Osnova fondů | Cíl je jedna šablona pro všechny fondy; převzatý fond se ke dni přechodu převede převodovou tabulkou | Jiná než osnova Services | R |
| 2026-11-07 | Typy nástrojů | Číselník typů navrhuje kategorii IFRS 9, způsob ocenění, roli účtu a list ČNB; účetní může na nástroji změnit | Návrhy potvrdí účetní politika | R+P |
| 2026-11-07 | Úročení nástrojů | Výchozí je efektivní úroková míra, lineární úročení je volba podle fondu a musí mít zdůvodnění | Platí pro nástroje v naběhlé hodnotě; soulad ověřit s auditorem | R+P |
| 2026-11-07 | Ostatní podíly | Investice do fondů bez ISIN jsou samostatná skupina nástrojů s upisovacím závazkem, vazbou na fond a třídu | Účtování platby, vypořádání a podrozvahy se doplní | R+P |
| 2026-11-07 | Okamžik zaúčtování obchodu | Parametr fondu podle IFRS 9: Trade date accounting (výchozí), nebo Settlement date accounting | Jednotně pro stejně klasifikovaná aktiva; ostatní podíly mají vlastní postup | R |
| 2026-11-07 | Změna klasifikace | Klasifikace je po prvním obchodu neměnná; nahrazuje „s platností“ ze záznamu IFRS 9. Výjimka: reklasifikace dluhových nástrojů při změně obchodního modelu podle IFRS 9 jako samostatný schválený krok | Výjimka se doplní do systému, až bude potřeba | R |
| 2026-11-07 | Termíny ČNB | Termíny a výkazy zveřejňuje ČNB v SDAT a budou se stahovat odtud; v Odoo se negenerují podle vlastních pravidel | Zatím jen obecné příklady | R |
| 2026-11-07 | Měna zveřejnění kurzu | Třída má měnu zveřejnění kurzu; dosavadní pojem „měna třídy“ znamená právě ji a probíhají v ní úpisy a odkupy. NAV fondu a kapitál třídy zůstávají ve funkční měně | Upřesnění záznamu Funkční měna | R |
| 2026-11-07 | Jedna pracovní relace | Kód, dokumenty, Claude Doc i export architektury se dělají v relaci ve VS Code; relace v aplikaci se pro projekt nepoužívá | Nahrazuje rozdělení relací v `CLAUDE.md` | R |
| 2026-11-07 | Rozsah harmonogramu | Do etapy Základ a fond patří registr protistran, převodová tabulka na výkazy, událost Převzetí, výchozí stav tříd a historie FK; první měsíční výkazy jsou nutné pro první fond | Termíny beze změny, posoudit na bráně 22. 1. | R |
| 2026-11-07 | Den kurzu na dokladech | Doklad bere kurz ČNB ke dni účetního případu, u české společnosti k DUZP; ve dnech bez kurzu poslední vyhlášený. Odoo 20 hledá kurz ostře před datem, `investra_rates` to upravuje | Ověřit § 24 zákona o účetnictví a zapsat do účetní politiky | R+P |
| 2026-11-07 | Přecenění cizích měn | Services měsíčně a na žádost účetního, fondy při ocenění; doúčtování do zůstatku na oddělené účty, výstup je návrh dokladu; doklad do přeceněného období se řeší doplňkovým přeceněním | Politika v `docs/politika-preceneni.md`, schválil Martin Zíma bez posouzení auditorem | R |
| 2026-11-07 | Zdroj kurzu | Kurz se řídí měnou účetnictví: CZK ČNB, EUR ECB; pevný kurz se nepoužívá | Upřesňuje záznam Funkční měna; systém zdroj kontroluje u knih a profilů přecenění; přepočet pro NAV se řídí statutem | R |
| 2026-11-07 | Směna měny | Přepočet kurzem ČNB, rozdíl proti skutečnému kurzu jako realizovaný zisk nebo ztráta v den směny; § 24d odst. 6 se nepoužívá | | R |
| 2026-11-07 | Vazba záznamu na knihu | Po založení nejde pohyb, obchod, cenu, splátku, ocenění, externí částku ani termín přesunout do jiného fondu; omyl se řeší smazáním a novým záznamem, proto příprava smí smazat nezaúčtovaný pohyb. Zaúčtovaný pohyb je zamčený | Bezpečnostní revize větve: Odoo kontroluje přístup při zápisu jen podle stavu před změnou | R |
| 2026-11-07 | Čtyři oči u ceny | Zadavatel je i ten, kdo změnil návrh ceny; schválit nesmí zadavatel ani zakladatel záznamu; systémová pole nejdou nastavit ani přes kontext volání | Bezpečnostní revize větve; platí i pro stav obchodu a ocenění | R |
| 2026-11-08 | Uzávěrka Services | Účty 701, 702, 710 se nepoužívají a jsou archivované; výsledek ukazuje Odoo na 431, rozdělení výsledku se účtuje ručně, knihy uzavírá nevratný zámek období | Odchylka od ČÚS 002 podle § 36 odst. 1 ZoÚ; popsat ve směrnici a ověřit s auditorem. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Párování zúčtovacích účtů | Zapnuto u 324, 325, 335, 342, 378, 379, 388, 389; u 331 a 336 vypnuto, zápisy z externího systému přijdou v sumě; časové rozlišení 381 až 385 se nepáruje | Zapnutí jde později i při existujících dokladech. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Typy účtů Services | 231, 232, 241, 249, 453 krátkodobý závazek; 451, 452, 459, 461 dlouhodobý závazek | Opravuje typ aktivum a vlastní kapitál ze standardní osnovy; ve výkazu rozhoduje zbytková doba splatnosti. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Smíšené účty Services | Účty 373, 395 a 481 se nechávají beze změny; případné další účty se doplní, až budou potřeba | Nový účet jde založit i s doklady; změna typu účtu s doklady působí zpětně. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Účet 473200 | Skrytý (archivovaný); krátkodobé dluhopisy jsou na 241000 a Services dluhopisy nevydává | Jde kdykoli zapnout. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Výchozí účty deníků Services | Prodejní deník 602000, nákupní 518000 | Dřív 604000 a 504000 (zboží). Jen předvyplňuje řádek dokladu. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Názvy účtů a 593 Services | Opraveny názvy 347 Ostatní dotace, 358 Pohledávky za společníky sdruženými ve společnosti, 563 Kurzové ztráty; účet 593 archivován; 547 a 647 se nechávají | Vyhláška 500 mimořádné provozní a finanční položky uvádí. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | Daně a fiskální pozice Services | Archivováno 32 daní a 4 fiskální pozice; fáze: neplátce, identifikovaná osoba, plátce | Test na kopii: výchozí daň účtu přidala odpočet 21 %, po archivaci ne. Žádost o identifikovanou osobu podána. Podklad `docs/osnova-revize-podklad.md` | R |
| 2026-11-08 | DPH identifikované osoby | Registrace dorazila; daně pro přijaté služby z EU ve vlastním modulu `investra_vat_identified` (daň k úhradě bez odpočtu, zvyšuje náklad); platí pro každou knihu, která je jen identifikovanou osobou | Zaúčtování a řádky přiznání potvrdí metodik nebo daňový poradce; den účinnosti a DIČ doplnit; nainstalováno v `investra_dev` 2026-11-08 | R+P |
