# MN-08 Zdroj kurzů „Neimplementováno“ pro funkční měnu mimo CZK a EUR

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (kurzy a přepočet; zastavení výpočtu bez kurzu) |
| Výchozí větev | `ukol/MN-manual` (po MN-07) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-16 „Poznámky ze zakládání fondu“ bod 5a a 5b; poznámka Martina 5 |

**Stav:** `investra.entity.rate_source` je ČNB nebo ECB; `RATE_SOURCE_BY_CURRENCY` (`investra_entity/models/entity.py`) vynucuje
CZK → ČNB a EUR → ECB, jiná funkční měna (např. USD) dostane ČNB bez kontroly. `rate_source` čtou `investra_rates`, `investra_fx_revaluation`
(`fx_profile.py`), `investra_nav` (`movement.py`, `valuation.py`) a průvodce knihy.

**Cíl (rozhodnutí Martina):** funkční měna mimo CZK a EUR je povolená, ale zdroj kurzů je „Neimplementováno“; import kurzů
jiné centrální banky (FED) se nedělá. Kde je pro takovou knihu potřeba kurz, výpočet skončí srozumitelnou chybou a nepoužije
tiše kurz ČNB.

**Plán (od Clauda; Opus ověří a odchylky popíše):**

1. Nová hodnota `none` („Neimplementováno“) v `rate_source`; kontrola: CZK → ČNB, EUR → ECB, jiná měna → Neimplementováno.
   Průvodce a formulář knihy ji ukáží jen pro čtení s vysvětlením.
2. Projít všechna místa, která `rate_source` čtou nebo stahují kurzy; pro `none` zastavit chybou „Kniha <název> nemá zdroj
   kurzů pro funkční měnu <měna> (není implementováno).“ Ruční zadání kurzu (pokud ho Odoo nebo naše moduly umožňují)
   posoudit: doporučit, zda ho připustit, a rozhodnutí nechat Martinovi – do té doby jen chyba.
3. Bod 5b (výkazy ČNB vždy kurzem ČNB) se neprogramuje; ověřit jen, že nic v kódu dnes nepředpokládá opak, a nález uvést.
4. Testy: kniha v USD má zdroj Neimplementováno; přecenění, ocenění a pohyb třídy v cizí měně v takové knize skončí chybou;
   CZK a EUR beze změny (celá sada `all`).
5. Migrace není potřeba, pokud v `investra` žádná kniha mimo CZK a EUR není (ověřit SELECTem); jinak zastavit a napsat Martinovi.
6. Nasazení: povýšení dotčených modulů v `investra` se zálohou, restart 8071. Manuál `01-spolecnost-a-kniha.md` – funkční měna a kurzy.

**Rozsah souborů:** moduly, které čtou `rate_source` (výše), jejich testy a verze, manuál kap. 1, tento soubor, předávka.

**Mimo rozsah:** import kurzů dalších bank; přepočet výkazů ČNB (etapa CN).

**Kritéria přijetí:** plán schválený Martinem v promptu (červená zóna); testy `all` bez selhání na `investra_ci_*`; Výsledek
uvádí seznam míst, kde se kurz čte, a jak se pro `none` chovají.

## Výsledek

Provedl Claude (Opus 5.5, hlavní relace) 16. 11. 2026 podle plánu schváleného Martinem.

- **Změněné soubory:**
  - `investra_entity`: `models/entity.py` – hodnota `none` („Neimplementováno“), `rate_source_for()` (CZK → ČNB, EUR → ECB,
    jiná → Neimplementováno), `_require_rate_source()` s chybou „Kniha <název> nemá zdroj kurzů pro funkční měnu <měna>
    (není implementováno).“, výchozí hodnota, onchange a create podle měny společnosti (dřív pevně ČNB), přísná kontrola
    i pro jiné měny; `views/entity_views.xml` – zdroj jen pro čtení, vysvětlení, žluté upozornění u `none`; test.
  - `investra_rates`: `base_currency()` neznámý zdroj odmítne (dřív by spadl do EUR) – pojistka i pro `get_rate`/`convert`.
  - `investra_fx_revaluation`: profil má `none`, výchozí/onchange/create podle měny firmy, `_published_rate` pro `none` chyba;
    formulář zdroj jen pro čtení; testy. `test_fx_run` přepnut na firmu v CZK (testovací firma Odoo je v USD a dosud tiše
    počítala kurzem ČNB – přesně chování, které úkol ruší).
  - `investra_nav`: `fund._fx_at` (movement.py) přes `_require_rate_source`; kontrola pohybu třídy v cizí měně (i s ručním
    kurzem); `valuation._rate_source` přes `_require_rate_source`; `_manual_rates` pro `none` vrací prázdný seznam; profil
    přecenění fondu už nedostává záložní „cnb“; nový `tests/test_no_rate_source.py`.
  - `investra_chart_fund`: průvodce ukáže „Neimplementováno“ a upozornění (`rate_source_missing`); test.
  - Verze: entity 0.12.1, rates 0.3.1, fx_revaluation 0.3.3, nav 0.31.1, chart_fund 0.12.4. Manuál kap. 1 (oddíl
    „Funkční měna mimo CZK a EUR“), `docs/otevrene-body.md` (2 body), tento soubor, předávka.
- **Místa, kde se kurz čte, a chování pro `none`:**
  | Místo | Chování pro knihu bez zdroje |
  |---|---|
  | `investra.fund._fx_at` (pohyb třídy create/write, deriváty `posting.py`) | chyba, pokud měna ≠ funkční; ve funkční měně kurz 1 |
  | `investra.valuation._fx` (portfolio, banky, nevypořádané obchody, třídy, deriváty `valuation.py`) | chyba přes `_fx_at` |
  | `investra.valuation._rate_source` (zdroj na řádcích ocenění) | chyba (volá se jen u cizí měny) |
  | `investra.valuation._manual_rates` | prázdný seznam (kurz se nepoužil) |
  | `investra.class.movement._check_rate_source` | chyba u třídy v cizí měně i s ručně zadaným kurzem |
  | `investra.fx.run._published_rate` (přecenění) | chyba |
  | `investra.rate.base_currency/get_rate/convert` | chyba „Zdroj kurzů none není implementován.“ (pojistka) |
  | `investra.rate._publish`, `_rate_funds`, `_check_change_allowed` (hledají podle cnb/ecb) | knihu `none` nezahrnou |
  | Obchod (`investra.trade.fx_rate`) | beze změny: kurz obchodu se zadává u obchodu; ocenění pozice pak chybou |
  | Průvodce a formulář knihy, profil přecenění | jen pro čtení, upozornění |
- **Bod 3 (výkazy ČNB kurzem ČNB):** `investra_cnb` kurzy nečte ani nepřepočítává; nic v kódu nepředpokládá opak. Přepočet
  výkazů zůstává na etapu CN.
- **Bod 5 (migrace):** SELECT v `investra` (read-only): všechny knihy CZK/ČNB nebo EUR/ECB, žádná jiná měna, profily také →
  migrace dat není potřeba.
- **Ověřeno (příkaz a výsledek):**
  - `tools/run_tests.sh investra_fx_revaluation,investra_nav` – 0 failed, 0 errors z 387 (po opravě `test_fx_run`; první běh
    pěti modulů selhal jen na `test_fx_run` s USD firmou a na datu úpisu v novém testu).
  - `tools/run_tests.sh all` – 0 failed, 0 errors z 795 testů (`investra_ci_20261116_154120`, smazána); varování v logu jen
    stará (popisky polí, markdown2, addons_path, log migrace MN-09).
  - Záloha `zalohy/investra-2026-11-16-pred-MN08.dump` (pg_dump -Fc, 9 MB, `pg_restore -l` 10 953 položek);
    `-u investra_entity,investra_rates,investra_fx_revaluation,investra_chart_fund,investra_nav --stop-after-init` v `investra`
    bez ERROR; verze v `ir_module_module` odpovídají; výběr `rate_source` má cnb/ecb/none; 8071 restartována (HTTP 200).
- **Ověřil Martin v prohlížeči 16. 11. 2026:** formuláře (zdroj jen pro čtení, upozornění v průvodci při volbě USD).
- **Neověřeno:** že nativní
  přepočet Odoo v knize v USD použije sdílené kurzy ČNB, je odvozeno z kódu (`_publish` zapisuje ČNB jako společné kurzy),
  testem neověřeno.
- **Otevřené otázky a návrhy mimo rozsah:** (1) ruční kurz pro knihu bez zdroje – doporučuji zatím nepřipustit a později
  řešit vlastním zdrojem v evidenci kurzů se schvalovací maticí, ne kurzem u pohybu; (2) nativní přepočet Odoo (faktury,
  platby v cizí měně) v knize mimo CZK/EUR by tiše použil kurz ČNB – do rozhodnutí takovou knihu nezakládat pro ostrý
  provoz. Oba body zapsány v `docs/otevrene-body.md`; rozhoduje Martin.
