# IM-12 Převzetí a instalace do investra_test a investra_vzhled

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 (při chybě migrace se zastavit a předat Opusu) |
| Zóna | provozní krok s datovým dopadem; souhlas uživatele z 15. 11. 2026 (deník, „Číselník BA0088 v katalogu ČNB“) |
| Závisí na | IM-09, IM-10 (IM-11 se doinstaluje později stejným postupem) |
| Číst | `CLAUDE.md` (Bezpečnostní pravidla, Prostředí), `tools/run_tests.sh`, sekce Výsledek v `IM-05` (migrace SPPI) |

**Stav 15. 11. 2026 (ověřeno SELECTem):** `investra_instrument_master` není nainstalován v žádné databázi;
`investra_instruments` je v `investra_test` i `investra_vzhled` ve verzi 20.0.0.14.2, kód je 20.0.0.15.0 s migrací SPPI.
Uživatel proto nové obrazovky zatím nikde nevidí. Kontejner `investra-vzhled-web` čte moduly z `~/odoo-review`.

**Postup:**
1. Záloha: `pg_dump` (formát custom) `investra_test` a `investra_vzhled` do `zalohy/` s datem a „pred-IM“; ověřit
   čitelnost (`pg_restore -l`). Bez čitelné zálohy nepokračovat.
2. Před upgradem si SELECTem uložit počty zařazení podle `sppi` a `ifrs9_category` v obou databázích.
3. `investra_test`: upgrade `investra_instruments` a instalace `investra_instrument_master` (bez demo dat);
   z logu migrace 20.0.0.15.0 opsat do Výsledku nástroje s konfliktem SPPI. Po upgradu stejné SELECTy:
   kategorie IFRS 9 zařazení se nesmí změnit; rozdíl = zastavit, nic neopravovat, popsat uživateli.
4. `investra_vzhled`: převést `feature/instrument-master` do `~/odoo-review` (postup z paměti „souhlas s upgradem
   vzhledu“), stejný upgrade a instalace přes `docker exec investra-vzhled-web`, pak restart kontejneru; stejné kontroly.
   Restart `investra-test-web`, aby načetl nový kód.
5. Kouřová zkouška čtením: formulář nástroje, portfolia a nabídka Nastavení → Číselníky se načtou bez chyby v logu.
6. Sekce Převzetí v IM-01 až IM-10: datum, výsledek, odkaz na tento úkol.
7. Deník rozhodnutí a Claude Doc (tabulka Přijatá rozhodnutí): instalace provedena; výplata „Nepravidelně“.
   Předávka do `docs/predavky/`.

**Nedělat:** `investra_dev`, sloučení do `feature/nav-prototyp` nebo `main` (jen na výzvu uživatele), obnova databáze
ze zálohy bez dotazu, mazání čehokoli kromě vlastních `investra_ci_*`, ruční SQL zápisy.

**Kritéria přijetí:** obě databáze mají `investra_instrument_master` ve stavu installed a `investra_instruments`
20.0.0.15.0 (nebo vyšší); kategorie zařazení beze změny; zálohy existují a jsou čitelné; uživatel dostal adresy,
kde co uvidí (8071 test, 8072 vzhled).

## Výsledek

**Stav: hotová jen část (`investra_test`); `investra_vzhled` se nepovýšil – zastaveno před krokem 4.** Provedl Claude Code (Sonnet 5.5), 15. 11. 2026.

**1. Zálohy** (`zalohy/`, mimo git): `investra_test-2026-11-15-pred-IM.dump` (6,1 MB), `investra_vzhled-2026-11-15-pred-IM.dump` (6,3 MB);
`pg_restore -l` u obou čitelný (10 291 položek).

**2. Stav před upgradem** (SELECT nad `investra_portfolio_classification`):
- `investra_test`: 9 zařazení; SPPI Nehodnotí se 8, Splněn 1; IFRS 9 FVTPL 8, naběhlá hodnota 1; kontrolní součet dvojic (id, sppi, kategorie) `d0a30097…`.
- `investra_vzhled`: 20 zařazení; SPPI Nehodnotí se 19, Splněn 1; FVTPL 19, naběhlá hodnota 1; součet `97b42bd1…` (zatím jen stav před, bez upgradu).

**3. `investra_test`:** `odoo -u investra_instruments -i investra_instrument_master --without-demo` (bez testů), návratový kód 0, v logu 0 ERROR/CRITICAL.
- Migrace 20.0.0.15.0, log: „IM-05: SPPI přeneseno na 4 nástrojů; nástroje s rozdílným SPPI: žádné; zařazení podle SPPI před {na: 8, pass: 1}, po {pass: 1, na: 8}.“
- Stavy: `investra_instrument_master` 20.0.0.6.0 installed, `investra_instruments` 20.0.0.15.0, `investra_nav` 20.0.0.28.9 (povýšen jako závislý).
- Po upgradu stejné SELECTy: **kategorie IFRS 9, SPPI i kontrolní součet beze změny** (9 zařazení).
- Restart `investra-test-web`; `/web/login` vrací 200, registr se načetl bez chyby (0 ERROR). Pohledy nástroje/portfolia/zařazení v DB (12) a 2 položky nabídky s „číselník“ existují.

**4. `investra_vzhled` – NEPROVEDENO. Důvod:** konvertovat větev do `~/odoo-review` nelze bez zásahu do cizí práce. Klon je na `feature/instrument-master` v commitu 840ff11 (bez IM-09 a IM-10) a má **neuložené úpravy** `investra_counterparty/views/counterparty_views.xml` a `investra_instruments/views/instrument_views.xml` (ruční verze IM-09, v `docs/ukoly/CP-*` nezapsaná). Stejné soubory mění commit 29ee710, takže převzetí by je přepsalo nebo skončilo konfliktem. Nic jsem v klonu neměnil.
Kontejner `investra-vzhled-web` čte moduly jen z `~/odoo-review` (`/mnt/review-addons`).
Návrh: (a) úpravy v klonu zahodit, protože je pokrývá 29ee710, a klon přepnout na tento commit; nebo (b) je nejdřív uložit stranou/commitnout. Rozhodne Martin.

**Neověřeno:** kouřová zkouška v UI (formulář nástroje, portfolio, Nastavení → Číselníky) – jen log, registr a SELECT; testy Odoo se nespouštěly (úkol je nepožaduje); `investra_instrument_master` je nainstalován bez demo dat.
**Adresy:** 8071 – `investra_test` (nové obrazovky už vidět); 8072 – `investra_vzhled` zatím beze změny.

### Doplnění 15. 11. 2026 odpoledne – `investra_vzhled` a `investra_nav` 20.0.0.29.0 (Claude Code, Opus 5.5)

Martin rozhodl variantu (a): úpravy dvou pohledů v `~/odoo-review` zahodit (pokrývá je 29ee710). Diff zahozených úprav
uložen jen dočasně mimo repozitář. Klon posunut fast-forwardem 840ff11 → `b27ad0a`, pracovní strom čistý.

1. **Zálohy:** `zalohy/investra_vzhled-2026-11-15-pred-nav29.dump` (6,0 MB, 10 291 položek),
   `zalohy/investra_test-2026-11-15-pred-nav29.dump` (6,0 MB, 10 737 položek); `pg_restore -l` čitelné.
2. **`investra_vzhled`:** `-u investra_instruments,investra_nav -i investra_instrument_master --without-demo` přes
   `docker exec investra-vzhled-web`, rc 0, 0 ERROR/CRITICAL (log `.test-logs/upgrade-vzhled-2026-11-15-nav29.log`).
   IM-05: SPPI přeneseno na 12 nástrojů, konflikty žádné, zařazení {na 19, pass 1} před i po.
   IM-11: 20 nástrojů pevná sazba, 9 toků platných, 0 období. Restart kontejneru; 4 řádky ERROR/CRITICAL v logu
   pocházejí ze starého procesu v sekundě před restartem (neznal nový modul), po restartu registr bez chyby, `/web/login` 200.
3. **`investra_test`:** `-u investra_nav` přes `docker exec investra-test-web`, rc 0, 0 ERROR
   (log `.test-logs/upgrade-test-2026-11-15-nav29.log`); IM-11: 9 nástrojů pevná sazba, 9 toků, 0 období.
   Restart, registr bez chyby, 8071 `/web/login` 200.
4. **Kontrola dat** (SELECT před a po, obě DB): počet a kontrolní součet zařazení (id, SPPI, IFRS 9) a toků
   (id, nástroj, datum, částka) **beze změny** (vzhled 20 zařazení `97b42bd1…`, test 9 `d0a30097…`, toky 9 `dcfbfadc…`).
5. **Stav modulů v obou DB:** `investra_instrument_master` 20.0.0.6.0, `investra_instruments` 20.0.0.15.0,
   `investra_nav` 20.0.0.29.0, vše installed. Kritéria přijetí splněna.

Nález: varování o duplicitních popiscích `investra.valuation.class` → zadání `AG-017` (návrh).
Neověřeno: UI v prohlížeči (formulář nástroje, průvodce sazbou, nabídka Přehled na 8072 – bod 4 předávky čeká na
text chyby od Martina); testy Odoo se nespouštěly (testy IM-11 prošly na čisté DB, viz IM-11 Výsledek).
