# Předávka 2026-11-18 – ZJ-10 sloučené do main

**Cíl:** sledování změn nastavení (ZJ-10, fáze 1 a 2) je hotové, otestované a v `main`; navazují drobné úpravy vzhledu a menu.

**Stav:** `main` a `ukol/ZJ-zjednoduseni` na `e1e566a` (pushnuto). Pracovní DB `investra` povýšená (`investra_theme`, `investra_fund`),
`investra-web` běží na 8071. Zálohy v `zalohy/`: `investra-2026-11-18-pred-theme-chatter.dump`, `investra-2026-11-18-pred-menu-role.dump`.

**Hotové:**
- Claude Doc: 3 rozhodnutí z 18. 11. a otevřený bod „Ruční úprava vypočtené úplaty“ (rozhodnutí o vzhledu a menu níže tam ještě chybí).
- Test `TestBaseModeRetroactive` (`investra_nav/tests/test_fees.py`): změna `base_mode` nemění zaúčtované ocenění, návrh se změní až novým výpočtem.
- Chatter vedle formuláře: šířka podle okna, širší formulář (`investra_theme/static/src/scss/theme.scss`); Martin ověřil.
- Menu: Role přímo pod Schvalování a audit, nadřazená „Uživatelé a role“ zrušena.
- `tools/run_tests.sh all`: 917 testů bez chyby (před změnou menu); po ní `investra_fund` 52 testů bez chyby.

**Zbývá (první krok):**
1. Doplnit do Claude Doc rozhodnutí „Vzhled chatteru a menu Role“ (řádek je v `docs/rozhodnuti.md`).
2. Martin rozhodne o zámku `base_mode` po prvním výpočtu a o „Ruční úpravě vypočtené úplaty“ (obojí červená zóna, potřebuje plán).

**Rozhodnutí:** viz deník 2026-11-18 (poslední řádek).

**Otevřené:** objem `mail_message` po delším provozu; práva čtení chatteru pro `account.group_account_readonly` (neověřeno);
po změně menu zkontrolovat případné odkazy na nabídku v dokumentaci.

**Číst:** `CLAUDE.md`, `docs/ukoly/ZJ-10-sledovani-zmen-nastaveni.md` (konec), `docs/rozhodnuti.md` (konec), `docs/otevrene-body.md`.
