# IM-00 Evidence nástrojů – přehled úkolů a rozdělení mezi modely

Plán: `docs/navrh-evidence-nastroju.md` (schválen 14.–15. 11. 2026). Každý úkol = nová relace Claude Code, která čte jen
`CLAUDE.md`, uvedené oddíly plánu a svůj soubor úkolu. Větev `feature/instrument-master` (z `feature/nav-prototyp`).

| Úkol | Obsah | Model | Zóna | Závisí na |
|---|---|---|---|---|
| IM-01 | Addon, číselníky, práva, seed | Sonnet 5.5 | oranžová | — |
| IM-02 | Průvodce importem číselníků | Sonnet 5.5 | oranžová | IM-01 |
| IM-03 | Emitent: detailní ESA a odvozené údaje | Sonnet 5.5 | oranžová | IM-01 |
| IM-04 | Nástroj: BA0088, CFI, atributy, potvrzení | Sonnet 5.5 | oranžová | IM-01 |
| IM-05 | SPPI z zařazení na nástroj (migrace) | **Opus 5.5** | červená | IM-04 |
| IM-06 | Portfolio: kategorie, schválení, zámek, kompatibilita | **Opus 5.5** | červená (logika klasifikace) | IM-05 |
| IM-07 | Účetní profil a přiřazení | Sonnet 5.5 | oranžová | IM-04, IM-06 |
| IM-08 | README addonu, ukázkové SELECTy, test report | Haiku 5.5 (nebo Antigravity/Copilot v `~/odoo-review`) | zelená | IM-07 |
| IM-09 | Oprava formuláře nástroje: emitent s popiskem, odchylka od typu jako upozornění | Haiku 5.5 (nebo Copilot/Antigravity) | zelená | — |
| IM-10 | Výplata úroku „Nepravidelně“ (toky ručně) | Sonnet 5.5 | červená (malá) | — |
| IM-11 | Variabilní sazba: krok 1 návrh, krok 2 implementace | **Opus 5.5** | červená | IM-10 |
| IM-12 | Záloha, instalace do `investra_test` a `investra_vzhled`, převzetí | Sonnet 5.5 | provozní | IM-09, IM-10 |
| IM-13 | Jedna pracovní databáze `investra` s ukázkovými daty; testy jen na dočasných DB | **Opus 5.5** | provozní | IM-12 |

Proč takto: úkoly s přesným popisem polí a hlášek zvládne Sonnet; Opus jen tam, kde se mění stávající červená zóna,
migrují data a upravují stávající testy klasifikace. Fable 5.2 už není potřeba; vrátit se k němu jen při změně
architektury nebo sporu o účetní logiku. Vzhledové doladění pohledů lze zadat Antigravity nebo Copilotu (bez kreditů Clauda).

Pravidla pro každou relaci:
- Po dokončení úkolu se zastavit; další úkol až na pokyn uživatele. Úkoly IM-05 a IM-06 potřebují před začátkem
  výslovné schválení uživatele (červená zóna).
- Testy na dočasné databázi `investra_ci_master` podle oddílu 2 plánu. Instalaci do `investra_test` a `investra_vzhled`
  uživatel povolil 15. 11. 2026, ale až po dokončení modulu a se zálohou předem; jednotlivé úkoly ji nedělají.
  `investra_dev` se neinstaluje.
- Commit do `feature/instrument-master`, push `origin feature/instrument-master:feature/instrument-master`; do `main` ne.
- Vzhled aplikace zachovat (oddíl 2 plánu).
- Do sekce Výsledek svého souboru doplnit: změněné soubory, příkaz a výsledek testů s počty, co se neověřilo, odchylky.

Prompt pro relaci (doplnit číslo úkolu):

    Přečti CLAUDE.md, docs/ukoly/IM-00-prehled.md a docs/ukoly/IM-0X-….md a z docs/navrh-evidence-nastroju.md jen oddíly
    uvedené v úkolu. Celý projekt neprocházej. Proveď úkol, pusť testy podle oddílu 2 plánu, doplň sekci Výsledek,
    commitni a zastav se.

**Stav 15. 11. 2026 (ST-01):** IM-01 až IM-13 převzaty a sloučeny do `main` (fast-forward); testy `all` 685, 0 selhání, 0 chyb.

**Stav 15. 11. 2026 (ST-01):** IM-01 až IM-13 převzaty a sloučeny do `main` (fast-forward); testy `all` 685, 0 selhání, 0 chyb.
