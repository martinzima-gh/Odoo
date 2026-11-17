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

### Nezávislá revize Copilot (17. 11. 2026)

**Rozsah:** v historii je `a90cc29` před implementačním commitem `968b312`; zadaný diff `1b835de..a90cc29` tedy implementaci neobsahuje. Revidoval jsem skutečné změny `1b835de..968b312` a ověřil, že po nich v relevantním kódu další změny nejsou.

1. **V pořádku.** `schedule.py` počítá všech pět frekvencí podle plánu, včetně striktně pozdějšího pátku/pracovního dne a konců měsíce, čtvrtletí a roku. Přehled bere poslední zaúčtované ocenění, jinak Datum vzniku, a dřívější draft má přednost před očekávaným datem. Přestupný rok, přelomy, víkend a datum budoucího zaúčtovaného ocenění jsou pokryty testy.
2. **DOPORUČENÍ — LOW (doslovné grep kritérium).** V běžném modelu, pohledech a právech nezůstává aktivní kalendář ocenění ani pole `dashboard_next_late`; starý model/tabulka jsou odkazovány jen migračním skriptem. Doslovné hledání ale stále najde popisné/regresní zmínky: `tools/nav_demo/demo_prehled.py:68`, `addons/custom/investra_dashboard/tests/test_dashboard.py:47,53` a `docs/manual/04-oceneni-a-matice.md:10,31`. Nejde o aktivní funkčnost, ale přijetí „žádný odkaz“ není doslova splněno; upřesnit kritérium tak, aby povolovalo migraci, test nepřítomnosti pole a vysvětlující manuál, případně tyto zmínky odstranit.
3. **V pořádku.** `pre-migration.py` ověří existenci tabulky, spočítá řádky, při neprázdné tabulce skončí chybou a odstraní pouze prázdnou tabulku. Žádné jiné SQL změny ani mazání dat.
4. **V pořádku.** Diff odstranil právě tři přístupová pravidla kalendáře; ostatní řádky `security/ir.access.csv` beze změny.
5. **DOPORUČENÍ — LOW (chybějící hrana testů).** Testy pokrývají všech pět frekvencí, přestupný rok, přelomy, pracovní dny/víkendy, chybějící datum, budoucí poslední ocenění i scénáře dashboardu. Samostatný případ platného data s prázdnou frekvencí ale chybí (nyní je pokryt jen neznámý řetězec); funkce přitom prázdnou frekvenci bezpečně vrátí jako `False`. Osm odpovídajících čistých kontrol funkce proběhlo úspěšně; Odoo testy jsem nespouštěl.
6. **V pořádku.** Kapitoly 2–4 odpovídají kódu: názvy Datum vzniku a Frekvence ocenění, cesta do formuláře, výchozí Měsíčně, pravidla výpočtu i nehlídaná lhůta. Datum vzniku nemá výchozí hodnotu a bez něj se očekávané datum neukáže.

**Neověřeno:** nezávislé spuštění Odoo testů `all` a opakování povýšení/databázové kontroly; předchozí výsledek zaznamenává jejich provedení hlavní relací, zde jsem ověřil zdrojový kód. Prohlížeč jsem neověřoval.

**Shrnutí:** Žádné zásadní nálezy. Dvě drobná doporučení výše.

## Převzetí

Claude 17. 11. 2026: převzato jako zápis revize. Bez zásadních nálezů; dvě LOW doporučení (grep kritérium MN-14 – povolit migraci, test nepřítomnosti a manuál; chybí test platného data s prázdnou frekvencí) druhé zapracováno 17. 11. 2026 (test prázdné frekvence v `test_schedule.py`, `investra_fund` 22 testů OK); první čeká na rozhodnutí.
