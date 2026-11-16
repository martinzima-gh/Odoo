# CP-MN14 Nezávislá revize MN-14 (kalendář ocenění)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | revize (jen čtení) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | žádná; Copilot nic neupravuje, jen zapíše nálezy do tohoto souboru |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-14 (commity 968b312 až a90cc29), pokyn Martina 16. 11. 2026 |

**Cíl:** nezávisle ověřit, že MN-14 dělá, co zadání říká, a nic navíc. Šetří revizi Clauda; Claude pak jen prověří nálezy.

**Co zkontrolovat** (`git diff 1b835de..a90cc29`, zadání v `docs/ukoly/MN-14-vypusteni-kalendare-oceneni.md`):
1. `investra_fund/models/schedule.py` (`next_valuation_date`): pravidla dnů podle frekvence (konec období, pátek, pracovní den bez svátků),
   hraniční případy (přelom měsíce a roku, přestupný rok, poslední ocenění v budoucnosti, žádné ocenění → Datum vzniku, prázdná frekvence).
2. `investra_dashboard/models/dashboard.py`: nezbyl žádný odkaz na kalendář, `dashboard_next_late` ani „Ocenění po termínu“
   (grep v celém `addons/` včetně views, `data/`, `static/`, i18n, `tools/`, `docs/manual/`).
3. `migrations/20.0.0.9.0/pre-migration.py`: maže jen prázdnou tabulku, jinak zastaví; nic jiného nemění.
4. `security/ir.access.csv`: odstraněny právě 3 řádky kalendáře, nic dalšího.
5. Testy: pokrývají hraniční případy z bodu 1? Co chybí? (Testy Odoo nespouštěj; čistý Python smíš.)
6. Manuál kap. 2–4: odpovídá chování kódu (názvy polí, nabídek, výchozí hodnoty).

**Mimo rozsah:** žádné úpravy souborů mimo tento záznam; nic nepřepisovat; neřešit styl, jen skutečné chyby (u každého nálezu soubor, řádek, scénář).

**Kritéria přijetí:** zápis do Výsledku: u každého z 6 bodů „v pořádku“ nebo nález s důkazem; seznam „neověřeno“.

## Výsledek

Doplní Copilot (změněné soubory: jen tento; nálezy; neověřeno).

## Převzetí

Doplní Claude.
