# ZJ-12 Základ úplat ve čtyřech krocích, společný dopočet a ruční opravy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **červená** (`investra_nav`: `engine.py`, `models/valuation.py`, `models/fee_rule.py`, migrace, očekávané hodnoty referenčních scénářů); UI a protokol oranžová |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (nebo aktuální pracovní větev) |
| Zadal, dne | Martin, 18. 11. 2026 (návrh Claude, rozhodnutí v deníku z 18. 11. 2026) |
| Řešitel | Claude (kroky 1–4, červená); kroky 5–6 může po plánu převzít Antigravity nebo Copilot |
| Navazuje na | ZJ-06 bod 7, ZJ-10, ZJ-11; mění ZJ-11 (upřesnění a, bod 3, bod 6) a ZJ-07 (bod 2) |
| Stav | zadání zapsáno 2026-11-18, **kód čeká na Martinovo potvrzení zadání** |

**Cíl:** základ každé úplaty, výkonnostní odměny a daně se nastaví jednou srozumitelnou volbou „Základ: po kroku 1–4“. Všechny smysluplné kombinace se spočítají
jedním společným dopočtem, každá vypočtená hodnota jde ručně opravit jedním mechanismem a nic se nezmění zpětně u zaúčtovaných ocenění.

Referenční model (PowerShell) a jeho očekávané hodnoty: `docs/ukoly/ZJ-12/` (`model.ps1`, `testy.ps1`, `README.md`).

## Kroky výpočtu a volba základu

| Krok | Obsah |
|---|---|
| 1 | FK před úplatami a daní (stav po portfoliu, FX a nevypořádaných obchodech) |
| 2 | časově rozlišené úplaty, ruční úplaty a opravy |
| 3 | výkonnostní odměna |
| 4 | daň |

| Druh pravidla | Přípustné volby | Výchozí | Význam |
|---|---|---|---|
| Časově rozlišená úplata, základ FK, kapitál třídy, průměrný FK | 1, 2, 3, 4 | 1 | stav NAV k datu ocenění po daném kroku; „po kroku 2“ zahrnuje i úplatu samotnou; 4 = výsledný (zveřejněný) FK |
| Časově rozlišená úplata, základ aktiva nebo bez základu | bez volby (skrytá, ukládá 1) | 1 | úplaty jsou závazky a aktiva nemění |
| Výkonnostní odměna | 1, 2, 4 | 2 | 1 = hodnota třídy **plus úplaty, které třída nesla od poslední krystalizace**; nikdy po sobě samé |
| Očekávaná daň | 1, 2, 3 | 3 | které náklady snižují základ: 1 žádné úplaty ani odměna, 2 úplaty, 3 úplaty i odměna (dnešní chování); nikdy po sobě samé |

- Pořadí kroků 2 a 3 se nezadává, vyplývá ze základu: odměna „po kroku 1“ = před úplatami, úplata „po kroku 3“ = po odměně.
- Smíšení základů v jednom fondu je povolené bez varování.
- Popisky voleb jsou podle druhu, např. u úplaty „Po kroku 1 – před úplatami tohoto ocenění“, u odměny „Po kroku 1 – před úplatami od začátku období odměny“, u daně „Po kroku 2 – úplaty snižují základ“.

## Návrh

### A. Model (červená, migrace)

1. `investra.fee.rule`: nové pole `base_step` (Selection `1`–`4`, `tracking=True`) místo `base_mode` a `perf_base`. Přípustnost podle tabulky se kontroluje v `@api.constrains`.
   U výkonnostní odměny a daně se pole Zdroj základu (`base_source`) skryje: výpočet ho dnes ignoruje (`_apply_performance` bere vždy hodnotu třídy).
2. Kontroly na pravidle: nejvýš jedna aktivní výkonnostní odměna na třídu (dělení odměny jde přes podíl příjemcům), nejvýš jedno pravidlo daně na fond.
3. `investra.valuation.external` (řádek ruční úplaty a opravy) dostane čtyři nová pole:
   - `correction_target` („Co opravuje“: Částka / Základ),
   - `validity` („Platnost“: Do konce období / Jen toto ocenění, jen u odměny a daně, výchozí do konce období),
   - `computed_at_entry` („Vypočteno při zadání“, snímek),
   - `origin_id` („Převzato z“, Many2one na řádek předchozí verze ocenění).

   `corrects_rule_id` přijme všechny druhy pravidel. Z `_check_correction` zmizí zákaz odměny a daně, zůstane měna fondu, třída podle pravidla a povinná poznámka.
   Příloha zůstává nepovinná a bez upozornění.
4. Nový model nevzniká. Základ zůstává v hlavičce pravidla bez „Platí od“.

### B. Výpočet (červená)

1. **Společný dopočet** jako čistá funkce v `engine.py`, například `solve_fees(state, rules, pinned)`.
   - Vstup: hrubý stav (hodnoty tříd po kroku 1, předběžný kapitál a poměr tříd, výsledek od začátku roku), pravidla, pevné částky.
   - Výstup: částky za (pravidlo, třída).
   - Metoda: iterace pevného bodu (Jacobi) s relativní tolerancí 1e-12 × největší částka (dnes absolutní 1e-6 v `valuation.py:953`), nejvýš 500 kroků, jinak `UserError`.
   - Zaúčtování (`_book_fee`, daň, přesuny) až po ustálení, v pevném pořadí pravidel. Nahrazuje pevné pořadí v `_compute_all` (`valuation.py:413–428`) i dopočet úplat „po“ (`:946–964`).
2. **Stavy:**
   - po kroku 1: nic,
   - po kroku 2: úplaty, ruční úplaty a opravy (včetně vlastní),
   - po kroku 3: navíc odměna,
   - po kroku 4: navíc daň.

   Odměna ani daň nikdy nezahrnují samy sebe.
3. **Odměna „po kroku 1“:** k hodnotě třídy se přičtou úplaty, které třída nesla od `perf_base_date`:
   - řádky úplat s třídou (časově rozlišené, ruční, opravy) z dřívějších ocenění v období a z tohoto ocenění,
   - podíl třídy na úplatách celého fondu podle uloženého poměru (`investra.valuation.class.ratio`) každého ocenění,
   - minus přesuny, které třída jako příjemce dostala,
   - u měřítka „hodnota na kus“ úplata na kus podle kusů v každém ocenění.

   Přičtená částka se uloží do detailu řádku. Implementovat jako obecnou funkci „přičti úplaty od data D“ (odměna: D = krystalizace; daň: D = 1. 1.).
   Časově rozlišené úplaty zůstávají u stavu k datu ocenění.
4. **Daň:**
   - základ = výsledek od začátku roku + zpět přičtené náklady kroků, které podle volby základ nesnižují, + opravy základu;
   - požadovaná daň = sazba × max(0, základ), účtuje se doplatek proti zaúčtované. Jeden doklad, „doúčtování po výkonnostní odměně“ (`tax:<id>:perf`) zaniká;
   - odměna po kroku 4 s daní po kroku 3 se dopočítá společně, to nahrazuje dnešní dvoukrokové zjednodušení.
5. **Daňový efekt tříd:** daň fondu zůstává společná. Daňový efekt položek výsledku s třídou (odměna, úplaty a ruční úplaty třídy, opravy, zajištění) se přesune té třídě přes `internal_clearing`.
   - Přesun do třídy c = e × (spec_c − ρ_c × Σ spec), součet 0. Efektivní sazba e = (daň bez specifických položek − daň s nimi) / Σ spec: v zisku sazba, ve ztrátě 0, při přechodu přes nulu poměrně.
   - Neuznatelné účty podle ZJ-07 se vynechají.
   - Třída může mít zápornou daň, účtuje se ale jen přesun.
   - **Implementační upřesnění (referenční model ho neověřuje, je jednoobdobový):** přesun počítat kumulativně od 1. 1. a účtovat jako doplatek proti dříve zaúčtovaným přesunům třídy, stejně jako daň. Ověřit vícedobým testem.
   - Úspora z daňové ztráty minulých let se dělí poměrem, ztráta se po třídách nesleduje (uvést v manuálu).
6. **Průměrný FK:**
   - volba kroku jako u FK; dnešní bod průměru je stav po zvoleném kroku, dřívější body jsou zveřejněné FK, průměr prostý;
   - v dopočtu má dnešní bod váhu 1/n;
   - opravit podezření z kódu: pravidlo s více třídami volá `_apply_average` pro každou třídu (`valuation.py:932–937`). Doklad se nezdvojí (stejný klíč a obsah), řádek rozpisu ano a další ocenění pak odečte `booked` dvakrát. Ověřit testem v kroku 1.
7. **Opravy** (dva průchody):
   - (1) dopočet bez oprav = „Vypočteno“, uložit do detailu řádku a porovnat se snímkem `computed_at_entry`;
   - (2) opravená pravidla mají pevnou částku vypočteno + oprava, ostatní se dopočítají k ní. Výsledek je přesně vypočteno + oprava.

   Opravy podle druhu:
   - **Časově rozlišená úplata:** oprava je trvalá (jako ZJ-11); u průměrného FK se nedorovnává.
   - **Odměna a daň** (platnost „do konce období“):
     - součet převzatých oprav z dřívějších ocenění v období (odměna od krystalizace, daň od 1. 1.) se přičte k požadovanému stavu;
     - „Ukončit opravu“ založí opravu o −převzatou částku s povinnou poznámkou;
     - u „jen toto ocenění“ další ocenění zobrazí upozornění, že oprava skončila;
     - krystalizace a konec roku převzaté opravy ukončí.
   - **Oprava základu:** přičte se k základu pravidla. U daně je to ruční úprava základu ze ZJ-07 bod 2 (kladná = připočitatelná, záporná = odčitatelná), platí do konce roku.
8. **Kontroly ocenění:**
   - **stop:**
     - konzistence: každé pravidlo bez pevné částky přepočtené z konečných čísel musí vyjít stejně (relativní tolerance);
     - vypočtená částka se liší od snímku při zadání opravy: „Úplata X: při opravě A, nyní B; oprava C“, uživatel opravu potvrdí nebo upraví;
     - oprava odkazuje na pravidlo, které změnilo druh nebo třídy nebo je neaktivní (`_check_correction` znovu při výpočtu);
   - **upozornění:**
     - „Obsahuje převzaté opravy (n)“;
     - „Předchozí verze měla ruční úpravy (n), které v této verzi nejsou“.
9. **Stopa:** poznámka kroků Spočítání a Odeslání ke schválení (`_compute_note`, `_log_step("submitted")`) dostane seznam oprav (pravidlo, třída, vypočteno → oprava, zdůvodnění, kdo zadal).
   Ocenění nedostane `mail.thread`.
10. **Nová verze po stornu nebo vrácení depozitářem** (`_new_version`): tlačítko „Převzít z verze n“ zkopíruje ruční úpravy a opravy včetně nové kopie přílohy (patřící nové verzi) a vyplní `origin_id`. Nechtěné se v návrhu smažou.

### C. Rozhraní (oranžová)

1. **Fond, záložka Schéma výpočtu:**
   - tabulka pravidel fondu (název, druh, zdroj, „Základ: po kroku …“ jen s přípustnými volbami);
   - předvolby „Standardní fond“ (úplaty 1, odměna 2, daň 3) a „Úplaty z výsledného FK“ (úplaty 4, daň 2);
   - náhled s čísly (FK 1 000 000, sazby aktuálních verzí, rok), počítaný **stejnou funkcí** jako ocenění;
   - informace „vzájemný dopočet“ u zacyklených kombinací (např. úplata 4 + daň 2, odměna 4 + daň 3), ne chyba.
2. **Formulář pravidla:** pole Základ s popisky a nápovědou podle druhu. Varování při změně základu u průměrného FK, odměny a daně: „Změna se projeví i za dosavadní část roku nebo období odměny; rozdíl se doúčtuje v dalším ocenění.“
3. **Ocenění, záložka Úplaty:**
   - sloupce Vypočteno / Oprava / Výsledek / Zdůvodnění / Zadal / Kdy se zobrazí **jen pokud ocenění opravu má**;
   - tlačítko „Opravit“ u všech druhů (dnes jen `kind == 'periodic'`, `valuation.py:1966`). Dialog: Co opravuje, Rozdíl nebo Cílová částka (vzájemně se dopočítávají), Platnost u odměny a daně, poznámka, příloha;
   - převzaté opravy jako řádky jen pro čtení s tlačítkem „Ukončit opravu“; tlačítko „Převzít z verze n“.

### D. Migrace (červená)

1. Pre-migrace převede hodnoty dřív, než Odoo 20 sloupce zrušených polí smaže (rozhodnutí 2026-11-17 „Zrušená pole a sloupce databáze“):
   - `base_mode`: `before`→1, `after`→2;
   - `perf_base`: `before_fees`→1, `after_fees`→2, `after_tax`→4;
   - pravidla daně → 3; aktiva, bez základu a průměrný FK → 1.
2. Před povýšením zkontrolovat data (dvě odměny na téže třídě, dvě pravidla daně na fondu, průměrný FK s třídami) a nález předložit Martinovi.
   Záloha a zkouška na `investra_ci_*`. Výsledky stávajících pravidel se nemění, kromě pravidel s „odměna před úplatami“ (rozhodnutí 2) a fondů s daní a specifickými položkami tříd (daňový efekt), a to jen v nových výpočtech.

### E. Protokol a XLS (oranžová, spolu se ZJ-11 krokem 3)

- List Úplaty (`models/package.py:178`), dnes Pravidlo, Třída, Částka, Článek statutu. Přibude Základ (krok), Částka základu, Vypočteno, Oprava, Výsledek, Zdůvodnění, Převzato z.
  Sloupce oprav jen v ocenění s opravou, hodnoty ze snímku v detailu řádku, ne z pravidla. Starší ocenění mají v detailu jen klíč `base_mode`: zobrazit převedeně, balíčky se znovu negenerují.
- Přemostění třídy: nová položka „Daňový efekt specifických položek“.

## Testy

1. **Charakterizační testy dnešního chování** před změnou, včetně podezření u průměrného FK s více třídami.
2. **Referenční model (`docs/ukoly/ZJ-12/`) převést do Pythonu** jako testy čisté funkce dopočtu v `engine.py` (bez Odoo). Očekávané hodnoty jsou v `docs/ukoly/ZJ-12/README.md`:
   - 720 kombinací: ustálení ze dvou startů, jediné řešení, konzistence, NAV = hrubý − úplaty − odměna − daň, součet daně tříd = daň fondu, nezápornost;
   - shoda s dnešním pořadím u 40 kombinací;
   - 1 152 oprav s pevnou částkou;
   - příklady C1–C8.
3. **Odoo testy se změnou očekávaných hodnot** (schvaluje Martin):
   - `test_perf_after_tax_then_tax_is_topped_up`: 19,00 / 4,05 → 19,19 / 4,04, jeden doklad daně;
   - `test_correction_lowers_cost_before_after_fees`: výsledek 9 901,98 → 9 800,99, FK 990 198,02 → 990 199,01;
   - scénář `s4_uplata_odmena_dan.json`: kapitály tříd kvůli daňovému efektu.
4. **Přepis polí v testech:** `base_mode` a `perf_base` v `test_fees`, `test_fee_correction`, `test_bridge`, `test_scenarios` (klíč `base`) a `test_tracking_zj10` na `base_step`.
   `TestBaseModeRetroactive` přejmenovat a ponechat aserce.
5. **Nové testy:**
   - odměna po kroku 1 s přičtením (měsíční ocenění, roční krystalizace: odměna 22 130 → 24 000; měřítko na kus s úpisem v polovině období);
   - tři kroky daně × odměna 1, 2 a 4;
   - úplata po kroku 4 s daní po kroku 2 (C4);
   - daňový efekt: C5, ztráta, přechod přes nulu (C7) a vícedobý kumulativní přesun;
   - průměrný FK po kroku 2;
   - kontroly na pravidle;
   - opravy odměny a daně: platnost, převzetí přes tři ocenění, ukončení, krystalizace, přelom roku;
   - oprava základu daně;
   - kontroly z B.8;
   - převzetí z verze;
   - migrace.

## Postup

| # | Krok | Zóna | Riziko |
|---|---|---|---|
| 1 | Charakterizační testy a testy čisté funkce podle referenčního modelu (bez změny chování) | červená (očekávané hodnoty) | nízké |
| 2 | `base_step`, migrace, kontroly na pravidle, nová pole na řádku opravy; výsledky beze změny | červená (migrace) | střední |
| 3 | Společný dopočet (B.1–B.6, B.8 konzistence), zaúčtování po ustálení | červená | **vysoké** |
| 4 | Opravy všech druhů, převzaté opravy, kontroly B.8, stopa B.9, převzetí z verze B.10 | červená | střední |
| 5 | Schéma výpočtu, formulář pravidla, záložka Úplaty | oranžová | nízké |
| 6 | Protokol a XLS (E), spolu se ZJ-11 krokem 3; manuál (kroky výpočtu, opravy, zjednodušení daňové ztráty) | oranžová, zelená | nízké |

Po každém kroku test `investra_nav`, před sloučením `investra_nav+`, `all` před `main`. Zaúčtovaná ocenění nejdou přepočítat, takže se jich změna nedotkne.

## Ověřené nálezy v kódu (commit `1c08179`)

- Pevné pořadí v `_compute_all` (`valuation.py:413–428`). Snímek odměny „před úplatami“ (`:416`) vrací jen úplaty tohoto ocenění.
- Dopočet úplat „po“ (`:946–964`) s absolutní tolerancí 1e-6. Engine má nepoužitou větev `base_mode == "after"` (`engine.py:156`), ocenění volá vždy `"before"`.
- Průměrný FK: dnešní bod = FK před úplatami (`:936`), dřívější body = zveřejněné FK (`:899`). U více tříd vznikají opakovaná volání (`:932–937`).
- Daň: řádky bez třídy (`:1080`), dělí se poměrem. Odměna se účtuje s třídou (`_book_fee`, `:866`).
- Dvě odměny na téže třídě se počítají postupně podle `_order = fund_id, id`. Dvě pravidla daně: rozhodne poslední.
- Formulář ukazuje Zdroj základu i u odměny (`views/nav_views.xml:468`), výpočet ho ignoruje.
- Ocenění nemá `mail.thread` (dědí `investra.record.guard` a `investra.approval.pending.mixin`). Kroky (`investra.valuation.step`) nejdou změnit ani smazat.
- `_new_version` založí prázdný návrh, ruční úplaty a opravy se nepřenesou.
- `_clear` maže řádky rozpisu, ne ruční úplaty. Změna ruční úplaty nebo pravidla zablokuje odeslání do přepočtu (`_inputs_now`). Po odeslání je řádek zamčený (`_check_open`).
- Oprava úplaty „po“ posune vypočtenou částku (`test_correction_lowers_cost_before_after_fees`: 9 901,98).
- Ve schvalovací matici zatím chybí aktivita pro opravu. Druhá osoba u oprav je podle ZJ-11 „přes matici, výchozí bez“, aktivitu doplnit podle potřeby.

## Otevřené body: vazby na ZJ-07 a DA-01

Daň se v ZJ-12 řeší jen v rozsahu zadání (krok 4, volba základu 1–3, společný dopočet, přesun daňového efektu tříd, oprava základu). Nad ten rámec se nic neřeší;
tři vazby na ZJ-07 zůstávají otevřené a rozhodnou se při návrhu ZJ-07 (návrh, bez kódu):

1. **Kde se nastavuje uznatelnost úplat a odměny:** krok daně (volba „které náklady snižují základ“: žádné / úplaty / úplaty i odměna, tj. celá položka na pravidle)
   × daňový profil ZJ-07 (výjimky po účtech: neuznatelný náklad se do základu nepřičítá ani neodečítá). ZJ-12 počítá s tím, že neuznatelné účty ze ZJ-07 se při
   daňovém efektu tříd vynechají; vztah obou nastavení (kdo má přednost, zda se kombinují) je třeba určit.
2. **Samostatný základ s jinou sazbou** (ZJ-07): ZJ-12 počítá jedno pravidlo daně a jeden základ na fond. Samostatný základ potřebuje druhé pravidlo nebo
   řádek profilu; to koliduje s omezením „nejvýš jedno pravidlo daně na fond“ (část A.2) a s oddělením přesunu daňového efektu tříd.
3. **Odložená daň a daňový efekt tříd:** ZJ-12 účtuje jen splatnou (očekávanou) daň a přesun efektu položek třídy; odložená daň (vyhláška 501/2002 Sb., ČÚS) se do něj
   nepromítá. Je třeba určit, zda se odložená daň rozděluje mezi třídy stejným způsobem a zda ji ovlivní přesun efektu specifických položek.

**Překryv ZJ-07 s DA-01** (`docs/plan-dalsiho-vyvoje.md`, etapa s daněmi): DA-01 („Daně fondu – daňové a nedaňové účty …, výpočet splatné daně, dohad na daň, odložená daň“)
zahrnuje totéž co ZJ-07 (daňový profil, výjimky po účtech, samostatný základ, odložená daň). Před návrhem ZJ-07 rozhodnout, zda se ZJ-07 sloučí do DA-01,
nebo zda ZJ-07 zůstane jako zjednodušený profil a DA-01 jako následná plná varianta. Do rozhodnutí se v ZJ-07 ani v DA-01 nic nezavádí.

## Zjištění kroku 1 (2026-11-18)

- Referenční model z přílohy A je převedený do Pythonu (`addons/custom/investra_nav/tests/ref_fee_model.py`, testy `test_fee_reference_model.py`) a reprodukuje A.1 přesně:
  720 kombinací, 1 152 oprav, shoda s dnešním pořadím u 40 kombinací, 33 kroků, relativní zbytek 3,305e-13, **12 013 kontrol, 0 selhání**; příklady C1–C8 sedí.
  Běží bez Odoo (`python3 ref_fee_model.py`). V kroku 3 se testy přepnou na čistou funkci v `engine.py`.
- **Podezření z B.6 potvrzeno** (`test_fee_characterization.py`): pravidlo průměrného FK se dvěma třídami vytvoří dva řádky rozpisu (doklad jen jeden) a další ocenění
  odečte zaúčtovanou úplatu dvakrát (`booked` 6 200 místo 3 100). Chyba existuje dnes, test ji zachycuje jako dnešní chování; v kroku 3 se očekávaná hodnota změní na 3 100.

## Výsledek

## Převzetí
