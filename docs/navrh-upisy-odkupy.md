# Návrh: úpisy a odkupy – zdroj, zaokrouhlení, poplatek, historie (bod 8 UX)

Stav: **schváleno uživatelem 11. 11. 2026** (včetně G). Pořadí provedení: F, G, pak A–E. Zóna: zdroj a historie oranžová;
zaokrouhlení, poplatek, zaúčtování a zámek ocenění červená (účtování, NAV). Navazuje na rozhodnutí „Kurz úpisu
v průběhu období“ (2026-11-04), „Cesta úpisů“ (2026-11-09) a „Detail účetních událostí“ (2026-11-11).

## Jak to funguje dnes

- Model `investra.class.movement` (`investra_nav/models/movement.py`): třída, datum, typ, kusy, částka v měně
  kurzu, kurz měny, částka ve funkční měně, vazba na účetní událost.
- Chybí: zdroj (IS / ruční zadání), cena za kus, vazba na ocenění s cenou, poplatek, rozdíl ze zaokrouhlení
  kusů, historie změn (model nemá `mail.thread`).
- Zaúčtování `_book()` volají **jen testy**; v UI tlačítko není. Událost má dva řádky: banka / kapitál třídy.
- Zaúčtovaný pohyb nejde změnit ani smazat; storno ani oprava neexistuje.
- Ocenění bere pohyby s datem v `(datum předchozího zaúčtovaného ocenění, datum ocenění]`.

### Zámek schváleného ocenění – ověřeno v kódu 2026-11-11

| Co | Zámek od schválení ocenění? |
|---|---|
| Ruční kurz (`investra.rate`) | **ano** – odmítne se kurz k datu ≤ datu ocenění ve stavu Schváleno a dál |
| Doklady v účetnictví (obchody, splátky, časové rozlišení, ruční doklady) | **ne** – brání jen `hard_lock_date`, který se nastaví až při zveřejnění |
| Úpisy a odkupy | **ne** |

Důsledek: úpis nebo odkup s datem ≤ datu schváleného ocenění, zadaný až po schválení, se do toho ocenění
nedostane a příští ocenění ho také nevezme (začíná až po datu předchozího). **Do NAV by se nedostal nikdy.**
Totéž platí pro obchod nebo doklad: změní účetnictví pod schváleným oceněním bez upozornění.

## Návrh řešení

**A. Zdroj (oranžová)**
- `source`: IS / ruční zadání; `external_ref` (dávka a řádek z IS, jedinečný v rámci fondu).
- Ruční zadání vyžaduje důvod.

**B. Cena a zaokrouhlení (červená)** – odpověď 1 a 5
- Pole `price` (cena za kus v měně kurzu) a `valuation_id` (ocenění, z něhož cena je).
- Parametry na fondu jako výchozí, na třídě s přepsáním (stejně jako desetinná místa kurzu): desetinná místa
  kusů (výchozí 6), způsob zaokrouhlení kusů (výchozí dolů), komu patří rozdíl (výchozí zůstává ve fondu) (zůstává ve fondu → kapitál třídy / vrací se investorovi
  → závazek, výplatu zadává IS).
- Vše posílá a určuje IS: kusy, cenu, hrubou částku, poplatek i rozdíl. Odoo nic nedopočítává, jen kontroluje:
  `hrubá částka = kusy × cena + poplatek + rozdíl`, kusy odpovídají desetinným místům a způsobu třídy,
  cena = zveřejněný kurz třídy (odchylka jen s důvodem).

**C. Poplatek (červená)** – odpověď 2
- Parametr na fondu, přepsání na třídě: sazba vstupního a výstupního poplatku. Poplatek se platí ven
  (obhospodařovatel nebo distributor, příjemce se eviduje u pohybu; parametr určuje výchozího): závazek fondu
  vůči příjemci, kapitál třídy dostane jen čistou částku.
- Z IS přichází částka poplatku; Odoo ji porovná se sazbou. Při ručním zadání se poplatek předvyplní ze sazby
  a uživatel ho může upravit; odchylka od sazby se zobrazí v kontrolách ocenění.

**D. Historie změn (oranžová)**
- `mail.thread` s tracking u věcných polí (kdo, kdy, z čeho na co).
- Oprava zaúčtovaného pohybu = storno (opačná událost k datu původního pohybu) a nový pohyb s odkazem na
  opravovaný. Jde jen do ocenění, které ještě není schválené (odpověď 3, zámek F).

**E. Zaúčtování v UI (červená)** – odpověď 4
- Tlačítko „Zaúčtovat“ pro skupinu přípravy ocenění, i hromadně ze seznamu. Před zaúčtováním kontroly B a C.

**F. Obecný zámek ocenění – vrstva 1, měkký (červená, nové; samostatný krok před B–E)**
- Od stavu Ke schválení (dál Schváleno, Zaúčtováno, U depozitáře, Potvrzeno) nejde do fondové knihy zaúčtovat
  ani stornovat doklad s datem ≤ datu ocenění, kromě dokladů samotného ocenění. Kontrola na jednom místě
  (`investra_posting`, zaúčtování dokladu) – pokryje obchody, splátky, časové rozlišení, úpisy, odkupy i ruční doklady.
- Úpis a odkup s datem ≤ datu takového ocenění nejde založit, změnit ani smazat ani před zaúčtováním.
- Cesta ven zůstává: vrácení ocenění (dnešní postup) – pak se do něj účtovat dá.

**G. Zámek po zveřejnění – vrstva 2 a pojistka (červená, návrh, čeká na potvrzení)**
- Ověřeno v Odoo 20: `hard_lock_date` nejde zrušit ani posunout zpět, ani administrátorem. Dnes ho nastaví
  zveřejnění ocenění, takže pojistka na zrušení dnes neexistuje.
- Návrh: zveřejnění nastaví zámek pro všechny (`fiscalyear_lock_date`) k datu ocenění. Pojistkou je
  standardní výjimka Odoo (`account.lock_exception`): důvod, uživatel, čas konce, odvolání, auditní stopa změn
  během výjimky. Investra doplní: výjimku zakládá jen skupina schvalování ocenění, účinná až po potvrzení
  druhou osobou, je vidět v kontrolách příštího ocenění.
- `hard_lock_date` (nevratný) až po účetní závěrce ověřené auditorem, ruční krok schvalovatele.
- Mění rozhodnutí „Zaúčtování ocenění“ (2026-11-06) jen v tom, kterým zámkem Odoo se období uzamyká.

## Dopad na data a účetnictví

- Migrace: stávající pohyby dostanou `source = ruční`, `price = částka / kusy`, poplatek a rozdíl 0;
  parametry fondu výchozí (6 míst, dolů, rozdíl ve fondu).
- Zaúčtované doklady se nemění. Nové pohyby s poplatkem nebo rozdílem mají 3–4 řádky; nové role účtů
  (závazek z poplatku, rozdíl ze zaokrouhlení, závazek vůči investorovi) v `investra_chart_fund`.
- Kapitál třídy a měřená výkonnost berou čistou částku. Očekávané hodnoty referenčních scénářů se nemění
  bez souhlasu (u pohybů bez poplatku se nic nemění).
- Zámek F může odmítnout dnes možné postupy; v `investra_test` i `investra_dev` před nasazením ověřit SELECTem,
  že žádný doklad ani pohyb už nepadá do období schváleného ocenění.

## Testy (nad `investra_test`, po záloze)

- Úpis a odkup bez poplatku: doklad shodný s dneškem (regrese).
- Poplatek: řádky dokladu, čistá částka v kapitálu a kusech třídy; ruční úprava poplatku; odchylka v kontrolách.
- Rozdíl ze zaokrouhlení v obou variantách; nesoulad částek nebo kusů → chyba.
- Cena odlišná od zveřejněného kurzu bez důvodu → chyba.
- Historie v chatteru; storno a nový pohyb; storno do schváleného ocenění odmítnuto, po vrácení projde.
- Zámek F: obchod, splátka, ruční doklad a úpis s datem ≤ schválenému ocenění odmítnuty; po datu projdou.
- Duplicitní `external_ref` odmítnut. Celá sada testů modulů Investry.

## Odpovědi uživatele (11. 11. 2026)

1. Zaokrouhlení kusů: ano, parametr.
2. Poplatek: parametr (fond, třída), platí se ven; při ručním zadání ho uživatel může upravit.
3. Storno jen do neschváleného ocenění; schválené ocenění nejde měnit ani do něj účtovat – má platit vždy.
4. Tlačítko Zaúčtovat patří do bodu 8.
5. Vše posílá a určuje IS.
Souhlas s doporučením: B–E (nyní B–F) najednou, A jako první samostatný krok.

## Odpovědi uživatele – druhé kolo (11. 11. 2026)

- Zámek ve dvou vrstvách: měkký (vratný vrácením ocenění) a tvrdý po zveřejnění; i na zrušení posledního
  zámku musí být pojistka → návrh G.
- Měkký zámek od stavu Ke schválení, jako samostatný krok před B–E.
- Příjemce poplatku: evidovat oba (obhospodařovatel, distributor).
- Výchozí hodnoty: 6 míst kusů, dolů, rozdíl ve fondu.

## Ověřit u uživatele

- G: souhlas 11. 11. 2026 – zveřejnění nastaví vratný zámek pro všechny s výjimkou jako pojistkou; nevratný tvrdý zámek až po auditu
  účetní závěrky.

## Provedení (11. 11. 2026)

Upřesnění od uživatele: nové účty a role; odkup: kusy × cena = výplata + poplatek + rozdíl; sazba z hrubé částky;
zbytek do 0,01 na výnos/náklad ze zaokrouhlení (výsledek fondu), větší = chyba. Čísla účtů pracovní (osnova podle 501 otevřená).

| Případ | Řádky dokladu (MD +, D −) |
|---|---|
| Úpis | banka +platba; kapitál třídy −(kusy × cena + rozdíl, zůstává-li ve fondu); závazek z poplatků −poplatek; závazek vůči investorům −rozdíl (vrací-li se); zbytek: výnos −/náklad + |
| Odkup | kapitál třídy +(kusy × cena − rozdíl, zůstává-li ve fondu); banka −výplata; závazek z poplatků −poplatek; závazek vůči investorům −rozdíl (vrací-li se); zbytek: náklad +/výnos − |
| Bez poplatku a rozdílu | banka / kapitál třídy jako dřív (regrese ověřena testem) |

Kód: `investra_nav/models/movement.py`, kontroly ocenění `_run_movement_checks`, testy `investra_nav/tests/test_movement.py`.
Deník: „Úpisy a odkupy – účty a vzorce“ a „Úpisy a odkupy – provedení (body A–E)“, včetně odchylek od plánu.
