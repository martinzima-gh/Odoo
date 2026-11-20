# ZJ-07 Očekávaná daň v ocenění: daňový profil fondu (návrh)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (`investra_nav/models`, výpočet daně); nejdřív jen návrh, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Opus 5.5 |

**Kontext:** dnešní výpočet (`investra_nav/models/valuation.py`, `_apply_tax`) bere výsledek od začátku roku (výnosy minus náklady bez daně) × sazba verze
a účtuje doplatek do požadovaného zůstatku. Chybí neuznatelné náklady, osvobozené a nezdanitelné výnosy, položky se samostatným základem a jinou
sazbou, ztráta z minulých let, ruční úpravy základu a odložená daň.

**Rozhodnuto 17. 11. 2026 (Martin):** varianta B – **daňový profil fondu**. Obecně platí základní sazba fondu a všechny náklady a výnosy jsou daňové;
zadávají se jen výjimky (účet → režim: neuznatelný náklad, osvobozený nebo nezdanitelný výnos, samostatný základ se sazbou).

**Návrh má obsahovat** (varianty a doporučení, bez kódu):
1. Model profilu a výjimek po účtech, platnost od data, vazba na knihu fondu.
2. ~~Ruční úpravy základu v ocenění~~ – **přesunuto do ZJ-12** (rozhodnutí 2026-11-18): oprava základu daně je řádek opravy u pravidla daně
   s volbou „Co opravuje: Základ“ (kladná = připočitatelná, záporná = odčitatelná, poznámka povinná, příloha nepovinná, platí do konce roku). ZJ-07 zůstává profil, výjimky po účtech, ztráta a odložená daň.
3. Ztráta z minulých let k odečtení (návrh ZJ-12: údaj daňového profilu na rok; rozhodne se v ZJ-07).
4. Zobrazení výpočtu daně v ocenění a v náhledu zaúčtování.
5. Právní rámec ověřený ve Sbírce zákonů s přesnými odkazy: zákon č. 586/1992 Sb. (sazba základního investičního fondu a ostatních fondů,
   samostatný základ daně, osvobození, neuznatelné náklady, ztráta); daňový režim změn reálné hodnoty u fondu; účetní rámec fondu pro odloženou daň.
   Co nejde ověřit, označit; nejasný výklad navrhnout k ověření u daňového poradce nebo auditora.

**Otevřené otázky pro Martina:** které fondy budou základní investiční fondy (sazba); odložená daň teď, nebo jako otevřený bod.

**Doplněno 17. 11. 2026 (průchod UI ZJ-06):**
- Pravidlo druhu Očekávaná daň nemá nákladovou roli; doplnit při řešení daní.
- ~~Základ časově rozlišené úplaty „po dani“ a cyklus odměny po dani~~ – **vyřešeno rozhodnutími 2026-11-18** (ZJ-12): základ „po kroku 1–4“ a společný dopočet
  s kontrolou konzistence; kruh úplata–daň i odměna–daň se řeší ustálením, ne zvláštními doúčtováními.

## Technický plán

Schváleno Martinem 19. 11. 2026 včetně odchylek C0.1–C0.8: `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 9 (9.1 zadání a referenční příklady, 9.2 technický plán,
9.3 postup a kód) a **Právní rámec** z oddílu 1 (D1–D14). Obsah se sem nekopíruje. DA-01 se do tohoto úkolu slučuje (D1).

- Provedení: běh 4 (účty a daňové modely, Sonnet 5.5) a běh 5 (výpočet daně a migrace, Opus 5.5), viz
  `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md`; zobrazení a manuál běh 6 (Copilot).
- Otázky pro daňového poradce a metodika jsou v `docs/otevrene-body.md` (dávka ZJ-07 až ZJ-19).
- Odchylky od plánu se zapisují do Výsledku.

## Výsledek

Běh 4 dávky (Claude Sonnet 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`: účty, modely a data, **bez výpočtu daně** (engine,
`_tax_item`, `_book_tax`, migrace sazeb a FVOCI ocenění jsou běh 5).

- **Změněné soubory:** `investra_nav/models/tax_rule.py` (nový: `investra.tax.rule`, `.version`, `investra.fund.tax.exception`),
  `models/fund_tax.py` (nový: pole fondu `tax_rule_id`, `tax_rate_now`, `tax_exception_ids`, `tax_fee_rule_id`, `tax_base_step`, nosič,
  `_tax_rules_used`, kontrola účtů, `action_add_common_tax_exceptions` vč. D11), `models/valuation.py` (`tax_rule_id` na opravě),
  `data/tax_rules.xml` (6 pravidel), `views/tax_views.xml` (nabídka Nastavení › Daně › Daňová pravidla, výchozí pohledy),
  `security/ir.access.csv`; `investra_entity/data/account_role.xml` (role `revaluation_reserve`, `revaluation_reserve_tax`);
  `investra_chart_fund` (účty 564300, 564400, 564500, 571100, 667500 a role v `ROLE_ACCOUNTS`/`EXTRA_ROLE_ACCOUNTS`; účty C1 doplnil běh 3);
  `investra_cnb/data/cnb_map.xml` (řádek 41 ROFO10_21 pro obě role); test `test_tax_rules_models.py` (14).
- **Ověřeno:** `tools/run_tests.sh investra_entity+` (všechny vlastní moduly): 1149 testů, 0 selhání; snímek ocenění 35 po povýšení
  kopie shodný. Testy: data pravidel, účty a role šablony, `_book_accounts`, kontroly pravidla a sazby, výjimky (unikátnost, podíl,
  neuznatelné jen u výnosu, D10 rozvahový účet se splatným pravidlem, odložené jen na rozvahovém účtu, účet daně nejde), nosič se zakládá a
  archivuje, výchozí pravidlo jen splatný obecný základ, použitá pravidla nesdílejí účty, běžné výjimky vč. FVOCI (D9 podle sazby, D10),
  oprava daně s pravidlem.
- **Neověřeno:** migrace `investra_chart_fund` 20.0.0.13.0 a `investra_nav` 20.0.0.39.0 na kopii ze zálohy (běh 7, verze se zatím nezvedly);
  právní rámec D1–D14 jsem znovu neověřoval (přejato ze zadání dávky).
- **Odchylky od plánu:**
  1. Čísla nových účtů G1 jsou pracovní, **k potvrzení Martinem / metodikem**: 564300 Oceňovací rozdíly FVOCI, 564400 Odložená daň
     k oceňovacím rozdílům, 564500 Opravná položka ECL v OCI, 571100 Realizované přecenění FVOCI, 667500 Opravné položky ECL
     (osnova 501 přesné číslo nepředepisuje; 564 Ostatní kapitálové fondy, 571 Nerozdělený zisk, 667 Jiné provozní náklady).
  2. ČNB: obě nové role na ROFO10_21 ř. 41 „Změna RH ostatních nástrojů vykázaných v RH do OCI“ (součet 39, 33, 28, 1). Přesnější rozdělení
     na ř. 35 (OCI z kapitálových nástrojů) a ř. 40 (dluhové nástroje) podle druhu nástroje mapa neumí (jen filtr kategorie IFRS 9) –
     otevřený bod pro metodika.
  3. Povinnost pravidla na opravě daně platí jen u fondu s daňovým pravidlem (`tax_rule_id` nebo výjimky), aby se nerozbily dosavadní
     fondy a opravy; migrace dosavadních oprav a povinnost bez výjimky až v běhu 5.
  4. Nosič: neplatí zatím ORM kontrola „druh Očekávaná daň jen z fondu“ ani úprava `fee_rule._check_archive` o účty všech použitých pravidel –
     dosavadní testy zakládají pravidla daně přímo; do běhu 5 spolu s přepisem testů. Nosič se zakládá s verzí sazby podle výchozího
     pravidla, aby dosavadní výpočet fungoval. Pole „Nosič v Pravidlech úplat jen pro čtení“ je věc formuláře (běh 6).
  5. Výchozí pravidlo fondu: kromě `kind = general` musí být `method = current` (odložené pravidlo je jen ve výjimce na rozvahovém účtu).
  6. Kontrola unikátnosti účtů porovnává všechny kódy (daň, rozvaha, zápočet) použitých pravidel, tedy i zápočet proti účtu daně jiného pravidla.
  7. `_check_unused` verze sazby hledá `"tax_rule": <id>` v detailu řádku daně v ocenění; tento klíč zapíše výpočet daně (běh 5).
- **Otevřené otázky a návrhy mimo rozsah:** odpovědi daňového poradce (viz oddíl 1 zadání) – pravidla jdou nastavit bez změny kódu.

## Převzetí
