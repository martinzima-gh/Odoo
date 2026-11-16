# Návrh: oprava zveřejněného ocenění

Stav: **návrh k rozhodnutí Martinem**, kód se nemění. Zóna červená (NAV, účtování, zámek období, kurz třídy).
Podnět: Martin 15. 11. 2026 – zveřejněné ocenění může být výjimečně chybné a musí existovat řízená cesta opravy.

## Stav dnes (ověřeno v kódu 16. 11. 2026, `investra_nav/models/valuation.py`, `lock_exception.py`)

- Smazat jde jen ocenění ve stavu Návrh a Spočteno (`unlink`).
- Vrátit nebo stornovat s novou verzí jde jen do stavu Potvrzeno depozitářem (`action_return`, `action_reverse`).
  Zveřejněné ocenění stornovat nejde.
- Zveřejnění nastaví zámek období knihy (`fiscalyear_lock_date`) na datum ocenění. Snížit ho pod datum zveřejněného
  ocenění nejde; výjimka ze zámku (žádost podle matice) jen dočasně pustí účtování do zamčeného období vybranému uživateli.
- Nevratný `hard_lock_date` se nastavuje ručně po auditu závěrky; výjimka ho neotevře.
- Na zveřejněné ocenění navazuje: kurz třídy jako očekávaná cena úpisů a odkupů (`investra.class.movement.valuation_id`),
  přemostění dalšího ocenění (`previous_id`, FK t−1, srovnávací hodnoty odměn), potvrzení depozitáře, balíček ocenění
  s kontrolním součtem, později výkazy ČNB a předání kurzu do IS.
- Nové ocenění fondu vznikne až po zveřejnění předchozího, takže chyba se typicky zjistí při práci na dalším ocenění.

**Mezera:** chybně zveřejněné ocenění nejde stáhnout ani nahradit opravenou verzí; výjimka ze zámku dovolí jen ruční
doklady, ale kurz, FK ani stav ocenění nezmění a není z ní vidět, že kurz byl chybný.

## Zásady (platí pro všechny varianty)

1. Nic se nemaže. Původní ocenění, jeho doklady a zveřejněný kurz zůstávají v historii s důvodem opravy.
2. Opravu zadává jedna osoba a potvrzuje druhá (nová činnost schvalovací matice „Oprava zveřejněného ocenění“).
3. Opravené ocenění projde znovu celým postupem včetně depozitáře a zveřejnění.
4. Systém vyčíslí dopad: rozdíl FK a kurzu každé třídy (částka a %) a seznam úpisů a odkupů vypořádaných chybným kurzem.
   O kompenzaci investorů systém nerozhoduje a neúčtuje ji sám; připraví podklad.
5. Po nevratném zámku (po auditu) se zpětně neopravuje nikdy; zbývá jen oprava v běžném období.

## Varianty

| | A. Oprava v dalším období | B. Stažení a nová verze | C. Podle významnosti (A + B) |
|---|---|---|---|
| Co se stane | Zveřejněné ocenění zůstane. Založí se záznam „Zjištěná chyba ocenění“ (důvod, vyčíslený dopad, rozhodnutí) a oprava se zaúčtuje v běžném období; projeví se v dalším kurzu | Žádost se čtyřma očima → systém stornuje doklady ocenění k jejich datu (interní výjimkou ze zámku), původní verze dostane stav „Nahrazeno opravou“, vznikne nová verze v návrhu; po zveřejnění se zámek obnoví | Systém spočítá dopad na kurz; pod prahem ze statutu nabídne A, nad prahem B |
| Zveřejněný kurz | nemění se | nahrazen novým, starý zůstává v historii označený jako chybný | podle větve |
| Pozdější ocenění | nedotčená | musí se nejdřív vrátit nebo nahradit, od nejnovějšího zpět (řetěz) | podle větve |
| Úpisy a odkupy za chybný kurz | jen seznam v záznamu chyby | seznam + rozdíl proti opravenému kurzu jako podklad pro IS | podle větve |
| Pracnost | malá (nový model, sestava, bez zásahu do zámku) | velká (zámek, storna, stavy, řetěz ocenění, přemostění, testy) | největší, ale B lze omezit |
| Riziko | nevýznamná chyba ano; významná chyba by zůstala ve zveřejněném kurzu | zásah do uzamčeného období; chyba v řetězu by rozbila navazující ocenění | práh musí být v předpisu, ne v kódu |

## Doporučení: C ve dvou krocích

**Krok 1 (malý):** varianta A + omezené B jen pro případ „chyba zjištěná hned po zveřejnění“:

- B se povolí, jen když jde o **poslední** zveřejněné ocenění fondu, po něm není žádné ocenění mimo Návrh a Spočteno,
  žádný zaúčtovaný úpis ani odkup nepoužil jeho kurz a období není nevratně zamčené. Pak není co řetězit ani kompenzovat.
  Rozpracované další ocenění (Návrh, Spočteno) se před opravou zruší tlačítkem z OC-01 a po opravě založí znovu.
- Ve všech ostatních případech jen A se záznamem chyby a vyčíslením dopadu.

**Krok 2 (až s IS a prvním skutečným fondem):** plné B s řetězem pozdějších ocenění a podkladem pro kompenzace,
práh významnosti jako parametr fondu podle statutu.

Důvod: krok 1 pokryje nejčastější chybu (překlep zjištěný den po zveřejnění) bez zásahu do navazujících ocenění;
plné B bez IS neumí dohledat dopad na investory, takže by dalo falešný pocit úplné opravy.

## Rozsah kroku 1 (po schválení; červená zóna, plán schvaluje Martin)

1. Činnost matice `valuation_correct` (výchozí: schvalovatel požádá, jiný schvalovatel potvrdí), žádost s povinným důvodem.
2. Model „Zjištěná chyba ocenění“: ocenění, důvod, způsob (A / B), dopad po třídách, dotčené pohyby, kdo a kdy, příloha.
3. Akce „Opravit zveřejněné ocenění“ ve formuláři: kontrola podmínek, náhled dopadu a dokladů ke stornu
   (společný model `investra.posting.preview`), po potvrzení storna, stav „Nahrazeno opravou“, nová verze.
4. Zámek: snížení `fiscalyear_lock_date` na datum předchozího zveřejněného ocenění jen uvnitř této akce
   (stejná pojistka jako `_ALLOW` v `lock_exception.py`), zveřejnění nové verze ho vrátí.
5. Přehled fondů: výjimka „Ocenění se opravuje“; seznam Ocenění: filtr na nahrazená.
6. Testy: podmínky odmítnutí, storna k datu, obnovení zámku, přemostění nové verze, čtyři oči, historie.

Nový stav ocenění je změna výběru existujícího pole (migrace není potřeba, hodnota se jen přidává).

## K rozhodnutí

1. Varianta (doporučení: C, krok 1 teď, krok 2 později).
2. Kdo opravu žádá a kdo potvrzuje; má potvrzovat i někdo mimo oceňování (compliance, vedení)?
3. Má se o opravě automaticky zakládat záznam pro depozitáře, nebo stačí nové kolo potvrzení?
4. Název stavu: „Nahrazeno opravou“ × použít stávající „Stornováno“ s příznakem.
5. Práh významnosti: odkud se vezme (statut, Pravidla oceňování) a zda je stejný pro všechny třídy.

## Opora v předpisech – NEOVĚŘENO

Znění jsem neověřoval; před schválením kroku 1 ověřit ve Sbírce zákonů a u ČNB, výklad potvrdit s compliance a auditorem:

- ZISIF (zákon č. 240/2013 Sb.) a jeho prováděcí předpisy: pravidla oceňování, lhůty a povinnosti při chybně
  stanovené aktuální hodnotě podílového listu nebo investiční akcie, včetně případné povinnosti kompenzace investorů
  a hranice, od které vzniká. Konkrétní ustanovení neuvádím, abych nevymýšlel citaci.
- Statut fondu a vnitřní předpis Pravidla oceňování: postup při chybě, práh významnosti, role depozitáře.
- Vyhláška č. 501/2002 Sb. a ČÚS pro finanční instituce: oprava chyb minulých období v účetnictví fondu
  (varianta A účtuje opravu v běžném období – ověřit, kam a zda podle významnosti).
- Oznamovací povinnosti vůči ČNB a depozitáři při chybě ocenění.
