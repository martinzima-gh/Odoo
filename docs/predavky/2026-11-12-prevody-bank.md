# Předávka 2026-11-12: převody mezi bankami, role s více účty, bankovní poplatky

**Cíl:** ověřit převod mezi dvěma bankami přes peníze na cestě 119000 a připravit knihy fondů na více bank (Enterprise).

**Stav:** větev `feature/nav-prototyp`, commit „Role s více účty, převody mezi bankami přes 119, bankovní poplatky 612“.

**Hotovo:**
- Rozhodnutí uživatele (deník 2026-11-12 „Role s více účty“, „Převody mezi bankami a bankovní poplatky“; Doc rev 307, export).
- `investra_entity` 20.0.0.5.0: `investra.role.account.extra_account_ids`, `accounts_for`, `add_extra_account`, účet v jedné
  roli (omezení), účet nového bankovního deníku k roli `bank`; role `expense_bank_fee`.
- `investra_chart_fund` 20.0.0.5.0: 119100 Inkasa na cestě, 119200 Platby na cestě (Odoo Outstanding, dříve 131102/131103),
  612000 Bankovní poplatky; modely párování Internal Transfers → 119000 (byl archivovaný 322101), Bank Fees → 612000
  (byl 615000); migrace 0.5.0.
- `investra_cnb` 20.0.0.5.0: součet hlavního i dalších účtů, VYFO20_11 ř. 23 pro bankovní poplatky, `_accounts_without_role`.
- `investra_nav` 20.0.0.8.0: zůstatky rolí s dalšími účty, FX přecenění bank po účtech, kontrola `accounts_role` (upozornění).
- Testy: čistá databáze 440 testů 0 chyb. Kopie `investra_test`: předvaha podle id účtu shodná; 14 selhání testů
  schvalování způsobují řádky matice 81, 82 (12. 11. 06:38, druhá osoba vypnuta), ne kód.
- `investra_test` aktualizována (záloha `zalohy/investra_test-2026-11-12-pred-prevody-bank.dump`), web 8071 restartován,
  ve fondu 244 deník BNK2 (131102). SELECTy `docs/sql/15-prevody-bank.sql`.

**Zbývá – první krok:** ruční převod v Community UI nejde (ruční záznam nenabízí bankovní účty). Cesta přes 119000
ověřena simulací na kopii (deník 2026-11-12 „Převod mezi bankami – ověření simulací“). Další krok: test v UI až s Enterprise.
V `investra_test` je nezaúčtovaný koncept ručního dokladu z 12. 11. (MISC, 119000) z pokusu uživatele – zahodit v UI.
Hotovo po předávce: pomocné databáze smazány, matice opravena (řádek 82 zpět, řádek 83 od 13. 11.),
`investra_dev` na `investra_entity` 0.5.0.

**Otevřené otázky:** ocenění 9572 (Delta) schválené 12. 11. bez druhé osoby zůstává v historii; složka příloh
`investra_dev_kopie` bez databáze (z dřívější relace) – smazat?
poplatky 612 vs. 611 (pokladní a mezibankovní operace) – rozhodnuto 612; pokladna (deník typu cash) zatím bez role.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/rozhodnuti.md` (poslední dva záznamy)
4. `addons/custom/investra_chart_fund/migrations/20.0.0.5.0/post-migration.py`
5. `docs/sql/15-prevody-bank.sql`
