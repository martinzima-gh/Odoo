# 4. Kalendář ocenění a schvalovací matice

*Ověřeno v kódu, v prohlížeči neověřeno.*

Kapitola navazuje na fond z kap. 2 a 3 (Fond Alfa Růst, obhospodařovatel Alfa Investiční společnost, a.s.). Cíl: nastavit termíny
ocenění a pravidla schvalování tak, aby šlo spočítat a schválit první ocenění. Podrobný postup ocenění je v pozdější kapitole.

## 1. Kalendář ocenění

**Investra › Nastavení › Fondy › Fondy › [fond] › Kalendář ocenění.** Kalendář je záložka ve formuláři fondu; samostatnou nabídku nemá.
Řádky se přidávají v seznamu přímo (**Přidat řádek**).

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Datum ocenění** | ano | – | plánovaný den ocenění; ve fondu jedinečné („Datum ocenění je v kalendáři už uvedené.“) |
| **Plánované zveřejnění** | ne | prázdné | den, do kdy se má ocenění zveřejnit; bez něj platí termín = datum ocenění |

**Vztah k jiným polím:**

- **Frekvence ocenění** (Denně až Ročně, výchozí Měsíčně, kap. 2) je jen informace o plánované četnosti. Kalendář podle ní řádky
  **nevytváří** a ocenění je s ní **nekontroluje**. Dny ocenění zadáváte ručně.
- **Datum vzniku** (kap. 2) určuje začátek prvního oceňovacího období; bez něj první ocenění skončí chybou „Fond nemá datum vzniku.“
  Kalendář s ním nesouvisí: první řádek kalendáře může být kdykoli (kontrola, že není před datem vzniku, neexistuje).
- **Mimořádné ocenění** nemá zvláštní pole ani druh: zadá se jako další řádek kalendáře s požadovaným datem.

**Kde se kalendář používá:** jen v Přehledu fondů (karta fondu). Další ocenění po posledním zaúčtovaném je první datum kalendáře
po něm. Datum, které není mezi zveřejněnými oceněními a jeho termín (Plánované zveřejnění, jinak Datum ocenění) už uplynul,
zobrazí kartě „Ocenění po termínu“ (výjimka vyžadující zásah).

**Co kalendář nehlídá:** ocenění jde založit k libovolnému datu, i mimo kalendář. Řádek kalendáře jde měnit i mazat kdykoli,
i po prvním ocenění (v kódu žádný zámek není; ocenění se tím nemění, jen karta fondu). Kontrola kalendáře proti statutu a zákonné lhůtě, kterou předpokládá deník rozhodnutí (2026-11-04 „Interval ocenění“), v kódu není (nález 1).

**Příklad:** Fond Alfa Růst, frekvence Měsíčně, Datum vzniku 1. 1. 2027. Řádky: 31. 1. 2027 (zveřejnění 5. 2. 2027), 28. 2. 2027
(zveřejnění 5. 3. 2027), a mimořádné ocenění 15. 3. 2027 (zveřejnění prázdné). Čísla jsou smyšlená.

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

- [ ] Fond: **Datum vzniku** vyplněné (jinak „Fond nemá datum vzniku.“), **Frekvence ocenění**, třídy (kap. 2, 3).
- [ ] Kalendář ocenění: aspoň řádek pro první datum ocenění (není povinný pro založení ocenění, ale karta fondu jinak neukáže další ocenění).
- [ ] Fond: **Obhospodařovatel** vyplněný, pokud má platit matice obhospodařovatele; jinak platí výchozí řádky.
- [ ] Schvalovací matice: výchozí řádky vznikly s modulem, takže **nic nezakládat nemusíte**. Pro vlastní pravidla založte řádky
      (činnost Schválení ocenění, případně Schválení ceny a Zveřejnění ocenění).
- [ ] Skupiny uživatelů: **Investra: příprava ocenění** (zakládá a předkládá ocenění) a **Investra: schvalování ocenění**
      (schvaluje, zveřejňuje, mění matici). U čtyř očí potřebujete **dva různé uživatele**. Uživatele a role zakládá kap. 5.
- [ ] Kontrola: v ocenění bez upozornění „Ocenění schvaluje druhá osoba“ (jinak je nastavena jedna osoba).

## Nálezy pro pročištění

1. Kalendář se nekontroluje proti **Frekvenci ocenění**, **Datu vzniku**, statutu ani zákonné lhůtě (deník 2026-11-04 „Interval ocenění“
   to předpokládá); chybí i generování řádků podle frekvence.
2. Ocenění lze založit k datu mimo kalendář; kalendář slouží jen Přehledu fondů.
3. Mimořádné ocenění nemá vlastní druh ani pole; od řádkového data se neliší.
4. Záložka **Zpřísnění matice** ve fondu je seznam bez možnosti přidat řádek přímo (zjištěno ze zdrojového XML, neověřeno v prohlížeči).
5. Výchozí řádky matice (od 1. 1. 2000) nejde měnit ani mazat běžným uživatelem; pravidlo se mění jen novým řádkem pro obhospodařovatele.
6. Seznam matice (`default_order`) i formulář nezobrazují sloupec **Výchozí řádek**, takže řádky z modulu se od vlastních
   rozliší jen poznámkou „Výchozí – chování před maticí“.
7. Vlastní čtyři oči u schválení ceny a ocenění jsou ve formuláři záznamu, u ostatních činností v Žádostech; manuál zatím
   nepopisuje tlačítka na záznamech (kap. 8 a další).
