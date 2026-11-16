# MN-14 Vypuštění kalendáře ocenění; další ocenění a zpoždění z frekvence

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (Přehled fondů, formulář fondu, odstranění modelu a prázdné tabulky; ocenění, NAV a účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` (po MN-13) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-13 (nálezy 1–4); rozhodnutí 2026-11-16 „Kalendář ocenění se vypouští (MN-14)“; souhlas Martina 16. 11. 2026 s odstraněním modelu a tabulky |

**Stav:** model `investra.valuation.calendar` (`investra_fund/models/fund.py`, pole `calendar_ids`, záložka ve formuláři fondu,
práva v `security/ir.access.csv`) čte jen Přehled fondů (`investra_dashboard/models/dashboard.py`: `_dashboard_next`,
`_dashboard_values`, `_dashboard_exceptions`, pole `dashboard_next_late` a jeho `_search_…`). Ocenění, období ani účtování
kalendář nepoužívají. V `investra` je tabulka prázdná (SELECT 16. 11. 2026: 0 řádků).

**Cíl (rozhodnutí Martina):** kalendář vypustit. Přehled fondů počítá další ocenění a zpoždění z údajů fondu.

**Plán (od Clauda; provádějící model ověří a odchylky popíše):**

1. **Nový parametr fondu** `publication_lag_days` (Integer, „Lhůta zveřejnění (pracovní dny)“, výchozí 0 = zveřejnit
   v den ocenění; nápověda: počet pracovních dnů od data ocenění do zveřejnění podle statutu) v `investra_fund`,
   ve formuláři u Frekvence ocenění.
2. **Očekávané datum dalšího ocenění** (čistá funkce, testovatelná bez databáze, např. `investra_fund/models/schedule.py`):
   z data posledního zaúčtovaného ocenění, u prvního z Data vzniku (`launch_date`, `investra_nav`), a frekvence:
   měsíčně / čtvrtletně / ročně = poslední den následujícího kalendářního období; týdně = nejbližší další pátek;
   denně = nejbližší další pracovní den. Pracovní den = pondělí až pátek; státní svátky se zatím neberou (zapsat
   do nápovědy a Výsledku). Bez data vzniku a bez ocenění: bez očekávaného data, Přehled to ukáže jako dnes
   „Nezaloženo“ bez termínu. *Pravidla dnů jsou návrh Clauda; jinou volbu ze statutu řeší pozdější úkol.*
3. **Termín zveřejnění** = očekávané datum + `publication_lag_days` pracovních dnů. **Po termínu** = termín < dnes a k očekávanému
   datu není zveřejněné ocenění. Upozornění „Ocenění po termínu“ (dnes počet zmeškaných řádků kalendáře) hlásí jedno
   zmeškané ocenění; pokud jich je víc za sebou (např. tři měsíce bez ocenění), uvést počet zmeškaných období.
4. **Přehled fondů:** `_dashboard_next`, `_dashboard_values`, `_dashboard_exceptions`, `dashboard_next_late` a filtr přepsat
   na body 2–3; rozpracované nebo mimořádné ocenění s dřívějším datem má dál přednost (jako dnes). Texty karty beze změny,
   kde to jde.
5. **Odstranění kalendáře:** model, pole `calendar_ids`, záložka, práva, pravidlo společnosti. Tabulku
   `investra_valuation_calendar` odstraní Odoo při povýšení modulu (zánik `ir.model`); ověřit na dočasné kopii `investra`
   ze zálohy, jinak `pre-migrate` s `DROP TABLE IF EXISTS` a novou verzí. Před povýšením SELECTem ověřit, že tabulka
   je v `investra` dál prázdná; jinak zastavit a napsat Martinovi.
6. **Nástroje a testy:** `tools/nav_demo/demo_prehled.py` (kalendář nahradit Datem vzniku / frekvencí / lhůtou), testy
   `investra_dashboard/tests/test_dashboard.py` přepsat; nové testy čisté funkce (všech pět frekvencí, přelom roku,
   pátek a víkend, lhůta přes víkend) a Přehledu (po termínu, včas, víc zmeškaných období, mimořádné ocenění, fond bez data
   vzniku). Celá sada `all`.
7. **Manuál:** `docs/manual/04-kalendar-a-matice.md` přejmenovat na `04-oceneni-a-matice.md` (README: odkaz a téma
   „frekvence ocenění, lhůta zveřejnění a schvalovací matice“), oddíl Kalendář nahradit popisem bodů 1–3; v kap. 2 a 3
   odstranit zmínky o kalendáři.
8. **Nasazení neprovádět** – povýšení `investra_fund`, `investra_dashboard` (a `investra_nav`, pokud se mění) a restart udělá
   hlavní relace se zálohou.

**Rozsah souborů:** `investra_fund` (model, views, práva, verze, případně migrace), `investra_dashboard` (model, view, testy,
verze), `tools/nav_demo/demo_prehled.py`, manuál kap. 2–4 a README, tento soubor, předávka.

**Mimo rozsah:** kontrola intervalu proti statutu a zákonné lhůtě (deník 2026-11-04 „Interval ocenění“), státní svátky,
nepravidelné dny ocenění ze statutu, schvalovací matice (nálezy MN-13 5–9 řeší jiný úkol).

**Kritéria přijetí:** testy `all` bez selhání na `investra_ci_*`; povýšení ověřené na kopii `investra` (tabulka zmizí, Přehled
se otevře); ve Výsledku seznam změněných míst a odchylek.

## Výsledek

(doplní provádějící model)
