# MN-17 Matice: odlišit řádky z modulu a záložka Zpřísnění matice

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `addons/custom/investra_fund/views/*.xml`) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | bez větve; zápis do `~/odoo-review`, bez commitu |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | nálezy MN-13 č. 6 a 7 |

**Cíl:** (6) v seznamu a formuláři řádků schvalovací matice je poznat, který řádek je výchozí z modulu a který vlastní; (7) záložka fondu „Zpřísnění matice“ je z pohledu uživatele srozumitelná (popisek, co ukazuje a kde se zpřísnění zadává).

**Smí:** jen pohledy XML v `investra_fund/views/`; pole `builtin` už existuje (nové pole se nezakládá, Python se nemění). Např. sloupec/štítek „Výchozí (modul)“ v seznamu, `readonly` ve formuláři, nápověda. Když to bez nového pole nejde, zastavit a napsat návrh.

**Mimo rozsah:** práva (`security/`) a změna toho, kdo řádky smí měnit (to je MN-18); logika matice.

**Kritéria přijetí:** `tools/view_check` projde; popis změn s názvy polí; v prohlížeči (8072) ověřeno, co šlo, zbytek označen „neověřeno“.

## Výsledek

Doplní provádějící agent.

## Převzetí

Doplní Claude.
