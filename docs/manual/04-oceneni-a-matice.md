# 4. Ocenění a schvalovací matice

*Ověřeno v kódu, v prohlížeči neověřeno.*

Kapitola navazuje na fond z kap. 2 a 3 (Fond Alfa Růst, obhospodařovatel Alfa Investiční společnost, a.s.). Cíl: nastavit frekvenci
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

**Investra › Nastavení › Fondy › Schvalovací matice.** Seznam je seskupený podle činnosti. Matice určuje, kolik lidí a s jakou
nejnižší rolí činnost provede. Role jsou dvě skupiny uživatelů: **Investra: příprava ocenění** (nižší) a **Investra: schvalování
ocenění** (vyšší; splní i požadavek na přípravu).

### Řádek matice

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Činnost** | ano | – | jedna z deseti činností, viz níže |
| **Obhospodařovatel** | ne | prázdné | kniha druhu Investiční společnost; řádek platí pro všechny její fondy. Prázdné = výchozí matice. Zobrazí se jen, není-li vyplněn fond |
| **Zpřísnění pro fond** | ne | prázdné | řádek jen pro jeden fond; smí pravidlo jen zpřísnit. Zobrazí se jen, není-li vyplněn obhospodařovatel |
| **Platí od** | ano | dnes | od kdy řádek platí; platí vždy nejnovější řádek s datem do dne ocenění či úkonu |
| **Kdo provádí (nejnižší role)** | ano | Příprava ocenění | nejnižší role toho, kdo činnost provede nebo ocenění předloží |
| **Jen tito uživatelé** (provádí) | ne | prázdné | jmenovitě povolení; prázdné = kdokoli s rolí |
| **Druhá osoba** | ano | Ano – čtyři oči | **Ne – stačí jeden člověk**, **Ano – čtyři oči**, **Kroky** |
| **Počet osob** | jen čtení | dopočet | provádějící + počet kroků (u „Ne“ vždy 1) |
| **Poznámka** | ne | – | např. odkaz na vnitřní předpis (jen název a článek, ne text) |

**Kdo schvaluje** (tabulka kroků, viditelná u Ano a Kroky; řádky se řadí tahem za úchyt):

| Pole kroku | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Pořadí** | – | 10 | pořadí kroku (úchyt pro přesun) |
| **Krok** | ano | Kontrola druhou osobou | název kroku |
| **Nejnižší role** | ano | Schvalování ocenění | nejnižší role schvalovatele |
| **Jen tito uživatelé** | ne | prázdné | jmenovitě povolení; prázdné = kdokoli s rolí |

Pole **Výchozí řádek** (`builtin`, řádky dodané modulem) ve formuláři není; pole **Počet osob** a **Výchozí řádek** se nezadávají.
Pole **Obhospodařovatel**, **Zpřísnění pro fond** a **Poznámka** jsou ve formuláři i v seznamu; v seznamu jsou navíc volitelné sloupce
**Počet osob** (skrytý) a filtr **Bez druhé osoby**.

**Chování voleb:**

- **Ne** smaže kroky a ukáže varování, že úkon provede jeden člověk bez druhé osoby a zapíše se do Úkonů bez druhé osoby.
- **Ano** doplní jeden krok „Kontrola druhou osobou“ (role Schvalování ocenění); víc kroků u Ano nejde.
- **Kroky** vyžaduje aspoň jeden krok; každý krok musí provést jiný člověk než zadavatel a předchozí schvalovatelé.

**Kontroly (znění chyb):**

- „Řádek patří buď obhospodařovateli, nebo fondu (zpřísnění).“
- „Bez druhé osoby nemá řádek schvalovatele. Smažte je nebo změňte volbu.“
- „Čtyři oči mají jednoho schvalovatele; pro více použijte Kroky.“
- „Kroky musí mít aspoň jednoho schvalovatele.“
- „Pro činnost a den už řádek matice existuje.“ (jedinečné: činnost, obhospodařovatel, fond, Platí od)
- „Fond … smí pravidlo matice jen zpřísnit; platí … s nejnižšími rolemi podle matice.“ (řádek fondu musí mít aspoň tolik osob,
  aspoň tak vysoké role a jmenovité omezení nejvýš tak široké jako pravidlo obhospodařovatele či výchozí)

**Kdo smí matici měnit:** jen skupina **Investra: schvalování ocenění** („Schvalovací matici mění jen skupina schvalování ocenění.“).
Ostatní s Odoo skupinou účetnictví jen pro čtení (`account.group_account_readonly`, obě role ji zahrnují) matici jen čtou. Záložka fondu
**Zpřísnění matice** ukazuje řádky fondu (Činnost, Platí od, Kdo provádí, Druhá osoba, Počet osob); doporučený způsob zadání je
nabídka Schvalovací matice s polem **Zpřísnění pro fond** (zadání přímo ze záložky v prohlížeči neověřeno).

**Co nejde změnit (nejde ani zpětně):**

- „Řádek matice nejde založit zpětně; „Platí od“ musí být dnes nebo později.“
- „Platný řádek matice nejde měnit ani mazat. Změnu zadejte novým řádkem s pozdějším „Platí od“.“ Řádek s „Platí od“ **dnes** nebo v budoucnu
  jde ještě upravit i smazat; od zítřka už ne. Změna kroků se počítá jako změna řádku.
- Každá změna se zapíše do historie řádku (chatter) a ocenění ji ukáže v kontrole „Schvalovací matice se od minulého ocenění nezměnila“
  (upozornění).

### Činnosti

| Činnost | Výchozí (bez řádku matice) |
|---|---|
| Schválení ocenění | provádí Příprava, schvaluje Schvalování (čtyři oči) |
| Vrácení a storno ocenění | Schvalování, jeden člověk |
| Zveřejnění ocenění | Schvalování, jeden člověk |
| Schválení ceny | provádí Příprava, schvaluje Schvalování (čtyři oči) |
| Ruční kurz a přepis kurzu | Schvalování, jeden člověk |
| Výjimka z uzamčení | Schvalování, schvaluje Schvalování (čtyři oči) |
| Ruční zadání úpisu a odkupu | Příprava, jeden člověk |
| Ruční přepsání kategorie IFRS 9 | Příprava, jeden člověk |
| Storno a oprava splátky nástroje | Příprava, jeden člověk |
| Storno a oprava obchodu | Příprava, jeden člověk |

Výchozí chování je i uloženo jako deset řádků bez obhospodařovatele i fondu, **Platí od** 1. 1. 2000, poznámka „Výchozí – chování před maticí“.
Tyto řádky vznikají s modulem; po založení fondu se nic dalšího nezakládá. Pro fond bez obhospodařovatele platí jen ony.
Platí tedy, že **bez jediného vlastního řádku** už první ocenění vyžaduje druhou osobu.

**Pořadí hledání pravidla pro fond a činnost:** nejnovější řádek obhospodařovatele fondu (k danému dni) → jinak výchozí řádek → jinak
vestavěné chování. Řádek fondu platí, jen když je přísnější nebo stejný. Sdílený záznam (kurz zdroje, sdílená cena) se řídí
nejpřísnějším pravidlem ze všech dotčených fondů.

### Příklad

Fond Alfa Růst má Obhospodařovatele Alfa Investiční společnost, a.s. a schvaluje ocenění podle výchozího řádku: provádí Příprava,
schvaluje Schvalování. Chcete, aby u tohoto fondu storno obchodu potvrzovala druhá osoba (výchozí je jeden člověk). Nový řádek:
**Činnost** Storno a oprava obchodu, **Zpřísnění pro fond** Fond Alfa Růst, **Platí od** dnes, **Kdo provádí** Příprava ocenění,
**Druhá osoba** Ano – čtyři oči (krok Kontrola druhou osobou, role Schvalování ocenění). Zpřísnění prošlo, protože 2 osoby > 1.
Příklad je smyšlený.

## 3. Žádosti ke schválení a Úkony bez druhé osoby

Obě nabídky jsou pod **Investra › Nastavení › Auditní stopa**.

**Žádosti ke schválení.** Jednorázový úkon (vrácení a storno ocenění, zveřejnění, ruční kurz, ruční úpis a odkup, ruční kategorie,
storno splátky a obchodu), který matice určuje pro čtyři oči nebo kroky, se neprovede hned. Vznikne žádost (stav **Čeká na potvrzení**),
kterou jiný člověk s požadovanou rolí **Potvrdí** (nebo **Zamítne**). Po posledním potvrzení se úkon provede jménem žadatele.
Žádost nelze ručně založit ani smazat; formulář je jen pro čtení, má tlačítka Potvrdit (s potvrzením), Zamítnout a Otevřít záznam,
tabulku potvrzení (Krok, Nejnižší role, Jen tito uživatelé, Potvrdil, Potvrzeno dne) a historii.
Chyby: „Žádost musí potvrdit jiný člověk než žadatel a předchozí schvalovatelé.“, „Potvrdit lze jen čekající žádost.“
Žádost zamítne žadatel, nebo schvalovatel s požadovanou rolí. Schválení ocenění a ceny a výjimka z uzamčení se potvrzují přímo
na záznamu (ocenění, cena, žádost o výjimku), ne žádostí.

**Úkony bez druhé osoby.** Seznam jen pro čtení: kdy, činnost, záznam, kdo provedl, kniha a řádek matice. Zapisuje se každý úkon, který
provedl jeden člověk podle matice. Záznam nejde změnit ani smazat. Ocenění je ukáže v kontrole „Úkony od minulého ocenění provedla
druhá osoba“ (upozornění); úkony podle výchozích řádků (`Výchozí – chování před maticí`) se jen zapíší, v kontrole se neukazují.

## 4. Minimální nastavení pro první ocenění

- [ ] Fond: **Datum vzniku** vyplněné (jinak „Fond nemá datum vzniku.“), **Frekvence ocenění**, třídy (kap. 2, 3); z Data vzniku a frekvence karta fondu spočítá další ocenění.
- [ ] Fond: **Obhospodařovatel** vyplněný, pokud má platit matice obhospodařovatele; jinak platí výchozí řádky.
- [ ] Schvalovací matice: výchozí řádky vznikly s modulem, takže **nic nezakládat nemusíte**. Pro vlastní pravidla založte řádky
      (činnost Schválení ocenění, případně Schválení ceny a Zveřejnění ocenění).
- [ ] Skupiny uživatelů: **Investra: příprava ocenění** (zakládá a předkládá ocenění) a **Investra: schvalování ocenění**
      (schvaluje, zveřejňuje, mění matici). U čtyř očí potřebujete **dva různé uživatele**. Uživatele a role zakládá kap. 5.
- [ ] Kontrola: v ocenění bez upozornění „Ocenění schvaluje druhá osoba“ (jinak je nastavena jedna osoba).

## Nálezy pro pročištění

1. Frekvence ocenění se nekontroluje proti statutu ani zákonné lhůtě (deník 2026-11-04 „Interval ocenění“ to předpokládá);
   ocenění lze založit k libovolnému datu. Státní svátky a nepravidelné dny ze statutu se v dalším ocenění neberou.
2. Mimořádné ocenění nemá vlastní druh ani pole; je to ocenění k dřívějšímu dni.
3. Lhůta zveřejnění se nehlídá (rozhodnutí Martina 16. 11. 2026).
4. Záložka **Zpřísnění matice** ve fondu je seznam bez možnosti přidat řádek přímo (zjištěno ze zdrojového XML, neověřeno v prohlížeči).
5. Výchozí řádky matice (od 1. 1. 2000) nejde měnit ani mazat běžným uživatelem; pravidlo se mění jen novým řádkem pro obhospodařovatele.
6. Seznam matice (`default_order`) i formulář nezobrazují sloupec **Výchozí řádek**, takže řádky z modulu se od vlastních
   rozliší jen poznámkou „Výchozí – chování před maticí“.
7. Vlastní čtyři oči u schválení ceny a ocenění jsou ve formuláři záznamu, u ostatních činností v Žádostech; manuál zatím
   nepopisuje tlačítka na záznamech (kap. 8 a další).
