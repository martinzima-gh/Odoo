# Předávka 2026-11-12: storno a oprava obchodu, pojistka kurzu

**Cíl:** opravit zaúčtovaný obchod stornem (vypořádání nebo celého obchodu) a zabránit chybnému kurzu vypořádání.

**Stav:** větev `feature/nav-prototyp`, commit „Storno vypořádání, storno a oprava obchodu…“ (pushnuto).
`investra_fund` 0.6.0, `investra_instruments` 0.12.0, `investra_nav` 0.21.0. Claude Doc rev 326.
`investra_test` povýšena se souhlasem uživatele (záloha `zalohy/investra_test-2026-11-12-pred-stornem-obchodu.dump`,
předvaha a počty dokladů shodné), web 8071 restartován. Testy nad `investra_test` mají 13 selhání matice a schvalování
kvůli ručním řádkům matice 81 a 82 (bez druhé osoby od 12. 11.), stejně jako před změnou; na čisté DB 0 chyb.

**Hotovo (deník 12. 11. „Storno a oprava obchodu, pojistka kurzu“ a „Náhled zaúčtování jako standard“):**
- Tlačítka Stornovat vypořádání / Opravit / Stornovat, okno s důvodem (`investra_nav/models/trade_reverse.py`).
- Stav Stornováno, obchod mimo pozice; zámek ocenění vrstva 1 odmítne, po zveřejnění jen s výjimkou z uzamčení.
- Matice `trade_reverse` bez druhé osoby; kurz v měně fondu vynucen 1; upozornění na odchylku kurzu vypořádání nad 10 %.
- Testy: čistá DB 509 testů (14 nových), po opravě testu celá sada 507 testů 0 chyb (`-u`).
- Upgrade ověřen na kopii `investra_test`: předvaha a počty dokladů shodné; storno vypořádání obchodu 5348 na kopii prošlo
  (MISC/2026/11/0003 stornováno 0005, nové vypořádání 0006 s kurzem 1). Pomocné DB `investra_ci_storno*` smazány.
- Pravidlo do CLAUDE.md: náhled zaúčtování u každé operace s účetním dopadem.

**Zbývá – první krok:** uživatel opraví obchod 5348 v UI (Stornovat vypořádání, kurz vypořádání 1, Vypořádat);
pak ověřit doklady a předvahu.
Pak otevřený bod „Náhled zaúčtování u dalších operací“ (splátky, úpisy a odkupy) – zatím neprogramovat.

**Otevřené otázky:** žádné nové. Známé omezení: storno nevypořádaného obchodu bez dokladu (rozvaha ke dni vypořádání)
v zveřejněném období zámek Odoo nehlídá; rozdíl v RH do vypořádání dorovná další ocenění.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `addons/custom/investra_nav/models/trade_reverse.py`
4. `docs/otevrene-body.md` (bod „Náhled zaúčtování u dalších operací“)
