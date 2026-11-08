# Odpovědi na krok 1 revize

Koncept 8. 11. 2026. Odpovědi z dokumentace projektu připravil vývojový agent, místa označená **DOPLNIT** vyplní
vlastník projektu. Před odesláním revidující AI projít a doplnit; nic z toho není schválený závazek.

---

## A. K předpokladům

| # | Předpoklad | Odpověď |
|---|---|---|
| 1 | Investiční společnost povolení do Q1 2027 nedostane, první fond formálně spravuje jiný subjekt, Services dělá outsourcing | V dokumentaci rozhodnuto není; otevřený bod „soulad s žádostí o povolení“. **DOPLNIT** |
| 2 | Funkční měna prvního fondu je CZK | Architektura podporuje i EUR (funkční měna může být jiná než CZK, kurzy ECB). Pro první fond **DOPLNIT** |
| 3 | Jednoduchý portfolio mix, deriváty a repo nejsou pro start nutné | Deriváty nejsou v povinném rozsahu pro první fond (rozhodnutí 7. 11. 2026). Fondy často drží aktiva přes SPV (účast, úvěr SPV, příplatek mimo základní kapitál). Skutečné složení **DOPLNIT** |
| 4 | Účetnictví investiční společnosti není v rozsahu prvního ostrého provozu | Pořadí nasazení je rozhodnuté: Services, investiční společnost, potom fondy. Harmonogram ale investiční společnost samostatně neplánuje. Termín **DOPLNIT** |
| 5 | Výkazy ČNB přes SDAT ve strojovém formátu, odesílá člověk | Ano: termíny a výkazy se stahují ze SDAT; návrh začíná variantou se souborem; AI ani systém nic neodesílají bez člověka. Způsob podpisu je otevřený |
| 6 | Předchozí administrátor předá předvahu, pozice, třídy a historii pro performance fee | Plánovaný vstupní formát to obsahuje (viz C.4). Co skutečně dodá, **DOPLNIT** |
| 7 | Depozitář NAV kontroluje, jeho stanovisko je podmínkou zveřejnění | Ano, zveřejnění kurzu a uzamčení období až po stanovisku depozitáře. Zda počítá vlastní NAV, **DOPLNIT** |
| 8 | Jednotky uživatelů, žádná produkce | Ano: dvě účetní fondů, druhá osoba na schvalování; produkce zatím není |
| 9 | Services od 19. 3. 2026 v Odoo, obsah `investra_dev` do produkce | Účetnictví od 19. 3. 2026 v Odoo ano. Způsob převodu do produkce rozhodnutý není, **DOPLNIT** |
| 10 | Omezený rozpočet, rozhodnutí o edici bez schváleného rozpočtu | **DOPLNIT** |
| 11 | Ceny ručně nebo z Excelu, placený zdroj zatím není | Oprava: ceny pocházejí z Bloombergu, do Odoo se importují z Excelu; přímé napojení případně později (rozhodnutí 4. 11. 2026) |

---

## B. Odpovědi na otázky

**1. Aktiva prvního fondu.** V dokumentaci nejsou. Známé obecně: fondy často drží účasti a úvěry v SPV;
deriváty nejsou pro první fond povinné; typy nástrojů v prototypu viz C.5.
**DOPLNIT:** typy a počet nástrojů, způsob ocenění (tržní cena, posudek, model, naběhlá hodnota), měny, zda jsou kupóny a dividendy.

**2. Kdo bude fond právně spravovat a v jaké roli bude Services.** Investiční společnost je v přípravě (žádost o povolení ČNB).
**DOPLNIT:** stav žádosti, kdo bude obhospodařovatel a administrátor k přechodu, role Services.

**3. Výkazy ČNB prvního fondu.** Rozhodnuto: první měsíční výkazy jsou pro první fond nutné. Zkušební provoz počítá
s měsíčními výkazy RISIFI30, RISIFI33, TISIFI10, VISIFI10 a RISIFI37. Platí metodika FOFI20261201, nové metodiky ČNB jsou v plánu od 2027.
**DOPLNIT:** první referenční období a zda je možná přechodná cesta mimo Odoo.

**4. Převzetí.** Fond přechází ke dni uzávěrky nebo ocenění, ne migrací celé historie; postup viz C.4.
**DOPLNIT:** den převzetí, podoba dat od předchozího administrátora, zda je počáteční stav auditovaný.

**5. Edice a rozpočet.** Průzkum doporučuje Enterprise (plán Custom) na vlastním hostingu v EU; web Odoo uvádí 22,90 až 27,90 €
za uživatele a měsíc při ročním placení, závazně až nabídka. Licence je za uživatele, ne za společnost.
Záměr je externí partner pro českou lokalizaci; rozsah rozhodnutý není.
**DOPLNIT:** rozpočtový strop, Odoo.sh ano či ne, partner.

**6. IS.** Rozhraní je navržené jako 9 typů zpráv (viz C.3); hlavní je finalizovaná závěrka klientských transakcí, v jednom
oceňovacím období jich může být víc. Rozhodnuto: IS vytváří platební příkazy na výplaty a spouští převody, Odoo páruje výpisy;
kurz úpisu v průběhu období je poslední známý, řídí IS. Dokumentace a API IS zatím chybí.
**DOPLNIT:** zda je IS vybraný, forma předávání (soubor nebo API), četnost, kdo určuje cut-off.

**7. Banka.** Rozhodnuto: výpisy se načítají automaticky, párování je návrh, který účetní vždy schválí; třída má účet pro úpisy
a pro odkupy, fond investiční účet, zvlášť pro každou měnu; platební příkazy jako soubor s autorizací dvěma osobami a kontrolou depozitářem.
**DOPLNIT:** banky, formáty výpisů, počet pohybů měsíčně.

**8. Ceny a nástroje.** Zdroj Bloomberg, import z Excelu. Ceny mají historii, zdroj, autora a schválení druhou osobou.
**DOPLNIT:** počet nástrojů při startu a za rok.

**9. Lidé.** Dvě účetní fondů se zastupují; u fondů Investry je druhá osoba povinná pro ceny a ocenění, schválení vedením fondu
je volitelné a pořadí schvalovatelů je parametr fondu. U Services: banka se páruje jen se schválením účetní; čtyři oči u faktur Services nejsou rozhodnuté.
**DOPLNIT:** kdo zadává a kdo schvaluje (role), zastupování schvalovatele, čtyři oči u Services.

**10. Účetní rámec prvního fondu.** Možné rámce: vyhláška 501 s IFRS pro finanční nástroje, nebo plné IFRS (u plného IFRS se od 2027 použije IFRS 18).
Výroční zprávy: export dat z Odoo, dokončení ve Wordu.
**DOPLNIT:** rámec prvního fondu a kde vznikne účetní závěrka.

**11. Hosting a DORA.** Hosting rozhodnutý není; doporučení vlastní hosting v EU. Plán obsahuje produkci, zálohy, test obnovy
a mapu DORA; evidence dodavatelů je otevřený bod. MFA a hesla se řeší při návrhu produkce.
**DOPLNIT:** kdo bude provozovat, RTO a RPO, požadavek na lokalitu dat.

**12. Depozitář.** Dnes dostává Excel s listy Portfolio, NAV, Předvaha a Úplaty; stanovisko se eviduje v Odoo a vrácení
depozitářem stornuje doklady ocenění a vytvoří novou verzi. Vzorce v Excelu se mají vypnout (otevřený bod).
**DOPLNIT:** formát a lhůty depozitáře, zda počítá vlastní NAV.

**13. Services naostro.** Nerozhodnuto. `investra_dev` je označená TEST a má 9 skutečných dokladů a 6 konceptů.
**DOPLNIT:** převést, nebo založit čistou databázi; jak opravit vadné doklady.

**14. Kapacita a termíny.** Konec Q1 2027 je v deníku vedený jako předpoklad, ne pevné rozhodnutí; brána 22. 1. 2027 má posoudit pokračování.
**DOPLNIT:** hodiny týdně na vývoj, kdy budou účetní k dispozici na testy, zda je termín smluvní nebo regulatorní.

**15. Podklady.** Výtahy jsou v části C.

---

## C. Přílohy

### C.1 Akceptace prototypu a přechodu fondu (z harmonogramu)
Prototyp:
1. NAV a kurz každé třídy se shodují s nezávislým výpočtem, včetně příkladu performance fee a třídy v EUR.
2. Stejné vstupy dávají stejný výsledek a opakovaný výpočet nic nezdvojí.
3. Součet tříd se rovná FK, pozice se rovnají hlavní knize.
4. Bez schválení nejde návrh zaúčtovat ani změnit; zadavatel si nemůže schválit vlastní ocenění.
5. Vrácení před zaúčtováním vytvoří novou verzi bez storen; vrácení depozitářem stornuje všechny doklady a zaúčtuje novou verzi.
6. Každé číslo jde dohledat k ceně, kurzu, parametru a schvalovateli.

Přechod fondu:
1. Předvaha, otevřené položky, pozice a kusy ke dni přechodu se shodují se zdrojem.
2. Ve dvou po sobě jdoucích oceněních souhlasí NAV a kurz třídy; každý rozdíl je vysvětlený a schválený.
3. Zkušební výkazy ČNB projdou závažnými kontrolami bez ruční úpravy; ruční zásah má zdůvodnění.
4. Test obnovy splnil limity podle DORA a vnitřních předpisů.
5. Role, čtyři oči, MFA a neměnnost jsou ověřené na produkčním nastavení.
6. Obě účetní zvládnou ocenění podle manuálu, včetně zastoupení.
7. Balíček pro audit a depozitáře je kompletní.
8. Přechod schválí odpovědná osoba, zápis se založí k fondu.

### C.2 Ocenění: kroky a stavy
**Kroky:**
- **0. Příprava:** závěrky z IS, spárovaná banka, obchody, kurzy, úroky, nároky.
- **1. Ceny:** import a schválení.
- **2. Přecenění cizích měn:** návrh dokladu.
- **3. Reálná hodnota po pozicích:** návrh dokladu.
- **4. Úplaty, dohady a daň:** podle pořadí ve statutu.
- **5. NAV a rozdělení:** NAV a rozdělení na třídy, kusy z IS, zaokrouhlení.
- **6. Kontroly a sestava:** stav OK, upozornění nebo stop.
- **7. Schválení:** kompletního finálního ocenění druhou osobou, případně dalšími podle parametru fondu.
- **8. Zaúčtování:** jedním krokem.
- **9. Depozitář.**
- **10. Zveřejnění kurzu a uzamčení období.**
- **11. Navazující kroky:** úhrada úplat, snímek pro výkazy ČNB.

**Stavy záznamu ocenění v prototypu:** Návrh → Spočteno → Ke schválení → Schváleno → Zaúčtováno → U depozitáře →
Potvrzeno depozitářem → Zveřejněno a uzamčeno; vedlejší stavy Vráceno a Stornováno.
Akce: spočítat, odeslat ke schválení, schválit, vrátit s důvodem, zaúčtovat, odeslat depozitáři, potvrzení depozitáře,
vrácení depozitářem s důvodem, zveřejnit.

**Kontroly v kroku 6:**
- zůstatek banky proti výpisu,
- účty úpisů a odkupů proti závazkům k držitelům,
- pozice proti saldu účtů,
- kusy proti IS a depozitáři,
- nároky na kupóny a dividendy,
- změna FK nad prahem, stáří cen,
- předběžné kontroly ČNB.

**Sestava ke schválení:** přemostění FK (počátek, úpisy a odkupy, FX, reálná hodnota, úplaty, performance fee, daň, konec),
aktiva a pasiva podle rolí účtů, výpočet po třídách, změna ceny za kus, ceny a výjimky.

### C.3 Rozhraní Odoo a IS (9 zpráv, pracovní návrh)
| Zpráva | Směr | Obsah |
|---|---|---|
| Číselník fondů a tříd | Odoo → IS | Fond, třída, ISIN, měna, stav |
| Identifikátory plateb a převodů | IS → Odoo | Fond, třída, u výplat částka |
| Potvrzení platby | Odoo → IS | Identifikátor, částka, datum |
| Závěrka | IS → Odoo | Hlavička, transakce, součty za třídu |
| Kurz | Odoo → IS | Datum ocenění, platnost, zveřejnění, příznak opravy |
| Použití závěrky | Odoo → IS | Ve kterém ocenění byla závěrka použita |
| Denní stav kusů | IS → Odoo | Třída, datum, kusy |
| Agregace držitelů pro ČNB | IS → Odoo | Podle sektoru a rezidence, bez osobních údajů |
| Rozhodnutí o dividendě | Odoo → IS | Třída, dividenda na kus, rozhodný den, výplata |

Pravidla:
- **Zprávy:** verzované s jednoznačným ID, při výpadku se doručí později ve stejném pořadí.
- **Storno:** storno v IS vyvolá storno v Odoo.
- **Kontroly v Odoo:**
  - závěrka musí navazovat na předchozí,
  - cena úpisu se porovná se zveřejněným kurzem,
  - kusy a peníze se denně porovnají s účetnictvím.

### C.4 Převzetí fondu (postup)
1. Společný vstupní formát: osnova, předvaha, otevřené položky, pozice, třídy, kusy a kurzy, atributy pro výkazy.
2. Mapování účtů fondu na role; osnova fondu může zůstat.
3. Počáteční stavy: zůstatky, otevřené položky, kapitál podle tříd.
4. Pozice po nástrojích: pořizovací cena v měně, pořizovací kurz, kurzový rozdíl, přecenění.
5. Údaje pro výpočty: historie NAV, high-water mark, hurdle.
6. Kontroly: předvaha, otevřené položky proti účtům, pozice proti hlavní knize, kusy proti IS, FK se zreprodukuje.
7. Paralelní běh: jedno až dvě ocenění v obou systémech, pak přepnutí se schválením.
8. Historie zůstane jako archiv; při přechodu v průběhu roku se doplní obraty po měsících.

### C.5 Typy nástrojů v prototypu
| Typ | IFRS 9 | Ocenění |
|---|---|---|
| Akcie, podílový list nebo ETF | FVTPL | Cena × kusy |
| Dluhopis | FVTPL | Cena × kusy |
| Termínovaný vklad, reverzní repo | Naběhlá hodnota | Naběhlá hodnota |
| Poskytnutý úvěr, účast | FVTPL | Model nebo znalec |
| Burzovní a mimoburzovní derivát | FVTPL | Cena × kusy, podle smlouvy |
| Ostatní podíl (fond bez ISIN) | FVTPL | Zadaná hodnota pozice |

Návrhy jsou pracovní, potvrdí je účetní politika fondu. Klasifikace je po prvním obchodu neměnná.
