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

(doplní provádějící model)
