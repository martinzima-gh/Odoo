# IM-08 Dokumentace, ukázkové dotazy a test report

| Položka | Hodnota |
|---|---|
| Model | Haiku 5.5 (nebo Antigravity / Copilot v `~/odoo-review`) |
| Zóna | zelená |
| Plán | celý `docs/navrh-evidence-nastroju.md`; sekce Výsledek v `docs/ukoly/IM-01` až `IM-07` |

**Cíl:** krátká dokumentace pro uživatele a správce číselníků a doklad o testech.

**Rozsah souborů:**
- `addons/custom/investra_instrument_master/README.md`: co modul dělá, postup uživatele (emitent → nástroj → portfolio →
  zařazení), správa číselníků a import nové metodiky, instalace a upgrade, zdroje seed dat, seznam neimplementovaných bodů
  (oddíl 8 plánu).
- `docs/sql/12-evidence-nastroju.sql`: jen `SELECT` (emitenti s ESA a typem, nástroje bez BA0088, portfolia s kategorií,
  zařazení bez účetního profilu); otestovat jen čtením.
- `docs/ukoly/IM-test-report.md`: tabulka úkol → počet testů → výsledek, převzatá ze sekcí Výsledek.
- `README.md` v kořeni: nahradit zastaralý příkaz pro testy odkazem na `tools/run_tests.sh`.

**Mimo rozsah:** kód, pohledy, `CLAUDE.md`, deník rozhodnutí, otevřené body, `docs/architektura.md` (zapisuje hlavní relace).

**Commit:** `Dokumentace a test report evidence nástrojů`

## Výsledek

## Převzetí
