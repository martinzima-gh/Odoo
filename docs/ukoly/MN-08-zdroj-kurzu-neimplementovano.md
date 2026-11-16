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

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
