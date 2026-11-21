# Podklad ZJ-25: katalog kontrol ocenění

Zdroj: větev `origin/ukol/ZJ-24-hlasky-a-sazby`, commit `dc1a404`. Čteno přes `git show`, nic neměněno.
Zkratky souborů: **NAV** = `addons/custom/investra_nav/models/valuation.py`, **DER** = `addons/custom/investra_derivative/models/valuation.py`.
Řádky v tabulce = řádek volání `self._check(` na uvedené větvi.

Nalezeno **44 kódů** (39 v NAV, 5 v DER; jiné moduly `_check(` pro ocenění nevolají) + 1 nový `class_split` = **45**.
Závažnost dnes: 14 × stop, 30 × upozornění (`warning`). Stav `stop` blokuje jen `action_submit` (NAV ř. 2581, `STOPPING = ("stop",)` ř. 23).

## 1. Kde a v jakém pořadí kontroly vznikají

`action_compute` → `_compute_all` (NAV ř. 473) → `_clear()` (ř. 392–397: `self.check_ids.unlink()`; DER ř. 47 přidává `derivative_line_ids.unlink()`) → … → `_apply_fees` (ř. 1738) → `_apply_scheme` → `_finish` (ř. 2120) → `_run_checks` (ř. 2305, v DER přepsáno ř. 174: nejdřív `super()`, pak 5 kontrol derivátů, jen když fond má aspoň jeden derivát) → `_run_bridge_checks` (ř. 2247).

Pořadí zakládání (= pořadí záznamů, model nemá `_order`, tj. podle `id`):
1. v `_apply_fees`: `correction_changed` (přes `_capture_computed`), `tax_no_rule`, `fee_consistency`, `base_correction_ended`, `correction_once_ended` (`_check_previous_corrections`), `carried_corrections` (`_check_carried`), `fee_no_common_class`, `average_class_gap`, `version_entries_missing` (`_check_version_copies`), `tax_credit_lost` (uvnitř `_book_tax`), `correction_negative` (`_check_negative_corrections`);
2. v `_run_checks`: `classes_sum` … `lock_exception`, pak `_run_movement_checks` (`movements_posted`, `movement_fee_rate`, `movement_price`), pak `fee_overlap` … `instrument_changes`; v DER `derivative_*`;
3. v `_run_bridge_checks`: `bridge_movements`, `bridge_units`, `bridge_result`, `bridge_opening` (+ nově `class_split`).

Kontroly se tedy při každém přepočtu **celé smažou a založí znovu** (žádná aktualizace podle kódu). Pozor: `_since_previous` (ř. 2405–2410) bere `max(previous.check_ids.create_date)` předchozího ocenění jako okamžik „od minulého ocenění“ pro `second_person`, `matrix_change`, `instrument_changes` – nové podřízené záznamy (položky) na tom nic nemění, ale kontroly musí dál vznikat při výpočtu (create_date).

## 2. Katalog kontrol

Formáty: **částka** = 2 des. místa (`f"{x:.2f}"`, v UI s mezerou tisíců), **počet** = celé číslo, **kusy** = 6 des. míst, **text** = volný řetězec. „Položky“ = nové `investra.valuation.check.item` (viz kap. 5). Kde je potřeba změnit pomocnou funkci, aby vracela záznamy místo textů, je to uvedeno ve sloupci Co nesedí jako **[refaktor]**.

| kód | dnešní název | oblast | severity | Co se kontroluje | Jak opravit | Očekáváno | Skutečnost | Rozdíl | Co nesedí (položky) | soubor:řádek |
|---|---|---|---|---|---|---|---|---|---|---|
| classes_sum | Součet tříd se rovná FK | Kapitál a třídy | stop | Kapitály všech tříd po zaokrouhlení dávají dohromady kapitál fondu. | Jde o chybu výpočtu, ne vstupů: ocenění znovu spočítejte (tlačítko Spočítat); přetrvá-li, pošlete správci aplikace podrobnosti kontroly. | `fund_capital` (částka) | `sum(rounded.values())` (částka) | skutečnost − očekáváno (částka) | třídy: `investra.valuation.class` (řádky `class_line_ids`), hodnoty „kapitál {rounded[c]}“ | NAV:2306 |
| clearing_zero | Vnitřní zúčtování je za fond nulové | Kapitál a třídy | stop | Přesuny mezi třídami (vnitřní zúčtování) se za celý fond vyrovnají na nulu. | Najděte doklad s jednostranným přesunem mezi třídami na účtu role Vnitřní zúčtování (Nastavení › Účtování › Účty rolí ukáže účet) a opravte nebo stornujte ho. | `0` (částka) | `clearing` = `_role_balance("internal_clearing")` (částka) | = `clearing` | účty role `internal_clearing` (`account.account`, `Role.accounts_for(company,"internal_clearing")`) s nenulovým zůstatkem; **[refaktor]** nový `_read_group` po `account_id` jako v `_accounts_without_role` | NAV:2308 |
| positions_ledger | Pozice se rovnají hlavní knize | Portfolio a obchody | stop | Reálná hodnota nástrojů na záložce Portfolio se rovná zůstatku účtů, na kterých jsou nástroje zaúčtované. | Porovnejte záložku Portfolio ocenění se zůstatky účtů nástrojů (Nastavení › Účtování › Účty rolí); obvykle jde o ruční doklad na účet nástroje mimo obchod nebo o chybějící zařazení (Investra › Portfolio › Zařazení nástrojů). | `engine.money(positions)` (součet `fair_value` řádků portfolia mimo `kind == "bank"`, částka) | `instrument_ledger` = `_position_balance()` (částka) | skutečnost − očekáváno (částka) | nejasné: kód porovnává jen dva součty, rozdíl po pozicích nezná. Návrh: účty (`account.account`) z `mappings` v `_position_balance` se zůstatkem (**[refaktor]**); bez refaktoru „—“ | NAV:2313 |
| trades_settled | Obchody po termínu vypořádání jsou vypořádané | Portfolio a obchody | warning | Obchody, jejichž den vypořádání už nastal, jsou vypořádané. | Investra › Portfolio › Obchody: u obchodu ve stavu nevypořádaný doplňte vypořádání, případně opravte datum vypořádání. | `0` (počet) | `overdue` (počet) | = `overdue` | obchody `investra.trade`: **[refaktor]** `search_count` → `search`, hodnoty „vypořádání {settlement_date}“ | NAV:2318 |
| trades_booked | Obchody k datu jsou zaúčtované | Portfolio a obchody | stop | Každý obchod, který k datu ocenění už patří do portfolia, má zaúčtovaný doklad. | Investra › Portfolio › Obchody: obchod zaúčtujte; jde-li o neprovedený návrh, smažte ho. | `0` (počet) | `len(unbooked)` (počet) | = počet | `unbooked` (`investra.trade`), hodnoty „{instrument_id.name} {trade_date}“ | NAV:2325 |
| classification_override | Pozice bez ručně přepsané kategorie IFRS 9 | Portfolio a obchody | warning | Žádná pozice nemá ručně přepsanou účetní kategorii IFRS 9 proti rozhodovacímu stromu. | Investra › Portfolio › Zařazení nástrojů: zkontrolujte ruční kategorii (pole `category_override`) a buď ji zrušte, nebo potvrďte, že je úmyslná (upozornění zůstane pro schvalovatele). | — | `len(overridden)` (počet) | — | `overridden` (`investra.portfolio.classification`), hodnoty `display_name` | NAV:2329 |
| classification_proposal | Zařazení pozic odpovídá návrhu (způsob ocenění, role účtu) | Portfolio a obchody | warning | Způsob ocenění a role účtu u pozic odpovídají návrhu aplikace. | Investra › Portfolio › Zařazení nástrojů: u označeného zařazení vraťte způsob ocenění / roli účtu na návrh, nebo odchylku ponechte vědomě. | — | `len(deviating)` (počet) | — | `deviating` (`investra.portfolio.classification`), `display_name` | NAV:2336 |
| transit_zero | Peníze a inkasa na cestě jsou nulové | Účetnictví | warning | Na účtech peněz na cestě a inkas na cestě nezůstal k datu ocenění žádný zůstatek. | Spárujte platby s bankovním výpisem; zůstatek na účtu peněz/inkas na cestě (Nastavení › Účtování › Účty rolí) znamená nezaúčtovaný výpis nebo splátku. | `0` (částka) | `transit` (částka) | = `transit` | účty rolí `cash_in_transit` (+ `cash_in_transit_receipt`) se zůstatkem (`account.account`) **[refaktor]** | NAV:2346 |
| scheduled_repayments | Splátky splatné podle kalendáře jsou zaúčtované | Portfolio a obchody | warning | Splátky a kupóny, které byly podle kalendáře nástroje splatné do data ocenění, jsou zaúčtované. | Investra › Portfolio › Splátky nástrojů: splátku v návrhu zaúčtujte; chybí-li úplně, založte ji. | — | `len(missing)` (počet) | — | z n-tic `missing` `(i, m, d, p, n)`: nástroj `i` (`investra.instrument`), hodnoty „{datum d}: {p + n} (chybí / v návrhu)“; nejasné: druhý prvek n-tice docstring nazývá „model“, v `_missing_scheduled` jde z cyklu `for instrument, portfolio in positions` – pravděpodobně portfolio | NAV:2353 |
| accounts_role | Účty se zůstatkem mají roli (jinak chybí ve výkazech ČNB) | Účetnictví | warning | Každý účet, na kterém je k datu zůstatek, je přiřazený k roli, jinak se nedostane do výkazů ČNB. | Nastavení › Účtování › Účty rolí: účet přidejte k odpovídající roli (hlavní nebo další účet). | — | `len(unassigned)` (počet) | — | `unassigned` (`account.account`), hodnoty `display_name` + zůstatek (**[refaktor]** `_accounts_without_role` dnes zůstatek zahazuje; vracet `(account, balance)`) | NAV:2361 |
| no_foreign_drafts | K datu nejsou jiné nezaúčtované doklady | Účetnictví | warning | Kromě návrhů tohoto ocenění nejsou v knize k datu žádné nezaúčtované doklady. | Doklady v návrhu s datem do data ocenění zaúčtujte nebo smažte (seznam dokladů standardního účetnictví Odoo; nejasné, které menu je v instalaci viditelné). | `0` (počet) | `pending` (počet) | = `pending` | doklady `account.move`: **[refaktor]** `search_count` → `search`, hodnoty „{name} {date}“ | NAV:2367 |
| manual_rate | Ocenění používá jen vyhlášené kurzy | Ceny a kurzy | warning | Kurzy měn použité v ocenění jsou vyhlášené (ČNB/ECB), ne zadané ručně. | Nastavení › Účtování › Kurzy měn: po vyhlášení kurzu ruční kurz nahraďte vyhlášeným a ocenění přepočítejte; jinak ruční kurz zdůvodněte. | — | `len(manual)` (počet) | — | kurzy `investra.rate` (`record` z `_manual_rates`), hodnoty „{currency} {date}: {origin} ({reason})“ – **[refaktor]** `_manual_rates` vracet i `record` | NAV:2369 |
| price_age | Ceny nejsou starší než povolené stáří | Ceny a kurzy | warning | Žádná cena v portfoliu není starší, než dovoluje nastavení nástroje. | Investra › Portfolio › Ceny: zadejte a schvalte aktuální cenu; je-li stará cena správná, upravte u nástroje maximální stáří ceny (`max_price_age`, Nastavení › Nástroje › Nástroje). | po položkách: „≤ {limit} dní“ | po položkách: „{age} dní“ | po položkách: „{age − limit} dní“ | ceny `investra.instrument.price` (`line.price_id`) nebo nástroj; hodnoty „cena k {price_date}, stáří {age} dní (limit {limit})“ – **[refaktor]** `_stale_prices` vracet řádek | NAV:2371 |
| bond_calendar | Dluhopisy v portfoliu mají kalendář toků (jinak se nepočítá naběhlý úrok) | Portfolio a obchody | warning | Každý dluhopis v portfoliu má zadané smluvní peněžní toky, aby se počítal naběhlý úrok. | Nastavení › Nástroje › Nástroje: u dluhopisu doplňte Smluvní peněžní toky (`cashflow_ids`). | — | `len(no_calendar)` (počet) | — | `no_calendar` (`investra.instrument`), `name` | NAV:2376 |
| lock_exception | Uzamčené období nebylo otevřeno výjimkou | Schvalování | warning | Od zveřejnění minulého ocenění nikdo neotevřel uzamčené účetní období výjimkou. | Nastavení › Schvalování a audit › Výjimky z uzamčení: ověřte důvod výjimky a zda byla vrácena (stav odvolaná); informativní pro schvalovatele. | — | `len(exceptions)` (počet) | — | žádosti `investra.lock.exception.request` (`requests`), hodnoty „{user}, do {lock_date}: {reason} (požádal …, potvrdil …)“ – **[refaktor]** vracet záznamy | NAV:2379 |
| fee_overlap | Úplaty téže role nejsou zároveň na fondu a na třídách | Úplaty a daň | warning | Stejný druh nákladu (např. odměna za obhospodařování) není zároveň v pravidle celého fondu i v pravidle tříd. | Fond › záložka Úplaty (nebo Nastavení › Fondy › Pravidla úplat): ponechte úplatu jen na fondu, nebo jen na třídách. | — | `len(overlaps)` (počet) | — | pravidla `investra.fee.rule`; nejasné: `_overlaps` (fee_rule.py ř. 387) vrací jen texty – **[refaktor]** vracet i pravidla | NAV:2385 |
| price_fund_deviation | Fond používá sdílené tržní ceny | Ceny a kurzy | warning | Fond nepoužívá vlastní cenu tam, kde ke stejnému dni existuje schválená sdílená cena. | Investra › Portfolio › Ceny: vlastní cenu fondu smažte, nebo vyplňte důvod odchylky (`deviation_reason`). | po položkách: sdílená cena | po položkách: cena fondu | po položkách: rozdíl | ceny `investra.instrument.price` (`line.price_id`), hodnoty „{day}: fond {fund} / sdílená {shared} ({reason})“ – **[refaktor]** `_deviating_prices` vracet záznam | NAV:2388 |
| matrix_valuation | Ocenění schvaluje druhá osoba | Schvalování | warning | Schvalovací matice vyžaduje u schválení ocenění druhou osobu. | Nastavení › Schvalování a audit › Schvalovací matice: u řádku schválení ocenění nastavte dvě osoby. | „≥ 2 osoby“ | `rule.persons` (počet) | — | řádek matice `investra.approval.matrix` (`rule.row`), `display_name` | NAV:2392 |
| second_person | Úkony od minulého ocenění provedla druhá osoba | Schvalování | warning | Od minulého ocenění nebyl žádný úkon proveden bez druhé osoby. | Nastavení › Schvalování a audit › Úkony bez druhé osoby: projděte úkony; informativní pro schvalovatele, oprava není nutná. | — | `len(alone)` (počet) | — | záznamy `investra.approval.log` (`logs` v `_acts_without_second_person`), hodnoty „{činnost}: {record_name} ({user}, {čas})“ – **[refaktor]** vracet záznamy | NAV:2395 |
| matrix_change | Schvalovací matice se od minulého ocenění nezměnila | Schvalování | warning | Od minulého ocenění se nezměnil žádný řádek schvalovací matice. | Nastavení › Schvalování a audit › Schvalovací matice: ověřte, že změna byla schválená; informativní. | — | `len(changes)` (počet) | — | řádky `investra.approval.matrix` (`rows` v `_matrix_changes`) – **[refaktor]** vracet recordset | NAV:2398 |
| instrument_changes | Údaje nástrojů v portfoliu se od minulého ocenění nezměnily | Portfolio a obchody | warning | Od minulého ocenění se nezměnily údaje ani toky nástrojů, které fond drží. | Nastavení › Nástroje › Nástroje: v historii (chatter) nástroje ověřte změnu; informativní pro schvalovatele. | — | `len(changed)` (počet) | — | nástroj `investra.instrument` (`m.res_id` zpráv `mail.message`), hodnoty „{text změny} ({autor}, {datum})“ – **[refaktor]** | NAV:2402 |
| movements_posted | Úpisy a odkupy období jsou zaúčtované | Úpisy a odkupy | stop | Všechny úpisy a odkupy s datem v období ocenění jsou zaúčtované. | Investra › Úpisy a odkupy: pohyb v návrhu zaúčtujte, nebo smažte. | `0` (počet) | `len(draft)` (počet) | = počet | `draft` (`investra.class.movement`), `display_name` | NAV:2286 |
| movement_fee_rate | Poplatky úpisů a odkupů odpovídají sazbě třídy | Úpisy a odkupy | warning | Poplatek u úpisu či odkupu odpovídá sazbě nastavené u třídy (tolerance 0,01). | Investra › Úpisy a odkupy: opravte poplatek pohybu; je-li sazba třídy špatně, opravte ji ve třídě fondu (Nastavení › Fondy › Fondy › třída). | po položkách `fee_expected_class` (částka) | po položkách `fee_amount_class` (částka) | po položkách rozdíl (částka) | `fees` (`investra.class.movement`), hodnoty „{fee_amount_class} / {fee_expected_class}“ | NAV:2289 |
| movement_price | Úpisy a odkupy za zveřejněný kurz třídy | Úpisy a odkupy | warning | Úpisy a odkupy proběhly za zveřejněný kurz třídy. | Investra › Úpisy a odkupy: zkontrolujte kurz pohybu a důvod odchylky (pole `price_reason`). | — | `len(prices)` (počet) | — | `prices` (`investra.class.movement`), hodnoty `price_reason` | NAV:2293 |
| bridge_movements | Přemostění: FK (t−1) + úpisy − odkupy = upravený FK | Kapitál a třídy | stop | U každé třídy platí: kapitál z minulého ocenění + úpisy − odkupy = kapitál před rozdělením výsledku. | Chyba výpočtu: zkontrolujte Investra › Úpisy a odkupy (stornované a zpětně datované pohyby) a ocenění přepočítejte; přetrvá-li, pošlete podrobnosti správci. | po položkách `row["pre_capital"]` (částka) | po položkách `pre` (částka) | po položkách `pre − pre_capital` (částka); tolerance 0,01 | třídy `investra.valuation.class` (řádek ocenění pro `fund_class`), hodnoty „{code}: {pre} ≠ {pre_capital}“ | NAV:2267 |
| bridge_units | Přemostění: kusy (t−1) + úpisy − odkupy = kusy | Kapitál a třídy | stop | U každé třídy platí: kusy z minulého ocenění + upsané − odkoupené kusy = kusy k datu. | Jako u bridge_movements; typicky pohyb s kusy mimo období ocenění. | po položkách `row["units"]` (kusy) | po položkách `count` (kusy) | po položkách rozdíl (kusy); tolerance 0,000001 | `investra.valuation.class`, hodnoty „{code}: {count} ≠ {units}“ | NAV:2269 |
| bridge_result | Přemostění: upravený FK + společná a specifická změna = FK | Kapitál a třídy | stop | U každé třídy platí: kapitál před rozdělením + podíl na společném výsledku + změny jen této třídy = konečný kapitál třídy. | Chyba výpočtu; ocenění přepočítejte a pošlete podrobnosti správci. | po položkách `rounded[fund_class]` (částka) | po položkách `end` (částka) | po položkách rozdíl (částka); tolerance 0,01 | `investra.valuation.class`, hodnoty „{code}: {end} ≠ {rounded}“ | NAV:2270 |
| bridge_opening | Přemostění: součet FK (t−1) tříd = FK minulého ocenění | Kapitál a třídy | stop | Počáteční kapitály tříd dávají dohromady kapitál fondu z minulého ocenění. | Minulé ocenění bylo po zaúčtování změněno nebo přeskočeno: ověřte předchozí ocenění (pole Předchozí ocenění) a ocenění přepočítejte. | `previous_fk` (částka) | `opening` (částka) | `opening − previous_fk` (částka); tolerance 0,01 | předchozí ocenění `investra.valuation` (`self.previous_id`) | NAV:2272 |
| class_split (NOVÁ) | Rozpad tříd po účtech = přemostění | Kapitál a třídy | stop při \|rozdíl\| > 0,01 | U každé třídy součet rozpadu kapitálu třídy po účtech se rovná konečnému kapitálu třídy z přemostění. | Chyba výpočtu rozpadu: ocenění přepočítejte; přetrvá-li, pošlete správci podrobnosti (třída a účet s rozdílem). | po položkách `rounded[fund_class]` (částka) | po položkách součet rozpadu třídy (částka) | po položkách rozdíl (částka) | `investra.valuation.class`, hodnoty „{code}: rozpad {split} ≠ přemostění {rounded}“; viz kap. 7 | NAV: nová, v `_run_bridge_checks` za `bridge_opening` |
| correction_changed | Vypočtená částka opravených úplat se od zadání opravy nezměnila | Úplaty a daň | stop | Úplata, kterou někdo ručně opravil, vychází po přepočtu stejně jako v okamžiku zadání opravy. | Ocenění › záložka Ručně doložené úplaty: u opravy zvolte „Ponechat rozdíl“ nebo „Ponechat výsledek“ (případně opravu upravte) a přepočítejte. | po položkách `entry.computed_at_entry` (částka) | po položkách `computed` (částka) | po položkách rozdíl (částka) | opravy `investra.valuation.external` (`entry`), hodnoty „{rule}: při opravě {then}, nyní {now}; oprava {amount}“ | NAV:1673 |
| base_correction_ended | Oprava základu z minulého ocenění skončila | Úplaty a daň | warning | Upozorní, že oprava základu úplaty z minulého ocenění v tomto ocenění už neplatí. | Ocenění › záložka Ručně doložené úplaty: platí-li důvod dál, zadejte opravu základu znovu. | — | `len(base)` (počet) | — | `base` (`investra.valuation.external` minulého ocenění), pravidlo `corrects_rule_id.name` | NAV:1694 |
| correction_once_ended | Opravy „jen toto ocenění“ z minulého ocenění skončily | Úplaty a daň | warning | Upozorní, že opravy platné „jen pro toto ocenění“ z minulého ocenění tímto oceněním končí. | Ocenění › záložka Ručně doložené úplaty: je-li oprava potřeba i nyní, zadejte ji znovu. | — | `len(once)` (počet) | — | `once` (`investra.valuation.external`), `corrects_rule_id.name` | NAV:1699 |
| carried_corrections | Obsahuje převzaté opravy (n) – název dynamický | Úplaty a daň | warning | Upozorní, že ocenění obsahuje opravy úplat převzaté z dřívějších ocenění. | Ocenění › záložka Ručně doložené úplaty: ověřte převzaté opravy; nepatří-li sem, použijte „Ukončit opravu“. | — | `len(live)` (počet) | — | `live` (`investra.valuation.external`), hodnoty „{rule} {class} {amount} ({ocenění})“ | NAV:1714 |
| tax_no_rule | Fond má výchozí daňové pravidlo | Úplaty a daň | warning; vzniká **jen při chybě** (nikdy ok) | Fond má nastavené výchozí daňové pravidlo; bez něj se daň nepočítá. | Fond › záložka Daňová pravidla: vyberte výchozí daňové pravidlo (číselník Nastavení › Daně › Daňová pravidla). | — | — | — | fond `investra.fund` (`self.fund_id`) | NAV:1788 |
| fee_consistency | Společný dopočet úplat je konzistentní | Úplaty a daň | stop | Výpočet úplat, odměn a daně se ustálil (dopočet do sebe sedí). | Chyba výpočtu: zkontrolujte neobvyklá nastavení pravidel úplat (Fond › záložka Úplaty) a pošlete podrobnosti správci. | „≤ 1e-10“ (text) | `residual` (text `.1e`) | — | — (detail: `solved["steps"]`) | NAV:1829 |
| fee_no_common_class | Úplaty neplatí třídy bez podílu na společných položkách | Úplaty a daň | warning; jen fond s třídou `shares_common = False` | Úplatu neplatí třída, která se nepodílí na společných položkách fondu. | Fond › záložka Úplaty: z pravidla odeberte třídu bez podílu, je-li to omyl. | — | `len(wrong)` (počet) | — | dvojice `(rule, c)`: pravidlo `investra.fee.rule` (hodnoty „třída {c.code}“) | NAV:1843 |
| average_class_gap | Třídy průměrného FK jsou v pravidle bez přerušení | Úplaty a daň | warning; jen při pravidle průměrného FK s třídami | Třída v pravidle s průměrným kapitálem byla v pravidle po celý rok bez přerušení. | Fond › záložka Úplaty: zkontrolujte platnost třídy v pravidle průměrného FK; přerušení ovlivní průměr. | — | `len(gaps)` (počet) | — | `gaps` obsahuje jen `(class code, rule name)` – **[refaktor]** ukládat `(rule, fund_class)` → `investra.fee.rule` | NAV:1847 |
| correction_negative | Výsledek opravy … je záporný / Výsledek oprav úplat není záporný – název dynamický | Úplaty a daň | warning | Po opravách nevychází úplata, odměna ani daň záporně. | Ocenění › záložka Ručně doložené úplaty: opravu zmenšete nebo ukončete. | — | `len(negative)` (počet) | — | dnes `(label, value)`; **[refaktor]** při `negative.append` přidat `item["rule"]` → `investra.fee.rule`, hodnoty „{value:.2f}“ | NAV:1879 |
| tax_credit_lost | Zápočet zahraniční daně je celý využitý | Úplaty a daň | warning; jen pravidla se zápočtem (`credit_account_code`) | Zápočet zahraniční daně se celý využil a nic nepropadá. | Nastavení › Daně › Daňová pravidla: ověřte zápočet; propadlá část je skutečná ztráta, oprava jen při chybě vstupu. | po položkách `credit` (částka) | po položkách `credit_used` (částka) | po položkách `credit_lost` (částka) | řádky `rows`: pravidlo `investra.tax.rule` (`row["tax_rule"]` = id) | NAV:2073 |
| version_entries_missing | Předchozí verze měla ruční úpravy (n), které v této verzi nejsou – název dynamický | Úplaty a daň | warning | Ruční úpravy z vrácené předchozí verze ocenění nebyly v této verzi zapomenuty. | Ocenění › tlačítko Převzít z verze (akce `action_copy_from_version`), nebo úpravy zadejte znovu. | — | `len(missing)` (počet) | — | `missing` (`investra.valuation.external` předchozí verze) | NAV:2712 |
| derivative_settled | Nohy derivátů po datu vypořádání jsou vypořádané | Portfolio a obchody | stop; jen fond s deriváty | Nohy derivátů, jejichž den vypořádání nastal, jsou vypořádané. | Investra › Portfolio › Deriváty: u smlouvy proveďte vypořádání nohy. | `0` (počet) | `len(overdue)` (počet) | = počet | `overdue` (`investra.derivative.leg`) → otevírat smlouvu `investra.derivative` (`leg.derivative_id`), hodnoty „({settlement_date})“ | DER:184 |
| derivative_rate | Deriváty mají kurz měny k datu ocenění | Ceny a kurzy | stop; jen fond s deriváty | Pro všechny deriváty je k datu ocenění kurz měny. | Nastavení › Účtování › Kurzy měn: doplňte kurz k datu ocenění a přepočítejte. | — | `len(missing)` (počet) | — | `missing` (`investra.valuation.derivative`) → `derivative_id` (`investra.derivative`), hodnoty `problem` | DER:188 |
| derivative_manual_evidence | Ruční hodnoty derivátů mají přílohu nebo důvod | Ceny a kurzy | stop; jen fond s deriváty | Každá ručně zadaná hodnota derivátu má přiložený doklad nebo napsaný důvod. | Investra › Portfolio › Deriváty › smlouva › záložka Ruční hodnoty: přiložte dokument nebo vyplňte důvod. | — | `len(undocumented)` (počet) | — | `undocumented.derivative_id` (`investra.derivative`) | DER:191 |
| derivative_manual_difference | Ruční hodnoty derivátů odpovídají spočtené hodnotě v toleranci | Ceny a kurzy | warning; jen fond s deriváty | Ručně zadaná hodnota derivátu se od spočtené neliší víc, než dovoluje tolerance fondu. | Investra › Portfolio › Deriváty › záložka Ruční hodnoty: ověřte hodnotu; toleranci nastavíte ve formuláři fondu (pole Tolerance ruční hodnoty derivátu (% nominálu)). | po položkách `computed_value` (částka) | po položkách `manual_value` (částka) | po položkách `difference` (částka); limit `nominal × tolerance` | `deviating.derivative_id` (`investra.derivative`) | DER:195 |
| derivative_draft | Deriváty sjednané do data ocenění nejsou v návrhu | Portfolio a obchody | warning; jen fond s deriváty | Deriváty sjednané do data ocenění nezůstaly v návrhu. | Investra › Portfolio › Deriváty: smlouvu potvrďte (sjednejte), nebo smažte. | `0` (počet) | `len(drafts)` (počet) | = počet | `drafts` (`investra.derivative`), hodnoty „({trade_date})“ | DER:202 |

Počty podle oblasti: Kapitál a třídy 7 (vč. class_split), Portfolio a obchody 10, Ceny a kurzy 6, Úpisy a odkupy 3, Úplaty a daň 12, Účetnictví 3, Schvalování 4.

Pravidlo pro „Očekáváno/Skutečnost/Rozdíl“ u kontrol s položkami: na kontrole vyplnit **jen** tam, kde je jedna souhrnná hodnota (sloupce bez „po položkách“). U „po položkách“ nechat pole kontroly prázdná a hodnoty dát do `values` položky („očekáváno X, skutečnost Y, rozdíl Z“). U „počet“ s očekáváním `0` vyplnit expected „0“, actual počet; difference prázdné.

## 3. Dnešní model `investra.valuation.check`

NAV ř. 3383–3392 (třída `InvestraValuationCheck`), `_description = "Kontrola ocenění"`, bez `_order`:

| pole | typ | string | poznámka |
|---|---|---|---|
| valuation_id | Many2one `investra.valuation` | Ocenění | required, `ondelete="cascade"`, index |
| company_id | Many2one related `valuation_id.company_id` | – | store, index |
| code | Char | Kód | required |
| name | Char | Kontrola | required |
| status | Selection `ok` „V pořádku“ / `warning` „Upozornění“ / `stop` „Stop“ | Výsledek | required |
| detail | Char | Podrobnosti | |

`check_ids = fields.One2many("investra.valuation.check", "valuation_id", readonly=True, string="Kontroly")` (NAV ř. 201); `check_ids` je v `SYSTEM_FIELDS` (ř. 26–29). Zakládá se jen v `_check` (NAV ř. 2296–2303) přes `sudo().create`, `detail` = `str(detail)` (tj. i čísla). Přístup: `security/ir.access.csv` ř. 30–31 (`access_val_check_read` čtení pro `account.group_account_readonly`; pravidlo firmy `investra_val_check_rule`). Kód kontroly dále čte jen `_corrections_summary` (NAV ř. 290, `code == "carried_corrections"` → bere `name`). Balíček pro depozitáře ani otisk snímku kontroly neobsahují.

## 4. Záložka Kontroly a dashboard

* Formulář: `addons/custom/investra_nav/views/nav_views.xml`, záznam `view_valuation_form` (ř. 208), ř. 378:
  `<page string="Kontroly"><field name="check_ids"><list><field name="name"/><field name="status"/><field name="detail"/></list></field></page>` – stránka **nemá `name`**.
  XPath: `//page[@string='Kontroly']` nebo `//field[@name='check_ids']`. Zděděný `view_valuation_form_class_price_chart` (ř. 447) dělá `<xpath expr="//field[@name='check_ids']" position="before">` (ř. 503) a vkládá skupinu s `neutral_capital` – pole `check_ids` musí na stránce zůstat. Doporučení: přidat stránce `name="checks"` v základním pohledu a nové věci cílit `//page[@name='checks']`.
* Dashboard `addons/custom/investra_dashboard/models/dashboard.py`:
  * `_dashboard_exceptions` (ř. 244–270): na „kontrolovaném“ ocenění (rozpracované další, jinak poslední zaúčtované nezveřejněné, ř. 131–132) spočítá `check_ids` se `status == "stop"` → text „Kontroly se stopem: n“ (danger), `== "warning"` → „Kontroly s upozorněním: n“ (warning); výsledek do `dashboard_exceptions` / `dashboard_exception_count` (ř. 98–99, 170–171).
  * `action_open_checks` (ř. 504–519): okno `investra.valuation.check`, doména `[("valuation_id","=",…),("status","!=","ok")]`, `views [(False,"list")]`, `create: False`.
  * Pohled seznamu `view_valuation_check_dashboard_list` v `investra_dashboard/views/dashboard_views.xml` ř. 142–150 (priorita 50; sloupce `id` volitelně, `valuation_id`, `name`, `status` badge, `detail`). Je to jediný list pohled modelu, proto ho `(False,"list")` použije. Odkaz z karty: `dashboard_views.xml` ř. 108–112.
  * Dashboard kód (`code`) ani oblast nepoužívá. Návrh pro ZJ-25: do seznamu přidat `area` (a `groupby` oblast v kontextu akce `{"group_by": "area"}` – volitelné), `what`, `expected`, `actual`, `difference`.

## 5. Návrh nových polí a modelu položek

V `InvestraValuationCheck` (NAV, nebo přesunout do nového `models/valuation_check.py` – rozhodnutí na implementaci; import v `models/__init__.py`):

```python
from .check_catalog import CHECK_AREAS, CHECK_CATALOG

area = fields.Selection(CHECK_AREAS, compute="_compute_catalog", store=True, string="Oblast",
                        help="Oblast kontroly podle katalogu kontrol (check_catalog.py).")
what = fields.Char(compute="_compute_catalog", string="Co se kontroluje",
                   help="Srozumitelný popis kontroly z katalogu; mění se s katalogem i u starších ocenění.")
how = fields.Char(compute="_compute_catalog", string="Jak opravit",
                  help="Kde v aplikaci chybu opravit (nabídka, formulář, pole).")
expected = fields.Char(readonly=True, string="Očekáváno", help="Hodnota, která by měla vyjít (formátovaný text).")
actual = fields.Char(readonly=True, string="Skutečnost", help="Hodnota, která vyšla (formátovaný text).")
difference = fields.Char(readonly=True, string="Rozdíl", help="Skutečnost − očekáváno (formátovaný text).")
item_ids = fields.One2many("investra.valuation.check.item", "check_id", readonly=True, string="Co nesedí",
                           help="Položky, které kontrolu nesplnily; řádek otevře záznam.")
item_count = fields.Integer(compute="_compute_item_count", string="Počet položek")

@api.depends("code")
def _compute_catalog(self):
    for check in self:
        area, what, how = CHECK_CATALOG.get(check.code, (False, check.name, ""))
        check.area, check.what, check.how = area, what, how
```
(`what`/`how` nestored, aby se oprava textu v katalogu projevila hned; `area` stored kvůli seskupení/filtru.)

Nový model:

```python
class InvestraValuationCheckItem(models.Model):
    _name = "investra.valuation.check.item"
    _description = "Položka kontroly ocenění"
    _order = "check_id, sequence, id"

    check_id = fields.Many2one("investra.valuation.check", required=True, ondelete="cascade", index=True, string="Kontrola")
    company_id = fields.Many2one(related="check_id.company_id", store=True, index=True)
    sequence = fields.Integer(string="Pořadí")
    name = fields.Char(required=True, string="Položka", help="Název záznamu, který nesedí (nástroj, obchod, třída, doklad …).")
    values = fields.Char(string="Hodnoty", help="Co u položky nesedí, např. „očekáváno 100,00, skutečnost 99,50, rozdíl −0,50“.")
    res_model = fields.Char(string="Model záznamu", help="Technický model záznamu, který položka otevře.")
    res_id = fields.Many2oneReference(model_field="res_model", string="Id záznamu")

    def action_open(self):
        self.ensure_one()
        if not (self.res_model and self.res_id):
            return False
        return {"type": "ir.actions.act_window", "res_model": self.res_model, "res_id": self.res_id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}
```
Vzor `Many2oneReference(model_field="res_model")` už v repozitáři je (`investra_posting/models/event.py` ř. 51). Do `security/ir.access.csv` přidat analogicky k ř. 30–31: `access_val_check_item_read,…,investra.valuation.check.item,account.group_account_readonly,r,` a pravidlo firmy `investra_val_check_item_rule,…,crud,"[('company_id', 'in', company_ids)]"`. Otevření záznamu bez práva čtení skončí standardní chybou přístupu – nejasné, zda chcete `action_open` předem ověřovat `check_access("read")`.

Rozšíření `_check` (zpětně kompatibilní; všechna dnešní volání poziční/`severity=` zůstanou platná, DER beze změny funguje):

```python
def _check(self, code, name, ok, detail="", severity="stop", expected=None, actual=None, difference=None, items=None):
    """items: iterovatelné dicty {"record": <recordset jednoho záznamu>, "name"?: str, "values"?: str}
    nebo {"name": str, "values"?: str, "res_model"?: str, "res_id"?: int}. Položky se ukládají jen u nesplněné kontroly.
    expected/actual/difference: str se uloží beze změny, Decimal/float/int se formátuje helperem _check_format."""
    commands = []
    for index, item in enumerate([] if ok else (items or [])):
        record = item.get("record")
        commands.append((0, 0, {
            "sequence": index,
            "name": item.get("name") or (record.display_name if record else "-"),
            "values": item.get("values") or False,
            "res_model": record._name if record else item.get("res_model") or False,
            "res_id": record.id if record else item.get("res_id") or False,
        }))
    fmt = self._check_format
    self.env["investra.valuation.check"].sudo().create({
        "valuation_id": self.id, "code": code, "name": name, "status": "ok" if ok else severity, "detail": str(detail),
        "expected": fmt(expected), "actual": fmt(actual), "difference": fmt(difference), "item_ids": commands,
    })

def _check_format(self, value):
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return formatLang(self.env, float(value), digits=2)  # odoo.tools.misc.formatLang, česká čísla
```
`detail` ponechat (zpětná kompatibilita, dashboard seznam, `_corrections_summary`). Pole kontroly se plní jen tam, kde je ve sloupcích tabulky název proměnné; kusy formátovat volajícím jako text (6 míst).

Pohled (nav_views.xml ř. 378) – návrh nové stránky:
```xml
<page string="Kontroly" name="checks"><field name="check_ids"><list>
    <field name="area" optional="show"/><field name="name"/><field name="status" widget="badge"
        decoration-success="status == 'ok'" decoration-warning="status == 'warning'" decoration-danger="status == 'stop'"/>
    <field name="expected" optional="show"/><field name="actual" optional="show"/><field name="difference" optional="show"/>
    <field name="item_count" optional="show"/><field name="detail" optional="hide"/>
</list><form><group><field name="what"/><field name="how"/><field name="expected"/><field name="actual"/><field name="difference"/><field name="detail"/></group>
    <field name="item_ids"><list><field name="name"/><field name="values"/><button name="action_open" type="object" string="Otevřít"/></list></field>
</form></field></page>
```

## 6. `models/check_catalog.py` (nový soubor, hotový obsah)

```python
"""Katalog kontrol ocenění (ZJ-25): oblast, co se kontroluje a jak opravit. Texty pro účetní, ne pro programátora."""

CHECK_AREAS = [
    ("capital", "Kapitál a třídy"),
    ("portfolio", "Portfolio a obchody"),
    ("prices", "Ceny a kurzy"),
    ("movements", "Úpisy a odkupy"),
    ("fees", "Úplaty a daň"),
    ("accounting", "Účetnictví"),
    ("approval", "Schvalování"),
]

CHECK_CATALOG = {
    # Kapitál a třídy
    "classes_sum": ("capital", "Kapitály všech tříd po zaokrouhlení dávají dohromady kapitál fondu.",
                    "Jde o chybu výpočtu, ne vstupů: ocenění znovu spočítejte; přetrvá-li, pošlete správci aplikace podrobnosti kontroly."),
    "clearing_zero": ("capital", "Přesuny mezi třídami (vnitřní zúčtování) se za celý fond vyrovnají na nulu.",
                      "Najděte doklad s jednostranným přesunem mezi třídami na účtu role Vnitřní zúčtování (Nastavení › Účtování › Účty rolí) a opravte nebo stornujte ho."),
    "bridge_movements": ("capital", "U každé třídy: kapitál z minulého ocenění + úpisy − odkupy = kapitál před rozdělením výsledku.",
                         "Zkontrolujte Investra › Úpisy a odkupy (stornované a zpětně datované pohyby) a ocenění přepočítejte; přetrvá-li, pošlete podrobnosti správci."),
    "bridge_units": ("capital", "U každé třídy: kusy z minulého ocenění + upsané − odkoupené kusy = kusy k datu.",
                     "Zkontrolujte Investra › Úpisy a odkupy, zda některý pohyb s kusy není mimo období ocenění, a ocenění přepočítejte."),
    "bridge_result": ("capital", "U každé třídy: kapitál před rozdělením + podíl na společném výsledku + změny jen této třídy = konečný kapitál.",
                      "Chyba výpočtu: ocenění přepočítejte; přetrvá-li, pošlete podrobnosti správci aplikace."),
    "bridge_opening": ("capital", "Počáteční kapitály tříd dávají dohromady kapitál fondu z minulého ocenění.",
                       "Ověřte, že pole Předchozí ocenění ukazuje správné zaúčtované ocenění a že nebylo dodatečně změněno; pak přepočítejte."),
    "class_split": ("capital", "U každé třídy se součet rozpadu kapitálu po účtech rovná konečnému kapitálu třídy z přemostění.",
                    "Chyba výpočtu rozpadu: ocenění přepočítejte; přetrvá-li, pošlete správci třídu a účet s rozdílem."),
    # Portfolio a obchody
    "positions_ledger": ("portfolio", "Reálná hodnota nástrojů na záložce Portfolio se rovná zůstatku účtů, na kterých jsou nástroje zaúčtované.",
                         "Porovnejte záložku Portfolio se zůstatky účtů nástrojů (Nastavení › Účtování › Účty rolí); obvykle jde o ruční doklad na účet nástroje nebo chybějící zařazení (Investra › Portfolio › Zařazení nástrojů)."),
    "trades_settled": ("portfolio", "Obchody, jejichž den vypořádání už nastal, jsou vypořádané.",
                       "Investra › Portfolio › Obchody: doplňte vypořádání obchodu, případně opravte datum vypořádání."),
    "trades_booked": ("portfolio", "Každý obchod, který k datu ocenění patří do portfolia, má zaúčtovaný doklad.",
                      "Investra › Portfolio › Obchody: obchod zaúčtujte; jde-li o neprovedený návrh, smažte ho."),
    "classification_override": ("portfolio", "Žádná pozice nemá ručně přepsanou účetní kategorii IFRS 9.",
                                "Investra › Portfolio › Zařazení nástrojů: ruční kategorii zrušte, nebo ji ponechte vědomě (schvalovatel upozornění uvidí)."),
    "classification_proposal": ("portfolio", "Způsob ocenění a role účtu u pozic odpovídají návrhu aplikace.",
                                "Investra › Portfolio › Zařazení nástrojů: vraťte způsob ocenění nebo roli účtu na návrh, nebo odchylku ponechte vědomě."),
    "scheduled_repayments": ("portfolio", "Splátky a kupóny splatné podle kalendáře do data ocenění jsou zaúčtované.",
                             "Investra › Portfolio › Splátky nástrojů: splátku v návrhu zaúčtujte; chybí-li, založte ji."),
    "bond_calendar": ("portfolio", "Každý dluhopis v portfoliu má smluvní peněžní toky, aby se počítal naběhlý úrok.",
                      "Nastavení › Nástroje › Nástroje: u dluhopisu doplňte Smluvní peněžní toky."),
    "instrument_changes": ("portfolio", "Od minulého ocenění se nezměnily údaje ani toky nástrojů, které fond drží.",
                           "Nastavení › Nástroje › Nástroje: v historii nástroje ověřte, že změna je správná; jen pro informaci schvalovatele."),
    "derivative_settled": ("portfolio", "Nohy derivátů, jejichž den vypořádání nastal, jsou vypořádané.",
                           "Investra › Portfolio › Deriváty: u smlouvy proveďte vypořádání nohy."),
    "derivative_draft": ("portfolio", "Deriváty sjednané do data ocenění nezůstaly v návrhu.",
                         "Investra › Portfolio › Deriváty: smlouvu potvrďte, nebo smažte."),
    # Ceny a kurzy
    "manual_rate": ("prices", "Kurzy měn použité v ocenění jsou vyhlášené, ne zadané ručně.",
                    "Nastavení › Účtování › Kurzy měn: ruční kurz nahraďte vyhlášeným a přepočítejte, nebo ho zdůvodněte."),
    "price_age": ("prices", "Žádná cena v portfoliu není starší, než dovoluje nastavení nástroje.",
                  "Investra › Portfolio › Ceny: zadejte a schvalte aktuální cenu; je-li stará cena správná, upravte u nástroje maximální stáří ceny."),
    "price_fund_deviation": ("prices", "Fond nepoužívá vlastní cenu tam, kde existuje schválená sdílená cena ke stejnému dni.",
                             "Investra › Portfolio › Ceny: vlastní cenu fondu smažte, nebo vyplňte důvod odchylky."),
    "derivative_rate": ("prices", "Pro všechny deriváty je k datu ocenění kurz měny.",
                        "Nastavení › Účtování › Kurzy měn: doplňte kurz k datu ocenění a přepočítejte."),
    "derivative_manual_evidence": ("prices", "Každá ručně zadaná hodnota derivátu má přiložený doklad nebo důvod.",
                                   "Investra › Portfolio › Deriváty › záložka Ruční hodnoty: přiložte dokument nebo vyplňte důvod."),
    "derivative_manual_difference": ("prices", "Ruční hodnota derivátu se od spočtené neliší víc, než dovoluje tolerance fondu.",
                                     "Investra › Portfolio › Deriváty › záložka Ruční hodnoty: ověřte hodnotu; toleranci nastavíte ve formuláři fondu (Tolerance ruční hodnoty derivátu)."),
    # Úpisy a odkupy
    "movements_posted": ("movements", "Všechny úpisy a odkupy s datem v období ocenění jsou zaúčtované.",
                         "Investra › Úpisy a odkupy: pohyb v návrhu zaúčtujte, nebo smažte."),
    "movement_fee_rate": ("movements", "Poplatek u úpisu či odkupu odpovídá sazbě třídy.",
                          "Investra › Úpisy a odkupy: opravte poplatek pohybu; je-li špatně sazba, opravte ji u třídy fondu."),
    "movement_price": ("movements", "Úpisy a odkupy proběhly za zveřejněný kurz třídy.",
                       "Investra › Úpisy a odkupy: zkontrolujte kurz pohybu a důvod odchylky."),
    # Úplaty a daň
    "correction_changed": ("fees", "Ručně opravená úplata vychází po přepočtu stejně jako při zadání opravy.",
                           "Ocenění › Ručně doložené úplaty: u opravy zvolte „Ponechat rozdíl“ nebo „Ponechat výsledek“ a přepočítejte."),
    "base_correction_ended": ("fees", "Oprava základu úplaty z minulého ocenění v tomto ocenění už neplatí.",
                              "Ocenění › Ručně doložené úplaty: platí-li důvod dál, zadejte opravu základu znovu."),
    "correction_once_ended": ("fees", "Opravy „jen toto ocenění“ z minulého ocenění tímto oceněním skončily.",
                              "Ocenění › Ručně doložené úplaty: je-li oprava potřeba i nyní, zadejte ji znovu."),
    "carried_corrections": ("fees", "Ocenění obsahuje opravy úplat převzaté z dřívějších ocenění.",
                            "Ocenění › Ručně doložené úplaty: převzaté opravy ověřte; nepatří-li sem, použijte Ukončit opravu."),
    "tax_no_rule": ("fees", "Fond má výchozí daňové pravidlo; bez něj se daň nepočítá.",
                    "Fond › záložka Daňová pravidla: vyberte výchozí daňové pravidlo."),
    "fee_consistency": ("fees", "Výpočet úplat, odměn a daně se ustálil.",
                        "Chyba výpočtu: zkontrolujte neobvyklá nastavení pravidel (Fond › záložka Úplaty) a pošlete podrobnosti správci."),
    "fee_no_common_class": ("fees", "Úplatu neplatí třída, která se nepodílí na společných položkách fondu.",
                            "Fond › záložka Úplaty: z pravidla odeberte třídu bez podílu, je-li to omyl."),
    "average_class_gap": ("fees", "Třída v pravidle s průměrným kapitálem byla v pravidle celý rok bez přerušení.",
                          "Fond › záložka Úplaty: zkontrolujte platnost třídy v pravidle průměrného FK."),
    "correction_negative": ("fees", "Po opravách nevychází úplata, odměna ani daň záporně.",
                            "Ocenění › Ručně doložené úplaty: opravu zmenšete nebo ukončete."),
    "tax_credit_lost": ("fees", "Zápočet zahraniční daně se celý využil a nic nepropadá.",
                        "Nastavení › Daně › Daňová pravidla: ověřte zápočet; propadlá část je skutečná ztráta, opravte jen chybu vstupu."),
    "fee_overlap": ("fees", "Stejný druh nákladu není zároveň v pravidle celého fondu i v pravidle tříd.",
                    "Fond › záložka Úplaty: ponechte úplatu jen na fondu, nebo jen na třídách."),
    "version_entries_missing": ("fees", "Ruční úpravy z předchozí verze ocenění nebyly v této verzi zapomenuty.",
                                "Ocenění › Převzít z verze, nebo úpravy zadejte znovu."),
    # Účetnictví
    "transit_zero": ("accounting", "Na účtech peněz a inkas na cestě nezůstal k datu ocenění zůstatek.",
                     "Spárujte platby s bankovním výpisem; zůstatek znamená nezaúčtovaný výpis nebo splátku."),
    "accounts_role": ("accounting", "Každý účet se zůstatkem je přiřazený k roli, jinak chybí ve výkazech ČNB.",
                      "Nastavení › Účtování › Účty rolí: přidejte účet k odpovídající roli."),
    "no_foreign_drafts": ("accounting", "Kromě návrhů tohoto ocenění nejsou v knize k datu nezaúčtované doklady.",
                          "Doklady v návrhu s datem do data ocenění zaúčtujte, nebo smažte."),
    # Schvalování
    "lock_exception": ("approval", "Od zveřejnění minulého ocenění nikdo neotevřel uzamčené období výjimkou.",
                       "Nastavení › Schvalování a audit › Výjimky z uzamčení: ověřte důvod výjimky; jen pro informaci schvalovatele."),
    "matrix_valuation": ("approval", "Schvalovací matice vyžaduje u schválení ocenění druhou osobu.",
                         "Nastavení › Schvalování a audit › Schvalovací matice: u schválení ocenění nastavte dvě osoby."),
    "second_person": ("approval", "Od minulého ocenění nebyl žádný úkon proveden bez druhé osoby.",
                      "Nastavení › Schvalování a audit › Úkony bez druhé osoby: projděte úkony; jen pro informaci schvalovatele."),
    "matrix_change": ("approval", "Od minulého ocenění se nezměnil žádný řádek schvalovací matice.",
                      "Nastavení › Schvalování a audit › Schvalovací matice: ověřte, že změna byla schválená."),
}
```
Test: `set(CHECK_CATALOG) ⊇` všech kódů z `git grep '_check("'` (45) a každá oblast je klíčem `CHECK_AREAS`.

## 7. Nová kontrola `class_split`

> **Poradce 2026-11-20:** zdroj rozpadu definuje `plan-ZJ-25-technicky.md` oddíl C; kontrolu zakládej vždy podle něj (přednost před nejasností níže).

* Kód `class_split`, název „Rozpad tříd po účtech = přemostění“, oblast `capital`, `severity="stop"`, ok když pro všechny třídy `abs(split[c] − rounded[c]) <= Decimal("0.01")`.
* Místo: `_run_bridge_checks` za `bridge_opening`; signatura rozšířit o `split` (dict `fund_class → Decimal`), volat z `_finish` (ř. 2175).
* Volání:
```python
wrong = [(c, split[c], rounded[c]) for c in context if abs(split[c] - rounded[c]) > tolerance]
lines = {line.class_id: line for line in self.class_line_ids}
self._check("class_split", "Rozpad tříd po účtech = přemostění", not wrong,
            "; ".join(f"{c.code}: {s} ≠ {r}" for c, s, r in wrong),
            items=[{"record": lines[c], "name": c.code,
                    "values": f"očekáváno {r:.2f}, rozpad {s:.2f}, rozdíl {s - r:.2f}"} for c, s, r in wrong])
```
* **nejasné:** na větvi neexistuje žádný „rozpad tříd po účtech“ (`git grep` bez výsledku; v `docs/otevrene-body.md` ř. 68 je jen otevřený bod „Rozpad ostatních položek třídy … podle rolí účtů“). Zdroj `split` musí dodat ZJ-25/26 (např. součet `_delta` po účtech + podíl na `neutral` + `fixed`). Dokud neexistuje, kontrolu nezakládat (ani jako ok).

## 8. Nejasnosti

1. `class_split`: zdroj rozpadu po účtech v kódu není (viz 7).
2. `tax_credit_lost` je uvnitř `_book_tax`, které se volá pro každou položku druhu `tax`; při více daňových položkách by vzniklo víc kontrol se stejným kódem – z kódu nejde říct, zda položka daně je vždy jedna.
3. `positions_ledger`, `clearing_zero`, `transit_zero`: rozpad rozdílu na položky dnes kód nezná; navržené položky (účty) vyžadují nový dotaz.
4. `scheduled_repayments`: význam druhého prvku n-tice z `_missing_scheduled` (docstring „model“ vs. cyklus `instrument, portfolio`).
5. `no_foreign_drafts`: konkrétní nabídka dokladů v návrhu v UI (standardní Odoo účetnictví) nebyla z modulů Investra zjistitelná.
6. Pořadí výpisu kontrol: model nemá `_order`; zda řadit podle oblasti (`_order = "area, id"`), není rozhodnuto.
