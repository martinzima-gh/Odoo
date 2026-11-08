# Revize osnovy Investra Services: podklad k rozhodnutí

Stav 2026-11-07. Doplňuje `docs/osnova-investra-services.md`. Účetní rámec: vyhláška č. 500/2002 Sb., podnikatel, CZK.
Vychází ze čtení `investra_dev` (328 účtů, 0 dokladů) a přílohy č. 4 vyhlášky. V Odoo se zatím nic nezměnilo.
Rozhoduje účetní metodik, doporučení jsou jen návrh. Dotazy k ověření jsou v `docs/sql/08-osnova.sql`.

## Co je v pořádku

- Všech 54 účtových skupin směrné osnovy v Odoo je. Navíc jsou jen technické účty 999997 a 999998 pro slevy při platbě.
- Třídy 0, 1, 5 a 6 mají správné typy. Třída 3 je rozdělená na pohledávky a závazky správně, kromě smíšených účtů.
- Kurzové rozdíly míří na 563000 a 663000, přechodné účty na 261000 a 261001.
- Výchozí daň prodeje a nákupu je prázdná, což odpovídá neplátci.

## Proč to udělat před prvním dokladem

Dnes je 0 dokladů, takže změny typů a párování nic nepřepočítávají. Po prvních dokladech už je změna párování nebo typu pracnější.

Priorita typů je nižší, než říká návrh osnovy. Community nemá rozvahu ani výsledovku, jsou tam jen daňové výkazy.
Typ dnes neovlivňuje výpočet, rozhodne až ve výkazech. Výkazy podle vyhlášky 500 budeme stejně skládat podle čísel účtů, nebo přijdou s edicí.

## Body k rozhodnutí

| # | Bod | Nález | Doporučení |
|--:|---|---|---|
| 1 | Uzávěrkové účty 701, 702, 710 | Mají typ podrozvaha. Odoo nedovolí rozvahový a podrozvahový účet v jednom dokladu, takže klasické uzavírací zápisy nejdou zaúčtovat | Nepoužívat je a výsledek nechat na výpočtu Odoo přes 431000; viz níže |
| 2 | Párování | Vypnuté u všech zúčtovacích účtů kromě 311 až 315, 321, 343001 a 343002. Bez něj nejdou sledovat otevřené položky | Zapnout u 324, 325, 331, 335, 336, 342, 378, 379, 388, 389 |
| 3 | Typy podle návrhu | 231, 232, 241, 249 jsou aktivum; 451 až 459 a 461 vlastní kapitál | Opravit podle `docs/osnova-investra-services.md` |
| 4 | Smíšené účty 373, 395, 481 | Znaménko může být obojí, typ je jen jeden | Nechat typ, zařazení řešit až ve výkazu podle zůstatku |
| 5 | 473200 Vydané krátkodobé dluhopisy | Krátkodobý závazek ve skupině dlouhodobých, 241000 už existuje | Skrýt, Services dluhopisy nevydává |
| 6 | Výchozí účty deníků | Prodej 604000, nákup 504000 | Prodej a nákup podle návrhu osnovy; konkrétní účet potvrdí metodik |
| 7 | Názvy | Překlepy: 347 „dodace“, 358 „združenými“, 563 „Kursové“. 593 uvádí mimořádnou činnost, kterou výkazy už nemají | Opravit názvy, 593000 skrýt |
| 8 | Daně | 32 aktivních daní a 4 fiskální pozice, ač jde o neplátce | Ponechat do potvrzení režimu; ověřit, že účetní nemůže sazbu vybrat omylem |
| 9 | Deníky | Ocenění zásob a Daně na hotovostním základě Services nepotřebuje. Kód nákupního deníku je „PŘIJATÁ FAKTURA“ | Archivovat nepotřebné, kód zkrátit, pokud to nezmění číslování dokladů |
| 10 | Datum otevření účetnictví | V Odoo je 5. 11. 2026, tedy den instalace. Účetní období je kalendářní rok | Doplnit skutečné datum zahájení účetnictví |
| 11 | Účty ke skrytí a doplnění | Seznam je v návrhu osnovy; analytiky mezd závisí na dodavateli | Potvrdit skrytí, analytiky až po dohodě s dodavatelem mezd |

## Bod 8: daně a fiskální pozice (rozhodnuto 2026-11-08)

Režim: dnes neplátce, žádost o registraci jako identifikovaná osoba podaná, čeká se na doručení (potvrdil Martin Zíma); později plátce. Pojem identifikované osoby viz doplnění níže (§ 6h ZDPH).
Změna v `investra_dev` (0 dokladů, přes ORM): archivováno všech 32 daní a 4 fiskální pozice.
Důvod: 46 účtů (například 518xxx, 501xxx, 511xxx, 022xxx) má výchozí daň 21 % nebo 12 %. Test na dočasné kopii databáze: před archivací řádek na 518100 sám přidal daň 21 % a 210 Kč šlo jako odpočet na 343121; po archivaci daň nevznikla. Kopie byla po testu smazána.
Výchozí daně na účtech zůstávají a při návratu daní se uplatní.

Fáze: neplátce (žádné daně, DPH z faktury je součástí nákladu) → identifikovaná osoba (zapnout jen daně pro přijetí služby z EU a přenesenou daň; odpočet se neuplatňuje, úpravu účtů a daní potvrdí metodik nebo daňový poradce) → plátce (zapnout daně a nastavit 343xxx; EPO a kontrolní hlášení Community nemá).

## Bod 11: skrytí a doplnění účtů (rozhodnuto 2026-11-08)

V `investra_dev` (0 dokladů, přes ORM) archivováno 36 účtů: zásoby a výroba 111, 112, 119, 121 až 124, 131, 132, 139, 151 až 153; opravné položky 191 až 199; změny stavu zásob a aktivace materiálu 581 až 586; zemědělství 025, 026, 085, 086; POS 311001; nemovitosti 021, 031, 081.
Nemovitosti se skryly, protože je Services nevlastní ani nepronajímá (Martin Zíma), ač rejstřík uvádí jako předmět činnosti pronájem nemovitostí. 587 a 588 (aktivace dlouhodobého majetku) zůstávají, Services může vyvíjet vlastní software.
Nové účty bez výchozí daně: 518810 Software - licence a předplatné, 518950 Audit a ověření (kódy potvrdil Martin Zíma). Účty 336 a 342 pro mzdy se doplní po dohodě s dodavatelem mezd. Účty a daně k DPH identifikované osoby jsou v bodě 8.
Aktivních účtů 289, neaktivních 41 (36 z tohoto bodu a 5 z dřívějších).

## Revize osnovy je hotová (2026-11-08)

Body 1 až 11 jsou uzavřeny. Zbývá doplnit DIČ a kontakty společnosti, účty pro mzdy po dohodě s dodavatelem mezd a potvrzení zaúčtování DPH identifikované osoby metodikem nebo daňovým poradcem.

## Bod 10: datum otevření účetnictví (rozhodnuto 2026-11-08)

Datum otevření účetnictví v `investra_dev` je 19. 3. 2026, tedy den vzniku Investra Services s.r.o. podle výpisu z obchodního rejstříku (datum vzniku a zápisu). Dříve 5. 11. 2026, den instalace. Změna přes ORM, 0 dokladů; zámky období zůstávají prázdné.
První účetní období tak začíná dnem vzniku a končí 31. 12. 2026 (§ 17 odst. 1 zákona o účetnictví, knihy se otevírají ke dni vzniku povinnosti vést účetnictví); Odoo má kalendářní rok.
Doklady od vzniku do dneška se zaúčtují zpětně. Kurzy ČNB jsou načtené od 1. 1. 2026. Vlastní údaje společnosti (IČO, adresa) v Odoo zatím nedoplněny.

## Bod 9: deníky (rozhodnuto 2026-11-08)

V `investra_dev` (0 dokladů, přes ORM): archivovány deníky STJ (Ocenění zásob) a CABA (Daně na hotovostním základě); nákupní deník přejmenován z „PŘIJATÁ FAKTURA“ na „FP“. CABA je v nastavení společnosti vedený jako deník daní na hotovostním základě, který Services nepoužívá.
Číslování ověřeno na zkušebním dokladu, který se vrátil zpět: první doklad nákupního deníku dostane číslo FP/2026/11/0001, číslo se opakuje po měsících. Kód FP navrhl asistent; než přijdou doklady, jde změnit.

### Bod 8, doplnění: identifikovaná osoba (2026-11-08)

Registrace jako identifikovaná osoba dorazila (podle Martina Zímy); den účinnosti a DIČ doplnit.
Standardní daň l10n_cz pro přijetí služby z EU rozpisuje daň na vstup 343121 (odpočet) a výstup 343221. Identifikovaná osoba odpočet nemá, proto vznikl modul `investra_vat_identified` (varianta B):
daň 21 % a 12 % zaúčtuje závazek na 343221 (343212) a zároveň zvýší náklad na řádku dokladu; dluh dodavateli se nemění. Daně se zakládají pro každou společnost voláním `_setup_identified_vat_taxes()`, takže modul poslouží každé knize, která je jen identifikovanou osobou, i po přechodu Services na plátce.
Otestováno na kopii `investra_dev` (6 testů: 21 %, 12 %, dobropis, bez vstupní strany, zaúčtování, opakované založení), kopie smazána. Nainstalováno v `investra_dev` 2026-11-08 se souhlasem Martina Zímy a daně 21 % a 12 % vznikly v Investra Services (0 dokladů); ostatní daně zůstávají archivované.
K potvrzení metodikem nebo daňovým poradcem: zaúčtování (daň do nákladu a závazek), které řádky přiznání platí, štítky přiznání u daně (převzat jen základ). Právní základ je ověřený níže.

### Bod 8, ověření právního základu (2026-11-08)

Čteno doslova na zakonyprolidi.cz, zákon č. 235/2004 Sb. o DPH ve znění od 1. 1. 2026 (verze 69); porovnání s e-Sbírkou nebylo.
- § 6h: osoba povinná k dani se sídlem v tuzemsku, která není plátcem, je identifikovanou osobou ode dne přijetí zdanitelného plnění s místem plnění v tuzemsku od osoby neusazené v tuzemsku (služba, dodání zboží s montáží, dodání zboží soustavami). Platí pro dodavatele z EU i ze třetích zemí. § 6g se týká pořízení zboží z EU, ne služeb.
- § 9 odst. 1: místem plnění služby osobě povinné k dani je sídlo příjemce, tedy tuzemsko.
- § 108 odst. 3 písm. a) bod 1: u služby podle § 9 až 10d od osoby neusazené v tuzemsku přiznává daň příjemce, plátce nebo identifikovaná osoba.
- § 72 odst. 1: k odpočtu je oprávněn plátce; identifikovaná osoba není uvedena. Návrh bez odpočtu s tím souhlasí (výklad, potvrdí poradce).
Důsledek: stejné zaúčtování platí pro Microsoft (EU) i Cloudflare (USA). Daň z modulu se jmenuje „z EU“, což u dodavatele z USA zavádí.
Řádky přiznání: z druhotných zdrojů (Pohoda, pokyny Finanční správy ke kontrolnímu hlášení) služby od osoby registrované v jiném členském státě jdou na řádky 5 a 6, od osoby ze třetí země na řádky 12 a 13; v pokynech k přiznání neověřeno. Povinnost podat kontrolní hlášení identifikovanou osobou neověřena.

### Bod 8, daně ze třetích zemí (2026-11-08)

Standardní l10n_cz má daně 21 % EX S a 12 % EX S pro službu od osoby mimo EU (štítky řádků 12 a 13), ale jsou archivované. Modul `investra_vat_identified` proto zakládá vlastní verze bez odpočtu, stejně jako pro EU. V `investra_dev` přibyly daně „21 % IO přijatá služba ze třetí země“ a „12 % IO přijatá služba ze třetí země“ (základní štítek VAT 12 Base a VAT 13 Base); celkem jsou aktivní čtyři daně, ostatní zůstávají archivované.
Testy 8 z 8 na dočasné kopii `investra_dev`, kopie smazána. Daně jsem přidal bez restartu webu; spuštěný web zná starý kód modulu, dokud se nerestartuje, a na doklady to nemá vliv. Štítek daně (VAT x Tax) se nepřebírá, ověří poradce.

### Bod 8, česká lokalizace, štítky a fiskální pozice (2026-11-08)

Kontrola `l10n_cz` v Odoo 20: pole DUZP na dokladu, účetní datum i kurz se odvozují od DUZP; fiskální pozice přemapují daně podle partnera; definice přiznání DPH má řádky 1 až 66 (zobrazení jen s Enterprise `account_reports`). Identifikovanou osobu nemodeluje: řádky 43 a 44 (odpočet) počítá vzorec z řádků 3 až 13, standardní daně EU S a EX S účtují odpočet, pro dodavatele s vyúčtovanou českou DPH zvláštní režim není.
Změny v `investra_dev` přes modul `investra_vat_identified`:
- štítky daně (VAT 5, 6, 12, 13 Tax) na řádku rozpisu +100 % stejně jako ve standardu, štítky základu beze změny; řádek závazku bez štítku;
- fiskální pozice „Identifikovaná osoba – EU s DIČ“ (skupina DPH EU, DIČ povinné, sekvence 2) a „Identifikovaná osoba – ostatní zahraničí“ (bez země, sekvence 4); daně z EU patří k první, ze třetí země ke druhé;
- znovu zapnuta standardní pozice „Domácí partneři“ (CZ, sekvence 1), jinak by pozice bez země platila i pro české partnery. Odchylka od archivace v bodě 8.
Pozice daň jen přemapuje nebo odebere a omezí nabídku daní; prázdný řádek nevyplní, protože výchozí daně účtů jsou archivované. Dodavatel z EU bez DIČ dostane pozici „ostatní zahraničí“ (řádky 12 a 13).
Testy 13 z 13 na dočasné kopii `investra_dev`, kopie smazána; doklady (11 konceptů) beze změny.

## Bod 7: názvy a účet 593 (rozhodnuto 2026-11-08)

V `investra_dev` opraveny názvy (účty bez dokladů, změna přes ORM): 347000 Ostatní dotace, 358000 Pohledávky za společníky sdruženými ve společnosti, 563000 Kurzové ztráty. Účet 593000 (daň z příjmů z mimořádné činnosti, splatná) je archivovaný.
Účty 547000 a 647000 se nechávají: vyhláška 500 mimořádné provozní a finanční položky pořád uvádí (§ 25, § 27, § 33, § 34; přečteno na zakonyprolidi.cz, znění 1. 1. 2024). Příloha 4 přitom uvádí jen skupiny, názvy účtů si stanoví účetní jednotka.

## Bod 6: výchozí účty deníků (rozhodnuto 2026-11-08)

Prodejní deník FA má výchozí účet 602000 Tržby z prodeje služeb (dřív 604000), nákupní deník PŘIJATÁ FAKTURA účet 518000 Ostatní služby (dřív 504000). Změna přes ORM, 0 dokladů.
Výchozí účet jen předvyplní řádek dokladu; účetní ho může změnit a konkrétní účet určuje metodik.

## Bod 5: účet 473200 (rozhodnuto 2026-11-08)

Účet 473200 Vydané krátkodobé dluhopisy je v `investra_dev` archivovaný (bez dokladů, změna přes ORM). Krátkodobé dluhopisy pokrývá 241000 a Services dluhopisy nevydává; archivovaný účet jde kdykoli znovu zapnout.

## Bod 4: smíšené účty 373, 395, 481 (rozhodnuto 2026-11-08)

Nechává se, jak je: 373000 a 395000 aktivum, 481000 dlouhodobý závazek. V Odoo se nic nemění.
Účty se doplní, až budou potřeba (například samostatný účet pro opačné znaménko). Nový účet jde založit kdykoli, i když jsou doklady.
Změna typu existujícího účtu s doklady v Odoo 20 není blokovaná (kromě pohledávek a závazků v prodejních a nákupních deníkách), projeví se ale zpětně ve všech sestavách; proto typ po prvním dokladu neměnit bez posouzení.
Nepřečteno: zařazení zůstatků 373, 395 a 481 do položek rozvahy podle vyhlášky 500 a ČÚS 003.

## Bod 3: typy účtů (rozhodnuto 2026-11-08)

Změněno v `investra_dev` u devíti účtů bez dokladů, žádný nebyl výchozím účtem deníku ani účtem v daních:
krátkodobý závazek: 231000, 232000, 241000, 249000, 453000; dlouhodobý závazek: 451000, 452000, 459000, 461000.
Rezervy 451, 452 a 459 jsou dlouhodobé, rezerva na daň z příjmů krátkodobá. Typ je orientační, ve výkazu rozhoduje zbytková doba splatnosti.

## Bod 2: párování (rozhodnuto 2026-11-08)

Párování zapnuto v `investra_dev` u 324000, 325000, 335000, 342000, 378000, 379000, 388000 a 389000 (bez dokladů, změna přes ORM).
331000 a 336000 zůstávají vypnuté: mzdy vede externí dodavatel a zápisy přijdou v sumě. Zapnout jde později i s doklady; vypnout nejspíš ne, pokud jsou na účtu spárované řádky (neověřeno).
Časové rozlišení 381 až 385 se nepáruje. Community nemá automatický rozpis odložených nákladů a výnosů ani automatické párování dokladů proti sobě; pravidla párování míří na bankovní řádky.

## Bod 1: uzávěrka

Odoo výsledek období nezapisuje dokladem, počítá ho z výnosů a nákladů a ukazuje na účtu typu nerozdělený zisk, zde 431000.
Pravidlo je ověřené ve zdrojovém kódu (`_check_off_balance`). Průběh roční uzávěrky v Odoo zatím ověřený není.

| Varianta | Co znamená | Riziko |
|---|---|---|
| A: účty 70x a 710 nepoužívat | Závěrka se opře o sestavy, rozdělení zisku účetní zaúčtuje ručně | Ověřit, že to stačí pro uzavření účetních knih podle zákona o účetnictví |
| B: změnit účty na rozvahový typ | Uzavírací zápisy půjdou zaúčtovat | Odoo výsledek počítá i tak, hrozí dvojí zobrazení; nutný test |

**Rozhodnuto 2026-11-08: varianta A.** Účty 701000, 702000 a 710000 jsou v `investra_dev` archivované (bez dokladů, změna přes ORM).

- § 17 zákona o účetnictví (znění od 1. 1. 2026) stanoví dny otevření a uzavření knih, ne techniku; odst. 7 zakazuje zápisy do uzavřených knih po schválení závěrky.
- § 4 odst. 8 a příloha 4 vyhlášky 500 předepisují skupiny 70 a 71, ne účty 701, 702, 710. § 4 odst. 10 dovoluje programové vybavení.
- ČÚS 002 popisuje postup přes 701, 702, 710; odchylka podle § 36 odst. 1 je možná, pokud zůstane věrný a poctivý obraz. Úplné aktuální znění ČÚS 002 nebylo přečteno (stránka MF nedostupná), jen změna MF-123342/2013/28.
- Varianta B neprošla: Odoo nemá uzávěrkové období, uzavírací zápisy k 31. 12. by vynulovaly rozvahu k tomu dni a převod 710 na 431 by výsledek započetl dvakrát.

Před první uzávěrkou: popsat postup ve vnitřní směrnici a ověřit s auditorem, archivovat předvahu, rozdělení výsledku z 431 účtovat ručně, po schválení nastavit nevratný zámek období a v SQL předvaze přičíst k 431 výsledek minulých let.

## Co se tím neřeší

- Výkazy podle vyhlášky 500 v Community chybí a souvisí s rozhodnutím o edici.
- Režim DPH a účty 343xxx čekají na potvrzení registrace.
- Jednotná osnova fondů je zvlášť (`docs/osnova-fondu.md`), rámec vyhlášky 501.
