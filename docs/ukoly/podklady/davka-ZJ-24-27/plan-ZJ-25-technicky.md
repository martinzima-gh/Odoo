# ZJ-25 Ocenění – technický plán pro Sonnet (připravil poradce 2026-11-20 z kódu dc1a404; zadání oddíl 1)

**Schválil Martin 2026-11-20** (celý plán; rozpad bez ukládání – transient, rekonciliace řádku Převody přes doklady, kontroly, Portfolio).

Podklady: `podklad-katalog-kontrol.md` (44 kódů kontrol + `class_split`, model a katalog). Červená zóna; návrh je hotový zde, agent programuje podle plánu. Když kód plánu odporuje, **zastav a napiš** (neimprovizuj ve výpočtu).
Všechny nové výpočty jsou jen **zobrazení a kontrola**: nesmí změnit `fund_capital`, `class_line_ids` hodnoty, doklady ani snímek 35/39.

## A. Odvození rozpadu (proč to sedí přesně)
Z `_finish`: hodnota třídy `value_c = ratio_c × neutral + delta_c + fixed_c` (+ zbytek zaokrouhlení u jedné třídy),
`neutral = NA_t − Σ delta − Σ fixed` (`_shared_neutral`), `delta_c` = změna řádků s třídou c za období na účtech mimo equity/income/expense (`_delta`),
`shared_result_c = value_c − pre_capital_c − delta_c` (`_class_bridge`). U třídy s podílem `fixed = 0`, `ratio_c = pre_c / P`, P = Σ pre tříd s podílem.
Pak `shared_result_c = ratio_c × S + zaokrouhlení_c`, kde **společná změna fondu**
`S = neutral − P = Σ_{a∈A/L} U(a) − Σ_{a∈OB} T(a) − M + D`:
- `U(a)` = změna účtu a za období (`date > start`) z řádků **bez třídy**, jen účty `asset%`/`liability%`;
- `T(a)` = změna řádků s jakoukoli třídou na podrozvahových účtech (`off_balance`; obvykle 0 – řádek ukaž, jen když ≠ 0);
- `M` = Σ přes všechny třídy (`pre_capital − opening_capital`) = úpisy − odkupy (kapitálové pohyby, nejsou výsledek);
- `D` = Σ_{A/L} zůstatek k `start` (dnes v knize) − Σ `opening_capital` tříd = dodatečné zápisy do minulých období (obvykle 0; řádek jen když ≠ 0).
Specifická část: `delta_c = Σ_a T_c(a)` přes účty mimo equity/income/expense (A/L i off_balance), `T_c(a)` = změna řádků s třídou c.
Zaokrouhlení_c = `shared_result_c − Σ_rows money(ratio_c × common_row)` (zahrnuje i zbytek z `_finish`).
Domény řádků: přesně `self._line_domain(...)` (posted + návrhy tohoto ocenění), `date > start` (`start = _period_start()`), `date <= self.date`.

## B. Dočasný model `investra.valuation.class.account` – **TransientModel**, nic se trvale neukládá (rozhodl Martin 2026-11-20)
Důvod: zveřejněné ocenění je zamčené (`fiscalyear_lock_date`, výjimky jen přes `lock_exception.py`), rozpad jde kdykoli spočítat znovu.
Soubor `models/valuation_split.py` (do `models/__init__.py`), ACL pro `account.group_account_readonly` (čtení i zápis – transient).
Pole: `class_line_id` M2o `investra.valuation.class` required; `valuation_id` related; `mode` Selection
[("balance","Rozvaha"),("result","Podle výsledovky")]; `sequence` Integer; `group` Selection [("asset","Aktiva"),("liability","Závazky"),
("off_balance","Podrozvaha"),("capital","Kapitálové pohyby (nejsou výsledek)"),("prior","Dodatečné zápisy do minulých období"),
("income","Výnosy"),("expense","Náklady"),("equity","Vlastní kapitál a OCI"),("transfer","Převody mezi společnou částí a třídou"),
("rounding","Zaokrouhlení podílu")]; `account_id` M2o account.account (prázdné u capital/prior/transfer/rounding); `name` Char;
`common` Float(20,2) „Společné – fond“; `share` Float(20,2) „Podíl třídy“; `specific` Float(20,2) „Specifické – třída“;
`impact` Float(20,2) „Vliv na FK třídy“ (= share + specific). `_order = "mode, sequence, id"`.
Metoda `action_open_lines()` (jen když `account_id`): vrátí `ir.actions.act_window` na `account.move.line`, doména
`valuation._line_domain(("account_id","=",account), ("date",">",start), "|", ("investra_class_id","=",False), ("investra_class_id","=",class))`,
`context={"group_by": "investra_instrument_id"}`, pohled `view_move_line_class_split_list` (D2), název „Položky deníku – {účet}“.
Metoda `action_open_documents()` (jen řádek `transfer`): otevře dočasný model `investra.valuation.class.transfer` (TransientModel:
`class_line_id`, `move_id`, `date`, `source_name`, `common`, `specific`) – rekonciliace řádku Převody, viz C.

## C. Funkce `investra.valuation._class_split(self, context=None)` (v `valuation_split.py` jako `_inherit = "investra.valuation"`)
Vstup: při výpočtu `context` z `_finish` (Decimal ratio, pre_capital, fixed, opening_capital); bez něj (staré ocenění, balíček) se rekonstruuje
z `class_line_ids` (`Decimal(str(line.ratio))`, `pre_capital`, `opening_capital`, `delta`, `shared_result`; fixed = pre_capital, když ratio = 0).
Postup (jeden `_read_group` místo smyček): `groups = account.move.line._read_group(self._line_domain(("date",">",start)),
groupby=["account_id","investra_class_id"], aggregates=["balance:sum"])` a druhý `_read_group(self._line_domain(("date","<=",start),
"|", ("account_id.account_type","=like","asset%"), ("account_id.account_type","=like","liability%")), groupby=["account_id"],
aggregates=["balance:sum"])` pro D. Typ účtu u prvního dotazu ber z `account.account_type`.
Výstup: `{class_line: [row dict], ...}` s poli jako model B, pro oba `mode`; součty v Decimal, do řádků `float(engine.money(x))`.
- `balance`: skupiny asset/liability (U(a) do `common`, T_c(a) do `specific`), off_balance (common = −Σ T(a), specific = T_c(a)), capital
  (common = −M), prior (common = D, jen když ≠ 0), rounding (share = zaokrouhlení_c). `share = money(ratio_c × common)`. Řádky, kde
  common, share i specific jsou 0, vynech.
- `result`: účty `income%`, `expense%` a `equity%` **kromě** `equity_unaffected` a účtů role `class_capital`
  (`Role.accounts_for(company, "class_capital")`): common = −U(a), specific = −T_c(a); dále stejné řádky capital (−M), prior (D) a
  off_balance jako v `balance`; řádek `transfer` dorovná sloupce na součty režimu `balance` (common: S − Σ, specific: delta_c − Σ);
  rounding stejné jako v `balance`.
- **Rekonciliace řádku `transfer`** (`_class_split_transfers(class_line)`): pro každý doklad (`move_id`) období spočti tytéž dva sloupce jen
  z jeho řádků: transfer_doklad = (hodnota v režimu balance) − (hodnota v režimu result), kde M se přiřadí dokladu pohybu (`investra.class.movement`
  přes událost `res_model/res_id`) a D se nepřiřazuje (je v obou režimech stejně). Vrať jen doklady s nenulovým příspěvkem (typicky úplata třídy:
  náklad s třídou, závazek společný; přesun podle pořadí nároků; daňový efekt). **Σ dokladů = řádek `transfer`** (lineární, kontroluje test G4).
Kontrola (v `_finish` hned po `_run_bridge_checks`, funkce `_run_split_check(split, bridges)`, rozpad jen v paměti): pro každou třídu
`|Σ impact(balance) − (shared_result_c + delta_c)| ≤ 0,01` a `|Σ specific(balance) − delta_c| ≤ 0,01`; kód `class_split`, název
„Rozpad tříd po účtech = přemostění“, stop; Očekáváno = shared_result + delta, Skutečnost = Σ impact, Rozdíl; položky = třídy s rozdílem.
**Snímek**: ověř, že `docs/sql/28-snimek-oceneni.sql` kontroly nepočítá (podle katalogu ne); když ano, napiš to.
Otevření: `investra.valuation.class.action_open_split(mode)` smaže starší dočasné řádky téže třídy a uživatele, vytvoří nové z `_class_split()`
a vrátí `act_window` (list, `domain=[("id","in",ids)]`, `context={"group_by": "group"}`, název „Rozpad po účtech – {třída}“). Stav ocenění nehraje roli.

## D. Obrazovky (nav_views.xml; nový soubor `views/valuation_split_views.xml` do manifestu)
1. `view_valuation_class_form`: obsah `<sheet>` po nadpisu obal do `<notebook>`; stránka **Přemostění** = dnešní obsah beze změny; stránka
   **Účty**: krátký text „Změna společná a specifická rozepsaná po účtech. Součty odpovídají přemostění (kontrola Rozpad tříd po účtech).“,
   dvě tlačítka `action_open_split` s `context="{'split_mode': 'balance'}"` „Rozpad po účtech (rozvaha)“ a `'result'` „Podle výsledovky“.
   List dočasného modelu (`view_valuation_class_account_list`, `create="0" edit="0" delete="0"`): Skupina, Účet, Název, Společné – fond,
   Podíl třídy, Specifické – třída, Vliv na FK třídy (`sum` u čtyř částek), tlačítka řádku `action_open_lines` (fa-list, „Položky deníku“) a
   u `transfer` `action_open_documents` („Doklady“). List dokladů převodů: Datum, Doklad, Zdroj, Společné, Specifické (`sum`).
   Stránka **Úpisy a odkupy**: `movement_ids` (M2m computed: pohyby třídy `date > start`, `<= date`, ne storno) list: Datum, Pohyb, Zdroj, Kusy, Cena, Změna kapitálu.
   Stránka **Úplaty třídy**: `fee_line_ids` (M2m computed: `valuation_id.fee_line_ids` s `class_id` = třída) – použij existující list úplat.
2. `account.move.line` (inherit v investra_nav, nestored computed): `investra_class_label` Char „Třída“ (kód třídy, jinak „Společné“),
   `investra_source_name` Char „Zdroj“ (z `investra.accounting.event` s `move_id` = doklad: `env[res_model].browse(res_id).display_name`),
   metoda `action_open_source()`. List `view_move_line_class_split_list`: Datum, Doklad, Nástroj (`investra_instrument_id`), Třída, Zdroj (+ tlačítko
   „Otevřít“), Popis, Částka (`balance`, sum). Výpočet zdroje dávkově (jeden search událostí pro všechny `move_id`).
3. Model kontroly a katalog: přesně `podklad-katalog-kontrol.md` oddíl 5 (pole, model `investra.valuation.check.item`, rozšíření `_check`,
   ACL) a oddíl 6 (`check_catalog.py` doslova; 44 kódů + `class_split`). Navíc: stored computed `status_order` (stop 0, warning 1, ok 2) a
   `_order = "valuation_id, status_order, area, id"`. Kontroly označené v katalogu **[refaktor]** (pomocná funkce vrací text) uprav tak, aby
   vracela i záznamy pro `items`; výsledek kontroly (ok/stop) a `detail` se nesmí změnit. `class_split` počítá podle oddílu C tohoto plánu
   (nejasnost č. 1 podkladu je tím vyřešena). Dashboard: do `view_valuation_check_dashboard_list` přidej `area`, `expected`, `actual`, `difference`.
   Záložka **Kontroly** ocenění a odkaz v souhrnu: stránce dej `name="checks"` (XPath dědění na `check_ids` zachovej), dále podle oddílu 5 podkladu a: – pás tří čísel (computed
   `check_stop_count`, `check_warning_count`, `check_ok_count`), list seskupený podle `area` (`default_group_by` v kontextu O2m pole
   `context="{'group_by': 'area'}"`), řazení stop → warning → ok, rozbalení = formulář kontroly (Co se kontroluje, Očekáváno/Skutečnost/Rozdíl,
   O2m položek s tlačítkem Otevřít, Jak opravit). V řádku údajů pod nadpisem ocenění odkaz (button type object `action_show_checks`, otevře záložku
   Kontroly přes `context` / nebo jen přepne – když nejde, otevře list kontrol tohoto ocenění) s textem `check_summary` („Kontroly: 1 stop, 2 upozornění“),
   invisible když obojí 0.

## E. Soubor pro depozitáře (`models/package.py`)
- `_trial_balance` přepiš na `_trial_balance_split()`: posted řádky (`parent_state = posted`), `date <= self.date`; per účet: zůstatek k `start`
  (`date <= start`), pohyb `date > start` bez třídy, pohyb po třídách (sloupec pro každou třídu fondu podle kódu), pohyb celkem, zůstatek k datu.
  Jen účty se zůstatkem nebo pohybem ≠ 0. Řádek „Celkem“ (u podvojné knihy = 0 ve všech sloupcích; zapiš, i když ≠ 0).
  List Předvaha: sloupce Účet | Název | Zůstatek k {start} | Pohyb: Společné | Pohyb: {kód} … | Pohyb celkem | Zůstatek k {datum}.
- Nový list **Rozpad tříd** (za „Přemostění tříd“): řádky režimu `balance` (sjednocené přes účty), sloupce Účet | Název | Společné – fond |
  pro každou třídu: Podíl {kód}, Specifické {kód}, Vliv {kód}; poslední řádky: Celkem a „Kontrola: výsledek přemostění“ (shared_result + delta) a
  „Rozdíl“. Zdroj: `_class_split()` v paměti (nic se neukládá).
- List s řádky hlavní knihy **nepřidávat**.

## F. Texty 1.4 a Portfolio 1.5
- Texty: najdi `grep -rn` podle citací v zadání 1.4 (např. „celkový kapitál k datu ocenění“, „(ZJ-03)“, „Výjimky fondu“) v
  `views/nav_views.xml`, `models/tax_breakdown.py`, `models/valuation.py`; nahraď doslova větami ze zadání. `tax_breakdown.py`: poznámka jako
  výpočet „výsledek od zač. období X − výjimky Y + neuznatelné Z = základ W · po kroku N“ (čísla formátuj jako dnes ostatní částky v souboru);
  výjimky jen s nenulovým pohybem v `<details><summary>▸ Použité výjimky (n)</summary>…</details>`. Přesunuté věty do `help` příslušného pole
  a do `docs/manual/09-uplaty-a-opravy.md`.
- Portfolio (`investra.valuation.portfolio`, nestored computed, bez migrace): `prev_line_id` (řádek minulého ocenění se stejným
  instrument_id, portfolio_id, classification_id; dávkově jedním search), `price_change` Float „Změna ceny“ =
  `quantity × (u_t × fx_t − u_p × fx_p)`, `fx_change` Float „z toho kurz“ = `quantity × u_p × (fx_t − fx_p)`, kde `u = fair_value_currency / quantity`
  (kusy 0 nebo bez minulého řádku → 0). V listu portfolia ocenění sloupce s `optional="hide"`, `sum`.

## G. Testy (`tests/test_zj25_split.py`, `tests/test_zj25_checks.py`, `tests/test_zj25_package.py`)
1. Na referenčních scénářích (`TestScenarios` fixtures) pro každé ocenění: kontrola `class_split` ok; Σ impact = shared_result + delta pro každou třídu.
2. Fond se 2 třídami s podílem + 1 bez podílu; třída v cizí měně; specifická úplata třídy; úpis i odkup v období → `class_split` ok, řádek capital = −M.
3. Dodatečný zápis do minulého období (doklad s datem ≤ start po zaúčtování minulého ocenění) → řádek prior = D, kontrola ok.
4. Režim `result`: součty sloupců = režim `balance`; Σ dokladů z `_class_split_transfers` = řádek `transfer` (common i specific).
5. Staré ocenění (zveřejněné): `action_open_split` vrátí řádky a nic v ocenění ani v knize se nezmění (porovnej `fund_capital`, class lines, počet dokladů).
6. `action_open_lines`: doména vrací jen řádky účtu, období a (bez třídy | třída).
7. Balíček: list Předvaha má sloupec za každou třídu a součet = 0; list Rozpad tříd existuje a rozdíl = 0 (čti xlsx přes openpyxl, jako stávající test balíčku).
8. Kontroly: struktura (Očekáváno/Skutečnost/Rozdíl, položky) pro 3 vzorové kódy z katalogu; starší kontrola bez nových polí se zobrazí (detail).
9. Portfolio: změna ceny a kurzu na pozici v cizí měně proti ručně spočtené hodnotě.
Pak `investra_nav+`, `investra_dashboard`, `all`; snímek 35/39 beze změny.

## H. Pořadí commitů
1 model B + `_class_split` + kontrola + testy 1–6 → 2 katalog a pole kontrol + migrace (`migrations/<nová verze>/post-migrate.py` jen když
   přidáváš stored pole s výchozí hodnotou pro staré záznamy; jinak bez) + test 8 → 3 obrazovky D → 4 package E + test 7 → 5 texty F → 6 Portfolio + test 9.
Verze `investra_nav` +1. Výsledek do `docs/ukoly/ZJ-25-…md` (max 20 řádků) + seznam ke kontrole v prohlížeči.
