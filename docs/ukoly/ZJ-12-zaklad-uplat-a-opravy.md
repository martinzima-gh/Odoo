# ZJ-12 Základ úplat ve čtyřech krocích, společný dopočet a ruční opravy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **červená** (`investra_nav`: `engine.py`, `models/valuation.py`, `models/fee_rule.py`, migrace, očekávané hodnoty referenčních scénářů); UI a protokol oranžová |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (nebo aktuální pracovní větev) |
| Zadal, dne | Martin, 18. 11. 2026 (návrh Claude, rozhodnutí v deníku z 18. 11. 2026) |
| Řešitel | Claude (kroky 1–4, červená); kroky 5–6 může po plánu převzít Antigravity nebo Copilot |
| Navazuje na | ZJ-06 bod 7, ZJ-10, ZJ-11; mění ZJ-11 (upřesnění a, bod 3, bod 6) a ZJ-07 (bod 2) |
| Stav | kroky 1–3 hotové (2026-11-18) včetně daně v základu odměny a schváleného s4; krok 4 (opravy všech druhů, části 4a–4e) v práci |

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
| Výkonnostní odměna | 1, 2, 4 | 2 | 1 = hodnota třídy **plus úplaty a daň, které třída nesla od poslední krystalizace**; 2 = plus daň od krystalizace; 4 = zveřejněná hodnota (podle statutu: odměna z NAV po dani); nikdy po sobě samé |
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

   **Daň v základu odměny** (rozhodl Martin 18. 11. 2026): u odměny po kroku 1 a po kroku 2 se od `perf_base_date` přičte zpět i daň, kterou třída
   nesla: podíl třídy na pohybech daně podle poměru každého ocenění minus přesuny daňového efektu do třídy. Stejnou funkcí „přičti od data D“.
   Krok 1 = přičíst úplaty i daň, krok 2 = jen daň, krok 4 = nic. Starší řádky daně bez přesunů: jen podíl podle uloženého poměru ocenění.
   Důvod: krok má znamenat totéž v jednom ocenění i za celé období odměny (stejný princip jako u úplat). Výchozí krok odměny zůstává 2.
4. **Daň:**
   - základ = výsledek od začátku roku + zpět přičtené náklady kroků, které podle volby základ nesnižují, + opravy základu;
   - požadovaná daň = sazba × max(0, základ), účtuje se doplatek proti zaúčtované. Jeden doklad, „doúčtování po výkonnostní odměně“ (`tax:<id>:perf`) zaniká;
   - odměna po kroku 4 s daní po kroku 3 se dopočítá společně, to nahrazuje dnešní dvoukrokové zjednodušení.
5. **Daňový efekt tříd:** daň fondu zůstává společná. Daňový efekt položek výsledku s třídou (odměna, úplaty a ruční úplaty třídy, opravy, zajištění) se přesune té třídě přes `internal_clearing`.
   - Přesun do třídy c = e × (spec_c − ρ_c × Σ spec), součet 0. Efektivní sazba e = (daň bez specifických položek − daň s nimi) / Σ spec: v zisku sazba, ve ztrátě 0, při přechodu přes nulu poměrně.
   - Neuznatelné účty podle ZJ-07 se vynechají.
   - Třída může mít zápornou daň, účtuje se ale jen přesun.
   - **Implementační upřesnění (referenční model ho neověřuje, je jednoobdobový):** daňový efekt E_c = e × spec_c se počítá od 1. 1., přesun je ale **přírůstkový**: přesun_c = ΔE_c − ρ_c(dnes) × ΔΣE, Δ proti minulému ocenění v roce (z detailu jeho řádku daně). Dřívější přesuny se dnešním poměrem nepřepočítávají, stejně jako daň rozdělená v minulých oceněních (Martin 18. 11. 2026; nahrazuje kumulativní doplatek ze stejného dne).
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
     U průměrného FK upravuje celoroční průměr a platí do konce roku jako převzatá oprava (vidět, lze ukončit). U úplaty ze stavu k datu (FK, kapitál
     třídy) platí jen pro toto ocenění; další ocenění upozorní „Minulé ocenění mělo opravu základu u pravidla X“ (Martin 18. 11. 2026).
   - **Potvrzení změny vypočtené částky** (kontrola stop z D4, Martin 18. 11. 2026): řádek opravy na záložce Úplaty má tlačítka „Ponechat rozdíl“
     a „Ponechat výsledek“; obě aktualizují `computed_at_entry` a ocenění se přepočte. Kontrola platí jen pro opravy zadané v tomto ocenění, ne pro převzaté.
   - **Zrušení úplaty** bez nové funkce (Martin 18. 11. 2026): v dialogu „Opravit“ zkratka „Vynulovat“ (cílová částka 0; krok 5). Pojistka: archivace
     pravidla odměny nebo daně se zastaví, má-li z posledního ocenění nenulovou naběhlou nebo zaúčtovanou částku („Nejdřív nastavte verzi sazby 0 %…“);
     ověřit, že archivované pravidlo naběhlou částku opravdu přestane rozpouštět. Manuál „Jak úplatu zrušit“ (jen toto ocenění = Vynulovat; od data =
     verze sazby 0 %; omyl = archivace) v kroku 6.
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

## Zjištění kroku 2 (2026-11-18)

- `investra.fee.rule.base_step` (výběr 1–4, `tracking`, výchozí podle druhu výpočtem `_compute_base_step`: úplata 1, odměna 2, daň 3;
  nepřípustná volba se po změně druhu nebo zdroje nahradí výchozí). Přípustnost podle tabulky hlídá `_check_base_step`; `base_mode` a `perf_base` zrušené.
  Formulář: Zdroj základu skrytý u odměny i daně, Základ skrytý u aktiv a bez základu. Popisky voleb podle druhu přijdou v kroku 5.
- Kontroly A.2 (`_check_single_performance_and_tax`): nejvýš jedna aktivní odměna na třídu, nejvýš jedno aktivní pravidlo daně na fond; pravidla bez tříd kontrolu odměn nespouštějí.
- Řádek opravy: `correction_target`, `validity`, `computed_at_entry` (plní tlačítko Opravit z vypočtené částky), `origin_id`. `_check_correction` přijme pravidlo každého druhu;
  „Jen toto ocenění“ jen u odměny a daně; Co opravuje a Platnost jen u opravy.
- **Dočasná pojistka do kroků 3 a 4** (`_check_fee_steps`): výpočet ocenění odmítne základ, který dnešní pořadí neumí (úplata po kroku 3 a 4, průměrný FK po kroku 2–4,
  daň po kroku 1 a 2), a opravy odměny, daně a základu. Inline formulář ruční úplaty dál nabízí jen časově rozlišenou úplatu (rozšíří krok 5). Výsledky existujících pravidel beze změny.
- Pre-migrace `migrations/20.0.0.37.0/pre-migration.py` (verze 20.0.0.36.0 → 20.0.0.37.0). Zkouška na `investra_ci_zj12mig` obnovené ze zálohy
  `zalohy/investra-2026-11-18-pred-ZJ12-krok2.dump`: převedeno 14 pravidel (1: 11 úplat, 2: odměna 3, 3: daně 4 a 7), staré sloupce smazané, rozpis úplat beze změny
  (123 řádků, součet 6 258 847,97), přepočet obou otevřených ocenění (fond 1 s odměnou a daní, fond 2 s daní) dal shodné FK i úplaty. Kopie smazána.
- Testy: nové `test_fee_base_step.py` (11 testů: výchozí a přípustné volby, změna druhu, jedna odměna na třídu, jedna daň na fond, pravidla bez tříd, pojistky výpočtu,
  pole opravy, převod v pre-migraci). Pole v testech převedená, `TestBaseModeRetroactive` → `TestBaseStepRetroactive`, scénáře mapují klíč `base` (JSON beze změny).
  Schválené nové hodnoty (19,19 / 4,04; 9 800,99 / 990 199,01) se zapíšou do testů v kroku 3 spolu s výpočtem.

## Zjištění kroku 3 (2026-11-18)

**Rozhraní** `engine.solve_fees(classes, items, pinned=None, max_steps=500, rel_tol=1e-12)` (čistá funkce, bez Odoo):

- `classes`: `{třída: {"value": hodnota po kroku 1, "ratio": ρ}}`; FK po kroku 1 = součet hodnot.
- `items`: položky v pevném pořadí s `key`, `stage` (2 úplata, ruční úplata, oprava; 3 odměna; 4 daň), `payer` (třída nebo fond),
  `share` a `recipients` (váhy přijímajících tříd), `base` (`None` = pevný základ; `{"scope": "fund"|"class", "class", "step"}`)
  a `amount` (funkce základ → přesná částka, nebo konstanta). Daň místo `base`/`amount` nese `tax` (sazba, krok, výsledek od 1. 1.
  po kroku 1 s přičtenými nezapočitatelnými náklady dřívějších ocenění, zaúčtovaná daň, specifické náklady tříd, dřívější přesuny).
- Stav po kroku s = položky se `stage ≤ s`; odměna ani daň nezahrnují samy sebe. Jacobiho iterace z nuly, relativní tolerance,
  neustálení = `ValueError` (ocenění `UserError`). Výstup: částky, základy, daň s přesuny daňového efektu, počet kroků, zbytek konzistence.
- Funkce částky staví ocenění z `periodic_fee` a `performance_fee` (nový klíč `exact` = částka před zaokrouhlením); engine o pravidlech nic neví.
- Shoda s referenčním modelem (`tests/ref_fee_adapter.py`, `test_fee_solver.TestSolveFeesEngine`): 720 kombinací (rozdíl ≤ 1e-10, nejvýš 32 kroků),
  rozdělení daně mezi třídy, 1 152 oprav (opravené pravidlo pevně na „Vypočteno“, oprava jako samostatná pevná položka).

**Zaúčtování po ustálení** (`_apply_fees`): průchod bez oprav, s opravami druhý průchod; pak doklady v pevném pořadí, částky už na pořadí nezávisí:
časově rozlišené úplaty (pravidla podle `_order`, třídy) → ruční úplaty a opravy → výkonnostní odměny (a krytí) → daň.
Daň je **jeden doklad** `tax:<id>`: doplatek daně a přesun daňového efektu tříd přes `internal_clearing` (součet 0); `tax:<id>:perf` zaniká.
Opravené pravidlo se zaúčtuje částkou i základem z průchodu bez oprav (detail `corrected`). Kontrola `fee_consistency` (stop při zbytku > 1e-10).

**Výpočet:**
- Řádky rozpisu nově nesou `expense` (náklad mimo fond) a `borne` (částka nesená třídami); z nich se počítá přičtení úplat od data
  (odměna po kroku 1 od krystalizace, daň od 1. 1.). Starší řádky je nemají: náklad = částka × (1 − podíl příjemců), plátce-třída nese celou
  částku, společnou úplatu třídy poměrem uloženým v ocenění; podíl přijatý od jiných tříd se u nich vynechá (odchylka jen u řádků před krokem 3).
- Daň: výsledek od 1. 1. z knihy po kroku 1; náklady dřívějších ocenění, které podle kroku základ nesnižují, se přičtou zpět. Specifické
  položky třídy = výsledkové řádky s třídou od 1. 1. (bez účtu daně) + položky tohoto ocenění s plátcem-třídou. Přesun přírůstkový
  (B.5): ΔE_c − ρ_c × ΔΣE proti minulému ocenění v roce; řádek daně ukládá nezaokrouhlený `effect` a `effect_total`, starší řádky kroku 3
  se dopočtou z `effective_rate` × `specific`. Haléřový rozdíl nese největší přesun; zaokrouhlení přesunu se mezi oceněními nedorovnává.
- Průměrný FK: jedna položka na pravidlo (oprava B.6); „booked“ z dřívějších ocenění bere jeden řádek pravidla na ocenění (i u starších dvojitých).
- **Odchylka od dřívějšího chování:** váhy přijímajících tříd jsou hodnoty tříd po kroku 1 (dřív stav knihy v okamžiku zaúčtování, závislý na
  pořadí dokladů). Krytí výkonnostní odměny zůstává mimo dopočet (přesun po zaúčtování odměny, jako dřív).
- Dočasná pojistka `_check_fee_steps` zúžena jen na opravy odměny, daně a základu (zaniká v kroku 4).
- Přemostění třídy: přesun daňového efektu je zatím v položce „Ostatní“; samostatnou položku přinese krok 6 (E).

**Testy:** schválené hodnoty zapsané (19,19 / 4,04 a jeden doklad daně; 9 900,99 vypočteno, výsledek 9 800,99, FK 990 199,01); B.6 charakterizace
na 3 100 a jeden řádek. Nové `test_fee_solver.py` (11 testů): engine × referenční model, neustálení, 36 kombinací kroků úplaty × odměny × daně
v Odoo proti modelu, C4, C5, C7, průměrný FK po kroku 2, odměna po kroku 1 s přičtením (2 000 / 4 000 / 6 000, krystalizace), měřítko na kus
s úpisem, přírůstkový přesun (únor −251,14) a velký úpis do B v únoru (lednový přesun se nepřepočítá; únor −17,94, kumulativně by bylo +180,59).
`investra_nav` 449/449, `investra_nav+` 523/523 (po přechodu na přírůstkový přesun). Zkouška na `investra_ci_zj12k3` ze zálohy
`zalohy/investra-2026-11-18-pred-ZJ12-krok2.dump` povýšené na 37.0: přepočet obou otevřených ocenění (35, 39) dal shodné FK, úplaty, kapitály
i kurzy; kopie smazána. Referenční výpočet `tools/nav_reference` doplněn o daňový efekt tříd (nový test, scénáře s1–s3 a s5 beze změny).

**Scénář s4 ke schválení** (Martin; v pracovním stromu, necommitováno): daňový efekt výkonnostní odměny třídy A, přírůstkový přesun. Odoo i `tools/nav_reference` shodně:

| Datum | Položka | Dosud | Nově |
|---|---|---|---|
| 31. 1. | přesun daňového efektu A / B | – | +241,08 / −241,08 (0,05 × (9 643,29 − 0,5 × 9 643,29)) |
| 31. 1. | kapitál A / B | 1 036 403,41 / 1 046 046,70 | 1 036 644,49 / 1 045 805,62 |
| 31. 1. | kurz A / B | 1 036,4034 / 1 046,0467 | 1 036,6444 / 1 045,8056 |
| 28. 2. | odměna A (doplatek) | −7 708,86 | −7 662,34 (lednový přesun zvýšil hodnotu A) |
| 28. 2. | daň (doplatek) | −3 268,94 | −3 271,26 |
| 28. 2. | přesun A / B | – | −192,40 / +192,40 (ΔE_A = 0,05 × (1 980,95 − 9 643,29) = −383,117; × (1 − ρ_A 0,4978004)) |
| 28. 2. | FK | 2 020 340,32 | 2 020 296,12 |
| 28. 2. | kapitál A / B | 1 009 364,60 / 1 010 975,72 | 1 009 359,83 / 1 010 936,29 |
| 28. 2. | kurz A / B | 1 009,3646 / 1 010,9757 | 1 009,3598 / 1 010,9362 |

**Daň v základu odměny (B.3, 2026-11-18):** `_earlier_fee_items` vrací i řádky daně (krok 4): třída nesla ρ_c(ocenění) × pohyb daně − přesun_c
(přesuny z detailu, starší řádky jen poměrem); `_tax_item` je vynechá. `_borne_since(třída, D, měřítko, kusy, kroky)` nahrazuje `_fees_borne_since`:
odměna po kroku 1 přičte úplaty i daň, po kroku 2 daň, po kroku 4 nic; detail odměny má `added_fees` a `added_tax`. Testy: úpis do B (únor 0 místo −400),
odměna s daní přes krystalizaci (přičtení 0 / 4 000 / 4 000 / 0 po 31. 3.), krok 4 nic nepřičítá, přesuny v každém ocenění přesně 0 a FK = kapitál + výsledek
− náklady (tři třídy, tři ocenění). `tools/nav_reference`: odměna (jen krok 2) přičítá nesenou daň, nový ruční test. `investra_nav` 452/452,
`investra_nav+` 526/526. Kopie zálohy povýšená na 37.0: ocenění 35 a 39 beze změny (FK, úplaty, kapitály, kurzy).

**Scénář s4 – schválená druhá verze** (Martin 18. 11. 2026; přírůstkový přesun a daň v základu odměny); nahrazuje předchozí návrh.

| Datum | Položka | Dosud (commit) | Nově |
|---|---|---|---|
| 31. 1. | přesun A / B | – | +241,08 / −241,08 |
| 31. 1. | kapitál A / B | 1 036 403,41 / 1 046 046,70 | 1 036 644,49 / 1 045 805,62 |
| 31. 1. | kurz A / B | 1 036,4034 / 1 046,0467 | 1 036,6444 / 1 045,8056 |
| 28. 2. | odměna A | −7 708,86 | −7 276,61 (přičtena lednová daň A 0,5 × 4 339,48 − 241,08 = 1 928,66) |
| 28. 2. | daň | −3 268,94 | −3 290,55 |
| 28. 2. | přesun A / B | – | −182,72 / +182,72 (ΔE_A = 0,05 × (2 366,68 − 9 643,29) = −363,83; × (1 − 0,4978004)) |
| 28. 2. | FK | 2 020 340,32 | 2 019 929,68 |
| 28. 2. | kapitál A / B | 1 009 364,60 / 1 010 975,72 | 1 008 993,39 / 1 010 936,29 |
| 28. 2. | kurz A / B | 1 009,3646 / 1 010,9757 | 1 008,9933 / 1 010,9362 |

## Plán kroku 4 (technický návrh schválen 2026-11-18; věcně rozhodnuto B.7–B.10)

1. **Převzaté opravy** `_carried_corrections()`: řádky oprav s platností „do konce období“ z `_earlier_valuations(D)`, součet podle (pravidlo, třída, cíl);
   D = `perf_base_date` u odměny, 31. 12. předchozího roku u daně a opravy základu průměrného FK. **Ukončení** = nová oprava o −převzatou částku
   s povinnou poznámkou a odkazem `ended_id` („Ukončuje opravu“) na ukončovanou; tím součet klesne na 0 a další ocenění ji nepřevezme.
   `origin_id` („Převzato z“) zůstává jen pro převzetí z verze (B.10), kontroly i protokol je rozlišují.
2. **Dva průchody** `_apply_fees`: (1) bez jakýchkoli oprav (nových i převzatých) = Vypočteno do detailu; (2) `pinned[klíč]` = vypočteno + převzaté + nové
   u oprav částky; oprava základu nepinuje, přičte se do základu položky (daň: výsledek; průměrný FK: průměr, převzatá do konce roku; FK a kapitál
   třídy: jen toto ocenění). Ostatní pravidla se dopočítají k pevným částkám.
3. **Naběhlá odměna** `perf_accrued` včetně oprav: „jen toto ocenění“ se dalším oceněním samo vrátí (požadovaný stav bez opravy), „do konce období“ drží
   převzetí; při krystalizaci se oprava stane součástí splatné odměny a převzetí začne znovu. Daň: zaúčtovaná daň v knize opravu obsahuje, konec roku ji ukončí.
4. **Daňový efekt:** opravy odměny a úplat tříd jsou specifické položky (plátce-třída); oprava daně ne (plátce fond).
5. **Kontroly a stopa (B.8, B.9):** stop D4 jen pro opravy zadané v tomto ocenění (`computed_at_entry` ≠ Vypočteno), metody `action_keep_difference`
   a `action_keep_result` (aktualizují snímek a přepočtou); stop při změně druhu/tříd/archivaci opraveného pravidla (`_check_correction` při výpočtu);
   upozornění „Převzaté opravy (n)“, „Oprava jen pro toto ocenění skončila“, „Minulé ocenění mělo opravu základu u pravidla X“; seznam oprav v poznámce
   kroků Spočítání a Odeslání ke schválení. Pojistka `_check_fee_steps` zaniká.
6. **Převzetí z verze (B.10)** `action_copy_from_version`: kopíruje jen řádky zadané ve vrácené verzi (ruční úpravy a opravy, nová kopie přílohy, `origin_id`),
   převzaté opravy ne (vzniknou znovu výpočtem).
7. **Archivace pravidla odměny nebo daně:** `write(active=False)` se zastaví při nenulové naběhlé nebo zaúčtované částce z posledního ocenění; test, že
   archivované pravidlo naběhlou částku přestane rozpouštět (důvod pojistky).
8. **Části a commity:** 4a převzaté opravy částky a dva průchody (odměna, daň, úplaty) · 4b oprava základu · 4c kontroly, upozornění, Ponechat rozdíl/výsledek ·
   4d stopa a převzetí z verze · 4e pojistka archivace. Každá část s testy `investra_nav`, před sloučením `investra_nav+`. Tlačítka a dialog v UI krok 5.
   Překryv ZJ-07 × DA-01 krok 4 neblokuje: oprava základu daně podle ZJ-12, vztah k daňovému profilu počká (Martin 18. 11. 2026).

## Zjištění kroku 4 (2026-11-18)

**4a – převzaté opravy částky a dva průchody.** Oprava odměny je položka kroku 3 (plátce třída), oprava daně položka kroku 4 (plátce fond,
v engine je daní jen položka s `tax`). `_carried_corrections(pravidlo, třída, od)`: opravy „do konce období“ z dřívějších ocenění (odměna od
`perf_base_date`, daň od 1. 1.); opravené pravidlo má pevnou částku vypočteno (průchod bez oprav) + převzaté, nové opravy jsou samostatné
pevné položky a mají vlastní doklad (odměna: závazek z odměny; daň: účty daně, „Oprava daně …“). Řádek pravidla zaúčtuje vypočteno + převzaté
(detail `computed`, `carried`, `carried_ids`); naběhlá odměna se ukládá včetně oprav. Ukončení: `end_correction(řádek, poznámka)` založí opravu
o −částku s `ended_id` (pole „Ukončuje opravu“, kontrola `_check_ending`: stejné pravidlo, třída a cíl, dřívější ocenění téhož fondu, platnost
„do konce období“, jen jednou). Pojistka `_check_fee_steps` odmítá už jen opravu základu (do 4b). Hranice: když je opravená odměna i daň
zároveň, daň je pevná z průchodu bez oprav a na opravu odměny už nereaguje (podle B.7 „opravená pravidla mají pevnou částku“).
Testy `test_fee_carried.py` (9): převzetí odměny, „jen toto ocenění“ se vrátí, krystalizace oprava zaplatí a převzetí ukončí (splatná 19 000),
ukončení a jeho kontroly, daň převzatá a „jen toto ocenění“, oprava daně bez daňového efektu, oprava odměny jako specifická položka (přesun +225).
`investra_nav` 461/461.

**4b – oprava základu.** Řádek opravy základu nic neúčtuje (rozpis s částkou 0, detail `target: base`), přičte se k základu položky:
daň k základu (engine `_tax`: `base_correction`), převzatá od 1. 1.; průměrný FK k celoročnímu průměru, převzatá od 1. 1.; odměna k hodnotě
třídy, převzatá od krystalizace; úplata ze stavu k datu (FK, kapitál třídy, aktiva) jen v tomto ocenění, další ocenění upozorní kontrolou
`base_correction_ended` („Minulé ocenění mělo opravu základu u pravidla X“). Úplata bez základu opravu základu odmítne. **Upřesnění plánu:**
oprava základu je vstup výpočtu, uplatní se i v průchodu „Vypočteno“ (ten vynechává jen opravy částky); jinak by oprava částky téhož pravidla
opravu základu tiše přebila. Pojistka `_check_fee_steps` zrušena (s testem kroku 2). Testy (+5): daň převzatá do konce roku a v novém roce
ne, průměr převzatý (rozdíl = rozdíl lednového FK + oprava), stav k datu jen jedno ocenění s upozorněním, odměna převzatá, úplata bez základu.
`investra_nav` 465/465.

## Výsledek

## Převzetí
