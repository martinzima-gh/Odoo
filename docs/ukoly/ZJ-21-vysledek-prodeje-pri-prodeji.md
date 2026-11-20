# ZJ-21 Výsledek z prodeje se účtuje při prodeji

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování obchodu, ocenění, výpočet NAV, očekávané hodnoty scénářů) – jen s plánem schváleným Martinem |
| Výchozí větev | `main` (po sloučení dávky ZJ-07 až ZJ-19) |
| Větev úkolu | `ukol/ZJ-21-vysledek-prodeje` |
| Zadal, dne | Martin, 2026-11-20 (rozhodnutí: výsledek z prodeje se účtuje při prodeji) |
| Navazuje na | ZJ-15 (cena odúčtování), rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“, `docs/ukoly/ZJ-20-poznamky-zpracovani.md` bod 9 |
| Model | Opus 5.5, úsilí high |

**Kontext:** Dnes obchod účtuje nástroj v částce prodeje a realizovaný výsledek vzniká až v ocenění (`_realised_ccy`, `_cost_walk`).
Ve formuláři obchodu se tak pole Odúčtování neprojeví a náhled ukazuje jiné částky, než uživatel čeká.

**Cíl:** Prodej odúčtuje nástroj v účetní hodnotě (pořizovací, nebo ručně upravená **cena odúčtování**) a rozdíl proti tržbě zaúčtuje
hned jako výnos nebo ztrátu z prodeje. Náhled zaúčtování prodeje ukazuje stejné řádky (společná funkce účtování a náhledu).

## Technický plán (návrh k schválení Martinem, nic se neprogramuje do schválení)

1. **Účetní hodnota k datu prodeje.** Naběhlá hodnota a FVOCI: pořizovací cena (průměrka po nástroji a portfoliu, včetně
   kapitalizovaného poplatku) nebo cena odúčtování; naběhlý úrok zůstává zvlášť. FVTPL: poslední zaúčtovaná reálná hodnota
   + přecenění do data prodeje (cena k datu prodeje). Návrh: FVTPL odúčtovat v poslední zaúčtované hodnotě a změnu ceny do dne prodeje
   vykázat jako přecenění v dokladu prodeje; rozhodnutí a příklad ověřit s metodikem.
2. **Doklad prodeje:** D banka (nebo nevypořádané) tržba; K nástroj účetní hodnota; K/D výsledek z prodeje (role realizace).
   Cena odúčtování mění jen rozdělení výsledku, nikoli celkový výsledek (ZJ-15 B2).
3. **Ocenění:** `_realised_ccy` a `_cost_walk` nesmí realizaci účtovat podruhé; počítají jen rozdělení pro sloupce listu portfolia
   a výkazy. Kontrola: součet realizace + přecenění + kurz stejný jako před změnou.
4. **Stará data:** existující prodeje jsou zaúčtované v částce prodeje. Návrh: nová logika platí od data nasazení (pole nebo datum
   v nastavení), starší prodeje dál přes ocenění. Rozhodnout před kódem.
5. **Třídy, kurz, poplatky:** realizace nese třídu portfolia (ZJ-09); cizí měna: kurzová složka podle účetní hodnoty; poplatek prodeje
   zůstává náklad (ZJ-16).
6. **Testy:** přepis referenčních scénářů s prodejem (očekávané hodnoty ověřit ručně a odůvodnit), snímek ocenění 35 a 39,
   storno prodeje, částečný prodej, prodej s cenou odúčtování, odložené vypořádání, FVOCI akcie bez recyklace.
7. **Migrace:** jen když se rozhodne o dopočtu starých prodejů; jinak žádná.

**Kritéria přijetí:** náhled a doklad shodné; ocenění nepočítá výsledek dvakrát; číselný příklad (nákup 10 × 100, prodej 4 × 130) ve
všech třech zařazeních; snímek 35/39 beze změny nebo s odůvodněným rozdílem v předávce.

## Výsledek

Doplní Claude po schválení plánu.

## Převzetí

Doplní Claude.
