# Předávka 2026-11-11: zámek ocenění, plán bodu 8, schvalovací matice

**Cíl:** bod 8 UX (úpisy a odkupy) s předpoklady: zámek ocenění ve třech vrstvách a schvalovací matice.

**Stav:** větev `feature/nav-prototyp`, poslední commit `9e0333a` (vrstva 2) a tato předávka (pushnuto).

**Hotovo:**
- Plány schválené: `docs/navrh-upisy-odkupy.md` (A–E úpisy, F–G zámek), `docs/navrh-schvalovaci-matice.md`.
- Deník rozhodnutí a Claude Doc: „Úpisy a odkupy (bod 8 UX)“, „Zámek ocenění ve třech vrstvách“, „Schvalovací matice“.
- Vrstva 1 (`investra_nav/models/valuation_lock.py`): od Ke schválení do Potvrzeno nic s datem ≤ datu ocenění.
- Vrstva 2 (`investra_nav/models/lock_exception.py`): zveřejnění = `fiscalyear_lock_date`, výjimka jen ze žádosti
  (dva různí schvalovatelé, zatím napevno), kontrola `lock_exception` v ocenění. `investra_nav` 20.0.0.5.0.
- `investra_test`: záloha `zalohy/investra_test-2026-11-11-pred-zamkem-oceneni.dump`, 186 testů nav + dashboard prošlo,
  web 8071 restartován, čítač `res_company_id_seq` 4942.

**Zbývá – první krok:** naprogramovat schvalovací matici podle `docs/navrh-schvalovaci-matice.md`
(model řádků u knihy obhospodařovatele, pole Obhospodařovatel na fondu, migrace `second_person_required`
a `approval_step_ids`, napojení: ocenění, ceny, ruční kurz, výjimka z uzamčení; kontroly v ocenění).
Pak body A–E úpisů a odkupů. Na konci celá sada testů všech 13 modulů Investry (uživatel souhlasí s jedním během).

**Postupy:**
- Po `-u` samostatným procesem vždy restartovat `investra-test-web` (jinak drží starý kód – dnešní chyba
  `max_rate_age_days` na Přehledu).
- `-u investra_nav` spustí jen testy nav a dashboard; ostatní moduly jen s jejich `-u`.
- Změna schématu nebo aktualizace modulu v `investra_test` jen se souhlasem uživatele.

**Otevřené otázky:** žádné; ruční kurz dál blokuje jeho dosavadní kontrola od stavu Schváleno (vrstva 1 se kurzů netýká).
V `investra_dev` se zámek ani matice zatím nenasazují.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-schvalovaci-matice.md`
4. `docs/navrh-upisy-odkupy.md` (body A–E)
5. `addons/custom/investra_nav/models/lock_exception.py`
