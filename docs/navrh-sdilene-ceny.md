# Návrh: sdílené tržní ceny přes fondy a měna ceny

Plán ke schválení. Červená zóna (`investra_instruments/models`, cena vstupuje do NAV v `investra_nav`, `record_guard`,
pravidla přístupu). Stav 11. 11. 2026, připravil Claude podle bodu 10 podkladu UX z 10. 11. 2026; upraveno podle
odpovědí uživatele z 11. 11. 2026. Nic není naprogramované.

**Bod 10 podkladu UX:** „Ceny: tabulka jen ID; ceny mají být sdílené přes fondy.“ Návrh v podkladu: sdílená tržní cena
se schvaluje jednou; cena z posudku zůstává na fondu; seznam s nástrojem, datem, cenou, měnou, zdrojem a stavem.
„Měna ceny“ tedy znamená, že u ceny musí být vidět, v jaké měně je.

**Cíl:** Tržní cenu nástroje zadat a schválit jednou a použít ji ve všech fondech, které nástroj drží. Cena z posudku
nebo jiná odchylka zůstává cenou fondu. Ocenění bere poslední známou cenu a upozorní na starou cenu.

## Jak to funguje dnes

- `investra.instrument.price`: povinný `fund_id`, `company_id` = společnost fondu, unikátnost (fond, nástroj, datum),
  stav Návrh → Schváleno, čtyři oči, schválenou nejde měnit ani smazat, cena na 8 desetinných míst.
- Ocenění (`valuation.py`, `_approved_price`) hledá schválenou cenu **téhož fondu přesně k datu ocenění**;
  hodnota = kusy × cena × kurz **měny nástroje** podle zdroje kurzů fondu. Rozhodnutí 2026-11-04 přitom říká
  „poslední známá cena“.
- Řádek portfolia ukládá jednotkovou cenu a zdroj (text), ne odkaz na záznam ceny. Hotové ocenění proto na pozdější
  změnu ceny nereaguje.
- Kontroly ocenění mají závažnost Stop (blokuje) a Upozornění (neblokuje, je vidět v kontrolách).

## Zjištěná rizika

1. Různé ceny téhož nástroje ke stejnému dni v různých fondech; nikdo to nekontroluje.
2. Import z Bloombergu a schválení se opakuje pro každý fond.
3. Měna ceny se neukazuje ani nekontroluje; cena v jiné měně z importu projde a zkreslí NAV.
4. Cenu jde zadat fondu, který nástroj „jen pro jiný fond“ nesmí držet.
5. O víkendu, svátku nebo u nelikvidního titulu ocenění skončí chybou, i když je k dispozici poslední známá cena.

## Varianty

| | A: kopírování do fondů | B: jeden model, fond nepovinný (doporučeno) | C: samostatná tržní cena + cena fondu |
|---|---|---|---|
| Princip | Průvodce založí z jedné ceny návrhy pro všechny fondy s pozicí | Cena bez fondu = sdílená tržní cena; cena s fondem = cena fondu (posudek, odchylka) | Nový model tržní ceny; cena fondu na ni odkazuje |
| Počet schválení | za každý fond | jedno | dvě úrovně |
| Riziko rozdílných cen | zůstává | odchylka jen s důvodem a upozorněním | nízké |
| Zásah do kódu | malý | střední | velký, dvojí záznamy |

Doporučení **B**: odpovídá návrhu v podkladu UX, zachová schvalování a ochrany a dnešní ceny zůstanou platné
bez převodu dat.

## Návrh řešení (varianta B)

**Model ceny**
- `fund_id` nepovinný. Prázdný = **sdílená tržní cena**; vyplněný = **cena fondu** (posudek, odchylka).
- `company_id` u ceny fondu = společnost fondu, u sdílené ceny = **kniha správce cen** (parametr v nastavení;
  rozhodnutí uživatele: Investra). Cenu nejde přesunout mezi sdílenou a fondem (ochrana knihy platí dál).
- Unikátnost: (nástroj, datum) pro sdílenou cenu a (fond, nástroj, datum) pro cenu fondu – dva unikátní indexy
  s podmínkou (prostá unikátnost by duplicitní sdílené ceny pustila, NULL se v PostgreSQL nerovná NULL).
- Cena fondu ke dni, ke kterému existuje sdílená cena, musí mít **důvod odchylky**.
- Nástroj „jen pro fond“: sdílenou cenu mít nesmí, cena fondu jen pro jeho fond.
- **Cena je vždy v jednotkách měny za kus** (ne v % jmenovité hodnoty ani v setinách). Přesnost **6 desetinných míst**
  (dnes 8; v `investra_test` má víc než 6 míst 0 z 11 cen a 0 z 8 obchodů, `investra_dev` ceny zatím nemá).

**Měna ceny**
- Nové povinné pole `currency_id` (výchozí = měna nástroje) v seznamu, formuláři i importu. Musí se rovnat měně
  nástroje; jinak import i uložení skončí chybou. Přepočet ceny z jiné měny se nedělá.

**Poslední známá cena a stáří ceny**
- Nové pole **Maximální stáří ceny (dny)** na typu nástroje jako návrh a na nástroji jako platná hodnota
  (stejně jako dnes klasifikace a způsob ocenění).
- Ocenění vezme schválenou cenu s nejnovějším datem **do data ocenění včetně**: přednost má cena fondu před
  sdílenou cenou téhož dne; novější sdílená cena má přednost před starší cenou fondu.
- Žádná cena do data ocenění → Stop (jako dnes).
- Cena starší než limit, nebo limit nevyplněný a cena není k datu ocenění → kontrola ocenění se závažností
  **Upozornění** (překonatelná: ocenění pokračuje, upozornění je vidět v kontrolách a v balíčku pro depozitáře).
  V detailu nástroj, datum ceny a stáří.
- Řádek portfolia dostane odkaz na použitý záznam ceny (`price_id`) a datum ceny.
- Upozornění také tehdy, když fond použil vlastní cenu, i když existuje sdílená ke stejnému dni (obě ceny a důvod).

**Změna schválené ceny**
- Hotová ocenění si drží svou cenu (uloženou na řádku), změna ceny v číselníku je nezmění. Kdo chce ocenění
  přepočítat, vrátí ho stávajícím postupem vrácení nebo storna.
- Schválenou cenu půjde opravit. Formulář před uložením upozorní (překonatelně): „Cena byla použita v oceněních: …“
  (podle `price_id` na řádcích; u starších ocenění bez odkazu podle fondu, nástroje a data ocenění).
- Oprava vrátí cenu do stavu Návrh, takže ji znovu schválí druhá osoba (zachová se rozhodnutí „Čtyři oči u ceny“).
- Změny ceny se evidují v historii záznamu (kdo, kdy, původní a nová hodnota). Smazat cenu použitou v ocenění nejde.

**Přístup a schvalování**
- Čtení: ceny vlastních společností a všechny sdílené ceny (pravidlo jen pro čtení
  `['|', ('fund_id', '=', False), ('company_id', 'in', company_ids)]`).
- Zápis a schválení sdílené ceny: jen uživatel s přístupem do knihy správce cen; čtyři oči beze změny.
- Přehled: ceny v návrhu u fondu = jeho ceny v návrhu + sdílené ceny v návrhu pro nástroje v jeho pozicích.

**Obrazovky (po sloučení modelu, zelené zadání pro AG)**
- Seznam cen: nástroj, datum, cena, měna, rozsah (Sdílená / Fond), fond, zdroj, stav, důvod odchylky; filtry.
- Nástroj a typ nástroje: pole Maximální stáří ceny.

## Dopad na data a účetnictví

- Stávající ceny zůstanou cenami fondu; `currency_id` se doplní měnou nástroje při aktualizaci modulu (ORM,
  po souhlasu a záloze). Hodnoty cen se zkrácením na 6 míst nezmění (ověřeno výše).
- Hotová ocenění a zaúčtované doklady se nemění. Nové ocenění k víkendu nebo svátku dnes skončí chybou, nově projde
  s poslední známou cenou a případným upozorněním.
- Referenční scénáře: očekávané hodnoty se nemění (ceny jsou k datu ocenění).

**Testy:** sdílená cena ve dvou fondech s různým zdrojem kurzů; cena fondu má přednost téhož dne a vyvolá
upozornění; cena fondu bez důvodu odmítnuta; duplicitní sdílená cena odmítnuta; měna ceny ≠ měna nástroje odmítnuta;
7 místo odmítnuto/zaokrouhleno; poslední známá cena v limitu bez upozornění, nad limitem s upozorněním, bez ceny Stop;
oprava schválené ceny vrátí návrh a hotové ocenění se nezmění; smazání použité ceny odmítnuto; uživatel bez knihy
správce cen sdílenou cenu přečte, ale nezaloží ani neschválí.

## Odpovědi uživatele (11. 11. 2026)

1. Kniha správce cen: Investra (upřesnit, která společnost, viz níže).
2. Měna ceny podle bodu 10: zobrazit a kontrolovat; přepočet z jiné měny se nedělá.
3. Cena vždy v jednotkách měny za kus, až 6 desetinných míst.
4. Poslední známá cena; při stáří nad parametr (na nástroji) překonatelné upozornění.
5. Bez složitého zrušení schválení: hotová ocenění drží svou cenu, změna ceny upozorní na použití v oceněních.

## Zbývá upřesnit

- Která společnost je „Investra“ pro knihu správce cen: Investra Services s.r.o., nebo investiční společnost
  (do jejího založení Services)? Řeší se parametrem, kód na tom nezávisí.
- Přesnost 6 míst i pro cenu na obchodu (dnes také 8)? Doporučení: ano, stejná cena na kus.

## Zóna a provedení

Červená zóna: provede Claude po schválení plánu. Pořadí: model, stáří ceny a pravidla přístupu
(`investra_instruments`) → hledání ceny, `price_id`, kontroly (`investra_nav`) → přehled (`investra_dashboard`) →
testy v `investra_test` → aktualizace `investra_dev` se souhlasem a zálohou → zelené zadání obrazovek pro AG.
