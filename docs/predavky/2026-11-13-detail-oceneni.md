# Předávka 2026-11-13: detail ocenění, převzetí CP, zásady obrazovek

**Cíl:** převzít práci Copilota (vzhled, graf kurzů) a předělat detail ocenění tak, aby byl jednoduchý a v duchu firemní grafiky.

**Stav:** větev `feature/nav-prototyp` (pushnutá); `investra_fund` 0.8.0, `investra_nav` 0.27.1, `investra_theme` beze změny verze.
`~/odoo-review` větev `cp/vzhled` = `feature/nav-prototyp` (sloučeno).

**Hotovo:**
- Příjemce poplatku jedním výběrem (5 voleb), migrace; `investra_test` i `investra_vzhled` povýšeny, doklady beze změny.
- Převzetí CP-2026-11-13 (opravy pro OWL 3), pak nový detail ocenění: řádek údajů, pás FK / změna FK / výsledek za období,
  karty tříd se změnou kurzu a grafem 12 měsíců, velký graf a panel Základní údaje zrušeny, NFK na Kontrolách.
- Stavový řádek ve všech formulářích jako bubliny (hotové Lagoon, aktuální Petroleum, budoucí bílé).
- Tabulka tříd: kód třídy, kurz a změna v notaci jazyka, bez ořezu a prázdných řádků; datum všude 30.09.2026.
- Zásady `docs/vzhled/zasady-obrazovek.md`, nový vzor v `.github/copilot-instructions.md`.
- Testy na čisté DB 312, 0 chyb. Zálohy v `zalohy/` (investra_test a investra_vzhled před každým upgradem).

**Zbývá – první krok:**
1. ~~Claude Doc~~ hotovo 2026-11-13: 7 rozhodnutí a otevřený bod účtů poplatků v Doc (rev 333), export `5dd8990`.
2. Copilot upravuje další obrazovky podle zásad; převzetí podle `docs/ukoly/CP-*`.

**Otevřené otázky:** „Fond – kapitál“ u příjemce poplatku jen pokud by ho vyžadoval statut; pruh nezaškrtnuté knihy u obchodu.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/vzhled/zasady-obrazovek.md`
4. `docs/rozhodnuti.md` (posledních 7 řádků)
