# Předávka 2026-11-11: přečíslování osnovy fondů podle vyhlášky 501 – provedeno

**Cíl:** převést šablonu `investra_fund` a knihy fondů na skupiny přílohy č. 4 vyhlášky 501/2002 Sb.

**Stav:** větev `feature/nav-prototyp`, commit „Osnova fondů podle vyhlášky 501: přečíslování šablony a knih“, pushnuto.

**Hotovo:**
- Převodová tabulka, rozhodnutí k otázkám a provedení v `docs/osnova-fondu.md` (sekce Provedení 2026-11-11).
- Kód: `investra_entity` 20.0.0.3.0 (role `repo_client`, `participation_fv`), `investra_chart_fund` 20.0.0.3.0 (CSV, prefixy
  1311/1111/3221, pomocné účty 7619xx/6619xx, migrace), `investra_instruments` 20.0.0.8.0 (`_proposal_role`),
  `investra_counterparty` 20.0.0.2.0 (repo podle sektoru ESA), `investra_cnb` 20.0.0.3.0 (map_74–77), `investra_nav`
  (kontrola `classification_proposal`, upozornění).
- Ověřeno na kopii: předvaha podle id účtu shodná, NAV 5 ocenění shodné se základem (starý kód), 432 testů 0 chyb, reference 55 OK.
- `investra_test`: 5 ocenění Ke schválení vráceno (rozhodl uživatel), záloha `zalohy/investra_test-2026-11-11-pred-osnovou-501.dump`,
  moduly aktualizovány, předvaha shodná, web 8071 restartován.
- Deník (2 záznamy), otevřené body (bod osnovy uzavřen, nový bod ČNB pro účasti v RH), Claude Doc rev 304, export `docs/architektura.md`.

Pomocné kopie `investra_test_osnova` a `investra_test_zaklad` (databáze a filestore) smazány na pokyn uživatele.

**Zbývá – první krok:** opravit ukázková data v `investra_test` (se souhlasem). Dál: metodik potvrdí řádek ROFO10_11 pro účasti v RH (14, nebo 6/7); ukázková data: dluhopis má
v zařazení roli `instrument` místo `instrument_debt`, chybějící schválená cena dluhopisu fondu Beta k 2026-10-31);
`investra_dev` – přečíslování až se zálohou a souhlasem (fondové knihy ověřit dotazem, `investra_nav` tam není).

**Rozhodnutí:** deník 2026-11-11 „Osnova fondů – převodová tabulka“ a „Osnova fondů – provedení“.

**Otevřené otázky:** závaznost tříd a skupin směrné osnovy (§ 66 vyhlášky 501 doslovně neověřen); otisk ocenění podle rolí
místo čísel účtů (volitelný samostatný plán, červená zóna).

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/osnova-fondu.md` (převodová tabulka a Provedení)
4. `addons/custom/investra_chart_fund/migrations/20.0.0.3.0/post-migration.py`
5. `docs/otevrene-body.md` (bod „Účasti v reálné hodnotě ve výkazu ČNB“)
