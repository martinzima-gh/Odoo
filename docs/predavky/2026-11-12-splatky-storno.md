# Předávka 2026-11-12: Excel balíčku, zámek a storno splátky

**Cíl:** uzavřít otevřené body „Excel balíčku pro depozitáře“ a „Zámek splátky po zaúčtování“.

**Stav:** větev `feature/nav-prototyp`, commity `db066de` (Excel) a `0b3fb2e` (splátky) + dokumentace.

**Hotovo:**
- Balíček XLSX: `strings_to_formulas` vypnuto, text začínající `=` zůstane textem (test s fondem „=1+1 Fond“).
- `investra_nav` 20.0.0.9.0: splátka má stav Návrh/Zaúčtováno/Stornováno; zaúčtovaná je zamčená (změna, smazání,
  zápis stavu a události); storno k datu splátky a oprava (storno + nová splátka v návrhu, `replaced_id`), okno
  s důvodem (`investra.instrument.repayment.reverse.wizard`); zámek ocenění při zadání, změně, smazání a stornu;
  stornovaná splátka neblokuje kalendář. Migrace: splátky s událostí → Zaúčtováno.
- `investra_fund` 20.0.0.4.0: činnost matice `repayment_reverse`, výchozí bez druhé osoby (rozhodnutí uživatele).
- Testy: čistá databáze `investra_ci_splatky`, všechny vlastní moduly, 449 testů 0 chyb (9 nových).
  V `investra_test` (bez upgradu) 215 testů `investra_nav`, 8 chyb jen v matici kvůli řádkům 81 a 82 platným 12. 11.
- Deník rozhodnutí, otevřené body, Claude Doc rev 310 a export, SELECTy `docs/sql/16-splatky.sql`
  (spuštěny jen na prázdné databázi).

**Zbývá – první krok:** se souhlasem uživatele záloha a upgrade `investra_test` na `investra_fund` 0.4.0 a
`investra_nav` 0.9.0 (v `investra_test` 0 splátek, migrace nic nemění), restart webu 8071, zkouška storna v UI.
`investra_dev` se netýká (`investra_nav` tam není).

**Otevřené otázky:** smazat pomocnou databázi `investra_ci_splatky`? Složka příloh `investra_dev_kopie` (z dřívějška)?
Koncept ručního dokladu MISC 119000 v `investra_test` zahodí uživatel v UI.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední dva záznamy)
4. `addons/custom/investra_nav/models/instrument_accrual.py` (třída splátky)
5. `docs/sql/16-splatky.sql`
