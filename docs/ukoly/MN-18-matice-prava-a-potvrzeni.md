# MN-18 Matice: výchozí řádky a rozdělení potvrzení

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (`investra_fund/security/`, data) – plán doplní Claude před zadáním |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | nálezy MN-13 č. 5 a 8 |

**Rozhodnutí Martina 17. 11. 2026** (po variantách Clauda): nález 5 = varianta B, nález 8 = varianta A i B. Zapsáno v `docs/rozhodnuti.md`.

**Cíl a postup (část 1, nález 5, varianta B – Python, oranžová zóna):**
1. V `investra_fund/models/approval_matrix.py` (`write`, `unlink`; případně v `_check_editable`) pro řádky s `builtin = True` hlásit
   samostatnou chybu: „Výchozí řádek z modulu nejde měnit ani smazat; zadejte nový řádek s pozdějším „Platí od“.“ Chování pro
   ostatní řádky a pro `sudo` se **nemění**; existující hlášení pro platné vlastní řádky zůstává.
2. Testy v `investra_fund/tests/`: schvalovatel nezmění ani nesmaže `builtin` řádek (nová chyba, ne obecná); vlastní řádek s pozdějším
   „Platí od“ jde založit; vlastní platný řádek dál hlásí původní chybu; `sudo` beze změny.
3. **Nepřidávat** zákaz zeslabení (varianta C zamítnuta jako zásah do řízení kontrol).

**Cíl a postup (část 2, nález 8, varianta A i B):**
4. Manuál `docs/manual/04-oceneni-a-matice.md`: tabulka „Kde se činnost potvrzuje“ (na záznamu: schválení ocenění, schválení ceny,
   výjimka z uzamčení, zveřejnění; v Žádostech ke schválení: ostatní činnosti z `ACTIVITIES`) – ověřit proti kódu `_gate` a
   `investra_nav/models/valuation.py`; věta, že řádek obhospodařovatele může pravidlo i zeslabit a odpovídá za to schvalovatel.
5. Varianta B: na formuláři záznamu, u kterého čeká žádost (`investra.approval.request`, stav `pending`, shoda `res_model` + `res_id`),
   zobrazit upozornění „Čeká na potvrzení v Žádostech ke schválení“ s odkazem na žádost. Nejdřív **inventura**: seznam modelů,
   které volají `_gate` s `record`, a jejich formulářů. Pro jednotné řešení použít malý abstraktní mixin (výpočetní pole
   `pending_request_id`, `search` podle `res_model`/`res_id`, bez uložení) a jednu sdílenou část pohledu. **Zastavit a napsat návrh**, pokud
   formulářů je víc než 6 nebo je nutné měnit stavy či účtování.

**Smí:** `investra_fund` (model matice, mixin, testy, views), formuláře ostatních modulů jen přidáním upozornění (bez změny logiky),
manuál kap. 4, tento soubor. **Nesmí:** práva (`ir.access.csv`), stavový automat ocenění, účtování, NAV, migrace; nic nenasazovat.

**Kritéria přijetí:** testy `investra_fund` a modulů s upraveným formulářem bez selhání (`tools/run_tests.sh`, jen Claude); ve Výsledku
seznam změněných míst, inventura formulářů a co se neověřilo v prohlížeči. Nasazení udělá hlavní relace se zálohou.

## Výsledek

Doplní provádějící agent.

## Převzetí

Doplní Claude.
