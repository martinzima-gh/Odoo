# Podklad ZJ-27 „Zařazení z obchodu“ – fakta z kódu

Zdroj: `origin/ukol/ZJ-24-hlasky-a-sazby` (commit dc1a404). Cesty relativně k `addons/custom/`, čísla řádků platí pro tento commit.
Zkratky: **INS** = `investra_instruments`, **MST** = `investra_instrument_master`, **NAV** = `investra_nav`, **DER** = `investra_derivative`.

Závislosti modulů (manifesty): INS ← `investra_posting, investra_rates, investra_fund`; MST ← `investra_chart_fund, investra_counterparty, investra_instruments`;
NAV ← `investra_fund, investra_instruments, investra_allocation, investra_fx_revaluation` (**NAV nezávisí na MST**); DER ← `investra_nav, investra_counterparty, investra_instrument_master`;
counterparty ← INS; cnb ← INS; dashboard ← NAV. Verze: INS 20.0.0.16.0, MST 20.0.0.8.1, NAV 20.0.0.44.0, DER 20.0.0.4.0, investra_fund 20.0.0.13.0, counterparty 20.0.0.5.0.
Moduly nemají adresáře `i18n`.

---

## A. Kde se zařazení hledá a vyžaduje

### A1. `Classification._valid` – INS `models/portfolio.py:645-651`
```python
@api.model
def _valid(self, portfolio, instrument, day):
    """Zařazení nástroje v portfoliu platné k datu, nebo prázdný záznam."""
    return self.sudo().search([
        ("portfolio_id", "=", portfolio.id), ("instrument_id", "=", instrument.id), ("valid_from", "<=", day),
        "|", ("valid_to", "=", False), ("valid_to", ">=", day),
    ], order="valid_from desc", limit=1)
```
Volání `_valid`: INS `instrument.py:896` (obchod), NAV `instrument_accrual.py:453` (splátka), NAV `dividend.py:246` (dividenda), NAV `valuation.py:544` (ocenění portfolia), DER `posting.py:70` (`_line_extra`), DER `posting.py:104` (`_ensure_classification`), DER `valuation.py:157` (řádek portfolia derivátu), dashboard `dashboard.py:384`.

### A2. Obchod `investra.trade` (INS `models/instrument.py`)
- Pole `classification_id` (ř. 682-684): `Many2one("investra.portfolio.classification", compute="_compute_classification_id", string="Zařazení")` – **neukládá se**; `ifrs9_category` (ř. 685) compute stejnou metodou.
- `_compute_classification_id` ř. 891-897, `@api.depends("portfolio_id", "instrument_id", "trade_date")`:
  `trade.classification_id = Classification._valid(trade.portfolio_id, trade.instrument_id, trade.trade_date) if ready else False`; `trade.ifrs9_category = trade.classification_id.ifrs9_category`.
- `_classification()` ř. 910-919 – odmítnutí: `UserError("Nástroj %(name)s nemá v obchodním modelu %(portfolio)s k %(day)s zařazení. Založte ho v obchodních modelech fondu.")`.
- Volání `_classification()`: ř. 1033 (`_fee_lines` extra), 1137 (`_event_lines` extra), 1165 (`_fee_settlement_lines`: `self._classification().role_id.code`), 1192 (`_planned_postings`: `role = self._classification().role_id.code`), 1222 (`_book`, první kontrola před `_check_sale`). NAV `valuation.py:1005` (`_compute_unsettled_fair_value`).
- `_book` ř. 1216-1232 (`for trade in self.filtered(state == "draft")`: other_holding → UserError; `trade._classification()`; `_check_sale()`; `_planned_step("book")`; …). Volá se z `action_book` ř. 1091-1094 jako `self.sudo()._book()`.
- **Navázané computy na zařazení**: `fee_treatment` ř. 960-964 `@api.depends("side","quantity","ifrs9_category")` → `"capitalise"` jen pro nákup v amortised/fvoci; `_fee_lines` ř. 1035 ho čte. NAV `trade_preview.py`: `classification_summary` ř. 91-105, `_ready_for_preview` ř. 143-146 (vyžaduje `self.classification_id`), `_preview_extra_html` ř. 180 a `_expected_result` ř. 196 (čtou `classification_id.valuation_method == "amortised"`), ř. 206 (`classification_id.role_id.code`).
- Test na odmítnutí: INS `tests/test_classification.py:49-54` `TestClassification.test_trade_without_classification_is_not_booked` (očekává `UserError` z `_book`).

### A3. Splátka `investra.instrument.repayment` (NAV `models/instrument_accrual.py`, model ř. 330)
- `_classification()` ř. 451-453: `_valid(self.portfolio_id._origin, self.instrument_id._origin, self.date)`.
- Odmítnutí je v `_validate` ř. 747-789, ř. 759-763: `ValidationError("Nástroj %(name)s nemá v modelu %(portfolio)s k %(day)s zařazení.")`. **`_validate` se volá i z `@api.constrains` `_check_repayment` ř. 741-745** (při uložení, ne jen při zaúčtování), dále z `_book` ř. 836 a `_preview_documents` ř. 861.
- ř. 779: `self._classification().valuation_method == "amortised"` (kontrola kalendáře u splátky „scheduled“).
- `_book_lines` ř. 801-831: `classification = repayment._classification()` ř. 807; extra ř. 813; `classification.role_id.code` ř. 829.
- Portfolio splátky: `domain="[('id','in',allowed_portfolio_ids)]"` ř. 344-347 (jen portfolia s držbou).

### A4. Dividenda `investra.dividend` (NAV `models/dividend.py`, model ř. 29); `investra.dividend.event` jen zakládá řádky (dividend_event.py:133-150)
- `_classification()` ř. 244-246: `_valid(self.portfolio_id._origin, self.instrument_id._origin, self.ex_date)`.
- Odmítnutí v `_validate` ř. 217-242, ř. 237-240: `UserError("Nástroj %(name)s nemá v portfoliu %(portfolio)s k %(day)s zařazení.")`. `_validate` volá `action_book` ř. 384-392 (ř. 388) a `_preview_documents` ř. 447. Není v constrains.
- `_line` ř. 311-321: extra s `self._classification().id` (ř. 314). Role řádků dividendy se z `classification.role_id` **neberou** (účty podle kódů, `_account` ř. 300-309).

### A5. Derivát `investra.derivative` (DER `models/posting.py`, `_inherit` ř. 38-39)
Celé `_ensure_classification` ř. 100-107:
```python
def _ensure_classification(self):
    """Zařazení nástroje v obchodním modelu ke dni sjednání (kategorie, způsob ocenění a role podle návrhu typu)."""
    self.ensure_one()
    Classification = self.env["investra.portfolio.classification"]
    if not Classification._valid(self.portfolio_id, self.instrument_id, self.trade_date):
        Classification.create({
            "portfolio_id": self.portfolio_id.id, "instrument_id": self.instrument_id.id, "valid_from": self.trade_date,
        })
```
- Jediné volání: `_agree` ř. 201-207 (`derivative._ensure_classification()` ř. 207), `_agree` se volá z `action_agree` ř. 196-199 jako `self.sudo()._agree()` → create běží **sudo** (gate ruční kategorie i kontroly zápisu se přeskočí).
- `_line_extra` ř. 64-74: zařazení do extra jen u portfolia s třídou (`portfolio_id.class_id`). Role derivátu se nebere ze zařazení, ale z `ROLES[kind]` ř. 19-27 (`derivative`, `derivative_liability`, …).
- Nástroj derivátu: `_instrument_vals` derivative.py:235-247, typ `investra_instruments.type_derivative_otc`; portfolio derivátu `domain="[('fund_id','=',fund_id)]"` derivative.py:39-42, výchozí `_default_portfolio()` ř. 98-99, 225-227.
- DER `valuation.py:157` `_valid(...)` k datu ocenění pro `classification_id` řádku portfolia (může být prázdné).

### A6. Ocenění
- NAV `valuation.py:529-670` `_compute_portfolio`: ř. 544 `_valid(portfolio, instrument, self.date)`; ř. 545-549 `UserError("Nástroj %(name)s nemá v obchodním modelu %(portfolio)s k %(day)s zařazení.")`; ř. 550 `amortised = classification.valuation_method == "amortised"`; ř. 553 `fvoci = classification.ifrs9_category == "fvoci" and not amortised`; ř. 554 `role = classification.role_id.code`; ř. 625 extra; řádek `investra.valuation.portfolio` `_portfolio_row` ř. 672-700 (`classification_id` ř. 680).
- `_closed_positions` ř. 510-527: čte `investra_classification_id` z řádků, `classification.role_id.code` ř. 522, `classification.ifrs9_category` ř. 524.
- `_compute_unsettled_fair_value` ř. 995-1028: `trade._classification()` ř. 1005, `ifrs9_category` ř. 1006, 1025.
- `_position_balance` ř. 362-369: role = `investra.instrument.type.search([]).role_id | classification(fund).role_id` (**čte role typu**). Totéž DER `valuation.py:60-61`.
- Kontroly ocenění ř. 2327-2339: `classification_override` (filtr `category_override`) a `classification_proposal` (filtr `deviates_from_proposal`), obě `severity="warning"`. Kódy kontrol nejsou nikde jinde (žádná data XML).
- `investra.valuation.portfolio` ř. 3344-3380: `classification_id` M2O (ř. 3358), `ifrs9_category` related (ř. 3359).

### A7. `account.move.line.investra_classification_id`
- Definice INS `instrument.py:1322-1324` (`ondelete="restrict"`, index btree_not_null, není v integritním hashi); zákaz změny po zaúčtování `write` ř. 1330-1333.
- Plní se jen přes `extra` řádků událostí: obchod (`_event_lines` ř. 1137, `_fee_lines` ř. 1033), splátka (instrument_accrual.py:813), dividenda (dividend.py:314), ocenění (valuation.py:625, 792, 1022), derivát (posting.py:73 jen u portfolia třídy). INS `models/accounting_event.py:22-64` `_portfolio_class_lines` z něj odvozuje třídu.
- Čtení: `InvestraFundPortfolio._has_postings` INS portfolio.py:206-217; valuation.py:514-515, 590, 719, 869, 1014; cnb `models/cnb_map.py:63` (`investra_classification_id.ifrs9_category`); migrace INS 20.0.0.4.0.

### A8. Kdo čte `valuation_method`, `role_id`, `ifrs9_category`, `category_override`, `valid_to` zařazení (mimo INS/MST portfolio.py)
- `valuation_method`: NAV valuation.py:550; instrument_accrual.py:779; trade_preview.py:180, 196; dashboard.py:384.
- `role_id`: INS instrument.py:1165, 1192; NAV instrument_accrual.py:829; valuation.py:365, 522, 554; trade_preview.py:206; DER valuation.py:61; MST accounting_profile.py:135, 145; counterparty migrace 20.0.0.2.0; tools/demo_data/seed.py:512.
- `ifrs9_category`: INS instrument.py:897 (→ `fee_treatment` 960-964); NAV valuation.py:524, 553, 1006, 1025; trade_preview.py:91-101; fund_tax.py:127-128 (`search_count` zařazení s `ifrs9_category = fvoci`); cnb_map.py:63; MST portfolio.py:202, 238.
- `category_override`: jen INS portfolio.py, MST portfolio.py (169-170, 190, 208), INS override_wizard.py, NAV valuation.py:2328, migrace counterparty 20.0.0.2.0:16 (předává do `_proposal`).
- `valid_to` zařazení: jen `_valid` (651), `_check_overlap` (605-616), pole ř. 264 a pohledy (instrument_views.xml:440, 506-509). **Žádný kód `valid_to` nezapisuje** – není metoda ani wizard reklasifikace; jen hlášky „reklasifikace … zatím není podporovaná“ (portfolio.py:226-230, 614, 628-631).

---

## B. Zařazení `investra.portfolio.classification` (INS `models/portfolio.py:245-651`)

`_inherit = ["investra.record.guard", "mail.thread", "investra.approval.pending.mixin"]`, `_order = "fund_id, portfolio_id, instrument_id, valid_from desc"`, `_book_fields = ("portfolio_id",)`, `_rec_names_search = ["instrument_id", "portfolio_id"]`.

| pole (ř.) | typ / atributy |
|---|---|
| portfolio_id (258) | M2O fund.portfolio, required, restrict, index |
| fund_id (259) | related portfolio_id.fund_id, store, index |
| company_id (260) | related portfolio_id.company_id, store, index |
| instrument_id (261) | M2O instrument, required, restrict, index |
| instrument_kind (262) | related instrument_id.type_id.kind |
| valid_from (263) | Date, required, default today, tracking |
| valid_to (264) | Date, readonly, help „Vyplní jen reklasifikace.“ |
| instrument_nature (266) | Selection NATURE, required, tracking |
| nature_note (267) | Char, tracking |
| sppi / sppi_note / sppi_version (272-280) | compute `_compute_sppi`, store, tracking (bez required) |
| business_model (282) | related portfolio_id.business_model |
| mandatory_category (284) | Selection IFRS9_CATEGORY, compute `_compute_category`, store |
| designation (289) | Selection DESIGNATION, required, default "none", tracking |
| designation_note (290) | Char, tracking |
| category_override (292) | Selection IFRS9_CATEGORY, tracking |
| override_note (296) | Char, tracking |
| computed_category (297) | compute `_compute_category`, store |
| ifrs9_category (301) | compute `_compute_category`, store, tracking |
| classification_basis (304) | Text, compute `_compute_category`, store, tracking |
| valuation_method (305) | Selection VALUATION_METHOD, **required**, tracking |
| role_id (306) | M2O investra.account.role, **required**, restrict, tracking |
| note (307) | Char, tracking |
| deviates_from_proposal (308) | Boolean compute `_compute_deviates` (neukládá se) |
MST přidává (accounting_profile.py:125-164): `accounting_profile_id` (compute, neukládá), `profile_state` (Selection `PROFILE_STATE = [("ok","V pořádku"),("missing","Není nastaven"),("deviates","Role se liší")]`, compute).
Z mixinu `investra.approval.pending.mixin`: `pending_request_id`, `action_open_pending_request` (form ř. 482-487).

Selekce: `IFRS9_CATEGORY` (INS instrument.py:8) `fvtpl`/`fvoci`/`amortised`; `VALUATION_METHOD` (ř. 9-12) `price` „Cena × kusy“, `amortised`, `model` „Model nebo znalec“, `contract` „Reálná hodnota podle smlouvy“, `position` „Zadaná hodnota pozice“; `NATURE` (portfolio.py:19-25) `debt, equity, puttable, derivative, participation`; `NATURE_BY_KIND` (28-32); `SPPI` (38) `pass, fail, na`; `SPPI_STATUS` (41) + `not_assessed`; `DESIGNATION` (51-55) `none`, `fvo`, `fvoci_equity`; `BUSINESS_MODEL` (12-17) `hold_to_collect, hold_collect_sell, fair_value, trading` (+ MST `na` „Nepoužije se“, MST portfolio.py:30); `SPPI_MODELS` (18), `SPPI_NATURES = {"debt","puttable"}` (34), `SPPI_CATEGORY_NATURES = {"debt"}` (37), `MANDATORY_BASIS` (56-62).

Konstanty (portfolio.py):
- `LOCKED_CLASSIFICATION` ř. 65-68 = `{"portfolio_id","instrument_id","valid_from","instrument_nature","nature_note","designation","designation_note","category_override","override_note","valuation_method","role_id"}`.
- `_OVERRIDE_OK = object()` ř. 70.
- `COMPUTED_CLASSIFICATION` ř. 71 = `{"ifrs9_category","mandatory_category","computed_category","classification_basis"}`.
- `SPPI_FROM_INSTRUMENT` ř. 72 = `{"sppi","sppi_note","sppi_version"}`.

Metody (signatury):
- `default_get` 312-322 (portfolio z `fund._default_portfolio()`).
- `_sppi_from(self, instrument, nature)` 330-335 (@api.model): SPPI z nástroje u `SPPI_NATURES` a stavu pass/fail, jinak `{"sppi":"na","sppi_note":False,"sppi_version":False}`; `_compute_sppi` 337-340.
- `_mandatory(self, nature, model, sppi)` 344-349: `debt` + SPPI model + `pass` → `amortised` (hold_to_collect) / `fvoci`; jinak `fvtpl`.
- `_final(self, mandatory, designation)` 351-358: `fvo`→`fvtpl`, `fvoci_equity`→`fvoci`, jinak mandatory.
- `_compute_category` 360-403 (depends vč. `category_override`, `override_note`); řádek (f) s „RUČNÍ PŘEPSÁNÍ“ 396-400. MST přepis pro model `na` portfolio.py:153-197 (kopie s řádkem (c) „Nepoužije se“, zase s větví category_override 190-194).
- `_default_nature(self, instrument)` 407-409: `NATURE_BY_KIND.get(instrument.type_id.kind, "equity")`.
- `_default_sppi_version` 411-421 (jen pro starou migraci).
- `_proposal(self, instrument, portfolio, nature, sppi="na", designation="none", override=False, valid_from=None)` 423-435: `final = override or _final(_mandatory(nature, portfolio.business_model, sppi), designation)`; method = `amortised` při final amortised; jinak `model`, pokud `type.valuation_method == "amortised"`; jinak `type.valuation_method`; vrací `{"valuation_method", "role_id": _proposal_role(instrument, kind.role_id, final, valid_from).id}`.
- `_proposal_role(self, instrument, role, category, valid_from)` 437-443: `role_participation` + `fvtpl` → `investra_entity.role_participation_fv`. Přepis v `investra_counterparty/models/classification.py:10-20`: `role_repo` + protistrana se sektorem mimo `BANK_SECTORS = ("1210000","1220000")` → `investra_entity.role_repo_client`.
- `_override_gate` 445-457 (matice `classification_override`, `rule.persons > 1` → UserError), `_log_override` 459-462, `request_category_override(self, category_override, override_note)` 464-479 (`Matrix._gate("classification_override", self, "request_category_override", {...})`).
- `create` 481-506: gate pro `category_override`; zákaz `COMPUTED_CLASSIFICATION` a `SPPI_FROM_INSTRUMENT` ve vals (UserError); `setdefault("instrument_nature", _default_nature)`; při instrumentu+portfoliu `setdefault` hodnot z `_proposal(...)` (valuation_method, role_id).
- onchange `_onchange_instrument_nature` 508-511, `_onchange_proposal` 513-519.
- `_compute_deviates` 521-536: `(valuation_method, role_id.id) != proposal`.
- `_check_classification` 542-593 (constrains `instrument_nature, nature_note, designation, designation_note, category_override, override_note, valuation_method, portfolio_id, instrument_id, valid_from`): povaha≠druh bez `nature_note`; **debt + SPPI model + sppi `na` → ValidationError „V modelu Držet pro inkaso nebo Inkaso i prodej musí mít nástroj vyhodnocený test SPPI (IFRS 9 4.1.2); posuďte ho na nástroji: %s.“ (556-560)**; designation bez note; `fvo` jen při mandatory amortised/fvoci; `fvoci_equity` jen `equity` a ne `trading`; override bez note / shodný s computed; puttable v amortised/fvoci; `(ifrs9_category == "amortised") != (valuation_method == "amortised")` 592-593.
- `_check_instrument_fund` 595-603.
- `_check_overlap` 605-616 (constrains `portfolio_id, instrument_id, valid_from, valid_to`): překryv platností → ValidationError „… změna po prvním obchodu je reklasifikace, která zatím není podporovaná.“
- `_trades` 618-621; `write` 623-638 (zákaz COMPUTED/SPPI pro ne-su; `LOCKED_CLASSIFICATION` po obchodu → UserError; gate při změně override); `unlink` 640-643.
- Sql: `_uniq = unique(portfolio_id, instrument_id, valid_from)` ř. 310.
- Zápis SPPI na nástroji volá `changed.classification_ids._check_classification()` (portfolio.py:155) a MST `InvestraInstrumentPortfolioCheck.write` → `_check_category_compatibility()` (MST portfolio.py:250-258).

MST `InvestraPortfolioClassificationMaster` (MST `models/portfolio.py:150-247`):
- `_measurement_code()` 199-204: fvoci → `FVOCI_E` při `designation == "fvoci_equity"`, jinak `FVOCI_D`; amortised → `AC`; fvtpl → `FVTPL`.
- `_check_category_compatibility` 208-247, constrains `portfolio_id, instrument_id, instrument_nature, designation, category_override`; bez kategorie portfolia nic nekontroluje (214-215). Hlášky: puttable v AC/FVOCI_D (217-221); **SPPI `fail` → „Nástroj s nesplněným testem SPPI nelze zařadit do portfolia %s. Zařaďte ho do portfolia FVTPL.“ (224-227); jiný než `pass` → „Portfolio %s vyžaduje u nástroje splněný test SPPI; nástroj %s ho má %s.“ (228-232)**; FVOCI_E bez `fvoci_equity` (233-236); nekompatibilní kategorie (237-247). Konstanty `CATEGORY_MODEL = {"AC":"hold_to_collect","FVOCI_D":"hold_collect_sell","FVOCI_E":"na"}` ř. 12, `SPPI_CATEGORIES = {"AC","FVOCI_D"}` ř. 13.

Override – další místa:
- Wizard INS `models/override_wizard.py` (`investra.classification.override.wizard`: `classification_id`, `category_override` required, `override_note` required, `action_confirm`); import v `models/__init__.py:3`; práva `security/ir.access.csv:22-23`; pohledy `views/instrument_views.xml:448-472` (form + akce `action_classification_override_wizard`) a tlačítko „Ruční kategorie…“ ve formuláři zařazení ř. 477-480; skupina „Ruční kategorie“ ř. 549-552; list ř. 442.
- Schvalovací činnost: investra_fund `models/approval_matrix.py:27` (`ACTIVITIES` `("classification_override","Ruční přepsání kategorie IFRS 9")`), `:43` (`BUILTIN` 0); data `investra_fund/data/approval_matrix.xml:56-62` (`matrix_default_classification_override`); `investra_fund/tests/common.py:15` (seznam činností).
- Kontroly ocenění NAV valuation.py:2327-2339 (`classification_override`, `classification_proposal`).
- Pohled „Odchylka od návrhu“: instrument_views.xml:444, 525. Formulář zařazení: `valuation_method` ř. 517-518 (`readonly="ifrs9_category == 'amortised'"`), `role_id` ř. 520-523; MST `accounting_profile_views.xml:120-131` (`view_classification_form_profile`, xpath za `role_id` přidává `accounting_profile_id`, `profile_state`).

---

## C. Portfolio a oceňovací kategorie

INS `investra.fund.portfolio` (portfolio.py:175-242): `fund_id` (req), `company_id` (related store), `name` (req), `sequence`, `business_model` (req, default `fair_value`), `assessment`, `active`, `classification_ids`, `class_id` (ZJ-09). `_name_uniq unique(fund_id, name)`. `write` 225-237 (zákaz změny `business_model` po obchodu), `unlink` 239-242. `InvestraFund.create` 659-668 zakládá každému novému fondu portfolio **„Hlavní“, `fair_value`, bez kategorie, kódu a důvodu** (sudo). `_default_portfolio` 670-674: jediné (aktivní) portfolio fondu, jinak prázdné – **nefiltruje stav ani platnost**.

MST rozšíření (MST portfolio.py:21-147):
- Pole: `code` (24), `measurement_category_id` (25-29, M2O `investra.measurement.category`, restrict, tracking, **nepovinné**), `business_model` selection_add `na` (30), `classification_reason_id` (31-33), `reason_help` (34), `strategy_description`, `sales_policy_description`, `valid_from` (37, default today), `valid_to` (38), `state` (39-42) `draft`/`approved`/`closed`, default draft, readonly, `approved_by`, `approved_on`, `review_frequency`, `last_review_date`, `next_review_date`, `is_locked`/`lock_date` (50-51 compute `_compute_lock`). `_code_uniq` UniqueIndex `(fund_id, code) WHERE code IS NOT NULL` (53).
- `LOCKED_PORTFOLIO = ("measurement_category_id","business_model","classification_reason_id","fund_id")` ř. 15; `STATE_FIELDS = {"state","approved_by","approved_on"}` ř. 17; `_BUTTON_OK` ř. 18; `APPROVER_GROUP = "investra_entity.group_valuation_approver"` ř. 9.
- `_onchange_measurement_category_id` 55-60 (model podle `CATEGORY_MODEL`).
- `_compute_lock` 62-71: `trade_date:min` obchodů portfolia (sudo `_read_group`).
- `_check_category_model` 73-81, `_check_validity` 83-87, `_check_state_write` 89-91, `create` 93-97, `write` 99-114 (zámek po obchodu; po změně kategorie/modelu `classification_ids._check_category_compatibility()`).
- `_missing_for_approval` 118-121: povinné `code, measurement_category_id, classification_reason_id, assessment, valid_from`.
- `action_approve` 127-139 (jen schvalovatel, jen z `draft`, zápis sudo s `_BUTTON_OK`: state approved, approved_by, approved_on); `action_close` 141-147 (state closed, `valid_to` = dosavadní nebo dnes).
- MST pohledy `views/portfolio_views.xml`: `view_portfolio_form_master` (ř. 4, inherit `investra_instruments.view_portfolio_form`; `measurement_category_id` ř. 30 `required="state == 'draft'"`, tlačítka ř. 8-17, `valid_from`/`valid_to` ř. 54), `view_portfolio_search` ř. 68, `view_portfolio_list_master` ř. 84-99. Profil na portfoliu `accounting_profile_views.xml:100-118` (`view_portfolio_form_profile`, stránka za `governance`).

`investra.measurement.category` (MST `models/classification_codes.py:5-19`): `_inherit = ["investra.codelist.mixin","mail.thread"]`; `help_text`, `ifrs9_category` Selection `[("fvtpl","FVTPL"),("fvoci","FVOCI"),("amortised","Naběhlá hodnota")]` required; `create` jen superuživatel. Mixin `codelist_mixin.py` dává `code`, `name`, `valid_from`, `valid_to` (ř. 19) a display „kód název“. Data `data/measurement_category.xml` (`noupdate="1"`): `measurement_ac` (AC, amortised), `measurement_fvoci_d` (FVOCI_D, fvoci), `measurement_fvoci_e` (FVOCI_E, fvoci), `measurement_fvtpl` (FVTPL, fvtpl). Důvody `data/classification_reason.xml`: `reason_business_model` BUSINESS_MODEL, `reason_sppi_fail`, `reason_mandatory_fvtpl`, `reason_fvtpl_designation`, `reason_equity_fvoci_election`, `reason_other`.

Výběr portfolia na obchodu (INS instrument.py): pole ř. 675-678 `domain="[('fund_id', '=', fund_id)]"` (bez stavu a platnosti); `portfolio_choice` 754-757 = `len(fund_id.portfolio_ids) > 1`; `default_get` 735-747 (`fund._default_portfolio()`); `_onchange_fund_id` 899-902; `_onchange_sale_portfolio` 864-872 (prodej: portfolio z držby); `create` 1059-1063 (bez portfolia → `_default_portfolio`, jinak UserError „Fond má víc obchodních modelů; vyberte…“); `_check_portfolio` 904-908. Formulář obchodu: portfolio jen při `portfolio_choice` (instrument_views.xml:205-208). **Stav ani platnost portfolia se dnes nikde při obchodu, splátce, dividendě ani ocenění nekontroluje.**

---

## D. Typ nástroje a nástroj

Typ `investra.instrument.type` (INS instrument.py:85-126): `code`, `name`, `active`, `group` (listed/debt/money_market/loan/derivative/other_holding), `kind` (equity/bond/fund/participation/loan/derivative/deposit/repo/other_holding), `ifrs9_category` „Navržená kategorie IFRS 9“ required (111), `valuation_method` „Navržený způsob ocenění“ required (112), `role_id` „Navržená role účtu“ required, restrict (113), `cnb_sheet` „Navržený list ČNB“ (114), `max_price_age` „Navržené maximální stáří ceny (dny)“ (115-119), `isin_required`, `code_prefix`. MST přidává `ba0088_required` (MST instrument.py:35-37; data MST `data/instrument_type.xml`: deposit/repo/loan = False).
Data typů INS `data/instrument_type.xml` (`noupdate="1"`) – `valuation_method` / `role_id`: equity price/role_instrument; fund price/role_instrument; bond price/role_instrument_debt; deposit amortised/role_deposit; repo amortised/role_repo; loan model/role_loan_given; participation model/role_participation; derivative_listed price/role_derivative; derivative_otc contract/role_derivative; other_holding position/role_other_holding.
Kdo čte `type.role_id`: `_proposal` (portfolio.py:435), NAV valuation.py:364, DER valuation.py:60. `type.valuation_method`: `_proposal` (430-434). Pohledy typu: instrument_views.xml:279-288 (list, ř. 285), `view_instrument_type_form` 290-318 (ř. 306-310).

Nástroj `investra.instrument` (INS instrument.py:129-373): `cnb_sheet` (155), `max_price_age` (156-160), `deviates_from_type` (161, compute 302-306 – porovnává jen `cnb_sheet`), `fair_value_level` (162, `"1","2","3"`), `market = fields.Char(string="Trh")` (163), `price_excludes_accrued` (171-175, compute 292-295 = `kind == "bond"`, store, readonly=False), `classification_ids` (196-199).
- `_type_proposal(self, kind)` ř. 210-211: `{"cnb_sheet": kind.cnb_sheet, "max_price_age": kind.max_price_age}`; použití `create` ř. 261-263 (`setdefault`), `_onchange_type_id` ř. 287-290.
- `LOCKED_AFTER_TRADE = {"type_id","currency_id"}` ř. 18; `NAV_INSTRUMENT_FIELDS` ř. 26-29 (obsahuje `max_price_age`).
- `market`: čte ho jen pohled `instrument_views.xml:73` (`invisible="type_group != 'listed'"`). V Pythonu, testech, tools ani datech se nepoužívá.
- `max_price_age` čte NAV valuation.py:2468-2471 (`_stale_prices`) a dashboard.py:390. `cnb_sheet` a `fair_value_level` žádná logika (jen pohledy, seed).
- Formulář nástroje `view_instrument_form` instrument_views.xml:34-124: skupina „Ocenění a klasifikace“ ř. 77-82, upozornění na typ ř. 84-86, záložka zařazení ř. 106-113 (`valuation_method`, `role_id`).

Jmenovitá hodnota kusu:
- `principal` – NAV instrument_accrual.py:24-27 `fields.Float(digits=(20,2), string="Jistina na jednotku")`, help „Doporučeno 1: kusy obchodu = jistina, cena na jednotku jistiny.“ Použití: `_principal_per_unit` ř. 115-120 (= součet toků Jistina v kalendáři, jinak `principal`, jinak 1), generátor kalendáře ř. 52-…, `_position_principal` ř. 503-506 (kusy × jistina na jednotku).
- `nominal_value` – MST instrument.py:55 `fields.Monetary("Nominál", currency_field="currency_id")`, kontrola ≥ 0 ř. 147-153; v logice se nepoužívá. Seed dluhopisů: `nominal_value: 10000` a `principal: 10000` (tools/demo_data/seed.py:219-241), ceny obchodů 9850/10050 za kus (seed.py:593-595).
- `face_value`, `nominal` u nástroje neexistuje (DER `nominal` = nominál otevřených noh smlouvy).
- Toky kalendáře `investra.instrument.cashflow.amount` = „Částka na jednotku“ (instrument.py:389); úrok/splátky: `_schedule` (instrument_accrual.py:508-…) a `_fair_value_interest` (268-311) násobí tok × kusy; `_calendar_accrued_interest` (969-973) = |kusy| × `_accrued_coupon_unit`.
- **Nejasné:** který z `principal` / `nominal_value` je „jmenovitá hodnota kusu“ pro zadání ceny v % (INS, kde je obchod i cena, nemá ani jedno; `principal` je v NAV, `nominal_value` v MST).

---

## E. Ceny

Obchod: `quantity` (688, help „Kladně nákup, záporně prodej.“), `side`/`units` (690-693), `price = fields.Float(required=True, digits=(20,8), string="Cena")` (697, bez help), `accrued_interest` (700-704, jen dluhopis, kladně; „Platba obchodu = kusy × cena + naběhlý úrok“), `_signed_accrued_interest` 955-958, kontrola `_check_accrued_interest` 940-953. Hodnota obchodu `_event_lines` ř. 1132-1136: `foreign = self.quantity * self.price`; `interest_foreign = _signed_accrued_interest()`; `amount = round(foreign*fx)`; `interest = round((foreign+interest_foreign)*fx) - amount`. Předvyplnění úroku NAV instrument_accrual.py:975-992 (onchange + create). Další použití `trade.price` (za kus): NAV instrument_accrual.py:164, 299; valuation.py:758, 1009; trade_preview.py (nápověda ceny 76-89 `price_hint`).
`price_excludes_accrued` (nástroj): dluhopis zaškrtnuto → RH = kusy × cena + naběhlý úrok (cena je čistá, za kus).

Schválená cena `investra.instrument.price` (INS instrument.py:434-659): docstring „Cena k datu v jednotkách měny nástroje za kus“; pole `instrument_id`, `instrument_code`, `instrument_isin`, `fund_id` (prázdné = sdílená), `scope`, `company_id`, `book_warning`, `date`, `price = fields.Float(required=True, digits=(20,8), string="Cena", tracking=True, help="V jednotkách měny ceny za kus.")` (463), `previous_price_hint` (464, compute 539-557), `currency_id` (465-468), `source` (req), `deviation_reason`, `state` draft/approved, `entered_by`, `approved_by`. `SYSTEM_PRICE_FIELDS` ř. 80, `PRICE_INPUT_FIELDS` ř. 82. `_last_approved_for` 497-510; `action_approve` 642-655 (matice `price_approve`). U dluhopisů je cena **bez AÚV** (plyne z `price_excludes_accrued`, valuation.py:580-582).
Import cen: **žádný modul cenu nástroje nezapisuje** (investra_rates/cnb jsou kurzy měn a mapování výkazů); zakládá ji jen ruční zadání a skripty `tools/demo_data/seed.py:272`, `tools/nav_demo/demo.py:71`, `demo_prehled.py:57, 90`, `tools/vzhled_fiktivni_data.py:83`. Čtení: NAV valuation.py:499-508 `_approved_price`, 2477, 2541; dashboard.py:379-390; NAV `price_usage.py` (_inherit).
Ocenění `_compute_portfolio` ř. 578-584: `value_ccy = d(quantity) * d(price.price)`; `+ accrued_ccy` při `instrument.price_excludes_accrued`; `fair_value_currency = value_ccy` (`_portfolio_row` ř. 693); amortised větev ř. 574-577 bez ceny.
Formuláře: obchod `investra_instruments.view_trade_form` (instrument_views.xml:176-278; skupina `trade_price` ř. 240-248, `price` ř. 243, `accrued_interest` ř. 247; zařazení ř. 265-268); dědí NAV `views/trade_views.xml:31` `view_trade_form_preview` (xpath `//group[@name='trade_price']/field[@name='accrued_interest']` ř. 60) a ř. 76 `view_trade_form_derecognition`; list obchodů `view_trade_list` ř. 133-150. Cena `investra_instruments.view_price_form` ř. 351-382 (`price` ř. 370), `view_price_list` ř. 326-350, `view_price_search` ř. 383.

---

## F. Účetní profily (MST `models/accounting_profile.py`)

- `investra.accounting.profile` (9-16): codelist mixin + `role_id` M2O account.role required, `note`.
- `investra.accounting.profile.assignment` (19-114): `company_id` (compute z portfolia, store, required, precompute), `portfolio_id` (prázdné = všechna), `ba0088_id` (domain selectable), `ba0088_group_id`, `accounting_profile_id` required, `role_id` related, `priority` (default 10, nižší vyhrává), `valid_from` required, `valid_to`, `note`. `_order = "company_id, priority, id"`. **Žádné pole `instrument_id`.**
- Constrains: `_check_code_or_group` 59-62; `_check_validity` 64-68; `_check_portfolio_company` 70-77; **`_check_overlap` 79-92** (doména: company, portfolio, ba0088_id, ba0088_group_id, priority, překryv platností → ValidationError „Pro tuto kombinaci a prioritu už platí pravidlo %s.“).
- `_select(self, company, portfolio, ba0088, day)` 94-114: hledá podle firmy a platnosti, portfolio prázdné nebo shodné; filtr kód / skupina (`ba0088.group_id`) / obecné; řazení `(priority, 0 kód / 1 skupina / 2 obecné, 0 s portfoliem / 1 bez, id)`; vrací `rules[:1]`.
- Zařazení: `_compute_accounting_profile` 134-145 (`profile_state` ok/missing/deviates proti `role_id`), `_profile_rule` 147-153 (**den = max(dnes, valid_from)**, ne datum obchodu), `_require_profile` 155-164 (UserError „Pro portfolio %(p)s a druh %(k)s není nastaven účetní profil.“). **`_require_profile` se v produkčním kódu nikde nevolá** – jen v testech (test_accounting_profile.py:113, 121).
- Seed: modul žádná data profilů ani pravidel nemá; zakládá je jen `tools/demo_data/seed.py:501-521` (profily AP-AKCIE/AP-DLUH/AP-VKLAD/AP-UVER na role instrument/instrument_debt/deposit/loan_given; pravidla podle `ba0088` nástroje, bez něj podle portfolia; roli bere z `record.role_id` zařazení).
- Role → účet: investra_entity `models/account_role.py:33-41` `account_for(company, code)` (hlavní účet mapování `investra.role.account`, jinak UserError „Kniha %(book)s nemá účet pro roli %(role)s.“) a `:43-49` `accounts_for(company, code)` (hlavní + `extra_account_ids`). Účtování pracuje s kódem role v řádku (`{"role": code, …}`), převod na účet dělá `investra.accounting.event._create_event`.
- Obchod bere roli zařazení: INS instrument.py:1192 (`_planned_postings`), 1165 (`_fee_settlement_lines`; `_fee_lines(role, …)` ji pak dává řádku kapitalizovaného poplatku 1038). Splátka: instrument_accrual.py:829. Ocenění: valuation.py:554 (+ 522). Náhled prodeje: trade_preview.py:206.
- Role mimo profily dnes: `_proposal_role` (účast FV → `role_participation_fv`; counterparty: repo s nebankou → `role_repo_client`). Typy repo/vklad/úvěr nemají povinné BA0088 (MST data/instrument_type.xml), takže je `_select` podle druhu nerozliší.

---

## G. Testy, které po změně padnou (soubor : třída.metoda – důvod)

Ruční kategorie / gate:
- INS `tests/test_classification.py:166` `TestClassificationRules.test_fund_units_never_amortised_or_fvoci` (ř. 175 `category_override`).
- INS `tests/test_classification.py:231` `TestClassificationRules.test_manual_override_needs_reason_and_is_documented` (celý test o override).
- NAV `tests/test_accrual.py:601` `TestAccrual.test_manual_override_warns_in_valuation` (override + kontrola `classification_override`).
- NAV `tests/test_approval_matrix.py:290` `TestApprovalMatrix.test_classification_override_needs_request` a `:306` `test_classification_override_one_person_is_logged`.
- investra_fund `tests/common.py:15` (seznam činností obsahuje `classification_override`) – upravit při zrušení činnosti.

Návrh / odchylka / ruční způsob ocenění a role:
- INS `tests/test_instrument.py:221` `TestInstrumentType.test_type_prefills_proposal` (`deviates_from_proposal`, `deviates_from_type`; deposit ve fair_value čeká `valuation_method == "model"`).
- `:232` `test_accountant_can_override_proposal` (ruční `valuation_method`, `deviates_from_proposal`).
- `:239` `test_override_is_tracked` (zápis `valuation_method`).
- `:249` `test_override_at_creation_keeps_rest_of_proposal` (`valuation_method="model"` při create; role `instrument_debt` z typu).
- `:257` `test_form_fills_proposal` (Form zařazení, `form.valuation_method`).
- `:279` `test_amortised_needs_matching_method` (`valuation_method="price"` v AC).
- `:283` `test_classification_locked_after_trade` (ř. 290 zápis `valuation_method`; ř. 295-296 druhé zařazení = „reklasifikace“).
- `:322` (`test_other_holding_is_own_group`) čte `valuation_method == "position"`.
- `:388` `TestChartRoles.test_participation_at_fair_value_has_own_role` (role z typu + `_proposal_role`, `deviates_from_proposal`).
- investra_counterparty `tests/test_counterparty.py:98` `TestRepoRole.test_bank_counterparty_keeps_repo`, `:101` `test_non_bank_counterparty_is_repo_client` (role repo podle protistrany, `deviates_from_proposal`).
- INS `tests/test_tracking.py:30` `TestInstrumentTracking.test_instrument_type_tracking` (setUp ř. 20-21 a ř. 37 zapisují `valuation_method`, `role_id` typu).
- MST `tests/test_portfolio.py:60` `test_ac_accepts_sppi_bond` (čte `valuation_method`) – projde, pokud computed AC → amortised.

Profily:
- MST `tests/test_accounting_profile.py` setUp 13-23 (profily z `classification.role_id` – role už bude z profilu), `:50` (`profile_state` ok), `:79` (missing), `:109` `test_missing_profile_state_and_require_profile`, `:115` `test_role_deviation_is_shown_and_nothing_is_overwritten` (`deviates`, role zařazení se nemění). `:87`/`:92` (`_check_overlap`) – změna, přidá-li se `instrument_id` do domény.

Portfolio bez kategorie / zařazení před obchodem:
- MST `tests/test_portfolio.py:126` `test_portfolio_without_category_behaves_as_before` (portfolio bez kategorie).
- INS `tests/test_classification.py:49` `test_trade_without_classification_is_not_booked` (čeká UserError; po změně se zařazení založí, nebo chyba přijde z neschváleného portfolia / chybějící kategorie).
- Fixtures `portfolio()`/`classify()` v INS `tests/test_instrument.py:35-48` a NAV `tests/common.py:65-82` zakládají portfolia **bez kategorie, ve stavu draft** a zařazení ručně; portfolio „Hlavní“ vzniká s fondem bez kategorie. S povinnou kategorií, schváleným portfoliem a rolí z profilů selže každý test, který zaúčtuje obchod/splátku/dividendu nebo počítá ocenění (testy volající `classify(`/`portfolio(`: INS test_classification (41×), test_instrument (15×); NAV test_accrual, test_approval_matrix, test_benchmark, test_company_access, test_derecognition, test_dividend, test_dividend_event, test_draft_delete, test_ex_coupon, test_fair_value_interest, test_fvoci, test_portfolio_class, test_posting_preview, test_shared_price, test_tax_rules, test_tax_rules_models, test_trade_fee, test_trade_preview, test_trade_recognition, test_variable_rate, test_workflow; cnb test_cnb_map; dashboard test_dashboard; DER test_portfolio_class.py:23 – DER tests/common.py portfolia nezakládá).
- NAV `tests/test_fvoci.py:37` zakládá FVOCI akcie volbou `designation` ručně (bez portfolia FVOCI_E) – po rozhodnutí 3 bude volba z portfolia.

Trh / typ: žádný test `market` nečte.

---

## H. Seed, demo a testovací data (portfolia, zařazení, profily)

- Modulová data: INS `InvestraFund.create` (portfolio.py:659-668) = portfolio „Hlavní“ bez kategorie; jiná XML data s portfolii/zařazeními/profily nejsou. Kategorie MST `data/measurement_category.xml`, důvody `data/classification_reason.xml`.
- Migrace: INS `migrations/20.0.0.4.0/post-migration.py` (portfolia „Hlavní/Držet pro inkaso/Inkaso i prodej“ a zařazení z dřívějších polí nástroje), `20.0.0.5.0` (volá `_check_classification`), counterparty `20.0.0.2.0` (volá `_proposal` s `category_override`, nastavuje `role_id`).
- `tools/demo_data/seed.py`: `CATEGORY` ř. 286 (jen `ac`, `fvtpl`), `REASONS` ř. 285; `Fund.portfolio()` 308-321 (kategorie, důvod, `action_approve()`; první portfolio přepíše „Hlavní“); `classify()` 323-326 (zařazení ručně); portfolia A-FV, B-FV, B-AC, C-UV, C-VK, D-FV, D-AC, E-FV (ř. 435-496); profily a pravidla 501-521; obchody `trade()` 376-387.
- `tools/nav_demo/demo.py:55`, `demo_prehled.py:44-46`, `demo_vklad.py:54-59` (portfolio „Držet pro inkaso“ bez kategorie), `tools/vzhled_fiktivni_data.py:64-76` (portfolio „Reálná hodnota“ bez kategorie, zařazení ručně).
- Testové fixtures viz G (INS test_instrument.py:35-48, NAV tests/common.py:65-82, MST test_portfolio.py:26-30 `make_portfolio`, MST test_accounting_profile.py:13-46, DER test_portfolio_class.py:23).

---

## I. Nejasnosti a rizika

1. **Závislosti:** kategorie, stav a platnost portfolia i profily jsou v MST; obchod (INS), splátka/dividenda/ocenění (NAV) MST neznají a `tools/run_tests.sh investra_nav` MST neinstaluje. Nejasné: zda auto-zařazení a výběr role dělat v MST přepisem (`_classification`, `_planned_postings`…), nebo přesunout pole níž / přidat závislost.
2. Fond při založení dostane „Hlavní“ bez kategorie (INS) – koliduje s povinnou kategorií; MST view má `required="state == 'draft'"`, model ne.
3. `trade.classification_id`, `ifrs9_category` a `fee_treatment` jsou neuložené computy; po založení zařazení v `_book` je nutné je zneplatnit, jinak se poplatek zaúčtuje jako náklad místo kapitalizace. Náhled (`_ready_for_preview`, trade_preview.py:143-146; `_preview_documents` splátky/dividendy volá `_validate`) bez existujícího zařazení dnes nic neukáže.
4. Splátka kontroluje zařazení v `@api.constrains` (instrument_accrual.py:741-763) – při uložení, ne při zaúčtování.
5. `_profile_rule` počítá den jako max(dnes, valid_from), ne datum obchodu; `_select` neumí nástroj; role repo s nebankou a účast FV (`_proposal_role`, counterparty) profily podle BA0088 nerozliší (repo/vklad/úvěr BA0088 nemají) – pokryje jen nové `instrument_id` nebo pravidla na portfolio.
6. Zrušení `role_id` na typu rozbije `_position_balance` (NAV valuation.py:364) a DER valuation.py:60 (berou role všech typů).
7. Způsob ocenění: ocenění rozlišuje jen `amortised` vs. ostatní (cena × kusy); typy deposit/repo mají `valuation_method = amortised` a `_proposal` je mimo AC mění na `model`. Nejasné: výchozí „Určení reálné hodnoty“ pro deposit/repo (selekce nástroje asi bez `amortised`).
8. Cena v %: INS nemá jmenovitou hodnotu kusu; kandidáti `principal` (NAV, „Jistina na jednotku“) a `nominal_value` (MST, „Nominál“) – nejasné, který použít; u dluhopisů je cena čistá (bez AÚV).
9. FVOCI_E portfolio má `business_model = "na"`, které zná jen MST; designation `fvoci_equity` vyžaduje `designation_note` (`_check_classification` 562-563).
10. Mixin `investra.approval.pending.mixin` na zařazení slouží dnes jen ruční kategorii; činnost `classification_override` je v investra_fund (selekce `ACTIVITIES`, `BUILTIN`, XML) – při odstranění hodnoty selekce a záznamu matice je potřeba migrace existujících řádků matice/žádostí (nejasné, zda v DB existují).
11. Derivát zakládá zařazení sudo bez kontroly portfolia; po rozhodnutí 2 je třeba sjednotit (schválené a platné portfolio).
