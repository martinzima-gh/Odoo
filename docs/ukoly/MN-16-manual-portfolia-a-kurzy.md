# MN-16 Manuál kap. 6 a 7: portfolia a nástroje, kurzy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `docs/manual/`) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | bez větve; zápis do `~/odoo-review`, bez commitu |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-15 (stejný formát), osnova `docs/manual/README.md` (kap. 6 a 7) |

**Cíl:** `docs/manual/06-portfolia-a-nastroje.md` (portfolio fondu, instrumenty, vazba na kmenová data) a `docs/manual/07-kurzy.md` (zdroje kurzů, ruční kurz, chování „Neimplementováno“ podle rozhodnutí MN-08 v deníku).

**Zdroje (číst cíleně):** `investra_instruments`, `investra_instrument_master`, `investra_rates` (models, views, security), `docs/rozhodnuti.md` (hesla kurzy, zdroj kurzů, MN-08), seed `tools/demo_data/seed.py`.

**Formát a pravidla:** stejné jako MN-15. Kap. 7 nesmí slibovat zdroje, které nejsou implementované.

**Rozsah souborů:** dva soubory kapitol, dva řádky v `docs/manual/README.md`, sekce Výsledek. Kód neměnit.

**Kritéria přijetí:** každé pole formulářů instrumentu a kurzu popsané nebo vynechané s důvodem; nálezy ve Výsledku.

## Výsledek

Doplní provádějící agent.

## Převzetí

Doplní Claude.
