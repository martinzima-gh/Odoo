# ST-01 Převzetí IM a sloučení do `main`

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zakázané soubory a `main` – provádí jen Claude (Sonnet) se souhlasem Martina v promptu |
| Výchozí větev | `feature/instrument-master` |
| Větev úkolu | žádná nová; pracuje se ve `feature/instrument-master` |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/plan-dalsiho-vyvoje.md` (Etapa 0), rozhodnutí „Jedna verze aplikace“ 2026-11-15 |

**Cíl:** `main` obsahuje celý dnešní stav aplikace (evidence nástrojů, pracovní databáze `investra`), aby další etapy
začínaly větví z `main`. Kód se nemění.

**Výchozí stav (ověřeno čtením 15. 11. 2026, před prací ověř znovu):**

- `origin/main` (commit `6e0fcd1` ze 7. 11.) → `feature/nav-prototyp` +320 commitů → `feature/instrument-master` +31;
  žádná větev nemá nic navíc, sloučení je tedy prosté posunutí ukazatele (fast-forward), bez slučovacího commitu.
- Místní větev `main` neexistuje. Místní i vzdálené `feature/*` jsou shodné, pracovní strom čistý.
- Sekce Převzetí chybí v IM-11, IM-12, IM-13 (IM-01 až IM-10 ji mají).
- Běží jen `investra-web` (8071) nad připojenou složkou `addons/custom`.

**Postup:**

1. `git status`, `git fetch origin`, zopakovat kontrolu `git rev-list --left-right --count` pro tři dvojice výše.
   Kdyby levá strana nebyla 0 nebo strom nebyl čistý, zastavit se a napsat Martinovi.
2. `tools/run_tests.sh all` (dočasná `investra_ci_*`, sama se smaže). Očekávání 677 testů, 0 selhání, 0 chyb;
   jiný výsledek = zastavit, neslučovat.
3. Doplnit sekci Převzetí v IM-11, IM-12, IM-13 (datum, commit, výsledek testů, nálezy – z jejich sekce Výsledek
   a z `docs/predavky/2026-11-15-im13-hotovo.md`) a jeden řádek stavu v `IM-00-prehled.md`.
4. Deník `docs/rozhodnuti.md` (sloučení do `main`, datum, důvod), předávka `docs/predavky/2026-11-15-st01-main.md`.
   Commit a `git push origin feature/instrument-master:feature/instrument-master`.
5. Sloučení **bez přepínání větví** (přepnutí na starší větev by změnilo soubory pod běžící instancí 8071):
   `git push origin feature/instrument-master:feature/nav-prototyp`, pak `git push origin feature/instrument-master:main`
   (obyčejný push bez `--force` projde jen jako fast-forward). Místně `git fetch origin`,
   `git fetch . feature/instrument-master:feature/nav-prototyp`, `git branch main origin/main`.
6. Ověřit: `origin/main`, `origin/feature/nav-prototyp` a `feature/instrument-master` ukazují na stejný commit;
   `curl` na http://127.0.0.1:8071/web/login vrací 200.

**Rozsah souborů:** `docs/ukoly/IM-00`, `IM-11`, `IM-12`, `IM-13` (jen Převzetí a stav), tento soubor (Výsledek),
`docs/rozhodnuti.md`, `docs/predavky/`. Nic jiného.

**Mimo rozsah:** kód modulů, databáze, kontejnery, `--force`, mazání větví, větve `kontrola/*`, klon `~/odoo-review`,
GitHub Actions (ST-02), pravidla agentů (ST-04).

**Kritéria přijetí:**

- testy 677/0/0 před sloučením (číslo z výstupu skriptu, ne odhad),
- tři větve na stejném commitu, `git status` čistý,
- odmítne-li GitHub push do `main` (ochrana větve), nic neobcházet: zastavit se a navrhnout pull request,
- ve Výsledku návrh, které větve smazat (kandidáti: `feature/investra-skeleton` shodná s původním `main`,
  `feature/nav-prototyp`, `feature/instrument-master`, zastaralé `review/ag/*`) – jen návrh, mazání po Martinově souhlasu,
- zpráva Martinovi: co šlo ven (větve, commity) a z které větve se zakládá `etapa/derivaty`.

**Návrat:** `main` byl před sloučením na `6e0fcd1`; vrácení by znamenalo přepis historie, tedy jen na Martinův pokyn.

## Výsledek

Doplní provádějící relace.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Návrh větví ke smazání:**
