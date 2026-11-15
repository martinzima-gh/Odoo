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

Hotovo 15. 11. 2026 (Claude Code), větev `feature/instrument-master`. Kód ani pohledy beze změny.

**Změněné soubory:** nové `addons/custom/investra_instrument_master/README.md`, `docs/sql/23-evidence-nastroju.sql`,
`docs/ukoly/IM-test-report.md`; upraven `README.md` v kořeni (příkaz pro testy nahrazen odkazem na `tools/run_tests.sh`).

**Ověření SELECTů:** addon není nainstalovaný v `investra_test`, `investra_dev` ani `investra_vzhled`, proto jsem ho nainstalovala
do dočasné `investra_ci_master` (bez demo dat) a všech 9 dotazů pustila v read-only režimu: žádná chyba, všechny jen s prázdným
výsledkem kromě počtů číselníků (BA0088 84, ESA 80, kategorie 4, důvody 6; ručně změněných 0). Dočasná DB je smazána, filestore
po ní nezůstal. Testy Odoo se nespouštěly.

**Neověřeno:** správnost výsledků na datech (v DB nebyli emitenti, nástroje ani portfolia); dotaz 7 (zařazení bez účetního profilu)
napodobuje výběr profilu v SQL, protože `profile_state` není uložené pole; vzhled a obsah README bez prohlížení v aplikaci.
Test report čísla jen přebírá ze sekcí Výsledek.

**Odchylky:**
- Soubor SQL se jmenuje `23-…`, ne `12-…` ze zadání: číslo 12 už má `12-ucetni-udalosti.sql`.
- Doplněno 15. 11. 2026 po dokončení IM-02: README (verze 20.0.0.6.0, postup importu) a test report (79 testů) aktualizovány;
  původní verze uváděla průvodce jako nehotový.
- Test report nemá širší sadu všech modulů po IM-07 a IM-02 (poslední byla po IM-06).

## Převzetí
