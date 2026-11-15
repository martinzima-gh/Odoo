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
