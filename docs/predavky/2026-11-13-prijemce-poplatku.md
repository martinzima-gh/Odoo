# Předávka 2026-11-13: příjemce poplatku jedním výběrem

**Cíl:** místo zaškrtávátka „do kapitálu“ jeden výběr příjemce, stejný pro vstupní i výstupní poplatek.

**Stav:** větev `feature/nav-prototyp`, commit `4f9871c` (+ tato předávka); `investra_fund` 0.8.0, `investra_nav` 0.27.0.

**Hotovo:**
- Volby: Obhospodařovatel, Distributor, Fond, Třída – výnos (`class_income`), Třída – kapitál (`class_capital`);
  fond, třída i pohyb. Zaúčtování, role, účty a mapování ČNB beze změny. „Fond – kapitál“ záměrně není.
- Pre-migrace obou modulů převede „class“ podle zaškrtávátka; Odoo 20 pak staré sloupce samo odstraní.
- Testy na čisté DB: 319, 0 chyb. Pomocné DB `investra_ci_prijemce`, `investra_ci_migrace` smazány.
- `investra_test`: záloha `zalohy/investra_test-2026-11-13-pred-prijemcem-poplatku.dump`, upgrade, doklady 78,
  řádky 192 beze změny, fond s „Třída + kapitál“ → `class_capital`. Web 8071 restartován.
- Deník: „Příjemce poplatku jedním výběrem“.

**Zbývá – první krok:**
1. Uživatel zkontroluje formulář fondu na 8071.
2. Claude Doc (v relaci chyběl konektor Claude Docs): řádky deníku „Firma nové účetní knihy“, „Příjemce vstupního
   a výstupního poplatku“, „Upozornění na nezaškrtnutou knihu ve formuláři“, „Příjemce poplatku jedním výběrem“
   a otevřený bod „Účty poplatků za úpis a odkup ve prospěch fondu“; pak export do `docs/architektura.md`.
3. `investra_vzhled` (8072, moduly z `~/odoo-review`) má starou verzi; povýšit jen po dohodě.

**Otevřené otázky:** „Fond – kapitál“ jen pokud by ho vyžadoval statut fondu s více třídami.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední čtyři řádky)
