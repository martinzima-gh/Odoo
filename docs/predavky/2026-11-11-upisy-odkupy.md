# Předávka 2026-11-11: úpisy a odkupy, body A–E

**Cíl:** bod 8 UX – úpisy a odkupy (zdroj, cena, poplatek, rozdíl, historie, storno, Zaúčtovat) napojené na matici.

**Stav:** větev `feature/nav-prototyp`, commity „Úpisy a odkupy, body A–E…“ a „Předávka: úpisy a odkupy“ (pushnuto).

**Hotovo:**
- `investra_nav` 20.0.0.7.0 (`models/movement.py`): zdroj IS/ruční s důvodem, cena s vazbou na zveřejněné ocenění,
  poplatek s příjemcem, rozdíl a komu patří, zbytek do 0,01 na výnos/náklad, stav, chatter, Zaúčtovat (i hromadně),
  storno a oprava (průvodce); ruční zadání, storno a oprava přes `_gate("subscription_manual")`. Ocenění vynechá
  stornované, bere `capital_amount`; kontroly `movements_posted`, `movement_fee_rate`, `movement_price` (upozornění).
- `investra_fund` 20.0.0.3.0: parametry fondu a třídy. `investra_entity`/`chart_fund`/`cnb` 20.0.0.2.0: 4 nové role,
  pracovní účty 325500, 325600, 668100, 548100, migrace do existujících knih, mapování ČNB.
- `investra_test`: 427 testů všech modulů; opraveny 2 chyby (test ČNB porušoval zámek ocenění; test historie), cnb + nav
  znovu prošly. Záloha `zalohy/investra_test-2026-11-11-pred-upisy-odkupy.dump`. Web 8071 restartován, čítač společností 5770.
- Deník (2 záznamy), otevřený bod „Osnova fondů podle 501“, Claude Doc rev 298, export `docs/architektura.md`,
  SQL `docs/sql/14-upisy-odkupy.sql` (ověřeno pod `dbeaver_ro`).

**Zbývá – první krok:** rozhodnout s uživatelem, zda nezaúčtovaný pohyb v období má ocenění zastavit (dnes upozornění).
Dál: osnova fondů podle vyhlášky 501 (ověřit zdroj, převod rolí); import pohybů z IS až s dokumentací IS.

**Rozhodnutí:** deník 2026-11-11 „Úpisy a odkupy – účty a vzorce“ a „– provedení (body A–E)“ včetně odchylek.

**Otevřené otázky:** zpřísnění kontroly nezaúčtovaných pohybů; čísla účtů podle 501; v UI ověřit formulář pohybu ručně.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-upisy-odkupy.md` (sekce Provedení)
4. `addons/custom/investra_nav/models/movement.py`
5. `docs/osnova-fondu.md`
