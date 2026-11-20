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

### Běh 5 (Claude Opus 5.5, 20. 11. 2026): výpočet daně po pravidlech, migrace

- **Změněné soubory:** `investra_nav/engine.py` (`_tax_rule_amount`, `_tax_rules`, `_tax` po pravidlech, plochý spec beze změny),
  `models/valuation.py` (`_tax_item` po pravidlech vč. výjimek, podílu, neuznatelných, D10 a odložené daně; `_book_tax` po pravidlech,
  `_apply_base_correction` po pravidlech, oprava daně na účty pravidla, `tax_account` u položek dopočtu, `_fee_account_id`, kontroly
  `tax_no_rule` a `tax_credit_lost`, výchozí pravidlo opravy daně), `models/tax_breakdown.py` (nové pole `tax_breakdown_html`),
  `models/fee_rule.py` (druh Očekávaná daň jen z fondu, pojistka archivace přes účty pravidel), `models/fee_scheme.py` (náhled ze sazby
  výchozího pravidla, „náhled bez výjimek“, informace D2), `migrations/20.0.0.39.0/post-migration.py` (C5), testy
  `test_tax_rules.py` (nový, 21), `test_fiscal_year.py` (příklad hospodářského roku), `common.py` (`fund_tax`, `shared_tax_rule`), přepis
  testů zakládajících nosič přímo (`test_bridge`, `test_class_no_common`, `test_fee_*`, `test_fees`, `test_scenarios`,
  `test_tax_rules_models`, `investra_dashboard/tests/test_dashboard.py`), `tools/nav_reference/test_engine.py` (třída `TaxRules`, 8), `tools/demo_data/seed.py`, `tools/nav_demo/demo.py`.
- **Ověřeno:** viz předávka `docs/predavky/2026-11-20-davka-beh-5.md` (testy, snímek 35/39 shodný po migraci na kopii, referenční čísla).
  Migrace na kopii `investra`: fondy A a B → „Daň ZIF 5 %“, nosič fondu „01 Zímův fond CZK“ nemá sazbu → přeskočen (varování v logu).
- **Odchylky od plánu:**
  1. Engine: efekt tříd se sčítá jako e_r × Σ spec_r po pravidlech (u jednoho pravidla stejné číslo jako dřív, i v posledním místě).
  2. `_tax_item`: výsledek a specifické položky každého pravidla se zaokrouhlí na haléře jako dosud `_sum`; fond bez výjimek = dnešní čísla.
  3. Doklad daně: `extra.account_id` jen u účtu, který není hlavním účtem role (u ZIF/21 % se řádky ani otisk proti dnešku nemění).
     Odložená daň FVOCI se účtuje řádkem role `expense_tax` s účtem 564400 (kapitál) a `tax_payable` s účtem 348000.
  4. Detail řádku daně: `rules` s klíčem `"tax_rule": <id>` (zámek verze sazby), `exceptions` (s `rule_name`), `nondeductible`, `excluded`.
  5. Upozornění `tax_no_rule` je u každého fondu bez výchozího pravidla (C0.6; nosič bez pravidla se archivuje, proto podmínka „nosič bez
     pravidla“ nenastane). Fondy bez daně (v `investra` C, D, E a „01 Zímův fond CZK“) tak mají v dalších oceněních nové upozornění.
     `tax_credit_lost` jen u fondu s pravidlem se zápočtem, aby se kontroly ostatních ocenění nezměnily. Test dashboardu (stav „ok“)
     proto nastavuje fondu výchozí pravidlo.
  6. Oprava daně: pravidlo je povinné vždy; bez zadání dostane výchozí pravidlo fondu (create i tlačítko Opravit); ukončení převzaté opravy
     přebírá pravidlo. Test `test_tax_rules_models` upraven (bez pravidla → výchozí, ne chyba).
  7. Nosič: druh Očekávaná daň jde založit nebo nastavit jen v kontextu `investra_tax_carrier` (fond, migrace, `install_mode`);
     `test_fee_base_step` testuje model nosiče s tímto kontextem, ostatní testy nastavují `fund.tax_rule_id`.
  8. Pojistka archivace nosiče: součet |zaúčtované daně| přes pravidla z rozpadu posledního ocenění a pravidla fondu (splatná pohyb účtu
     daně od začátku období, odložená zůstatek rozvahového účtu); ocenění bez rozpadu → hlavní účet role jako dřív.
  9. Migrace: standardní pravidlo jen tehdy, když fond nemá řádek daně před platností standardu (1. 1. 2024), jinak „Daň <fond>“;
     archivovaný nosič výchozí pravidlo nedostane; nosič bez sazby se přeskočí.
  10. Rozpad daně je samostatný soubor `tax_breakdown.py` (pole na ocenění), zobrazení ve formuláři dodá Copilot (běh 6).
  11. Náhled ve Schématu výpočtu bere sazbu z výchozího pravidla fondu; fond bez něj má poznámku „daň v náhledu chybí“.
- **Zdroje výsledkových řádků s třídou (daň po třídách, 9.1 C):** výpočet čte výsledkové řádky s třídou z knihy (`_read_group` podle účtu
  a třídy), takže efekt jde třídě řádku bez ohledu na zdroj. Zdroje a testy přesunu efektu:
  úplaty a odměny tříd a jejich opravy – stávající testy ZJ-12 (`test_bridge`, `test_fee_solver`, `test_fee_carried`);
  ruční úplata s třídou – `test_class_effect_manual_fee_of_class`; ruční doklad s třídou (penále Mimo základ, dividenda samostatný
  základ) – `test_class_effect_exempt_penalty`, `test_class_effect_separate_rule`; portfolio třídy (obchody, realizace, ZJ-09 A) –
  `test_class_effect_portfolio_of_class`; třída bez podílu – `test_class_no_common`. **Bez vlastního testu daně:** poplatky z úpisů
  a odkupů ve prospěch třídy, kurzové rozdíly a zajištění třídy, deriváty třídy – jejich řádky s třídou testují vlastní moduly, daň je
  bere stejnou cestou (návrh: doplnit při převzetí, běh 7).

## Převzetí
