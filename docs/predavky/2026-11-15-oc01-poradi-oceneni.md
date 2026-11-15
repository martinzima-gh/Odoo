# Předávka: OC-01 pořadí ocenění a zrušení návrhu (2026-11-15)

**Cíl:** nové ocenění nejde založit před existujícím pozdějším oceněním fondu; návrh ocenění jde zrušit tlačítkem.

**Stav:** větev `ukol/OC-01` (z `feature/instrument-master`), pushnutá do `origin ukol/OC-01`. Do `main` nesloučeno.

**Hotové:**
- `investra_nav` 20.0.0.29.1: `_check_no_later_valuation`, tlačítko „Zrušit návrh“ (`action_cancel_draft`),
  `unlink` ruší návrhy dokladů, fond má historii (chatter).
- Testy: `investra_nav` 344, `all` 685, 0 selhání; 8 nových testů v `TestValuationOrderAndCancel`.
- `investra` povýšená (záloha `zalohy/investra-2026-11-15-pred-OC01.dump`), instance 8071 běží; ocenění fondu C
  k 15. 10. 2026 odmítnuto (ověřeno v shellu s rollbackem).
- Deník rozhodnutí, Claude Doc (Přijatá rozhodnutí), otevřené body, Výsledek v zadání.

**Zbývá:**
1. ~~Zrušení id 39 a kontrolní SELECTy~~ hotovo 15. 11. 2026 (výsledek v zadání).
2. Sloučení `ukol/OC-01` do pracovní větve / `main` jen na Martinovu výzvu.

**Rozhodnutí:** 2026-11-15 „Pořadí ocenění a zrušení návrhu (OC-01)“.

**Otevřené:** výjimka pro historická ocenění při převzetí fondu (PF); zrušení návrhu verze 2+ blokuje novou verzi
k témuž datu (jedinečnost fond–datum–verze).

**Číst:** `CLAUDE.md`, `docs/ukoly/OC-01-poradi-a-zruseni-oceneni.md`, tato předávka.
