# Návrh: přemostění kapitálu tříd v ocenění

Plán ke schválení. Model je červená zóna (`investra_nav/models`), obrazovka zelená. Stav 10. 11. 2026,
připravil Claude na pokyn uživatele (poznámka 6 z podkladu UX a požadavek z 10. 11. 2026). Nic není naprogramované.

**Cíl:** Záložka Třídy ve formuláři ocenění ukáže pro každou třídu cestu od počátečního stavu k závěrečnému kurzu:
kapitál, kusy a kurz z minulého ocenění → úpisy, odkupy, dividendy → upravený kapitál → podíl na společném výsledku,
úplaty, výkonnostní odměna, ostatní položky třídy → konečný kapitál, kusy, kurz a změna kurzu. Pod tabulkou kontroly.
Struktura vychází z návrhu vedoucího (revize, krok 2, záložka Třídy) a z obecných poznatků z ukázkových sešitů
(bez jejich dat).

## Cílová tabulka (řádek = třída, poslední řádek součet)

| Skupina | Sloupec | Zdroj | Dnes v modelu |
|---|---|---|---|
| Třída | Třída, měna zveřejnění | `class_id` | ano |
| Počáteční stav | FK (t−1) | `capital` předchozího ocenění | ne (jen uvnitř výpočtu) |
| | Kusy (t−1) | `units` předchozího ocenění | ne |
| | Kurz (t−1) | `price` předchozího ocenění | ne |
| Pohyby | + Úpisy, + kusy | pohyby třídy v období | ne (jen součet v předběžném kapitálu) |
| | − Odkupy, − kusy | pohyby třídy v období | ne |
| | − Dividendy | výplata z třídy | ne; pohyb typu dividenda zatím neexistuje, sloupec bude 0 do jeho zavedení |
| | = Upravený FK | `pre_capital` | ano |
| Rozdělení | Alokační poměr | `ratio` | ano |
| | Podíl na společném výsledku | poměr × NFK − upravený FK | ne (dopočet) |
| | − Úplaty třídy | řádky úplat třídy bez výkonnostní odměny | ne (řádky úplat existují) |
| | − Výkonnostní odměna | řádky úplat druhu výkonnostní | ne (řádky existují) |
| | ± Ostatní položky třídy | specifická změna − úplaty − výkonnostní odměna (např. měnové zajištění třídy) | ne (dopočet z `delta`) |
| | ± Zaokrouhlení | rozdíl po zaokrouhlení přiřazený třídě | ne |
| Konečný stav | = FK | `capital` | ano |
| | Kusy | `units` | ano |
| | Kurz za kus (měna zveřejnění) | `price` | ano |
| | Kurz přepočtu měny | kurz funkční měny k měně zveřejnění | ne |
| | Δ kurzu % | kurz / kurz (t−1) − 1 | ne |

**Kontroly pod tabulkou** (jako řádky záložky Kontroly):
- FK (t−1) + úpisy − odkupy − dividendy = upravený FK,
- kusy (t−1) + kusy úpisů − kusy odkupů = kusy,
- upravený FK + společný výsledek + úplaty + výkonnostní odměna + ostatní + zaokrouhlení = FK, po třídách,
- Σ FK tříd = FK fondu, Σ FK (t−1) = FK předchozího ocenění.

## Varianty

| Varianta | Co | Pro | Proti |
|---|---|---|---|
| **A. Uložené hodnoty** (doporučeno) | nová pole na `investra.valuation.class` plní výpočet v `_class_context` a `_finish` | čísla zůstanou přesně taková, jak se počítala; jdou do balíčku pro depozitáře a do snímku | změna modelu v červené zóně, testy |
| B. Počítaná neuložená pole | dopočet při zobrazení z řádků úplat, pohybů a předchozího ocenění | méně zásahů do výpočtu | po pozdější opravě pohybu nebo předchozího ocenění by tabulka ukázala jiná čísla, než se počítala; nejde filtrovat ani exportovat spolehlivě |

## Návrh řešení (varianta A)

1. **Model** (`investra_nav/models/valuation.py`, třída `InvestraValuationClass`): nová pole
   `opening_capital`, `opening_units`, `opening_price`, `subscription_amount`, `subscription_units`,
   `redemption_amount`, `redemption_units`, `dividend_amount`, `shared_result`, `fee_amount`, `performance_amount`,
   `other_amount`, `rounding_amount`, `fx_rate`, `price_change_pct`. Všechna jen ke čtení, plněná výpočtem.
2. **Výpočet:** `_class_context` už má předchozí řádek a pohyby; doplní rozpad. `_finish` doplní společný výsledek,
   úplaty a výkonnostní odměnu z `fee_line_ids` podle třídy, zaokrouhlení (`remainder`), kurz přepočtu a změnu kurzu.
   Výsledek NAV, kusy ani kurz se nemění; jen se ukládá rozpad, který výpočet už zná.
3. **Kontroly:** čtyři kontroly výše v `_run_checks` se závažností Stop (rozdíl nad 0,01).
4. **Snímek a balíček:** rozpad přidat do balíčku pro depozitáře (list Třídy). Otisk snímku (`snapshot_hash`)
   se nemění, aby zůstala porovnatelná starší ocenění.
5. **Obrazovka** (zelená, samostatné zadání AG po sloučení modelu): záložka Třídy jako seznam se sloupci podle
   tabulky, součty (`sum`) u částek, méně používané sloupce volitelné (`optional`). Formulář řádku s rozpadem
   ve skupinách Počáteční stav, Pohyby, Rozdělení, Konečný stav.

**Testy:** nové testy nad existujícími scénáři v `investra_nav/tests/`: každá kontrola přemostění projde
na všech scénářích; ručně spočtený rozpad pro jeden scénář se dvěma třídami (úpis, odkup, úplata, výkonnostní odměna,
zaokrouhlení). Očekávané hodnoty existujících scénářů v `tests/scenarios/*.json` se nemění.

## Dopad

- Na účetnictví žádný: nevznikají ani se nemění doklady.
- Existující ocenění nové sloupce nemají vyplněné (0). Doplní se až novým výpočtem návrhu; schválená a zaúčtovaná
  ocenění se nepřepočítávají. Migrace dat není potřeba.

## Otázky pro uživatele

1. Dividendy: má se pohyb třídy „výplata dividendy“ (z IS) zavést hned s tímto krokem, nebo stačí sloupec
   a doplnit později s rozhodnutím o dividendách?
2. Má se v tabulce zobrazovat i kapitál v měně zveřejnění třídy (u tříd v jiné než funkční měně), nebo stačí
   kurz za kus a kurz přepočtu?
3. Rozpad „ostatních položek třídy“ dál (měnové zajištění, dohady, položky specifické pro třídu) podle rolí účtů:
   teď, nebo až podle prvního fondu, který je bude mít?

## Zóna a provedení

Model a výpočet: červená zóna, provede Claude po schválení uživatelem. Obrazovka: zelené zadání AG po sloučení.
