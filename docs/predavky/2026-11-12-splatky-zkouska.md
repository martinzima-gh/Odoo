# Předávka 2026-11-12: zkouška storna a opravy splátky v investra_test

**Cíl:** ověřit zámek, opravu a storno splátky (`investra_nav` 0.9.0, `investra_fund` 0.4.0) na datech `investra_test`.

**Stav:** větev `feature/nav-prototyp`; navazuje na `docs/predavky/2026-11-12-splatky-storno.md`.

**Hotovo (souhlas uživatele, zápis jen do `investra_test`):**
- Verze modulů a řádek matice 101 `repayment_reverse` (bez druhé osoby) ověřeny read-only; záloha
  `zalohy/investra_test-2026-11-12-pred-storno-splatky.dump` už existovala, upgrade se neopakoval.
- Zkouška přes Odoo shell jako `delta_priprava` (bez sudo) stejnými metodami jako tlačítka formuláře a okna storna;
  v prohlížeči neklikáno. Fond Delta, Ukázkový termínovaný vklad, datum 15. 12. 2026:
  - splátka 239 (5 045 500) zaúčtována, MISC/2026/12/0001; změna i smazání zaúčtované odmítnuty;
  - oprava: 239 Stornováno (MISC/2026/12/0002), nová 240 v návrhu s `replaced_id` 239, upravena na 5 000 000
    a zaúčtována (MISC/2026/12/0003);
  - storno 240: Stornováno (MISC/2026/12/0004); smazání stornované odmítnuto.
- `docs/sql/16-splatky.sql` (společnost 3363): kontrola 2 vrátila 0 řádků; účty Bankovní účty a Termínované vklady
  mají ze 4 dokladů saldo 0,00 (storna jsou záporná).

**Zbývá – první krok:** volitelně projít splátky 239 a 240 v UI na portu 8071 (Nástroje → Splátky nástrojů),
hlavně vzhled tlačítek a okna storna. Koncept ručního dokladu MISC 119000 zahodí uživatel v UI.

**Otevřené otázky:** žádné nové.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/predavky/2026-11-12-splatky-storno.md`
