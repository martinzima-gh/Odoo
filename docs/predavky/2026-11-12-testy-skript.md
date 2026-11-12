# Předávka 2026-11-12: skript na testy Odoo, role Copilota

**Cíl:** šetřit kredity při testech; vyjasnit, zda testy může dělat Copilot.

**Stav:** větev `feature/nav-prototyp`; commity `54c91c7` (skript), `dd191b5` (CLAUDE.md) a commit s touto předávkou.

**Hotovo:**
- `tools/run_tests.sh <modul[,modul]>`: pevně `investra_test`, log v `.test-logs/` (mimo git), na výstup souhrn a chyby;
  OK jen při >0 testech a bez ERROR v logu. Volitelně `TEST_TAGS`, `MAX_LINES`.
- Pojistka: rozdíl verzí modulu kód × `investra_test` → konec s kódem 3 (`ALLOW_UPGRADE=1` jen po dohodě a se zálohou).
  Důvod: běh `investra_instruments` v 8:56 aktualizoval i `investra_nav` 0.9.0 během práce jiné relace (`-u` bere závislé moduly).
- Ověřeno: čistý běh OK, 0 testů = NEÚSPĚCH, chyba v logu = NEÚSPĚCH, rozdíl verzí = zastaveno (simulace v pomocné složce).
- Copilot testy Odoo nespouští (CLAUDE.md, `.github/copilot-instructions.md`). Pravidlo testů v CLAUDE.md (Prostředí).
- Deník rozhodnutí, Claude Doc rev 311 a export `docs/architektura.md`.

**Výsledek testů 12. 11.** (`investra_nav,investra_fund,investra_instruments` nad `investra_test`): 293 testů, 4 failed + 4 errors,
vše v `test_approval_matrix` a `test_workflow` – známá kolize s řádky matice platnými od 12. 11. (řádek 81)
a 13. 11. (řádek 83), viz deník 2026-11-12 „oprava schvalovací matice“. Ostatních 285 prošlo. Od 14. 11. má projít.

**Zbývá – první krok:** 14. 11. spustit `tools/run_tests.sh investra_nav,investra_fund` a ověřit, že matice prošla.
Návrh na později (zeptat se Martina): testy matice nezávislé na datech v DB, nebo volba skriptu pro čistou
databázi `investra_ci_*` (založení a smazání DB vyžaduje souhlas).

**Otevřené otázky:** žádné nové.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `tools/run_tests.sh`
4. `docs/predavky/2026-11-12-splatky-storno.md` (navazující práce: zkouška storna splátky v UI)
