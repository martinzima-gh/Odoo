# Předávka 2026-11-11: oprava ukázkových dat investra_test po přečíslování osnovy

**Cíl:** opravit roli ukázkového dluhopisu a chybějící cenu fondu Beta k 2026-10-31.

**Stav:** větev `feature/nav-prototyp`, commit „Oprava ukázkových dat investra_test: role dluhopisu, cena Beta“.

**Hotovo (jen data `investra_test`, kód beze změny):**
- Záloha `zalohy/investra_test-2026-11-11-pred-opravou-ukazkovych-dat.dump`.
- Zařazení 1, 7, 4 (Ukázkový, Alfa, Beta): role `instrument_debt`; přeúčtování 381000 → 382000 událostí „Ostatní“
  (Ukázkový a Alfa 30 240 000 k 2027-02-01, Beta 10 000 k 2026-10-04), doklady zaúčtované a zahašované.
- Cena dluhopisu fondu Beta k 2026-10-31 = 10 000 (beta_priprava / beta_schvaleni).
- Koncepty ocenění 9567, 9568, 9569 přepočtené: FK shodné se základem, kontrola zařazení bez upozornění.
- Popis v `docs/osnova-fondu.md` (Provedení), kontrolní SELECT 8 v `docs/sql/11-klasifikace.sql`.

**Zbývá – první krok:** `investra_dev` – přečíslování osnovy až se zálohou a souhlasem (nejdřív dotazem ověřit fondové
knihy; `investra_nav` tam není). Dál: metodik potvrdí řádek ROFO10_11 pro účasti v RH (14, nebo 6/7).

**Rozhodnutí:** varianta A opravy (změna role + přeúčtování), cenu schvaluje ukázkový schvalovatel – uživatel 2026-11-11.

**Otevřené otázky:** zveřejněná ocenění k 2027-01-31 (Ukázkový, Alfa) mají dluhopis na 381000 – u testovacích dat
ponecháno; závaznost tříd a skupin směrné osnovy (§ 66 vyhlášky 501).

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/osnova-fondu.md` (Provedení)
4. `addons/custom/investra_chart_fund/migrations/20.0.0.3.0/post-migration.py`
5. `docs/otevrene-body.md` (bod „Účasti v reálné hodnotě ve výkazu ČNB“)
