# Návrh: sdílené tržní ceny přes fondy a měna ceny

Plán ke schválení. Červená zóna (`investra_instruments/models`, cena vstupuje do NAV v `investra_nav`, `record_guard`,
pravidla přístupu). Stav 11. 11. 2026, připravil Claude podle bodu 10 podkladu UX z 10. 11. 2026. Nic není naprogramované.

**Cíl:** Tržní cenu kótovaného nástroje zadat a schválit jednou a použít ji ve všech fondech, které nástroj drží.
U každé ceny je vidět a kontroluje se, v jaké měně je. Fond může mít vlastní cenu jen jako doloženou odchylku.

## Jak to funguje dnes

- `investra.instrument.price`: povinný `fund_id`, `company_id` = společnost fondu, unikátnost (fond, nástroj, datum),
  stav Návrh → Schváleno, čtyři oči (zadavatel ani zakladatel neschvaluje), schválenou nejde měnit ani smazat.
- Ocenění (`valuation.py`, `_approved_price`) hledá schválenou cenu **téhož fondu přesně k datu ocenění**;
  hodnota = kusy × cena × kurz **měny nástroje** k datu ocenění podle zdroje kurzů fondu.
- Na řádku portfolia se ukládá jednotková cena a zdroj (text), ne odkaz na záznam ceny.
- Přehled (`dashboard.py`) počítá ceny v návrhu podle fondu.
- Nástroj je společný (bez společnosti); `fund_id` na nástroji znamená „jen pro tento fond“.

## Zjištěná rizika

1. **Různé ceny téhož nástroje ke stejnému dni v různých fondech** – nikdo to nekontroluje; u depozitáře a auditora
   těžko vysvětlitelné (rovné zacházení, Pravidla oceňování).
2. **Násobná práce** – import z Bloombergu (rozhodnutí 2026-11-04) a schválení se opakuje pro každý fond.
3. **Měna ceny je jen předpoklad** – cena se bere v měně nástroje. Cena z importu v jiné měně (např. pence místo liber,
   USD u nástroje vedeného v EUR) projde bez chyby a zkreslí NAV.
4. Cenu jde zadat fondu, který nástroj „jen pro jiný fond“ nesmí držet (chybí kontrola `instrument.fund_id`).

## Varianty

| | A: kopírování do fondů | B: jeden model, fond nepovinný (doporučeno) | C: samostatná tržní cena + cena fondu |
|---|---|---|---|
| Princip | Průvodce založí z jedné ceny návrhy pro všechny fondy s pozicí | Cena bez fondu = sdílená tržní cena; cena s fondem = odchylka fondu s důvodem | Nový model `investra.market.price`; cena fondu na ni odkazuje a schvaluje se ve fondu |
| Počet schválení | za každý fond | jedno (odchylka zvlášť) | dvě úrovně |
| Riziko rozdílných cen | zůstává | odchylka jen s důvodem a upozorněním v ocenění | nízké |
| Zásah do kódu | malý | střední (model, pravidla, hledání ceny, testy) | velký (nový model, migrace, dvojí záznamy) |
| Auditní stopa | duplicitní záznamy | jeden záznam + odkaz z řádku ocenění | nejpodrobnější, ale zdvojená |

Doporučení **B**: řeší všechna čtyři rizika, zachová stávající schvalování a ochrany a dnešní ceny fondů zůstanou platné
bez migrace dat.

## Návrh řešení (varianta B)

**Model ceny**
- `fund_id` nepovinný. Prázdný = **sdílená tržní cena**; vyplněný = **cena fondu**.
- Nové pole `scope` (Sdílená / Fond) jen pro zobrazení a filtry (počítané, uložené).
- `company_id` už nebude jen `related` na fond: u ceny fondu = společnost fondu, u sdílené ceny = **kniha správce cen**
  (nastavení, viz otázka 1). Ochrana knihy (`_book_fields`) platí dál: cenu nejde přesunout mezi sdílenou a fondem.
- Unikátnost: (nástroj, datum) pro sdílenou cenu a (fond, nástroj, datum) pro cenu fondu – dva unikátní indexy
  s podmínkou (PostgreSQL bere NULL jako různé hodnoty, prostá unikátnost by duplicitní sdílené ceny pustila;
  syntaxi indexu s podmínkou v Odoo 20 ověřím).
- Cena fondu ke dni, ke kterému existuje sdílená cena, musí mít **důvod odchylky** (např. jiný trh, znalecký posudek,
  nelikvidní pozice ve fondu).
- Nástroj „jen pro fond“ (`instrument.fund_id`): sdílenou cenu mít nesmí, cena fondu jen pro jeho fond.

**Měna ceny**
- Nové povinné pole `currency_id` (výchozí = měna nástroje), viditelné v seznamu, formuláři i importu.
- Fáze 1 (doporučeno teď): měna ceny **musí** být měna nástroje – kontrola zachytí chybný sloupec měny při importu.
  Hodnota NAV ani účtování se nemění, FX a přecenění na RH se dál dělí podle měny nástroje.
- Fáze 2 (jen když ji první fondy potřebují): cena v jiné měně se přepočte na měnu nástroje křížovým kurzem
  k datu ocenění podle zdroje kurzů fondu; do řádku ocenění se uloží původní cena, měna i kurz. Plán zvlášť.

**Ocenění**
- Hledání ceny: schválená cena fondu k datu → jinak schválená sdílená cena k datu → jinak dnešní chyba „Chybí schválená cena“.
- Řádek portfolia dostane odkaz na použitý záznam ceny (`price_id`) a příznak, zda šlo o cenu fondu.
- Nová kontrola ocenění (Upozornění): fond použil vlastní cenu, i když existuje sdílená; ukáže obě ceny a důvod.
- Přepočet do funkční měny zůstává ve fondu: sdílená cena je v měně nástroje, každý fond ji přepočte svým kurzem
  (ČNB / ECB podle rozhodnutí „Zdroj kurzu“). Rozdíl v Kč/EUR mezi fondy je tedy správný.

**Přístup a schvalování**
- Čtení: uživatel s právem číst ceny vidí ceny svých společností **a všechny sdílené ceny** (pravidlo přístupu
  `['|', ('fund_id', '=', False), ('company_id', 'in', company_ids)]` jen pro čtení).
- Zápis a schválení sdílené ceny: jen uživatel s přístupem do knihy správce cen (příprava / schvalování ocenění).
- Čtyři oči, zámek schválené ceny a zákaz smazání platí beze změny.
- Přehled: ceny v návrhu u fondu = jeho ceny v návrhu + sdílené ceny v návrhu pro nástroje v jeho pozicích.

**Obrazovky (po sloučení modelu, zelené zadání pro AG)**
- Seznam cen: sloupce Rozsah, Měna, Důvod odchylky; filtry Sdílené / Fond; formulář s fondem nepovinným a nápovědou.

## Dopad na data a účetnictví

- Stávající ceny v `investra_dev` a `investra_test` zůstanou cenami fondu; `currency_id` se jim doplní měnou nástroje
  při aktualizaci modulu (přes ORM, po souhlasu a záloze).
- Výsledek NAV ani zaúčtované doklady se nemění; dosavadní ocenění zůstávají, nové pole `price_id` u nich bude prázdné.
- Referenční scénáře: očekávané hodnoty se nemění; přibudou testy (níže).

**Testy:** sdílená cena použitá dvěma fondy s různým zdrojem kurzů; cena fondu má přednost a vyvolá upozornění;
cena fondu bez důvodu při existující sdílené ceně odmítnuta; duplicitní sdílená cena odmítnuta; měna ceny ≠ měna
nástroje odmítnuta; uživatel bez knihy správce cen sdílenou cenu nezaloží ani neschválí, ale přečte; nástroj
„jen pro fond“ bez sdílené ceny; přesun ceny mezi sdílenou a fondem odmítnut.

## Otázky pro uživatele

1. **Kniha správce cen:** která společnost sdílené ceny „vlastní“ a kdo je smí zadávat – investiční společnost
   (obhospodařovatel/administrátor fondů), nebo Investra Services? Doporučení: parametr v nastavení, výchozí
   investiční společnost; do jejího založení Investra Services.
2. **Co je bod 10 „měna ceny“:** stačí měnu ceny zobrazit a kontrolovat (fáze 1), nebo už první fondy mají ceny
   v jiné měně, než je měna nástroje (fáze 2)?
3. **Kotace v procentech nebo setinách** (dluhopisy v % jmenovité hodnoty, akcie v pencích): řešit „násobitelem kotace“
   na ceně? Doporučení: ne teď, až podle pozic prvního fondu.
4. **Poslední známá cena:** rozhodnutí 2026-11-04 říká „poslední známá cena“, kód chce cenu přesně k datu ocenění
   (víkendy, svátky, nelikvidní tituly). Doporučení: samostatný krok hned po tomto – hledat poslední schválenou cenu
   do data ocenění s limitem stáří (parametr fondu) a upozorněním v ocenění.
5. **Oprava schválené sdílené ceny:** dnes ji nejde změnit; chyba by se týkala více fondů. Doporučení: zatím řešit
   cenou fondu s důvodem; řízené zrušení schválení (jen dokud na ceně nestojí ocenění od stavu Ke schválení) jako
   otevřený bod.

## Zóna a provedení

Červená zóna: provede Claude po schválení plánu a odpovědích na otázky 1 a 2. Pořadí: model a pravidla přístupu
(`investra_instruments`) → hledání ceny, `price_id` a kontrola (`investra_nav`) → přehled (`investra_dashboard`) →
testy v `investra_test` → aktualizace `investra_dev` se souhlasem a zálohou → zelené zadání obrazovek pro AG.
