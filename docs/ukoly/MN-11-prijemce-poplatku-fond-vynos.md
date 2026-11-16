# MN-11 Příjemce poplatku „Fond – výnos“

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen popisek a nápověda; hodnota `fund` a účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` (po MN-10) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | poznámka Martina 2 z průchodu 16. 11. 2026; rozhodnutí 2026-11-16 „Poznámky z průchodu 2“ bod 2 |

**Požadavek (Martin):** příjemce vstupního i výstupního poplatku „Fond“ jde do výsledovky, proto se má jmenovat „Fond – výnos“.

**Zjištěno z kódu:** `FEE_RECIPIENT` v `investra_fund/models/fund.py` má hodnotu `("fund", "Fond")`; podle nápovědy jde o výnos
celého fondu dělený mezi třídy poměrem (role `entry/exit_fee_income`). Kapitálová varianta je jen u třídy („Třída – kapitál“),
na úrovni fondu žádná není, takže stačí změnit popisek.

**Plán:**

1. Popisek `fund` → „Fond – výnos“ v `FEE_RECIPIENT` (platí pro fond, třídu i pohyb třídy, vstupní i výstupní poplatek).
2. Nápovědy polí příjemce: „Fond – výnos: výnos celého fondu, dělí se mezi třídy poměrem.“ (zbytek textu beze změny).
3. Najít a upravit texty, které popisek „Fond“ citují (testy, manuál `docs/manual/02-fond.md` a `03-tridy.md`, nápovědy).
4. Testy dotčených modulů, pak `all`. Povýšení `investra_fund` (a modulů s upravenými texty) v `investra` se zálohou, restart 8071.

**Mimo rozsah:** nová kapitálová varianta pro fond; účty rolí poplatků (otevřený bod „Účty poplatků za úpis a odkup“).

**Kritéria přijetí:** v `investra` se v rozbalovacím seznamu příjemce ukazuje „Fond – výnos“; uložené hodnoty se nemění
(SELECT počtu `fund` před a po stejný); testy `all` bez selhání.

## Výsledek

Hotovo 16. 11. 2026 (Sonnet), větev `ukol/MN-manual`.

- `investra_fund/models/fund.py`: popisek `fund` → „Fond – výnos“ v `FEE_RECIPIENT`; nápovědy výchozích příjemců
  „Fond – výnos: výnos celého fondu, dělí se mezi třídy poměrem.“ Hodnota `fund` a účtování beze změny.
- `docs/manual/02-fond.md`: tabulka příjemců a věta o kapitálu. `03-tridy.md` popisek „Fond“ necituje.
- Jiné texty citující popisek (testy, nápovědy v `investra_nav`) nenalezeny; pole pohybu a třídy berou popisek ze stejného `FEE_RECIPIENT`.
- Verzi modulu jsem nezvyšoval (kvůli střetu s MN-10 a MN-12); povýšení `investra_fund` a restart 8071 udělá hlavní relace najednou.
- Testy `tools/run_tests.sh all`: 796 testů, 0 failed, 0 error; dočasná `investra_ci_20261116_164352` smazána.
- Neověřeno: zobrazení v rozbalovacím seznamu v `investra` (nasazení neprováděno) a SELECT počtu `fund` před/po (do `investra` jsem nesahal; změna popisku hodnoty neovlivňuje).

- **Nasazení (hlavní relace, 16. 11. 2026, společně MN-10 až MN-12):** záloha `zalohy/investra-2026-11-16-pred-MN10-12.dump` (pg_dump -Fc, 8,7 MB, `pg_restore -l` 10 953 položek); testy `all` 801/0 selhání (`investra_ci_20261116_172931`, smazána); `-u investra_entity,investra_fund,investra_nav --stop-after-init` v `investra` bez chyby (v logu jen docutils k popisu modulů); verze entity 20.0.0.12.2, fund 20.0.0.8.5, nav 20.0.0.31.3; 8071 restartována (HTTP 200). Ověřit v prohlížeči: Martin.
