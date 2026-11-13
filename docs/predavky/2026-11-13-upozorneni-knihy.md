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

- `investra_test`: záloha `zalohy/investra_test-2026-11-13-pred-upozornenim-knihy.dump`, upgrade na 0.14.1; doklady 78,
  řádky 192, nástroje 8, ceny 13 beze změny. Testy: jen 5 známých selhání „nesmí schválit“ u cen (ruční řádek matice).
  Pruh ověřen na datech (admin bez knihy investiční společnosti). Web 8071 restartován.

**Zbývá – první krok:**
1. Uživatel vyzkouší pruh v UI 8071 (nový nástroj s nezaškrtnutou knihou investiční společnosti).
2. Claude Doc (konektor Claude Docs v relaci chyběl): doplnit řádky deníku „Firma nové účetní knihy“, „Příjemce vstupního
   a výstupního poplatku“, „Upozornění na nezaškrtnutou knihu ve formuláři“ a otevřený bod „Účty poplatků za úpis
   a odkup ve prospěch fondu“; pak přepsat `docs/architektura.md` exportem.

**Otevřené otázky:** stejný problém může mít obchod (kniha fondu nezaškrtnutá); zatím neřešeno, počkat na zkušenost uživatele.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední tři řádky)
