# ZJ-25 Ocenění: rozpad tříd, kontroly, balíček, texty, Portfolio

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (NAV, ocenění) – jen podle plánu schváleného Martinem |
| Výchozí větev | ukol/ZJ-24-bod-15 |
| Větev úkolu | `ukol/ZJ-25-oceneni-kontroly-rozpad` |
| Zadal, dne | Martin, 2026-11-20 (návrh poradce, schváleno na plátně návrhů) |
| Vlastník | Claude |
| Navazuje na | dávka ZJ-24 bod 15 · ZJ-25 · ZJ-27 · ZJ-26, postup `docs/ukoly/podklady/davka-ZJ-24-27/00-prehled.md` |

**Cíl, rozsah, mimo rozsah a kritéria přijetí:** zadání oddíl 1 v `docs/ukoly/podklady/davka-ZJ-24-27/zadani-ZJ-25-26-oceneni-a-vzhled.md`.

**Technický plán:** `docs/ukoly/podklady/davka-ZJ-24-27/plan-ZJ-25-technicky.md`, katalog kontrol `docs/ukoly/podklady/davka-ZJ-24-27/podklad-katalog-kontrol.md`.

## Výsledek (2026-11-21, větev `ukol/ZJ-25-oceneni-kontroly-rozpad`, commity „ZJ-25 K1“ až „K6“)

- **K1 rozpad tříd:** `models/valuation_split.py` – `_class_split` (jen v paměti, pohledy Rozvaha a Podle výsledovky), dočasné modely
  `investra.valuation.class.account` a `.transfer`, kontrola `class_split` v `_finish`; položky deníku (`view_move_line_class_split_list`).
- **K2 kontroly:** `models/check_catalog.py` (45 kódů z podkladu + `fee_not_in_force` z bodu 15 = 46), `models/valuation_check.py`
  (oblast, Co/Jak, Očekáváno/Skutečnost/Rozdíl, položky `investra.valuation.check.item`, řazení stop → upozornění → ok, počty); `_check` rozšířená zpětně
  kompatibilně. Strukturovaný výsledek a položky jsou vyplněné u přímých kontrol (classes_sum, clearing_zero, positions_ledger, trades_*, bridge_*, class_split,
  movements_*, classification_*, transit_zero, accounts_role, no_foreign_drafts, bond_calendar); kontroly „[refaktor]“ (pomocné funkce vracející text) mají jen oblast a Co/Jak z katalogu.
- **K3 obrazovky:** záložky přemostění (Účty, Úpisy a odkupy, Úplaty třídy), záložka Kontroly (pás čísel, seskupení podle oblasti, formulář kontroly), odkaz v souhrnu, dashboard.
- **K4 balíček:** Předvaha po třídách, list Rozpad tříd. **K5 texty** (souhrn, rozpad daně, převzaté opravy, ruční úplaty; nápověda a manuál kap. 9). **K6 Portfolio:** Změna ceny, z toho kurz.
- **Verze** `investra_nav` 20.0.0.46.0. Testy `test_zj25_split/checks/package/portfolio.py`; `all` 1244 testů bez chyby.
- **Snímek 35/39:** hodnoty beze změny; jediný rozdíl je nový řádek kontroly `35 | class_split | ok` (snímek vypisuje kódy kontrol, plán to předpokládal). Nový výchozí stav: `docs/predavky/snimek-35-39-pred-ZJ-27.txt`.
- **Odchylky od plánu:** (1) rozpad zaokrouhlení se dorovnává v každém pohledu zvlášť (součty obou pohledů tak sedí i na haléře); (2) „Použité výjimky“ v rozpadu daně se
  filtrují podle pohybu na účtu od začátku účetního období (detail řádku daně pohyb neukládá); (3) kontrola `class_split` navíc ověřuje společnou změnu = NFK − předběžný kapitál tříd s podílem;
  (4) strukturované výsledky nejsou u kontrol „[refaktor]“ (viz výše). Migrace nebyla potřeba (stored `area` a `status_order` se dopočítají při povýšení).
- **Neověřeno v prohlížeči:** záložky přemostění, seznamy rozpadu a položek deníku, záložka Kontroly (default_group_by), odkaz v souhrnu, texty, sloupce Portfolia.

## Převzetí

Do `main` jen na Martinovu výzvu („slučuj“).
