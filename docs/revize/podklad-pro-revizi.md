# Podklad pro nezávislou revizi projektu Investra na Odoo

Stav k 8. 11. 2026. Podklad je určený jiné AI, která projekt ani Odoo nezná. Popisuje cíl, co je hotové,
jak Odoo funguje, co plánujeme a kde vidíme slabá místa. Zadání revize je v souboru `zadani-pro-ai.md`.

Podklad neobsahuje osobní údaje, hesla ani obsah důvěrných dokumentů. Firmy klientů a fondů nejsou jmenované,
ukázková data v testovací databázi jsou smyšlená.

---

## 1. Kontext: kdo jsme a co stavíme

**Investra** je česká skupina, která chce spravovat investiční fondy pro různé zakladatele:

| Subjekt | Role | Účetní rámec |
|---|---|---|
| Investra Services s.r.o. | Servisní společnost: účetnictví, administrace, IT. Vznik 19. 3. 2026, neplátce DPH, identifikovaná osoba k DPH | Vyhláška č. 500/2002 Sb. (podnikatelé), CZK |
| Investiční společnost (v přípravě, žádost o povolení ČNB) | Obhospodařovatel a administrátor fondů | Vyhláška č. 501/2002 Sb. (finanční instituce) |
| Fondy, SICAV, podfondy (od Q1 2027, převzaté od jiných administrátorů) | Fondy kvalifikovaných investorů (FKI); každý fond i podfond vede samostatné účetnictví (ZISIF § 114, § 164, § 165) | Vyhláška 501 s IFRS pro finanční nástroje, nebo plné IFRS |

**Cíl:** jedna platforma na Odoo pro účetnictví všech subjektů a pro výpočet **NAV** (čisté hodnoty aktiv fondu
a kurzu každé třídy podílových listů nebo investičních akcií), včetně výkazů pro ČNB a podkladů pro depozitáře a audit.

**Samostatný informační systém pro investory (dále „IS“, mimo Odoo)** vede držitele podílů, pokyny k úpisu a odkupu,
jejich vypořádání a osobní údaje. Odoo osobní údaje investorů nedrží; od IS dostává jen souhrny za třídu.

**Lidé a role:**

| Role | Kdo | Co dělá |
|---|---|---|
| Metodik a vlastník projektu | finančník, bývalý účetní metodik | Rozhoduje o účetních postupech, vyvíjí s pomocí AI (Claude Code) |
| Vedoucí | jednatel | Rozhoduje o rozpočtu, edici, harmonogramu |
| Účetní fondů (2 osoby, později víc) | | Ocenění, účtování, výkazy, zastupují se |
| Schvalovatel (druhá osoba) | | Schvaluje ceny a ocenění (princip čtyř očí) |
| Externí vývojář české lokalizace | partner Odoo | Záměr: česká lokalizace (DPH, banka, výkazy), zatím nerozhodnuto |
| Depozitář, auditor, ČNB | externí | Dostávají podklady a výkazy |

**Objem:** start s jedním fondem, postupně desítky fondů a podfondů; ocenění typicky měsíčně, i mimořádně;
fondy mají víc tříd v CZK a EUR.

**Způsob vývoje:** vlastník projektu vyvíjí s AI agentem Claude Code v jedné relaci ve VS Code. Každá změna se testuje,
commituje do vlastní větve a zapisuje do deníku rozhodnutí. AI nic neschvaluje, neúčtuje ani neodesílá.

---

## 2. Odoo pro začátečníka

### Co je Odoo
Open-source podnikový systém (ERP) v Pythonu nad databází PostgreSQL s webovým rozhraním. Skládá se z **modulů**
(addonů): základní moduly dodává Odoo S.A., další komunita (OCA) nebo si je píše firma sama. Používáme **Odoo 20**,
připnuté sestavení `20.0-20261102`.

**Edice:**

| Edice | Licence | Co v ní pro nás chybí nebo je navíc |
|---|---|---|
| Community | LGPL-3, zdarma | Nemá v nabídce rozvahu, výsledovku, hlavní knihu ani zobrazení přiznání DPH; nemá bankovní párování s výpisy, automatické časové rozlišení, vytěžování PDF faktur |
| Enterprise | Předplatné za uživatele (web Odoo uvádí 22,90 až 27,90 € za uživatele a měsíc ročně) | Má výše uvedené; vlastní moduly vyžadují plán Custom |

Vyvíjíme na Community; Enterprise zůstává otevřená volba (rozhodnout do 20. 11. 2026).

### Základní pojmy
| Pojem | Význam |
|---|---|
| Modul (addon) | Balík kódu s manifestem, modely, zobrazeními a daty. Instaluje se a aktualizuje do konkrétní databáze |
| Model | Tabulka s logikou (ORM); např. `account.move` = účetní doklad |
| Zobrazení (view) | Formulář, seznam, kanban, pivot, graf; definované v XML, frontend je framework OWL (JavaScript) |
| Nabídka a akce | Menu a co se po kliknutí otevře |
| Přístupová práva | V Odoo 20 sloučená do modelu `ir.access` (operace a doména, např. „jen záznamy mé společnosti“) |
| Společnost (`res.company`) | Samostatná účetní jednotka s vlastní osnovou, deníky, daněmi a měnou. Uživatel si vpravo nahoře vybírá, které společnosti vidí |
| Pobočka | Podřízená společnost; dědí měnu a kurzy z hlavní, proto pro fondy nepoužitelná |
| Účtová osnova | Účty (`account.account`) s typem (aktivum, závazek, náklad…); kód účtu je uložen pro každou společnost zvlášť |
| Deník (`account.journal`) | Řada dokladů (prodej, nákup, banka, ostatní); určuje číslování, např. `FP/2026/10/0001` |
| Účetní doklad (`account.move`) | Doklad s řádky (`account.move.line`) Má dáti a Dal. Faktura je doklad s typem: přijatá faktura, vydaná faktura, příjemka (účtenka) |
| Daň (`account.tax`) | Sazba a rozpis na řádky dokladu (repartition lines); **štítky** (tags) říkají, do kterého řádku přiznání DPH částka patří |
| Fiskální pozice | Podle partnera (země, DIČ) přemapuje daně a účty na dokladu |
| Kurzy | Pro každou měnu a den; Odoo přepočítává doklady v cizí měně |
| Zámky období | Datum, do kterého nejde účtovat; nevratný zámek uzavře období |
| Párování | Spojení řádků (faktura a platba) na účtech s povoleným párováním |
| Česká lokalizace `l10n_cz` | Česká osnova, daně, fiskální pozice, pole **DUZP** (datum zdanitelného plnění), definice přiznání DPH. Účetní datum i kurz se u českých dokladů řídí DUZP |

### Zjištění o Odoo 20, na která jsme narazili
- Kurz se v Odoo 20 hledá ostře *před* datem dokladu; náš modul to upravuje na kurz ČNB ke dni účetního případu.
- Přijatá faktura z minulého měsíce dostane účetní datum poslední den toho měsíce, z aktuálního měsíce pozdější z data faktury a dneška (pravidlo kvůli číslování).
- Fiskální pozice umí daň na řádku jen přemapovat nebo odebrat; prázdný řádek nevyplní.
- Při zápisu Odoo kontroluje přístup jen podle stavu *před* změnou (záznam šlo přesunout do cizí knihy); opraveno vlastní ochranou.
- Výchozí hodnoty z kontextu volání (`default_*`) se doplňují až uvnitř založení záznamu; obcházely kontrolu stavu; opraveno.
- Přiznání DPH v `l10n_cz` počítá odpočet (řádky 43 a 44) automaticky z daně v řádcích 3 až 13, tedy předpokládá plátce DPH.

---

## 3. Technické prostředí

| Položka | Stav |
|---|---|
| Provoz | Docker na notebooku vlastníka; PostgreSQL v kontejneru; žádná produkce |
| Databáze `investra_dev` | Účetnictví Investra Services (označené TEST, ale už se skutečnými doklady); web na portu 8070 |
| Databáze `investra_test` | Prototyp NAV se smyšlenými fondy Alfa, Beta, Gama, Delta; web na portu 8071 jen na vyžádání; červený pruh TEST |
| Databáze `odoo_cz` | Výuková, Odoo 19 s komunitním balíkem Odoo Mates; ve vývoji se nepoužívá |
| Kód | Soukromý GitHub, větev `feature/nav-prototyp`, `main` beze změn; vlastní moduly v `addons/custom/` |
| Testy | 274 automatických testů vlastních modulů v Odoo, 13 testů modulu DPH, 55 testů referenčního výpočtu NAV mimo Odoo; spouští se ručně, CI zatím není |
| Zálohy | Databáze ano ručně; soubory příloh (PDF dokladů, „filestore“) zatím ne |
| Prohlížení dat | SQL dotazy jen pro čtení v DBeaveru (`docs/sql/`) |

---

## 4. Co je hotové

### 4.1 Účetnictví Investra Services (`investra_dev`)
**Revize osnovy (11 bodů, provedeno 8. 11. 2026):**
- **Uzávěrka:** účty 701, 702, 710 se nepoužívají (Odoo nemá uzávěrkové období); výsledek ukazuje Odoo na 431, rozdělení zisku ručně, knihy uzavírá nevratný zámek.
- **Párování:** zapnuté u zúčtovacích účtů 324, 325, 335, 342, 378, 379, 388, 389.
- **Typy účtů:** opravené typy úvěrů a rezerv, 289 aktivních a 41 skrytých účtů.
- **Názvy a nové účty:** opravené názvy, nové účty 518810 Software a 518950 Audit.
- **Deníky:** výchozí účty deníků 602000 a 518000, nákupní deník FP.
- **Datum otevření:** 19. 3. 2026.

**DPH:** Services je neplátce a identifikovaná osoba (ZDPH § 6h). Ze služeb od zahraničních dodavatelů přiznává
daň bez nároku na odpočet; daň zvyšuje náklad. Standardní české daně by účtovaly i odpočet, proto vznikl modul
`investra_vat_identified` se čtyřmi daněmi (21 % a 12 %, EU a třetí země), štítky přiznání a fiskálními pozicemi.
Zaúčtování ještě potvrdí daňový poradce.

**První doklady:** 9 zaúčtovaných (přijaté faktury, účtenka jako příjemka, dvě vydané faktury, faktury ze zahraničí
v USD s DPH identifikované osoby). PDF se nahrávají do Odoo, ale údaje se opisují ručně (vytěžování v Community není).

**Zjištěné problémy u dokladů:** číslování vydaných faktur v Odoo nesedí s čísly na skutečně vystavených fakturách;
výdaj hrazený soukromě statutárem je zaúčtovaný jako závazek vůči dodavateli; náklady jiné společnosti skupiny
v knize Services; časové rozlišení se v Community dělá ručně.

### 4.2 Fondové moduly (prototyp NAV v `investra_test`)
| Modul | Obsah |
|---|---|
| `investra_entity` | Registr účetních knih (kniha = společnost Odoo), role účtů, skupiny uživatelů |
| `investra_chart_fund` | Pracovní osnova fondu, mapování rolí na účty |
| `investra_rates` | Kurzy ČNB a ECB, neměnný záznam se zdrojem a datem stažení |
| `investra_fund` | Fondy, třídy (měna zveřejnění kurzu, zaokrouhlení), kalendář ocenění |
| `investra_posting` | Účetní události: každý zápis vzniká z události podle pravidla, ochrana dokladů, třída na účetním řádku, storno |
| `investra_instruments` | Typy nástrojů, nástroje, ceny se schválením, obchody (trade date nebo settlement date), pozice |
| `investra_allocation` | Verzovaná pravidla rozdělení mezi třídy |
| `investra_nav` | Úplaty (management, performance fee), ocenění v krocích, kontroly, schválení druhou osobou, zaúčtování, depozitář, zveřejnění kurzu, balíček pro depozitáře (Excel), naběhlá hodnota (EIR), termínovaný vklad |
| `investra_fx_revaluation` | Přecenění cizích měn podle profilů účtů, výstup jako návrh dokladu |
| `investra_counterparty` | Registr protistran a emitentů (země, sektor ESA 2010, LEI) |
| `investra_cnb` | Převodová tabulka rolí účtů na řádky výkazů ČNB |
| `investra_dashboard` | Přehled fondů: stav ocenění, výjimky, termíny ČNB |
| `investra_env_banner` | Červený pruh TEST v testovací databázi |

**Ověřeno:** pět scénářů NAV se shoduje s referenčním výpočtem mimo Odoo (stejný autor, tedy ne nezávislá kontrola);
opakovaný výpočet nic nezdvojí; součet tříd = fondový kapitál; pozice = hlavní kniha; zadavatel si neschválí vlastní ocenění.

**Chybí:** poplatky obchodů, dohadné položky, kupóny a dividendy, repo, úvěry, deriváty a ostatní podíly v účtování,
výkazy ČNB (známý jen rozsah: pro FKI 760 položek), napojení IS, banka, obrazovky ověřené uživatelem, test na reálném objemu.

### 4.3 Bezpečnostní revize (8. 11. 2026)
Nalezené a opravené: obejití schválení ceny (čtyři oči) přes kontext volání a podvržení zadavatele; přesun záznamu
do cizí knihy přes změnu vazby. Otevřené: sdílené nástroje bez omezení na knihu, nezaúčtované návrhy obchodů v pozicích,
zámek splátky, vzorce v Excelu pro depozitáře.

### 4.4 Průzkumy (v `docs/pruzkum/` a `reports/`)
| Téma | Hlavní závěr |
|---|---|
| Edice a hosting | Doporučení Enterprise (plán Custom) na vlastním hostingu v EU; rozhoduje cena vlastního vývoje výkazů |
| Regulatorní změny | Novela ZISIF 130/2026 Sb. účinná od 1. 9. 2026 (úvěry, likvidita, depozitáři); nové metodiky ČNB od 2027 |
| Výkazy ČNB | Pro FKI asi 760 položek, největší mezery: protistrany a registry |
| Převzetí fondu | Postup, data a kontroly ke dni přechodu |
| Dluhové nástroje | Jeden model peněžních toků pro vklady, repo, dluhopisy, úvěry |
| IS v Odoo | Šlo by to za 170 až 290 člověkodnů; pro start externí IS |
| iÚčto pro Services | Česká online účetní služba; pro Services reálná alternativa, pro fondy ne; odloženo |
| Mnoho společností v jedné databázi | Pro desítky fondů model obstojí, stovky nejsou doložené; rizika: správa nastavení, souhrnné přehledy, obnova jednoho fondu |

---

## 5. Klíčová rozhodnutí (výběr, úplný deník v `docs/rozhodnuti.md`)
| Oblast | Rozhodnutí |
|---|---|
| Kniha = společnost | Každý fond, podfond i SICAV je samostatná hlavní společnost Odoo; části SICAV (investiční, neinvestiční) jsou pole na řádku |
| Role účtů | Pravidla (FX, alokace, výkazy) se odkazují na roli účtu, ne na číslo; fungují nad různými osnovami |
| Jediný účtovací modul | Fondové moduly neúčtují přímo; zápis vzniká z události podle pravidla a jde dohledat zpět |
| IS | Samostatná aplikace pro investory; Odoo vlastní fondy, třídy, nástroje, ocenění, účetnictví, banku a výkazy |
| Ocenění | Schvaluje se kompletní finální ocenění po poplatcích a dani; druhá osoba povinná |
| Třídy | Měna zveřejnění kurzu je vlastnost třídy; NAV a kapitál třídy jsou ve funkční měně fondu |
| IFRS 9 | Univerzální podpora modelů; klasifikace na nástroji, po prvním obchodu neměnná |
| Kurzy | Účetnictví v CZK bere ČNB, v EUR ECB; doklad bere kurz ke dni účetního případu (u ČR k DUZP) |
| Přecenění FX | Services měsíčně, fondy při ocenění; výstup je návrh dokladu |
| Bankovní tok | Výpisy se načtou automaticky, párování je návrh, účetní vždy schvaluje |
| Termíny ČNB | Stahují se ze systému ČNB (SDAT), v Odoo se nevymýšlejí |
| Archivace | Pravidla podle druhu záznamu, export čitelný bez Odoo |
| Kontinuita | Náhradní aplikace nebude; zálohy, obnova a bezpečnost Odoo |

---

## 6. Plán a harmonogram
| Období | Etapa | Brána |
|---|---|---|
| do 20. 11. 2026 | Příprava: edice, hosting, rozdělení práce | Můžeme začít |
| 16. 11. – 18. 12. 2026 | Investra Services: lokalizace, DPH, banka se schválením, faktury, výkazy | 18. 12.: zkušební účetní měsíc |
| 7. 12. 2026 – 22. 1. 2027 | Prototyp NAV: jeden fond, víc tříd, CZK a EUR, celý cyklus | 22. 1.: pokračovat, nebo změnit plán |
| 25. 1. – 26. 2. 2027 | Základ a fond: knihy, role, nástroje, IFRS 9, protistrany, převody na výkazy, převzetí | 26. 2.: připraveno ke zkušebnímu provozu |
| 1. 2. – 5. 3. 2027 | IS a provoz: napojení IS, produkce, zálohy, test obnovy, DORA | Test obnovy |
| 1. 3. – 26. 3. 2027 | Zkušební provoz: první fond, dvě ocenění, zkušební výkazy ČNB, manuál | 26. 3.: přechod |
| konec Q1 2027 | První fond v ostrém provozu | |

Harmonogram nemá rezervu a rozsah roste. Akceptační kritéria jsou v `docs/harmonogram.md`.

---

## 7. Otevřené body a rizika (výběr, úplný seznam v `docs/otevrene-body.md`)
| Bod | Proč na tom záleží |
|---|---|
| Community, nebo Enterprise | Chybí výkazy, banka, vytěžování dokladů; vlastní vývoj je drahý |
| Hosting a provoz | Zálohy včetně příloh, obnova, MFA, DORA |
| Účetnictví Services naostro | Databáze označená TEST už má skutečné doklady |
| Napojení IS | Dokumentace a API IS chybí; podmínka převzetí fondů |
| Výkazy ČNB | Velký rozsah; převod rolí na řádky výkazů je pracovní návrh |
| Mnoho společností | UI s desítkami společností, souhrnné přehledy, správa nastavení napříč knihami |
| Uživatelská přívětivost | Obrazovky neověřil uživatel; fondové funkce jsou v aplikaci „Investra“, účetní v aplikaci „Fakturace“ |
| Nezávislá kontrola | Referenční výpočet má stejného autora jako kód |
| DPH identifikované osoby | Zpětná kontrola zahraničních služeb od vzniku; potvrzení postupu poradcem |
| Kapacita | Jeden vlastník vyvíjí s AI; harmonogram bez rezervy |

---

## 8. Uživatelé a hlavní procesy (podklad pro návrh obrazovek)

### Účetní Investra Services
1. Přijatá faktura: nahrát PDF → vznikne prázdný koncept → opsat dodavatele, data, DUZP, měnu, řádky, účet, daň → potvrdit.
2. Účtenka (příjemka): drobný výdaj, často hrazený soukromě; závazek vůči tomu, kdo platil.
3. Vydaná faktura (služby fondům a klientům).
4. Banka: v Community bez párování výpisů; plán je automatické načtení a návrh párování se schválením.
5. Měsíční přecenění cizích měn, uzávěrka, výkazy (rozvahu a výsledovku dnes jen SQL).

**Dnešní třecí plochy:**
- **Ruční práce:** údaje z PDF se opisují ručně a daň identifikované osoby se volí ručně.
- **Kázeň u dat:** DUZP musí odpovídat dni vzniku povinnosti; účetní datum se posouvá samo.
- **Chybějící přehledy:** nejsou v nabídce, předvaha jen přes SQL.

### Účetní fondu (měsíční ocenění)
1. Ceny nástrojů: zadat (případně import z Excelu) → schválit druhou osobou.
2. Obchody a pohyby tříd (úpisy, odkupy ze závěrky IS).
3. Výpočet ocenění: úplaty, performance fee, alokace mezi třídy, kontroly.
4. Schválení druhou osobou → zaúčtování → balíček pro depozitáře → stanovisko depozitáře → zveřejnění kurzu.
5. Přehled fondů napříč knihami: co je hotové, co čeká, výjimky, termíny ČNB.
6. Výkazy ČNB měsíčně.

**Dnešní třecí plochy:**
- **Přepínání společností:** každý fond je společnost, takže přehled napříč fondy a přepínání v UI jsou těžkopádné; prázdné seznamy, když není vybraná správná společnost.
- **Rozdělená nabídka:** fondové funkce jsou v aplikaci „Investra“, účetní funkce (přecenění, doklady) v aplikaci „Fakturace“.
- **Nedokončené obrazovky:** testovací databáze má anglické popisky, v některých seznamech chybí ukázková data, obrazovky nikdo neprošel jako uživatel.

### Schvalovatel a vedoucí
- **Fronta ke schválení:** ceny a ocenění.
- **Stav fondů:** přehled se stavem, výjimkami a termíny.
- **Zastupování:** kdo za koho schvaluje, aby se práce nezastavila.

---

## 9. Pravidla, která musí návrhy respektovat
- **Legislativa:**
  - zákon o účetnictví č. 563/1991 Sb. a vyhlášky 500/2002 a 501/2002 Sb.,
  - České účetní standardy, IFRS ve znění EU,
  - ZISIF č. 240/2013 Sb. a NV 243/2013 Sb.,
  - zákon o DPH č. 235/2004 Sb.,
  - DORA (nařízení EU 2022/2554), GDPR, metodiky výkazů ČNB.

  Právní závěry potvrzuje auditor, daňový poradce nebo právník.
- **Auditovatelnost:** každé číslo dohledatelné k ceně, kurzu, parametru a schvalovateli; neměnnost zaúčtovaného; storno místo přepisu.
- **Čtyři oči** u cen, ocenění a ručních úprav kurzu.
- **Bez úprav jádra Odoo:** všechno ve vlastních modulech s testy.
- **Parametrizace místo kódu:** fondy mají různé statuty.
- **Data o investorech:** Odoo je nedrží.
- **AI nerozhoduje:** navrhuje, člověk schvaluje.
- **Community je základ:** Enterprise je otevřená volba; návrh má říct, co platí pro kterou edici.

---

## 10. Odkazy do repozitáře

Revidující AI repozitář ani kód nedostane. Odkazy slouží k tomu, aby se v otázkách mohla odvolat na konkrétní dokument;
detail pak dodá vlastník projektu.

| Soubor | Obsah |
|---|---|
| `docs/architektura.md` | Úplná architektura (export sdíleného dokumentu) |
| `docs/rozhodnuti.md` | Deník rozhodnutí |
| `docs/otevrene-body.md` | Otevřené body a rizika |
| `docs/harmonogram.md` | Harmonogram a akceptace |
| `docs/prototyp-nav.md` | Stav fondových modulů a testů |
| `docs/analyza-odoo20-nav.md` | Technická zjištění o Odoo 20 |
| `docs/osnova-revize-podklad.md` | Revize osnovy Services a DPH identifikované osoby |
| `docs/pruzkum/`, `reports/` | Průzkumy a rešerše |
| `addons/custom/` | Kód vlastních modulů |
