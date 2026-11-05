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
| 2026-11-04 | Funkční měna | CZK nebo jiná (např. EUR); kurzy ČNB i ECB | Předpisy se upraví později, nyní do nich nezasahovat | R |
| 2026-11-04 | FX přecenění | Uživatelsky definované skupiny účtů | | R |
| 2026-11-04 | Třídy a alokace | Široce parametrizovatelné | Různí zakladatelé | R |
| 2026-11-04 | Interval ocenění | Uživatelsky definovaný pro fond, i mimořádná ocenění; kontrola proti statutu a zákonné lhůtě | | R |
| 2026-11-04 | IS | Samostatná aplikace Asetiq: jen vypořádání nákupů a prodejů a evidence držitelů | | R |
| 2026-11-04 | Instrumenty a portfolio | Vlastníkem je Odoo | Asetiq evidenci portfolia nemá | R |
| 2026-11-04 | Příchozí platby | Na účet třídy pro úpisy, banka je v Odoo | | R |
| 2026-11-04 | Výplaty odkupů | Platební příkazy vytváří IS | | R |
| 2026-11-04 | Bankovní účty | Třída má účet pro úpisy a pro odkupy, fond investiční účet; zvlášť pro každou měnu | | R |
| 2026-11-04 | Převody mezi účty | Spouští IS, Odoo je páruje na výpisech | | R |
| 2026-11-04 | Závěrka klientských transakcí | Vytváří IS; více závěrek v jednom oceňovacím období | | R |
| 2026-11-04 | Kurz úpisu v průběhu období | Poslední známý kurz, ruční úprava možná, řídí IS | Do Odoo přichází počet a cena | R |
| 2026-11-04 | Fondový modul | Univerzální, včetně výplaty dividend z tříd | | R |
| 2026-11-04 | Schvalování ocenění | Parametrizovatelné; u fondů Investry povinná druhá osoba; stanovisko obhospodařovatele a depozitáře se eviduje v Odoo | Ocenění schvaluje i administrátor | R |
| 2026-11-04 | Výpočet tříd | Pouze z rozvahy; přesuny mezi třídou a společným majetkem přes vnitřní zúčtování | | R+P |
| 2026-11-04 | Odoo a ABRA | Odoo nahradí ABRA, včetně oběhu dokladů | | R |
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
| 2026-11-04 | Kniha = společnost | Každá účetní kniha je hlavní společnost, ne pobočka; SICAV i podfondy jsou samostatné společnosti | | R (ověřit v etapě 2) |
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
