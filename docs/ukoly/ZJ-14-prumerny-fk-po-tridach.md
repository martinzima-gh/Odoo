# ZJ-14 Úplata z průměrného FK po třídách

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (výpočet úplat, dopočet, opravy); plán schvaluje Martin |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (nebo aktuální pracovní větev) |
| Zadal, dne | Martin, 19. 11. 2026 |
| Řešitel | Claude |
| Navazuje na | ZJ-12 (B.6 průměrný FK, B.7 opravy základu), rozhodnutí 2026-11-19 „Průměrný FK po třídách – zásady“ |
| Stav | **zadané, čeká na technický plán** |

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

## Výsledek

## Převzetí
