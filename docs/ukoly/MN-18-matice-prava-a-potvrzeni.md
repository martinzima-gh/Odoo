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

Provedl Claude (Sonnet 5.5) 17. 11. 2026 na `ukol/MN-manual`; nic nenasazeno, pracovní DB `investra` nedotčena.

**Změněná místa**
- `investra_fund/models/approval_matrix.py`: `_check_editable` hlásí pro `builtin` řádky vlastní chybu (write, unlink i kroky řádku); `sudo` a ostatní řádky beze změny.
- Nový `investra_fund/models/approval_pending.py` (abstraktní mixin `investra.approval.pending.mixin`: nestored `pending_request_id`, `action_open_pending_request`); import v `models/__init__.py`.
- Mixin přidán do `_inherit`: `investra.valuation`, `investra.class.movement`, `investra.instrument.repayment`, `investra.trade` (v `trade_reverse.py` nutné i `_name`), `investra.derivative`, `investra.portfolio.classification`.
- Upozornění (stejný blok XML) v šesti formulářích: `nav_views.xml` (ocenění, pohyb, splátka), `trade_views.xml` (obchod, přes dědění pohledu), `derivative_views.xml`, `instrument_views.xml` (zařazení portfolia).
- Testy v `investra_nav/tests/test_approval_matrix.py` (5 nových: hláška builtin, sudo, nový řádek, původní hláška vlastního platného řádku, upozornění na záznamu); manuál kap. 4 (tabulka „Kde se činnost potvrzuje“, věta o zeslabení, nález 5).

**Inventura formulářů** (modely volající `_gate` s `record`): 6 – ocenění, pohyb třídy, splátka nástroje, obchod, smlouva derivátu, zařazení portfolia. Limit 6 nepřekročen, stavy ani účtování se nemění. `manual_rate` volá `_gate` bez záznamu (`res_id` 0), pruh nemá kde zobrazit. Schválení ceny a výjimka z uzamčení `_gate` nevolají (`_approve_step`, potvrzení na záznamu).

**Odchylka od zadání:** zadání řadí zveřejnění mezi činnosti potvrzované na záznamu; kód (`action_publish` → `_gate`) a test ukazují Žádosti ke schválení. V manuálu uvedeno podle kódu.

**Testy:** `tools/run_tests.sh investra_fund,investra_nav,investra_instruments,investra_derivative` – 512 testů, 0 failed, 0 error. (První dva běhy selhaly při načtení pohledů: pole mixinu v pohledu nad modelem bez mixinu, a chybějící `_name` při seznamu `_inherit`; opraveno.)

**Neověřeno:** vzhled pruhu a funkce odkazu v prohlížeči (jen validace pohledů při instalaci a test metod); texty hlášení v angličtině/překladech.

## Převzetí

Doplní Claude.
