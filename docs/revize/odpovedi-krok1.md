# Odpovědi na krok 1 revize

8. 11. 2026. Odpovědi připravil vývojový agent z dokumentace projektu a z dosavadní práce s vlastníkem projektu,
vlastník je potvrdil. Kde odpověď neznáme, je to výslovně uvedeno spolu s naším doporučením; v takovém případě
**navrhni varianty**.

## Hlavní princip: univerzální řešení

Nestavíme systém pro jeden konkrétní fond. Investra bude spravovat fondy různých zakladatelů a převezme je
od různých administrátorů, proto musí být fondové moduly **univerzální a připravené na co nejvíc variant**.
První fond je jen první případ použití. Co se liší mezi fondy, má být parametr (nastavení fondu, třídy, nástroje,
pravidla), ne kód psaný pro konkrétní fond. Zejména:
- všechny běžné typy nástrojů a způsoby ocenění (tržní cena, posudek, model, naběhlá hodnota, zadaná hodnota pozice),
- libovolné měny nástrojů, tříd i funkční měna fondu (CZK, EUR a další),
- fond, SICAV s podfondy i bez nich, víc tříd s různými úplatami, performance fee, hurdle a high-water mark,
- oba účetní rámce fondů (vyhláška 501 s IFRS pro nástroje, nebo plné IFRS),
- libovolná frekvence ocenění včetně mimořádného,
- různé depozitáře, banky a formáty dat.

Při hodnocení priorit proto rozlišuj **univerzální jádro** (musí být hotové pro jakýkoli první fond) a **rozšíření**
(přidají se podle potřeby dalších fondů, ale architektura s nimi musí počítat od začátku).

---

## A. K předpokladům

| # | Předpoklad | Odpověď |
|---|---|---|
| 1 | Investiční společnost povolení do Q1 2027 nedostane, první fond formálně spravuje jiný subjekt, Services dělá outsourcing | Nevíme, stav žádosti není jistý. Systém musí umět obojí: Services jako poskytovatel účetnictví a NAV pro jiného obhospodařovatele i vlastní investiční společnost jako obhospodařovatel a administrátor. Navrhni varianty a dopady na role a odpovědnosti v systému |
| 2 | Funkční měna prvního fondu je CZK | Nevíme. Funkční měna je parametr fondu; podporovat CZK i EUR (případně další) od začátku |
| 3 | Jednoduchý portfolio mix, deriváty a repo nejsou pro start nutné | Nevíme, jaký mix bude mít první fond. Systém má umět všechny běžné typy nástrojů. Prioritu stanov tak, aby jádro zvládlo typické FKI: účasti a úvěry v SPV, dluhopisy, akcie a fondy, termínované vklady, ostatní podíly s upisovacím závazkem. Deriváty a repo jako navazující rozšíření s připravenou architekturou |
| 4 | Účetnictví investiční společnosti není v rozsahu prvního ostrého provozu | Pořadí je rozhodnuté: Services, investiční společnost, potom fondy. Termín investiční společnosti závisí na povolení ČNB, proto není v harmonogramu pevně. Doporučení: investiční společnost jako další kniha ve stejném systému (vyhláška 501), bez zvláštního vývoje navíc kromě výkazů kapitálu obhospodařovatele |
| 5 | Výkazy ČNB přes SDAT ve strojovém formátu, odesílá člověk | Ano. Termíny a výkazy se stahují ze SDAT, výstup je soubor, odesílá a podepisuje člověk |
| 6 | Předchozí administrátor předá předvahu, pozice, třídy a historii pro performance fee | Nevíme, liší se podle administrátora. Proto společný vstupní formát s převodníkem pro každý zdroj (C.4). Navrhni, jak řešit chybějící údaje (např. pořizovací kurz, high-water mark) |
| 7 | Depozitář NAV kontroluje, jeho stanovisko je podmínkou zveřejnění | Ano. Zda depozitář počítá vlastní NAV, se liší podle depozitáře; systém má umět předat podklady i přijmout jeho výsledek k porovnání |
| 8 | Jednotky uživatelů, žádná produkce | Ano |
| 9 | Services od 19. 3. 2026 v Odoo, obsah `investra_dev` do produkce | Účetnictví Services od 19. 3. 2026 v Odoo ano. Převod do produkce nerozhodnutý, viz otázka 13 |
| 10 | Omezený rozpočet, rozhodnutí o edici bez schváleného rozpočtu | Ano, rozpočet schválený není. Preferujeme řešení, které funguje v Community i Enterprise (vlastní moduly nad standardním účetnictvím); koupi doporuč tam, kde ušetří víc vývoje, než stojí |
| 11 | Ceny ručně nebo z Excelu, placený zdroj zatím není | Oprava: ceny pocházejí z Bloombergu, do Odoo se importují z Excelu; přímé napojení případně později. Import má být univerzální (různé zdroje a formáty, ruční zadání s podkladem) |

---

## B. Odpovědi na otázky

**1. Aktiva prvního fondu.** Nevíme a nechceme řešení na míru jednomu fondu: systém musí být univerzální pro všechny
běžné typy nástrojů, měny a zdroje cen. Typy v prototypu jsou v C.5. Fondy často drží aktiva přes SPV (účast, úvěr SPV,
příplatek mimo základní kapitál). Kupóny i dividendy počítej jako běžnou součást. **Navrhni varianty** pořadí, v jakém
typy nástrojů a jejich události (kupón, dividenda, splátka, poplatek obchodu) dokončit.

**2. Kdo bude fond spravovat a role Services.** Nevíme; žádost investiční společnosti o povolení je v přípravě.
Systém musí podporovat obě uspořádání (viz předpoklad 1): Services jako outsourcing účetnictví a NAV pro cizího
obhospodařovatele i vlastní investiční společnost. **Navrhni varianty** rolí, oprávnění a schvalování pro oba případy.

**3. Výkazy ČNB.** První měsíční výkazy jsou pro první fond nutné; zkušební provoz počítá s RISIFI30, RISIFI33,
TISIFI10, VISIFI10, RISIFI37 (metodika FOFI20261201, změny metodik od 2027). První referenční období nevíme, závisí na dni
převzetí. Přechodná cesta mimo Odoo není rozhodnutá; preferujeme výkazy z Odoo. **Navrhni varianty** včetně záložní
(dočasný export do šablony a ruční kontrola) a co z výkazů musí být hotové k prvnímu fondu.

**4. Převzetí.** Den ani podobu dat nevíme; liší se podle předchozího administrátora. Počítáme s převzetím ke dni uzávěrky
nebo ocenění a paralelním během (C.4). **Navrhni** univerzální vstupní formát, kontroly a postup pro chybějící údaje.

**5. Edice a rozpočet.** Rozpočet schválený není. Doporučení průzkumu je Enterprise (plán Custom) na vlastním hostingu v EU.
Odoo.sh nepreferujeme: lokalita dat tam podle podmínek Odoo není smluvně zaručená, což může kolidovat s DORA (ověřit).
Externí partner pro českou lokalizaci je záměr, nerozhodnutý. **Navrhni varianty** (Community s vlastním vývojem a moduly OCA,
Enterprise, kombinace) s odhadem, co který kus stojí v práci a co v licencích.

**6. IS.** Investra bude mít samostatnou aplikaci IS pro investory; dokumentace a API zatím nemáme. Rozhraní je navržené
jako 9 verzovaných zpráv (C.3). Cut-off určuje IS podle statutu fondu; vstup transakcí do závěrky je parametr fondu.
**Navrhni** rozhraní nezávislé na konkrétním IS: nejdřív soubor (import a kontrola), později API, se stejnými zprávami.

**7. Banka.** Services použila Fio banku pro složení základního kapitálu; provozní banka Services ani banky fondů a depozitáře nejsou rozhodnuté, každý fond může mít jinou. Objem u Services jsou jednotky až desítky pohybů měsíčně; u fondů nevíme.
**Navrhni** univerzální import výpisů (formáty GPC/ABO, CAMT.053, MT940, případně API bank) a párování se schválením účetní.

**8. Počet nástrojů.** Nevíme; u FKI očekáváme jednotky až nižší desítky nástrojů na fond, při desítkách fondů stovky celkem.
Obrazovky a import cen navrhni tak, aby zvládly stovky nástrojů a hromadné schválení s výjimkami.

**9. Lidé.** Účetnictví Services dnes vede vlastník projektu sám (metodik). Pro fondy: dvě účetní, které se zastupují; druhá osoba
povinná u cen a ocenění; vedení fondu, administrátor nebo obhospodařovatel jako volitelní další schvalovatelé podle parametru fondu.
Zastupování schvalovatele a čtyři oči u Services nejsou rozhodnuté. **Navrhni** přiměřené řešení pro malý tým (kdo smí co,
zastupování, co dělat, když je k dispozici jen jedna osoba) a zda čtyři oči u Services zavést jen pro platby.

**10. Účetní rámec.** Systém musí podporovat oba rámce fondů: vyhlášku 501 s IFRS pro finanční nástroje i plné IFRS
(od 2027 IFRS 18). Rámec prvního fondu nevíme. Výroční zpráva: export dat z Odoo, dokončení ve Wordu. Kde vznikne účetní
závěrka (rozvaha, výsledovka, příloha), rozhodnuté není; souvisí s edicí. **Navrhni varianty.**

**11. Hosting a DORA.** Provozovatel ani RTO a RPO stanovené nejsou. Požadavek: data v EU, zálohy včetně příloh, test obnovy,
MFA, evidence ICT dodavatelů podle DORA. **Navrhni varianty** provozu (vlastní IT, správce na smlouvu, cloud v EU) a rozumné
cílové RTO a RPO pro malou investiční společnost, s tím, že konkrétní hodnoty potvrdí vnitřní předpisy.

**12. Depozitář.** Formát a lhůty nevíme, liší se podle depozitáře. Dnes Excel s listy Portfolio, NAV, Předvaha, Úplaty.
**Navrhni** univerzální balíček (strojově čitelný a pro člověka), evidenci stanoviska a porovnání s případným výpočtem depozitáře.

**13. Services naostro.** Nerozhodnuto. Doporučení vývojového agenta: založit čistou produkční databázi se stejným nastavením
(osnova, daně, deníky) a doklady od 19. 3. 2026 přenést nebo znovu zadat s opravami; `investra_dev` zůstane vývojová.
**Navrhni varianty** a jejich dopad na auditovatelnost a termín 18. 12.

**14. Kapacita a termíny.** Vývoj dělá vlastník projektu s AI agentem při běžné práci; přesný počet hodin týdně nevíme, počítej
s částečným úvazkem. Kdy budou účetní k dispozici na testy, nevíme; nejpozději ve zkušebním provozu. Konec Q1 2027 je cíl, ne smluvní
ani regulatorní termín; brána 22. 1. 2027 má rozhodnout o pokračování. **Navrhni**, co zjednodušit nebo přesunout, aby se cíl stihl
bez ztráty univerzálnosti jádra.

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
