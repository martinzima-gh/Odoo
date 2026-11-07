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
