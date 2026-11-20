# 4. Ocenění a schvalovací matice

*Ověřeno v kódu, v prohlížeči neověřeno (Martin 16. 11. 2026 přijal bez ověření). Matice a role přepsány po ZJ-01 až ZJ-03 (17. 11. 2026).*

Kapitola navazuje na fond z kap. 2 a 3 (Fond Alfa Růst). Cíl: nastavit frekvenci
ocenění a pravidla schvalování tak, aby šlo spočítat a schválit první ocenění. Podrobný postup ocenění je v pozdější kapitole.

## 1. Frekvence ocenění a další ocenění

Kalendář ocenění už neexistuje (MN-14). Den dalšího ocenění program **počítá** z údajů fondu a ukazuje ho na kartě Přehledu fondů.
Pole jsou ve formuláři fondu (**Investra › Nastavení › Fondy › Fondy › [fond]**, kap. 2): **Datum vzniku** a **Frekvence ocenění**
(Denně až Ročně, výchozí Měsíčně).

**Jak se datum počítá.** Výchozí je datum posledního zaúčtovaného ocenění, u prvního ocenění **Datum vzniku**; datum je vždy
**po** výchozím dni:

| Frekvence | Další ocenění |
|---|---|
| Měsíčně | poslední den následujícího kalendářního měsíce |
| Čtvrtletně | poslední den následujícího kalendářního čtvrtletí |
| Ročně | poslední den následujícího kalendářního roku |
| Týdně | nejbližší další pátek |
| Denně | nejbližší další pracovní den (pondělí až pátek) |

Státní svátky se zatím neberou, takže denní frekvence může vyjít na svátek. Pravidla dnů jsou návrh; konkrétní dny ocenění ze statutu
řeší pozdější úkol. Bez Data vzniku a bez zaúčtovaného ocenění se datum neukáže a karta fondu ukáže „Nezaloženo“ bez termínu.

**Rozpracované a mimořádné ocenění.** Ocenění založené k dřívějšímu dni (než vyjde výpočet) má na kartě přednost; mimořádné
ocenění proto nepotřebuje zvláštní pole. Ocenění jde založit k libovolnému datu; frekvenci program s ním nekontroluje.

**Co se nehlídá.** Lhůta zveřejnění se nehlídá a upozornění „Ocenění po termínu“ zaniklo. Kontrola intervalu proti statutu a zákonné
lhůtě (deník rozhodnutí 2026-11-04 „Interval ocenění“) v kódu není.

**Příklad:** Fond Alfa Růst, frekvence Měsíčně, Datum vzniku 1. 1. 2027. První další ocenění: 31. 1. 2027. Po zaúčtování
31. 1. 2027 karta ukáže 28. 2. 2027; při frekvenci Čtvrtletně by po 31. 1. 2027 ukázala 30. 6. 2027 (poslední den druhého čtvrtletí). Čísla jsou smyšlená.

## 2. Schvalovací matice

**Investra › Nastavení › Fondy › Schvalovací matice.** Seznam je seskupený podle činnosti. Matice je **jedna pro celou aplikaci**
(po zjednodušení ZJ-01 už nemá obhospodařovatele, zpřísnění pro fond ani jmenovité uživatele). Určuje, zda činnost provede jeden člověk, nebo
potřebuje druhou osobu či více kroků. **Kdo** činnost smí provést a schválit, určují role (kap. 5): role má u každé činnosti příznaky
**Provádí** a **Schvaluje**.

### Řádek matice

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Činnost** | ano | – | jedna z deseti činností, viz níže |
| **Platí od** | ano | dnes | od kdy řádek platí; platí vždy nejnovější řádek s datem do dne ocenění či úkonu |
| **Druhá osoba** | ano | Ano – čtyři oči | **Ne – stačí jeden člověk**, **Ano – čtyři oči**, **Kroky** |
| **Počet osob** | jen čtení | dopočet | provádějící + počet kroků (u „Ne“ vždy 1) |
| **Poznámka** | ne | – | např. odkaz na vnitřní předpis (jen název a článek, ne text) |

**Kdo schvaluje** (tabulka kroků, viditelná u Ano a Kroky; řádky se řadí tahem za úchyt):

| Pole kroku | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Pořadí** | – | 10 | pořadí kroku (úchyt pro přesun) |
| **Krok** | ano | Kontrola druhou osobou | název kroku |
| **Role** | ne | prázdné | konkrétní role Investry, která krok smí schválit; prázdné = kdokoli s rolí, která má činnost s příznakem Schvaluje |

Pole **Počet osob** a **Výchozí řádek** (řádek dodaný modulem) se nezadávají.

**Chování voleb:**

- **Ne** smaže kroky a ukáže varování, že úkon provede jeden člověk bez druhé osoby a zapíše se do Úkonů bez druhé osoby.
- **Ano** doplní jeden krok „Kontrola druhou osobou“; víc kroků u Ano nejde.
- **Kroky** vyžaduje aspoň jeden krok; každý krok musí provést jiný člověk než zadavatel a předchozí schvalovatelé.

**Kontroly (znění chyb):**

- „Bez druhé osoby nemá řádek schvalovatele. Smažte je nebo změňte volbu.“
- „Čtyři oči mají jednoho schvalovatele; pro více použijte Kroky.“
- „Kroky musí mít aspoň jednoho schvalovatele.“
- „Pro činnost a den už řádek matice existuje.“ (jedinečné: činnost, Platí od)
- „%s smí podle schvalovací matice provést jen uživatel s rolí, která má tuto činnost s příznakem Provádí.“ (a obdobně pro Schvaluje)

**Kdo smí matici měnit:** jen uživatel s úrovní přístupu **Správa** (nebo správce systému Odoo): „Schvalovací matici mění jen uživatel
s úrovní přístupu Správa.“ Ostatní matici čtou. Schvalovatel (příznak Schvaluje) matici nezmění.

**Co nejde změnit (nejde ani zpětně):**

- „Řádek matice nejde založit zpětně; „Platí od“ musí být dnes nebo později.“
- „Platný řádek matice nejde měnit ani mazat. Změnu zadejte novým řádkem s pozdějším „Platí od“.“ Řádek s „Platí od“ **dnes** nebo v budoucnu
  jde ještě upravit i smazat; od zítřka už ne. Změna kroků se počítá jako změna řádku.
- Každá změna se zapíše do historie řádku (chatter) a ocenění ji ukáže v kontrole „Schvalovací matice se od minulého ocenění nezměnila“
  (upozornění).

### Činnosti

| Činnost | Výchozí řádek z modulu |
|---|---|
| Schválení ocenění | čtyři oči |
| Vrácení a storno ocenění | jeden člověk |
| Zveřejnění ocenění | jeden člověk |
| Schválení ceny | čtyři oči |
| Ruční kurz a přepis kurzu | jeden člověk |
| Výjimka z uzamčení | čtyři oči |
| Ruční zadání úpisu a odkupu | jeden člověk |
| Ruční přepsání kategorie IFRS 9 | jeden člověk |
| Storno a oprava splátky nástroje | jeden člověk |
| Storno a oprava obchodu | jeden člověk |

Výchozí chování je uloženo jako deset řádků, **Platí od** 1. 1. 2000, poznámka „Výchozí – chování před maticí“; vznikají s modulem
a nejdou měnit ani mazat („Výchozí řádek z modulu nejde měnit ani smazat; zadejte nový řádek s pozdějším „Platí od“.“).
Pravidlo se mění **novým řádkem** s pozdějším „Platí od“. Bez vlastního řádku už první ocenění vyžaduje druhou osobu.

**Ukázková databáze** (`tools/demo_data/run_seed.sh`) navíc zakládá pro všech deset činností řádek **jeden člověk** s „Platí od“ ke dni založení
a poznámkou „Pracovní databáze: schvaluje jeden uživatel (pokyn 15. 11. 2026)“, aby jeden člověk mohl ocenění připravit i schválit. Čtyři oči
nastavíte novým řádkem s pozdějším „Platí od“ (nebo ještě dnes upravíte řádek ze dne založení).

**Hledání pravidla pro činnost:** nejnovější řádek s „Platí od“ do dne úkonu, jinak vestavěné chování. Sdílený záznam (kurz zdroje, sdílená cena)
se řídí nejpřísnějším pravidlem ze všech dotčených fondů.

### Příklad

Chcete, aby storno obchodu potvrzovala druhá osoba (výchozí je jeden člověk). Nový řádek: **Činnost** Storno a oprava obchodu,
**Platí od** zítřejší datum, **Druhá osoba** Ano – čtyři oči (krok Kontrola druhou osobou). Úkon pak provede uživatel s rolí, která má činnost
s příznakem Provádí; vznikne žádost, kterou potvrdí jiný uživatel s rolí s příznakem Schvaluje. Příklad je smyšlený.

## 3. Žádosti ke schválení a Úkony bez druhé osoby

Obě nabídky jsou pod **Investra › Nastavení › Schvalování a audit** (tamtéž je jako první Schvalovací matice).

**Žádosti ke schválení.** Jednorázový úkon (vrácení a storno ocenění, zveřejnění, ruční kurz, ruční úpis a odkup, ruční kategorie,
storno splátky a obchodu), který matice určuje pro čtyři oči nebo kroky, se neprovede hned. Vznikne žádost (stav **Čeká na potvrzení**),
kterou jiný člověk s rolí, která činnost schvaluje, **Potvrdí** (nebo **Zamítne**). Po posledním potvrzení se úkon provede jménem žadatele.
Žádost nelze ručně založit ani smazat; formulář je jen pro čtení, má tlačítka Potvrdit (s potvrzením), Zamítnout a Otevřít záznam,
tabulku potvrzení (Krok, Role kroku, Potvrdil, Potvrzeno dne) a historii.
Chyby: „Žádost musí potvrdit jiný člověk než žadatel a předchozí schvalovatelé.“, „Potvrdit lze jen čekající žádost.“
Žádost zamítne žadatel, nebo schvalovatel (role s příznakem Schvaluje). Schválení ocenění a ceny a výjimka z uzamčení se potvrzují přímo
na záznamu (ocenění, cena, žádost o výjimku), ne žádostí.

**Kde se činnost potvrzuje.** Ověřeno proti kódu (`_gate` v `investra_fund`, `valuation.py`, `instrument.py`, `lock_exception.py`):

| Činnost | Kde se potvrzuje |
|---|---|
| Schválení ocenění | na záznamu ocenění (tlačítko Schválit) |
| Schválení ceny | na záznamu ceny |
| Výjimka z uzamčení | na záznamu žádosti o výjimku |
| Vrácení a storno ocenění, zveřejnění ocenění | v Žádostech ke schválení |
| Ruční kurz, ruční úpis a odkup, ruční kategorie IFRS 9, storno a oprava splátky a obchodu | v Žádostech ke schválení |

Zveřejnění ocenění se potvrzuje v Žádostech, ne na záznamu (odchylka od původního zadání úkolu MN-18; vychází z kódu
`action_publish` → `_gate` a z testu `test_publish_with_four_eyes_goes_through_request`).

Na formuláři ocenění, obchodu, smlouvy derivátu, pohybu třídy, splátky nástroje a zařazení portfolia se u záznamu, kterému
čeká žádost, zobrazí žlutý pruh **Čeká na potvrzení v Žádostech ke schválení** s odkazem **Otevřít žádost**. Pruh jen informuje;
potvrzuje se až v žádosti. Ruční kurz žádný záznam nemá, proto se u něj pruh nezobrazí.

**Zeslabení pravidla** (například z čtyř očí na jednoho člověka) novým řádkem matice systém nehlídá; odpovědnost nese uživatel se Správou,
který řádek zadal. Ocenění ho ukáže v kontrole „Ocenění schvaluje druhá osoba“ a v seznamu Úkonů bez druhé osoby.

**Úkony bez druhé osoby.** Seznam jen pro čtení: kdy, činnost, záznam, kdo provedl, kniha a řádek matice. Zapisuje se každý úkon, který
provedl jeden člověk podle matice. Záznam nejde změnit ani smazat. Ocenění je ukáže v kontrole „Úkony od minulého ocenění provedla
druhá osoba“ (upozornění); úkony podle výchozích řádků (`Výchozí – chování před maticí`) se jen zapíší, v kontrole se neukazují.

## 4. Ručně doložené úplaty v ocenění

Úplatu, kterou Odoo nespočte z pravidla (například ji spočetl depozitář), zadáte přímo v ocenění. Záložka **Ručně doložené úplaty** je ve formuláři
ocenění viditelná, dokud ocenění není odesláno ke schválení; po odeslání už řádky nejde měnit („Ručně doložené úplaty po odeslání ke schválení nejde měnit.“).
Dřívější druh pravidla „externí“ zrušilo ZJ-03.
Opravu vypočtené úplaty, odměny nebo daně (tlačítko **Opravit** na záložce Úplaty) popisuje kap. 9.

| Pole | Povinné | Význam |
|---|---|---|
| **Třída** | ne | prázdná = společný náklad celého fondu (dělí se poměrem), jinak jen dané třídě |
| **Částka** | ano | nenulová; **+ náklad, − výnos** (viz níže) |
| **Měna** | ne | výchozí funkční měna fondu; cizí měna se přepočte kurzem k datu ocenění ze zdroje kurzů fondu |
| **Účet (náklad nebo výnos)** | ano | účet knihy typu náklad nebo výnos |
| **Poznámka** | ano | proč a od koho částka je |
| **Soubor s výpočtem** | ne | příloha |

**Znaménko částky.** Kladná částka je **náklad** (MD zvoleného nákladového účtu), záporná je **výnos** (D zvoleného výnosového účtu). Příklad:
poplatek správci 5 000 se zadá jako `5 000` na nákladový účet; vratka od správce 1 200 jako `−1 200` na výnosový účet, FK se zvýší o 1 200.
Opačné znaménko (kladná na výnosovém účtu, záporná na nákladovém) je účetně možné jako snížení výnosu nebo opravu nákladu; řádek na to
upozorní. Procento neuznatelnosti z výjimky daně na účtu platí i pro výnosový účet (přičte se k základu pravidla jako u výnosu v hlavní knize).

**Zaúčtování:** k datu ocenění MD zvolený účet (náklad; u výnosu D), D závazek z úplat (role účtu „fee_payable“). Řádky nesou původní měnu, takže závazek
přecení FX přecenění. Pořadí výpočtu: spolu s ostatními úplatami, **před** výkonnostní odměnou a daní; ruční úplata třídy proto snižuje základ odměny.
Náhled zaúčtování v ocenění ukáže tytéž řádky jako doklad po zaúčtování.

**Příklad (smyšlený):** fond v CZK, třídy A a B po 1 000 CZK, ruční úplata celého fondu 4 EUR, kurz 25,000 k datu ocenění → MD ostatní náklady 100 CZK,
D závazek z úplat 100 CZK; fond kapitál 2 000 → 1 900.

**Neaktuální výpočet.** Změní-li se po stisknutí **Spočítat** vstupy výpočtu (ruční úplata, pravidlo nebo verze úplaty, třída, úpis či odkup, obchod,
schválená cena, schvalovací matice, kurzy), formulář ocenění ukáže žlutý pruh „Vstupy výpočtu se změnily po posledním výpočtu (…)“ a ocenění nejde odeslat
ke schválení („Výpočet ocenění není aktuální, po výpočtu se změnilo: …“), dokud ho nespočtete znovu. Hlídají se jen uvedené vstupy. Souhrn s grafem kurzu tříd
se po každém Spočítat načte znovu.

**Historie kroků.** Záložka **Historie** ve formuláři ocenění ukazuje každý krok: založení (u další verze „Verze 2“ atd.), každé Spočítat
s FK a kurzy tříd, odeslání ke schválení, schválení po krocích, žádost podle matice, vrácení a storno s důvodem, zaúčtování, odeslání a potvrzení
depozitáři, zveřejnění. U kroku je, kdo a kdy ho provedl. Záznam nejde změnit ani smazat. Pole **Založil** je autor ocenění, **Spočítal** je ten,
kdo ocenění naposledy spočítal; ten ho nesmí schválit. Ocenění založená před zavedením historie mají jen kroky od nasazení.

## 5. Minimální nastavení pro první ocenění

- [ ] Fond: **Datum vzniku** vyplněné (jinak „Fond nemá datum vzniku.“), **Frekvence ocenění**, třídy (kap. 2, 3); z Data vzniku a frekvence karta fondu spočítá další ocenění.
- [ ] Schvalovací matice: výchozí řádky vznikly s modulem, takže **nic zakládat nemusíte**. Vlastní pravidla zadejte novým řádkem
      (činnost Schválení ocenění, případně Schválení ceny a Zveřejnění ocenění).
- [ ] Role a uživatelé (kap. 5): role s činností Schválení ocenění s příznakem **Provádí** pro připravovatele a **Schvaluje** pro schvalovatele.
      U čtyř očí potřebujete **dva různé uživatele**. Uživatele a role zakládá kap. 5.
- [ ] Kontrola: v ocenění bez upozornění „Ocenění schvaluje druhá osoba“ (jinak je nastavena jedna osoba).

## Nálezy pro pročištění

1. Frekvence ocenění se nekontroluje proti statutu ani zákonné lhůtě (deník 2026-11-04 „Interval ocenění“ to předpokládá);
   ocenění lze založit k libovolnému datu. Státní svátky a nepravidelné dny ze statutu se v dalším ocenění neberou.
2. Mimořádné ocenění nemá vlastní druh ani pole; je to ocenění k dřívějšímu dni.
3. Lhůta zveřejnění se nehlídá (rozhodnutí Martina 16. 11. 2026).
4. Výchozí řádky matice (od 1. 1. 2000) nejde měnit ani mazat běžným uživatelem; hlásí se „Výchozí řádek z modulu nejde měnit ani smazat; zadejte nový řádek s pozdějším „Platí od“.“ (MN-18). Pravidlo se mění jen novým řádkem.
5. Seznam matice (`default_order`) i formulář nezobrazují sloupec **Výchozí řádek**, takže řádky z modulu se od vlastních
   rozliší jen poznámkou „Výchozí – chování před maticí“.
6. Vlastní čtyři oči u schválení ceny a ocenění jsou ve formuláři záznamu, u ostatních činností v Žádostech; manuál zatím
   nepopisuje tlačítka na záznamech (kap. 8 a další).
