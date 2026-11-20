# AG-024 ISIN v přehledech, filtrech, seskupení a hledání

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (pohledy), oranžová (`investra_instruments`, `investra_instrument_master` – `name_search`, zobrazený název) podle plánu níže |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` |
| Větev úkolu | `ag/AG-024-isin` |
| Zadal, dne | Martin (poznámky) / Claude, 2026-11-20 |
| Navazuje na | `docs/ukoly/ZJ-20-poznamky-zpracovani.md`, bod 3 |

**Cíl:** U cenných papírů je klíčový **ISIN**. V přehledech je vidět hned na začátku, filtruje se, seskupuje a hledá podle ISINu,
ne podle názvu. Při výběru nástroje v jakémkoli formuláři stačí napsat ISIN.

**Rozsah souborů:**
- zelená: seznamy, vyhledávání, filtry a seskupení všech modelů, které mají nástroj: obchody, ceny, dividendy, splátky, deriváty,
  pozice a portfolio v ocenění (sloupec), zařazení portfolia, nástroje samé.
- oranžová, jen podle plánu: zobrazený název nástroje „ISIN – název“ (`_compute_display_name`) a `_search_display_name`/`name_search`
  hledající podle ISIN i názvu, v modulech `investra_instruments` a `investra_instrument_master`.

**Plán (schválil Claude, 2026-11-20):**
1. Nástroj má `display_name` ve tvaru „ISIN název“ (u nástroje bez ISINu jen název).
2. Hledání v poli Nástroj (`name_search`) a ve vyhledávacích pohledech: shoda ISIN (začátek, bez ohledu na velikost písmen) i název.
3. Seznamy: ISIN jako **první** sloupec před názvem; sloupec Název následuje.
4. Přednastavené filtry a seskupení „Nástroj“ seskupují podle ISINu (zobrazený název ISIN).
5. Hromadná kontrola: `grep -rn 'instrument_id' addons/custom/*/views/*.xml` – každé místo, kde se nástroj zobrazuje nebo vybírá.

**Mimo rozsah:** doplnění názvu při zadání nového nástroje podle ISINu (zdroj názvu není určený – otevřená otázka pro Martina,
viz ZJ-20, bod 3); změna povinných polí; migrace.

**Kritéria přijetí:** soupis míst (soubor, pohled, změna) ve Výsledku; v obchodu jde vybrat nástroj napsáním ISINu; seznamy mají ISIN
první; test na hledání podle ISINu (nový test v `investra_instruments/tests/`); žádná změna existujících očekávaných hodnot.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
