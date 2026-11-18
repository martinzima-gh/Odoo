# Předávka 2026-11-18 – ZJ-10 fáze 2 hotová

**Cíl:** sledování změn nastavení (ZJ-10) – fáze 2 je naprogramovaná, otestovaná a nasazená do pracovní DB.

**Stav:** větev `ukol/ZJ-zjednoduseni`, kód commit `2a93615` (pushnuto do `origin ukol/ZJ-zjednoduseni`); pracovní DB `investra` povýšená
(11 modulů, záloha `zalohy/investra-2026-11-18-pred-ZJ10-1b-2.dump`), `investra-web` běží na 8071 (HTTP 200).

**Hotové:** mixin s rodičem přes cestu; úplaty (pravidlo, verze, pásma), benchmark (nový seznam/formulář/nabídka), alokace, FX profil, období sazby
(jen poznámka). Testy 455 + 787 bez chyb. Detaily v sekci „Fáze 2“ v `docs/ukoly/ZJ-10-sledovani-zmen-nastaveni.md`.

**Zbývá:**
1. Martin: vizuálně ověřit chatter a Nastavení → Fondy → Benchmarky v prohlížeči (8071).
2. Claude Doc: doplnit 3 rozhodnutí z 18. 11. (fáze 2 ZJ-10, rozsah testů, mixin s cestou) a otevřený bod „Ruční úprava vypočtené úplaty“.
3. Samostatný test, že změna `base_mode` zpětně nemění uložená ocenění (plán bod 5) – zatím jen popsáno.
4. `tools/run_tests.sh all` před sloučením do `main` (jen na Martinův pokyn).

**Rozhodnutí:** viz deník 2026-11-18; odchylka – popisy řádků verze/pásma/nároku (viz ZJ-10, „Fáze 2“).

**Otevřené:** objem `mail_message` po delším provozu; práva čtení chatteru pro účetní čtenáře (neověřeno).

**Číst:** `CLAUDE.md`, `docs/ukoly/ZJ-10-sledovani-zmen-nastaveni.md` (sekce Fáze 2), `docs/rozhodnuti.md` (konec).
