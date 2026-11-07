# IS v Odoo: jak náročné by to bylo

Stav 2026-11-07. Analýza k zvážení, ne rozhodnutí. Platí rozhodnutí z 2026-11-04, že IS je samostatná aplikace. Dokumentaci IS nemáme, proto srovnání s ní chybí. Člověkodny jsou můj hrubý odhad.

**Závěr:** technicky to jde, je to ale přibližně stejně velký projekt jako celá fondová část. Odhad je 170 až 290 člověkodnů, tedy 8 až 14 člověkoměsíců, bez klientského portálu. Do převzetí prvního fondu ke konci Q1 2027 se to nevejde. Doporučuji pro start počítat s externím IS a rozhodnout až po získání jeho dokumentace. Pokud se IS bude stavět v Odoo, tak jako **samostatnou instanci a databázi**, ne jako modul v účetní databázi.

## Co IS dělá

Podle architektury: držitelé, AML a osobní údaje, pokyny k nákupu a prodeji, kusy na držitele, závěrka klientských transakcí, volba kurzu pro pokyn, platební příkazy, dividendy držitelům včetně srážkové daně a reinvestice, agregovaná data pro ČNB.

## Co se dá v Odoo převzít

| Potřeba | Odoo | Hodnocení |
|---|---|---|
| Investor | `res.partner` | Základ ano, KYC, AML a daňové údaje jsou vlastní |
| Dokumenty a e-maily | Přílohy, šablony, `mail` | Ano |
| Bankovní platby | Výpisy a párování jsou v Enterprise, v Community ne | Závisí na edici |
| Klientský portál | Portál Odoo | Základ ano, investiční pokyny jsou vlastní vývoj |
| Práva a více společností | Skupiny a pravidla záznamů | Ano, ale je potřeba silnější oddělení osobních údajů |
| Registr kusů | Nic | Vlastní, jádro systému |
| Neměnnost a audit | Naše události a hashe jdou rozšířit | Vlastní |
| AML kontroly a sankční seznamy | Nic | Externí služba a vlastní postup |

## Odhad

| Oblast | Člověkodny |
|---|---|
| Evidence investorů, KYC, oprávněné osoby | 15 až 25 |
| AML: rizikový profil, sankční seznamy, přezkumy, hlášení | 15 až 30 |
| Pokyny, úpisy, identifikátory, kurz pokynu | 15 až 25 |
| Příchozí platby a párování | 10 až 15 |
| Registr kusů po držitelích a třídách, převody | 15 až 25 |
| Závěrka klientských transakcí | 8 až 12 |
| Odkupy, platební příkazy | 10 až 15 |
| Dividendy, srážková daň, reinvestice | 10 až 15 |
| Vstupní a výstupní poplatky | 5 až 10 |
| Potvrzení a výpisy investorům | 10 až 15 |
| FATCA a CRS | 10 až 20 |
| Agregace pro ČNB | 5 až 10 |
| Převod dat držitelů u převzatých fondů | 15 až 30 |
| Bezpečnost, role, audit, testy, DORA | 20 až 30 |
| Manuál a zaškolení | 10 |
| **Celkem** | **173 až 287** |
| Volitelně klientský portál a distributoři | +30 až 60 |

Úspora za integraci s externím IS (9 zpráv): asi 20 až 40 člověkodnů. AI zrychlí psaní kódu, méně už analýzu, ověření, testy a schvalování, které tu převažují. Odhad nezahrnuje provoz ani licence.

## Varianty

| Hledisko | Externí IS | Modul ve stejné databázi | Samostatná instance Odoo |
|---|---|---|---|
| Rychlost pro první fond | Nejlepší, pokud IS je připravené | Nereálná | Nereálná |
| Integrace | 9 zpráv | Žádná | Stejná jako externí, ale pod naší kontrolou |
| Osobní údaje a AML | Oddělené | V účetní databázi, široký dopad incidentu | Oddělené |
| Riziko výpadku | Oddělené | Společné | Oddělené |
| Vlastní kontrola a změny | Závisí na dodavateli | Plná | Plná |
| Odpovědnost za shodu | Část na dodavateli | Celá naše | Celá naše |
| Závislost na dodavateli | Ano | Ne | Ne |
| DORA | Další poskytovatel IKT | Vlastní vývoj kritické funkce | Vlastní vývoj kritické funkce |

## Co je nejtěžší

Není to programování, ale odpovědnost:

- **Evidence držitelů** je právně závazný záznam; chyba znamená chybné kusy a nároky.
- **AML** vyžaduje postup, odpovědnou osobu a kontrolu seznamů, ne jen obrazovky.
- **Uchovávání a výmaz** osobních údajů musí současně plnit lhůty AML a GDPR.
- **Daně:** srážková daň a smlouvy o zamezení dvojímu zdanění po investorech.
- **Převzaté fondy** přinášejí historii držitelů v různé kvalitě.

Přesné povinnosti jsem neověřoval, posoudit s právníkem a compliance: ZISIF, zákon 253/2008 Sb., vyhláška 58/2006 Sb., GDPR, FATCA a CRS, případně ZPKT podle způsobu distribuce.

## Doporučení

1. Pro start počítat s externím IS, harmonogram nemá rezervu.
2. Zachovat oddělení přes 9 zpráv. Když je definujeme jako vlastní rozhraní, IS půjde později vyměnit bez zásahu do účetnictví.
3. Získat dokumentaci IS, cenu a plán úprav; pak porovnat cenu za 3 až 5 let.
4. Pokud IS nesplní zadání, začít samostatnou instancí a nejmenším rozsahem: držitelé, pokyny, kusy, závěrka.
