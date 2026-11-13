# Předávka 2026-11-13: upozornění na nezaškrtnutou knihu ve formuláři

**Cíl:** uživatel nemá přijít o vyplněný nástroj nebo cenu. Po chybě „zaškrtněte knihu“ přepnutí firem znovu načte
stránku a neuložený formulář zahodí (jádro Odoo). Proto formulář upozorní předem.

**Stav:** větev `feature/nav-prototyp`, `investra_instruments` 0.14.1 (jen vypočítané pole a pohled, bez migrace).

**Hotovo:**
- `book_problem()` v `investra_instruments/models/instrument.py`: jeden text pro chybu při uložení i pro pruh ve formuláři.
- Pole `book_warning` (bez uložení) u nástroje a ceny, žlutý pruh nahoře ve formuláři; přepočítá se po změně fondu.
- Test `test_form_warns_about_book_before_filling`; čistá DB (`l10n_cz` + `investra_instruments`): 79 testů, 0 chyb.
  Pomocné DB `investra_ci_kniha`, `investra_ci_kniha2` smazány.
- Deník rozhodnutí: „Upozornění na nezaškrtnutou knihu ve formuláři“.

**Zbývá – první krok:**
1. Upgrade `investra_test` na `investra_instruments` 0.14.1 (po souhlasu, se zálohou). Pozor: `-u` povýší i `investra_nav`
   a načte jeho pracovní kopii, kde měla relace `odoo-dev-29` necommitnutou historii cen (`valuation_price_history`).
   Upgradovat až po jejím commitu. Pak restart webu 8071 a ověření pruhu v UI.
2. Claude Doc (konektor Claude Docs v relaci chyběl): doplnit řádky deníku „Firma nové účetní knihy“, „Příjemce vstupního
   a výstupního poplatku“, „Upozornění na nezaškrtnutou knihu ve formuláři“ a otevřený bod „Účty poplatků za úpis
   a odkup ve prospěch fondu“; pak přepsat `docs/architektura.md` exportem.

**Otevřené otázky:** stejný problém může mít obchod (kniha fondu nezaškrtnutá); zatím neřešeno, počkat na zkušenost uživatele.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední tři řádky)
