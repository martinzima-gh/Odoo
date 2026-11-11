# Předávka 2026-11-11: riziko 4 a Platnost kurzů

**Cíl:** dořešit riziko 4 ochrany kurzů a nastavení stáří kurzu podle lístku a měny.

**Stav:** větev `feature/nav-prototyp`, poslední commit je ten s touto předávkou (pushnuto). `investra_test` má
aktualizované `investra_rates`, `investra_nav`, `investra_fx_revaluation`; `investra_dev` beze změny.
Nová databáze `investra_test_kontrola` = záloha `zalohy/investra_test-2026-11-11-pred-platnosti-kurzu.dump` + nový kód.

**Hotovo:**
- Riziko 4 akceptováno: standard Odoo se neohýbá, kurzy ČNB zůstávají společné, zámek zrušen; den navíc zůstává.
  Charakterizační test zůstal jako hlídač chování Odoo.
- Tabulka Platnost kurzů (`investra.rate.validity`): ČNB denní 5, měsíční 35, ECB 5, výjimky pro měny;
  pole stáří na fondu a profilu přecenění odstraněna. 362 testů prošlo v `investra_test_kontrola`.

**Zbývá – první krok:** zjistit, proč v `investra_test` padá příprava testů přecenění (otevřený bod „Testy přecenění
v `investra_test`“), nebo se souhlasem nahradit `investra_test` kopií. Pak plány bodů 15, 8, 14, 16, 5.3, 3.

**Rozhodnutí (deník 2026-11-11):** „Platnost kurzů a smíšené kurzy“, „Riziko 4 akceptováno, standard Odoo“,
„Platnost kurzů – provedení“.

**Otevřené otázky:** smazat `investra_test_kontrola` po vyřešení; aktualizace modulů v `investra_dev`.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (řádky Testy přecenění, Platnost kurzů v `investra_dev`)
4. `docs/navrh-ochrana-kurzu.md` (sekce od „Riziko 4“)
5. `addons/custom/investra_rates/models/validity.py`
