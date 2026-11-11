# Předávka 2026-11-11: schvalovací matice naprogramována

**Cíl:** bod 8 UX (úpisy a odkupy) s předpoklady; zámek ocenění hotový, schvalovací matice hotová.

**Stav:** větev `feature/nav-prototyp`, commit „Schvalovací matice obhospodařovatele“ (pushnuto).

**Hotovo:**
- `investra_fund` 20.0.0.2.0: `models/approval_matrix.py` – řádky matice (činnost, nejnižší role provádějícího,
  druhá osoba Ne/Ano/Kroky, schvalovatelé s nejnižší rolí, jmenovití uživatelé, Platí od), pole Obhospodařovatel
  a Zpřísnění matice na fondu, záznam „Úkony bez druhé osoby“, žádost → potvrzení, výchozí řádky (data, `builtin`).
- Napojení: ocenění (předložení, schválení, vrácení, storno, zveřejnění), cena, ruční kurz (`investra_rates`
  háčky `_check_manual_access`, `_manual_pending`), výjimka z uzamčení, ruční kategorie IFRS 9 (tlačítko „Ruční kategorie…“).
- Kontroly ocenění `matrix_valuation`, `second_person`, `matrix_change` (upozornění).
- Migrace `investra_nav` 20.0.0.6.0; `investra_test`: 310 testů fund/rates/instruments/nav/dashboard prošlo,
  záloha `zalohy/investra_test-2026-11-11-pred-matici.dump`, web 8071 restartován, čítač `res_company_id_seq` 5194.
- Deník rozhodnutí a Claude Doc: „Schvalovací matice – provedení“ (včetně odchylky u výchozích řádků).
- Ukázkové SQL `docs/sql/13-schvalovaci-matice.sql` (ověřeno na `investra_test`).

**Zbývá – první krok:** body A–E úpisů a odkupů podle `docs/navrh-upisy-odkupy.md`; ruční úpis a odkup
napojit na činnost `subscription_manual` (vzor: `_gate` jako u zveřejnění ocenění). Na konci celá sada testů
všech 13 modulů (souhlas uživatele s jedním během). Export Claude Doc do `docs/architektura.md` (Doc rev 297, soubor 289).

**Rozhodnutí:** viz deník 2026-11-11 „Schvalovací matice – provedení“.

**Otevřené otázky:** fond 200 v `investra_test` měl vypnutou druhou osobu; teď platí čtyři oči. Pro ruční
zkoušení bez druhé osoby přidat výchozí řádek „Schválení ocenění“ s volbou Ne (Nastavení → Fondy → Schvalovací matice).
Tabulka `investra_fund_approval_step` zůstala v DB prázdná (Odoo ji nesmazalo), nevadí.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-upisy-odkupy.md` (body A–E)
4. `addons/custom/investra_fund/models/approval_matrix.py`
5. `addons/custom/investra_nav/models/valuation.py` (metody `_matrix_gate`, `action_publish`)
