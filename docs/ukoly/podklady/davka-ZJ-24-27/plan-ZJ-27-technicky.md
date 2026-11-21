# ZJ-27 Zařazení z obchodu – technický plán pro Sonnet (připravil poradce 2026-11-21 z kódu dc1a404)

**Schválil Martin 2026-11-21** (bloky K2–K10; úpravy: převod stávající pozice na nový účet – K5b; výběr pravidla podle konkrétnosti, Priorita skrytá – K4).

Podklad s místy v kódu: `podklad-zj27-fakta.md` (dále „F“, např. F-A2 = oddíl A2). Zkratky modulů: INS, MST, NAV, DER jako v F.
Červená zóna (účtování, ocenění). Úsilí relace pro tuto část: **high**. Když kód plánu odporuje, zastav a napiš.
Neměnit: zaúčtované doklady, uložená ocenění, snímek 35/39 (existující zařazení si ponechají roli i způsob ocenění).

## 0. Rozhodnutí (Martin 2026-11-20/21)
1. Zařazení vzniká **jen automaticky** při zaúčtování obchodu nebo dohodnutí derivátu; nic se v něm ručně nevyplňuje.
2. Kategorie z portfolia (povinná `measurement_category_id`); obchod jen do **schváleného** portfolia platného k datu. **Žádné výchozí portfolio** fondu.
3. Způsob ocenění: AC → naběhlá hodnota, jinak „Určení reálné hodnoty“ nástroje (nové pole, výchozí z typu).
4. Role pozice jen z **pravidel účetních profilů** (nové rozsahy: typ, kategorie, nástroj; pravidla bez knihy = všechny knihy). Detail role ukazuje,
   proč a kde se použije. Výjimka v kódu zůstává jen pro repo s nebankovní protistranou (modul protistran).
5. Ruší se: ruční kategorie (dialog, matice, kontroly), ruční způsob ocenění a role, „odchylka od návrhu“, stav profilu „Role se liší“, reklasifikace,
   pole „Trh“ na nástroji. Typ si nechá roli jen jako **skrytou technickou zálohu** pro testy samotného INS.
6. Cena v % jmenovité hodnoty u dluhových nástrojů (obchod i schválená cena); jmenovitá hodnota = „Jistina na jednotku“ (`principal`,
   `_principal_per_unit`); pole MST „Nominál“ skrýt. Nové volitelné „Místo obchodu“ na obchodu. Tlačítko „Účetní zůstatky“ na nástroji.
7. Přehled „Pravidla účtování“ jen pro čtení. Test: agent stávající data doplní sám a vypíše, co změnil (nezastavuje se).

## K1 Závislosti a umístění
- `investra_nav/__manifest__.py`: do `depends` přidej `investra_instrument_master` (cyklus nevzniká: MST ← chart_fund, counterparty, INS).
- V INS jen **háčky** s dnešním chováním; skutečná logika v MST (zná kategorii, stav portfolia, profily):
  - `investra.portfolio.classification._ensure(portfolio, instrument, day, source)` – INS: `_valid(...)`, jinak dosavadní UserError.
  - `investra.portfolio.classification._planned(portfolio, instrument, day)` – INS: z `_valid` nebo `{}`; vrací dict
    `{"ifrs9_category", "valuation_method", "role_id", "rule_id", "record"}` pro náhled a pro computy obchodu.
- MST přepíše oba háčky (K5). INS testy běží beze změny chování (bez MST se nic nezakládá).

## K2 Portfolio (MST `models/portfolio.py`, INS `portfolio.py`)
- `measurement_category_id` `required=True` v modelu; `_onchange_measurement_category_id` beze změny.
- INS `InvestraFund.create` (F-C, portfolio.py:659-668): **nezakládat** „Hlavní“ (smazat blok). `_default_portfolio`: jediné portfolio fondu,
  které je ve stavu `approved` (MST přepis; INS beze stavu jako dnes).
- Nová MST metoda `fund_portfolio._usable(day)` = `state == "approved"` a `valid_from <= day` a (`valid_to` prázdné nebo `>= day`).
- Domény výběru portfolia (obchod F-C ř. 675-678, derivát F-A5, splátka a dividenda F-A3/A4): přidej `('state','=','approved')` (MST/NAV pohled
  přes `attributes`); kontrola k datu je v `_ensure` (K5).
- Hláška bez portfolia: „Fond %(fund)s nemá schválené portfolio platné k %(day)s. Založte a schvalte ho ve fondu, záložka Portfolia.“
- Texty o reklasifikaci (F-A8: portfolio.py:226-230, 614, 628-631) nahraď: „Po prvním obchodu se zařazení nemění. Pro jiný způsob řízení
  založte nové portfolio a toto uzavřete.“ Pole `valid_to` zařazení skryj ze všech pohledů (model ponech kvůli `_valid`).

## K3 Nástroj (INS `instrument.py`, NAV `instrument_accrual.py`, MST)
- Nové pole INS `fair_value_method = fields.Selection([("price","Cena × kusy"),("model","Model nebo znalec"),("contract","Reálná hodnota podle smlouvy"),
  ("position","Zadaná hodnota pozice")], string="Určení reálné hodnoty", tracking=True, required=True)`; výchozí v `_type_proposal`:
  `type.valuation_method` nebo `"model"`, je-li typ `amortised` (stejně jako dnes `_proposal`). Přidej do `NAV_INSTRUMENT_FIELDS`.
  Typ: popisek `valuation_method` → „Výchozí určení reálné hodnoty“ (hodnota `amortised` u typu = „model“ u nástroje).
- `market`: smaž pole i z pohledu (F-D: nikde jinde se nečte).
- MST `nominal_value`: v pohledech `invisible="1"` (pole ponech, data se nemažou).
- „Jistina na jednotku“ (`principal`): popisek ve formuláři nástroje „Jmenovitá hodnota kusu“ (jen string v pohledu NAV).
- Chytré tlačítko „Účetní zůstatky“ (NAV, formulář nástroje): akce `account.move.line`, doména `[("investra_instrument_id","=",id),("parent_state","=","posted")]`,
  `context={"group_by": ["company_id","account_id"]}`, pohled seznam s `balance` sum; počet = počet knih s nenulovým zůstatkem.

## K4 Pravidla účetních profilů (MST `accounting_profile.py`)
- `investra.accounting.profile.assignment`: `company_id` **nepovinné** (prázdné = všechny knihy; compute z portfolia ponech, `required` pryč),
  nová volitelná pole `type_id` (M2O `investra.instrument.type`), `measurement_category_id` (M2O), `instrument_id` (M2O nástroj, „Nástroj (ISIN)“).
- `_select(company, portfolio, instrument, day)` (nová signatura; staré volání uprav): kandidáti platní k `day`, `company_id` ∈ {company, prázdné},
  každý vyplněný rozsah musí sedět (portfolio, kategorie portfolia, typ, ba0088/skupina nástroje, nástroj). Vyhrává **nejkonkrétnější**:
  `(0 nástroj / 1 ba0088 / 2 skupina / 3 typ / 4 nic, 0 portfolio / 1 bez, 0 kategorie / 1 bez, 0 kniha / 1 všechny, priority, id)`.
  Pole `priority` skryj ze všech pohledů (výchozí 10, jen technický rozhodčí).
- `_check_overlap`: dvě pravidla se **stejnými rozsahy** (kniha, portfolio, kategorie, typ, ba0088, skupina, nástroj – prázdné = prázdné) a překrytou
  platností nejdou uložit (bez ohledu na prioritu). Hláška: „Stejné pravidlo už platí: %s. Upravte jeho platnost nebo ho ukončete.“
- `_profile_rule` na zařazení: den = `valid_from` (ne dnes).
- Data `data/accounting_profile_defaults.xml` (`noupdate="1"`): profil + pravidlo bez knihy pro každý typ z INS `data/instrument_type.xml`
  s rolí podle dnešního `type.role_id` (F-D), priorita 100; navíc pravidlo typ `participation` + kategorie FVTPL → `role_participation_fv`, priorita 90.
- Detail role (`investra.account.role` formulář, investra_entity + MST přes inherit): záložky **Účty v knihách** (mapování `investra.role.account`:
  kniha, účet, další účty), **Kdy se použije** (pravidla profilů s touto rolí: rozsahy, priorita, platnost), **Události účtování** (z K8).

## K5 Zařazení (INS `portfolio.py` + MST přepis)
- Pole se stávají jen pro čtení a dopočtená:
  - `instrument_nature` = `_default_nature(instrument)` (compute store; `nature_note` skrýt);
  - `designation` = `fvoci_equity`, je-li kategorie portfolia FVOCI_E; `fvo`, je-li kategorie FVTPL a povinná kategorie (`_mandatory`) vychází
    `amortised`/`fvoci` (jinak by `_check_classification` fvo odmítl); jinak `none`;
    `designation_note` = „Podle portfolia {název}“ (compute store);
  - `valuation_method` = compute store: `amortised`, když `ifrs9_category == "amortised"`, jinak `instrument_id.fair_value_method`;
  - `role_id` stored, plní se při založení z `_profile_rule()`; změní ho **jen převod pozice (K5b)**, nikdy tiše změna pravidla;
    nové pole `role_rule_id` (M2O assignment, „Pravidlo role“) pro „proč“; computed `role_rule_mismatch` (Boolean): výsledek `_select` k dnešku ≠ `role_id`.
- MST `_ensure(portfolio, instrument, day, source)`: (1) `portfolio._usable(day)` jinak hláška K2; (2) existující `_valid` → vrať;
  (3) SPPI: kategorie AC/FVOCI_D a nástroj bez `sppi_status == "pass"` → UserError „Nástroj %(isin)s nemá posouzený (splněný) test SPPI, který portfolio
  %(p)s vyžaduje. Doplňte ho na nástroji, záložka Test SPPI.“; (4) pravidlo profilu `_select(...)`, bez něj UserError „Pro %(isin)s v portfoliu %(p)s
  není pravidlo účetního profilu. Doplňte ho v Nastavení › Účetnictví › Přiřazení účetních profilů.“; (5) `create` sudo s `valid_from=day`, `role_id`,
  `role_rule_id`, `note=f"Vzniklo z {source.display_name}"`; konstrukce `_check_category_compatibility` proběhne jako dnes.
  Repo s nebankovní protistranou: po výběru role zavolej dnešní úpravu z modulu protistran (F-B `_proposal_role` v counterparty) – zachovat.
- MST `_planned(...)`: totéž bez zápisu; při chybě vrací `{"error": text}`.
- Zrušit: `_proposal`, `_proposal_role` (logiku účasti FV nahradí pravidlo K4), `_onchange_proposal`, `_compute_deviates`/`deviates_from_proposal`,
  `category_override`, `override_note`, `_override_gate`, `_log_override`, `request_category_override`, větve override v `_compute_category`
  (INS i MST kopie F-B), `profile_state` „deviates“ (zůstává ok/missing). Ze `LOCKED_CLASSIFICATION` vyřaď zrušená pole.
- Pohledy zařazení: formulář jen pro čtení (pás: Kategorie, Způsob ocenění, Role + pravidlo, Od; poznámka „Vzniklo z …“; sbalený Postup klasifikace),
  `create="0" edit="0"` v seznamu i formuláři; tlačítko „Ruční kategorie…“ a skupina pryč; seznam v portfoliu: Nástroj, Od, Způsob ocenění.

## K5b Převod stávající pozice na nový účet (Martin 2026-11-21)
- Průvodce `investra.classification.role.transfer.wizard` (MST): `classification_ids` (M2M, z výběru v seznamu zařazení nebo z formuláře),
  `date` (required, default dnes; musí být > `company.fiscalyear_lock_date`, jinak hláška „Datum spadá do zamčeného období (do %s).“),
  řádky náhledu (computed): zařazení, dnešní role → nová role (`_select` k `date`), zůstatek k převodu.
- Zůstatek = součet `balance` řádků `account.move.line` s `investra_classification_id = zařazení`, `parent_state = posted`, `date <= date`
  na účtech `Role.accounts_for(company, staré_role)` (tj. jen pozice; úrok, přecenění a jiné role se nepřevádějí – mají vlastní pevné role).
- Akce „Převést pozici“ (btn-primary; vratná dalším převodem): pro každé zařazení událost `investra.accounting.event._create_event(company,
  f"role_transfer:{classification.id}:{date}", "Převod pozice na nový účet", date, "transaction", lines)` s řádky
  `{"role": nová, "amount": zůstatek}` a `{"role": stará, "amount": -zůstatek}`, oba s `extra` jako obchod (nástroj, zařazení; třída z portfolia
  přes `_portfolio_class_lines`); pak `classification.sudo().write({"role_id": nová, "role_rule_id": pravidlo})` (výjimka v `write` přes kontext
  `investra_role_transfer`). Do chatteru zařazení: „Převedeno z role X na Y k datu D, doklad …“. Nulový zůstatek → jen změna role, bez dokladu.
- Kontrola ocenění (NAV, `_run_checks`): kód `classification_role_rule`, „Účtování pozic odpovídá pravidlům profilu“, warning; položky = zařazení
  s `role_rule_mismatch` a nenulovou pozicí, odkaz na zařazení. Přidej do `check_catalog.py` (oblast Účetnictví; Co: „Pozice se účtují na účty
  podle platných pravidel účetních profilů.“; Jak: „V Zařazení vyberte pozice a použijte Převést pozici na nový účet.“).
- Seznam zařazení: filtr „Účtování neodpovídá pravidlu“ (`role_rule_mismatch`), akce v menu Akce „Převést pozici na nový účet“.

## K6 Obchod, derivát, splátka, dividenda
- Obchod (INS `instrument.py`): v `_book` (F-A2 ř. 1216-1232) **před** `trade._classification()` zavolej
  `Classification._ensure(trade.portfolio_id, trade.instrument_id, trade.trade_date, trade)` a pak
  `trade.invalidate_recordset(["classification_id", "ifrs9_category", "fee_treatment"])`.
- `_compute_classification_id`: když `_valid` nic nenajde, `ifrs9_category` vezmi z `_planned(...)` (aby `fee_treatment` a náhled seděly už v návrhu).
  Nové computed pole `classification_preview` (Char): „Vznikne při zaúčtování: {kategorie}, {způsob}, role {role} (pravidlo {pravidlo})“ nebo text chyby.
- NAV `trade_preview.py` (F-A2: ř. 143-146, 180, 196, 206): místo `classification_id.X` čti `trade._classification_values()` = `_valid` nebo `_planned`.
- Derivát (DER `posting.py:100-107`): `_ensure_classification` nahraď voláním `_ensure(...)` (stejný háček; role derivátu dál z `ROLES[kind]`).
- Splátka a dividenda: beze změny (pozice bez zařazení nemůže existovat); jen hlášky sjednoť s K2.
- „Místo obchodu“: INS `venue = fields.Char(string="Místo obchodu", help="Kde byl obchod uzavřen (burza, OTC, protistrana); pro rekonciliace pozic.")`,
  ve formuláři u vypořádání, v seznamu `optional="hide"`, ve vyhledávání.

## K7 Cena v % (NAV, protože zná `_principal_per_unit`)
- Obchod a `investra.instrument.price`: `price_mode = fields.Selection([("unit","Za kus"),("percent","V % jmenovité hodnoty")], default="unit", required=True)`,
  `price_percent = fields.Float(digits=(16, 6), string="Cena v %")`; viditelné jen u `instrument_id.type_id.group in ("debt","money_market")`.
- V `create`/`write` a v `@api.onchange("price_mode","price_percent","instrument_id")`: při `percent` nastav `price = round(price_percent / 100 × instrument._principal_per_unit(), 8)`.
  Pole `price` zůstává jediným vstupem výpočtů (nic dalšího se nemění). Vedle procent text „= {cena} {měna} za kus“.
- Chybí-li jmenovitá hodnota (`_principal_per_unit` vrátí 1 bez kalendáře i `principal`) → ValidationError „Nástroj %s nemá jmenovitou hodnotu kusu; doplňte Jmenovitou hodnotu kusu.“

## K8 Přehled „Pravidla účtování“ (NAV, jen pro čtení)
- Model `investra.posting.rule` (`sequence`, `event` Char „Událost“, `step` Char „Krok“, `side` Selection debit/credit/sign „MD / D / podle znaménka“,
  `role_id` M2O nebo `role_source` Char „z pravidla profilu (pozice)“, `note`), data `data/posting_rules.xml` (`noupdate="0"`) sestavená **z kódu**:
  obchod (nákup, prodej, vypořádání, poplatek), splátka, dividenda, úpis/odkup, úplaty, ocenění (přecenění, úrok, kurz, nevypořádané), derivát.
  Zdroj každého řádku uveď v `note` (soubor:metoda). Nabídka Nastavení › Účetnictví › Pravidla účtování (seznam seskupený podle události, bez editace).
- Test: každá `role_id` v datech existuje a každý kód role použitý v `{"role": ...}` řádcích obchodu, splátky, dividendy a derivátu je v přehledu.

## K9 Odstranění ruční kategorie a kontrol
- INS `override_wizard.py` + import, ACL (F-B), pohledy a akce; investra_fund `ACTIVITIES`/`BUILTIN` `classification_override` a záznam
  `data/approval_matrix.xml:56-62`; migrace: smaž řádky matice a zruš čekající žádosti s touto činností (stav zrušeno, poznámka ZJ-27).
- NAV kontroly `classification_override`, `classification_proposal` (valuation.py:2327-2339) smaž, a jejich řádky v `check_catalog.py` (ze ZJ-25).
- `investra.approval.pending.mixin` na zařazení odeber, pokud ho nic jiného nepoužívá.

## K10 Migrace a data (MST post-migrate nové verze; NAV/INS dle potřeby) – test, agent nezastavuje, vše vypíše do `docs/ukoly/ZJ-27-…md`
1. Portfolia bez kategorie: z `business_model` (hold_to_collect → AC, hold_collect_sell → FVOCI_D, `na` → FVOCI_E, jinak FVTPL); bez kódu → `P{id}`,
   bez důvodu → `reason_business_model`. Portfolia s doklady a stavem draft → `approved` (approved_by = OdooBot, poznámka do chatteru „Schváleno migrací ZJ-27“).
   Portfolia bez dokladů a zařazení jménem „Hlavní“ → archivovat.
2. Nástroje: `fair_value_method` z jejich zařazení mimo AC (nejčastější; při rozporu vypsat) nebo z typu.
3. Pravidla profilů: data K4; existující zařazení, jejichž role se liší od výsledku `_select`, **neměnit**, jen vypsat.
4. Zařazení s `category_override`: hodnotu smazat, kategorie se přepočte; neslučitelné s portfoliem jen vypsat.
5. Snímek 35/39 musí zůstat stejný (role a způsob existujících zařazení se nemění).

## K11 Testy
- Fixtures: INS `tests/test_instrument.py:35-48` beze změny chování (INS bez MST); NAV `tests/common.py:65-82` a MST/DER/cnb/dashboard fixtures:
  helper `portfolio(...)` založí portfolio **s kategorií a schválené** (`action_approve` jako schvalovatel), `classify(...)` nahraď `_ensure(...)`
  (nebo nech obchod zařazení založit). Fond už nedostává „Hlavní“ – testy, které na něj spoléhaly, založí portfolio helperem.
- Přepsat/odstranit testy z F-G (override, proposal, ruční způsob, profile_state deviates, role z typu, portfolio bez kategorie); zachovat jejich účel
  tam, kde dává smysl (např. účast FV → nyní z pravidla K4; repo nebanka → stále z modulu protistran).
- Nové `investra_instrument_master/tests/test_zj27_auto_classification.py`: obchod do schváleného FVTPL portfolia založí zařazení (kategorie, způsob
  z nástroje, role z pravidla, `role_rule_id`); neschválené / neplatné portfolio → hláška; AC bez SPPI → hláška; bez pravidla → hláška; FVOCI_E →
  designation z portfolia; pravidlo pro ISIN má přednost před typem; pravidlo knihy před „všechny knihy“; druhý obchod použije existující zařazení;
  změna pravidla nezmění existující zařazení, ale nastaví `role_rule_mismatch` a kontrolu `classification_role_rule`; převod pozice (K5b):
  doklad MD nová / D stará ve výši zůstatku, role zařazení změněna, datum v zamčeném období odmítnuto, nulový zůstatek bez dokladu, ocenění po
  převodu sedí (kontrola pozice = kniha); dvě pravidla se stejnými rozsahy nejdou uložit; derivát přes `_ensure`.
- NAV: cena v % (obchod, cena; přepočet; chybějící jistina), `classification_preview`, `fee_treatment` v návrhu AC (kapitalizace), Účetní zůstatky (doména),
  test přehledu pravidel (K8).
- Pořadí běhu: INS → MST → NAV+ → DER → `all`; snímek 35/39.

## K12 Pořadí commitů
1 K1 háčky + závislost → 2 K4 pravidla a data → 3 K3 nástroj → 4 K2 portfolio → 5 K5 zařazení (MST `_ensure`/`_planned`) → 5b K5b převod pozice → 6 K6 obchod/derivát/náhled
→ 7 K9 odstranění → 8 K10 migrace → 9 K11 fixtures a testy → 10 K7 cena v % → 11 K8 přehled pravidel a detail role → 12 Účetní zůstatky, místo obchodu.
Verze: INS, MST, NAV, DER, investra_fund, investra_counterparty +1. Výsledek do `docs/ukoly/ZJ-27-zarazeni-z-obchodu.md` (max 30 řádků + výpis migrace).
