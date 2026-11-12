<!-- Export z Claude Doc "Investra – architektura Odoo a IS" (https://claude.ai/artifact/YPQf7hVsbVDpGgRAxYH19w). Zdroj pravdy je Doc; soubor se přepisuje exportem, neupravovat ručně. Revize Doc: 318. -->
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
| IFRS 18 | Jednotky na plném IFRS používají IFRS 18 místo IAS 1 pro období od 1. 1. 2027 | Rozhodnuto |
| Ochrana zaúčtování | Zamčené návrhy ocenění chrání serverová kontrola; automatické účtování přijatých faktur je v šabloně společnosti vypnuté | Rozhodnuto, ověřit prototypem |
| Pravidla archivace | Pravidla podle druhu záznamu a export archivu čitelný bez Odoo; lhůty ZISIF ověřit | Rozhodnuto |
| Prototyp NAV | Ověřit celý cyklus na jednom fondu před plným vývojem fondových modulů | Rozhodnuto |
| Bankovní tok | Výpisy se načítají automaticky a párování se připraví jako návrh; účetní ho vždy schválí, automatické zaúčtování je budoucí volba, zatím vypnutá | Rozhodnuto |
| Dashboard | Přehled napříč fondy se stavem ocenění, výjimkami a termíny ČNB | Rozhodnuto |
| Registrace uživatelů | V produkci vypnutá, účty zakládá správce | Rozhodnuto |
| Třídy fondů | Fondy jsou vícetřídové, model i prototyp s tím počítají od začátku | Rozhodnuto |
| Příprava před fondy | Napojení IS a mapa DORA jsou součástí přípravy před převzetím fondů | Rozhodnuto |
| Cílový termín | Start a převzetí fondů reálně ke konci Q1 2027, upřesnit podle harmonogramu | Předpoklad |
| Rozdělení vývoje | Záměr: externí vývojář hlavně česká lokalizace, fondové moduly interně s Claude; rozsah externí práce zatím není rozhodnutý, nezávislou kontrolu fondového kódu určit | Návrh, k rozhodnutí |
| IFRS 9 | Systém podporuje všechny modely podle IFRS 9; klasifikace a model jsou na nástroji s platností, převzatý fond si zachová nastavení, implementace podle prvních fondů | Rozhodnuto |
| Kontinuita | Náhradní aplikace nebude; kontinuitu zajistí zálohy, obnova a bezpečnost Odoo, požadavky DORA zůstávají | Rozhodnuto |
| Provozní manuál | Před převzetím fondů vznikne manuál pro účetní včetně zastupování | Rozhodnuto |
| Fakturace úplat | Úplaty mezi společnostmi vznikají automaticky u obou stran | Rozhodnuto, ověřit prototypem |
| Harmonogram a akceptace | Termíny a akceptace podle docs/harmonogram.md, bez rezervy, znovu posoudit po bráně 22. 1. | Rozhodnuto |
| Začátek prací | Začíná se účetnictvím Investra Services s.r.o., prototyp NAV navazuje souběžně | Rozhodnuto |
| Mzdy | Vede je externí dodavatel, do Odoo se importuje jen účetní zápis; formát domluvit | Rozhodnuto |
| Typy nástrojů | Číselník typů navrhuje kategorii IFRS 9, způsob ocenění, roli účtu a list ČNB; účetní může na nástroji změnit | Rozhodnuto |
| Úročení nástrojů | Výchozí je efektivní úroková míra, lineární úročení je volba podle fondu a musí mít zdůvodnění | Rozhodnuto |
| Ostatní podíly | Investice do fondů bez ISIN jsou samostatná skupina nástrojů s upisovacím závazkem a vazbou na fond a třídu | Rozhodnuto |
| Okamžik zaúčtování obchodu | Parametr fondu podle IFRS 9: Trade date accounting (výchozí), nebo Settlement date accounting | Rozhodnuto |
| Změna klasifikace | Klasifikace je po prvním obchodu neměnná; výjimkou je reklasifikace dluhových nástrojů při změně obchodního modelu jako samostatný schválený krok | Rozhodnuto |
| Termíny ČNB | Termíny a výkazy zveřejňuje ČNB v SDAT a budou se stahovat odtud; zatím jen obecné příklady | Rozhodnuto |
| Měna zveřejnění kurzu | Třída má měnu zveřejnění kurzu, probíhají v ní úpisy a odkupy; NAV fondu a kapitál třídy zůstávají ve funkční měně | Rozhodnuto |
| Den kurzu na dokladech | Doklad bere kurz ČNB ke dni účetního případu, u české společnosti k DUZP; ve dnech bez kurzu poslední vyhlášený | Rozhodnuto |
| Přecenění cizích měn | Services měsíčně a na žádost účetního, fondy při ocenění; doplúčtání do zůstatku na oddělené účty, výstup je návrh dokladu; doklad do přeceněného období řeší doplňkové přecenění | Rozhodnuto |
| Zdroj kurzu | Kurz se řídí měnou účetnictví: CZK ČNB, EUR ECB; pevný kurz se nepoužívá | Rozhodnuto |
| Směna měny | Přepočet kurzem ČNB, rozdíl proti skutečnému kurzu jako realizovaný zisk nebo ztráta v den směny | Rozhodnuto |
| Vazba záznamu na knihu | Po založení nejde pohyb, obchod, cenu, splátku, ocenění, externí částku ani termín přesunout do jiného fondu; omyl se řeší smazáním a novým záznamem, proto příprava smí smazat nezaúčtovaný pohyb. Zaúčtovaný pohyb je zamčený. | Bezpečnostní revize větve: Odoo kontroluje přístup při zápisu jen podle stavu před změnou. |
| Čtyři oči u ceny | Zadavatel je i ten, kdo změnil návrh ceny; schválit nesmí zadavatel ani zakladatel záznamu; systémová pole nejdou nastavit ani přes kontext volání. | Bezpečnostní revize větve; platí i pro stav obchodu a ocenění. |
| Uzávěrka Services | Účty 701, 702, 710 se nepoužívají a jsou archivované; výsledek ukazuje Odoo na 431, rozdělení výsledku se účtuje ručně, knihy uzavírá nevratný zámek období. | 2026-11-08. Odchylka od ČÚS 002 podle § 36 odst. 1 ZoÚ; popsat ve směrnici a ověřit s auditorem. |
| Párování zúčtovacích účtů | Zapnuto u 324, 325, 335, 342, 378, 379, 388, 389; u 331 a 336 vypnuto, zápisy z externího systému přijdou v sumě; časové rozlišení 381 až 385 se nepáruje. | 2026-11-08. Zapnutí jde později i při existujících dokladech. |
| Typy účtů Services | 231, 232, 241, 249, 453 krátkodobý závazek; 451, 452, 459, 461 dlouhodobý závazek. | 2026-11-08. Opravuje typ aktivum a vlastní kapitál ze standardní osnovy; ve výkazu rozhoduje zbytková doba splatnosti. |
| Smíšené účty Services | Účty 373, 395 a 481 se nechávají beze změny; případné další účty se doplní, až budou potřeba. | 2026-11-08. Nový účet jde založit i s doklady; změna typu účtu s doklady působí zpětně. |
| Účet 473200 | Skrytý (archivovaný); krátkodobé dluhopisy jsou na 241000 a Services dluhopisy nevydává. | 2026-11-08. Jde kdykoli zapnout. |
| Výchozí účty deníků Services | Prodejní deník 602000, nákupní 518000. | 2026-11-08. Dřív 604000 a 504000 (zboží). Jen předvyplňuje řádek dokladu. |
| Názvy účtů a 593 Services | Opraveny názvy 347 Ostatní dotace, 358 Pohledávky za společníky sdruženými ve společnosti, 563 Kurzové ztráty; účet 593 archivován; 547 a 647 se nechávají. | 2026-11-08. Vyhláška 500 mimořádné provozní a finanční položky pořád uvádí. |
| Daně a fiskální pozice Services | Archivováno 32 daní a 4 fiskální pozice; fáze: neplátce, identifikovaná osoba, plátce. | 2026-11-08. Test na kopii: výchozí daň účtu přidala odpočet 21 %, po archivaci ne. Žádost o identifikovanou osobu podána. |
| DPH identifikované osoby | Registrace dorazíla; daně pro přijaté služby z EU ve vlastním modulu investra\_vat\_identified (daň k úhradě bez odpočtu, zvyšuje náklad); platí pro každou knihu, která je jen identifikovanou osobou. | 2026-11-08. Zaúčtování a řádky přiznání potvrdí metodik nebo daňový poradce; den účinnosti a DIČ doplnit; instalace do investra\_dev čeká na souhlas. |
| DPH identifikované osoby: instalace | Modul investra\_vat\_identified nainstalován v investra\_dev; daně 21 % a 12 % IO přijatá služba z EU vznikly v Investra Services, ostatní daně zůstávají archivované. | 2026-11-08. Zaúčtování a řádky přiznání potvrdí metodik nebo daňový poradce. |
| Deníky Services | Archivovány STJ a CABA; nákupní deník má kód FP (dříve PŘIJATÁ FAKTURA). | 2026-11-08. První doklad FP/2026/11/0001; kód jde změnit, dokud nejsou doklady. |
| Datum otevření účetnictví Services | 19. 3. 2026, den vzniku s.r.o. podle obchodního rejstříku; první účetní období do 31. 12. 2026. | 2026-11-08. Dříve 5. 11. 2026 (den instalace). Doklady od vzniku se zaúčtují zpětně. |
| Skrytí a doplnění účtů Services | Archivováno 36 účtů (zásoby a výroba, opravné položky, aktivace materiálu, zemědělství, POS, nemovitosti); přidány 518810 Software - licence a předplatné a 518950 Audit a ověření; 587 a 588 zůstávají. | 2026-11-08. Services nemovitosti nevlastní; účty pro mzdy až po dohodě s dodavatelem mezd. |
| Osnova Investra Services | Revize bodů 1 až 11 hotová, osnova potvrzena v investra\_dev. | 2026-11-08. Nahrazuje návrh z 2026-11-07; DIČ, kontakty, účty pro mzdy a potvrzení zaúčtování DPH zůstávají otevřené. |
| Daně identifikované osoby podle původu dodavatele | Modul investra\_vat\_identified má čtyři daně: 21 % a 12 % z EU (řádky 5 a 6) a ze třetí země (řádky 12 a 13); standardní EX S z l10n\_cz zůstává archivovaná. | 2026-11-08. Právní základ § 6h, § 9 odst. 1, § 108 odst. 3 a § 72 ZDPH; řádky přiznání z druhotných zdrojů, štítky daně ověří poradce. |
| Štítky a fiskální pozice identifikované osoby | Daně IO nesou štítky základu i daně podle standardu; fiskální pozice „Identifikovaná osoba – EU s DIČ“ a „– ostatní zahraničí“; standardní pozice Domácí partneři znovu zapnuta. | 2026-11-08. Pozice nevyplní prázdný řádek, jen omezí nabídku a odeberou nevhodnou daň. Odpočet v řádcích 43 a 44 musí být u IO nula. |
| Provozní banka Services | Fio banka. | 2026-11-09, potvrdil metodik 8. 11. První profil importu výpisů bude pro Fio. |
| Daňové přiznání Services za 2026 | Services podá přiznání elektronicky sama, v běžné lhůtě. | 2026-11-09. Při elektronickém podání 4 měsíce po skončení období (§ 136 odst. 2 písm. a) daňového řádu). Uzávěrka 2026 nemusí být hotová v březnu. |
| Kurzy fondu s funkční měnou EUR | Účetnictví fondu používá kurzy ECB; výkazy pro ČNB jsou vždy v CZK a z EUR se přepočítávají kurzem ČNB. | 2026-11-09, potvrdil metodik 8. 11. Každý přepočet ve výkazu nese kurz, datum a zdroj. |
| Cesta úpisů | Liší se podle fondu (účet fondu nebo sběrný účet), je to parametr fondu. Výplaty odkupů a dividend zadává IS, Odoo je spáruje. | 2026-11-09, potvrdil metodik 8. 11. Ochrana údajů investorů ve výpisech je otevřený bod. |
| Schválení ocenění cizím obhospodařovatelem | Písemně mimo Odoo; schválení se přiloží k ocenění a bez něj ocenění nejde schválit. | 2026-11-09, potvrdil metodik 8. 11. Kdo přílohu zaeviduje, určí schvalovací matice. |
| Performance fee | Jen po třídě fondu (high-water mark a hurdle za třídu); série a vyrovnání nejsou v rozsahu. | 2026-11-09, potvrdil metodik 8. 11. Vyrovnání po investorech by patřilo do IS. |
| Návrh obrazovky NAV od vedoucího | Je to návrh obrazovky, ne druhý výpočet. Výpočet NAV zůstává jen v investra\_nav; převezme se přemostění kapitálu po třídách a údaje o období. | 2026-11-09. |
| Externí revize projektu | Revize a úvaha o variantě iÚčto jsou podkladem, ne rozhodnutím; doporučení rozhodují lidé. | 2026-11-09. Soubory v docs/revize/. |
| Klasifikace IFRS 9 podle fondu a obchodního modelu | Klasifikace není vlastností sdíleného nástroje. Určuje ji obchodní model, ve kterém fond nástroj drží: tentýž nástroj může mít v různých fondech různou klasifikaci a i v jednom fondu může být jeden nákup FVTPL a jiný FVOCI. Klasifikace má platnost od; po prvním obchodu ji změní jen řízená reklasifikace. | 2026-11-09, potvrdil metodik. Upřesňuje záznamy IFRS 9 a Změna klasifikace z 2026-11-07. |
| Role agentů a Google Antigravity | Claude Code je hlavní vývojář a architekt a jediný zapisuje do hlavní pracovní složky, dokumentů a databází. Google Antigravity (jen oficiální rozšíření Google) je druhý vývojář a revizor: vymezené úkoly podle zón kódu, diagnostika a code review, jen v odděleném klonu ve větvích ag/\*, bez pushe, Dockeru a databází. Copilot je nezávislý kontrolor. | 2026-11-09. Šetřit kapacitu Clauda na rutinní práci a mít další nezávislý pohled na kód psaný AI. Nahrazuje jednu pracovní relaci z 2026-11-07. Izolace úrovně 1, úroveň 2 je otevřený bod. |
| Bezpečnostní hook pro Antigravity | Každé volání nástroje Antigravity v odděleném klonu kontroluje bezpečnostní hook s guardem. Guard sám schválí bezpečné čtení, kontroly a commit v rozsahu úkolu na větvi ag/\*. Větve, pull a merge vyžadují potvrzení. Push, Docker, databáze, instalace, přístup mimo klon a obcházení shellu zakáže, stejně jako jakoukoli chybu nebo neznámý vstup. Antigravity smí běžet v režimu Auto se sandboxem. | 2026-11-09. Praktický test v oficiálním rozšíření pro VS Code potvrdil všechna tři rozhodnutí hooku: schválení bez dotazu, vyžádání potvrzení a zákaz. Guard a hook mění jen Claude a každá jejich změna musí projít testy guardu. Nahrazuje preset Request Review. |
| Antigravity se sandboxem a bez gitu | Antigravity zůstává v režimu Auto se sandboxem. Jen upravuje soubory v pracovní kopii odděleného klonu a doplní výsledek úkolu; větev ag/\* a commit s autorem „Antigravity“ vytvoří Claude při převzetí. Guard zná i nástroje rozšíření pro VS Code. | 2026-11-09. Režim Auto je v Antigravity svázaný se sandboxem a sandbox v rozšíření nejde vypnout ani povolit jen pro .git. Varianta s nejmenším počtem potvrzení. Nahrazuje záznam „Antigravity bez sandboxu“, který nešel provést. |
| Copilot jako náhradní vývojář | Když Antigravity narazí na limit, dělá úkol GitHub Copilot (režim Agent) v samostatném okně VS Code nad odděleným klonem, podle stejných zón a postupu: jen soubory z rozsahu úkolu, bez commitu, pushe, Dockeru a databází. Testy Odoo a commit s autorem „Copilot“ dělá Claude při převzetí. Mimo tyto úkoly zůstává Copilot nezávislým kontrolorem. | 2026-11-09, rozhodl uživatel; první úkol AG-005 převzat bez nálezů. Copilot nemá bezpečnostní hook jako Antigravity, chrání ho jen schvalování příkazů a izolace v klonu. Upřesňuje záznam „Role agentů a Google Antigravity“. |
| Struktura nabídky Investra | Nabídka podle práce: Přehled; Ocenění (ocenění, kurzy měn); Portfolio (obchody, ceny, splátky nástrojů); Úpisy a odkupy; Výkazy (termíny ČNB); Nastavení se skupinami Fondy (fondy, účetní knihy, pravidla úplat, alokační schémata), Nástroje (nástroje, typy nástrojů, protistrany), ČNB (převodová tabulka) a Auditní stopa (účetní události). Přecenění cizích měn zůstává v nabídce Účetnictví. | 2026-11-10, schválil uživatel podle podkladu UX z téhož dne. Číselníky a nastavení patří do Nastavení, doplňky účetnictví zůstávají v účetnictví. Nadřazené nabídky jsou v modulu investra\_entity, na kterém závisí všechny moduly. Provedení úkolem AG-006, navazující zelené úpravy AG-007 až AG-010; body z oranžové a červené zóny dostanou samostatné plány. |
| Přepis kurzu | Vyhlášený kurz ČNB nebo ECB smí přepsat jen uživatel se skupinou „Investra: schvalování ocenění“, s důvodem. Přepis se eviduje vedle původního kurzu a platí pro účetnictví i ocenění. Čtyři oči se nevyžadují. | 2026-11-10, rozhodl uživatel (varianta 2). Technické řešení a zámek kurzů Odoo jsou v plánu ochrany kurzů (docs/navrh-ochrana-kurzu.md), který čeká na schválení. |
| Ochrana kurzů | Kurzy Odoo zapisuje jen evidence kurzů Investra; ruční přepis a ruční kurz jsou záznamy evidence s důvodem a ruční zápis kurzu v nastavení měn Odoo se odmítne. Měsíční kurzy ČNB se budou stahovat jako další zdroj. Ocenění s ručním kurzem dostane kontrolu se závažností Upozornění. | 2026-11-10, schválil uživatel (plán ochrany kurzů, varianta C, včetně odpovědí na otázky). Červená zóna, provede Claude; upozornění v ocenění je samostatný krok. Navazuje na „Přepis kurzu“. |
| Přemostění kapitálu tříd | Rozpad od kapitálu minulého ocenění ke konečnému kurzu se ukládá na řádku třídy při výpočtu, s kontrolami přemostění. Sloupec dividend vznikne hned (do zavedení pohybu výplaty dividendy 0); u tříd v jiné než funkční měně se zobrazí i kapitál a pohyby v měně zveřejnění. | 2026-11-10, schválil uživatel (plán přemostění, varianta A). Výsledek NAV, kusy ani kurz se nemění. Rozpad ostatních položek třídy zůstává otevřený. |
| Kurzy měn v nabídce | Nabídka Kurzy měn se přesune z Ocenění do Nastavení → Účtování. | 2026-11-10, schválil uživatel: kurzy používá ocenění i účetnictví. Upřesňuje „Struktura nabídky Investra“. |
| Stahování kurzů ve vývojové instanci | Plánovaná úloha stahování kurzů je ve vývojové databázi zapnutá, chybějící kurzy ČNB z 9. 11. doplněny. V datech modulu zůstává vypnutá a zapíná se při nasazení. | 2026-11-10, schválil uživatel. Kurzy Odoo a evidence kurzů ČNB se po doplnění shodují. |
| Vrácení a storno ocenění | Schvalovatel může s povinným důvodem vrátit ocenění před zaúčtováním (návrhy zaniknou bez storna), vrátit ho za depozitáře a nově stornovat zaúčtované nebo depozitářem potvrzené ocenění (storno dokladů k datu ocenění). Vždy vznikne nová verze v návrhu, stará zůstane s důvodem. Storno se odmítne, když na ocenění navazuje pozdější ocenění. Zveřejněné ocenění se nevrací. | 2026-11-10, schválil uživatel. Oprava po zveřejnění se řeší dalším oceněním nebo podle statutu, ne návratem v systému (období je nevratně uzamčené). |
| Zámek příloh ocenění | Přílohy ocenění (balíček pro depozitáře, soubory ručně doložených úplat) a řádky ručně doložených úplat po odeslání ke schválení nejde změnit ani smazat. Nový balíček vznikne jako nová příloha; uložený otisk upozorní, kdyby soubor neodpovídal. | 2026-11-10, nález a schválení uživatele: u zveřejněného ocenění šlo balíček přepsat jiným souborem, protože Odoo řídí práva k příloze jen podle práva zápisu do ocenění, ne podle jeho stavu. |
| Předávka mezi relacemi | Na konci úkolu, na pokyn „předávka“ nebo u dlouhé konverzace vzniká krátký předávací protokol v adresáři předávek repozitáře (nejvýš 40 řádků, bez důvěrných dat) a odpověď končí promptem pro novou relaci. Nová relace čte jen soubory z předávky. | 2026-11-11, rozhodl uživatel: úspora kreditů – krátké relace s předávkou místo dlouhých konverzací. Pravidlo je v pravidlech projektu (CLAUDE.md). |
| Sdílené tržní ceny | Cena bez fondu je sdílená tržní cena, schvaluje se jednou a platí pro všechny fondy; vede ji kniha investiční společnosti. Cena s fondem je cena fondu (posudek, odchylka), při sdílené ceně téhož dne s důvodem. Cena je v jednotkách měny nástroje za kus, měna se ukazuje a kontroluje. Ocenění bere poslední známou schválenou cenu; cena starší než maximální stáří nástroje je překonatelné upozornění. Oprava schválené ceny ji vrátí ke schválení druhou osobou; hotová ocenění drží svou cenu. | 2026-11-11, schválil uživatel (plán docs/navrh-sdilene-ceny.md, varianta B). Upřesňuje Reálnou hodnotu (poslední známá cena) a Čtyři oči u ceny. Provedeno týž den. |
| Datum ceny v balíčku | List portfolio v balíčku pro depozitáře má sloupec Datum ceny za zdrojem ceny. | 2026-11-11, schválil uživatel: ocenění bere poslední známou cenu, která může být starší než datum ocenění. Provedeno týž den. |
| Obchodní model fondu a zařazení nástroje | Fond má jedno nebo více portfolií s obchodním modelem (Držet pro inkaso, Inkaso i prodej, Ostatní). Pro nástroj v portfoliu je zařazení s kategorií IFRS 9, způsobem ocenění, rolí účtu, testem SPPI, určením (IFRS 9 4.1.5, 5.7.5) a platností od; obchod nese portfolio. Klasifikace, způsob ocenění a role se z nástroje odstraní, typ nástroje je dál navrhuje. Zařazení bez schvalování čtyřma očima. Nový fond dostane portfolio „Hlavní“ s modelem Ostatní (FVTPL). Účtování FVOCI je samostatný otevřený bod. | 2026-11-11, zvolil uživatel (plán docs/navrh-klasifikace-ifrs9.md, varianta B). Upřesňuje Klasifikaci IFRS 9 podle fondu a obchodního modelu (2026-11-09). List ČNB zůstává na nástroji. Provedeno týž den (krok A22 revize); odchylka: zařazení na řádku dokladu není v integritním hashi, chrání ho zákaz změny po zaúčtování. |
| Kniha bez kurzu zdroje | Doklad v měně bez platného kurzu zdroje knihy se odmítne; platí pro knihy ČNB i ECB, kurzovní lístky se chovají shodně. Chybějící kurz se zadá jako ruční kurz zdroje knihy s důvodem. Křížový kurz mezi ČNB a ECB se nepoužívá, jsou to nezávislé lístky. | 2026-11-11, rozhodl uživatel. Test potvrdil, že kniha ECB přepočte měnu mimo ECB společným kurzem ČNB. Plán provedení v docs/navrh-ochrana-kurzu.md (Riziko 4) čeká na schválení. Upřesňuje Ochranu kurzů (2026-11-10). |
| Klasifikace IFRS 9 po krocích (a)–(f) | Zařazení eviduje odděleně (a) povahu nástroje podle IAS 32, (b) test SPPI s odůvodněním a zněním IFRS 9, (c) obchodní model portfolia (Držet pro inkaso, Inkaso i prodej, Řízení na reálnou hodnotu, Obchodování), (d) vypočtenou povinnou klasifikaci, (e) určení 4.1.5 nebo volbu 5.7.5 s odůvodněním a (f) výslednou kategorii s textem zdůvodnění. Podílové listy s právem odkupu a účasti jsou ve FVTPL bez volby 5.7.5; volba není u modelu Obchodování. Ruční přepsání kategorie jen se zdůvodněním, označené jako odchylka a s upozorněním v ocenění. Do prvního obchodu jde vše ručně upravit, pak platí zámek. SPPI pro období od 1. 1. 2026 podle nařízení (EU) 2025/1047. | 2026-11-11, body 1–5 ověřil uživatel vůči IFRS přijatým EU; nařízení 2025/1047 ověřeno jen ze sekundárního zdroje (otevřený bod). Ruční přepsání rozhodl uživatel proti doporučení Clauda. Provedeno týž den (dodatek plánu docs/navrh-klasifikace-ifrs9.md). |
| Platnost kurzů a smíšené kurzy | Nejvyšší stáří kurzu je parametr kurzovního lístku (ČNB denní, ČNB měsíční, ECB) s výjimkami pro jednotlivé měny; jediné místo nastavení, stáří kurzu na fondu a profilu přecenění se odstraní. Smíšené kurzy se nepoužijí ani v zobrazení a souhrnech. Křížový kurz mezi ČNB a ECB se nepoužívá ani výjimečně; v krajním případě se zadá ruční kurz s důvodem. | 2026-11-11, rozhodl uživatel. Plán v docs/navrh-ochrana-kurzu.md (Riziko 4, Upřesnění) čeká na schválení provedení. Upřesňuje Knihu bez kurzu zdroje (2026-11-11). |
| Riziko 4 akceptováno, standard Odoo | Standardní chování Odoo u kurzů se neohýbá: kurzy ČNB zůstanou společné, kniha ECB může u měny mimo ECB převzít společný kurz ČNB, měna bez kurzu má 1,0 a před prvním kurzem platí pozdější kurz. Zámek dokladů a skrytí smíšených kurzů se ruší; měnu mimo ECB doplní v knize ECB ruční kurz s důvodem. Kurz platí v den vyhlášení (den navíc v \_get\_rates zůstává). Tabulka Platnost kurzů platí jen pro ocenění, přecenění FX, úpisy a odkupy. | 2026-11-11, rozhodl uživatel, riziko natažení kurzu akceptuje. Ruší zámek z Knihy bez kurzu zdroje a část o smíšených kurzech z Platnosti kurzů. Charakterizační test zůstává. |
| Platnost kurzů – provedení | Tabulka Platnost kurzů provedena: výchozí stáří ČNB denní 5, ČNB měsíční 35, ECB 5 dní, výjimky pro jednotlivé měny; platí pro ocenění, přecenění cizích měn, úpisy a odkupy. Pole stáří kurzu na fondu a profilu přecenění odstraněna. | 2026-11-11, schválil uživatel. Odchylky v docs/navrh-ochrana-kurzu.md (Provedení – Platnost kurzů). Všech 362 testů modulů prošlo v kopii testovací databáze. |
| Testovací databáze a limit společností | Příprava testů přecenění v investra\_test padala, protože čítač id společností přerostl 10000: Odoo skládá id mapování kódu účtu jako účet × 10000 + id společnosti a testy zakládají společnosti, jejichž id se po testu nevrací. Čítač vrácen na nejvyšší existující id, moduly aktualizovány na aktuální kód, kontrolní kopie databáze smazána. Postup kontroly čítače je v docs/prototyp-nav.md. | 2026-11-11, se souhlasem uživatele. Všech 363 testů modulů Investry prošlo v investra\_test. Limit se týká jen testovacích databází. |
| Ochrana a platnost kurzů v investra\_dev | Moduly investra\_rates a investra\_fx\_revaluation aktualizovány ve vývojové databázi; ochrana kurzů a tabulka Platnost kurzů (ČNB denní 5, ČNB měsíční 35, ECB 5 dní) tam platí. Modul investra\_nav ve vývojové databázi nainstalovaný není. | 2026-11-11, se souhlasem uživatele. Před aktualizací záloha databáze. Na doklady to nemělo dopad, profil přecenění tam zatím žádný není. |
| Detail účetních událostí (bod 15 UX) | Účetní událost ukazuje fond, zdroj s proklikem, částku ve funkční měně (součet MD dokladu) a částku v původní měně, má-li doklad jedinou cizí měnu. Druh je výběr: Obchod, Vypořádání obchodu, Úpis/odkup, Splátka, Ocenění, Konverze měn, Ostatní. Formulář události s řádky dokladu; doklad odkazuje na svou událost. Staré události doplnila migrace. | 2026-11-11, schválil uživatel. Bez účetního dopadu: doklady, klíče a otisky se nemění. Ověřeno v testovací databázi, 378 testů prošlo; vývojová databáze modul událostí zatím nemá. |
| Úpisy a odkupy (bod 8 UX) | Úpis a odkup eviduje zdroj (IS nebo ruční zadání s důvodem, identifikátor z IS), cenu za kus s vazbou na ocenění, poplatek s příjemcem (obhospodařovatel, distributor; platí se ven jako závazek fondu) a rozdíl ze zaokrouhlení kusů. Vše posílá a určuje IS, Odoo jen kontroluje. Parametry na fondu s přepsáním na třídě: desetinná místa kusů (6), zaokrouhlení (dolů), komu patří rozdíl (fond), sazby poplatků; při ručním zadání lze poplatek upravit. Historie změn v chatteru; oprava zaúčtovaného pohybu stornem a novým pohybem, jen do neschváleného ocenění. Tlačítko Zaúčtovat v UI. | 2026-11-11, schválil uživatel. Plán docs/navrh-upisy-odkupy.md (body A–E). Provedení po zámku ocenění. |
| Zámek ocenění ve třech vrstvách | (1) Od stavu Ke schválení do Potvrzeno nejde do fondové knihy zaúčtovat ani stornovat doklad s datem do data ocenění (kromě dokladů ocenění) ani zadat, změnit či smazat úpis nebo odkup; zrušení vrácením ocenění. (2) Zveřejnění nastaví vratný zámek Odoo pro všechny; pojistkou je výjimka z uzamčení Odoo jen pro skupinu schvalování ocenění, účinná po potvrzení druhou osobou a vidět v kontrolách příštího ocenění. (3) Nevratný tvrdý zámek Odoo až po auditu účetní závěrky, ručně. | 2026-11-11, schválil uživatel. Dosud zamykal jen kurzy a zveřejnění nevratným tvrdým zámkem; úpis zadaný po schválení s datem do data ocenění by do NAV nevstoupil nikdy. Mění rozhodnutí Zaúčtování ocenění jen v druhu zámku při zveřejnění. Pořadí: vrstva 1, vrstva 2, pak úpisy a odkupy. |
| Schvalovací matice obhospodařovatele | Matice u účetní knihy obhospodařovatele (Nastavení → Fondy); fond smí řádek jen zpřísnit. Řádek: činnost, kdo provádí (skupina Investry, volitelně jmenovití uživatelé), druhá osoba (ne / ano / kroky v pořadí), kdo schvaluje, platnost od. Činnosti: schválení, vrácení, storno a zveřejnění ocenění, schválení ceny, ruční kurz, výjimka z uzamčení, ruční úpis a odkup, ruční přepsání kategorie IFRS 9. Druhou osobu jde vypnout u každé činnosti, výchozí je zapnuto; úkon bez druhé osoby a změny matice ukáže příští ocenění v kontrolách. Nové role se nezavádějí. | 2026-11-11, schválil uživatel. Mění Schvalování ocenění (2026-11-04, povinná druhá osoba) na „podle matice“ a druhou osobu u výjimky z uzamčení. Soulad nastavení s vnitřními předpisy, statuty a dohodou s depozitářem Odoo neověří. |
| Schvalovací matice – provedení | Každý stupeň má nejnižší roli (příprava ocenění < schvalování ocenění; vyšší splní nižší), volitelně jmenovití uživatelé. Jeden člověk: krok schválení zůstává, smí ho provést i zadavatel. Jednorázové úkony se čtyřma očima (vrácení, storno, zveřejnění, ruční kurz, ruční kategorie IFRS 9) jdou přes žádost → potvrzení a provedou se jménem žadatele po posledním potvrzení. Sdílený kurz a sdílená cena se řídí nejpřísnějším pravidlem dotčených fondů. Platný řádek matice se nemění, změna = nový řádek. Ocenění ukazuje upozornění: schválení bez druhé osoby, úkony bez druhé osoby a změny matice od kontrol předchozího ocenění. | 2026-11-11, odpovědi uživatele; naprogramováno. Odchylka od plánu: úkony podle výchozích řádků (chování před maticí, např. zveřejnění jedním schvalovatelem) se jen zapisují do záznamu „Úkony bez druhé osoby“, kontrola ocenění je neukazuje. Fond s vypnutou druhou osobou migrace nepřevede (fond smí matici jen zpřísnit), platí výchozí matice. |
| Úpisy a odkupy – účty a vzorce | Úpis: přijatá platba = kusy × cena + poplatek + rozdíl ze zaokrouhlení kusů + zbytek. Odkup: hrubá částka = kusy × cena + zbytek, výplata = hrubá částka − poplatek − rozdíl. Kusy × cena na haléře matematicky; zbytek (nesoulad dat z IS) do 0,01 jde na výnos nebo náklad ze zaokrouhlení úpisů a odkupů (výsledek fondu, dělí se mezi třídy poměrem), větší zastaví zaúčtování. Sazba poplatku z hrubé částky; odchylka je upozornění v kontrolách ocenění. Nové role: závazek z poplatků za úpis a odkup, závazek vůči investorům z rozdílů, výnos a náklad ze zaokrouhlení; ve výkazech ČNB na řádcích obdobných stávajících rolí. | 2026-11-11, odpovědi uživatele. Čísla nových účtů jsou pracovní jako celá šablona fondu; osnova podle vyhlášky 501 je otevřený bod. |
| Úpisy a odkupy – provedení (body A–E) | Pohyb má zdroj (IS s identifikátorem jedinečným ve fondu / ruční zadání s důvodem), cenu za kus s vazbou na poslední zveřejněné ocenění (jiná cena jen s důvodem), poplatek s příjemcem, rozdíl a komu patří, stav Nezaúčtováno / Zaúčtováno / Stornováno a historii změn. Tlačítko Zaúčtovat (i hromadně) pro skupinu přípravy ocenění; ruční zadání, storno a oprava jdou přes činnost matice „Ruční zadání úpisu a odkupu“. Oprava = storno k datu pohybu a nový pohyb v návrhu s odkazem; do ocenění od stavu Ke schválení nejde. Ocenění vynechá stornované pohyby, bere čistou změnu kapitálu a upozorní na nezaúčtované pohyby, poplatek mimo sazbu a cenu mimo zveřejněný kurz. Parametry na fondu s přepsáním na třídě: místa a zaokrouhlení kusů, komu patří rozdíl, sazby poplatků, příjemce. | 2026-11-11, naprogramováno a ověřeno v testovací databázi. Odchylky od plánu: desetinná místa kusů 0–6 (ukládají se na 6 míst); pohyb bez ceny (starší) se účtuje jako dřív, tlačítko cenu vyžaduje; nezaúčtovaný pohyb do ocenění dál vstupuje, kontrola je jen upozornění (zpřísnění navrženo). |
| Nezaúčtovaný úpis nebo odkup zastaví ocenění | Kontrola ocenění „Úpisy a odkupy období jsou zaúčtované“ má výsledek Stop: ocenění s nezaúčtovaným pohybem v období nejde předložit ke schválení. Nahrazuje odchylku z provedení bodů A–E (dříve jen upozornění). | 2026-11-11, schválil uživatel. Ruční pohyb by jinak vstoupil do NAV bez zaúčtování a bez schválení podle matice. |
| Osnova fondů podle vyhlášky 501 – zásady přečíslování | Šablona fondů se přečísluje hned, před prvním ostrým fondem, podle skupin směrné účtové osnovy vyhlášky 501/2002 Sb. (příloha č. 4). Úplaty obhospodařovateli, administrátorovi, depozitáři a výkonnostní odměna jdou do skupiny 63 Správní náklady; výsledek běžného období do skupiny 59; účasti do skupiny 41, účast oceňovaná reálnou hodnotou do výsledku do skupiny 38. Role a výpočty se nemění, mění se jen čísla účtů. | 2026-11-11, rozhodl uživatel. Čísla skupin je potřeba ověřit proti doslovnému textu přílohy č. 4; převodová tabulka a migrace knih jsou další krok. |
| Osnova fondů – převodová tabulka | Převodová tabulka podle přílohy č. 4 vyhlášky 501/2002 Sb.: peníze na cestě ve skupině 32, vnitřní zúčtování tříd ve 34, závazky z úpisu, odkupu a rozdílů vůči investorům ve 37 (závazky z emise vlastních cenných papírů). Reverzní repo se dělí podle protistrany: banka nebo centrální banka (sektor ESA S.121, S.122) ve skupině 13, ostatní ve skupině 21 (nová role). | 2026-11-11, rozhodl uživatel; text přílohy č. 4 ověřil ve Sbírce. Upřesňuje zásady přečíslování. Plán přečíslování a migrace čeká na schválení. |
| Osnova fondů – provedení | Šablona a knihy fondů přečíslovány podle přílohy č. 4 vyhlášky 501/2002 Sb. Nové role: repo s nebankovní protistranou (212000) a účasti v reálné hodnotě do výsledku (384000). Zařazení nástroje navrhuje roli podle kategorie IFRS 9 a sektoru ESA protistrany; kontrola ocenění upozorní na odchylku od návrhu. Původní účet účastí se zůstatky nese účasti v reálné hodnotě, pro účasti ve skupině 41 je nový účet; pomocné účty Odoo z třídy 9 přesunuty do 76 a 66. | 2026-11-11, schválil uživatel. Předvaha podle id účtu a NAV beze změny, 432 testů prošlo. Uzavírá otevřený bod osnovy podle vyhlášky 501; mapování ČNB pro účasti v RH zůstává otevřené. |
| Rámce jednotek – upřesnění | Investra Services s.r.o. účtuje podle vyhlášky 500/2002 Sb.; investiční společnost, fondy, podfondy a SICAV podle vyhlášky 501/2002 Sb. Rámec a osnova jsou vlastností knihy, výpočty a výkazy ČNB pracují s rolemi, takže systém obslouží obě osnovy. | 2026-11-12, potvrdil uživatel. Doplňuje Rámce jednotek (2026-11-07). |
| Osnova fondů – syntetické účty | Knihy rámce 501 používají syntetické účty podle vnitřního seznamu (skupina 25 vynechána); kód = syntetický účet + 3 číslice analytiky. Šablona fondů přečíslována: repo s bankou 133, s nebankovní protistranou 214, úvěry 218, deriváty 313, vnitřní zúčtování tříd 341900, závazky z úpisu a odkupu 376, akcie 384, dluhopisy 383, účasti 413100/413200, kapitál tříd 564, úplaty 636 (služby), přecenění 615/715, kurzové 616/716, úroky 711, dividendy 714. Peníze na cestě 119000 a zároveň převodový účet Odoo; neidentifikované platby nový účet 229000 s vlastní rolí (ČNB ostatní pasiva). Kontrola peněz na cestě zůstává upozorněním a neidentifikované platby nezahrnuje. | 2026-11-12, rozhodl uživatel. Nahrazuje peníze na cestě ve 32 a syntetiku z přečíslování 2026-11-11. Zda jsou syntetické účty součástí předpisu, neověřeno. Dělení úvěrů podle splatnosti, účastí podle vlivu, derivátů podle podkladu a úroků podle zdroje až novými rolemi. Předvaha podle id účtu a ocenění beze změny, 434 testů prošlo. |
| investra\_dev – přečíslování osnovy fondů a aktualizace modulů | Přečíslování osnovy fondů se vývojové databáze netýká: je v ní jen kniha Investra Services (rámec 500), modul osnovy fondů ani NAV nejsou nainstalované, fondové knihy ani ocenění nejsou. Aby databáze odpovídala kódu, aktualizovány moduly knih (role účtů 36 → 43) a kurzů (háčky schvalovací matice). | 2026-11-12, se souhlasem uživatele. Záloha a zkouška na kopii; předvaha podle id účtu, doklady a kurzy beze změny, úloha stahování kurzů zůstala zapnutá. Předávka z 2026-11-12 krok uváděla omylem. |
| Role s více účty | Role má v knize jeden hlavní účet pro účtování a k tomu další účty. Zůstatky rolí v ocenění, výkazy ČNB a kontroly sčítají hlavní i další účty; účet smí patřit jen jedné roli. Účet nového bankovního deníku se k roli banky přidá sám. Platby na cestě Odoo jsou na 119100 a 119200 a patří k penězům na cestě. FX přecenění bank se počítá po jednotlivých bankovních účtech. Nová kontrola ocenění upozorní na účet se zůstatkem bez role. | 2026-11-12, rozhodl uživatel. Dosud měla role jen jeden účet, takže zůstatek druhé banky by ve výkazu ČNB chyběl. Zamítnuto: role podle prefixu účtu (čísla účtů v logice) a jen kontrola. Výpočtu FK podle typů účtů se změna netýká. |
| Převody mezi bankami a bankovní poplatky | Převod mezi bankami jde přes peníze na cestě 119000, na který vede i model párování Internal Transfers. Bankovní poplatky jsou na novém účtu 612000 s vlastní rolí, ve výkazu ČNB VYFO20\_11 ř. 23 Náklady na poplatky a provize; na něj vede model párování Bank Fees. Počítá se s Odoo Enterprise (párování výpisů). | 2026-11-12, rozhodl uživatel (poplatky na 612). Modely párování dosud vedly na archivovaný převodový účet a na ztrátu z přecenění. V Odoo Community jde převod v UI jen ručním interním dokladem. Zkouška na kopii: předvaha podle id účtu shodná, testy bez chyb. |
| Testovací databáze – oprava schvalovací matice | Dva řádky matice bez druhé osoby (schválení ocenění a cen) nebyly záměr. Nepoužitý řádek pro ceny vrácen na „s druhou osobou“; řádek pro ocenění zůstává, protože podle něj bylo schváleno jedno ukázkové ocenění, a druhou osobu vrací nový řádek od 13. 11. 2026. | 2026-11-12, rozhodl uživatel. Nic se nemazalo; jednoosobové schválení zůstává v historii. Matice dovoluje změnu jen novým řádkem. |
| Vývojová databáze – aktualizace modulu knih | Modul knih aktualizován kvůli rolím s více účty (role 43 → 44). Mapování rolí ve vývojové databázi zatím není, takže se žádný účet nepřiřadil. | 2026-11-12, se souhlasem uživatele. Záloha a zkouška na kopii; předvaha podle id účtu, doklady a kurzy beze změny, úloha stahování kurzů zůstala zapnutá. |
| Převod mezi bankami – ověření simulací | V Odoo Community převod mezi bankami v UI zadat nejde: ruční záznam bankovní účty nenabízí, bankovní transakce jde vždy na nevyjasněné položky a párování výpisů je jen v Enterprise. Cesta Enterprise přes peníze na cestě ověřena simulací na kopii testovací databáze: po odeslání je 100 000 na penězích na cestě, po připsání a spárování nula; banky ve výkazu ČNB zahrnují všechny bankovní účty, aktiva beze změny. | 2026-11-12, varianta zvolená uživatelem; účtování jen na kopii, kopie smazána. Test v UI až s Enterprise. |
| Excel balíčku pro depozitáře – text jako text | Balíček XLSX pro depozitáře zapisuje text z knihy vždy jako text: název fondu, třídy nebo nástroje začínající „=“ se v Excelu nespustí jako vzorec. | 2026-11-12, uzavírá otevřený bod; jen kód a test, bez migrace. |
| Zámek a storno splátky | Splátka nástroje má stav Návrh, Zaúčtováno, Stornováno. Zaúčtovanou splátku nejde změnit ani smazat. Chybu opraví storno k datu splátky (pozice nástroje se znovu otevře) nebo oprava (storno a nová splátka v návrhu s odkazem na opravovanou), stejně jako u úpisu a odkupu. Zadání, změna, smazání i storno s datem v uzamčeném ocenění skončí chybou. Nová činnost schvalovací matice „Storno a oprava splátky nástroje“, výchozí bez druhé osoby. | 2026-11-12, rozhodnutí uživatele; uzavírá otevřený bod „Zámek splátky po zaúčtování“. |
| Spouštění testů Odoo a role Copilota | Testy Odoo spouští jen Claude jedním skriptem nad testovací databází: celý log se ukládá mimo git, na výstup jde jen souhrn a chyby. Nula testů i chyba v logu je neúspěch. Když se verze modulu v kódu liší od testovací databáze, skript se zastaví, protože by spustil upgrade a migraci; upgrade jen po dohodě a se zálohou. Copilot testy Odoo nespouští, jen čte a komentuje. | 2026-11-12, rozhodl uživatel. Důvod: úspora kreditů, drahé je čtení logu, ne běh. Předávání testů Copilotovi zamítnuto. Pojistka doplněna poté, co běh testů jednoho modulu aktualizoval v testovací databázi i závislý modul během práce jiné relace. |
| Splátky jistiny nástrojů | Jeden mechanismus splátky pro nástroje v naběhlé i reálné hodnotě. Splátka účtuje na inkasa na cestě (119100) proti nástroji, výpis pak inkaso vynuluje párováním. Ve formuláři se vybírá jen nástroj, který fond k datu drží, obchodní model se doplní z nákupu; formulář ukáže zbývající jistinu před a po splátce a předvyplní jistinu a úrok podle kalendáře. Zbývající jistina se vede v kusech pozice, přeplacení odmítne i server. Nástroj v reálné hodnotě nese pořizovací cenu, naběhlý úrok a přecenění. Přepočet efektivní úrokové míry se zatím neřeší: v naběhlé hodnotě jen splátka podle kalendáře. | 2026-11-12, rozhodl uživatel. Důvod: splátka musí nést nástroj a zařazení, jinak ji ocenění nevidí; přímé účtování na banku by se po zavedení výpisů zdvojilo. Etapa 1 splátka, etapa 2 naběhlý úrok v reálné hodnotě v ocenění. Mimořádná splátka v naběhlé hodnotě je otevřený bod k auditorovi. Stávající vklady se nepřevádějí: jistina na jednotku se bere z kalendáře, takže výpočet funguje pro 1 kus × 5 000 000 i pro 5 000 000 kusů × 1. |
| Mimořádná splátka nástroje | Splátka má druh: podle kalendáře, nebo mimořádná. Mimořádná splátka úměrně sníží zbylé toky kalendáře, původní efektivní úroková míra se nemění. S volbou Uzavírá pozici (zaškrtne se sama, když jistina pokryje zbytek; ručně jen u diskontu nebo vyrovnání, formulář pak ukáže neuhrazenou jistinu) uzavře celou pozici a zbytek naběhlé hodnoty doúčtuje ocenění zatím do úrokových výnosů. Poplatek stržený protistranou je samostatná složka splátky na bankovní poplatky; výplata na inkasa na cestě je o něj nižší. | 2026-11-12, rozhodl uživatel. Citace IFRS 9 a IAS 1 neověřené; s auditorem ověřit, zda zbytek při předčasném ukončení nepatří na samostatný řádek. Nový splátkový kalendář a poplatek placený fondu protistranou zůstávají otevřené. |
| Návrhy kalendářních splátek | Kalendářní splátky se nezadávají ručně: denní úloha založí ke splatným tokům kalendáře splátky v návrhu (jistina a úrok podle kalendáře, po mimořádné splátce snížené), uživatel je zkontroluje a zaúčtuje; totéž umí tlačítko v seznamu splátek. Ocenění upozorní na splatný tok bez zaúčtované splátky a rozliší, zda je splátka v návrhu, nebo chybí. Přehled operací ke zpracování (dashboard) se navrhne, až bude známo, kde všude vznikají. | 2026-11-12, rozhodl uživatel (návrhy místo automatického zaúčtování nebo párování s výpisem). Důvod: chybějící splátku by ocenění odúčtovalo do úroků a NAV by byla do jejího zadání nižší. Párování s výpisem až s Enterprise. |

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

Stav modulů a testů je v `docs/prototyp-nav.md`. V Odoo 20 se přístupová práva a záznamová pravidla sloučila do modelu ir.access (soubor security/ir.access.csv s operacemi crud a doménou).

**Třídy:** každá má vlastní měnu zveřejnění kurzu (nezávislou na funkční měně fondu, NAV a kapitál třídy zůstávají ve funkční měně), parametry hurdle a performance a příjemce performance allocation. Performance allocation může přesouvat hodnotu mezi třídami, aniž by měnila celkové NAV podfondu. Třída může být růstová, nebo může vyplácet dividendy.

**Instrumenty:** Dluhopis, akcie, podíl ve společnosti, nemovitost, derivát a ostatní. Fondy často drží aktiva přes SPV jako majetkovou účast, takže pořizovací cena má složky (příplatek mimo základní kapitál, úvěr SPV). Hotovost instrument není, zůstává na bankovních účtech v hlavní knize. Evidence musí od začátku sbírat údaje pro ČNB, například LEI, CFI, sektor a zemi emitenta. U dluhopisů a derivátů také parametry pro ocenění: kupon, frekvenci, splácení, konvenci počítání dní, senioritu a rating.

**Pozice:** nezadávají se ručně, vypočtou se z transakcí k libovolnému datu. Provedená transakce se nepřepisuje, oprava je storno a nová transakce.

**Ceny:** mají historii, zdroj, autora a schválení. Oprava vznikne jako nová verze, aby šlo NAV zpětně zreprodukovat.

**Deriváty a podrozvaha:** deriváty jsou samostatný typ s oběma stranami obchodu a nominály. Fondy vykazují podrozvahové položky, například pohledávky a závazky z termínových operací a opcí a hodnoty předané k obhospodařování.

**Portfoliová transakce:** nese datum sjednání i vypořádání, okamžik zaúčtování je parametr fondu: Trade date accounting (výchozí), nebo Settlement date accounting.

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

### Bankovní tok

Výpisy se načítají automaticky a párování se jen připraví jako návrh. Účetní ho vždy schválí, teprve potom se zaúčtuje. Automatické zaúčtování je budoucí volba, zatím vypnutá.

### Mzdy a fakturace úplat

**Mzdy** se vedou externě, do Odoo přichází jen účetní zápis k importu. Formát se teprve domluví.

**Fakturace úplat** mezi společnostmi vzniká automaticky u obou stran; ověřit prototypem.

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

**Modely IFRS 9:** datový model umí všechny modely podle IFRS 9. Klasifikace je po prvním obchodu neměnná a převzatý fond si zachová své nastavení; reklasifikace při změně obchodního modelu by byla samostatný schválený krok. Implementace se děje podle prvních fondů.

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
| DOFOS31 | Struktura investičních nástrojů | Čtvrtletně, fondy kolektivního investování | Portfolio |
| DOFOS40 | Údaje o nemovitostech | Čtvrtletně, speciální fondy nemovitostí | Portfolio |
| ROFOS13 | Hlášení fondu kvalifikovaných investorů | Ročně, do konce 4. měsíce | Registr fondů, ocenění |
| ROFOS11 | Hlášení fondu kolektivního investování (speciální fondy) | Měsíčně, do 30 dnů | Registr fondů, ocenění, IS |
| VYFOS20 | Výkaz zisku a ztráty | FKI ročně do konce 4. měsíce; fond kolektivního investování čtvrtletně, kumulativně od počátku roku | Hlavní kniha |
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
- **Produkce:** oddělené produkční, testovací a vývojové prostředí; šifrování dat v klidu i při přenosu; role a oddělení povinností; MFA pro privilegované účty; přístup z řízených zařízení a přes VPN s vícefaktorovým ověřením; denní šifrované zálohy mimo primární lokalitu; pravidelné testy obnovy; monitoring; správa aktualizací; registrace uživatelů vypnutá, účty zakládá správce. Současné lokální prostředí je jen prototyp.
- **Uchování a archivace:** Pravidla archivace podle druhu záznamu. Obecně 5 let, účetní závěrka a výroční zpráva 10 let, daňové doklady podle daňových předpisů (zákon o účetnictví § 31, znění ověřit), lhůty ZISIF ověřit. Export archivu musí být čitelný bez Odoo.
- **Dashboard:** přehled napříč fondy se stavem ocenění, výjimkami a termíny ČNB.
- **Kontinuita:** náhradní aplikace nebude. Zálohy, obnova a kontinuita se řeší v rámci Odoo, požadavky DORA zůstávají.
- **Provozní manuál:** před převzetím fondů vznikne manuál pro účetní včetně zastupování.
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

Začíná se účetnictvím Investra Services s.r.o., prototyp NAV navazuje souběžně. Potom přijdou na řadu role účtů a specifikace rozhraní, protože na nich stojí vše ostatní a vyvíjejí se podle nich oba systémy. Etapy popisují vývoj fondových modulů a mohou běžet souběžně s fázemi 1 a 2. Cílem je start a převzetí fondů ke konci Q1 2027, termíny a brány jsou níže.

1. **Investra Services:** zkušební společnost, česká lokalizace, osnova, DPH, banka se schválením účetní, faktury, výkazy.
2. **Prototyp NAV (ověřovací etapa):** běží souběžně s Investra Services; jeden fond, více tříd, CZK a EUR, celý cyklus včetně zámku návrhů, zaúčtování a storna od depozitáře.
3. **Specifikace:** rozhodnutí z otevřených bodů, seznam rolí účtů, účetní politika pro FX.
4. **Dvě zkušební knihy:** CZK a EUR, vlastní osnova, kurzy ČNB a ECB, jako součást Investra Services a prototypu. Ověří návrh „kniha = společnost“.
5. **Specifikace rozhraní s IS:** podle aktuálního zadání, aby mohl začít vývoj IS.
6. **Účtování a FX:** `investra_posting` a FX skupiny, vyzkoušené na simulovaných událostech.
7. **Fondy a portfolio:** fond, třídy, instrumenty, ceny, pozice. Prototyp pole třídy na účetním řádku a vnitřního zúčtování.
8. **Napojení na IS:** závěrky, kurzy, párování plateb, denní kontroly.
9. **Alokace a ocenění:** plná verze po ověření prototypu.
10. **Výkazy:** snímky dat a první výkaz ČNB.

**Etapa Investra Services (fáze 1) navíc zahrnuje:** šablonu společnosti, neměnnost, oddělení rolí a čtyři oči i pro nastavení, zálohy a test obnovy.

**Bankovní tok v etapě Investra Services:** automatické načítání výpisů a návrh párování se schválením účetní; automatické zaúčtování zůstává vypnuté.

**Příprava před fondy:** napojení IS a mapa DORA musí být hotové před převzetím fondů.

**Třídy fondů:** fondy jsou vícetřídové, model i prototyp s více třídami počítají od začátku, ne jako s výjimkou.

**Termíny a brány** (podrobnosti a akceptace jsou v `docs/harmonogram.md`):

| Období | Etapa | Brána |
| --- | --- | --- |
| do 20. 11. 2026 | Příprava | Můžeme začít |
| 16. 11. – 18. 12. 2026 | Investra Services | 18. 12.: zkušební účetní měsíc |
| 7. 12. 2026 – 22. 1. 2027 | Prototyp NAV | 22. 1.: pokračovat, změnit rozsah, nebo změnit plán |
| 25. 1. – 26. 2. 2027 | Základ a fond | 26. 2.: připraveno pro zkušební provoz |
| 1. 2. – 5. 3. 2027 | IS a provoz | Test obnovy prošel |
| 1. 3. – 26. 3. 2027 | Zkušební provoz | 26. 3.: přechod |
| konec Q1 2027 | Převzetí | Přechod schválen |

Na konci plánu není rezerva, termín se znovu posoudí po bráně 22. 1.

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

- **Třídy v různých měnách jsou reálný požadavek.** Jeden fond může mít třídy v CZK i EUR. Model třídy musí mít vlastní měnu. Měna třídy je měna zveřejnění kurzu, probíhají v ní i úpisy a odkupy; funkční měnu fondu podle IAS 21 neurčuje. Fond s třídou v EUR může mít dál funkční měnu CZK: účetnictví a FK se vedou v CZK a kapitál třídy se do EUR přepočítává kurzem k datu ocenění.
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
| Účasti v reálné hodnotě ve výkazu ČNB | Po přečíslování podle vyhlášky 501 (2026-11-11) má účast v reálné hodnotě do výsledku vlastní roli; do rozvahy ČNB jde zatím na řádek Účasti jako dosud, IFRS 9 a metodika mohou chtít řádek finančních aktiv v RH do výsledku | Potvrdí účetní metodik; současně ověřit závaznost tříd a skupin směrné osnovy (§ 66 vyhlášky 501) |
| Aktualizace předpisů | Funkční měna EUR, schvalování, střediska SICAV v předpisu 12; nyní se nemění | Projít později |
| Start Investra Services | Současné účetnictví, termín přechodu, plátcovství DPH, hosting, formát importu mezd | Upřesnit |
| Zdrojové systémy fondů | Které systémy a zda mají údaje po pozicích a pořizovací kurzy | Upřesnit u prvních fondů |
| Podrozvaha v Odoo | Podpora ve standardním Odoo není ověřená, deriváty a opce jsou u fondů významné | Ověřit v prototypu |
| Evidence aktiv uvnitř SPV | Zda Odoo má vést i aktiva dceřiných společností (např. jednotlivé automobily) pro ocenění, limity a výkazy, nebo jen účast a úvěr | Upřesnit |
| Pole výkazů ČNB | Katalog výkazů, položek, kontrol a číselníků je v docs/cnb/ (metodika FOFI20261201) | Doplnit ukazatele u položek bez kontroly a převodníky z Knihovny SDAT; ověřit termíny RISIFI37 a ROFOS13 |
| Převodová tabulka ČNB | Převod rolí na řádky výkazů je pracovní návrh | Potvrdit až při testu výkazů ČNB (rozhodnutí 2026-11-07) |
| Zrušená část třetí vyhlášky 244/2013 Sb. | Možný dopad na Pravidla oceňování u pohledávek po splatnosti a v insolvenci | Zatím neprověřovat (rozhodnutí 2026-11-07); vrátit se při aktualizaci předpisů |
| Hosting | Určuje provoz, zálohy, obnovu a dodavatelskou smlouvu | Rozhodnout před ostrým startem; posoudit proti závazkům v žádosti o povolení a DORA |
| Soulad s žádostí o povolení | Technický popis v žádosti se musí shodovat se skutečným provozem účetnictví a IT | Porovnat žádost s architekturou a s právníkem nebo compliance určit, zda a jak změnu oznámit ČNB |
| Termín startu a převzetí fondů | Cíl je konec Q1 2027; vývoj fondových modulů musí stihnout první fondy, jinak je potřeba přechodné řešení | Sestavit harmonogram zpětně od cíle, připravit záložní postup |
| Dopad DORA | Rozsah pro investiční společnost, role Investra Services a dodavatelů, včetně AI | Určit rozsah a doplnit evidenci dodavatelů |
| Hesla a MFA | Délka hesla závisí na vícefaktorovém ověření; vynutit MFA | Řešit při návrhu produkce; požadavek ověřit v aktuálním NIST SP 800-63B |
| Lhůty uchování podle ZISIF | Zvláštní lhůty pro obhospodařovatele a administrátora nejsou ověřené | Ověřit v aktuálním znění a doplnit do Pravidel archivace |
| Automatické testy (CI) | Testy modulů se zatím spouštějí ručně | Po prvním funkčním modulu nastavit automatickou instalaci modulu a testy |
| Transakční výkazy a oznámení | Katalog pokrývá jen rámec Fondy; hlášení obchodů mají krátkou lhůtu a vlastní data | Ověřit povinnost Investry, pak rozhodnout o rozsahu a doplnit katalog |
| Postup ocenění | Typovaná pravidla poplatků, pořadí modulů | Rozhodnout; doporučení je v části Postup ocenění v Odoo |
| TISIFI10 u nových smluv | Zda je bez vypořádání přeceněním celá změna RH, nebo se vychází z první známé RH; mění výsledek v měsíci sjednání | Počítat celou změnu; potvrdit s ČNB před implementací |
| Výkazy speciálních fondů | Speciální fondy mohou podávat jiné výkazy než FKI, například ROFOS11 a DOFOS70 | Ověřit v plánu výskytů SDAT a doplnit tabulku výkazů |
| Příplatek mimo základní kapitál | Zda se počítá do CET1 a na který řádek DOFOS60 patří; ovlivňuje vykázaný kapitál | Potvrdit s auditorem nebo ČNB |
| Naběhlá hodnota ve fondu | Fond je převážně v reálné hodnotě; EIR nebo lineárně se hodí hlavně pro krátké termínované vklady a úvěry s variabilní sazbou | Potvrdit soulad s § 196 ZISIF s auditorem před napojením účtování |
| Klasifikace podle fondu | Nástroj je společný pro fondy, ale obchodní model má každý fond svůj | Přesunout klasifikaci na vazbu fond a nástroj |
| Oceňování derivátů | Návrh je v docs/navrh-oceneni-derivatu.md, zatím odložený | Rozsah určit podle pozic prvních fondů |
| Napojení na SDAT | Návrh je v docs/navrh-sdat.md; termíny poskytuje služba ctiVykazovaciPovinnost; varianta podpisu a soulad pečeti s § 10 vyhlášky 267/2020 Sb. jsou otevřené | Odloženo do získání přístupu do testovacího SDAT |

### Chybějící podklady

- [ ] Dokumentace a API IS.
- [ ] Kdo a kdy zajistí úpravy IS.
- [ ] Oceňovací dokumentace, včetně „Výpočtu bonusů pro fondy s delší periodou“.
- [ ] Zbývající ukazatele u položek a převodníky ČNB z Knihovny SDAT (ostatní je v docs/cnb/).
- [ ] Ukázky nastavení tříd a alokací od zakladatelů.
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
