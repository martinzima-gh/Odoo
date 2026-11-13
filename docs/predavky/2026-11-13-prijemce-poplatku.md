# Předávka 2026-11-13: příjemce vstupního a výstupního poplatku

**Cíl:** vstupní a výstupní poplatek mají vlastního příjemce (obhospodařovatel, distributor, fond, třída);
u třídy volba výnos / kapitál podle statutu. Dále výchozí firma nové účetní knihy podle přepínače.

**Stav:** větev `feature/nav-prototyp`, kód v 0c1f718 (pushnuto), kniha v 53cba5b.
`investra_entity` 0.8.0, `investra_chart_fund` 0.8.0, `investra_cnb` 0.8.0, `investra_fund` 0.7.0, `investra_nav` 0.25.0.

**Hotovo:**
- Fond a třída: `entry_/exit_fee_recipient`, `entry_/exit_fee_capital`; pohyb `fee_recipient` + `fee_to_capital`.
  Fond + kapitál zakázáno (kontrola na fondu, třídě i pohybu).
- Účtování `_fee_line()` v `movement.py`; poplatek třídy jde do `capital_amount` (třída ho dostane celý v ocenění).
- Role `entry/exit_fee_income` (767200, 767300) a `entry/exit_fee_capital` (564100, 564200), účty „(pracovní)“; ČNB řádky.
- Migrace: `investra_fund` 0.7.0 pre (kopie starého `fee_recipient`), `investra_chart_fund` 0.8.0 post (účty a mapování).
- Čistá DB: 544 testů, 0 chyb (5 nových v `test_movement.py`).
- `investra_test`: záloha `zalohy/investra_test-2026-11-13-pred-poplatky.dump`, upgrade; doklady 78 / řádky 192 / obrat
  a kapitál z pohybů (230 100 000) beze změny; příjemci převzati (vše obhospodařovatel); 7 knih má nové role.
  Testy: jen známá 3 selhání `TestApprovalMatrix` (řádek matice 83 od 2026-11-13). Web 8071 restartován.
- Deník rozhodnutí (2 řádky), otevřený bod „Účty poplatků za úpis a odkup ve prospěch fondu“.

**Zbývá – první krok:** doplnit do Claude Doc (tabulka Přijatá rozhodnutí) řádky „Firma nové účetní knihy“
a „Příjemce vstupního a výstupního poplatku“ a otevřený bod; pak přepsat `docs/architektura.md` exportem
(13. 11. odpoledne byl Claude Doc nedostupný). Uživatel vyzkouší v UI 8071 formulář fondu a úpis s poplatkem.

**Pozor:**
- Firma „Investra Services s.r.o.“ (id 8148) v `investra_test` má šablonu fondu, ale nemá knihu ani mapování rolí (stav dřívější).
- `TestSharedInstrumentBook.test_book_not_active_gives_clear_message` jednou selhal při instalaci s testy (s tehdy
  necommitovaným kódem jiné relace); samostatně i v opakovaném běhu prošel.

**Otevřené otázky:** čísla účtů a zachycení výnos / kapitál potvrdit u auditora (otevřený bod).

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední dva řádky)
4. `addons/custom/investra_nav/models/movement.py` (`_capital_functional`, `_fee_line`)
