# Otevřené body a rizika

Stav k 2026-11-10. Zdroj pravdy je Claude Doc (sekce Otevřené body a rizika); tento soubor drží stejný seznam
a navíc podrobné body z implementace.
Uzavřený bod přesunout do `docs/rozhodnuti.md`.

## Rozhodnutí, která chybí

| Bod | Proč na tom záleží | Doporučení |
|---|---|---|
| Community, nebo Enterprise | Chybí finanční výkazy, bankovní párování a oběh dokladů | Rozhodnout nejpozději po zkušebních knihách (etapa zkušebních knih), před ostrým startem Investra Services. Kritéria: finanční výkazy, bankovní párování, oběh dokladů, cena licencí a hostingu, kompatibilita vlastních modulů |
| Údaje o investorech ve výpisech fondů (revize R17) | Výpisy fondů obsahují u úpisů a odkupů jména a účty investorů; pseudonymní ID z IS je stále osobní údaj. Import výpisu by porušil pravidlo, že Odoo nedrží data o investorech | Rozhodnout před vývojem banky fondu, do 4. 12. 2026. Návrh revize: podle parametru fondu sběrný účet se souhrnnou platbou, nebo import bez jména a účtu protistrany; vědomé připuštění údajů jen po posouzení pověřencem |
| Nezávislý výpočet NAV (revize R12) | Referenční výpočet i kód má stejný autor; systematická chyba projde obojím | Určit osobu mimo autora kódu, scénáře dodat do 8. 1. 2027 |
| Zpracování dat Googlem u Antigravity | Kód a dokumentace projektu odcházejí ke Googlu; nejasný trénink na datech, umístění dat a typ účtu | Ověří Martin nebo IT: podmínky služby, vypnutí sběru dat v Nastavení, osobní, nebo firemní účet. Rezidenci dat dokumentace uvádí jen u firemního nasazení; samostatné Antigravity IDE se pro firemní nasazení nepodporuje |
| Izolace Antigravity úrovně 2 | Na úrovni 1 (stejný uživatel macOS) chrání `.env`, zálohy, `duverne/` a větve `main` jen pravidla a schvalování příkazů; klíčenka s přístupem ke GitHubu je sdílená | Před ostrými daty: samostatný uživatel macOS bez přístupu do `/Users/martin`, vlastní token jen pro větve `ag/*`, ochrana větví na GitHubu (u soukromého repozitáře ověřit, zda je potřeba GitHub Pro) |
| Testy Odoo pro Antigravity | Antigravity nesmí Docker ani databáze, testy Odoo proto spouští Claude při převzetí | Zavést CI na GitHubu (krok A11 revize), testy pak poběží v cloudu bez hesel |
| Hosting | Určuje provoz, zálohy, obnovu a dodavatelskou smlouvu | Rozhodnout před ostrým startem; posoudit proti závazkům v žádosti o povolení a DORA |
| Soulad s žádostí o povolení | Technický popis v žádosti se musí shodovat se skutečným provozem účetnictví a IT | Porovnat žádost s architekturou a s právníkem nebo compliance určit, zda a jak změnu oznámit ČNB |
| Termín startu a převzetí fondů | Cíl je konec Q1 2027; vývoj fondových modulů musí stihnout první fondy, jinak je potřeba přechodné řešení | Sestavit harmonogram zpětně od cíle, připravit záložní postup |
| Dopad DORA | Rozsah pro investiční společnost, role Investra Services a dodavatelů, včetně AI | Určit rozsah a doplnit evidenci dodavatelů |
| Hesla a MFA | Délka hesla závisí na vícefaktorovém ověření; vynutit MFA | Řešit při návrhu produkce; požadavek ověřit v aktuálním NIST SP 800-63B |
| Lhůty uchování podle ZISIF | Zvláštní lhůty pro obhospodařovatele a administrátora nejsou ověřené | Ověřit v aktuálním znění a doplnit do Pravidel archivace |
| Postup ocenění | Typovaná pravidla poplatků, pořadí modulů | Rozhodnout; doporučení je v Doc (Postup ocenění v Odoo) |
| Transakční výkazy a oznámení | Katalog pokrývá jen rámec Fondy; hlášení obchodů mají krátkou lhůtu a vlastní data | Ověřit povinnost Investry, pak rozhodnout o rozsahu a doplnit katalog |
| TISIFI10 u nových smluv | Zda je bez vypořádání přeceněním celá změna RH; mění výsledek v měsíci sjednání | Počítat celou změnu; potvrdit s ČNB před implementací |
| Výkazy speciálních fondů | Speciální fondy mohou podávat jiné výkazy než FKI, například ROFOS11 a DOFOS70 | Ověřit v plánu výskytů SDAT a doplnit tabulku výkazů |
| Příplatek mimo základní kapitál | Zda se počítá do CET1 a na který řádek DOFOS60 patří; ovlivňuje vykázaný kapitál | Potvrdit s auditorem nebo ČNB |
| Podrobnosti dividend | Účet pro výplatu, dopad na kurz k rozhodnému dni | Upřesnit |
| Zdroje cen | Jaká aktiva fondy drží, frekvence posudků | Upřesnit |
| Možnosti IS | Závěrka, identifikátory, příjem číselníku a kurzu, dividendy, API | Získat dokumentaci |
| Aktualizace předpisů | Funkční měna EUR, schvalování, střediska SICAV v předpisu 12 | Projít později, nyní neměnit |
| Start Investra Services | Současné účetnictví, termín přechodu, plátcovství DPH, hosting, formát importu mezd | Upřesnit |
| Zdrojové systémy fondů | Které systémy, zda mají údaje po pozicích a pořizovací kurzy | Upřesnit u prvních fondů |
| Podrozvaha v Odoo | Podpora ve standardním Odoo neověřená; deriváty a opce jsou u fondů významné | Ověřit v prototypu |
| Naběhlá hodnota ve fondu | Fond je převážně v reálné hodnotě; EIR nebo lineárně se hodí hlavně pro krátké termínované vklady a úvěry s variabilní sazbou. Ověřit soulad s § 196 ZISIF | Potvrdit s auditorem před napojením účtování; u variabilní sazby přepočet EIR při změně sazby |
| Sloupec „Ocenění reálnou hodnotou“ v DOFOS31 | Listy DOFO31_11, _12 (sloupec 10), _21 (4) a _22 (7), ukazatel EFO0244; popis ukazatele v SDAT je prázdný. Může záviset na klasifikaci nebo způsobu ocenění pozice | Zjistit význam (dotaz na ČNB nebo nová metodika) před naprogramováním výkazu DOFOS31; hodnotu brát z ocenění pozice a zařazení, ne z nástroje |
| Primární ověření novely IFRS 9 (EU) 2025/1047 | Převzetí novely klasifikace a oceňování ověřeno jen ze sekundárního zdroje (OIC); EUR-Lex z tohoto počítače nevrací text. Dřívější použití novely neověřeno. Systém pro období od 1. 1. 2026 vyžaduje SPPI podle novely | Ověřit text nařízení (EU) 2025/1047 na EUR-Lex (uživatel); případně upravit pravidlo znění SPPI |
| Potvrzení SPPI u migrovaných zařazení | Vklad ve fondu Delta má SPPI „Splněn“ převzaté migrací s poznámkou „potvrdit“ | Účetní potvrdí posouzení SPPI (testovací data, zatím jen `investra_test`) |
| Účtování FVOCI | Změna RH pozice FVOCI se dnes účtuje do výsledku; kapitálový fond (OCI), recyklace u dluhu a úrok efektivní mírou nejsou naprogramované. Změna RH nevypořádaného obchodu FVOCI ocenění zastaví | Samostatný plán (červená zóna); do té doby rozhodnout, zda ocenění s pozicí FVOCI zastavit nebo upozornit (odloženo uživatelem 2026-11-11) |
| Oceňování derivátů | Návrh v `docs/navrh-oceneni-derivatu.md`; Přílohy 1 a 2 Pravidel oceňování vyžadují aktualizaci referenčních sazeb, chybí metodiky pro některé nástroje | Rozhodnout rozsah podle pozic prvního fondu; změnu předpisu navrhne oddělení oceňování |
| Napojení na SDAT | Návrh v `docs/navrh-sdat.md`; termíny poskytuje `ctiVykazovaciPovinnost`. Otevřené: varianta podpisu, soulad pečeti s § 10 vyhlášky 267/2020 Sb., přístupy do testu | Začít variantou se souborem a čtením přes služby |
| Evidence aktiv uvnitř SPV | Zda vést i aktiva dceřiných společností, nebo jen účast a úvěr | Upřesnit |
| Automatické testy (CI) | Testy modulů se zatím spouštějí ručně | Po prvním funkčním modulu nastavit GitHub Actions s instalací modulu a testy |
| Převodová tabulka ČNB | Převod rolí na řádky výkazů je pracovní návrh (`docs/cnb/prevodova-tabulka.md`) | Potvrdit až při testu výkazů ČNB (rozhodnutí 2026-11-07) |
| Zrušená část třetí vyhlášky 244/2013 Sb. | Možný dopad na Pravidla oceňování u pohledávek po splatnosti a v insolvenci | Zatím neprověřovat (rozhodnutí 2026-11-07); vrátit se při aktualizaci předpisů |
| Pole výkazů ČNB | Katalog výkazů, položek, kontrol a číselníků je v `docs/cnb/` (metodika FOFI20261201) | Doplnit ukazatele u položek bez kontroly a převodníky z Knihovny SDAT; ověřit termíny RISIFI37 a ROFOS13 |
| DPH identifikované osoby | Zaúčtování daně u přijaté služby z EU (platí i pro dodavatele ze třetích zemí, např. USA; daň „ze třetí země“ pro řádky 12 a 13 je přidaná v modulu od 2026-11-08) (daň do nákladu a závazek, bez odpočtu), řádky přiznání a štítky; den účinnosti a DIČ | Potvrdit s metodikem nebo daňovým poradcem; pokyny k přiznání a kontrolnímu hlášení ověřit (§ 6h, § 108, § 72 přečteny); EPO podání Community nemá |
| iÚčto pro Investra Services | Odloženo 2026-11-08, řeší se mimo projekt; porovnání v `docs/pruzkum/07-iucto-services.md` | Pokračuje se v Odoo; vrátit se, pokud vedení hybrid potvrdí |
| Sdílené nástroje bez pravidla společnosti | Příprava jednoho fondu může změnit peněžní toky nástroje drženého jiným fondem | Rozhodnout, zda nástroje sdílet, nebo omezit podle knihy |
| Návrhy obchodů v pozicích | Nezaúčtovaný návrh obchodu zvyšuje pozici fondu | Rozhodnout, zda se mají počítat jen zaúčtované obchody |
| Oddělení uživatelů podle fondů | Určuje váhu izolace knih | Rozhodnout, kdo má přístup do kterých knih |
| Zámek splátky po zaúčtování | Částku splátky a `event_id` jde po zaúčtování změnit; dvojí zaúčtování zastaví klíč události | Zamknout stejně jako pohyb |
| Správa knihy a poplatků | Modely pravidel úplat, tříd a kalendáře mohou mít stejný přesun mezi knihami pro skupinu správce účetnictví | Prověřit a rozšířit ochranu záznamu |
| Excel balíčku pro depozitáře | Text začínající `=` se zapíše jako vzorec | Vypnout `strings_to_formulas` |
| Rozpad ostatních položek třídy | Přemostění tříd (schváleno 2026-11-10) ukazuje ostatní položky třídy jedním číslem; měnové zajištění, dohady a položky specifické pro třídu nejsou rozepsané | Rozhodnout teď, nebo až podle prvního fondu, který takové položky bude mít (rozpad podle rolí účtů) |
| Ochrana kurzů v `investra_dev` | Ochrana kurzů je hotová (2026-11-10), ale v `investra_dev` začne platit až po aktualizaci modulu `investra_rates`; stahování kurzů tam už běží | Aktualizovat modul se souhlasem uživatele |
| Body podkladu UX bez plánu | Poznámky uživatele z 2026-11-10 (podklad mimo repozitář, shrnutí v `docs/predavka-2026-11-10-ux.md`): 3 přehled fondů jako tabulka a snímek; 5.3 výpočetní protokol; 8 zdroj, zaokrouhlení, poplatek a historie u úpisů a odkupů; 9 klasifikace IFRS 9 na obchodu; 14 termínované vklady; 15 detail účetních událostí; 16 pravidla úplat proti sešitům (bod 10 hotový 2026-11-11) | Plán ke každému bodu zvlášť (oranžová a červená zóna). Doporučené pořadí: 9, 15, 8, 14, 16, 5.3, 3 |
| Maximální stáří ceny pro typy nástrojů | Pole je hotové (2026-11-11), ale všude je 0: ocenění upozorní na každou cenu starší než datum ocenění | Uživatel nastaví výchozí počet dní u typů nástrojů podle Pravidel oceňování |

## Chybějící podklady

- [ ] Dokumentace a API IS.
- [ ] Kdo a kdy zajistí úpravy IS.
- [ ] Oceňovací dokumentace, včetně „Výpočtu bonusů pro fondy s delší periodou“.
- [ ] Zbývající ukazatele u položek a převodníky ČNB z Knihovny SDAT (ostatní je v `docs/cnb/`).
- [ ] Ukázky nastavení tříd a alokací od zakladatelů.
- [ ] Naběhlý úrok a klasifikace podle IFRS 9.

## Rizika

| Riziko | Dopad | Opatření |
|---|---|---|
| Vzorce pokrývají jen zjednodušenou variantu | Nepočítá s převodem hodnoty mezi třídami | Ověřit na ukázkách od zakladatelů |
| Vstup nových investorů za starší kurz | Zvýhodnění nebo poškození stávajících investorů | Nastavení podle statutu, přehled ručních úprav |
| Fondové moduly vyvíjené svépomocí | Trvalá práce na migracích a testech při nových verzích Odoo | Testy, minimum zásahů do core |
| Odoo jako NAV systém | Může se ukázat méně vhodné než specializovaný systém | Ověřit prototypem před produkcí |
| Velký počet společností | Pomalejší práce v UI, složitější souhrnné přehledy | Vlastní přehledy, ověřit v etapě zkušebních knih |
| Celé účetnictví v Odoo od začátku | Větší rozsah: oběh dokladů, výkazy, předpisy, DORA | Postup po fázích, start na Investra Services |
| Chybějící údaje při převzetí fondu | Bez pořizovacího kurzu nebo údajů po pozicích nejde oddělit FX a FV | Účetní postup pro stanovení hodnot ke dni přechodu |
| Testy přecenění v `investra_test` | Od 2026-11-11 10:45 padá příprava `TestFxRun` (AccountTestInvoicingCommon, MissingError u kopie daňového účtu), i s kódem před změnou Platnosti kurzů; v kopii ze zálohy `investra_test_kontrola` vše prochází | Zjistit, co se v `investra_test` změnilo (porovnat s kopií), nebo `investra_test` nahradit kopií se souhlasem uživatele |
| Platnost kurzů v `investra_dev` | Tabulka Platnost kurzů a odstranění stáří z fondu a profilu (2026-11-11) začnou v `investra_dev` platit až po aktualizaci `investra_rates`, `investra_nav`, `investra_fx_revaluation` | Aktualizovat se souhlasem uživatele (spolu s bodem Ochrana kurzů v `investra_dev`) |
