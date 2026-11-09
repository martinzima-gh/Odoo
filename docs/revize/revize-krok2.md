# Revize projektu Investra na Odoo 20 – krok 2: revize a doporučení

Zpracováno 8. 11. 2026 podle souborů `podklad-pro-revizi.md`, `zadani-pro-ai.md` a `odpovedi-krok1.md`.
Kód ani repozitář jsem neviděl. Dokument je důvěrný.
Doplněno o odpovědi metodika z 8. 11. 2026: kurzy ECB a ČNB, klasifikace podle IFRS 9 a otevřené otázky z kapitoly 6; zohledněn návrh obrazovky NAV od vedoucího.
Úvaha o variantě iÚčto je vedle v souboru `uvaha-iucto.md`, hlavní směr je Odoo.

**Značky původu tvrzení:**
- **(P)** fakt z podkladu nebo z odpovědí,
- **(Z)** moje odborná znalost (Odoo do verze 18/19, účetnictví fondů, IFRS),
- **(D)** domněnka nebo odhad,
- **„ověřit v Odoo 20“** / **„ověřit v předpisu“** – nejsem si jistý, že funkce nebo pravidlo v této podobě platí.

Odhady pracnosti jsou v člověkodnech (MD) práce vlastníka s AI agentem a jsou vždy (D).

Zkratky rolí: **ÚS** účetní Services, **ÚF** účetní fondu, **SCH** schvalovatel, **VED** vedoucí.
Zkratky rozhodnutí (R1…R17) odkazují na kapitolu 4, kroky (A01…) na akční plán v kapitole 5.

---

## 1. Shrnutí pro vedení

**Hlavní závěry**

1. **Architektura je správná a pro desítky fondů obhájitelná.** Kniha = společnost Odoo, pravidla nad rolemi účtů,
   zápisy jen z událostí, investoři v IS. Slabá místa nejsou v návrhu, ale kolem něj:
   - žádná produkce ani ověřená obnova,
   - jediný vývojář,
   - referenční výpočet NAV od stejného autora jako kód,
   - obrazovky, které neprošel uživatel,
   - dva souběžně vyvíjené prototypy výpočtu NAV (R18).
2. **Jádru chybí peněžní toky nástrojů.** Kupóny, dividendy, poplatky, splátky, úroky SPV, upisovací závazky a dohady.
   Spolu s převzetím, bankou, rozhraním IS a pěti výkazy ČNB tvoří kritickou cestu. Před dalším vývojem je potřeba
   vyřešit dvě architektonické věci:
   - **osobní údaje investorů v bankovních výpisech fondů:** jména a účty u úpisů a odkupů jsou v rozporu s pravidlem
     „Odoo nedrží data o investorech“. Cesta úpisů se liší podle fondu a výplaty zadává IS, takže řešení bude
     parametrem fondu (rozhodnutí R17),
   - **klasifikaci IFRS 9 podle fondu:** metodik potvrdil, že jeden nástroj může mít v různých fondech různou
     klasifikaci a že reklasifikace může nastat. V prototypu je klasifikace pravděpodobně na sdíleném nástroji (A22).
3. **Harmonogram v plném rozsahu nevyjde (D).**
   - Jádro odhaduji na 100 až 170 MD. Do 26. 3. 2027 zbývá 95 pracovních dní a vývoj běží na částečný úvazek.
   - Dvě řádná měsíční ocenění se do zkušebního provozu 1.–26. 3. nevejdou. Paralelní běh proto použije historická
     ocenění k 31. 1. a 28. 2. 2027; data dodá předchozí administrátor do konce února.
   - 26. 3. 2027 je Velký pátek, tedy státní svátek.
   - První roční uzávěrka Services musí být hotová v březnu (daňové přiznání v běžné lhůtě), tedy souběžně se
     zkušebním provozem.

   **Reálné je:** Services naostro od 4. 1. 2027, uzávěrka Services 2026 do konce února, jádro ověřené na syntetickém
   fondu do konce února a v březnu paralelní běh s prvním fondem na oceněních k 31. 1. a 28. 2.
4. **Enterprise ušetří víc práce, než stojí.** V Community by Services potřebovala 35 až 75 MD vlastního vývoje
   (výkazy, banka, DPH, časové rozlišení). Moduly OCA pro nové Odoo 20 pravděpodobně nebudou včas (D, ověřit).
   Licence pro 5 až 8 uživatelů vychází podle ceníku v podkladu na 1 400 až 2 700 € ročně (cenu plánu Custom ověřit).
5. **Hlavní uživatelský problém je přepínání společností a dvě aplikace.** Řeší ho:
   - přehledy napříč knihami podle oprávnění, ne podle přepínače společností,
   - jedna aplikace „Investra“,
   - průvodce oceněním,
   - fronta ke schválení se zastupováním.

   Vše jde postavit standardními zobrazeními Odoo bez vlastního JavaScriptu.

**Pět nejdůležitějších doporučení**

| # | Doporučení | Termín |
|---|---|---|
| 1 | Rozhodnout **Enterprise (plán Custom) na spravovaném hostingu v EU** se zálohami databáze i příloh a testem obnovy | 20. 11. 2026 |
| 2 | **Services naostro v čisté produkční databázi.** Nastavení z modulů, 9 dokladů znovu zadat s opravami, `investra_dev` zůstane vývojová | zkušební měsíc do 18. 12. 2026, ostrý start 4. 1. 2027 |
| 3 | **Jádro dokončit podle kritické cesty:** rozhodnout osobní údaje v bance a přesunout klasifikaci IFRS 9 na úroveň fondu → peněžní toky nástrojů → převzetí → banka → IS přes soubory → balíček pro depozitáře → 5 výkazů ČNB se záložní šablonou | brány 22. 1. a 26. 2. 2027 |
| 4 | **Nezávislá kontrola hned:** druhá osoba sestaví nezávislý výpočet NAV, testy poběží automaticky (CI), účetní testují obrazovky od prosince | scénáře 8. 1. 2027, brána 22. 1. 2027 |
| 5 | **Ostrý provoz definovat bránou, ne datem:** dvě po sobě souhlasná paralelní ocenění, zkušební výkazy bez ruční úpravy, test obnovy. Rozsah zmrazit 22. 1. | 22. 1. 2027 |

**Co nedělat**
- Nepouštět Services naostro z databáze `investra_dev` označené TEST ani z notebooku.
- Nepsat vlastní bankovní párování, výkazy a vytěžování PDF, pokud se koupí Enterprise.
- Nestavět IS v Odoo ani API k IS dřív, než funguje souborové rozhraní se stejnými zprávami.
- Neimportovat bankovní výpisy fondů, dokud není rozhodnuto, jak se z nich vyloučí údaje o investorech.
- Nedělat deriváty a repo před peněžními toky jádra. Architektura s nimi ale musí počítat.
- Nesdílet nástroje a ceny mezi knihami bez pravidel a nepoužívat pobočky (branches) pro fondy.
- Nespoléhat na referenční výpočet od stejného autora jako na jediný důkaz správnosti NAV.
- Nedávat AI do schvalovací ani účtovací cesty.
- Nevyvíjet souběžně dva výpočty NAV (R18).

---

## 2. Posouzení

### 2.1 Architektura

**Kniha = samostatná společnost Odoo (P)**

*Silné stránky (Z):*
- každý fond má vlastní měnu, osnovu, deníky, číslování a zámky období, což odpovídá samostatnému účetnictví fondu a podfondu,
- jde použít funkční měnu EUR,
- obnovu nebo audit jedné knihy lze vymezit,
- přístup oddělí pravidla podle společnosti (v Odoo 20 sloučená do `ir.access`, P).

*Rizika:*
1. **Nastavení se rozchází mezi knihami (D, vysoké).** Daně, deníky, číselné řady, fiskální pozice a mapování rolí má
   každá kniha zvlášť. U desítek knih se ručně udržované nastavení rozejde.
   → **Šablona knihy** (verzovaný popis nastavení), **průvodce založením knihy** a **přehled odchylek** knihy od šablony.
2. **Souhrnné přehledy (P).** Standardní seznamy ukazují jen záznamy aktivních společností (Z).
   → Přehledy napříč fondy musí číst data všech knih, ke kterým má uživatel *oprávnění*, bez ohledu na zaškrtnutí
   v přepínači (obrazovka O3).
3. **Sdílené záznamy (P, otevřený nález „sdílené nástroje bez omezení na knihu“).**
   - Sdílení je užitečné: jeden ISIN, jedna cena z Bloombergu.
   - → Oddělit **sdílený kmen** (ISIN, typ, emitent, tržní cena z veřejného zdroje) od **dat knihy** (pozice,
     klasifikace podle IFRS 9, cena ze znaleckého posudku nebo modelu).
   - Klasifikace IFRS 9 patří ke vztahu fond–nástroj: jeden nástroj může mít v různých fondech různou klasifikaci
     (P, potvrdil metodik 8. 11. 2026).
   - Klasifikace potřebuje platnost od, protože reklasifikace při změně obchodního modelu může nastat (P), i když vzácně.
   - Podle nálezu předpokládám, že dnes je klasifikace na sdíleném nástroji (D). Přesun na úroveň fondu je krok A22.
4. **Obnova jedné knihy (P).** Ze zálohy celé databáze nejde obnovit jen jeden fond.
   → **Export knihy** čitelný bez Odoo (A55) a obnova celé databáze do vedlejší instance, ze které se data dohledají.
   Neslibovat obnovu jednoho fondu v produkční databázi.

*Alternativy:*

| Varianta | Kdy dává smysl | Hodnocení |
|---|---|---|
| Jedna databáze, kniha = společnost (dnes) | desítky knih, malý tým | **ponechat** |
| Databáze na fond | stovky fondů nebo požadavek tvrdé izolace od zakladatele | správa N databází, N upgradů, přehled napříč fondy jen přes datový sklad; zatím ne |
| Pobočky | nikdy pro fondy | dědí měnu a kurzy (P) |

**Investiční společnost** bude další knihou ve stejném systému (P). Se šablonou knihy jde jen o osnovu podle vyhlášky 501
a výkazy obhospodařovatele (A69). Termín se řídí povolením ČNB a nesmí blokovat první fond v režimu outsourcingu.

**Role účtů (P)** – *silné*, pravidla přežijí různé osnovy převzatých fondů.
- *Riziko:* neúplné mapování. → Kontrola „každý účet se zůstatkem nebo obratem má roli“ jako stop v ocenění a v převzetí.
- Role a převody na výkazy verzovat s platností od, protože se metodiky ČNB od 2027 mění (P).

**Jediný účtovací modul (P)** – *silný pro audit*. Otevřené jsou dvě věci:
1. **Standardní doklady ve fondových knihách.** Fondy mají přijaté faktury (audit, depozitář, znalec) a bankovní pohyby.
   - *Varianta A (doporučuji):* standardní přijaté faktury a banka jsou v knize fondu povolené, ale jen s účty, které mají
     roli, a vlastní modul je při potvrzení zaregistruje jako událost. Ocenění, přecenění, úplaty a obchody vznikají jen
     z událostí.
   - *Varianta B:* všechno přes události, tedy znovu napsat přijaté faktury a banku (desítky MD).
   - Rozhodnutí R7.
2. **Ruční úpravy.** → Událost „ruční úprava“ s povinným důvodem, přílohou a schválením druhou osobou (P: čtyři oči
   u ručních úprav).

**Rozdělení Odoo a IS (P)** – *správné*. Odoo je zdrojem kurzu, IS zdrojem kusů a pokynů.
- **IS zatím neexistuje (P).** → Nejdřív soubory s verzovaným schématem a **simulátor IS**, API až se stejnými zprávami
  (P, souhlasím). Navázání závěrek, idempotence a storna patří do jádra.
- **Osobní údaje v bankovních výpisech (nové zjištění, Z).**
  - Výpisy z účtů fondů obsahují u úpisů a odkupů jméno a číslo účtu investora.
  - Pseudonymní identifikátor ze zpráv IS je podle GDPR stále osobní údaj, protože IS umí investora dohledat.
  - Pravidlo „Odoo nedrží data o investorech“ (P) proto padne s prvním importem výpisu fondu, pokud to návrh nevyřeší.
  - Cesta úpisů se liší podle fondu (P): někde na účet fondu u depozitáře, jinde na sběrný účet.
  - → Rozhodnutí R17 před vývojem banky fondu, řešení jako parametr fondu. U účtu fondu se při importu nepřebírá
    jméno a účet protistrany a páruje se přes identifikátor z IS. U sběrného účtu přijde do Odoo jen souhrnná platba
    za třídu. Vědomé připuštění minimálních údajů jen s posouzením pověřence pro ochranu osobních údajů.
  - Výplaty odkupů a dividend investorům zadává IS (P). Odoo je jen spáruje a potvrdí.
- **Performance fee jen po třídě fondu (P, rozhodl metodik 8. 11. 2026).** High-water mark a hurdle se počítají za třídu.
  Série a vyrovnání (equalisation) nejsou v rozsahu. Kdyby je převzatý fond potřeboval, série jdou přidat jako třídy
  a vyrovnání po investorech patří do IS, protože Odoo nemá data o investorech (Z). Zápis rozhodnutí je krok A56.

**Dva režimy provozu (P, nerozhodnuto)**

| | Režim A: Services účtuje pro cizího obhospodařovatele | Režim B: vlastní investiční společnost |
|---|---|---|
| Kdo odpovídá za NAV a výkazy (Z, ověří právník) | obhospodařovatel nebo administrátor s licencí; Services je dodavatel | investiční společnost |
| Kdo schvaluje ocenění | ÚF a SCH Services v Odoo; obhospodařovatel písemně mimo Odoo, schválení se přiloží k ocenění (P) | ÚF + SCH investiční společnosti |
| Oprávnění v Odoo | uživatelé Services jen ke knihám fondů daného obhospodařovatele; obhospodařovatel účet v Odoo nepotřebuje | navíc kniha investiční společnosti |
| Kdo podepisuje a odesílá výkazy ČNB | obhospodařovatel (Odoo připraví soubor) | investiční společnost |
| Kniha investiční společnosti v Odoo | ne | ano, vyhláška 501 |

→ **Schvalovací matice a odpovědný subjekt jako parametry fondu s platností od** (R6). Stejný kód pokryje oba režimy
a získání licence znamená nový záznam, ne vývoj. Cizí obhospodařovatel schvaluje písemně mimo Odoo (P, rozhodnuto
8. 11. 2026). Jeho schválení přiloží a zaeviduje schvalovatel Services, ne zadavatel, a bez něj nejde ocenění schválit.
Licence pro obhospodařovatele tak nejsou potřeba.

**Kdo smí co (návrh pro malý tým, rozhodnutí R4, R5, R6)**

| Akce | Zadává | Schvaluje (nikdy zadavatel) | Když schvalovatel chybí |
|---|---|---|---|
| Ceny | ÚF | SCH nebo druhá ÚF | druhá ÚF podle delegace |
| Ocenění | ÚF | SCH; u cizího obhospodařovatele navíc jeho písemné schválení přiložené k ocenění | náhradník podle matice, jinak ocenění počká |
| Ruční úprava, ruční kurz | ÚF | SCH nebo druhá ÚF | jako u cen |
| Změna parametrů fondu (úplaty, alokace, role účtů) | metodik | SCH nebo VED | změna počká |
| Otevření uzamčeného období | metodik | VED | nelze |
| Platby Services | metodik | jednatel (R4) | platba počká nebo dodatečná kontrola podle R4 |
| Zveřejnění kurzu | ÚF po potvrzení depozitářem | už schváleno | druhá ÚF |

Změna parametrů fondu mění NAV stejně jako změna kódu. Proto ji navrhuji verzovat a schvalovat druhou osobou (D).

**Jiná platforma.** Úvaha o variantě „iÚčto pro všechny subjekty a vlastní aplikace pro ocenění“ je vedle v souboru
`uvaha-iucto.md`. Hlavní směr je Odoo (P, 8. 11. 2026) a tato revize s ním počítá.

### 2.2 Využití Odoo: použít, koupit, vyvíjet

**Ze standardu Odoo použít (Community, Z):**
- účetní doklady, deníky, číselné řady, zámky období, párování, kurzy s vlastním doplněním ČNB a ECB (P),
- multi-company s přístupovými pravidly,
- chatter a historii změn pro auditní stopu, aktivity pro úkoly a připomínky,
- e-mailový alias deníku pro přijaté faktury (vytvoří koncept s PDF, ověřit v Odoo 20),
- dvoufázové ověření TOTP včetně vynucení (ověřit v Odoo 20),
- zobrazení seznam, formulář, kanban, pivot, graf, kalendář a průvodce,
- export do XLSX.

**Enterprise vs. Community: co by se jinak vyvíjelo**

| Funkce | Community | Enterprise (Z, ověřit v Odoo 20) | Odhad vlastního vývoje v Community (D) |
|---|---|---|---|
| Předvaha, hlavní kniha, saldokonto | chybí (P); OCA `account_financial_report`, port pro 20 nejistý | finanční výkazy | 8–15 MD, nebo port OCA 3–6 MD |
| Rozvaha a výsledovka (vyhláška 500, 501) | chybí; OCA `mis_builder` (port?) | výkazy definované v datech bez Pythonu; české šablony podle vyhlášky 500 ověřit v lokalizaci | 10–20 MD |
| Zobrazení přiznání DPH | chybí (P) | ano; pro identifikovanou osobu nutná úprava definice (P) | 3–8 MD |
| Import výpisů a párování | chybí (P); OCA `account_statement_import_*`, `account_reconcile_oca` (port?) | import CAMT a dalších formátů, párovací rozhraní, synchronizace bank (pokrytí českých bank ověřit) | 12–25 MD |
| Časové rozlišení | ruční (P); OCA `account_spread_cost_revenue` (port?) | automatické | 3–5 MD |
| Vytěžování PDF faktur | chybí (P) | ano, přes službu Odoo (IAP) za kredity; dokumenty jdou na servery Odoo | 5–10 MD (vlastní vytěžování s potvrzením člověkem) |
| Schvalování, Dokumenty, editovatelné tabulky | ne | ano | pro fondy je stejně nutné vlastní schvalování; Enterprise tu zásadně nepomůže |
| Upgrade vlastních modulů | vlastními silami | upgradovací služba řeší standardní data; vlastní moduly zůstávají na vás (ověřit v podmínkách Odoo) | – |

- **Součet v Community: zhruba 35 až 75 MD bez vytěžování PDF, s ním 40 až 85 MD (D).** Při částečném úvazku jednoho
  vývojáře to jsou měsíce.
- **Licence Enterprise:** pro 5 až 8 uživatelů vychází 22,90–27,90 € × 12 × 5–8 ≈ **1 400 až 2 700 € ročně** podle
  ceníku v podkladu. Cenu plánu Custom a podmínky provozu na vlastním hostingu ověřit u Odoo nebo partnera.

**I s Enterprise zůstane vlastní práce (D):**
- rozvaha a výsledovka podle vyhlášky 500, pokud nejsou v lokalizaci (2–5 MD), a podle vyhlášky 501 pro fondy (v obou edicích),
- úprava přiznání DPH pro identifikovanou osobu (modul už existuje),
- formát GPC (ABO) pro české banky pravděpodobně chybí (ověřit). Řešit vlastním profilem importu, nebo u bank
  zvolit CAMT.053 či OFX, pokud je nabízejí (ověřit u bank).

**Vyvíjet vždy, v obou edicích (P, Z):**
- fondy, třídy, nástroje, ocenění, úplaty, alokace, IFRS 9,
- výkazy ČNB, rozhraní IS, převzetí, balíček pro depozitáře,
- DPH identifikované osoby, schvalovací matice, přehledy napříč knihami.

**Další doporučení:**
- **OCA:** do 20. 11. ověřit stav portu každého potřebného modulu (větev `20.0` na GitHubu OCA). Moduly bez portu
  počítat jako vlastní vývoj, ne jako „zdarma“ (D).
- **Česká lokalizace:** externí partner dává smysl jen pro ohraničenou zakázku na DPH a bankovní formáty, s převzetím
  kódu do vašeho repozitáře a s testy. Odoo Mates (P) jen jako inspirace.

### 2.3 Mezery k prvnímu fondu a k účetnictví Services

Seřazeno podle dopadu na termín. **J** = univerzální jádro, **R** = rozšíření s připravenou architekturou.

**Investra Services (brána 18. 12. 2026)**

| # | Mezera | Dopad | Poznámka |
|---|---|---|---|
| S1 | Produkční prostředí, zálohy včetně příloh, obnova, MFA | blokuje | dnes notebook a databáze TEST se skutečnými doklady (P) |
| S2 | Rozhodnutí o edici | blokuje S4, S5, S8 | 20. 11. |
| S3 | Opravy dokladů: číslování vydaných faktur, soukromý výdaj statutára, cizí náklady skupiny | blokuje uzávěrku | soukromý výdaj patří na závazek vůči osobě, která platila (Z); cizí náklady přefakturovat nebo přeúčtovat; postup schválí metodik, sporné body auditor |
| S4 | Předvaha, hlavní kniha, rozvaha a výsledovka podle vyhlášky 500 v nabídce | blokuje | dnes SQL (P) |
| S5 | Import výpisů a párování se schválením | vysoký | jednotky až desítky pohybů (P); provozní banka Services bude Fio (P); základ se použije i pro fondy |
| S6 | DPH identifikované osoby: potvrzení poradcem, zpětná kontrola od 19. 3. 2026, přiznání bez odpočtu, automatický návrh daně | vysoký | daňové riziko |
| S7 | Roční uzávěrka 2026 (první účetní období od 19. 3. 2026) a podklady pro daňové přiznání v běžné lhůtě (P) | vysoký pro kapacitu | musí být hotová v březnu; doporučuji do 26. 2. 2027, před zkušebním provozem fondu |
| S8 | Hlídání obratu pro povinnou registraci k DPH | střední | jestli se do obratu počítají služby fondům a zda jsou osvobozené, ověří daňový poradce (ověřit v předpisu) |
| S9 | Časové rozlišení | střední | ručně jde |
| S10 | Vytěžování PDF | nízký pro termín, vysoký pro pohodlí | R10 |

**Fondy (brány 22. 1. a 26. 2. 2027)**

| # | Mezera | J/R | Dopad |
|---|---|---|---|
| F1 | Nezávislé ověření NAV jinou osobou než autorem | J | blokuje akceptaci prototypu (C.1 bod 1) |
| F2 | Rozhodnutí R17 (osobní údaje v bance a IS) a klasifikace IFRS 9 na úrovni fondu s oddělením sdílených dat (A22) | J | blokuje banku fondu a peněžní toky nástrojů |
| F3 | Peněžní toky nástrojů: kupón, dividenda (nárok k rozhodnému dni, výplata, srážková daň), poplatek obchodu, splátka a umoření, úrok úvěru SPV, příplatek mimo základní kapitál | J | blokuje každý reálný fond |
| F4 | Dohadné položky, úplaty k úhradě a daň z příjmů fondu (splatná, případně odložená; sazbu a postup potvrdí poradce) | J | blokuje NAV |
| F5 | Ostatní podíl s upisovacím závazkem (výzvy ke splacení, distribuce, podrozvahový závazek) | J | typické u FKI (P) |
| F6 | Funkční měna EUR celým cyklem | J | parametr (P); v účetnictví kurzy ECB, výkazy ČNB vždy v CZK s přepočtem z EUR kurzem ČNB (P, potvrdil metodik podle legislativy) |
| F7 | Univerzální import cen (Bloomberg přes Excel, profily formátů, příloha zdroje, hromadné schválení) | J | každé ocenění |
| F8 | Převzetí: vstupní formát, převodník, kontroly, pravidla pro chybějící údaje | J | blokuje první fond |
| F9 | Banka fondu: import a párování úpisů a odkupů; cesta úpisů je parametr fondu a výplaty zadává IS (P, R17) | J | kontrola v kroku 6 (P) |
| F10 | Rozhraní IS přes soubory (9 zpráv) a simulátor | J | podmínka převzetí (P) |
| F11 | Balíček pro depozitáře strojově čitelný, bez vzorců, s evidencí stanoviska a porovnáním | J | krok 9 (P) |
| F12 | Výkazy ČNB RISIFI30, RISIFI33, TISIFI10, VISIFI10, RISIFI37 včetně přepočtu z EUR do CZK kurzem ČNB a záložní export do šablony | J | brána přechodu (C.1 bod 3) |
| F13 | Schvalovací matice, zastupování, schvalování změn parametrů, uzavření 4 bezpečnostních nálezů | J | čtyři oči (P) |
| F14 | Obrazovky O1, O3, O4 a uživatelský test | J | brána přechodu (C.1 bod 6) |
| F15 | Performance fee jen po třídě fondu (rozhodnuto, P); série a vyrovnání mimo rozsah | R | jen kdyby to vyžadoval statut převzatého fondu |
| F16 | Účetní závěrka fondu (rozvaha a výsledovka podle rámce, příloha ve Wordu) | J | až k první roční závěrce fondu |
| F17 | Test na objemu, export knihy čitelný bez Odoo | J | před ostrým provozem |
| F18 | Repo, deriváty, API k IS, přímé napojení Bloombergu a bank, IFRS 18, kniha investiční společnosti | R | po prvním fondu nebo podle povolení ČNB |

**Varianty pořadí typů nástrojů (odpověď na otázku 1)**

| Varianta | Pořadí | Plus / minus |
|---|---|---|
| **A: podle četnosti u FKI (doporučuji)** | 1. termínovaný vklad a účet (hotové) → 2. účast a úvěr SPV, příplatek → 3. dluhopis, akcie a ETF s kupóny, dividendami a poplatky → 4. ostatní podíl s upisovacím závazkem → 5. repo → 6. deriváty | pokryje většinu FKI se strukturou SPV; deriváty až podle potřeby |
| B: podle společného modelu peněžních toků | vše dluhové naráz (vklad, úvěr, dluhopis, repo) → majetkové → deriváty | technicky elegantní, ale repo přijde dřív, než je potřeba |
| C: podle prvního fondu | jen to, co fond drží | rychlé, ale v rozporu s požadavkem na univerzálnost (P) |

Doporučuji **A** s tím, že úvěr, dluhopis a vklad sdílejí jeden model peněžních toků (P, průzkum „Dluhové nástroje“).
Repo pak bude hlavně konfigurace.

**Převzetí: chybějící údaje (odpověď na otázku 4)**

| Chybí | Návrh pravidla (rozhodne metodik, ověří auditor) |
|---|---|
| Pořizovací kurz pozice v cizí měně | převzít pořizovací cenu v CZK ze zdroje a dopočítat implicitní kurz; když chybí i ta, použít kurz ke dni převzetí s příznakem „převzato bez historie“ |
| High-water mark | podle statutu: NAV na kus ke dni převzetí, nebo historie od předchozího administrátora potvrzená depozitářem; bez potvrzení se performance fee neúčtuje a ocenění skončí stopem |
| Hurdle a historie NAV | import historie kurzů tříd; bez ní se mezitímní výnos počítá ode dne převzetí s příznakem |
| Atributy pro výkazy (sektor, rezidence, LEI) | chybějící atribut je upozornění v převzetí a stop v kontrole ČNB |
| Otevřené položky bez párovacího klíče | jedna položka na partnera a účet s odkazem na zdrojový seznam |

Každá převzatá položka nese **zdroj, datum převzetí a příznak úplnosti**. Audit tak pozná, co pochází od předchozího administrátora.

### 2.4 Uživatelská přívětivost: shrnutí

Dnešní problémy (P):
- přepínání společností,
- dvě aplikace,
- anglické popisky,
- obrazovky neověřené uživatelem.

Principy návrhu:
1. **Jedna aplikace „Investra“** s nabídkou podle práce:
   - *Můj den* (O3 s filtrem „moje fondy“ a O4),
   - *Ocenění*, *Ceny*, *Schvalování*, *Fondy*,
   - *Účetnictví fondů*, *Výkazy ČNB*, *Services*.

   Standardní účetní funkce jsou dostupné ze stejné nabídky.
2. **Obrazovky napříč knihami nezávislé na přepínači.** Při otevření záznamu z jiné knihy se kniha přepne sama
   (ověřit v Odoo 20).
3. **Ocenění jako průvodce.** Každý krok ukáže stav, výsledek kontroly a jedno hlavní tlačítko.
4. **Každé varování nabídne akci:** „otevřít rozdíl“, „spárovat“, „vrátit“.
5. **České popisky a ukázková data jsou podmínkou uživatelského testu**, ne kosmetikou.

Detailní návrhy jsou v kapitole 3.

### 2.5 Efektivita

**Kroky a kliknutí (D, odhad z popisu procesů; změřit v uživatelském testu A25 a A45)**

| Proces | Dnes | Po návrhu | Jak to poznáme |
|---|---|---|---|
| Přijatá faktura Services z PDF | ~30 kliknutí, 4–6 min, opis všech polí | 8–12 kliknutí, 1–2 min (předvyplnění z historie dodavatele nebo vytěžení, daň identifikované osoby automaticky) | čas v uživatelském testu, podíl dokladů bez ruční opravy daně |
| Schválení cen (20 nástrojů) | každá cena zvlášť, ~60 kliknutí | 1 import, 1 hromadné schválení, výjimky jednotlivě: 5–10 kliknutí | počet kliknutí na dávku |
| Měsíční ocenění jednoho fondu | 11 kroků ve dvou aplikacích s přepínáním, 80–120 kliknutí | průvodce: nejvýš 35 kliknutí do odeslání ke schválení, 0 přepnutí společnosti | měření v testu |
| Přehled stavu 20 fondů | 20× přepnout nebo SQL | 1 obrazovka | otevření do 3 s při 30 fondech |
| Výpis banky | ruční zápis | import, návrh párování, potvrzení | podíl navržených párů (cíl stanovit po prvním měsíci) |
| Přiznání DPH identifikované osoby | ruční výběr dokladů | přehled za období s kontrolami a exportem | 0 zahraničních služeb bez daně |

**Co automatizovat:**
- import kurzů (hotovo, P), cen ze souboru, výpisů a závěrek IS,
- termíny ze SDAT (P),
- kontroly v kroku 6, výpočet úplat a dohadů,
- balíček pro depozitáře, data výkazů ČNB,
- připomínky termínů, přehled odchylek nastavení knih.

**Co ponechat ručně kvůli kontrole:**
- schválení cen a ocenění,
- výjimky z kontroly stop,
- ruční úpravy a ruční kurz (vždy čtyři oči),
- hodnoty z posudku a modelu,
- změny mapování rolí, pravidel alokace a parametrů úplat,
- odeslání výkazů ČNB a podkladů depozitáři,
- zveřejnění kurzu, otevření uzamčeného období.

**Výkon a správa při desítkách společností**
- **Výkon (D):** desítky společností a stovky nástrojů jsou pro PostgreSQL malý objem. Riziko jsou počítaná pole bez
  uložení a přehledy, které počítají po záznamech.
  → Přehled napříč fondy plnit z uloženého stavového snímku fondu, který se aktualizuje při změně stavu, ne při
  každém otevření.
- **Test na objemu (A57):** 30 knih × 50 nástrojů × 24 ocenění × 3 třídy plus 2 roky dokladů. Cíl: přehled do 3 s,
  výpočet ocenění fondu do 60 s (cíle potvrdit).
- **Správa:** šablona knihy, průvodce založením a přehled odchylek (A54).

**Údržba při nových verzích Odoo (Z)**
- Odoo vydává hlavní verzi zhruba ročně a podporuje poslední tři. Plánovat upgrade **každé 2 roky** a mezitím jen
  opravná sestavení s během všech testů.
- Dědit standardní modely jen tam, kde je to nutné, a nepřepisovat standardní metody bez volání rodiče.
  Žádný vlastní JavaScript (OWL) tam, kde stačí standardní zobrazení.
- Místa, kde vlastní moduly mění standardní chování (hledání kurzu, kontrola zápisu do cizí knihy, výchozí hodnoty
  z kontextu – P), vést v **registru úprav chování** s testem ke každému (A68). Při upgradu se projde jako první.

### 2.6 Rizika a soulad

Nedávám právní závěry; sloupec „Kdo ověří“ říká, kdo má poslední slovo.

| Riziko | Typ | Popis | Kdo ověří |
|---|---|---|---|
| Uzávěrka bez účtů 701, 702, 710 | účetní | výsledek jen na 431 a zámek místo uzávěrkových zápisů (P); splňuje požadavek na uzavření a otevření účetních knih? | auditor (ověřit v předpisu) |
| Skutečné doklady v databázi TEST, nesoulad číslování vydaných faktur | účetní | průkaznost a návaznost číselné řady | auditor |
| Soukromý výdaj statutára jako závazek vůči dodavateli | účetní | nesprávný věřitel v saldokontu | metodik, auditor |
| Dva zdroje kurzu u fondů v EUR | účetní, regulatorní | v účetnictví kurz ECB, výkazy ČNB jsou vždy v CZK a přepočítávají se z EUR kurzem ČNB (P, potvrdil metodik podle legislativy); hrozí záměna zdroje nebo data kurzu → každý přepočet ve výkazu nese kurz, datum a zdroj | metodik; datum kurzu podle metodiky výkazu |
| Klasifikace IFRS 9 na sdíleném nástroji | účetní | jeden nástroj může mít v různých fondech různou klasifikaci (P, potvrdil metodik); prototyp ji má pravděpodobně na sdíleném nástroji (D) | vývoj (A22), auditor při revizi pravidel |
| Neměnná klasifikace IFRS 9 | účetní | reklasifikace může nastat (P, potvrdil metodik); absolutní zákaz ji znemožní → klasifikace s platností od a řízená událost „reklasifikace“ se schválením (A74) | metodik, auditor |
| IFRS 18 od 2027 u fondů s plnými IFRS | účetní | nové členění výsledovky (P) | auditor (účinnost a přijetí v EU ověřit) |
| Referenční výpočet od stejného autora | účetní, regulatorní | systematická chyba v kódu i v kontrole | nezávislá osoba, depozitář |
| Změna parametrů fondu bez druhé osoby | účetní | parametry mění NAV stejně jako kód | metodik (A40) |
| DPH identifikované osoby | daňové | zpětné přiznání služeb od 19. 3. 2026, hranice povinné registrace, souhrnné a kontrolní hlášení (zda se týkají identifikované osoby) | daňový poradce |
| Osobní údaje investorů v bankovních výpisech fondů a ve zprávách IS | GDPR | jména a účty investorů ve výpisech; pseudonymní ID je stále osobní údaj | pověřenec pro ochranu osobních údajů, právník |
| Outsourcing pro cizího obhospodařovatele | regulatorní | pověření jiného výkonem činnosti, odpovědnost za NAV a výkazy | právník, ČNB (ověřit v předpisu: ZISIF) |
| DORA | regulatorní | rozsah působnosti pro obhospodařovatele i pro Services jako dodavatele ICT služeb, registr ICT dodavatelů, testy obnovy, incidenty, smluvní náležitosti | právník, compliance |
| Licence dat Bloomberg | smluvní | sdílení cen mezi fondy a předávání depozitáři může licence omezovat | vedoucí podle smlouvy |
| Vytěžování PDF službou Odoo | bezpečnost | doklady Services odcházejí ke třetí straně (data investorů ne, ta v Odoo nejsou) | compliance |
| Skutečná data na notebooku vlastníka | bezpečnost | ztráta nebo krádež zařízení; šifrování disku ověřit | IT, přesun do produkce |
| Chybí záloha příloh | provoz | ztráta PDF dokladů = ztráta průkaznosti | IT |
| Otevřené bezpečnostní nálezy (4) | bezpečnost | sdílené nástroje, nezaúčtované návrhy obchodů v pozicích, zámek splátky, vzorce v Excelu | vývoj a druhá osoba |
| Závislost na jednom vývojáři | provoz | nikdo jiný nezná kód ani provoz | vedoucí (R14) |
| Dva prototypy výpočtu NAV | provoz, účetní | dvojí práce a dvě různá čísla NAV pro stejný fond a datum; nejasné, co platí | VED + metodik (R18) |
| Kód psaný AI bez lidské revize | provoz, účetní | chyba v účtovacích pravidlech projde testy stejného autora | revize kritických modulů partnerem (R14) |
| Schvalování při nepřítomnosti | provoz | jediná dostupná osoba by schválila sama sebe | R5 |

**Doporučené cíle obnovy (D, potvrdí vnitřní předpisy):**
- RPO 1 hodina pro databázi (průběžná archivace transakčního logu PostgreSQL) a 24 hodin pro přílohy (denní záloha),
- RTO 1 pracovní den,
- test obnovy čtvrtletně a po každé změně hostingu.

Pro malou investiční společnost s měsíčním oceněním je to přiměřené. Den výpadku nezastaví zveřejnění kurzu
a hodinu práce jde zadat znovu.

### 2.7 Harmonogram

**Je realistický?** V plném rozsahu ne.

| Fakt nebo odhad | Hodnota |
|---|---|
| Rozsah jádra F1–F17 včetně obrazovek (D) | 100–170 MD |
| Pracovní dny od 9. 11. 2026 do 26. 3. 2027 bez státních svátků | 95 |
| Kapacita při polovičním úvazku (D; skutečný úvazek neznáme, P) | zhruba 45 MD |
| Souběžná práce mimo fondy | Services naostro (prosinec), první roční uzávěrka Services hotová v březnu (přiznání v běžné lhůtě, P) |

**Kalendářní kolize:**
- **Dvě řádná měsíční ocenění se do zkušebního provozu 1.–26. 3. 2027 nevejdou.** Ocenění k 31. 3. se dělá až v dubnu.
  Paralelní běh proto použije historická ocenění k 31. 1. a 28. 2. 2027 (A61). Předchozí administrátor dodá data
  do konce února (P), ocenění k 28. 2. ale bude úplné až po jeho dokončení začátkem března (D).
- **26. 3. 2027 je Velký pátek (státní svátek).** Bránu přechodu posunout na 25. 3.
- **Uzávěrka Services 2026:** daňové přiznání v běžné lhůtě (P), takže uzávěrka musí být hotová v březnu. Doporučuji ji
  dokončit do 26. 2. 2027, než začne zkušební provoz fondu.

**Co změnit:**

| Změna | Proč |
|---|---|
| 20. 11.: rozhodnout edici, hosting a přechod Services do produkce současně | všechno ostatní na tom závisí |
| Services: zkušební měsíc do 18. 12. ponechat, ostrý start 4. 1. 2027 v produkci se znovu zadanými doklady | s Enterprise realistické, s Community ne (D) |
| Uzávěrku Services 2026 dokončit do 26. 2. 2027 | v březnu běží zkušební provoz a paralelní běh fondu |
| Prototyp NAV: k bráně 22. 1. přidat nezávislý výpočet (F1) a peněžní toky (F3); uživatelský test od 7. 12. | akceptace C.1 bez nezávislé kontroly neprojde |
| 22. 1.: zmrazit rozsah prvního fondu, vše R přesunout za ostrý provoz | ochrana termínu |
| Výkazy ČNB: datová vrstva a 5 výkazů do zkušebního provozu; pro první 1–2 období povolit záložní export do šablony s ruční kontrolou a zdůvodněním | 5 výkazů je zvládnutelných, 760 položek najednou ne |
| IS: souborové rozhraní a simulátor do 26. 2.; skutečný IS se připojí, až bude existovat | IS není v rukou projektu |
| Ostrý provoz = brána podle C.1, ne datum | konec Q1 je cíl, ne závazek (P) |
| Rezerva 20 % kapacity | dnes žádná (P) |

**Co zjednodušit bez ztráty univerzálnosti jádra:**
- **Nástroje:** datový model a parametry navrhnout pro všechny typy hned, dokončit a otestovat jen skupiny 1–4 varianty A.
  Repo a deriváty přidat později jako konfiguraci a rozšíření.
- **Převzetí:** společný formát hned, převodník jen pro první zdroj. Další převodníky přidat podle dalších administrátorů.
- **Banka:** profily formátů jen pro banky Services a prvního fondu. Další formáty jsou nastavení.
- **IS:** soubory a simulátor, API až s reálným IS.
- **Výkazy ČNB:** snímek dat a 5 výkazů. Ostatní výkazy podle metodik 2027 navážou na stejný snímek.
- **Obrazovky:** jen standardní zobrazení Odoo, žádný vlastní OWL před ostrým provozem.

**Kritická cesta (D):**
1. edice, hosting a R17,
2. produkce,
3. Services,
4. nezávislý NAV, klasifikace IFRS 9 podle fondu a peněžní toky,
5. převzetí a import cen,
6. banka a IS přes soubory,
7. depozitář,
8. výkazy ČNB,
9. paralelní běh.

---

## 3. Návrhy obrazovek

**Společné prvky:**
- **Jazyk a nabídka:** české popisky, jedna aplikace „Investra“.
- **Auditní stopa:** každý záznam má chatter s historií změn a schválení.
- **Klávesové zkratky:**
  - Tlačítka hlavních akcí dostanou zkratku Alt + písmeno přes atribut `data-hotkey` (ověřit v Odoo 20). Paleta
    příkazů Ctrl + K je standardní (Z).
  - Navržená písmena se vyhýbají zkratkám, které Odoo podle mé znalosti používá samo: S uložit, J zahodit,
    C nový záznam, N a P další a předchozí záznam (Z). Kolize je potřeba ověřit v Odoo 20.
- **Vlastní JavaScript (OWL)** je u každé obrazovky uveden výslovně. Kde uveden není, stačí standardní zobrazení.
- **Data v testech** jsou vždy syntetická.

### O1 Ocenění fondu (průvodce od cen po zveřejnění)

**Účel a kdo ji používá:** ÚF provede celé řádné nebo mimořádné ocenění jednoho fondu na jednom místě.
SCH ji otevírá z fronty ke schválení, VED jen ke čtení.

**Rozložení:**
```
┌ Ocenění: Fond Alfa · 30. 11. 2026 · řádné · verze 2 ─────────────────────────────────┐
│ [Návrh]─[Spočteno]─[Ke schválení]─[Schváleno]─[Zaúčtováno]─[U depozitáře]─[Zveřejněno] │
│ Zadal: ÚF1   Schvaluje: SCH (zástup: ÚF2)   Funkční měna: EUR   Termín ČNB: 15. 12.    │
├───────────────────────────────────┬───────────────────────────────────────────────────┤
│ KROKY                             │ DETAIL VYBRANÉHO KROKU                             │
│ ✔ 0 Příprava      IS, banka, kurzy │ 1 Ceny: 18 nástrojů                                │
│ ⚠ 1 Ceny          2 výjimky        │ ISIN/nástroj       Cena   Zdroj    Stáří   Δ %      │
│ ○ 2 Přecenění FX                   │ XS… Dluhopis A     101,2  BBG      1 d     +0,4     │
│ ○ 3 Reálná hodnota                 │ SPV Beta úvěr      –      posudek  210 d   ⚠        │
│ ○ 4 Úplaty, dohady, daň            │ [Importovat ceny] [Otevřít výjimky]                 │
│ ○ 5 NAV a třídy                    │                                                    │
│ ○ 6 Kontroly                       │                                                    │
│ ○ 7 Schválení                      │                                                    │
│ ○ 8–11 Zaúčtování až navazující    │                                                    │
├───────────────────────────────────┴───────────────────────────────────────────────────┤
│ SOUHRN  NAV 512 340 120 EUR · Δ FK +1,8 % · Třída A CZK 1,0432 (+0,6 %) · Třída I EUR 1,0711 │
│ [Spočítat (Alt+R)]  [Odeslat ke schválení (Alt+O)]        Kontroly: 0 stop · 2 upozornění │
└───────────────────────────────────────────────────────────────────────────────────────┘
Záložky: Přemostění FK | Aktiva a pasiva podle rolí | Třídy | Návrhy dokladů | Výjimky | Historie verzí
```

**Záložka Třídy – přemostění kapitálu po třídách.** Sloupce jsem převzal z návrhu vedoucího a doplnil měnu, změnu kurzu
a kontrolní řádek. Kapitál tříd je ve funkční měně fondu, kurz za kus v měně zveřejnění třídy (P).
```
Třída  Měna  FK (t−1)  + Úpisy  − Odkupy  − Dividendy  = Upravený FK  Výsledek  Perf. alokace  = FK  Kusy  Kurz/kus  Δ %
A      CZK   …         …        …         …            …              …         …              …     …     1,0432    +0,6
I      EUR   …         …        …         …            …              …         …              …     …     1,0711    +0,4
Celkem                                                                                         512 340 120 EUR
Kontroly: Σ FK tříd = FK fondu ✔ · FK (t−1) = FK předchozího zveřejněného ocenění ✔ · Σ výsledku tříd = výsledek fondu ✔
```

**Pole, akce a stavy:**
- **Stavy (P):** Návrh → Spočteno → Ke schválení → Schváleno → Zaúčtováno → U depozitáře → Potvrzeno depozitářem →
  Zveřejněno a uzamčeno; vedlejší stavy Vráceno a Stornováno.
- **Kroky 0–11 (P):** každý má stav OK, Upozornění, Stop nebo Neproběhl a odkaz na podklad (import cen, návrh dokladu FX,
  výpočet úplat).
- **Hlavička:** fond, datum ocenění, druh (řádné, mimořádné, opravné), verze, zadavatel, schvalovatelé podle matice,
  termíny ze SDAT.
- **Období (podle návrhu vedoucího):** začátek a konec, počet dní v období a v roce pro časové rozlišení úplat,
  odkaz na předchozí ocenění, počítaný příznak ziskového období.
- **Vstupy za fond:** výsledek hospodaření, oceňovací rozdíly a kapitálové fondy. Berou se z hlavní knihy podle rolí
  účtů s odkazem na zdroj, ne ručním zadáním.
- **Akce:**
  - *Spočítat* – kdykoli do odeslání ke schválení. Předchozí výsledek zůstane v historii.
  - *Odeslat ke schválení* – jen bez stopu, nebo se schválenou výjimkou ke každému stopu.
  - *Schválit* / *Vrátit s důvodem* – jen schvalovatel podle matice, nikdy zadavatel. U fondu cizího obhospodařovatele
    až s přiloženým písemným schválením obhospodařovatele.
  - *Vrátit do návrhu* – jen před schválením. Po zaúčtování už jen storno a nová verze (P, C.1 bod 5).
  - *Zaúčtovat*, *Odeslat depozitáři*, *Zaznamenat stanovisko* (potvrzeno / vráceno s důvodem), *Zveřejnit kurz*.

**Kontroly a varování (P, C.2):**
- **Stop:**
  - pozice ≠ hlavní kniha,
  - kusy ≠ IS,
  - účet se zůstatkem bez role,
  - chybí cena nebo kurz,
  - chybí závěrka IS,
  - nezaúčtované doklady před datem ocenění,
  - FK (t−1) třídy ≠ FK třídy v předchozím zveřejněném ocenění,
  - součet výsledku po třídách ≠ výsledek fondu, součet FK tříd ≠ FK fondu,
  - u fondu cizího obhospodařovatele chybí přiložené písemné schválení (blokuje schválení).
- **Upozornění:**
  - stáří ceny nad limit nástroje,
  - změna FK nad práh fondu,
  - skok ceny nad práh,
  - nespárovaná banka,
  - nárok na kupón nebo dividendu bez výplaty po splatnosti.

Každé varování má tlačítko „otevřít příčinu“ a pole „výjimka schválena kým a proč“.

**Prázdný stav a chyby:**
- *Bez ocenění:* „Pro fond Alfa zatím žádné ocenění. Další řádné ocenění podle kalendáře: 31. 12. 2026. [Založit ocenění]“
- *Chyba výpočtu:* pruh s krokem, příčinou a akcí, např. „Chybí kurz ECB USD k 30. 11. → [Stáhnout kurzy]“.
  Nikdy jen technická výjimka.
- *Souběžná změna:* „Ocenění mezitím změnil ÚF2 (10:42). Načtěte znovu.“

**Hromadné operace a zkratky:**
- Hromadné akce jsou v O3: založit ocenění pro vybrané fondy, spočítat vybrané.
- Zkratky: Alt+R spočítat, Alt+O odeslat ke schválení, Alt+A schválit (jen SCH), Alt+V vrátit.

**Jak postavit v Odoo 20:**
- Standardní **formulář** se stavovým řádkem a záložkami.
- Kroky jako **vnořený seznam** s dekorací podle stavu, souhrn jako pole jen ke čtení.
- Přemostění FK jako vnořený seznam nebo **pivot**.
- Záložka Třídy jako standardní **vnořený seznam** s ukotveným prvním sloupcem, českým formátem čísel a kurzem
  zaokrouhleným podle parametru třídy (P). Méně důležité sloupce budou volitelné, aby se tabulka vešla bez vodorovného
  posuvníku (ověřit v Odoo 20).
- Vrácení s důvodem jako **průvodce (wizard)**.
- **Vlastní OWL jen volitelně (P3, A73):** dvousloupcové rozložení „kroky vlevo, detail vpravo“. Ve standardu stačí
  kroky jako seznam a detail otevírat tlačítkem. Začít standardem a OWL zvážit po druhém kole testu.

### O2 Import a schválení cen

**Účel a kdo ji používá:** ÚF importuje ceny z Excelu (Bloomberg) nebo je zadá ručně s podkladem.
SCH je schválí hromadně kromě výjimek.
- Sdílená cena z veřejného zdroje se schvaluje jednou pro všechny fondy.
- Cena z posudku nebo modelu se schvaluje v každé knize zvlášť.

**Rozložení:**
```
┌ Import cen ────────────────────────────────────────────────────────────┐
│ Soubor: [bbg_2026-11-30.xlsx]  Profil: [Bloomberg PX_LAST v2 ▼]  Datum: 30. 11. │
│ [Načíst náhled]                                                        │
│ Náhled: 142 řádků · 138 OK · 3 neznámý ISIN · 1 změna nad 10 %          │
│ Stav  ISIN      Nástroj      Cena   Měna  Předchozí  Δ %    Fondy       │
│ ✔     CZ000…    Akcie X      512,0  CZK   505,0      +1,4   3           │
│ ⚠     XS…       Dluhopis A   88,1   EUR   101,2     -12,9   1           │
│ ✖     US…       –            12,3   USD   –          –      –           │
│ [Importovat OK řádky jako návrh]  [Stáhnout chyby]                      │
└────────────────────────────────────────────────────────────────────────┘
Seznam „Ceny ke schválení“: seskupeno podle data a zdroje; filtr Výjimky.
```

**Pole, akce a stavy:**
- **Cena:** nástroj, datum, cena, měna, typ ceny (bid, mid, last, posudek, model, zadaná hodnota pozice), zdroj,
  příloha zdrojového souboru, zadal, schválil, kdy.
- **Stavy:** Návrh → Schválená, Zamítnutá, Nahrazená. Oprava je nová cena, stará se nemaže.
- **Profil importu:** mapování sloupců, formát data, desetinná čárka, identifikátor (ISIN, ticker, vlastní kód).
  Je to nastavení, ne kód (P: univerzální import).

**Kontroly a varování:**
- neznámý identifikátor,
- duplicita ceny ke dni,
- skok nad práh nástroje,
- cena starší než datum ocenění,
- jiná měna než měna nástroje,
- zadavatel nemůže schválit vlastní cenu.

**Prázdný stav a chyby:**
- „Žádné ceny ke schválení.“
- Chybný soubor: seznam řádků s důvodem, ke stažení jako XLSX. Soubor bez známého profilu: „Vyberte profil nebo založte nový“.

**Hromadné operace a zkratky:**
- Hromadně schválit vybrané; výjimky se nevyberou automaticky a schvalují se jednotlivě s komentářem.
- Hromadně zamítnout s důvodem.
- Zkratky: Alt+A schválit vybrané, Alt+Z zamítnout.

**Jak postavit:**
- **Průvodce** pro import s náhledem.
- **Seznam** s hromadnou akcí a seskupením, **formulář** ceny.
- Bez OWL.

### O3 Přehled fondů napříč knihami

**Účel a kdo ji používá:** ÚF, SCH a VED vidí stav všech fondů bez přepínání společností: co je hotové, co čeká,
výjimky a termíny.

**Rozložení:**
```
┌ Přehled fondů · ocenění k 30. 11. 2026 ──── Filtr: [Moje fondy] [Po termínu] [Se stopem] ┐
│ Nezaloženo (3) │ Rozpracováno (5) │ Ke schválení (2) │ U depozitáře (4) │ Zveřejněno (12)     │
│ ┌───────────┐  │ ┌──────────────┐ │ ┌──────────────┐ │                  │                     │
│ │Fond Gama  │  │ │Fond Alfa     │ │ │Fond Beta     │ │ …                │ …                   │
│ │termín 7.12│  │ │krok 1 ⚠2     │ │ │čeká 2 dny    │ │                  │                     │
│ │[Založit]  │  │ │ÚF1 · ČNB 15.12│ │ │SCH           │ │                  │                     │
│ └───────────┘  │ └──────────────┘ │ └──────────────┘ │                  │                     │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│ Zobrazení: Kanban | Seznam | Pivot (fond × měsíc) | Kalendář termínů ČNB                       │
└────────────────────────────────────────────────────────────────────────────────────────────┘
Seznam: Fond · Kniha · Režim · Poslední zveřejněný kurz · Rozpracované ocenění · Krok · Stop/Upoz. · ÚF · Další termín ČNB · Dní do termínu
```

**Pole, akce a stavy:**
- **Řádek = uložený stavový snímek fondu.** Aktualizuje se při změně ocenění, ceny nebo výkazu.
- **Obsah snímku:** stav, krok, počty výjimek, termíny ze SDAT, odpovědná ÚF, poslední kurz tříd, režim
  (outsourcing / investiční společnost).
- **Akce:**
  - *Otevřít ocenění* – kniha se přepne sama (ověřit v Odoo 20),
  - *Založit ocenění* pro vybrané fondy,
  - *Spočítat vybrané* na pozadí,
  - *Přiřadit účetní*.

**Kontroly a varování:**
- červeně: po termínu nebo se stopem,
- oranžově: termín do 3 pracovních dnů,
- šedě: fond bez kalendáře ocenění,
- upozornění „u depozitáře déle než N dní“.

**Prázdný stav a chyby:**
- „Nemáte přístup k žádnému fondu. Požádejte správce o přidělení knih.“
- Když uživatel vidí jen část fondů: lišta „Zobrazeno 12 z 30 fondů, k ostatním nemáte oprávnění“.
  Nikdy prázdný seznam bez vysvětlení (dnešní problém, P).
- Chyba hromadného výpočtu u jednoho fondu nezastaví ostatní a zapíše se do chatteru toho ocenění.

**Hromadné operace a zkratky:**
- Výběr více fondů, hromadné založení nebo výpočet.
- Zkratka Alt+M: filtr „Moje fondy“.

**Jak postavit:**
- Model stavového snímku se standardními zobrazeními **kanban, seznam, pivot a kalendář**. Rozšiřuje `investra_dashboard`.
- Data se čtou podle **oprávnění uživatele ke knihám**, ne podle aktivních společností v přepínači.
- Bez OWL.

### O4 Fronta ke schválení a zastupování

**Účel a kdo ji používá:** SCH, a při zastupování ÚF, má na jednom místě vše, co čeká na schválení, napříč knihami:
- ceny, ocenění, ruční úpravy, ruční kurzy, převzetí a změny parametrů fondu,
- platby Services, pokud se zavedou (R4).

**Rozložení:**
```
┌ Ke schválení (7) ──────────── [Moje] [Jako zástup za SCH] [Vše, co smím] ───────────┐
│ Druh        Fond/kniha   Popis                         Zadal  Čeká  Výjimky  Termín  │
│ Ocenění     Alfa         30. 11., NAV 512,3 mil. EUR   ÚF1    1 d   2 upoz.  7. 12.  │
│ Ceny        (sdílené)    142 cen k 30. 11.              ÚF2    3 h   1        –       │
│ Ruční kurz  Beta         EUR/CZK k 30. 11.: 25,105      ÚF1    1 d   –        –       │
│ Parametr    Gama         Úplata za obhospodařování 1,5 % → 1,4 %  metodik 2 d –  –   │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Detail vybraného: souhrn a odkaz „Otevřít“ · [Schválit (Alt+A)] [Vrátit s důvodem (Alt+V)] │
└──────────────────────────────────────────────────────────────────────────────────────┘
Zastupování: Zastupuje [ÚF2] za [SCH] od [1. 12.] do [11. 12.] pro [všechny fondy / vybrané]
```

**Pole, akce a stavy:**
- **Položka:** druh, odkaz na záznam, kniha, zadavatel, od kdy čeká, termín, počet výjimek, požadovaná úroveň podle matice.
- **Akce:** Schválit, Vrátit s důvodem, Otevřít.
- **Zastupování:** kdo, za koho, od–do, rozsah fondů; stav Platné / Ukončené; auditované.

**Kontroly a varování:**
- Zadavatel neschválí vlastní záznam ani v zastoupení.
- Při schválení v zastoupení se zapíše, za koho bylo provedeno.
- U fondu cizího obhospodařovatele nejde ocenění schválit bez přiloženého písemného schválení obhospodařovatele.
- Upozornění na položky čekající déle než N dní a na blížící se termíny.
- Když je dostupná jen jedna osoba, platí R5, nikdy schválení sebe sama.

**Prázdný stav a chyby:**
- „Nic nečeká na vaše schválení. Naposledy schváleno: ocenění Alfa 27. 11.“
- Položku mezitím vyřídil jiný schvalovatel: „Položka už byla vyřízena (SCH, 10:42).“
- Zastupování mimo platné období: „Zastupování za SCH skončilo 11. 12.“

**Hromadné operace a zkratky:**
- Hromadně schválit jde jen položky stejného druhu bez výjimek (typicky ceny). Ocenění vždy jednotlivě.
- Zkratky: Alt+A schválit, Alt+V vrátit; pohyb mezi položkami standardním stránkováním formuláře (ověřit v Odoo 20).

**Jak postavit:**
- Společná fronta nad všemi schvalovanými záznamy (pohled nebo společný model; zvolí agent podle kódu).
- **Seznam** s detailem ve **formuláři**, **průvodce** pro vrácení, **aktivity** Odoo jako upozornění.
- Bez OWL.

### O5 Přijatá faktura z PDF (Services)

**Účel a kdo ji používá:** ÚS zadá přijatou fakturu nebo účtenku rychle a bez chyb v DUZP a dani.

**Rozložení:**
```
┌ Přijatá faktura FP/2026/11/0004 · Koncept ──────────────────────────────────────────────┐
│ ┌ PDF náhled ──────────────┐  Dodavatel: [Cloud Ltd (IE) ▼]  DIČ IE… · fiskální pozice: IO EU │
│ │                          │  Č. faktury dodavatele: [INV-8812]                              │
│ │  (náhled PDF)            │  Datum vystavení: [3. 11.]  DUZP: [31. 10.] ⓘ jiný měsíc než vystavení │
│ │                          │  Účetní datum: 31. 10. (z DUZP)   Splatnost: [17. 11.]           │
│ │                          │  Měna: USD · kurz ČNB platný k 31. 10. (vyhlášen 30. 10.): 23,412 │
│ └──────────────────────────┘  Hradil: (•) firma ( ) soukromě → [osoba ▼]                      │
│ Řádky: Licence 10/2026 · 518810 Software · 120,00 USD · DPH IO EU 21 % (navrženo) ✔             │
│ Souhrn: základ 2 809 Kč · daň IO 590 Kč (zvyšuje náklad, bez odpočtu) · k úhradě 120,00 USD    │
│ [Potvrdit (Alt+Q)]  [Uložit koncept]                                                          │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```
(31. 10. 2026 je sobota, platí kurz vyhlášený v pátek 30. 10.)

**Pole, akce a stavy:**
- Standardní pole přijaté faktury a stavy Koncept → Zaúčtováno → Storno.
- **Nové pole „Hradil“:** firma, nebo soukromě. Při úhradě soukromě vznikne závazek vůči osobě, která platila (Z, postup A05).
- Předvyplnění z historie dodavatele: účet, daň, splatnost.
- **Vstup:**
  - e-mailový alias deníku FP nebo přetažení PDF,
  - s Enterprise vytěžení (R10), jinak předvyplnění z historie.

**Kontroly a varování:**
- **Stop:**
  - duplicitní číslo faktury dodavatele,
  - DUZP v uzamčeném období,
  - zahraniční dodavatel služby bez daně identifikované osoby (viz O6),
  - chybí kurz k DUZP.
- **Upozornění:**
  - daň identifikované osoby u zboží,
  - součet řádků ≠ částka v PDF (jen u vytěženého dokladu).
- **Informace:** DUZP v jiném měsíci než vystavení.

**Prázdný stav a chyby:**
- Prázdný seznam „Doklady k zadání“: „Žádné nové doklady. Pošlete PDF na alias deníku nebo je přetáhněte sem.“
- Nečitelné PDF nebo neúspěšné vytěžení: koncept vznikne s přílohou a hlášením „Údaje nešlo načíst, vyplňte ručně“.
- Neznámý dodavatel: nabídka založit partnera z DIČ.

**Hromadné operace a zkratky:**
- Hromadné nahrání více PDF vytvoří koncepty.
- Hromadné potvrzení konceptů bez upozornění.
- Zkratky: Alt+Q potvrdit; další koncept standardním stránkováním (ověřit v Odoo 20).

**Jak postavit:**
- Standardní **formulář** přijaté faktury. Náhled PDF vedle formuláře je ve standardu na širokém displeji (ověřit v Odoo 20).
- Pole „Hradil“ a kontroly jako rozšíření dokladu.
- Návrh daně jako vlastní logika, protože fiskální pozice prázdnou daň nedoplní (P).
- Bez OWL.

### O6 DPH identifikované osoby

**Účel a kdo ji používá:** ÚS (metodik) měsíčně ověří, že všechny přijaté služby ze zahraničí mají daň identifikované
osoby, připraví podklad pro přiznání a provede zpětnou kontrolu od 19. 3. 2026.

**Rozložení** (čísla řádků přiznání jsou ilustrativní, ověřit s poradcem):
```
┌ DPH identifikované osoby · Období [10/2026 ▼] · Stav: Rozpracováno ────────────────────────┐
│ Kontroly: ✔ 7 dokladů s daní IO · ⚠ 1 zahraniční doklad bez daně · ✔ kurzy k DUZP           │
│ Doklad       Dodavatel  Země  DUZP   Plnění  Základ Kč  Daň Kč  Sazba  Řádek  Stav           │
│ FP/…/0004    Cloud Ltd  IE    31.10  služba  2 809      590     21 %   ř. 5   ✔              │
│ FP/…/0007    SaaS Inc   US    12.10  služba  1 170      –       –      –      ⚠              │
│ Souhrn: ř. 5 základ/daň · ř. 12 základ/daň · odpočet ř. 43–44: 0 (bez nároku)               │
│ [Označit výjimku s důvodem] [Export podkladu] [Uzavřít období DPH]                           │
│ Obrat pro registraci k DPH (12 měsíců): 1 240 000 Kč · limit nastaví metodik podle poradce   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
Záložka „Zpětná kontrola od 19. 3. 2026“: stejný seznam po měsících s počtem dokladů bez daně.
```

**Pole, akce a stavy:**
- **Období DPH:** Rozpracováno → Uzavřeno (po podání, které provádí člověk).
- **Doklad v přehledu:** druh plnění (služba, zboží), země, sazba, řádek přiznání.
- **Výjimka:** důvod, schválení metodikem.

**Kontroly a varování:**
- zahraniční dodavatel služby bez daně,
- daň identifikované osoby u tuzemského dodavatele,
- kurz není kurz ČNB platný k DUZP,
- doklad s DUZP v uzavřeném období DPH,
- odpočet v řádcích 43–44 ≠ 0 je stop (P: lokalizace předpokládá plátce),
- obrat se blíží nastavenému limitu.

**Prázdný stav a chyby:**
- „V období 10/2026 nejsou žádné zahraniční doklady.“ Zda se přiznání podává, potvrdí poradce.
- Chybí kurz k DUZP: řádek je červeně s akcí „Stáhnout kurz“.
- Pokus změnit uzavřené období: „Období je uzavřené. Oprava jen opravným dokladem v otevřeném období.“

**Hromadné operace a zkratky:**
- Hromadně doplnit navrženou daň u vybraných *konceptů*. U zaúčtovaných dokladů jen opravným dokladem.
- Export podkladu do XLSX a CSV.
- Zkratky: Alt+E export, Alt+X označit výjimku.

**Jak postavit:**
- **Seznam a pivot** nad řádky dokladů s daní identifikované osoby.
- **Formulář** období DPH.
- S Enterprise napojit na zobrazení přiznání DPH s upravenou definicí, v Community export.
- Bez OWL.

### O7 Banka: výpisy a párování (Services i fondy)

**Účel a kdo ji používá:** ÚS a ÚF importují výpis, systém navrhne spárování a účetní návrh potvrdí (P: párování je vždy
jen návrh).

**Rozložení:**
```
┌ Výpis 2026/11/003 · účet CZK · 14 pohybů · 11 navrženo · 3 bez návrhu ─────────┐
│ Datum  Protistrana        VS      Částka    Návrh               Jistota  Akce    │
│ 3.11   Klient X           260004  +12 100   FV/2026/0004        vysoká   ✔ ✖     │
│ 3.11   (úpis, maskováno)  ID-7731 +500 000  úpis třída A (IS)   vysoká   ✔ ✖     │
│ 3.11   ?                  –       -1 500    –                   –        [Ručně] │
│ [Potvrdit vybrané (Alt+Q)]   Zůstatek výpisu = zůstatek účtu ✔                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Pole, akce a stavy:**
- **Výpis:** účet, číslo, období, počáteční a konečný zůstatek, profil formátu, zdrojový soubor.
- **Řádek:** datum, částka, VS nebo identifikátor, protistrana (u plateb investorů podle R17 maskovaná), návrh, jistota.
- **Stavy řádku:** Nový → Navržený → Potvrzený; Ručně zaúčtovaný.
- **Akce:** Importovat, Potvrdit, Zamítnout návrh, Ručně spárovat nebo zaúčtovat.

**Kontroly a varování:**
- konečný zůstatek výpisu ≠ zůstatek účtu (stop),
- mezera v číslech výpisů,
- duplicitní import,
- platba úpisu bez identifikátoru z IS (upozornění v ocenění, krok 6).

**Prázdný stav a chyby:**
- „Žádný nový výpis. Poslední import 2. 11. [Importovat]“
- Nerozpoznaný formát: „Soubor neodpovídá profilu. Vyberte jiný profil.“

**Hromadné operace a zkratky:**
- Hromadně potvrdit návrhy s vysokou jistotou.
- Zkratka Alt+Q potvrdit vybrané.

**Jak postavit:**
- **Enterprise:** standardní párování a import, doplnit profily formátů, které chybí.
- **Community:** moduly OCA, pokud budou portované, nebo vlastní **průvodce** importu a **seznam** návrhů s hromadným
  potvrzením.
- Bez OWL. API bank až jako P3.

### O8 Výkazy ČNB

**Účel a kdo ji používá:** ÚF připraví výkazy fondu za období, zkontroluje je a vyexportuje soubor.
VED sleduje termíny. Odesílá a podepisuje člověk mimo Odoo (P).

**Rozložení:**
```
┌ Výkazy ČNB · Fond Alfa · 11/2026 ──────────────────────────────────────────────┐
│ Výkaz     Termín (SDAT)  Snímek ocenění  Kontroly          Stav          Akce   │
│ RISIFI30  15. 12.        30. 11. v2      0 stop · 1 upoz.  Připraveno    [Export] │
│ TISIFI10  15. 12.        30. 11. v2      2 stop            Rozpracováno          │
│ VISIFI10  …                                                                      │
│ Fond v EUR: částky v CZK přepočtené kurzem ČNB 25,105 (datum podle metodiky) ✔   │
│ Záložní cesta: [Export do šablony XLSX] (vyžaduje zdůvodnění, R9)                │
└─────────────────────────────────────────────────────────────────────────────────┘
Detail výkazu: řádek → hodnota → rozpad na účty, role, nástroje a protistrany
```

**Pole, akce a stavy:**
- **Výkaz:** fond, období, typ výkazu, verze metodiky, snímek ocenění, termín, verze výkazu; u fondu s funkční měnou EUR
  kurz ČNB pro přepočet do CZK s datem a zdrojem (P: výkazy ČNB jsou vždy v CZK).
- **Stavy:** Rozpracováno → Připraveno → Exportováno → Odesláno (zaznamená člověk) → Opraveno (nová verze).
- **Akce:** Vytvořit snímek, Spočítat, Exportovat, Záložní export se zdůvodněním, Zaznamenat odeslání, Založit opravu.

**Kontroly a varování:**
- chybějící atributy protistran (sektor, rezidence, LEI),
- u fondu v EUR chybí kurz ČNB pro přepočet, nebo je použitý jiný zdroj kurzu (stop),
- součty proti rozvaze a ocenění po přepočtu do CZK,
- závažné kontroly podle metodiky ČNB (ověřit v metodice FOFI20261201),
- blížící se termín.

**Prázdný stav a chyby:**
- „Pro období 11/2026 zatím není zveřejněné ocenění. Výkazy čekají na snímek.“
- Neznámá verze metodiky: „Výkaz RISIFI30 nemá převodovou tabulku pro metodiku platnou k 31. 1. 2027.“

**Hromadné operace a zkratky:**
- Hromadně vytvořit výkazy za období pro vybrané fondy.
- Hromadný export připravených výkazů.
- Zkratka Alt+E export.

**Jak postavit:**
- Model výkazu a řádků se **seznamem a formulářem**.
- Rozpad hodnoty jako akce, která otevře **seznam** zdrojových řádků.
- Kalendář termínů jako **kalendář**.
- Export souboru ve formátu pro SDAT (ověřit v metodice).
- Bez OWL.

### O9 Převzetí fondu (průvodce)

**Účel a kdo ji používá:** ÚF a metodik převezmou fond od předchozího administrátora. Přechod schvaluje odpovědná osoba
(P, C.1 bod 8).

**Rozložení:**
```
┌ Převzetí: Fond Delta · zdroj: Administrátor X · ke dni 31. 1. 2027 ────────────────────┐
│ 1 Zdroj ✔ → 2 Osnova a role ✔ → 3 Počáteční stavy ⚠ → 4 Pozice ○ → 5 Třídy a historie ○ │
│ → 6 Kontroly ○ → 7 Paralelní běh a schválení ○                                         │
│ Krok 3: předvaha 214 účtů · 2 účty bez role · rozdíl 0,00 · [Namapovat role]            │
│ Příznaky: 3 pozice „převzato bez historie“ (pořizovací kurz = kurz ke dni převzetí)     │
│ [Zpět] [Pokračovat] [Přerušit a uložit]                                                │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Pole, akce a stavy:**
- **Převzetí:** fond, zdroj, profil převodníku, den převzetí, zdrojové soubory, příznaky úplnosti.
- **Stavy:** Rozpracováno → Zkontrolováno → Paralelní běh → Schváleno → Převzato; vedlejší stav Zrušeno.
- **Akce:** Načíst, Namapovat role, Spustit kontroly, Označit chybějící údaj podle pravidla, Odeslat ke schválení.

**Kontroly a varování (P, C.4 bod 6):**
- předvaha a otevřené položky proti účtům,
- pozice proti hlavní knize,
- kusy proti IS,
- reprodukce FK,
- chybějící údaje podle pravidel z 2.3 jako upozornění s příznakem.

**Prázdný stav a chyby:**
- „Žádné rozpracované převzetí. [Založit převzetí]“
- Soubor neodpovídá formátu: seznam polí, která chybějí nebo mají špatný typ.

**Hromadné operace a zkratky:**
- Hromadné mapování účtů na role podle předpony účtu s náhledem.
- Zkratky: Alt+K spustit kontroly, Alt+U pokračovat.

**Jak postavit:**
- **Průvodce** nad trvalým záznamem převzetí, aby šlo přerušit a pokračovat.
- Mapování jako editovatelný **seznam**.
- Bez OWL.

---

## 4. Rozhodnutí pro lidi

| # | Rozhodnutí | Varianty | Doporučení a důvod | Kdo | Do kdy |
|---|---|---|---|---|---|
| R1 | Edice | a) Community s moduly OCA a vlastním vývojem; b) Enterprise (plán Custom); c) Services v Enterprise, fondy v Community (dvě instance) | **b.** Ušetří 35–75 MD (D), moduly OCA pro Odoo 20 pravděpodobně nebudou včas (ověřit). c) zdvojí provoz a odporuje cíli jedné platformy. Zkušební verzi Enterprise zajistit do 13. 11. 2026 (zatím otevřené) | VED + metodik | 20. 11. 2026 |
| R2 | Hosting a provozovatel | a) vlastní IT; b) spravovaný server nebo cloud v EU se smlouvou na správu; c) Odoo.sh | **b.** Malý tým nemá vlastní IT. U c) není smluvně zaručená lokalita dat (P, ověřit). RPO 1 h pro databázi, 24 h pro přílohy, RTO 1 pracovní den, test obnovy čtvrtletně (D) | VED | 20. 11. 2026 |
| R3 | Přechod Services do produkce | a) přejmenovat `investra_dev` na produkci; b) čistá databáze, nastavení z modulů, doklady znovu zadat s opravami; c) čistá databáze a import dokladů skriptem | **b.** Jen 9 dokladů (P), práce asi na den. Čistá auditní stopa bez testovací historie, opravy proběhnou správně. Termín 18. 12. udrží. a) přenese chyby a označení TEST, c) se při 9 dokladech nevyplatí | metodik | 20. 11. 2026 |
| R4 | Čtyři oči u Services | a) nezavádět; b) jen platby a ruční zápisy do uzavřeného období; c) všechny doklady | **b** s měsíční kontrolou jednatelem, dokud Services účtuje jedna osoba. c) je pro jednu osobu neprovozovatelné | VED | 18. 12. 2026 |
| R5 | Zastupování a jediná dostupná osoba | a) ocenění počká; b) náhradní schvalovatel podle matice fondu (VED, obhospodařovatel); c) dodatečné schválení do N dní | **b**, a když není nikdo, **a**. Nikdy schválení sebe sama. c) porušuje pravidlo, že bez schválení se nezaúčtuje (C.1 bod 4) | VED + metodik | 22. 1. 2027 |
| R6 | Režimy outsourcing / vlastní investiční společnost | a) navrhnout jen jeden režim; b) schvalovací matice a odpovědný subjekt jako parametr fondu s platností od | **b.** Stejný kód pro oba režimy, licence = nový záznam, ne vývoj. Cizí obhospodařovatel schvaluje písemně mimo Odoo (P, rozhodnuto 8. 11. 2026), schválení přiloží a zaeviduje SCH | metodik; odpovědnost ověří právník | 22. 1. 2027 |
| R7 | Standardní doklady ve fondových knihách | A) povolit přijaté faktury a banku s registrací jako událost; B) vše jen přes události | **A.** Nevyvíjet znovu přijaté faktury a banku. Ocenění, přecenění, úplaty a obchody jen přes události | metodik | 4. 12. 2026 |
| R8 | Pořadí typů nástrojů | A) podle četnosti u FKI; B) podle modelu peněžních toků; C) podle prvního fondu | **A** se společným modelem peněžních toků pro dluhové nástroje (2.3) | metodik | 4. 12. 2026 |
| R9 | Cesta výkazů ČNB pro první období | a) jen z Odoo; b) z Odoo se záložním exportem do šablony a zdůvodněním; c) externí nástroj | **b.** Chrání termín a zachová cíl „výkazy z Odoo“ | metodik + VED | 22. 1. 2027 |
| R10 | Vytěžování PDF | a) Enterprise vytěžování (doklady jdou ke službě Odoo); b) vlastní vytěžování s potvrzením člověkem; c) jen předvyplnění z historie | s Enterprise **a** po zápisu do evidence ICT dodavatelů, bez Enterprise **c** a později **b** | VED + compliance | 20. 11. 2026 (s R1) |
| R11 | Pravidla pro chybějící údaje při převzetí | tabulka v 2.3 | přijmout jako metodiku a nechat potvrdit auditorem | metodik + auditor | 26. 2. 2027 |
| R12 | Kdo udělá nezávislý výpočet NAV | a) účetní fondu v tabulce; b) depozitář (stínový NAV); c) externí poradce | **a** pro akceptaci prototypu (alespoň 3 scénáře včetně performance fee a třídy v EUR, dodat do 8. 1. 2027), **b** jako průběžná kontrola, pokud ji depozitář nabízí | VED | 4. 12. 2026 |
| R13 | Definice ostrého provozu | a) datum 31. 3. 2027; b) brána podle C.1 | **b** | VED | 22. 1. 2027 |
| R14 | Revize kódu a zastupování vývojáře | a) nic; b) partner reviduje kritické moduly; c) b) a smlouva na zastupování | **c.** Jediný autor a kód psaný AI; smlouva snižuje závislost na jednom člověku | VED | 22. 1. 2027 |
| R15 | Uzávěrka bez účtů 701, 702, 710 | a) ponechat zámek a 431; b) uzávěrkové a otevírací zápisy malým průvodcem | rozhodne auditor; **b** připravit, pokud auditor a) nepřijme | metodik + auditor | 15. 1. 2027 (před první roční uzávěrkou) |
| R16 | Kde vzniká účetní závěrka fondu | a) rozvaha a výsledovka z Odoo, příloha ve Wordu; b) vše mimo Odoo z předvahy | **a** (P: výroční zpráva se dokončuje ve Wordu) | metodik | 26. 2. 2027 |
| R17 | Údaje o investorech v bankovních výpisech fondů a ve zprávách IS | a) sběrný účet řízený IS, Odoo dostane jen souhrnnou platbu; b) při importu výpisu fondu ukládat u plateb investorů jen identifikátor z IS, částku a datum, jméno a účet protistrany nepřebírat; originál výpisu archivovat mimo Odoo; c) vědomě připustit minimální údaje s právním základem | **a** i **b** jako parametr fondu, protože cesta úpisů se liší podle fondu (P). c) jen po souhlasu pověřence. Výplaty investorům zadává IS (P) | VED + pověřenec pro ochranu osobních údajů | 4. 12. 2026 |
| R18 | Sjednocení prototypů výpočtu NAV | a) ponechat oba moduly vedle sebe; b) jediný výpočet v `investra_nav`, z modulu vedoucího převzít obrazovku (přemostění po třídách, údaje o období); c) přejít na modul vedoucího a doplnit do něj události, čtyři oči, zaúčtování a testy | **b.** `investra_nav` už má události, jediný účtovací modul, čtyři oči, 274 testů a shodu s referenčním výpočtem (P). Modul vedoucího může zůstat mimo produkci jako kontrolní výpočet pro testovací scénáře. a) znamená dvojí práci a dvě různá čísla NAV | VED + metodik | 4. 12. 2026 |

---

## 5. Akční plán pro vývojového agenta

**Výklad a pravidla plánu:**
- **Priority:** u kroků Services čtu P0 jako „blokuje ostrý provoz Services“ (brána 18. 12. a start 4. 1. 2027),
  u ostatních kroků podle zadání jako „blokuje první fond“.
- **Pořadí:** kroky jsou seřazené podle priority a uvnitř priority tak, aby každá závislost stála dřív.
- **Kroky agenta:** u typů `kód` a `obrazovka` popisuji chování a akceptaci, implementaci navrhne agent podle kódu.
- **Data a citlivé údaje:** agent používá jen syntetická testovací data. Nepracuje s hesly, osobními údaji ani se
  skutečnými doklady; kroky, které je vyžadují, má `rozhoduje: člověk`.
- **Značení:** „(nový)“ označuje část, která podle podkladu neexistuje.
- **Číslování:** krok A75 (rozhodnutí R18) přibyl dodatečně. Podle priority patří mezi rozhodnutí na začátku plánu,
  proto stojí hned za A10 mimo číselnou řadu.

```yaml
- id: A01
  priorita: P0
  oblast: architektura
  typ: analýza
  nazev: Ověřit funkce Odoo 20 a stav portů OCA
  popis: Pro každou funkci z kapitoly 2.2 revize zjistit, zda je v Odoo 20 Community, v Enterprise, nebo v modulu OCA s větví 20.0, a s jakým omezením. Je to podklad pro rozhodnutí o edici; odhady vlastního vývoje v revizi jsou bez tohoto ověření jen orientační.
  dotcene_casti:
    - docs/pruzkum/
    - docs/analyza-odoo20-nav.md
  akceptace:
    - Tabulka pokrývá předvahu, hlavní knihu, rozvahu a výsledovku, přiznání DPH, import výpisů (CAMT.053, MT940, GPC, OFX), párování, časové rozlišení, vytěžování PDF, e-mailový alias deníku, náhled PDF u faktury, vynucení TOTP, přepnutí společnosti při otevření záznamu a zkratky tlačítek
    - U každé položky je edice, název modulu a ověřitelný zdroj (kód sestavení 20.0-20261102, dokumentace nebo repozitář OCA)
    - Co nešlo ověřit, je označené jako neověřené, ne jako dostupné
  zavisi_na: []
  odhad: S
  rozhoduje: agent
  riziko: Kód Enterprise agent nemá, funkce Enterprise ověří jen z dokumentace nebo ve zkušební verzi; poznáme podle podílu neověřených položek.

- id: A02
  priorita: P0
  oblast: architektura
  typ: rozhodnutí
  nazev: Rozhodnout edici Odoo (R1)
  popis: Vybrat mezi Community s moduly OCA a vlastním vývojem, Enterprise (plán Custom) a kombinací. Revize doporučuje Enterprise, protože ušetří zhruba 35 až 75 MD vývoje za licence řádově 1 400 až 2 700 € ročně. Termín 20. 11. 2026.
  dotcene_casti:
    - docs/rozhodnuti.md
    - docs/pruzkum/
  akceptace:
    - Rozhodnutí je v deníku rozhodnutí s variantou, cenou licencí a důvodem
    - Kroky A15, A18, A19, A53 a A64 mají podle edice upřesněný rozsah
  zavisi_na: [A01]
  odhad: S
  rozhoduje: člověk
  riziko: Odklad posune bránu 18. 12.; poznáme podle chybějícího zápisu k 20. 11.

- id: A03
  priorita: P0
  oblast: provoz
  typ: rozhodnutí
  nazev: Rozhodnout hosting, provozovatele a cíle obnovy (R2)
  popis: Vybrat provoz (vlastní IT, spravovaný server nebo cloud v EU se smlouvou na správu, Odoo.sh) a stanovit RTO a RPO. Revize doporučuje spravovaný provoz v EU, RPO 1 hodina pro databázi a 24 hodin pro přílohy a RTO 1 pracovní den; hodnoty potvrdí vnitřní předpisy.
  dotcene_casti:
    - docs/rozhodnuti.md
    - docs/otevrene-body.md
  akceptace:
    - Zápis v deníku rozhodnutí s poskytovatelem, lokalitou dat, RTO, RPO a odpovědnou osobou
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez rozhodnutí nelze připravit produkci; poznáme podle toho, že A12 a A13 nemohou začít.

- id: A04
  priorita: P0
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Rozhodnout přechod Services do produkce (R3)
  popis: Vybrat mezi přejmenováním investra_dev, čistou databází se znovu zadanými doklady a importem dokladů skriptem. Revize doporučuje čistou databázi s nastavením z modulů a znovu zadanými 9 doklady s opravami; investra_dev zůstane vývojová.
  dotcene_casti:
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí včetně data ostrého startu Services
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Další skutečné doklady zadané do investra_dev zvětší rozsah přenosu; poznáme podle počtu dokladů s datem po 8. 11. 2026.

- id: A05
  priorita: P0
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Schválit účetní postup oprav dokladů Services
  popis: Metodik rozhodne, jak opravit nesoulad číslování vydaných faktur, soukromě hrazený výdaj statutára (závazek vůči osobě, která platila, místo dodavatele) a náklady jiné společnosti skupiny (přefakturace nebo přeúčtování). Sporné body potvrdí auditor.
  dotcene_casti:
    - docs/rozhodnuti.md
    - docs/osnova-revize-podklad.md
  akceptace:
    - Ke každému ze tří problémů je v deníku rozhodnutí zvolený postup a účet nebo role účtu
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez rozhodnutí se chyby přenesou do produkce; poznáme při odsouhlasení v A20.

- id: A06
  priorita: P0
  oblast: ocenění
  typ: rozhodnutí
  nazev: Určit osobu pro nezávislý výpočet NAV (R12)
  popis: Vybrat, kdo nezávisle na autorovi kódu spočítá očekávané výsledky alespoň tří scénářů (performance fee, třída v EUR, úpisy a odkupy). Revize doporučuje účetní fondu v tabulce a jako průběžnou kontrolu depozitáře, pokud stínový výpočet nabízí.
  dotcene_casti:
    - docs/harmonogram.md
  akceptace:
    - Je jmenovaná role, která není autorem kódu, a termín dodání scénářů nejpozději 8. 1. 2027
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez nezávislé osoby nelze splnit akceptaci prototypu C.1 bod 1; poznáme na bráně 22. 1. 2027.

- id: A07
  priorita: P0
  oblast: architektura
  typ: rozhodnutí
  nazev: Rozhodnout o standardních dokladech ve fondových knihách (R7)
  popis: Rozhodnout, zda se v knihách fondů smějí používat standardní přijaté faktury a banka registrované jako události, nebo vše jen přes události. Revize doporučuje standardní doklady povolit a ocenění, přecenění, úplaty a obchody ponechat výhradně na událostech.
  dotcene_casti:
    - docs/rozhodnuti.md
    - investra_posting
  akceptace:
    - Zápis v deníku rozhodnutí se seznamem deníků, které jsou jen pro události
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Nejasnost povede k dokladům mimo účtovací modul bez dohledatelnosti; poznáme podle dokladů ve fondové knize bez vazby na událost.

- id: A08
  priorita: P0
  oblast: ocenění
  typ: rozhodnutí
  nazev: Rozhodnout pořadí typů nástrojů (R8)
  popis: Potvrdit pořadí dokončení typů nástrojů a jejich událostí. Revize doporučuje variantu A podle četnosti u FKI (účast a úvěr SPV, dluhopisy a akcie s kupóny a dividendami, ostatní podíl s upisovacím závazkem, potom repo a deriváty) se společným modelem peněžních toků pro dluhové nástroje.
  dotcene_casti:
    - docs/rozhodnuti.md
    - investra_instruments
  akceptace:
    - Zápis v deníku rozhodnutí s pořadím a s rozdělením na jádro a rozšíření
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez pořadí se rozpracuje víc typů najednou a žádný nebude hotový; poznáme podle počtu rozpracovaných typů.

- id: A09
  priorita: P0
  oblast: IS
  typ: rozhodnutí
  nazev: Rozhodnout, jak se do Odoo nedostanou údaje o investorech (R17)
  popis: Bankovní výpisy fondů obsahují u úpisů a odkupů jména a účty investorů a pseudonymní identifikátor z IS je podle GDPR stále osobní údaj. Cesta úpisů se liší podle fondu a výplaty investorům zadává IS (P), proto se varianta (sběrný účet řízený IS, nebo nepřebírání údajů protistrany při importu z účtu fondu) zvolí parametrem fondu; vědomé připuštění minimálních údajů jen po posouzení pověřencem pro ochranu osobních údajů.
  dotcene_casti:
    - docs/rozhodnuti.md
    - docs/architektura.md
  akceptace:
    - Zápis v deníku rozhodnutí se seznamem polí z výpisu a ze zpráv IS, která Odoo smí uložit, pro obě cesty úpisů
    - Vyjádření pověřence pro ochranu osobních údajů je založené u rozhodnutí
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Import výpisů fondů před rozhodnutím uloží osobní údaje investorů v rozporu s pravidlem projektu; poznáme podle jmen fyzických osob v řádcích výpisů fondu.

- id: A10
  priorita: P0
  oblast: architektura
  typ: rozhodnutí
  nazev: Rozhodnout schvalovací matici, režimy a zastupování (R5, R6)
  popis: Stanovit pro režim outsourcingu i pro vlastní investiční společnost, kdo zadává, schvaluje a zastupuje u cen, ocenění, ručních úprav, ručních kurzů a změn parametrů fondu, a co se stane, když je dostupná jen jedna osoba. Revize doporučuje matici jako parametr fondu, náhradního schvalovatele podle matice a nikdy schválení sebe sama.
  dotcene_casti:
    - docs/rozhodnuti.md
    - investra_entity
  akceptace:
    - Matice rolí a akcí je v deníku rozhodnutí pro oba režimy
    - Písemné schválení cizího obhospodařovatele (rozhodnuto 8. 11. 2026) má v matici určené, kdo ho zaeviduje a před kterým krokem ocenění je povinné
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez matice se zastupování vyřeší sdíleným účtem nebo schválením sebe sama; poznáme v auditní stopě schválení.

- id: A75
  priorita: P0
  oblast: architektura
  typ: rozhodnutí
  nazev: Sjednotit prototypy výpočtu NAV (R18)
  popis: Vedle investra_nav vznikl modul vedoucího pro výpočet NAV (podle snímku samostatná aplikace NAV Calculation). Rozhodnout, který výpočet bude jediný produkční. Revize doporučuje investra_nav (události, jediný účtovací modul, čtyři oči, testy) a z modulu vedoucího převzít přemostění kapitálu po třídách a údaje o období do obrazovky O1; modul vedoucího může zůstat mimo produkci jako kontrolní výpočet pro testovací scénáře.
  dotcene_casti:
    - investra_nav
    - modul NAV Calculation vedoucího (mimo podklad)
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí s určením jediného produkčního výpočtu a s tím, co se z druhého modulu převezme
    - Druhý modul nemá přístup k produkční databázi
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Dva výpočty vedle sebe dají rozdílná čísla a nebude jasné, které platí; poznáme podle dvou různých NAV pro stejný fond a datum.

- id: A11
  priorita: P0
  oblast: provoz
  typ: kód
  nazev: Spouštět testy automaticky (CI)
  popis: Všechny testy vlastních modulů, modulu DPH a referenčního výpočtu NAV poběží automaticky při každém odeslání větve a před sloučením do main a výsledek bude vidět u commitu. Dnes se spouštějí ručně.
  dotcene_casti:
    - addons/custom/
    - konfigurace CI (nový)
  akceptace:
    - Každý commit ve větvi má výsledek všech testů (dnes 274 + 13 + 55)
    - Sloučení do main je zablokované, když některý test selže
    - Testy běží nad prázdnou databází se syntetickými daty bez přístupu k investra_dev
  zavisi_na: []
  odhad: S
  rozhoduje: agent
  riziko: Při volbě Enterprise potřebuje CI přístup ke kódu Enterprise; poznáme podle selhání instalace modulů v CI.

- id: A12
  priorita: P0
  oblast: provoz
  typ: kód
  nazev: Připravit provozní skripty a příručku
  popis: Skripty a postup pro nasazení, aktualizaci modulů, zálohu databáze s průběžnou archivací transakčního logu, denní zálohu příloh (filestore), obnovu do vedlejší instance a monitorování, bez hesel v repozitáři.
  dotcene_casti:
    - provozní příručka (nový)
    - skripty provozu (nový)
  akceptace:
    - Obnova zálohy do čisté instance podle příručky proběhne na syntetických datech bez kroků mimo příručku
    - Obnovená instance má stejný počet dokladů a příloh a přílohy jdou otevřít
    - Automatická kontrola v CI nenajde v repozitáři hesla ani klíče
  zavisi_na: [A03]
  odhad: M
  rozhoduje: agent
  riziko: Skripty závisí na zvoleném poskytovateli; poznáme podle selhání testu obnovy v A13.

- id: A13
  priorita: P0
  oblast: provoz
  typ: dokumentace
  nazev: Zřídit produkci a zaprotokolovat test obnovy
  popis: Provozovatel podle příručky z A12 zřídí produkční prostředí v EU, zapne zálohy databáze i příloh a provede první test obnovy; výsledek se zapíše do protokolu.
  dotcene_casti:
    - provozní příručka (nový)
    - protokol testu obnovy (nový)
  akceptace:
    - Protokol testu obnovy s naměřeným RTO a RPO v limitech z A03
    - Produkce má platný certifikát, osobní účty správců a žádnou ukázkovou databázi
  zavisi_na: [A02, A12]
  odhad: M
  rozhoduje: člověk
  riziko: Zpoždění smlouvy s poskytovatelem posune ostrý start Services; poznáme podle chybějícího protokolu před 18. 12. 2026.

- id: A14
  priorita: P0
  oblast: bezpečnost
  typ: kód
  nazev: Vynutit MFA a nastavit přístupové role
  popis: Druhý faktor povinný pro všechny uživatele produkce, role podle matice z A10 a report oprávnění, který jde porovnat s maticí. Žádný sdílený účet a účet správce se nepoužívá k běžné práci.
  dotcene_casti:
    - investra_entity
  akceptace:
    - Přihlášení do produkce bez druhého faktoru nejde
    - Report oprávnění (uživatel, skupina, knihy) se shoduje s maticí a rozdíly jsou vidět
  zavisi_na: [A10, A12]
  odhad: S
  rozhoduje: agent
  riziko: Vynucení MFA může zablokovat automatické importy; poznáme podle selhání importů po zapnutí.

- id: A15
  priorita: P0
  oblast: účetnictví Services
  typ: kód
  nazev: Nastavení Services jako kód
  popis: Moduly po instalaci do prázdné databáze vytvoří stejné nastavení jako investra_dev po revizi z 8. 11. 2026 – osnovu (typy, párování, skryté a nové účty), deníky, daně a fiskální pozice identifikované osoby a datum otevření 19. 3. 2026. Ruční změna nastavení v produkci se ukáže jako odchylka.
  dotcene_casti:
    - investra_vat_identified
    - docs/osnova-revize-podklad.md
    - modul nastavení Services (nový)
  akceptace:
    - Automatický test nainstaluje moduly do prázdné databáze a porovnání osnovy, deníků, daní a fiskálních pozic s referenčním exportem nemá rozdíly
    - Opakovaná aktualizace modulů nic nezdvojí
    - Report odchylek ukáže ručně změněný účet
  zavisi_na: [A02, A04]
  odhad: M
  rozhoduje: agent
  riziko: Referenční export může obsahovat i chyby; poznáme při porovnání s 11 body revize osnovy.

- id: A16
  priorita: P0
  oblast: účetnictví Services
  typ: kód
  nazev: Číslování vydaných faktur a úhrada soukromě
  popis: Číslo vydané faktury v Odoo bude stejné jako na vystaveném dokladu, řadu půjde jednou nastavit na počáteční číslo a bude bez mezer a duplicit. Přijatá faktura a účtenka dostanou volbu, kdo hradil; při úhradě soukromě vznikne závazek vůči osobě, která platila, na účtu podle A05.
  dotcene_casti:
    - modul nastavení Services (nový)
    - investra_vat_identified
  akceptace:
    - Test vystaví fakturu a číslo v PDF se rovná číslu dokladu
    - Report návaznosti řady ukáže mezeru i duplicitu
    - Test účtenky hrazené soukromě vytvoří závazek vůči zvolené osobě, ne vůči dodavateli
  zavisi_na: [A05, A15]
  odhad: M
  rozhoduje: agent
  riziko: Změna číslování po zaúčtování by porušila návaznost; poznáme podle reportu návaznosti v produkci.

- id: A17
  priorita: P0
  oblast: účetnictví Services
  typ: kód
  nazev: DPH identifikované osoby v dokladech a přiznání
  popis: U přijatého dokladu od zahraničního dodavatele služby systém navrhne daň identifikované osoby i na prázdném řádku, potvrzení bez daně zastaví s vysvětlením (nebo vyžádá schválenou výjimku) a přiznání nebude obsahovat odpočet. Přibude hlídání obratu pro povinnou registraci s nastavitelným limitem.
  dotcene_casti:
    - investra_vat_identified
  akceptace:
    - Test služby z EU se sazbou 21 % skončí v řádku přiznání pro přijetí služby od osoby registrované v jiném členském státě
    - Test služby ze třetí země skončí v řádku pro ostatní plnění s povinností přiznat daň
    - Řádky odpočtu 43 a 44 jsou vždy nula
    - Potvrzení zahraniční služby bez daně skončí chybou s vysvětlením
    - Tuzemský dodavatel daň identifikované osoby nedostane
  zavisi_na: [A15]
  odhad: M
  rozhoduje: agent
  riziko: Postup ještě nepotvrdil daňový poradce (A49); poznáme podle změn po jeho vyjádření.

- id: A18
  priorita: P0
  oblast: účetnictví Services
  typ: kód
  nazev: Účetní sestavy v nabídce
  popis: Předvaha, hlavní kniha, saldokonto, rozvaha a výsledovka v členění podle vyhlášky 500 pro Services s exportem do XLSX; předvaha a hlavní kniha slouží i knihám fondů. V Enterprise konfigurací výkazů, v Community vlastním vývojem nebo modulem OCA (odhad pak L).
  dotcene_casti:
    - docs/sql/
    - modul sestav (nový)
  akceptace:
    - Předvaha se na stejných datech shoduje s dotazy v docs/sql/
    - Rozvaha bilancuje a výsledek se rovná zůstatku účtu 431
    - Sestavy jsou dostupné z nabídky bez SQL
  zavisi_na: [A02, A15]
  odhad: M
  rozhoduje: agent
  riziko: Členění rozvahy podle vyhlášky 500 nemusí být v lokalizaci; poznáme v A01.

- id: A19
  priorita: P0
  oblast: účetnictví Services
  typ: kód
  nazev: Import bankovních výpisů a návrh párování
  popis: Import výpisů přes profily formátů, návrh spárování s fakturami a platbami a potvrzení účetní; společný základ i pro banku fondů (A32). Provozní banka Services bude Fio (P); první profil bude pro Fio a vhodný formát výpisu nebo API Fio se ověří na začátku kroku. Kontrola konečného zůstatku, návaznosti výpisů a duplicitního importu.
  dotcene_casti:
    - modul bankovních výpisů (nový)
  akceptace:
    - Testy nad syntetickými výpisy ve formátu banky Services naimportují pohyby a konečný zůstatek sedí
    - Druhý import stejného výpisu je odmítnutý
    - Navržené spárování se zaúčtuje až po potvrzení účetní
  zavisi_na: [A02, A15]
  odhad: M
  rozhoduje: agent
  riziko: Formát GPC v Enterprise pravděpodobně chybí; poznáme v A01.

- id: A20
  priorita: P0
  oblast: účetnictví Services
  typ: dokumentace
  nazev: Zadat doklady Services do produkce a odsouhlasit
  popis: Metodik zadá doklady od 19. 3. 2026 do produkce s opravami podle A05, přiloží PDF a odsouhlasí předvahu s investra_dev upravenou o schválené opravy. Zkušební měsíc do 18. 12. 2026, ostrý start 4. 1. 2027.
  dotcene_casti:
    - produkční databáze Services (nový)
  akceptace:
    - Předvaha produkce se shoduje s předvahou investra_dev po schválených opravách
    - Každý doklad má PDF a čísla vydaných faktur sedí s doklady
  zavisi_na: [A13, A14, A16, A17]
  odhad: M
  rozhoduje: člověk
  riziko: Zadávání v prosinci soupeří s vývojem pro fondy; poznáme podle skluzu brány 18. 12. 2026.

- id: A21
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Porovnání s nezávislým výpočtem NAV v testech
  popis: Testy načtou vstupy a očekávané výsledky (NAV, kurz třídy, úplaty, performance fee) ze souboru od nezávislé osoby z A06 a porovnají je s výpočtem v Odoo bez tolerance kromě dohodnutého zaokrouhlení.
  dotcene_casti:
    - investra_nav
    - referenční výpočet NAV mimo Odoo
  akceptace:
    - Prochází alespoň tři scénáře včetně performance fee a třídy v EUR
    - Očekávané hodnoty nevytvořil agent ani kód a soubor nese autora a datum
    - Rozdíl v jediném čísle test zastaví a ukáže položku
  zavisi_na: [A06, A11]
  odhad: S
  rozhoduje: agent
  riziko: Nezávislá osoba může převzít předpoklady autora; poznáme podle toho, zda scénáře vycházejí ze statutu, ne z kódu.

- id: A22
  priorita: P0
  oblast: architektura
  typ: kód
  nazev: Klasifikace IFRS 9 na úrovni fondu a oddělení sdílených dat
  popis: Metodik potvrdil, že jeden nástroj může mít v různých fondech různou klasifikaci a že reklasifikace může nastat. Oddělit sdílený kmen nástroje (ISIN, typ, emitent, tržní cena z veřejného zdroje) od dat knihy (pozice, klasifikace podle IFRS 9 s platností od, cena z posudku nebo modelu), přesunout klasifikaci na vztah fond–nástroj, upravit výpočty, které ji čtou, a zapsat změnu rozhodnutí o IFRS 9 do deníku rozhodnutí.
  dotcene_casti:
    - investra_instruments
    - investra_counterparty
    - investra_nav
    - investra_posting
    - docs/rozhodnuti.md
  akceptace:
    - Tabulka polí s vlastníkem (sdílené, kniha) schválená metodikem
    - Tentýž syntetický nástroj má ve dvou fondech různou klasifikaci a ocenění i zaúčtování každého fondu se řídí jeho klasifikací
    - Klasifikace má platnost od a po prvním obchodu ji změní jen řízená reklasifikace (A74), jiná změna je odmítnutá
    - Seznam míst, kde se sdílená data mění bez kontroly oprávnění, je předaný do A23
    - Všechny dosavadní testy po přesunu procházejí
  zavisi_na: [A11]
  odhad: M
  rozhoduje: agent
  riziko: Klasifikaci může číst víc míst, než se čeká, a odhad pak vzroste na L; poznáme ze seznamu míst na začátku práce.

- id: A23
  priorita: P0
  oblast: bezpečnost
  typ: kód
  nazev: Uzavřít otevřené bezpečnostní nálezy
  popis: Sdílené nástroje mění jen oprávněné role podle A22, nezaúčtované návrhy obchodů se nepočítají do pozic, zaúčtovanou splátku nejde změnit a balíček pro depozitáře neobsahuje vzorce. Ke každému nálezu test.
  dotcene_casti:
    - investra_instruments
    - investra_nav
  akceptace:
    - Uživatel bez oprávnění ke knize neupraví sdílený nástroj ani data cizí knihy
    - Pozice ignoruje nezaúčtovaný návrh obchodu
    - Zaúčtovanou splátku jde jen stornovat
    - Excel pro depozitáře obsahuje jen hodnoty
  zavisi_na: [A11, A22]
  odhad: M
  rozhoduje: agent
  riziko: Zpřísnění oprávnění může rozbít dosavadní testovací scénáře; poznáme podle selhání testů po změně.

- id: A24
  priorita: P0
  oblast: UI
  typ: obrazovka
  nazev: Jedna aplikace Investra s českými popisky a ukázkovými daty
  popis: Fondové funkce a účetní funkce pro fondy v jedné aplikaci s nabídkou podle práce (Můj den, Ocenění, Ceny, Schvalování, Fondy, Účetnictví fondů, Výkazy ČNB, Services), české popisky a ukázková data v investra_test pro každý seznam.
  dotcene_casti:
    - investra_dashboard
    - investra_nav
    - investra_fund
    - investra_instruments
    - investra_fx_revaluation
  akceptace:
    - Uživatel ocení fond bez přechodu do aplikace Fakturace
    - Kontrola překladů nenajde anglický popisek ve fondových obrazovkách
    - Žádný seznam v nabídce není v testovací databázi prázdný
  zavisi_na: [A75]
  odhad: M
  rozhoduje: agent
  riziko: Přesun položek nabídky může rozbít odkazy; poznáme podle testů nabídek.

- id: A25
  priorita: P0
  oblast: UI
  typ: dokumentace
  nazev: Provést první kolo uživatelského testu
  popis: Obě účetní projdou podle scénářů ocenění, ceny a přehled v investra_test, měří se čas, počet kliknutí a přepnutí společnosti a zapisují se nálezy. Začít od 7. 12. 2026.
  dotcene_casti:
    - protokol uživatelského testu (nový)
  akceptace:
    - Protokol s naměřeným časem, počtem kliknutí a nálezy seřazenými podle závažnosti
    - Nálezy jsou převedené do kroků akčního plánu
  zavisi_na: [A24]
  odhad: S
  rozhoduje: člověk
  riziko: Účetní nemusí mít v prosinci čas; poznáme podle posunu termínu testu.

- id: A26
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Peněžní toky nástrojů jádra
  popis: Události kupón, dividenda (nárok k rozhodnému dni, výplata, srážková daň s nastavitelnou sazbou), poplatek obchodu (podle klasifikace v daném fondu u FVTPL do nákladů, u naběhlé hodnoty do pořizovací ceny), splátka jistiny a umoření, úrok úvěru SPV a příplatek mimo základní kapitál. Každá událost vytvoří zápis přes účtovací modul podle pravidla a jde stornovat; dluhové nástroje sdílejí jeden model peněžních toků.
  dotcene_casti:
    - investra_instruments
    - investra_posting
    - investra_nav
  akceptace:
    - Pro každou událost test zápisu, storna a vlivu na pozici a NAV
    - Nárok po rozhodném dni bez výplaty po splatnosti se ukáže v kontrole kroku 6
    - Scénář s kupónem a dividendou se shoduje s nezávislým výpočtem z A21
    - Pozice se po každé události rovnají hlavní knize
  zavisi_na: [A08, A21, A22, A23]
  odhad: L
  rozhoduje: agent
  riziko: Účtovací pravidla jednotlivých událostí potvrdí metodik a auditor; poznáme podle změn pravidel po jejich revizi.

- id: A27
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Dohadné položky, úplaty k úhradě a daň fondu
  popis: Dohady na audit, depozitáře, administraci a znalce podle parametrů fondu, jejich rozpuštění přijatou fakturou podle A07, úplaty k úhradě a daň z příjmů fondu (splatná, případně odložená) jako parametr. Sazbu a postup daně potvrdí daňový poradce.
  dotcene_casti:
    - investra_nav
    - investra_posting
  akceptace:
    - Dohad rozpuštěný fakturou nezdvojí náklad
    - Daň se počítá podle parametru fondu a je vidět v přemostění FK
    - Ocenění bez dohadu povinné položky skončí upozorněním
  zavisi_na: [A07, A21]
  odhad: M
  rozhoduje: agent
  riziko: Pořadí úplat a daně se liší podle statutu; poznáme podle scénáře se dvěma různými statuty.

- id: A28
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Upisovací závazek ostatního podílu
  popis: Výzva ke splacení, splacení, distribuce s rozlišením vrácení kapitálu a výnosu, evidence nesplaceného závazku mimo rozvahu a ocenění zadanou hodnotou pozice s datem a podkladem.
  dotcene_casti:
    - investra_instruments
    - investra_posting
  akceptace:
    - Test celého životního cyklu podílu od závazku po distribuci
    - Nesplacený závazek je vidět v přehledu pozic a v podkladu pro výkazy
  zavisi_na: [A26]
  odhad: M
  rozhoduje: agent
  riziko: Rozlišení vrácení kapitálu a výnosu závisí na podkladech správce podkladového fondu; poznáme podle distribucí bez rozpadu.

- id: A29
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Funkční měna EUR v celém cyklu
  popis: Fond s funkční měnou EUR, třídami v CZK a EUR, kurzy ECB v účetnictví, přeceněním cizích měn a zveřejněním kurzu třídy v CZK. Kurz ECB platí jen v účetnictví; výkazy ČNB jsou vždy v CZK a přepočítávají se z EUR kurzem ČNB (A39), jak potvrdil metodik podle legislativy.
  dotcene_casti:
    - investra_fund
    - investra_rates
    - investra_fx_revaluation
  akceptace:
    - Scénář fondu v EUR se shoduje s nezávislým výpočtem
    - Součet tříd se rovná FK a pozice hlavní knize i v EUR
    - Účetní doklady fondu v EUR používají jen kurzy ECB a každý nese zdroj a datum kurzu
  zavisi_na: [A21]
  odhad: M
  rozhoduje: agent
  riziko: Záměna zdroje kurzu mezi účetnictvím a výkazy ČNB; poznáme kontrolou zdroje kurzu u každého dokladu a přepočtu.

- id: A30
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Univerzální import a schválení cen
  popis: Import cen přes profily formátů (Excel z Bloombergu, další zdroje), náhled s chybami, příloha zdrojového souboru, kontroly a hromadné schválení bez výjimek podle obrazovky O2. Sdílená cena z veřejného zdroje se schvaluje jednou, cena z posudku nebo modelu v knize.
  dotcene_casti:
    - investra_instruments
  akceptace:
    - Import 200 syntetických cen s chybami ukáže neznámý identifikátor, duplicitu, skok nad práh a jinou měnu
    - Hromadné schválení vynechá výjimky
    - Zadavatel nemůže schválit vlastní cenu ani hromadně
  zavisi_na: [A23]
  odhad: M
  rozhoduje: agent
  riziko: Licence Bloomberg může omezit sdílení cen mezi fondy; poznáme z ověření licence vedoucím.

- id: A31
  priorita: P0
  oblast: IS
  typ: kód
  nazev: Souborové rozhraní IS a simulátor
  popis: Devět verzovaných zpráv podle pracovního návrhu, každá s jednoznačným ID, pořadím a schématem; zpracování je idempotentní a storno v IS vyvolá storno v Odoo. Kontroly navázání závěrek, ceny úpisu proti kurzu a kusů proti účetnictví. Simulátor generuje syntetické zprávy a validace odmítne pole vyloučená v A09.
  dotcene_casti:
    - investra_fund
    - investra_nav
    - rozhraní IS (nový)
  akceptace:
    - Stejná zpráva zpracovaná dvakrát nic nezdvojí
    - Závěrka, která nenavazuje na předchozí, je odmítnutá s vysvětlením
    - Zpráva s nepovoleným polem je odmítnutá
    - Simulátor vytvoří závěrky pro tři třídy a ocenění je zpracuje
  zavisi_na: [A09]
  odhad: L
  rozhoduje: agent
  riziko: Skutečný IS může mít jiný model než pracovní návrh; poznáme při první schůzce s dodavatelem IS a změna má být jen novou verzí zprávy.

- id: A32
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Banka fondu a párování úpisů a odkupů
  popis: Import výpisů fondu na základu z A19, párování úpisů a odkupů přes identifikátory z IS, úhrady úplat a faktur a ochrana údajů o investorech podle A09. Cesta úpisů (účet fondu, nebo sběrný účet se souhrnnou platbou) je parametr fondu a výplaty investorům zadává IS. Kontrola zůstatku banky proti výpisu a účtů úpisů a odkupů proti závazkům k držitelům v kroku 6.
  dotcene_casti:
    - investra_nav
    - modul bankovních výpisů (nový)
  akceptace:
    - Syntetický výpis se spáruje s identifikátory ze simulátoru IS
    - Uložené řádky výpisu neobsahují pole vyloučená v A09
    - Nespárovaná platba úpisu se ukáže jako upozornění v ocenění
    - Výplata odkupu zadaná v IS se spáruje přes identifikátor bez čísla účtu investora
    - Obě cesty úpisů fungují podle parametru fondu
  zavisi_na: [A09, A19, A31]
  odhad: M
  rozhoduje: agent
  riziko: Banky fondů nejsou známé a formát se může lišit; poznáme při prvním skutečném výpisu, změna má být jen novým profilem.

- id: A33
  priorita: P0
  oblast: ocenění
  typ: analýza
  nazev: Specifikovat formát převzetí a pravidla pro chybějící údaje
  popis: Popsat společný vstupní formát (osnova, předvaha, otevřené položky, pozice s pořizovací cenou a kurzem, třídy, kusy, historie NAV, high-water mark, hurdle, atributy pro výkazy), kontroly a návrh pravidel pro chybějící údaje podle kapitoly 2.3 revize.
  dotcene_casti:
    - docs/pruzkum/
    - specifikace převzetí (nový)
  akceptace:
    - Schéma formátu s povinnými a volitelnými poli a příkladem se syntetickými daty
    - Ke každému volitelnému údaji je pravidlo pro případ, že chybí
  zavisi_na: []
  odhad: M
  rozhoduje: agent
  riziko: Skutečný zdroj může mít údaje, které formát nezná; poznáme u prvního převzetí a formát rozšíříme verzí.

- id: A34
  priorita: P0
  oblast: ocenění
  typ: rozhodnutí
  nazev: Schválit metodiku chybějících údajů při převzetí (R11)
  popis: Metodik schválí pravidla z A33 a nechá je potvrdit auditorem, zejména pořizovací kurz, high-water mark a historii NAV.
  dotcene_casti:
    - docs/rozhodnuti.md
    - specifikace převzetí (nový)
  akceptace:
    - Zápis v deníku rozhodnutí s vyjádřením auditora
  zavisi_na: [A33]
  odhad: S
  rozhoduje: člověk
  riziko: Auditor může požadovat historii, kterou předchozí administrátor nemá; poznáme z jeho vyjádření.

- id: A35
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Převzetí fondu
  popis: Průvodce převzetím podle obrazovky O9 s převodníkem pro první zdroj, kontrolami podle postupu převzetí a příznakem převzato bez historie; převzetí jde přerušit a pokračovat.
  dotcene_casti:
    - investra_entity
    - investra_chart_fund
    - investra_instruments
    - modul převzetí (nový)
  akceptace:
    - Syntetický fond převzatý ze vzorového souboru má předvahu, otevřené položky, pozice a kusy shodné se zdrojem
    - FK se ke dni převzetí zreprodukuje
    - Chybějící údaj se řeší podle schváleného pravidla a je označený
  zavisi_na: [A26, A29, A34]
  odhad: L
  rozhoduje: agent
  riziko: První skutečný zdroj bude mít jiný tvar než vzor; poznáme při prvním převzetí a řeší se novým převodníkem, ne změnou jádra.

- id: A36
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Balíček pro depozitáře, stanovisko a porovnání
  popis: Balíček ve strojově čitelné podobě (CSV nebo JSON) a v XLSX bez vzorců s kontrolním součtem a listy portfolio, NAV, předvaha a úplaty, evidence stanoviska depozitáře a import výsledku depozitáře s porovnáním a tolerancí.
  dotcene_casti:
    - investra_nav
  akceptace:
    - Kontrolní součet balíčku sedí po opětovném načtení
    - Rozdíl proti výsledku depozitáře nad toleranci zastaví zveřejnění
    - Vrácení depozitářem stornuje doklady a vytvoří novou verzi ocenění
  zavisi_na: [A23]
  odhad: M
  rozhoduje: agent
  riziko: Depozitář může vyžadovat vlastní formát; poznáme při prvním jednání a řeší se novým profilem exportu.

- id: A37
  priorita: P0
  oblast: výkazy ČNB
  typ: analýza
  nazev: Zmapovat pět výkazů ČNB na data
  popis: Pro RISIFI30, RISIFI33, TISIFI10, VISIFI10 a RISIFI37 podle metodiky FOFI20261201 určit ke každé položce zdroj (role účtu, nástroj, protistrana, agregace z IS), chybějící atributy a závažné kontroly a navázat na převodovou tabulku v investra_cnb. U fondů s funkční měnou EUR určit pravidlo přepočtu z EUR do CZK kurzem ČNB včetně data kurzu podle metodiky.
  dotcene_casti:
    - investra_cnb
    - investra_counterparty
  akceptace:
    - Tabulka položek se zdrojem a stavem (dostupné, chybí, ručně)
    - Seznam mezer s odhadem a návrhem řešení
  zavisi_na: []
  odhad: M
  rozhoduje: agent
  riziko: Metodiky od 2027 se mění; poznáme podle verze metodiky v tabulce a převody musí mít platnost od.

- id: A38
  priorita: P0
  oblast: výkazy ČNB
  typ: rozhodnutí
  nazev: Rozhodnout cestu výkazů ČNB pro první období (R9)
  popis: Vybrat mezi výkazy jen z Odoo, výkazy z Odoo se záložním exportem do šablony a externím nástrojem. Revize doporučuje Odoo se záložní šablonou pro první jedno až dvě období s povinným zdůvodněním ručního zásahu.
  dotcene_casti:
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí s pravidly pro použití záložní cesty
  zavisi_na: [A37]
  odhad: S
  rozhoduje: člověk
  riziko: Záložní cesta se může stát trvalou; poznáme podle počtu období se záložním exportem.

- id: A39
  priorita: P0
  oblast: výkazy ČNB
  typ: kód
  nazev: Pět výkazů ČNB s kontrolami a exportem
  popis: Snímek dat k ocenění, výpočet pěti výkazů, závažné kontroly, export souboru pro SDAT, záložní export do šablony se zdůvodněním a rozpad každé hodnoty na zdroj podle obrazovky O8. Odesílá a podepisuje člověk.
  dotcene_casti:
    - investra_cnb
    - investra_dashboard
  akceptace:
    - Výkazy syntetického fondu projdou závažnými kontrolami bez ruční úpravy
    - Každou hodnotu jde rozpadnout na účty, nástroje nebo protistrany
    - U fondu s funkční měnou EUR jsou všechny částky výkazu v CZK přepočtené kurzem ČNB a každý přepočet nese kurz, datum a zdroj
    - Chybějící kurz ČNB k datu přepočtu zastaví export
    - Opravný výkaz vznikne jako nová verze
  zavisi_na: [A26, A29, A31, A37, A38]
  odhad: L
  rozhoduje: agent
  riziko: Formát souboru pro SDAT se může lišit od předpokladu; poznáme při prvním zkušebním nahrání člověkem.

- id: A40
  priorita: P0
  oblast: ocenění
  typ: kód
  nazev: Schvalovací matice, zastupování a schvalování změn parametrů
  popis: Matice z A10 jako parametr fondu s platností od, delegace zastupování s obdobím a rozsahem, zákaz schválení sebe sama i v zastoupení a schvalování změn parametrů fondu (úplaty, alokace, mapování rolí) druhou osobou.
  dotcene_casti:
    - investra_entity
    - investra_fund
    - investra_allocation
    - investra_nav
  akceptace:
    - Zadavatel, který schvaluje vlastní záznam v zastoupení, skončí chybou
    - Schválení v zastoupení zapíše, za koho bylo provedeno
    - Změna parametru úplaty platí až po schválení a je verzovaná
    - U fondu cizího obhospodařovatele nejde ocenění schválit bez přiloženého písemného schválení, které zaeviduje jiná osoba než zadavatel
  zavisi_na: [A10]
  odhad: M
  rozhoduje: agent
  riziko: Starší cesty schválení mohou matici obejít; poznáme testem, který zkouší schválení přes všechny akce a kontexty volání.

- id: A41
  priorita: P0
  oblast: UI
  typ: obrazovka
  nazev: Fronta ke schválení a zastupování (O4)
  popis: Jedna fronta napříč knihami pro ceny, ocenění, ruční úpravy, ruční kurzy, převzetí a změny parametrů; hromadné schválení jen pro položky stejného druhu bez výjimek, ocenění vždy jednotlivě.
  dotcene_casti:
    - investra_dashboard
    - fronta ke schválení (nový)
  akceptace:
    - Schvalovatel vidí položky všech knih, ke kterým má oprávnění, bez přepnutí společnosti
    - Hromadné schválení vynechá položky s výjimkou
    - Prázdná fronta ukáže poslední vyřízenou položku
  zavisi_na: [A40]
  odhad: M
  rozhoduje: agent
  riziko: Fronta může ukázat záznam knihy bez oprávnění; poznáme testem uživatele s omezenými knihami.

- id: A42
  priorita: P0
  oblast: UI
  typ: obrazovka
  nazev: Ocenění fondu jako průvodce (O1)
  popis: Formulář ocenění s kroky 0 až 11, stavem a výsledkem kontroly u každého kroku, souhrnem NAV a tříd a jedním hlavním tlačítkem; varování s akcí, která otevře příčinu. Záložka Třídy přebírá z návrhu vedoucího přemostění kapitálu po třídách (FK minulého období, úpisy, odkupy, dividendy, výsledek, performance alokace, FK, kusy, kurz). Bez vlastního JavaScriptu.
  dotcene_casti:
    - investra_nav
  akceptace:
    - Ocenění syntetického fondu od importu cen po zveřejnění proběhne bez přepnutí společnosti a bez odchodu z aplikace
    - Od importu cen po odeslání ke schválení stačí nejvýš 35 kliknutí
    - Každý stop má odkaz na příčinu
    - Záložka Třídy ukazuje přemostění kapitálu po třídách s kontrolním řádkem a vejde se na šířku obrazovky bez posuvníku
  zavisi_na: [A26, A27, A40, A75]
  odhad: M
  rozhoduje: agent
  riziko: Standardní formulář může být pro 12 kroků nepřehledný; poznáme ve druhém kole testu a pak zvážíme A73.

- id: A43
  priorita: P0
  oblast: UI
  typ: obrazovka
  nazev: Přehled fondů napříč knihami (O3)
  popis: Kanban, seznam, pivot a kalendář nad uloženým stavovým snímkem fondu; data podle oprávnění uživatele ke knihám, ne podle aktivních společností v přepínači. Rozšiřuje investra_dashboard.
  dotcene_casti:
    - investra_dashboard
  akceptace:
    - Uživatel s oprávněním ke 30 knihám a jednou aktivní společností vidí 30 fondů
    - Uživatel bez oprávnění ke knize ji nevidí ani ve vyhledávání a exportu
    - Přehled 30 fondů se otevře do 3 sekund
  zavisi_na: [A23]
  odhad: M
  rozhoduje: agent
  riziko: Čtení napříč knihami může obejít přístupová pravidla; poznáme testem oprávnění a bezpečnostní revizí.

- id: A44
  priorita: P0
  oblast: architektura
  typ: rozhodnutí
  nazev: Definovat ostrý provoz bránou a zmrazit rozsah (R13)
  popis: Na bráně 22. 1. 2027 potvrdit, že ostrý provoz prvního fondu nastane po splnění akceptace přechodu (dvě po sobě souhlasná paralelní ocenění, zkušební výkazy bez ruční úpravy, test obnovy), a zmrazit rozsah; rozšíření přesunout za ostrý provoz. Bránu přechodu přesunout z 26. 3. (Velký pátek) na 25. 3. 2027.
  dotcene_casti:
    - docs/harmonogram.md
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí a aktualizovaný harmonogram
  zavisi_na: [A21, A25]
  odhad: S
  rozhoduje: člověk
  riziko: Tlak na datum povede k přechodu bez splněné akceptace; poznáme podle nesplněných bodů C.1 v zápisu o přechodu.

- id: A45
  priorita: P0
  oblast: UI
  typ: dokumentace
  nazev: Provést druhé kolo uživatelského testu
  popis: Obě účetní a schvalovatel projdou nové obrazovky O1, O3 a O4 podle scénářů včetně zastoupení a porovnají kliknutí a čas s prvním kolem.
  dotcene_casti:
    - protokol uživatelského testu (nový)
  akceptace:
    - Protokol s porovnáním proti prvnímu kolu
    - Žádný otevřený nález s blokující závažností
  zavisi_na: [A41, A42, A43]
  odhad: S
  rozhoduje: člověk
  riziko: Test pozdě před zkušebním provozem nechá málo času na opravy; poznáme podle data testu po 26. 2. 2027.

- id: A46
  priorita: P1
  oblast: účetnictví Services
  typ: obrazovka
  nazev: Přijatá faktura z PDF (O5)
  popis: Vstup přes e-mailový alias deníku nebo přetažení PDF, náhled PDF vedle formuláře, předvyplnění z historie dodavatele, volba kdo hradil, návrh daně identifikované osoby a kontroly podle obrazovky O5.
  dotcene_casti:
    - investra_vat_identified
    - modul nastavení Services (nový)
  akceptace:
    - Zadání syntetické faktury zahraničního dodavatele trvá v testu nejvýš 2 minuty a nejvýš 12 kliknutí
    - Duplicitní číslo faktury dodavatele je zastavené
    - DUZP v uzamčeném období je zastavené
  zavisi_na: [A16, A17]
  odhad: M
  rozhoduje: agent
  riziko: Náhled PDF vedle formuláře nemusí v Odoo 20 fungovat jako dřív; poznáme v A01.

- id: A47
  priorita: P1
  oblast: účetnictví Services
  typ: obrazovka
  nazev: Přehled DPH identifikované osoby (O6)
  popis: Přehled za období s kontrolami, výjimkami, souhrnem pro přiznání, exportem podkladu a záložkou zpětné kontroly podle obrazovky O6.
  dotcene_casti:
    - investra_vat_identified
  akceptace:
    - Zahraniční služba bez daně v období se ukáže jako upozornění
    - Součty přehledu se shodují s řádky přiznání
    - Uzavřené období nejde měnit
  zavisi_na: [A17]
  odhad: M
  rozhoduje: agent
  riziko: Čísla řádků přiznání se mohou změnit s novým tiskopisem; poznáme při kontrole poradcem v A49.

- id: A48
  priorita: P1
  oblast: účetnictví Services
  typ: analýza
  nazev: Zpětně zkontrolovat zahraniční služby od 19. 3. 2026
  popis: Sestavit po měsících seznam dokladů od zahraničních dodavatelů s údajem, zda mají daň identifikované osoby, jako podklad pro daňového poradce. Pracuje jen s údaji dokladů v Odoo, ne s jejich přílohami.
  dotcene_casti:
    - investra_vat_identified
  akceptace:
    - Seznam pokrývá všechny měsíce od března 2026 a každý zahraniční doklad
  zavisi_na: [A17]
  odhad: S
  rozhoduje: agent
  riziko: Služby zaplacené kartou bez dokladu v Odoo seznam nezachytí; poznáme porovnáním s výpisy z karet, které provede člověk.

- id: A49
  priorita: P1
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Potvrdit postup DPH identifikované osoby u daňového poradce
  popis: Daňový poradce posoudí zaúčtování, řádky přiznání, výsledek zpětné kontroly z A48, povinnost souhrnného a kontrolního hlášení a sledování hranice pro povinnou registraci.
  dotcene_casti:
    - docs/osnova-revize-podklad.md
    - docs/rozhodnuti.md
  akceptace:
    - Písemné vyjádření poradce je založené a odchylky jsou převedené do kroků
  zavisi_na: [A48]
  odhad: S
  rozhoduje: člověk
  riziko: Zjištěné nepřiznané období znamená dodatečné přiznání; poznáme z vyjádření poradce.

- id: A50
  priorita: P1
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Rozhodnout čtyři oči u Services (R4)
  popis: Revize doporučuje čtyři oči jen u plateb a ručních zápisů do uzavřeného období a měsíční kontrolu jednatelem, dokud účetnictví Services vede jedna osoba.
  dotcene_casti:
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí a promítnutí do matice z A10
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez rozhodnutí zůstanou platby Services bez kontroly; poznáme podle plateb bez druhého podpisu.

- id: A51
  priorita: P1
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Rozhodnout uzávěrku bez účtů 701, 702 a 710 (R15)
  popis: Auditor posoudí, zda uzavření knih nevratným zámkem a výsledkem na účtu 431 bez uzávěrkových zápisů splňuje požadavky na uzavření a otevření účetních knih. Termín 15. 1. 2027, před první roční uzávěrkou.
  dotcene_casti:
    - docs/osnova-revize-podklad.md
    - docs/rozhodnuti.md
  akceptace:
    - Vyjádření auditora a zápis v deníku rozhodnutí
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Pozdní nesouhlas auditora vynutí opravu po uzávěrce; poznáme podle data vyjádření po 15. 1. 2027.

- id: A52
  priorita: P1
  oblast: účetnictví Services
  typ: kód
  nazev: Podpora roční uzávěrky 2026
  popis: Kontrolní seznam uzávěrky (časové rozlišení, dohady, přecenění cizích měn k 31. 12., odsouhlasení saldokont, rozdělení výsledku), nevratný zámek a případně uzávěrkové a otevírací zápisy podle A51. První účetní období Services začalo 19. 3. 2026. Daňové přiznání se podává v běžné lhůtě (P), proto uzávěrku dokončit do 26. 2. 2027, před zkušebním provozem fondu; lhůtu potvrdí daňový poradce.
  dotcene_casti:
    - investra_fx_revaluation
    - modul sestav (nový)
  akceptace:
    - Kontrolní seznam nejde uzavřít s nesplněnou položkou
    - Počáteční stavy roku 2027 se rovnají konečným stavům roku 2026
  zavisi_na: [A18, A51]
  odhad: M
  rozhoduje: agent
  riziko: Uzávěrka soupeří o kapacitu s fondy v lednu a únoru; poznáme podle skluzu kroků P0 nebo termínu 26. 2. 2027.

- id: A53
  priorita: P1
  oblast: účetnictví Services
  typ: kód
  nazev: Časové rozlišení
  popis: Rozpouštění nákladů a výnosů příštích období podle edice (standard Enterprise, nebo jednoduchý průvodce v Community) s návrhem dokladů ke schválení.
  dotcene_casti:
    - modul nastavení Services (nový)
  akceptace:
    - Předplatné na 12 měsíců vytvoří 12 návrhů a jejich součet se rovná faktuře
  zavisi_na: [A02]
  odhad: S
  rozhoduje: agent
  riziko: Ruční časové rozlišení z roku 2026 se může zdvojit; poznáme kontrolou zůstatků účtů časového rozlišení.

- id: A54
  priorita: P1
  oblast: architektura
  typ: kód
  nazev: Šablona knihy, průvodce založením a přehled odchylek
  popis: Verzovaná šablona nastavení knihy (osnova nebo mapování rolí, deníky, daně, číselné řady, parametry), průvodce založením knihy fondu, podfondu nebo SICAV a přehled odchylek každé knihy od šablony.
  dotcene_casti:
    - investra_entity
    - investra_chart_fund
  akceptace:
    - Kniha založená průvodcem projde kontrolou úplnosti bez ručního doplnění
    - Ručně změněné nastavení knihy se objeví v přehledu odchylek
    - Účet se zůstatkem bez role zastaví ocenění
  zavisi_na: [A07, A22]
  odhad: M
  rozhoduje: agent
  riziko: Převzaté fondy s vlastní osnovou se šabloně vymykají; poznáme v přehledu odchylek a řeší se mapováním rolí, ne výjimkou v kódu.

- id: A55
  priorita: P1
  oblast: architektura
  typ: kód
  nazev: Export knihy čitelný bez Odoo
  popis: Export jedné knihy (předvaha, doklady s řádky, přílohy, pozice, ocenění, schválení) do otevřených formátů s popisem struktury pro archivaci a pro dohledání dat po obnově.
  dotcene_casti:
    - investra_entity
    - investra_nav
  akceptace:
    - Export syntetické knihy jde otevřít bez Odoo a součty sedí s předvahou
    - U každého ocenění export obsahuje zadavatele, schvalovatele a použité ceny a kurzy
  zavisi_na: [A22]
  odhad: M
  rozhoduje: agent
  riziko: Export může obsahovat údaje, které do archivu nepatří; poznáme kontrolou polí proti pravidlům archivace.

- id: A56
  priorita: P1
  oblast: ocenění
  typ: dokumentace
  nazev: Zapsat rozhodnutí o performance fee po třídě
  popis: Metodik rozhodl 8. 11. 2026, že performance fee se počítá jen po třídě fondu (high-water mark a hurdle za třídu); série a vyrovnání (equalisation) nejsou v rozsahu. Zapsat rozhodnutí do deníku a ověřit, že výpočet a testy pokrývají performance fee po třídě včetně třídy v EUR.
  dotcene_casti:
    - investra_nav
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí s datem a důvodem
    - Testy pokrývají high-water mark, hurdle a třídu v EUR na úrovni třídy
  zavisi_na: []
  odhad: S
  rozhoduje: agent
  riziko: Převzatý fond se sériemi nebo vyrovnáním by potřeboval nový krok; poznáme při prověrce statutu před převzetím.

- id: A57
  priorita: P1
  oblast: provoz
  typ: analýza
  nazev: Test na objemu
  popis: Syntetická data 30 knih po 50 nástrojích, 24 ocenění a 3 třídách a dva roky dokladů; změřit přehled fondů, výpočet ocenění, frontu a výkazy.
  dotcene_casti:
    - investra_dashboard
    - investra_nav
  akceptace:
    - Přehled fondů do 3 sekund a výpočet ocenění fondu do 60 sekund, jinak seznam úzkých míst s návrhem
  zavisi_na: [A42, A43]
  odhad: M
  rozhoduje: agent
  riziko: Testovací stroj neodpovídá produkci; poznáme opakováním měření na produkčním prostředí před přechodem.

- id: A58
  priorita: P1
  oblast: bezpečnost
  typ: dokumentace
  nazev: Připravit dokumentaci podle DORA
  popis: Evidence ICT dodavatelů (hosting, Odoo, Bloomberg, případně služba vytěžování), plán kontinuity a obnovy, postup hlášení incidentů a smluvní náležitosti pro případ, že Services bude dodavatelem ICT služeb obhospodařovatele. Rozsah povinností ověří právník.
  dotcene_casti:
    - docs/otevrene-body.md
    - provozní příručka (nový)
  akceptace:
    - Evidence je úplná vůči seznamu dodavatelů z provozní příručky
    - Plán obnovy odkazuje na protokol testu obnovy z A13
  zavisi_na: [A03]
  odhad: M
  rozhoduje: člověk
  riziko: Rozsah povinností se může ukázat širší, než se čeká; poznáme z vyjádření právníka.

- id: A59
  priorita: P1
  oblast: provoz
  typ: rozhodnutí
  nazev: Zajistit revizi kódu a zastupování vývojáře (R14)
  popis: Revize doporučuje smlouvu s partnerem Odoo na revizi kritických modulů (účtovací modul, NAV, úplaty) a na zastupování při výpadku vlastníka projektu.
  dotcene_casti:
    - docs/rozhodnuti.md
    - investra_posting
    - investra_nav
  akceptace:
    - Podepsaná smlouva, nebo zdůvodněné rozhodnutí ji neuzavřít, v deníku rozhodnutí
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Bez zastupování zastaví výpadek vlastníka provoz i vývoj; poznáme podle toho, že nikdo jiný neumí nasadit opravu.

- id: A60
  priorita: P1
  oblast: ocenění
  typ: dokumentace
  nazev: Napsat manuál ocenění
  popis: Manuál pro účetní a schvalovatele po krocích obrazovek O1 až O4 včetně zastoupení, výjimek a vrácení depozitářem, se snímky ze syntetických dat.
  dotcene_casti:
    - manuál ocenění (nový)
  akceptace:
    - Druhá účetní provede ocenění podle manuálu bez pomoci (ověří se ve zkušebním provozu)
  zavisi_na: [A41, A42]
  odhad: M
  rozhoduje: agent
  riziko: Manuál zastará s každou změnou obrazovek; poznáme podle rozdílů ve druhém kole testu.

- id: A61
  priorita: P1
  oblast: ocenění
  typ: dokumentace
  nazev: Naplánovat paralelní běh prvního fondu
  popis: Postup paralelního běhu na oceněních k 31. 1. a 28. 2. 2027, protože dvě řádná měsíční ocenění se do zkušebního provozu v březnu nevejdou; předchozí administrátor dodá data do konce února 2027 (P). Kritéria shody a schválení rozdílů.
  dotcene_casti:
    - docs/harmonogram.md
  akceptace:
    - Plán obsahuje data ocenění, zdroje dat, toleranci a kdo rozdíly schvaluje
  zavisi_na: [A35]
  odhad: S
  rozhoduje: agent
  riziko: Data k 28. 2. budou úplná až po dokončení únorového ocenění začátkem března; poznáme podle data předání a zkrácení času na paralelní běh.

- id: A62
  priorita: P1
  oblast: ocenění
  typ: rozhodnutí
  nazev: Rozhodnout, kde vzniká účetní závěrka fondu (R16)
  popis: Revize doporučuje rozvahu a výsledovku z Odoo podle rámce fondu (vyhláška 501 s IFRS pro nástroje, nebo plné IFRS) a přílohu ve Wordu.
  dotcene_casti:
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí
  zavisi_na: []
  odhad: S
  rozhoduje: člověk
  riziko: Pozdní rozhodnutí zkrátí čas na první roční závěrku fondu; poznáme podle data zápisu.

- id: A63
  priorita: P1
  oblast: ocenění
  typ: kód
  nazev: Data účetní závěrky fondu
  popis: Rozvaha a výsledovka knihy fondu podle zvoleného rámce a export dat pro výroční zprávu, postavené na sestavách z A18 a rolích účtů.
  dotcene_casti:
    - investra_chart_fund
    - modul sestav (nový)
  akceptace:
    - Rozvaha syntetického fondu bilancuje a navazuje na předvahu
    - Export pro výroční zprávu obsahuje srovnatelné období
  zavisi_na: [A18, A62]
  odhad: M
  rozhoduje: agent
  riziko: Dva rámce znamenají dvě sady definic; poznáme podle počtu definic a jejich testů.

- id: A64
  priorita: P2
  oblast: účetnictví Services
  typ: rozhodnutí
  nazev: Rozhodnout vytěžování PDF (R10)
  popis: S Enterprise vytěžování službou Odoo po zápisu do evidence ICT dodavatelů, bez Enterprise předvyplnění z historie a později vlastní vytěžování s potvrzením člověkem.
  dotcene_casti:
    - docs/rozhodnuti.md
  akceptace:
    - Zápis v deníku rozhodnutí
  zavisi_na: [A02]
  odhad: S
  rozhoduje: člověk
  riziko: Doklady odejdou ke třetí straně bez evidence; poznáme kontrolou evidence ICT dodavatelů.

- id: A65
  priorita: P2
  oblast: účetnictví Services
  typ: kód
  nazev: Vytěžování PDF s potvrzením člověkem
  popis: Podle A64 předvyplnit dodavatele, data, DUZP, měnu a řádky z PDF; výsledek je vždy koncept, který potvrdí účetní, a u každého pole je vidět, zda je vytěžené.
  dotcene_casti:
    - modul nastavení Services (nový)
  akceptace:
    - Vytěžený doklad nikdy nevznikne jako zaúčtovaný
    - Na sadě syntetických faktur je změřená přesnost polí
  zavisi_na: [A46, A64]
  odhad: M
  rozhoduje: agent
  riziko: Chybně vytěžené DUZP projde bez povšimnutí; poznáme podle oprav DUZP po potvrzení.

- id: A66
  priorita: P2
  oblast: ocenění
  typ: kód
  nazev: Repo a reverzní repo
  popis: Repo a reverzní repo jako konfigurace společného modelu peněžních toků z A26 včetně evidence zajištění.
  dotcene_casti:
    - investra_instruments
    - investra_nav
  akceptace:
    - Reverzní repo se shoduje s nezávislým výpočtem naběhlé hodnoty
  zavisi_na: [A26]
  odhad: M
  rozhoduje: agent
  riziko: Zajištění může vyžadovat vlastní evidenci mimo model peněžních toků; poznáme při návrhu.

- id: A67
  priorita: P2
  oblast: ocenění
  typ: kód
  nazev: Výsledovka podle IFRS 18
  popis: Pro fondy s plnými IFRS členění výsledovky podle IFRS 18 jako další definice výkazu; účinnost a přijetí v EU ověří auditor.
  dotcene_casti:
    - modul sestav (nový)
  akceptace:
    - Fond s parametrem plné IFRS má výsledovku v novém členění se srovnatelným obdobím
  zavisi_na: [A63]
  odhad: M
  rozhoduje: agent
  riziko: Požadavky na prezentaci se mohou upřesnit; poznáme z vyjádření auditora.

- id: A68
  priorita: P2
  oblast: architektura
  typ: dokumentace
  nazev: Vést registr úprav chování standardu Odoo
  popis: Seznam míst, kde vlastní moduly mění standardní chování (hledání kurzu, kontrola zápisu do cizí knihy, výchozí hodnoty z kontextu a další), s odkazem na test ke každému; při upgradu se projde jako první.
  dotcene_casti:
    - docs/analyza-odoo20-nav.md
    - addons/custom/
  akceptace:
    - Každá položka registru má test, který selže, když úprava přestane platit
  zavisi_na: []
  odhad: S
  rozhoduje: agent
  riziko: Nová úprava se do registru nezapíše; poznáme při revizi kódu podle R14.

- id: A69
  priorita: P2
  oblast: architektura
  typ: analýza
  nazev: Připravit knihu investiční společnosti
  popis: Kniha investiční společnosti podle vyhlášky 501 ze šablony knihy a analýza výkazů obhospodařovatele pro ČNB; termín závisí na povolení ČNB.
  dotcene_casti:
    - investra_entity
    - investra_cnb
  akceptace:
    - Seznam výkazů obhospodařovatele s mezerami a odhadem
  zavisi_na: [A54]
  odhad: M
  rozhoduje: agent
  riziko: Povolení může přijít dřív, než bude kniha připravená; poznáme podle stavu žádosti.

- id: A70
  priorita: P3
  oblast: IS
  typ: kód
  nazev: API k IS
  popis: API se stejnými zprávami a pravidly jako souborové rozhraní z A31, až bude IS existovat.
  dotcene_casti:
    - rozhraní IS (nový)
  akceptace:
    - Stejné testovací zprávy dají přes API i přes soubor stejný výsledek
  zavisi_na: [A31]
  odhad: L
  rozhoduje: agent
  riziko: API otevírá Odoo do sítě; poznáme bezpečnostní revizí před nasazením.

- id: A71
  priorita: P3
  oblast: ocenění
  typ: kód
  nazev: Deriváty
  popis: Burzovní a mimoburzovní deriváty včetně maržových účtů, zajištění a ocenění podle smlouvy.
  dotcene_casti:
    - investra_instruments
    - investra_nav
  akceptace:
    - Forward a futures se shodují s nezávislým výpočtem
  zavisi_na: [A26]
  odhad: L
  rozhoduje: agent
  riziko: Ocenění mimoburzovních derivátů může vyžadovat externí model; poznáme u prvního fondu s deriváty.

- id: A72
  priorita: P3
  oblast: ocenění
  typ: kód
  nazev: Přímé napojení Bloombergu a bank
  popis: Stahování cen a výpisů přes API místo souborů; výsledek prochází stejnými kontrolami a schválením. Licenční podmínky Bloombergu ověří vedoucí.
  dotcene_casti:
    - investra_instruments
    - modul bankovních výpisů (nový)
  akceptace:
    - Výsledek z API je stejný jako import souboru za týž den
  zavisi_na: [A30, A32]
  odhad: M
  rozhoduje: agent
  riziko: Přístupové údaje k API musí spravovat člověk mimo repozitář; poznáme kontrolou tajemství v CI.

- id: A73
  priorita: P3
  oblast: UI
  typ: obrazovka
  nazev: Dvousloupcový průvodce oceněním ve vlastním OWL
  popis: Vlastní komponenta OWL s kroky vlevo a detailem vpravo, jen pokud druhé kolo testu ukáže, že standardní formulář nestačí.
  dotcene_casti:
    - investra_nav
  akceptace:
    - Kliknutí a čas oproti standardnímu formuláři klesnou o hodnotu dohodnutou po testu
  zavisi_na: [A45]
  odhad: M
  rozhoduje: agent
  riziko: Vlastní JavaScript zvyšuje náklady upgradu; poznáme v registru úprav (A68).

- id: A74
  priorita: P3
  oblast: ocenění
  typ: kód
  nazev: Řízená reklasifikace podle IFRS 9
  popis: Událost reklasifikace finančního aktiva v jednom fondu při změně obchodního modelu, s povinným důvodem, podkladem a schválením druhou osobou. Účinnost ode dne reklasifikace (první den prvního účetního období po změně obchodního modelu), prospektivně a bez přepracování dříve vykázaných zisků, ztrát a úroků; finanční závazky se nereklasifikují (Z, IFRS 9; pravidla potvrdí metodik a auditor). Datový model s platností klasifikace připraví už A22.
  dotcene_casti:
    - investra_instruments
    - investra_posting
    - investra_nav
  akceptace:
    - Reklasifikace z naběhlé hodnoty do FVTPL v syntetickém fondu vytvoří ke dni reklasifikace přecenění na reálnou hodnotu do výsledku a další ocenění použije novou klasifikaci
    - Reklasifikace v jednom fondu nezmění klasifikaci téhož nástroje v jiném fondu
    - Bez schválení druhou osobou se reklasifikace nezaúčtuje
  zavisi_na: [A22, A26, A40]
  odhad: M
  rozhoduje: agent
  riziko: Reklasifikace je vzácná a pravidla se nemusí ověřit na reálném případu; poznáme při revizi pravidel auditorem.
```

---

## 6. Otevřené otázky po revizi

| # | Otázka | Na co má vliv | Kdo odpoví |
|---|---|---|---|
| 1 | Povoluje licence Bloomberg sdílet ceny mezi fondy a předávat je depozitáři? | A30, A36 | VED (ověří ve smlouvě) |
| 2 | V jakém rozsahu se DORA vztahuje na investiční společnost a co z ní plyne pro Services jako dodavatele ICT služeb? | A58 | právník |
| 3 | Půjde do 13. 11. 2026 získat zkušební verzi Odoo 20 Enterprise pro ověření funkcí? | A01, R1 | VED, partner Odoo |

**Zodpovězeno metodikem 8. 11. 2026 a zapracováno:**
- *Kurzy:* fond s funkční měnou EUR používá kurzy ECB jen v účetnictví. Výkazy ČNB jsou vždy v CZK a z EUR se přepočítávají
  kurzem ČNB podle legislativy (F6, F12, O8, A29, A37, A39).
- *Klasifikace IFRS 9:* jeden nástroj může mít v různých fondech různou klasifikaci (A22).
- *Reklasifikace:* může teoreticky nastat. Klasifikace proto dostane platnost od, řízená reklasifikace je krok A74.
- *Úpisy a výplaty:* cesta úpisů se liší podle fondu (účet fondu, nebo sběrný účet), výplaty odkupů a dividend zadává IS
  (R17, F9, A09, A32).
- *Performance fee:* jen po třídě fondu; série a vyrovnání nejsou v rozsahu (2.1, F15, A56).
- *Schválení cizím obhospodařovatelem:* písemně mimo Odoo, schválení se přiloží k ocenění (R6, O1, O4, A10, A40).
- *Lhůta Services za rok 2026:* daňové přiznání v běžné lhůtě, uzávěrka musí být hotová v březnu, doporučeno
  do 26. 2. 2027 (S7, 2.7, A52).
- *Data pro paralelní běh:* předchozí administrátor je dodá do konce února 2027 (2.7, A61).
- *Banka Services:* provozní banka bude Fio (S5, A19).
- *Návrh obrazovky NAV od vedoucího:* přemostění kapitálu po třídách a údaje o období jsou převzaté do O1; sjednocení
  obou prototypů je rozhodnutí R18 (A75).
- *Platforma:* hlavní směr je Odoo. Úvaha o variantě iÚčto pro vše s vlastní aplikací pro ocenění je vedle v souboru
  `uvaha-iucto.md`.

Revize nevidí kód. Předpoklady o stavu prototypu (např. kde je dnes klasifikace IFRS 9) a o funkcích Odoo 20 ověří agent
v krocích A01 a A22. Pokud se ukážou jinak, je potřeba upravit odhady a pořadí kroků.
