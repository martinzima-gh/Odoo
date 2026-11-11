# Předávka 2026-11-11: bod 15 – detail účetních událostí

**Cíl:** u účetní události vidět fond, zdroj s proklikem, částku a měnu (bod 15 podkladu UX).

**Stav:** větev `feature/nav-prototyp`, commit `6777057` a tato předávka (pushnuto).

**Hotovo:**
- Plán a provedení: `docs/navrh-ucetni-udalosti.md` (odpovědi 1–3 ano, sekce Provedení s odchylkami).
- `investra_posting` 20.0.0.2.0, `investra_instruments` 20.0.0.6.0, `investra_nav` 20.0.0.3.0 včetně migrací.
- `investra_test`: záloha `zalohy/investra_test-2026-11-11-pred-bodem-15.dump`, aktualizace, ověření na datech,
  378 testů modulů Investry prošlo. Čítač `res_company_id_seq` po testech 4309.
- `investra_dev` modul `investra_posting` nemá, aktualizace se ho netýká.
- Deník rozhodnutí, otevřené body, Claude Doc (Přijatá rozhodnutí), `docs/sql/12-ucetni-udalosti.sql`.

**Zbývá – první krok:** plán bodu 8 (úpisy a odkupy: zdroj, zaokrouhlení, poplatek, historie změn);
pak 14, 16, 5.3, 3. U bodu 8 se zeptat na pravidlo zaokrouhlení a komu poplatek patří podle statutu.

**Otevřené otázky:** žádné z této relace.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (řádek Body podkladu UX bez plánu)
4. `docs/predavka-2026-11-10-ux.md` (bod 8)
