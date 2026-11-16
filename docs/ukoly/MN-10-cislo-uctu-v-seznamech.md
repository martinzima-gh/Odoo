# MN-10 Číslo účtu hlavní knihy všude před názvem

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (zobrazení účtu v celé aplikaci; účtování, role ani čísla účtů se nemění) |
| Výchozí větev | `ukol/MN-manual` (po MN-08) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | poznámka Martina 1 z průchodu 16. 11. 2026; rozhodnutí 2026-11-16 „Poznámky z průchodu 2“ bod 1 |

**Požadavek (Martin):** všude, kde se zobrazuje účet hlavní knihy (role účtů, náhled zaúčtování, profily, výběry účtu,
seznamy), ukázat před názvem číslo účtu: `321000 Dodavatelé`. Číslo v délce, jakou kniha používá (6 míst nebo jiná délka),
bez názvu fondu či společnosti.

**Zjištěno z kódu (Claude, neověřeno v prohlížeči):** Odoo 20 skládá `account.account.display_name` jako `kód název` jen tehdy,
když uživatel má skupinu `account.group_account_readonly` a pole `code` má pro **aktivní společnost** hodnotu
(`addons/account/models/account_account.py`, `_compute_display_name`). Kód účtu je v Odoo 20 závislý na společnosti
(`code_mapping_ids`); při pohledu na knihu fondu z jiné aktivní společnosti je prázdný a zobrazí se jen název.
Se `formatted_display_name` se místo názvu ukazuje `name_path`.

**Plán (od Clauda; provádějící model ověří a odchylky popíše):**

1. Diagnóza v `investra` (read-only): pro dvě místa (seznam rolí účtů knihy fondu, náhled zaúčtování obchodu) zjistit, proč
   je vidět jen název – chybějící skupina uživatele, nebo prázdný kód pro aktivní společnost. Výsledek zapsat.
2. Oprava v našem modulu (ne v jádru Odoo), nejníže v závislostech, např. `investra_entity`: rozšířit
   `_compute_display_name` účtu tak, aby při prázdném kódu pro aktivní společnost vzal kód účtu v jeho vlastní společnosti
   (`with_company(account.company_ids[:1])`); formát `kód název`, bez názvu společnosti. Na podmínku skupiny
   `group_account_readonly` nesahat bez Martinova souhlasu – pokud je příčinou ona, zastavit a napsat.
3. Projít vlastní moduly, kde se účet skládá ručně nebo přes `name` (`grep -rn "account_id.name\|account.name"`), a sjednotit
   na `display_name`. Vyhledávání účtu podle čísla i názvu ve výběrech musí dál fungovat.
4. Testy: účet knihy fondu má `display_name` „kód název“ i při jiné aktivní společnosti; náhled zaúčtování ukazuje číslo.
   Celá sada `all`.
5. Nasazení: povýšení dotčených modulů v `investra` se zálohou, restart 8071. Manuál – jen pokud někde popisuje účet bez čísla.

**Rozsah souborů:** model účtu ve zvoleném modulu, místa z bodu 3, jejich testy a verze, tento soubor, předávka.

**Mimo rozsah:** změna čísel účtů, osnovy, rolí; jádro Odoo.

**Kritéria přijetí:** testy `all` bez selhání na `investra_ci_*`; ve Výsledku příčina z bodu 1 a seznam upravených míst.

## Výsledek

(doplní provádějící model)
