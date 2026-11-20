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

**Soupis míst a změn:**

| Soubor / pohled | Změna |
|---|---|
| `addons/custom/investra_instruments/views/instrument_views.xml`: `view_instrument_list`, `view_instrument_search` | ISIN je před názvem; vyhledávací pole ISIN je první a přidáno seskupení podle existujícího pole ISIN. |
| `addons/custom/investra_instruments/views/instrument_views.xml`: `view_price_list`, `view_price_search` | Existující `instrument_isin` je v seznamu před názvem a přidáno do hledání. Seskupení zůstává podle nástroje: související pole ISIN není uložené, proto je nelze použít pro SQL seskupení. |
| `addons/custom/investra_nav/views/nav_views.xml`: portfolio v `view_valuation_form` | Existující `isin` je před názvem. |
| `addons/custom/investra_instruments/views/instrument_views.xml`: `view_trade_list`, `view_trade_search`, `view_trade_form` | Seznam a výběr používají `instrument_id`; samostatné pole ISIN chybí. Skupina zůstává podle nástroje a její popisek závisí na Claudově změně názvu. |
| `addons/custom/investra_instruments/views/instrument_views.xml`: `view_classification_list`, `view_classification_form`, `view_classification_search`, `view_portfolio_form`, `view_instrument_form` | Zařazení a vložené seznamy používají `instrument_id`; přidáno seskupení podle nástroje, přímé pole ISIN chybí. |
| `addons/custom/investra_nav/views/dividend_views.xml`: `view_dividend_list`, `view_dividend_search`, `view_dividend_form`, kontext tlačítka v `view_instrument_form_dividend` | Zobrazují nebo vybírají `instrument_id`; přidáno seskupení podle nástroje, přímé pole ISIN chybí. |
| `addons/custom/investra_nav/views/nav_views.xml`: `view_repayment_list`, `view_repayment_search`, `view_repayment_form`, `view_instrument_rate_wizard_form` | Přehledy/výběr používají `instrument_id`; přímé pole ISIN chybí. |
| `addons/custom/investra_derivative/views/derivative_views.xml`: `view_derivative_list`, `view_derivative_search`, `view_derivative_form` | Nástroj je nyní viditelný v seznamu, přidáno vyhledávací pole a seskupení podle nástroje; přímé pole ISIN chybí. |
| `addons/custom/investra_dashboard/views/dashboard_views.xml`: `view_cashflow_dashboard_list` | Toky zobrazují `instrument_id`; přímé pole ISIN chybí. |
| `addons/custom/investra_instrument_master/views/instrument_views.xml`: formulář podkladového nástroje a průvodce změnou | Výběr používá `underlying_instrument_id` / `instrument_id`; hledání podle ISIN závisí na Claudově části. |

- **Změněné soubory:** `addons/custom/investra_instruments/views/instrument_views.xml`, `addons/custom/investra_nav/views/nav_views.xml`, `addons/custom/investra_nav/views/dividend_views.xml`, `addons/custom/investra_derivative/views/derivative_views.xml`.
- **Ověřeno:** zdrojové XML a existence polí `isin` na nástroji a ocenění a `instrument_isin` na ceně.
- **Neověřeno:** výběr nástroje zadáním ISIN v UI, skutečné hledání/seskupení po změně Pythonu a upgrade modulů.
- **Otevřené otázky a návrhy mimo rozsah:** vyhledávací pole a samostatný sloupec ISIN nelze přidat do uvedených přehledů bez nových polí.
- **Zbývá Claudovi:** zobrazený název ve tvaru „ISIN – název“ a `_search_display_name` / `name_search` v `investra_instruments` a `investra_instrument_master`; poté ověřit výběr a seskupení podle ISIN.

## Převzetí

Převzato 2026-11-20 (`14c751e`). Python část doplnil Claude: `investra.instrument` má `_rec_names_search` (ISIN, název, kód, identifikátor) a `display_name` „ISIN název“; test `test_instrument_isin.py`. Opraveny dekorátory `_compute_book_warning`. Ověření výběru podle ISIN v prohlížeči čeká.
