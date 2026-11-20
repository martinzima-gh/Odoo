# ZJ-14 Úplata z průměrného FK po třídách

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (výpočet úplat, dopočet, opravy); plán schvaluje Martin |
| Výchozí větev | `ukol/ZJ-13-14` |
| Zadal, dne | Martin, 19. 11. 2026 |
| Řešitel | Claude |
| Navazuje na | ZJ-12 (B.6 průměrný FK, B.7 opravy základu), rozhodnutí 2026-11-19 „Průměrný FK po třídách – zásady“ |
| Stav | **hotovo 19. 11. 2026** (větev `ukol/ZJ-13-14`; `investra` povýšena, čeká na kontrolu Martina v prohlížeči) |

**Cíl:** pravidlo s Základem **Průměrný FK** a vyplněným polem Platí třídy počítá úplatu za každou třídu z průměru jejího kapitálu
(dnes je průměrný FK vždy úplata celého fondu a třídy se nepoužijí; pravidlo to ukazuje upozorněním).

**Rozhodnuté zásady (Martin, 2026-11-19):**
1. Průměr třídy jen přes ocenění, kdy třída existuje (ne nuly před prvním úpisem).
2. Třída přidaná do pravidla v průběhu roku se počítá **až od data**, kdy v pravidle je (ne zpětně od 1. 1.).
3. Průměr v **měně fondu** (kapitál třídy v měně fondu, jako u Kapitálu třídy).

**Co plán musí vyřešit:** dřívější body = FK třídy ze zaúčtovaných ocenění (`investra.valuation.class.capital`), dnešní bod = hodnota třídy
po zvoleném kroku (dopočet, rozsah třídy); doúčtování nárok od začátku (1. 1. / vznik třídy / zařazení do pravidla) minus zaúčtované u třídy;
označení nových řádků po třídách v detailu (odlišit od starých chybných řádků B.6 se stejnou částkou za každou třídu); opravy základu
a převzaté opravy po třídách; náhled Schématu výpočtu; příjemci; referenční příklad spočtený ručně; testy.

## Technický plán (schválil Martin 19. 11. 2026 zadáním)

**Rozsah.** Pravidlo s `base_source = average_fk` a vyplněným `class_ids` počítá úplatu za každou třídu zvlášť. Bez `class_ids` beze změny
(úplata celého fondu, oprava B.6). Upozornění „u průměrného FK se třídy nepoužijí“ se ruší, nápověda se přepisuje.

**Výpočet pro třídu c** (vše v měně fondu):
1. **Začátek nároku** S_c = nejpozdější z: (a) 31. 12. minulého roku (a datum vzniku fondu, jako dnes), (b) datum prvního nestornovaného
   úpisu třídy (`investra.class.movement`, `movement_type = subscription`, `state != reversed`) = vznik třídy, (c) datum zařazení do pravidla.
2. **Zařazení do pravidla** (bez nového pole): první zaúčtované ocenění v roce, které má řádek rozpisu (pravidlo, c) s `per_class` v detailu;
   S_c = začátek období toho ocenění (= datum předchozího ocenění). Bez takového řádku je zařazením toto ocenění. Přesnost je na ocenění.
3. **Body průměru:** kapitál třídy (`investra.valuation.class.capital`) zaúčtovaných ocenění fondu v roce (posted, sent, confirmed, published)
   s datem > S_c, jen těch s řádkem (pravidlo, c, `per_class`); plus dnešní bod = hodnota třídy po kroku `base_step` (položka dopočtu
   s plátcem c, vliv vlastní úplaty 1/n). Průměr prostý. Třída bez úpisu k datu ocenění položku nemá.
4. **Nárok** = `engine.periodic_fee(pravidlo, S_c, datum ocenění, průměr, classes_count jako dnes)`: pevné části, minimum, maximum a příplatky
   za každou třídu zvlášť (jako u Kapitálu třídy). Čistá funkce `engine.average_fee`.
5. **Pohyb** = nárok − booked_c; booked_c = součet řádků (pravidlo, c, `per_class`) dřívějších zaúčtovaných ocenění v roce. Ruční opravy
   částky (řádky bez pravidla) se nepočítají, platí trvale (ZJ-11).
6. **Detail řádku:** `{"per_class": true, "start": S_c, "points": [[datum, kapitál], …], "today": …, "average": …, "entitlement": …,
   "booked": …}` (+ dosavadní `amount`, `exact`, `segments`, `move`, `base_step`, příjemci). XLS a rozpis berou Základ = `average`.
7. **Pojistky:** pravidlo s letošními řádky BEZ `per_class` (počítané za fond) výpočet zastaví: „Pravidlo X bylo letos počítáno za celý fond;
   přepnout na třídy jde od 1. 1. nebo novým pravidlem.“ (SELECT v `investra` 19. 11. 2026: žádné pravidlo průměrného FK není.) Navíc
   obráceně (doplněno Claudem, výsledky ostatních pravidel nemění): pravidlo bez tříd s letošními řádky `per_class` se zastaví („…počítáno
   po třídách; přepnout na celý fond jde od 1. 1. nebo novým pravidlem“), jinak by booked fondu vzal jen jeden řádek.
   Přerušené zařazení: body z období mimo pravidlo se nepočítají (bod 3), S_c zůstává z prvního zařazení; upozornění
   `average_class_gap` „Třída X byla v pravidle Y letos přerušeně“.

**Navazující části.**
- `_earlier_fee_items`: řádky `per_class` se neslučují (slučování jen starých řádků B.6 bez `per_class`).
- Opravy (B.7): `_correction_key` u průměrného FK s třídami vrací třídu; oprava základu s třídou c se přičte k průměru třídy c, převzatá
  do konce roku (`_carried_corrections(pravidlo, c, 31. 12., base)`); oprava částky s třídou c je pevná částka položky (pravidlo, c).
- Příjemci: plátce je třída c, podíl příjemcům jako u ostatních úplat (váhy po kroku 1, revize CP-2026-11-19).
- Daňový efekt: úplata třídy c je specifická položka třídy c (plyne z plátce, doklad s třídou).
- Přemostění: řádky s třídou jdou do „Úplaty třídy“ (beze změny kódu).
- Schéma výpočtu (náhled): průměrný FK po třídách = položka za každou třídu, průměr = dnešní bod; poznámka „bez historie ocenění“.

**Testy** (`test_fee_average_class.py`): referenční příklad A, B, C (viz níže), pravidlo bez tříd beze změny (stávající testy), pojistka,
přerušené zařazení, oprava základu třídy do konce roku, oprava částky třídy, příjemce s podílem, krok 2 (dnešní bod po úplatách, dopočet).
Referenční příklad i v `tools/nav_reference` (čistý výpočet z bodů) a v `tools/nav_reference/test_engine.py` (`engine.average_fee`).

**Referenční příklad** (spočetl Martin ručně): sazba 3,65 % p. a., ACT/365, bez pevných částek; fond od 31. 12. 2026, ocenění 31. 1., 28. 2., 31. 3. 2027.
A (v pravidle od začátku): 31. 1. 3 100,00; 28. 2. nárok 5 929,50, pohyb 2 829,50; 31. 3. nárok 9 090,00, pohyb 3 160,50.
B (první úpis 15. 2. 2027, 500 000): 28. 2. 650,00; 31. 3. nárok 2 211,00, pohyb 1 561,00. C (do pravidla po ocenění 28. 2.): 31. 3. 930,00.

## Výsledek

**Kód** (`investra_nav`): `engine.average_fee` (čistá funkce: průměr bodů + dnešní bod + oprava základu, nárok, pohyb);
`valuation._average_class_item` a `_first_subscription` (začátek nároku, zařazení, body, booked, přerušení); `_apply_fees` položka za každou
třídu (plátce třída, příjemci), kontrola `average_class_gap` (jen u fondu s pravidlem průměrného FK po třídách); `_correction_key` a
`_apply_base_correction` s třídou; `_earlier_fee_items` neslučuje řádky `per_class`; pojistka v obou směrech (fond ↔ třídy v roce);
`fee_rule`: upozornění zrušeno, nápověda Základ a Platí třídy; `fee_scheme`: náhled po třídách s poznámkou „bez historie ocenění“.
Manuál `docs/manual/09-uplaty-a-opravy.md`. Data: v `investra` není žádné pravidlo průměrného FK (SELECT 19. 11. 2026), výsledky ocenění
(35, 39) se tedy nemění; povýšení ani restart nebyly potřeba (změny Pythonu se v `investra-web` projeví až po dohodnutém restartu).

**Referenční příklad proti ručním číslům** (`test_fee_average_class.py::test_reference_example`, v Odoo; `tools/nav_reference/test_engine.py::AverageByClass`, čistá funkce):

| Třída | Ocenění | Body | Průměr | Dní | Nárok | Pohyb | Ručně |
|---|---|---|---|---|---|---|---|
| A | 31. 1. | dnes 1 000 000 | 1 000 000 | 31 | 3 100,00 | 3 100,00 | 3 100,00 ✓ |
| A | 28. 2. | 1 000 000; dnes 1 010 000 | 1 005 000 | 59 | 5 929,50 | 2 829,50 | 5 929,50 / 2 829,50 ✓ |
| A | 31. 3. | 1 000 000; 1 010 000; dnes 1 020 000 | 1 010 000 | 90 | 9 090,00 | 3 160,50 | 9 090,00 / 3 160,50 ✓ |
| B | 28. 2. | dnes 500 000 | 500 000 | 13 | 650,00 | 650,00 | 650,00 ✓ |
| B | 31. 3. | 500 000; dnes 505 000 | 502 500 | 44 | 2 211,00 | 1 561,00 | 2 211,00 / 1 561,00 ✓ |
| C | 31. 3. | dnes 300 000 (začátek 28. 2.) | 300 000 | 31 | 930,00 | 930,00 | 930,00 ✓ |

**Odchylky a upřesnění** (schválil Martin 19. 11. 2026, deník „Průměrný FK po třídách – začátek nároku a odchylky ZJ-14“): (1) Test v Odoo běží s krokem 2: u kroku 1 je dnešní bod hodnota před úplatou a uložený kapitál po ní, takže by
lednový bod nemohl být zároveň 1 000 000 dnes i 1 000 000 v únoru; s krokem 2 je dnešní bod = uložený kapitál a ruční čísla platí přesně
(hodnoty tříd nastavené specifickými výsledky). Krok 1 má samostatný test (dnešní bod 1 006 900 před úplatou, bod ledna 996 900 po ní,
nárok 5 911,21). Čistá funkce počítá ruční příklad přímo z bodů. (2) Fond v testu vzniká 30. 12. 2026 a úpisy A a C jsou 31. 12. 2026:
úpis ke dni vzniku fondu by do prvního období nespadl (`date > začátek období`); začátek nároku je i tak 31. 12. 2026. (3) Třída s prvním
úpisem 1. 1. má v lednu 30 dní (začátek nároku = den úpisu, jako B: 15. 2. → 13 dní); charakterizační testy B.6 (pravidlo se dvěma
třídami, úpis 1. 1.) proto nově dávají 1 500 za třídu místo 3 100 za fond. (4) Pojistka i opačným směrem (třídy → fond), jinak by booked
fondu vzal jen jeden řádek. (5) Kapitál třídy je pole `capital` modelu `investra.valuation.class` (v zadání `…class.capital`).

**Testy:** `test_fee_average_class.py` 10 (referenční příklad, krok 1, obě pojistky, přerušení s upozorněním, oprava základu třídy převzatá
do konce roku, oprava částky třídy trvale, příjemce s podílem, pravidlo bez tříd beze změny, náhled); upravené `test_fee_characterization.py`
(2) a `test_fee_ui.py` (upozornění zrušeno). `investra_nav` 521/521, `investra_nav+` 595/595, `all` 1025/1025; `tools/nav_reference` 60/60.

### Povýšení `investra` (2026-11-19, Martin schválil)

Záloha `zalohy/investra-2026-11-19-pred-ZJ13-14.dump` (`pg_restore -l` čitelné, 10 488 položek). `-u investra_rates,investra_nav` s kódem
`5a9b1e5` bez ERROR (log `.test-logs/upgrade-investra-ZJ13-14.log`), restart `investra-web`, HTTP 200. Filtr Aktivní měny je v pohledu
a výchozí v akci Kurzy měn. Snímek `docs/sql/28-snimek-oceneni.sql` (ocenění, třídy, úplaty, doklady podle stavu, kontroly) před a po povýšení
shodný. Po přepočtu ocenění 35 (`action_compute` jako admin) beze změny FK, tříd, úplat, kontrol i zaúčtovaných a navržených dokladů;
změnilo se jen `write_date` a předchozí návrhy dokladů přešly do „zahozeno“ (12 → 16). Ocenění 39 je ve stavu vráceno, nepřepočítává se;
snímek beze změny.

## Převzetí
