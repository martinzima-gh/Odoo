# MN-04 Odchylka mapování rolí od standardu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (zobrazení a pomocná funkce; dohledání účtu při účtování `account_for` se nemění) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | rozhodnutí Martina 16. 11. 2026 „Mapování rolí – kopie se značkou odchylky (varianta A)“ v `docs/rozhodnuti.md` |

**Stav:** mapování role → účet je jen v knize (`investra.role.account`, `investra_entity/models/account_role.py`).
Standard je v kódu: `ROLE_ACCOUNTS` v `investra_chart_fund/models/template_investra_fund.py` (role → xmlid účtu šablony).
Při založení knihy fondu se zkopíruje (`_map_fund_roles`), při povýšení modulu se doplní jen chybějící role.
Z aplikace nejde poznat, který fond se od standardu odchyluje.

**Cíl:** v Účtech rolí je u každého řádku vidět, zda se fond odchyluje od standardu, a jde podle toho filtrovat.
Budoucí změnu standardu převede migrace jen u fondů bez odchylky.

**Plán (od Clauda):**

1. V `investra_chart_fund` rozšířit `investra.role.account` o nestorované počítané pole „Standard“ s hodnotami
   Podle standardu / Odchylka / Bez standardu (kniha není ze šablony `investra_fund` nebo role není v `ROLE_ACCOUNTS`)
   a o pole „Standardní účet“ (účet šablony v této knize). Porovnává se jen hlavní účet; Další účty (banky, platby
   na cestě) jsou z povahy věci fondové a odchylkou nejsou. Kvůli filtru doplnit metodu `_search`.
2. Seznam a vyhledávání Účty rolí: sloupce Standard a Standardní účet, filtr „Odchylka od standardu“, seskupení podle
   Standardu. Řádek s odchylkou zvýraznit (`decoration-warning`).
3. Pomocná metoda pro budoucí migrace: `_apply_standard_role(code)` – u všech knih fondů nastaví hlavní účet role
   podle šablony jen tam, kde je dnes Podle standardu nebo role chybí; řádky s odchylkou nemění a vrátí jejich seznam
   (pro výpis v logu migrace). Teď ji nic nevolá; v README modulu krátce popsat, jak ji použít při změně `ROLE_ACCOUNTS`.
4. Testy: nová kniha fondu má všechny role Podle standardu; ruční změna účtu → Odchylka a filtr ji najde; kniha
   investiční společnosti → Bez standardu; `_apply_standard_role` po změně standardu převede knihu bez odchylky
   a knihu s odchylkou nechá a vrátí.
5. Manuál: do `docs/manual/01-spolecnost-a-kniha.md` krátký oddíl „Role účtů a odchylky“ (kde je vidět, kdy výjimku
   použít, že vlastní analytiku je nutné napojit na roli a zařadit do převodové tabulky ČNB).
6. Povýšení `investra_chart_fund` v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071; SELECTem
   ve Výsledku uvést počet řádků s odchylkou v `investra` (čekáme 0).

**Rozsah souborů:** `addons/custom/investra_chart_fund/` (models, views, tests, verze, README), `docs/manual/01-spolecnost-a-kniha.md`,
tento soubor (Výsledek), předávka. `investra_entity` (model, `account_for`) neměnit.

**Mimo rozsah:** obecná vrstva mapování s výjimkami (varianta B, zamítnuta), změna `ROLE_ACCOUNTS`, osnova.

**Kritéria přijetí:** testy `investra_chart_fund` projdou na `investra_ci_*`; v `investra` jsou sloupce a filtr;
Výsledek uvádí, co zůstalo neověřené v prohlížeči.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
