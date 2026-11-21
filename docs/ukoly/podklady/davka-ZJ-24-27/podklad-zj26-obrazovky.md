# ZJ-26 Jednotný vzhled – technický podklad pro provedení

Zdroj: větev `origin/ukol/ZJ-24-hlasky-a-sazby` (stav 2026-11-20). Verze modulů `20.0.x` → **Odoo 20** (obraz
`odoo:20.0-20261102`). Struktura skupin ověřena ve zdrojích Odoo větve `20.0` (`web/static/src/views/form/`).
Zadání: `zadani-ZJ-25-26-oceneni-a-vzhled.md`, oddíl 2. Rozhodnuto: varianta B, popisky 200 px, u CP nadpis „ISIN + název“,
co je v pásu, se v sekcích neopakuje, upozornění pod pásem, štítky normálním písmem, číslování 1.–3. jen u Úpisu a odkupu.

Pravidla provedení (platí pro celý dokument):
- Přepiš `arch` přesně podle cílového XML níže. Atributy polí (`invisible`, `readonly`, `required`, `widget`, `options`,
  `context`, `domain`, `groups`, `force_save`, `placeholder`, `decoration-*`) se kopírují beze změny, pokud u pole není
  výslovně uvedeno jinak. Komentáře `<!-- … -->` z dnešních pohledů zachovej u příslušného prvku.
- Vnořené pohledy x2many (`<list>`/`<form>` uvnitř `<field>`) se nemění, jen se přesouvají s polem.
- Kontrolní součet = počet polí `<field>` v pohledu mimo vnořené `<list>`/`<form>` (vč. neviditelných). Po úpravě spočítej
  znovu stejným způsobem; musí sedět s číslem „po“.
- Nové třídy CSS: `o_investra_band` / `o_investra_band_item` / `o_investra_band_label` (pás údajů),
  `o_investra_metric_strip` / `o_investra_metric_item` (pás čísel – stávající), `o_investra_alerts` (kontejner upozornění),
  `o_investra_title` / `o_investra_title_sub` (nadpis ISIN + název), dialogy `o_investra_dialog_subject`,
  `o_investra_dialog_effect`, `o_investra_btn_ember`. SCSS v oddílu 3.
- Stabilní kotvy pro dědění: `<div name="investra_band">`, `<div name="investra_alerts">` a `name=` na každé `<group>`.
  (`name` na `div` Odoo připouští, viz `div name="button_box"`.)
- Testy, které čtou `arch` a omezují úpravu (nesmí se rozbít):
  - `investra_nav/tests/test_trade_preview.py:72` – v `view_trade_form` musí zůstat `invisible="not foreign_currency"`.
  - `investra_nav/tests/test_accrual.py:391-405` – ve `view_repayment_form` musí zůstat `invisible="not foreign_currency"`,
    `invisible="kind != 'extraordinary'"` a **první výskyt `name="fund_id"` musí být v arch před prvním `name="kind"`**.
  - `investra_instrument_master/tests/test_instrument.py:67-70` – ve složeném formuláři nástroje musí být pole
    `maturity_date, nominal_value, coupon_type, coupon_rate, asset_family, ba0088_id, cfi_code` a text `asset_family != 'debt'`.
  - `investra_nav/tests/test_tracking_zj10.py:138-142` – `view_fee_rule_form` má přesně jeden `<chatter`.
  - `investra_chart_fund/tests/test_new_book.py:96-99` – `parent_id` v průvodci knihou má `invisible` i `required` se `subfund`.
  - `investra_instrument_master/tests/test_new_book_identification.py:144-147` – v průvodci pole `partner_id, company_registry,
    vat, lei, esa_code_id` a `//field[@name='name' and @readonly='partner_id']`.
  - Texty historie: `investra_nav/tests/test_manual_fees.py:207` („Vstupní poplatek – článek statutu“) a
    `investra_nav/tests/test_shared_price.py:129` („Maximální stáří ceny (dny)“) → tyto popisky v Pythonu **neměnit**.

---

## 0. Změny po ZJ-27 (poradce 2026-11-21) – mají přednost před oddíly 1–4

ZJ-26 běží až po ZJ-27 (větev z `ukol/ZJ-27-zarazeni-z-obchodu`). Podklad níže popisuje stav před ZJ-27; u dotčených obrazovek proto:
1. **Kontrolní součty polí** přepočti na začátku každé dotčené obrazovky na skutečném stavu po ZJ-27 („před“) a stejné číslo musí vyjít „po“.
2. **Obchod (1.1):** pás: Fond, Portfolio, Nákup/prodej, Datum obchodu. Sekce **Cena** (Kusy, Drženo, Zadání ceny `price_mode` jako
   `widget="radio" options="{'horizontal': true}"` jen u dluhových, Cena / Cena v % s textem „= … za kus“, Naběhlý úrok) | **Vypořádání**
   (Datum vypořádání, Místo obchodu `venue`, kurz). Skupina **Zařazení**: v návrhu `classification_preview` (šedý text), po zaúčtování
   `classification_id`, `ifrs9_category`, způsob ocenění a role (related). Poplatek | Odúčtování beze změny.
3. **Nástroj (1.5):** pás: Typ, Měna, Jmenovitá hodnota kusu (`principal`, je-li dluhový), Splatnost – **bez Trhu** (pole neexistuje).
   Sekce „Ocenění a klasifikace“ → **Ocenění**: Určení reálné hodnoty (`fair_value_method`), Úroveň RH, Max. stáří ceny, List ČNB;
   `nominal_value` zůstává v arch (test MST `test_instrument.py:67-70`), ale `invisible="1"`. Chytré tlačítko Účetní zůstatky v `button_box`.
4. **Dialog 11 Ruční kategorie IFRS 9 (2.2) vypouští se** – po ZJ-27 neexistuje. Nový dialog **Převést pozici na nový účet** (ZJ-27 K5b):
   nadpis „Převést pozici na nový účet“, první řádek ISIN + název · portfolio, tabulka stará role → nová role, zůstatek; Datum; „Co se stane“:
   převodový doklad k datu, starší doklady se nemění; tlačítka „Převést pozici“ (primární) a „Zpět“. Dialogů je 14.
5. **Nové obrazovky ze ZJ-27** upravit stejnými zásadami (nadpis, pás, sekce B), každá samostatný commit:
   - **Zařazení** (jen pro čtení): nadpis „ISIN + název · portfolio“; pás Kategorie IFRS 9, Způsob ocenění, Role účtu (+ šedě pravidlo), Od;
     šedá poznámka „Vzniklo z …“; sekce Podklad (Povaha, Test SPPI) | Účetní profil (Profil, Stav); sbalený Postup klasifikace.
   - **Portfolio:** nadpis název (+ šedě kód); pás Fond, Třída, Oceňovací kategorie, Obchodní model, Stav a platnost; sekce Klasifikace
     (Důvod, Posouzení) | Řízení a kontrola (Schválil, Revize); záložky Nástroje v portfoliu (3 sloupce), Strategie, Účetní profil.
   - **Schválená cena:** pás Nástroj, Datum, Měna, Stav; sekce Cena (Zadání ceny jen u dluhových, Cena / Cena v %) | Zdroj (Zdroj, Odchylka).
   - **Role účtu (detail):** nadpis název role (+ šedě kód); záložky Účty v knihách, Kdy se použije, Události účtování.
   - **Pravidla účtování** (seznam): seskupení podle události, sloupce Krok, MD/D, Role, Poznámka.
6. Popisek „Jistina na jednotku“ se ve formuláři nástroje zobrazuje jako „Jmenovitá hodnota kusu“ (jen `string` v pohledu).

## 1. Obrazovky

Souhrn kontrolních součtů (pole mimo vnořené pohledy):

| # | Obrazovka | Před | Po | Rozdíl |
|---|---|---|---|---|
| 1 | Obchod (`view_trade_form` + 2 dědění) | 33 + 5 + 4 = 42 | 42 | 0 |
| 2 | Úpis a odkup (`view_movement_form`) | 44 | 45 | +1 (`state` jako štítek v pásu) |
| 3 | Pravidlo úplaty (`view_fee_rule_form`) | 21 | 21 | 0 |
| 4 | Třída fondu (`view_fund_class_form` + 1 dědění) | 22 + 1 = 23 | 23 | 0 |
| 5 | Nástroj (`view_instrument_form` + 4 dědění) | 38 + 1 + 22 + 0 + 7 = 68 | 68 | 0 |
| 6 | Splátka (`view_repayment_form`) | 24 | 24 | 0 |
| 7 | Derivát (`view_derivative_form`) | 17 | 17 | 0 |
| 8a | Dividenda (`view_dividend_event_form`) | 14 | 14 | 0 |
| 8b | Řádek dividendy (`view_dividend_form`) | 28 | 28 | 0 |
| 9 | Účetní událost (`view_event_form`) | 18 | 18 | 0 |
| 10 | Daňové pravidlo (`view_tax_rule_form`) | 11 | 11 | 0 |

---

### 1.1 Obchod – `investra_instruments.view_trade_form`

- Soubor: `addons/custom/investra_instruments/views/instrument_views.xml:176-278`, model `investra.trade`.
- Dědění:
  - `investra_nav.view_trade_form_preview` – `investra_nav/views/trade_views.xml:31-74`
  - `investra_nav.view_trade_form_derecognition` – `investra_nav/views/trade_views.xml:76-94`

**Dnes** (`<form class="o_investra_trade_form">`):
- header: `action_book` (Zaúčtovat, btn-primary, `invisible="state != 'draft'"`), `action_settle` (Vypořádat, btn-primary,
  `invisible="state != 'unsettled'"`), `state` statusbar `draft,unsettled,settled`. Dědění preview přidá před `state` 3 tlačítka
  `%(action_trade_reverse_wizard)d` (Stornovat vypořádání / Opravit / Stornovat).
- sheet (pořadí): alert-danger `invisible="state != 'reversed'"` s `reversal_reason`; alert-warning `invisible="not settlement_fx_note"`
  s `settlement_fx_note`; neviditelná `held_instrument_ids, portfolio_choice, foreign_currency, quantity(force_save)`;
  `div.oe_title` → `o_investra_metadata` (fund_id; „Třída:“ portfolio_class_id; portfolio_id; text „Sdílené portfolio“) →
  `h1` instrument_id → `o_investra_metadata` (side „Nákup / Prodej“, trade_date); `o_investra_metric_strip` (units,
  held_quantity, tlačítko `action_sell_all`); `group trade_content` = `trade_price` „Cena“ (div s label price + price +
  instrument_currency_id; instrument_kind; accrued_interest) | `trade_settlement` „Vypořádání“ (settlement_date, fx_rate,
  settlement_fx_rate) | `trade_fee` „Poplatek“ (fee_amount, fee_currency_id, company_currency_id, fee_fx_rate, fee_treatment);
  `group trade_classification` „Zařazení“ (classification_id, ifrs9_category); `group` „Účetní události“ (event_id,
  settlement_event_id, replaced_id, settlement_reversal_reason).
- Dědění preview: `//sheet/*[1]` before → `pending_request_id` + alert čekající žádosti; `//group[@name='trade_content']` before →
  alert `calendar_note`; před `trade_price/accrued_interest` → `price_hint`; `trade_classification/ifrs9_category` replace →
  `classification_summary`; `//group[@name='trade_content']` after → notebook `posting_preview`.
- Dědění derecognition: `//group[@name='trade_classification']` before → `group trade_derecognition` „Odúčtování“.

**Cíl** – celý `arch` základního pohledu:

```xml
<form class="o_investra_trade_form">
    <header>
        <button name="action_book" type="object" string="Zaúčtovat" class="btn-primary" invisible="state != 'draft'"/>
        <button name="action_settle" type="object" string="Vypořádat" class="btn-primary" invisible="state != 'unsettled'"/>
        <field name="state" widget="statusbar" statusbar_visible="draft,unsettled,settled"/>
    </header>
    <sheet>
        <field name="held_instrument_ids" invisible="1"/>
        <field name="portfolio_choice" invisible="1"/>
        <field name="foreign_currency" invisible="1"/>
        <field name="quantity" invisible="1" force_save="1"/>
        <div class="oe_title">
            <h1><field name="instrument_id" readonly="event_id or state in ('settled', 'reversed')"
                       domain="side == 'sell' and [('id', 'in', held_instrument_ids), ('type_id.kind', '!=', 'other_holding')] or [('type_id.kind', '!=', 'other_holding')]"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1" readonly="event_id or state in ('settled', 'reversed')"/>
            </div>
            <div class="o_investra_band_item" invisible="not portfolio_choice">
                <label for="portfolio_id"/>
                <field name="portfolio_id" nolabel="1" readonly="event_id or state in ('settled', 'reversed')" options="{'no_create': True}"/>
            </div>
            <div class="o_investra_band_item" invisible="not portfolio_class_id">
                <label for="portfolio_class_id" string="Třída"/>
                <field name="portfolio_class_id" nolabel="1" readonly="1"/>
            </div>
            <div class="o_investra_band_item" invisible="not portfolio_id or portfolio_class_id">
                <span class="o_investra_band_label">Portfolio</span>
                <span>Sdílené portfolio</span>
            </div>
            <div class="o_investra_band_item">
                <label for="side" string="Nákup / Prodej"/>
                <field name="side" nolabel="1" readonly="event_id or state in ('settled', 'reversed')"/>
            </div>
            <div class="o_investra_band_item">
                <label for="trade_date"/>
                <field name="trade_date" nolabel="1" readonly="event_id or state in ('settled', 'reversed')"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-danger" role="alert" invisible="state != 'reversed'">
                Obchod je stornovaný a nepočítá se do pozic. Důvod: <field name="reversal_reason" readonly="1" class="d-inline"/>
            </div>
            <div class="alert alert-warning" role="alert" invisible="not settlement_fx_note">
                <field name="settlement_fx_note" readonly="1"/>
            </div>
        </div>
        <div class="o_investra_metric_strip">
            <div class="o_investra_metric_item">
                <label for="units"/>
                <field name="units" nolabel="1" readonly="event_id or state in ('settled', 'reversed')"/>
            </div>
            <div class="o_investra_metric_item" invisible="side != 'sell'">
                <label for="held_quantity" string="Drženo"/>
                <field name="held_quantity" nolabel="1" readonly="1"/>
            </div>
            <div class="o_investra_metric_item" invisible="side != 'sell' or state != 'draft'">
                <button name="action_sell_all" type="object" string="Prodat vše"/>
            </div>
        </div>
        <group name="trade_content">
            <group name="trade_price" string="Cena">
                <label for="price" string="Cena za kus"/>
                <div class="o_row">
                    <field name="price" nolabel="1" readonly="event_id or state in ('settled', 'reversed')"/>
                    <field name="instrument_currency_id" nolabel="1" readonly="1"/>
                </div>
                <field name="instrument_kind" invisible="1"/>
                <field name="accrued_interest" invisible="instrument_kind != 'bond'" readonly="event_id or state in ('settled', 'reversed')"/>
            </group>
            <group name="trade_settlement" string="Vypořádání">
                <field name="settlement_date" readonly="state in ('settled', 'reversed')"/>
                <field name="fx_rate" invisible="not foreign_currency" readonly="event_id or state in ('settled', 'reversed')"/>
                <field name="settlement_fx_rate" invisible="not foreign_currency" readonly="state in ('settled', 'reversed')"/>
            </group>
        </group>
        <group name="trade_content_2">
            <group name="trade_fee" string="Poplatek">
                <field name="fee_amount" readonly="event_id or state in ('settled', 'reversed')"/>
                <field name="fee_currency_id" readonly="event_id or state in ('settled', 'reversed')" options="{'no_create': True}"/>
                <field name="company_currency_id" invisible="1"/>
                <field name="fee_fx_rate"
                       invisible="fee_currency_id == company_currency_id or (not fee_currency_id and not foreign_currency)"
                       readonly="event_id or state in ('settled', 'reversed')"/>
                <field name="fee_treatment" string="Účtování poplatku" readonly="1"/>
            </group>
            <group name="trade_classification" string="Zařazení">
                <field name="classification_id" invisible="1"/>
                <field name="ifrs9_category" readonly="1"/>
            </group>
        </group>
        <group name="trade_events" string="Účetní události" invisible="state == 'draft'">
            <field name="event_id"/>
            <field name="settlement_event_id"/>
            <field name="replaced_id" invisible="not replaced_id"/>
            <field name="settlement_reversal_reason" invisible="not settlement_reversal_reason"/>
        </group>
    </sheet>
</form>
```

Úpravy dědění (`investra_nav/views/trade_views.xml`):
- `view_trade_form_preview`:
  - `<xpath expr="//sheet/*[1]" position="before">` → `<xpath expr="//div[@name='investra_alerts']" position="inside">`
    (obsah – `pending_request_id` invisible + alert s tlačítkem `action_open_pending_request` – beze změny).
  - `<xpath expr="//group[@name='trade_content']" position="before">` (alert `calendar_note`) →
    `<xpath expr="//div[@name='investra_alerts']" position="inside">`.
  - `price_hint` (`//group[@name='trade_price']/field[@name='accrued_interest']` before) – beze změny, kotva platí.
  - `classification_summary` replace – beze změny, kotva platí.
  - `<xpath expr="//group[@name='trade_content']" position="after">` (notebook) → `<xpath expr="//group[@name='trade_events']" position="after">`.
- `view_trade_form_derecognition`: `<xpath expr="//group[@name='trade_classification']" position="before">` →
  `<xpath expr="//group[@name='trade_content_2']" position="after">` (skupina „Odúčtování“ celou šířkou pod Poplatek | Zařazení).

Výsledné pořadí: nadpis → pás → upozornění (storno, kurz vypořádání, čekající žádost, kalendář) → pás čísel → Cena | Vypořádání
→ Poplatek | Zařazení → Odúčtování (jen prodej) → Účetní události → záložka Zaúčtování.
Kontrola: základ 33 (state, held_instrument_ids, portfolio_choice, foreign_currency, quantity, instrument_id, fund_id, portfolio_id,
portfolio_class_id, side, trade_date, reversal_reason, settlement_fx_note, units, held_quantity, price, instrument_currency_id,
instrument_kind, accrued_interest, settlement_date, fx_rate, settlement_fx_rate, fee_amount, fee_currency_id, company_currency_id,
fee_fx_rate, fee_treatment, classification_id, ifrs9_category, event_id, settlement_event_id, replaced_id, settlement_reversal_reason)
+ preview 5 + derecognition 4 = 42.
Nadpis „ISIN + název“: `display_name` nástroje je už „ISIN název“ (`investra_instruments/models/instrument.py:236-239`); název
menším šedým viz Nejasnosti N1.

---

### 1.2 Úpis a odkup – `investra_nav.view_movement_form`

- Soubor: `investra_nav/views/nav_views.xml:827-961`, model `investra.class.movement`. Dědění z jiných modulů: **žádné**.

**Dnes**: header (Zaúčtovat; Opravit / Stornovat → `action_movement_reverse_wizard`; `state` statusbar `draft,posted`);
sheet: `pending_request_id` + alert čekající žádosti; `oe_title` h1 `fund_id` – `class_id`, pod ním `o_investra_metadata`
(movement_type, currency_id, date); alert `launch_warning`; group bez nadpisu (source, manual_reason, external_ref);
neviditelná foreign_currency, price_matches; group „1. Zadání“; group „2. Poplatek“ (uvnitř alert-info `fee_warning`);
group „3. Výsledek“; group vazeb (replaced_id, valuation_id, event_id); group reversal_reason; notebook Zaúčtování; chatter.

**Cíl**:

```xml
<form class="o_investra_movement_form">
    <header>
        <!-- beze změny: action_book, 2× action_movement_reverse_wizard, state statusbar -->
    </header>
    <sheet>
        <!-- MN-18: upozornění na čekající žádost (mixin investra.approval.pending.mixin) -->
        <field name="pending_request_id" invisible="1"/>
        <!-- Pomocná pole pro podmínky níže (neukládají se) -->
        <field name="foreign_currency" invisible="1"/>
        <field name="price_matches" invisible="1"/>
        <div class="oe_title">
            <h1>
                <field name="fund_id" readonly="1"/>
                <span> – </span>
                <field name="class_id" readonly="state != 'draft'"/>
            </h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="movement_type"/>
                <field name="movement_type" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item">
                <label for="date"/>
                <field name="date" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item">
                <label for="currency_id"/>
                <field name="currency_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <span class="o_investra_band_label">Stav</span>
                <field name="state" nolabel="1" widget="badge" readonly="1"
                       decoration-info="state == 'draft'" decoration-success="state == 'posted'" decoration-muted="state == 'reversed'"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-warning" role="alert" invisible="not pending_request_id">
                <strong>Čeká na potvrzení v Žádostech ke schválení.</strong>
                <button name="action_open_pending_request" type="object" class="btn btn-link p-0 ms-2" string="Otevřít žádost"/>
            </div>
            <div class="alert alert-warning" role="alert" invisible="not launch_warning">
                <field name="launch_warning" nolabel="1"/>
            </div>
            <div class="alert alert-info" role="alert" invisible="not fee_warning or state != 'draft'">
                <field name="fee_warning" nolabel="1"/>
            </div>
        </div>
        <group name="movement_source" string="Zdroj">
            <field name="source" readonly="state != 'draft'"/>
            <field name="manual_reason" readonly="state != 'draft'" required="source == 'manual'" invisible="source != 'manual'"/>
            <field name="external_ref" readonly="state != 'draft'" required="source == 'is'" invisible="source != 'is'"/>
        </group>
        <group name="movement_input" string="1. Zadání">
            <!-- obsah PŘESNĚ jako dnes nav_views.xml:888-911 (amount_class „Přijatá platba“, redemption_by, units „Kusy“,
                 requested_amount, label price + div.o_row s price / ikonou / zveřejněným kurzem / textem „První úpis…“,
                 price_reason, fx_rate) včetně komentářů -->
        </group>
        <group name="movement_fee" string="2. Poplatek">
            <field name="fee_rate_percent" string="Sazba třídy (%)"/>
            <field name="fee_percent" invisible="state != 'draft' or source != 'manual'"/>
            <field name="fee_amount_class" readonly="state != 'draft'"/>
            <field name="fee_recipient" readonly="state != 'draft'" required="fee_amount_class &gt; 0" invisible="not fee_amount_class"/>
            <field name="fee_partner_id" readonly="state != 'draft'"
                   invisible="not fee_amount_class or fee_recipient not in ('manager', 'distributor')"/>
        </group>
        <group name="movement_result" string="3. Výsledek">
            <!-- obsah jako dnes nav_views.xml:928-941, jen tři popisky kratší (oddíl 4):
                 capital_amount_class string="Změna kapitálu (měna kurzu)",
                 capital_amount string="Změna kapitálu (funkční)",
                 amount: přidat string="Hrubá částka (funkční)" -->
        </group>
        <group name="movement_links" string="Vazby" invisible="not replaced_id and not valuation_id and not event_id">
            <field name="replaced_id" invisible="not replaced_id"/>
            <field name="valuation_id" invisible="not valuation_id"/>
            <field name="event_id" invisible="not event_id"/>
        </group>
        <group name="movement_reversal" string="Storno" invisible="state != 'reversed'">
            <field name="reversal_reason"/>
        </group>
        <notebook invisible="not posting_preview">
            <page name="posting_preview" string="Zaúčtování">
                <field name="posting_preview" nolabel="1" readonly="1"/>
            </page>
        </notebook>
    </sheet>
    <chatter/>
</form>
```

Změny proti dnešku: pás doplněn o `state` (duplikát pole, readonly badge → +1 pole); `fee_warning` přesunut ze skupiny
„2. Poplatek“ do upozornění (atributy `mb-0`, `colspan="2"` odpadají); skupiny pojmenovány; Zdroj, 1., 2., 3. zůstávají pod sebou
(číslování 1.–3. ponechat). Vnitřní texty „text-danger“ (zbytek) a „text-warning“ (první úpis) zůstávají – nejsou to upozornění.
Kontrola 44 + 1 = 45.

---

### 1.3 Pravidlo úplaty – `investra_nav.view_fee_rule_form`

- Soubor: `investra_nav/views/nav_views.xml:622-730`, model `investra.fee.rule`. Dědění: **žádné**.

**Dnes**: `<form><sheet>` bez nadpisu; 4 alerty nahoře (info `invisible="kind != 'tax'"` s `fund_id` readonly; warning
`class_base_warning`, `overlap_warning`, `no_common_class_warning`); group (fund_id `readonly="context.get('investra_lock_fund')"
force_save`); group `invisible="kind == 'tax'"` (class_ids, recipient_share, recipient_class_ids, cover_class_id); group → group
(name, kind, statute_ref) | group (basis, base_source, base_step inv, base_step_fee, base_step_performance, base_step_tax,
expense_role, crystallisation); `version_ids` (list + form) pod tím; chatter.

**Cíl**:

```xml
<form>
    <sheet>
        <div class="oe_title">
            <h1><field name="name" placeholder="Název pravidla"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1" readonly="context.get('investra_lock_fund')" force_save="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="kind"/>
                <field name="kind" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="statute_ref" string="Článek statutu"/>
                <field name="statute_ref" nolabel="1"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <!-- ZJ-03 komentář + 4 alerty PŘESNĚ jako dnes nav_views.xml:627-640 (tax info s fund_id readonly, class_base_warning,
                 overlap_warning, no_common_class_warning) -->
        </div>
        <group name="fee_rule_main">
            <group name="fee_rule_target" string="Komu se účtuje" invisible="kind == 'tax'">
                <field name="class_ids" widget="many2many_tags" domain="[('fund_id', '=', fund_id)]" options="{'no_create': True}"/>
                <field name="recipient_share"/>
                <field name="recipient_class_ids" widget="many2many_tags" domain="[('fund_id', '=', fund_id)]" options="{'no_create': True}"/>
                <field name="cover_class_id" invisible="kind != 'performance'" domain="[('fund_id', '=', fund_id)]" options="{'no_create': True}"/>
                <!-- Rozhodnutí 2026-11-19: daň se účtuje vždy na roli Daň, třídy ani příjemce nemá. -->
                <field name="expense_role" invisible="kind == 'tax'"/>
            </group>
            <!-- ZJ-06 bod 10 / ZJ-12 komentáře přesunout sem -->
            <group name="fee_rule_calc" string="Výpočet">
                <field name="basis" invisible="kind == 'tax'"/>
                <field name="base_source" invisible="kind in ('tax', 'performance')"/>
                <field name="base_step" invisible="1"/>
                <field name="base_step_fee" invisible="kind != 'periodic' or base_source in ('assets', 'none')"/>
                <field name="base_step_performance" invisible="kind != 'performance'"/>
                <field name="base_step_tax" invisible="kind != 'tax'"/>
                <field name="crystallisation" invisible="kind != 'performance'"/>
            </group>
        </group>
        <notebook>
            <page name="versions" string="Verze sazby">
                <!-- ZJ-06 bod 11 komentář -->
                <field name="version_ids">
                    <!-- vnořený list a form PŘESNĚ jako dnes nav_views.xml:669-724 -->
                </field>
            </page>
        </notebook>
    </sheet>
    <!-- ZJ-10 fáze 2: historie pravidla … -->
    <chatter/>
</form>
```

Kontrola 21 = 21 (fund_id 2×: alert + pás, stejně jako dnes). „Historie“ = chatter (viz N4); jediný `<chatter/>` zůstává.

---

### 1.4 Třída fondu – `investra_fund.view_fund_class_form`

- Soubor: `investra_fund/views/fund_views.xml:89-126`, model `investra.fund.class`.
- Dědění: `investra_nav.view_fund_class_form_lock` – `investra_nav/views/nav_views.xml:589-597`
  (`<field name="code" position="before">` movement_locked inv.; atributy `readonly=movement_locked` na `code` a `currency_id`).

**Dnes**: ribbon Archivováno + active inv.; group → „Třída“ (fund_id readonly=id, code, name, currency_id, isin, distribution,
sequence, shares_common) | „Kurz a kusy“ (price_digits, price_rounding, unit_digits, unit_rounding, rounding_owner); group →
„Vstupní poplatek“ (entry_fee_rate „Sazba (%)“, entry_fee_recipient „Příjemce“, entry_fee_statute_ref „Článek statutu“,
entry_fee_note „Poznámka“) | „Výstupní poplatek“ (totéž exit_*); chatter. Bez nadpisu.

**Cíl**:

```xml
<form>
    <sheet>
        <widget name="web_ribbon" title="Archivováno" bg_color="text-bg-danger" invisible="active"/>
        <field name="active" invisible="1"/>
        <div class="oe_title">
            <h1>
                <field name="code" class="oe_inline" placeholder="Kód"/>
                <span> – </span>
                <field name="name" class="oe_inline" placeholder="Název třídy"/>
            </h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1" readonly="id"/>
            </div>
            <div class="o_investra_band_item">
                <label for="currency_id" string="Měna"/>
                <field name="currency_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="isin"/>
                <field name="isin" nolabel="1"/>
            </div>
        </div>
        <group name="class_main">
            <group name="class_class" string="Třída">
                <field name="distribution"/>
                <field name="sequence"/>
                <field name="shares_common"/>
            </group>
            <group name="class_rounding" string="Kurz a kusy">
                <field name="price_digits"/><field name="price_rounding"/>
                <field name="unit_digits"/><field name="unit_rounding"/><field name="rounding_owner"/>
            </group>
        </group>
        <group name="class_fees">
            <group name="class_entry_fee" string="Vstupní poplatek">
                <label for="entry_fee_rate" string="Sazba"/>
                <div class="o_row">
                    <field name="entry_fee_rate" nolabel="1"/>
                    <span>%</span>
                </div>
                <field name="entry_fee_recipient" string="Příjemce"/>
                <field name="entry_fee_statute_ref" string="Článek statutu"/>
                <field name="entry_fee_note" string="Poznámka"/>
            </group>
            <group name="class_exit_fee" string="Výstupní poplatek">
                <label for="exit_fee_rate" string="Sazba"/>
                <div class="o_row">
                    <field name="exit_fee_rate" nolabel="1"/>
                    <span>%</span>
                </div>
                <field name="exit_fee_recipient" string="Příjemce"/>
                <field name="exit_fee_statute_ref" string="Článek statutu"/>
                <field name="exit_fee_note" string="Poznámka"/>
            </group>
        </group>
    </sheet>
    <chatter/>
</form>
```

Dědění `view_fund_class_form_lock`: **beze změny** (cíle `field[@name='code']` a `field[@name='currency_id']` existují; movement_locked
se vloží neviditelně do h1 před `code`). `entry_fee_rate`/`exit_fee_rate` jsou uložené v procentech (`fund.py`, „Vstupní poplatek (%)“,
digits 7,4) → widget percentage **ne**, jen přípona „%“. Kontrola 22 + 1 = 23.

---

### 1.5 Nástroj – `investra_instruments.view_instrument_form`

- Soubor: `investra_instruments/views/instrument_views.xml:34-124`, model `investra.instrument`.
- Dědění:
  - `investra_counterparty.view_instrument_form_issuer` – `investra_counterparty/views/counterparty_views.xml:59-70`
    (`//field[@name='isin']/..` after → položka pásu `issuer_id`)
  - `investra_instrument_master.view_instrument_form_master` – `investra_instrument_master/views/instrument_views.xml:4-75`
    (header před sheet; atributy readonly na `isin`, `issuer_id`; `//field[@name='type_id']/..` after → položky ba0088_id, cfi_code;
    `//field[@name='calendar_missing']` before → 3 alerty classification_gap, isin_warning, cfi_warning;
    `//field[@name='maturity_date']/..` attributes invisible; `//notebook` before → group „Klasifikace ČNB“; `//notebook` inside → page „Detail“)
  - `investra_nav.view_instrument_form_dividend` – `investra_nav/views/dividend_views.xml:241-255`
    (`//sheet/div[hasclass('oe_title')]` before → button_box Dividendy)
  - `investra_nav.view_instrument_form_schedule` – `investra_nav/views/nav_views.xml:1029-1071`
    (`//field[@name='maturity_date']` before → principal, start_date, coupon_frequency; znovu before → ex_coupon_days; header před sheet;
    `//field[@name='coupon_rate']` before → rate_type; atributy coupon_rate; sloupce estimated, ex_date v cashflow_ids;
    `//field[@name='cashflow_ids']/..` after → stránky „Období sazeb“, „Nahrazené toky“)

**Dnes** (základ): h1 `name`; `o_investra_metadata` (type_id, isin `required="isin_required"`, currency_id); alert book_warning;
alert calendar_missing (text); calendar_missing inv.; group → „Identifikace“ (code, type_group, isin_required inv., identifier_kind,
identifier, fund_id, company_id, market, counterparty_id, collateral) | „Ocenění a klasifikace“ (cnb_sheet, max_price_age,
fair_value_level, deviates_from_type inv.); alert-info deviates_from_type; group „Ostatní podíl“; group „Úročení“ (maturity_date,
coupon_rate, day_count, price_excludes_accrued, accrual_method, accrual_note); group „Test SPPI“; notebook (Zařazení ve fondech,
Smluvní peněžní toky); chatter.

**Cíl** (základ):

```xml
<form class="o_investra_instrument_form">
    <sheet>
        <div class="oe_title o_investra_title">
            <h1>
                <field name="isin" required="isin_required" placeholder="ISIN"/>
                <field name="name" class="o_investra_title_sub" placeholder="Název nástroje"/>
            </h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="type_id"/>
                <field name="type_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="currency_id"/>
                <field name="currency_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item" name="band_maturity" invisible="type_group not in ('debt', 'money_market', 'loan')">
                <label for="maturity_date"/>
                <field name="maturity_date" nolabel="1"/>
            </div>
            <div class="o_investra_band_item" invisible="type_group != 'listed'">
                <label for="market"/>
                <field name="market" nolabel="1"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-warning" role="alert" invisible="not book_warning">
                <field name="book_warning" readonly="1"/>
            </div>
            <div class="alert alert-warning" role="alert" invisible="not calendar_missing">
                Dluhopis nemá kalendář toků: naběhlý úrok se v obchodech nepředvyplní a ocenění ho u pozice nepočítá.
                Doplňte toky na záložce Smluvní peněžní toky.
            </div>
            <div class="alert alert-info" role="alert" invisible="not deviates_from_type">
                List ČNB se liší od návrhu typu nástroje.
            </div>
        </div>
        <field name="calendar_missing" invisible="1"/>
        <field name="deviates_from_type" invisible="1"/>
        <group name="instrument_main">
            <group name="instrument_identification" string="Identifikace">
                <field name="code" invisible="not code"/><field name="type_group"/>
                <field name="isin_required" invisible="1"/>
                <field name="identifier_kind" invisible="isin" required="not isin"/>
                <field name="identifier" invisible="isin" required="not isin"/>
                <field name="fund_id" invisible="isin" required="not isin" readonly="id"
                       help="Nástroj bez ISIN patří jednomu fondu. Nástroj s ISIN je sdílený pro všechny fondy."/>
                <field name="company_id" groups="base.group_multi_company"/>
                <field name="counterparty_id" invisible="type_group not in ('money_market', 'loan', 'derivative')"/>
                <field name="collateral" invisible="type_group != 'money_market'"/>
            </group>
            <group name="instrument_valuation" string="Ocenění a klasifikace">
                <field name="cnb_sheet"/>
                <field name="max_price_age"/>
                <field name="fair_value_level"/>
            </group>
        </group>
        <group name="instrument_other_holding" string="Ostatní podíl" invisible="type_group != 'other_holding'">
            <field name="holding_kind" required="type_group == 'other_holding'"/>
            <field name="commitment_amount"/><field name="order_ref"/>
        </group>
        <group name="instrument_terms">
            <group name="instrument_interest" string="Úročení" invisible="type_group not in ('debt', 'money_market', 'loan')">
                <field name="coupon_rate"/><field name="day_count"/><field name="price_excludes_accrued"/>
                <field name="accrual_method"/>
                <field name="accrual_note" invisible="accrual_method != 'linear'" required="accrual_method == 'linear'"/>
            </group>
            <group name="instrument_sppi" string="Test SPPI" invisible="not sppi_applicable">
                <!-- 7 polí SPPI PŘESNĚ jako dnes instrument_views.xml:97-103 -->
            </group>
        </group>
        <notebook>
            <!-- beze změny: Zařazení ve fondech, Smluvní peněžní toky -->
        </notebook>
    </sheet>
    <chatter/>
</form>
```

Úpravy dědění (nutné – kotvy se přesouvají):
- `investra_counterparty.view_instrument_form_issuer`: `//field[@name='isin']/..` after (div položky pásu) →
  `<xpath expr="//group[@name='instrument_identification']" position="inside"><field name="issuer_id"/></xpath>`
  (emitent patří do Identifikace, pás má jen Typ, Měna, Splatnost, Trh).
- `investra_instrument_master.view_instrument_form_master`:
  - `//field[@name='isin']` attributes readonly – beze změny (pole je v h1).
  - `//field[@name='issuer_id']` attributes readonly – beze změny.
  - `//field[@name='type_id']/..` after (2 divy) → `<xpath expr="//group[@name='instrument_identification']" position="inside">`
    s `<field name="ba0088_id" readonly="review_state == 'reviewed'" options="{'no_create': True}"/>` a
    `<field name="cfi_code" readonly="review_state == 'reviewed'"/>` (bez divů, label, nolabel).
  - `//field[@name='calendar_missing']` before (3 alerty) → `//div[@name='investra_alerts']` position="inside".
  - `//field[@name='maturity_date']/..` attributes → **dvě** xpath se stejnou hodnotou
    `type_group not in ('debt', 'money_market', 'loan') and asset_family != 'debt'`:
    `//group[@name='instrument_interest']` attributes invisible a `//div[@name='band_maturity']` attributes invisible.
  - header, „Klasifikace ČNB“ (`//notebook` before), „Detail“ (`//notebook` inside) – beze změny.
- `investra_nav.view_instrument_form_schedule`: obě `<xpath expr="//field[@name='maturity_date']" position="before">` →
  `<xpath expr="//field[@name='coupon_rate']" position="before">` (obsah beze změny). Ostatní xpath beze změny. Výsledné pořadí
  v Úročení: principal, start_date, coupon_frequency, ex_coupon_days, rate_type, coupon_rate, day_count, price_excludes_accrued,
  accrual_method, accrual_note (splatnost je v pásu).
- `investra_nav.view_instrument_form_dividend`: beze změny (`//sheet/div[hasclass('oe_title')]` platí, `oe_title` zůstává přímým
  potomkem sheet).

Kontrola: základ 38 = 38; issuer 1; master 22; dividend 0; schedule 7 (principal, start_date, coupon_frequency, ex_coupon_days,
rate_type, rate_period_ids, superseded_cashflow_ids; estimated a ex_date jsou sloupce vnořeného listu) → 68 = 68.
Pole `isin` už nemá popisek (placeholder „ISIN“); nástroj bez ISIN má v nadpisu prázdné pole ISIN a název.

---

### 1.6 Splátka – `investra_nav.view_repayment_form`

- Soubor: `investra_nav/views/nav_views.xml:1153-1251`, model `investra.instrument.repayment`. Dědění: **žádné**.

**Dnes**: header (Zaúčtovat; Opravit / Stornovat → `action_repayment_reverse_wizard`; state `draft,posted`); pending alert;
neviditelná allowed_instrument_ids, allowed_portfolio_ids, portfolio_choice, foreign_currency; alert `write_off_amount`; h1 text
„Splátka nástroje“; `o_investra_metadata` (fund_id, kind, instrument_id, portfolio_id, date); strip (principal_amount, interest_amount,
fee_amount, amount, remaining_before + remaining_after v jedné buňce); group → „Splátka“ (closes_position, fx_rate) | „Záznam“
(event_id, replaced_id, reversal_reason); notebook Zaúčtování. Bez chatteru.

**Cíl**:

```xml
<form class="o_investra_repayment_form">
    <header>
        <!-- beze změny -->
    </header>
    <sheet>
        <!-- MN-18 -->
        <field name="pending_request_id" invisible="1"/>
        <field name="allowed_instrument_ids" invisible="1"/>
        <field name="allowed_portfolio_ids" invisible="1"/>
        <field name="portfolio_choice" invisible="1"/>
        <field name="foreign_currency" invisible="1"/>
        <div class="oe_title">
            <h1><field name="instrument_id" options="{'no_create': True}" readonly="state != 'draft'" placeholder="Nástroj"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item" invisible="not portfolio_choice">
                <label for="portfolio_id"/>
                <field name="portfolio_id" nolabel="1" options="{'no_create': True}" readonly="state != 'draft' or not portfolio_choice" force_save="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="kind"/>
                <field name="kind" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item">
                <label for="date"/>
                <field name="date" nolabel="1" readonly="state != 'draft'"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-warning" role="alert" invisible="not pending_request_id">
                <strong>Čeká na potvrzení v Žádostech ke schválení.</strong>
                <button name="action_open_pending_request" type="object" class="btn btn-link p-0 ms-2" string="Otevřít žádost"/>
            </div>
            <div class="alert alert-warning" role="alert" invisible="not write_off_amount">
                <!-- text s write_off_amount PŘESNĚ jako dnes nav_views.xml:1179-1181 -->
            </div>
        </div>
        <div class="o_investra_metric_strip">
            <div class="o_investra_metric_item">
                <label for="principal_amount"/>
                <field name="principal_amount" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="interest_amount"/>
                <field name="interest_amount" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="fee_amount"/>
                <field name="fee_amount" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="amount" string="Celkem"/>
                <field name="amount" nolabel="1"/>
            </div>
        </div>
        <group name="repayment_main">
            <group name="repayment_detail" string="Splátka">
                <field name="remaining_before"/>
                <field name="remaining_after"/>
                <field name="closes_position" readonly="state != 'draft'" invisible="kind != 'extraordinary'"/>
                <field name="fx_rate" readonly="state != 'draft'" invisible="not foreign_currency"/>
            </group>
            <group name="repayment_record" string="Záznam">
                <field name="event_id" invisible="not event_id"/>
                <field name="replaced_id" invisible="not replaced_id"/>
                <field name="reversal_reason" invisible="not reversal_reason"/>
            </group>
        </group>
        <notebook invisible="not posting_preview">
            <page name="posting_preview" string="Zaúčtování">
                <field name="posting_preview" nolabel="1" readonly="1"/>
            </page>
        </notebook>
    </sheet>
</form>
```

Test `test_accrual`: první `name="fund_id"` (pás) je před prvním `name="kind"` (pás) – splněno. Druh splátky šedě v nadpisu
**nedávat** (byl by v arch před `fund_id` → test spadne), viz N2. Kontrola 24 = 24.

---

### 1.7 Derivát – `investra_derivative.view_derivative_form`

- Soubor: `investra_derivative/views/derivative_views.xml:101-199`, model `investra.derivative`. Dědění: **žádné**.

**Dnes**: header (Sjednat s confirm; Vypořádat nohu; Stornovat vypořádání / Stornovat → `action_derivative_reverse_wizard`;
state `draft,agreed,settled,reversed`); pending alert; alert-danger reversed (reversal_reason); h1 `name` readonly;
`o_investra_metadata` (fund_id, portfolio_id); group class `o_investra_trade_content` → „Smlouva“ (kind radio horizontal,
partner_id, contract_ref, trade_date) | „Po sjednání“ (functional_currency_id, instrument_id, event_id, settlement_reversal_reason);
notebook (Nohy, Ruční hodnoty, Zaúčtování); chatter.

**Cíl**:

```xml
<form class="o_investra_trade_form">
    <header>
        <!-- beze změny -->
    </header>
    <sheet>
        <field name="pending_request_id" invisible="1"/>
        <div class="oe_title">
            <h1><field name="name" readonly="1" placeholder="Název se doplní z noh"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item">
                <label for="portfolio_id"/>
                <field name="portfolio_id" nolabel="1" readonly="state != 'draft'" options="{'no_create': True}"/>
            </div>
            <div class="o_investra_band_item">
                <label for="contract_ref"/>
                <field name="contract_ref" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_band_item">
                <label for="trade_date"/>
                <field name="trade_date" nolabel="1" readonly="state != 'draft'"/>
            </div>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-warning" role="alert" invisible="not pending_request_id">
                <strong>Čeká na potvrzení v Žádostech ke schválení.</strong>
                <button name="action_open_pending_request" type="object" class="btn btn-link p-0 ms-2" string="Otevřít žádost"/>
            </div>
            <div class="alert alert-danger" role="alert" invisible="state != 'reversed'">
                Smlouva je stornovaná. Důvod: <field name="reversal_reason" readonly="1" class="d-inline"/>
            </div>
        </div>
        <group name="derivative_main">
            <group name="derivative_contract" string="Smlouva">
                <field name="kind" readonly="state != 'draft'"/>
                <field name="partner_id" readonly="state != 'draft'"/>
            </group>
            <group name="derivative_agreed" string="Po sjednání" invisible="state == 'draft'">
                <field name="functional_currency_id"/>
                <field name="instrument_id"/>
                <field name="event_id"/>
                <field name="settlement_reversal_reason" invisible="not settlement_reversal_reason"/>
            </group>
        </group>
        <notebook>
            <!-- beze změny: legs, values, posting_preview -->
        </notebook>
    </sheet>
    <chatter/>
</form>
```

„Druh výběrem“ = u `kind` odstranit `widget="radio" options="{'horizontal': true}"` (jediná změna atributů v celém podkladu,
požadovaná zadáním). Třída `o_investra_trade_content` odpadá (nemá CSS). Šedé datum vypořádání v nadpisu viz N3. Kontrola 17 = 17.

---

### 1.8a Dividenda – `investra_nav.view_dividend_event_form`

- Soubor: `investra_nav/views/dividend_views.xml:41-105`, model `investra.dividend.event`. Dědění: **žádné**.

**Dnes**: header (Načíst držitele, Zaúčtovat vše, Zaplaceno; state `draft,booked,paid`); h1 instrument_id; group → „Nárok“ (isin,
ex_date, pay_date, currency_id, per_share) | „Srážka (výchozí pro držitele)“ (kind, withholding_rate, treaty_rate); separator
„Držitelé k večeru dne před ex-datem“; line_ids (list se součty); `group.oe_subtotal_footer` (gross_total, withheld_total, net_total);
p.text-muted; chatter.

**Cíl**:

```xml
<form>
    <header>
        <!-- beze změny -->
    </header>
    <sheet>
        <div class="oe_title">
            <h1><field name="instrument_id" options="{'no_create': True}" placeholder="Cenný papír (název nebo ISIN)"/></h1>
        </div>
        <div class="o_investra_metric_strip">
            <div class="o_investra_metric_item">
                <label for="gross_total" string="Hrubá"/>
                <field name="gross_total" nolabel="1"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="withheld_total" string="Srážka"/>
                <field name="withheld_total" nolabel="1"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="net_total" string="Čistá"/>
                <field name="net_total" nolabel="1"/>
            </div>
        </div>
        <group name="dividend_event_main">
            <group name="dividend_event_claim" string="Nárok">
                <field name="isin"/>
                <field name="ex_date"/>
                <field name="pay_date"/>
                <field name="currency_id"/>
                <field name="per_share"/>
            </group>
            <group name="dividend_event_withholding" string="Srážka (výchozí pro držitele)">
                <field name="kind"/>
                <field name="withholding_rate"/>
                <field name="treaty_rate" invisible="kind != 'foreign'"/>
            </group>
        </group>
        <notebook>
            <page name="holders" string="Držitelé k večeru dne před ex-datem">
                <field name="line_ids" nolabel="1" context="{'default_dividend_event_id': id}">
                    <!-- vnořený list PŘESNĚ jako dnes dividend_views.xml:75-89 (sum= na units, gross, withheld, net = součtový řádek) -->
                </field>
                <p class="text-muted">
                    <!-- text PŘESNĚ jako dnes dividend_views.xml:97-99 -->
                </p>
            </page>
        </notebook>
    </sheet>
    <chatter/>
</form>
```

Separator a `oe_subtotal_footer` odpadají (součty jsou v pásu čísel a v součtovém řádku listu). Kontrola 14 = 14.

### 1.8b Řádek dividendy – `investra_nav.view_dividend_form`

- Soubor: `investra_nav/views/dividend_views.xml:163-230`, model `investra.dividend`. Dědění: **žádné**.

**Dnes**: header (Zaúčtovat, Zaplaceno; state `draft,booked,paid,reversed`); neviditelná allowed_portfolio_ids, foreign_currency,
portfolio_class_id; alert-danger reversed (reversal_reason); h1 instrument_id; group → „Nárok“ (fund_id, portfolio_id, ex_date, units,
per_share, gross_amount) | „Výplata“ (pay_date, currency_id, fx_rate, pay_fx_rate, net_amount); group „Srážka a zápočet“ → (kind „Druh“,
withholding_rate, withheld_amount, treaty_rate) | (creditable_amount, excess_amount, excess_treatment, note); group „Zaúčtování“
(event_id, pay_event_id); notebook Zaúčtování; chatter.

**Cíl**:

```xml
<form>
    <header>
        <!-- beze změny -->
    </header>
    <sheet>
        <field name="allowed_portfolio_ids" invisible="1"/>
        <field name="foreign_currency" invisible="1"/>
        <field name="portfolio_class_id" invisible="1"/>
        <div class="oe_title">
            <h1><field name="instrument_id" readonly="state != 'draft'"/></h1>
        </div>
        <div class="o_investra_alerts" name="investra_alerts">
            <div class="alert alert-danger" role="alert" invisible="state != 'reversed'">
                Dividenda je stornovaná. Důvod: <field name="reversal_reason" readonly="1" class="oe_inline"/>
            </div>
        </div>
        <div class="o_investra_metric_strip">
            <div class="o_investra_metric_item">
                <label for="gross_amount" string="Hrubá"/>
                <field name="gross_amount" nolabel="1" readonly="1"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="withheld_amount" string="Srážka"/>
                <field name="withheld_amount" nolabel="1" readonly="state != 'draft'"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="net_amount" string="Čistá"/>
                <field name="net_amount" nolabel="1" readonly="1"/>
            </div>
        </div>
        <group name="dividend_main">
            <group name="dividend_claim" string="Nárok">
                <field name="fund_id" readonly="state != 'draft'"/>
                <field name="portfolio_id" domain="[('id', 'in', allowed_portfolio_ids)]" options="{'no_create': True}" readonly="state != 'draft'"/>
                <field name="ex_date" readonly="state != 'draft'"/>
                <field name="units" readonly="state != 'draft'"/>
                <field name="per_share" readonly="state != 'draft'"/>
            </group>
            <group name="dividend_payment" string="Výplata">
                <field name="pay_date" readonly="state in ('paid', 'reversed')"/>
                <field name="currency_id" readonly="1"/>
                <field name="fx_rate" invisible="not foreign_currency" readonly="state != 'draft'"/>
                <field name="pay_fx_rate" invisible="not foreign_currency" readonly="state in ('paid', 'reversed')"/>
            </group>
        </group>
        <group name="dividend_withholding" string="Srážka a zápočet">
            <group name="dividend_withholding_rate">
                <field name="kind" string="Druh" readonly="state != 'draft'"/>
                <field name="withholding_rate" readonly="state != 'draft'"/>
                <field name="treaty_rate" invisible="kind != 'foreign'" readonly="state != 'draft'"/>
            </group>
            <group name="dividend_withholding_credit">
                <field name="creditable_amount" readonly="state != 'draft'"/>
                <field name="excess_amount" invisible="kind != 'foreign'" readonly="1"/>
                <field name="excess_treatment" invisible="kind != 'foreign'" readonly="state != 'draft'"/>
                <field name="note" readonly="state != 'draft'"/>
            </group>
        </group>
        <group name="dividend_events" string="Zaúčtování" invisible="not event_id and not pay_event_id">
            <field name="event_id" readonly="1" invisible="not event_id"/>
            <field name="pay_event_id" readonly="1" invisible="not pay_event_id"/>
        </group>
        <notebook invisible="not posting_preview">
            <page name="posting_preview" string="Zaúčtování">
                <field name="posting_preview" nolabel="1" readonly="1"/>
            </page>
        </notebook>
    </sheet>
    <chatter/>
</form>
```

Kontrola 28 = 28 (gross_amount, withheld_amount, net_amount jen přesunuty do pásu čísel).

---

### 1.9 Účetní událost – `investra_posting.view_event_form`

- Soubor: `investra_posting/views/posting_views.xml:18-81`, model `investra.accounting.event`. Dědění: **žádné**.

**Dnes**: `<form create="false" edit="false" delete="false">`; header state `draft,locked,posted`; button_box (Zdroj
`action_open_source` invisible not res_id; Doklad `action_open_move` invisible not move_id); h1 name; group → (fund_id, company_id
„Kniha“, date, event_type, source_name) | (amount, currency_id, amount_currency inv. not foreign_currency_id, foreign_currency_id
tamtéž, move_id, reversal_move_id inv. not reversal_move_id); notebook (Řádky dokladu, Technické: key, fingerprint, res_model, res_id).

**Cíl**:

```xml
<form create="false" edit="false" delete="false">
    <header>
        <field name="state" widget="statusbar" statusbar_visible="draft,locked,posted"/>
    </header>
    <sheet>
        <div class="oe_button_box" name="button_box">
            <!-- beze změny -->
        </div>
        <div class="oe_title">
            <h1><field name="name"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="fund_id"/>
                <field name="fund_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="company_id" string="Kniha"/>
                <field name="company_id" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="date"/>
                <field name="date" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="event_type" string="Druh"/>
                <field name="event_type" nolabel="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="source_name"/>
                <field name="source_name" nolabel="1"/>
                <button name="action_open_source" type="object" class="btn btn-link p-0" icon="fa-external-link"
                        title="Otevřít zdroj" invisible="not res_id"/>
            </div>
        </div>
        <div class="o_investra_metric_strip">
            <div class="o_investra_metric_item">
                <label for="amount"/>
                <field name="amount" nolabel="1"/>
            </div>
            <div class="o_investra_metric_item">
                <label for="move_id"/>
                <field name="move_id" nolabel="1"/>
            </div>
            <div class="o_investra_metric_item" invisible="not reversal_move_id">
                <label for="reversal_move_id"/>
                <field name="reversal_move_id" nolabel="1"/>
            </div>
        </div>
        <group name="event_currency" string="Měna">
            <field name="currency_id"/>
            <field name="amount_currency" invisible="not foreign_currency_id"/>
            <field name="foreign_currency_id" invisible="not foreign_currency_id"/>
        </group>
        <notebook>
            <!-- beze změny: lines, technical -->
        </notebook>
    </sheet>
</form>
```

„Fond/kniha“ = dvě položky pásu (Fond, Kniha). „Zdroj (odkaz)“ = text `source_name` + tlačítko-odkaz `action_open_source`
(tlačítko je v pohledu podruhé; stat tlačítko „Zdroj“ zůstává). `reversal_move_id` dříve skryté atributem pole, nyní celou buňkou
pásu se stejnou podmínkou. Kontrola 18 = 18.

---

### 1.10 Daňové pravidlo – `investra_nav.view_tax_rule_form`

- Soubor: `investra_nav/views/tax_views.xml:18-55`, model `investra.tax.rule`. Dědění: **žádné**.

**Dnes**: group → (name, active, kind, method inv. exempt, rate_now percentage readonly inv. exempt) | „Účty“ inv. exempt
(tax_account_code, balance_account_code, credit_account_code inv. method != current, recognise_asset inv. method != deferred);
group „Sazby“ inv. exempt (version_ids list editable); group (note); chatter.

**Cíl**:

```xml
<form>
    <sheet>
        <div class="oe_title">
            <h1><field name="name" placeholder="Název pravidla"/></h1>
        </div>
        <div class="o_investra_band" name="investra_band">
            <div class="o_investra_band_item">
                <label for="kind"/>
                <field name="kind" nolabel="1"/>
            </div>
            <div class="o_investra_band_item" invisible="kind == 'exempt'">
                <label for="method"/>
                <field name="method" nolabel="1"/>
            </div>
            <div class="o_investra_band_item" invisible="kind == 'exempt'">
                <label for="rate_now" string="Sazba dnes"/>
                <field name="rate_now" nolabel="1" widget="percentage" readonly="1"/>
            </div>
            <div class="o_investra_band_item">
                <label for="active"/>
                <field name="active" nolabel="1"/>
            </div>
        </div>
        <group name="tax_rule_accounts" string="Účty" invisible="kind == 'exempt'">
            <field name="tax_account_code"/>
            <field name="balance_account_code"/>
            <field name="credit_account_code" invisible="method != 'current'"/>
            <field name="recognise_asset" invisible="method != 'deferred'"/>
        </group>
        <notebook>
            <page name="rates" string="Sazby" invisible="kind == 'exempt'">
                <field name="version_ids" nolabel="1">
                    <list editable="bottom">
                        <field name="valid_from"/>
                        <field name="rate" widget="percentage"/>
                        <field name="decision_ref"/>
                    </list>
                </field>
            </page>
            <page name="note" string="Poznámka">
                <field name="note" nolabel="1"/>
            </page>
        </notebook>
    </sheet>
    <chatter/>
</form>
```

Neviditelnost `method` a `rate_now` přenesena z pole na buňku pásu (stejná podmínka). „Stav“ ze zadání = pole `active`
(model nemá `state`; viz N5). „Historie“ = chatter (N4). Kontrola 11 = 11.

---

### 1.11 Ostatní formuláře (jen CSS)
Platí SCSS z oddílu 3 automaticky (popisky 200 px, štítky pásu čísel). Pozor na skupiny `col="4"`
(`investra_nav/views/nav_views.xml:148` a `:190`, formulář třídy ocenění): Odoo 20 pro `col` negeneruje vlastní mřížku; první sloupec
bude 200 px místo `fit-content(150px)` – ověřit v prohlížeči. Doplnění nadpisů a pojmenování skupin u číselníků v tomto podkladu
není rozepsáno (zadání 2.2 poslední odrážka) – nejasné: seznam formulářů nebyl součástí úkolu.

---

## 2. Dialogy (TransientModel)

`grep "models.TransientModel"` v `addons/custom` (mimo testy): 16 tříd ve 13 souborech.

| # | Model | Soubor modelu | Pohled | Dialog? |
|---|---|---|---|---|
| 1 | investra.trade.reverse.wizard | investra_nav/models/trade_reverse.py:151 | investra_nav/views/trade_views.xml:11 `view_trade_reverse_wizard_form` | ano |
| 2 | investra.class.movement.reverse.wizard | investra_nav/models/movement.py:822 | investra_nav/views/nav_views.xml:962 `view_movement_reverse_wizard_form` | ano |
| 3 | investra.instrument.repayment.reverse.wizard | investra_nav/models/instrument_accrual.py:915 | nav_views.xml:1252 `view_repayment_reverse_wizard_form` | ano |
| 4 | investra.instrument.repayment.drafts.wizard | instrument_accrual.py:946 | nav_views.xml:1098 `view_repayment_drafts_wizard_form` | ano |
| 5 | investra.instrument.rate.wizard | investra_nav/models/instrument_rate.py:350 | nav_views.xml:1073 `view_instrument_rate_wizard_form` | ano |
| 6 | investra.valuation.return.wizard | investra_nav/models/return_wizard.py:19 | nav_views.xml:111 `view_valuation_return_wizard_form` | ano |
| 7 | investra.valuation.end.wizard | investra_nav/models/valuation_corrections_ui.py:176 | nav_views.xml:424 `view_valuation_end_wizard_form` | ano |
| 8 | investra.derivative.settle.wizard | investra_derivative/models/wizard.py:8 | investra_derivative/views/derivative_views.xml:29 | ano |
| 9 | investra.derivative.reverse.wizard | investra_derivative/models/wizard.py:64 | derivative_views.xml:9 | ano |
| 10 | investra.rate.override.wizard | investra_rates/models/override_wizard.py:4 | investra_rates/views/rate_views.xml:3 | ano |
| 11 | investra.classification.override.wizard | investra_instruments/models/override_wizard.py:6 | investra_instruments/views/instrument_views.xml:448 | ano |
| 12 | investra.masterdata.change.wizard | investra_instrument_master/wizard/masterdata_change.py:8 | investra_instrument_master/views/instrument_views.xml:103 | ano |
| 13 | investra.new.book.wizard | investra_chart_fund/wizard/new_book.py:16 (+ `_inherit` investra_instrument_master/wizard/new_book.py:18) | investra_chart_fund/wizard/new_book_views.xml:3 + dědění investra_instrument_master/wizard/new_book_views.xml:3 | ano |
| 14 | investra.codelist.import.wizard | investra_instrument_master/wizard/codelist_import.py:15 | investra_instrument_master/wizard/codelist_import_views.xml:3 | ano (vícekrokový) |
| – | investra.codelist.import.line | codelist_import.py:162 | žádný vlastní formulář | **ne** – řádky náhledu (One2many `line_ids` průvodce 14), zobrazují se jen jako vnořený list |

Titulek dialogu v Odoo 20 = `name` akce, ne `<form string>`. Akce `type="action"` mají titulek v XML (`ir.actions.act_window`),
akce otevřené z Pythonu mají `name` ve slovníku (uvedeno u každého). Jedna akce = jeden titulek, proto u průvodců s více kroky
(`mode`) je nutné buď několik akcí (XML, zelená zóna), nebo společný titulek – níže navrženy samostatné akce.

### 2.1 Společný skelet dialogu

```xml
<form>
    <div class="o_investra_dialog_subject">
        <!-- první řádek: o jaký záznam jde, čitelně; pole readonly, nolabel -->
    </div>
    <div class="o_investra_dialog_effect">
        <div class="o_investra_dialog_effect_title">Co se stane</div>
        <field name="effect" nolabel="1" readonly="1"/>
    </div>
    <group name="dialog_input">
        <!-- pole k vyplnění v jednom sloupci (jedna group, žádná vnořená dvojice) -->
    </group>
    <footer>
        <!-- primární tlačítko pojmenované akcí; nevratné: class="btn-danger o_investra_btn_ember" -->
        <button special="cancel" string="Zpět"/>
    </footer>
</form>
```
`effect` se zobrazuje bez žlutého rámečku. Text je dnes souvislý odstavec (Python); „krátký seznam“ viz N6.

### 2.2 Dialog po dialogu

**1 Storno/oprava obchodu** (`investra.trade.reverse.wizard`)
- Dnes: akce `action_trade_reverse_wizard` „Storno nebo oprava obchodu“; group trade_id, mode (readonly); alert-warning effect;
  group reason; Potvrdit (btn-primary), Zrušit.
- Cílové titulky (3 akce v `investra_nav/views/trade_views.xml`, stejný model, `target=new`): `action_trade_reverse_wizard` (ponechat
  xmlid) → „Stornovat obchod“; nová `action_trade_reverse_settlement_wizard` → „Stornovat vypořádání obchodu“; nová
  `action_trade_correct_wizard` → „Opravit obchod“. Tlačítka ve `view_trade_form_preview` přesměrovat: Stornovat vypořádání → settlement
  akce, Opravit → correct akce, Stornovat → původní (kontexty `default_mode` beze změny).
- První řádek: `trade_id` – **model `investra.trade` nemá `name` ani `_compute_display_name`**, zobrazí se technický název → N7.
- Co se stane: `effect`. Vstup: `reason` (placeholder beze změny). `mode` ponechat jako `<field name="mode" invisible="1"/>`.
- Tlačítka: `action_confirm` třikrát s `invisible` podle režimu: „Stornovat vypořádání“ (`mode != 'settlement'`), „Stornovat obchod“
  (`mode != 'reverse'`), „Opravit obchod“ (`mode != 'correct'`); všechna `class="btn-danger o_investra_btn_ember"` (storno je nevratné);
  „Zpět“ `special="cancel"`.

**2 Storno/oprava úpisu a odkupu** (`investra.class.movement.reverse.wizard`)
- Dnes: akce `action_movement_reverse_wizard` „Storno nebo oprava pohybu“; stejná stavba jako 1.
- Titulky: `action_movement_reverse_wizard` → „Stornovat úpis nebo odkup“; nová `action_movement_correct_wizard` → „Opravit úpis nebo odkup“
  (tlačítko Opravit ve `view_movement_form` přesměrovat).
- První řádek: `movement_id` readonly nolabel – `display_name` = „Typ Třída Datum“ (`movement.py:147-151`); datum je `str(date)`,
  tj. ISO `2026-09-30`, ne `30.09.2026` → N7.
- Tlačítka: „Stornovat“ (`mode != 'reverse'`), „Opravit“ (`mode != 'correct'`), obě Ember; „Zpět“.

**3 Storno/oprava splátky** (`investra.instrument.repayment.reverse.wizard`)
- Dnes: akce `action_repayment_reverse_wizard` „Storno nebo oprava splátky“; stejná stavba.
- Titulky: `action_repayment_reverse_wizard` → „Stornovat splátku“; nová `action_repayment_correct_wizard` → „Opravit splátku“.
- První řádek: `repayment_id` – model nemá `name` ani `display_name` → N7.
- Tlačítka: „Stornovat splátku“ / „Opravit splátku“ podle `mode`, Ember; „Zpět“.

**4 Návrhy splátek podle kalendáře** (`investra.instrument.repayment.drafts.wizard`)
- Dnes: otevírá Python `instrument_accrual.py:620` s `name` „Návrhy podle kalendáře“; p.text-muted (vysvětlení); group date_to;
  „Založit návrhy“ btn-primary; Zrušit.
- Cílový titulek: „Založit návrhy splátek“ (změna řetězce v Pythonu `instrument_accrual.py:620`).
- První řádek: žádný záznam (hromadná akce) – vynechat. Co se stane: dnešní odstavec převést na seznam v XML:
  `<ul><li>Založí návrhy pro toky kalendáře splatné do zvoleného data ve fondech vybraných společností.</li><li>Nic se neúčtuje;
  návrh zaúčtujete až po kontrole.</li><li>Tok, který už návrh nebo splátku má, se přeskočí.</li></ul>`.
- Tlačítka: „Založit návrhy“ btn-primary (vratné – návrh lze smazat); „Zpět“.

**5 Nová úroková sazba** (`investra.instrument.rate.wizard`)
- Dnes: Python `instrument_rate.py:232` „Zadat novou sazbu“ (✓ sloveso); group instrument_id ro, valid_from, rate, note; alert-warning
  period_warning; alert-info effect; „Zadat sazbu“ btn-primary; Zrušit.
- Titulek beze změny. První řádek: `instrument_id` readonly nolabel (`display_name` „ISIN název“ ✓).
- Co se stane: `effect` bez rámečku. `period_warning` zůstává jako alert-warning (je to upozornění, ne popis).
- Tlačítka: „Zadat sazbu“ btn-primary; „Zpět“.

**6 Vrácení ocenění** (`investra.valuation.return.wizard`)
- Dnes: akce `action_valuation_return_wizard` „Vrácení ocenění“, 3 tlačítka ve formuláři ocenění (`nav_views.xml:228-234`);
  group valuation_id, mode; alert effect; reason; Potvrdit; Zrušit.
- Titulky: `action_valuation_return_wizard` → „Vrátit ocenění k přepracování“ (mode return); nové
  `action_valuation_return_depositary_wizard` → „Vrátit ocenění (depozitář)“, `action_valuation_reverse_wizard` → „Stornovat a přepracovat
  ocenění“; tlačítka v `nav_views.xml:228-234` přesměrovat.
- První řádek: `valuation_id` (`display_name` „Fond – 30.09.2026 – v1“, `valuation.py:228-232` ✓).
- Tlačítka: `action_confirm` × 3 podle `mode` („Vrátit k přepracování“, „Vrátit depozitářem“, „Stornovat a přepracovat“), Ember; „Zpět“.

**7 Ukončit opravu** (`investra.valuation.end.wizard`)
- Dnes: Python `valuation_corrections_ui.py:170` „Ukončit opravu“ (✓); alert-warning popis; group valuation_id, entry_id, amount, note;
  „Ukončit opravu“ btn-primary; Zrušit.
- První řádek: `valuation_id` + `amount`; `entry_id` (`investra.valuation.external`) nemá `name`/`display_name` → N7.
- Co se stane: dnešní text alertu jako `<ul>`: „Založí opravu o opačnou částku.“ / „Od tohoto ocenění se oprava přestane přebírat.“ /
  „Dřívější zaúčtovaná ocenění se nezmění.“
- Vstup: `note` (placeholder beze změny). Tlačítka: „Ukončit opravu“ – nevratnost nejasná (N8), návrh Ember; „Zpět“.

**8 Vypořádat nohu** (`investra.derivative.settle.wizard`)
- Dnes: Python `investra_derivative/models/posting.py:457` „Vypořádat nohu“ (✓); group→group (derivative_id, leg_id inv., settlement_date,
  bank_account_ids inv.) | group (buy_amount, buy_currency_id inv., buy_account_id, sell_amount, sell_currency_id inv., sell_account_id);
  p.text-muted; preview; „Vypořádat“ btn-primary; Zrušit.
- Cíl: jeden sloupec. První řádek: `derivative_id`, `settlement_date`, `buy_amount`, `sell_amount` readonly nolabel v `o_investra_dialog_subject`
  (spojit `<span> · </span>`). Co se stane: dnešní p.text-muted + `preview`. group dialog_input: leg_id inv., bank_account_ids inv.,
  buy_currency_id inv., sell_currency_id inv., buy_account_id, sell_account_id. Tlačítka: „Vypořádat nohu“ btn-primary (stornovatelné); „Zpět“.

**9 Storno derivátu** (`investra.derivative.reverse.wizard`)
- Dnes: akce `action_derivative_reverse_wizard` „Storno derivátu“; stavba jako 1.
- Titulky: `action_derivative_reverse_wizard` → „Stornovat smlouvu“; nová `action_derivative_reverse_settlement_wizard` → „Stornovat
  vypořádání nohy“ (tlačítko „Stornovat vypořádání“ ve `view_derivative_form` přesměrovat).
- První řádek: `derivative_id` (`name` = „Druh pár“ ✓). Tlačítka podle `mode` („Stornovat vypořádání“, „Stornovat smlouvu“), Ember; „Zpět“.

**10 Ruční kurz** (`investra.rate.override.wizard`)
- Dnes: akce `action_rate_override_wizard` „Ruční kurz“ (tlačítka „Nový ruční kurz“ `rate_views.xml:50` a „Přepsat kurz“ `:69`);
  alert-warning (výjimka, nejde změnit); group→group (origin radio, source, currency_id, date) | group (quantity, rate, current_id inv.,
  current_rate inv. not current_id, current_origin inv. not current_id); reason; „Uložit kurz“ btn-primary; Zrušit.
- Titulky: `action_rate_override_wizard` → „Zadat ruční kurz“; nová `action_rate_override_edit_wizard` → „Přepsat vyhlášený kurz“ (pro
  tlačítko `rate_views.xml:69`).
- První řádek: při přepisu `currency_id` + `date` + `source` jsou předvyplněné – zobrazit je v `o_investra_dialog_subject` jen
  pro čtení **nejde** (u nového kurzu se zadávají) → první řádek vynechat, pole zůstávají v group.
- Co se stane (místo žlutého rámečku): `<ul><li>Ruční kurz platí pro účetnictví i ocenění.</li><li>Zůstane v evidenci s důvodem a
  jménem zadavatele; nejde změnit ani smazat.</li><li>Opravu zadejte jako nový přepis.</li></ul>`.
- „Kurz za {množství} {měna}“ bez Pythonu:
  ```xml
  <group name="dialog_input">
      <field name="origin" widget="radio"/>
      <field name="source"/>
      <field name="currency_id" options="{'no_create': True, 'no_open': True}"/>
      <field name="date"/>
      <label for="rate" string="Kurz za"/>
      <div class="o_row">
          <field name="quantity" class="oe_inline"/>
          <field name="currency_id" readonly="1" class="oe_inline" options="{'no_open': True}"/>
          <span>=</span>
          <field name="rate" class="oe_inline"/>
          <span class="text-muted" invisible="not current_id">vyhlášený <field name="current_rate" nolabel="1" class="oe_inline"/>
              (<field name="current_origin" nolabel="1" class="oe_inline"/>)</span>
      </div>
      <field name="current_id" invisible="1"/>
      <field name="reason" placeholder="Proč se kurz zadává ručně (např. chyba zdroje, měna, kterou zdroj nevyhlašuje)"/>
  </group>
  ```
  (`currency_id` 2×: editovatelné + jen pro čtení v řádku kurzu; `current_rate`, `current_origin` přesunuty do řádku – pole se neztrácí.)
  Doslovný popisek „Kurz za 100 HUF“ jako dynamický text viz N9.
- Tlačítka: „Uložit kurz“ btn-primary (zadání není storno; nevratnost N8); „Zpět“.

**11 Ruční kategorie IFRS 9** (`investra.classification.override.wizard`)
- Dnes: akce `action_classification_override_wizard` „Ruční kategorie IFRS 9“; p (vysvětlení); group classification_id ro,
  category_override, override_note; Potvrdit; Zrušit.
- Titulek: „Přepsat kategorii IFRS 9“. První řádek: `classification_id` (`display_name` „nástroj – portfolio“, `portfolio.py:324-326` ✓).
- Co se stane: `<ul><li>Ruční kategorie je odchylka od rozhodovacího stromu IFRS 9 a ukáže se v ocenění.</li><li>Vyžaduje-li
  schvalovací matice druhou osobu, vznikne žádost a kategorie se zapíše až po potvrzení.</li></ul>`.
- Tlačítka: „Přepsat kategorii“ btn-primary; „Zpět“.

**12 Změnit klasifikaci** (`investra.masterdata.change.wizard`)
- Dnes: Python `investra_instrument_master/models/instrument.py:199` „Změnit klasifikaci“ (✓); alert-warning; group instrument_id,
  ba0088_id, cfi_code, isin, issuer_id, effective_date, reason; „Změnit“ btn-primary; Zrušit.
- První řádek: `instrument_id` (pole je v Pythonu `readonly=True`; `display_name` „ISIN název“ ✓).
- Co se stane: `<ul><li>Změna se zapíše do historie s uvedeným důvodem.</li></ul>` (dnešní text „Klasifikace je potvrzená…“).
- Tlačítka: „Změnit klasifikaci“ btn-primary; „Zpět“.

**13 Nová účetní kniha** (`investra.new.book.wizard`)
- Dnes: akce `action_new_book_wizard` „Nová účetní kniha“; alert-warning (nevratnost); group→group (name, entity_type, framework,
  parent_id) | group (currency_id, country_id, template, rate_source, rate_source_missing inv.); alert rate_source_missing;
  „Založit knihu“ btn-primary s `confirm`; Zrušit. Dědění instrument_master: `//group` before (same_name_partner_id, partner_profile_id
  inv., alert-info s tlačítkem), před `name` → partner_id, atributy `name` readonly=partner_id force_save, `//group` after → group
  „Identifikace (nepovinné)“ (group: company_registry, vat | group: esa_code_id, lei, div text-muted).
- Titulek: „Založit účetní knihu“. První řádek: žádný záznam (zakládá se) – vynechat.
- Cíl: první `<group>` zůstává **první group v arch** (kotva `//group` dědění), ale bez vnořených skupin – jedno pole pod druhým v pořadí
  name, entity_type, framework, parent_id, currency_id, country_id, template, rate_source, rate_source_missing (atributy beze změny,
  `parent_id` se `subfund` kvůli testu). Dědění: group „Identifikace (nepovinné)“ – odstranit vnořené `<group>` a pole dát přímo
  (company_registry, vat, esa_code_id, lei, div).
- Co se stane: dnešní text alertu jako `<ul>` (3 věty) bez rámečku; alert `rate_source_missing` zůstává alert-warning.
- Tlačítka: „Založit knihu“ btn-primary s dnešním `confirm`; „Zpět“.

**14 Import číselníku** (`investra.codelist.import.wizard`)
- Dnes: akce `action_codelist_import` „Import číselníku“; kroky `state` upload/preview/done; tlačítka „Zobrazit náhled“ (primary,
  upload), „Zapsat“ (primary, preview, confirm), „Zpět“ (`action_back`, preview), „Zavřít“ (cancel, mimo preview).
- Titulek: „Importovat číselník“. První řádek: žádný záznam – vynechat. Co se stane: alert-info v kroku preview → `<ul>` bez rámečku
  (3 věty), `invisible="state != 'preview'"` ponechat.
- Tlačítka beze změny (vícekrokový průvodce má vlastní „Zpět“ na předchozí krok; „Zavřít“ zůstává). Nejasné N10.

---

## 3. CSS (`investra_theme/static/src/scss/theme.scss`)

Ověřeno (Odoo `20.0`, `web/static/src/views/form/form_controller.scss` a šablona `web.Form.InnerGroup`):
`.o_inner_group` je `div.o_inner_group.grid`; od `sm` `grid-template-columns: fit-content(150px) minmax(0, 1fr)`,
s `.o_form_fw_labels` `150px 1fr`; buňky `.o_cell.o_wrap_label` (popisek) a `.o_cell.o_wrap_input` (pole), v řádkovém režimu obalené
`div.o_wrap_field_inline.d-flex.d-sm-contents`; do `767.98px` mixin `form-break-table` (jeden sloupec); malé dialogy
`.modal .modal-dialog.modal-sm … .o_inner_group` vždy jeden sloupec. `col=` negeneruje žádnou šířku sloupců.

Versálky dnes: `theme.scss:199-200` (`.o_investra_metric_item label` – `letter-spacing: .04em; text-transform: uppercase;`) a
`investra_nav/static/src/valuation_summary/valuation_summary.scss:70-76` (`.o_investra_label` – `letter-spacing: 0.06em;
text-transform: uppercase;`, pás ocenění). Pozor: `theme.scss:227-231` barví popisky polí jen pro čtení `!important` na Petroleum –
popisky pásů proto potřebují `!important`.

Úpravy:
1. `theme.scss:179-210` (`.o_investra_metric_strip`) – v `label` odstranit řádky `letter-spacing: .04em;` a `text-transform: uppercase;`,
   `font-size: 11px` → `12px`, doplnit `color: $investra-graphite-2 !important;` a selektor rozšířit o `.o_investra_band_label`.
2. Za blok `.o_form_view { … }` (za řádek 211) vložit:

```scss
// ZJ-26: jednotný vzhled formulářů (varianta B, schválil Martin 2026-11-20).
.o_form_view {
    // Pás údajů pod nadpisem: malý šedý popisek nad hodnotou. .o_investra_metadata zůstává jako starší název.
    .o_investra_band {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 4px 24px;
        margin-bottom: 18px;
        padding-bottom: 14px;
        border-bottom: 1px solid $investra-petroleum-4;

        .o_investra_band_item {
            min-width: 0;
        }

        label,
        .o_investra_band_label {
            display: block;
            margin-bottom: 2px;
            color: $investra-graphite-2 !important;
            font-size: 12px;
            font-weight: 600 !important;
        }

        .o_field_widget {
            color: $investra-graphite;
            font-weight: 500;
        }
    }

    // Upozornění pod pásem.
    .o_investra_alerts:not(:empty) {
        margin-bottom: 12px;

        .alert:last-child {
            margin-bottom: 0;
        }
    }

    // Nadpis cenného papíru: ISIN velkým písmem, název menším šedým.
    .o_investra_title h1 {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        column-gap: 12px;

        > .o_field_widget {
            flex: 0 1 auto;
            width: auto;
            min-width: 14ch;
        }

        > .o_investra_title_sub {
            flex: 1 1 20ch;
            font-size: 60%;
            font-weight: 500;

            &,
            input {
                color: $investra-graphite-2;
            }
        }
    }

    // Popisky v pevném sloupci 200 px ve všech skupinách (od md; pod 768 px zůstává skládání Odoo).
    // Součtový řádek (oe_subtotal_footer) má vlastní rozvržení Odoo.
    @include media-breakpoint-up(md) {
        .o_inner_group:not(.oe_subtotal_footer) {
            grid-template-columns: 200px minmax(0, 1fr);

            &.o_form_fw_labels {
                grid-template-columns: 200px minmax(0, 1fr);
            }
        }
    }
}

// Dialogy: první řádek, „Co se stane“ bez rámečku, povinná pole s hvězdičkou, nevratná akce v Ember.
.modal .o_form_view {
    .o_investra_dialog_subject {
        margin-bottom: 12px;
        color: $investra-petroleum;
        font-size: 1.1rem;
        font-weight: 600;

        .o_field_widget {
            display: inline;
        }
    }

    .o_investra_dialog_effect {
        margin-bottom: 12px;

        .o_investra_dialog_effect_title {
            color: $investra-graphite-2;
            font-size: 12px;
            font-weight: 600;
        }

        ul {
            margin: 4px 0 0;
            padding-left: 1.2em;
        }
    }

    .o_wrap_label:has(+ .o_wrap_input .o_required_modifier) .o_form_label::after {
        content: " *";
    }
}

.o_web_client .btn.o_investra_btn_ember {
    background-color: $investra-ember;
    border-color: $investra-ember;
    color: $investra-petroleum-0;   // kontrast 4,5 : 1; bílá na Ember má jen 3,5 : 1 (N11)

    &:hover,
    &:focus {
        background-color: $investra-ember-2;
        border-color: $investra-ember-2;
        color: $investra-petroleum-0;
    }
}
```

3. Stávající `.o_investra_metadata` (`theme.scss:153-177`) ponechat (používá ji formulář fondu a starší dědění), nebo selektor sloučit
   `.o_investra_band, .o_investra_metadata` – bez vlivu na pole.
4. `docs/vzhled/zasady-obrazovek.md`, „Rozvržení detailu“ bod 3: „štítek velkými písmeny (11 px, 600, Graphite 2)“ →
   „štítek normálním písmem (12 px, 600, Graphite 2)“; doplnit oddíl „Formuláře se zadáním“ pravidly 2.1 zadání.

Specifičnost: `.o_form_view .o_inner_group:not(.oe_subtotal_footer)` (0,3,0) přebije Odoo `.o_form_view .o_inner_group` (0,2,0);
`.modal .modal-dialog.modal-sm .o_form_view .o_inner_group` (0,5,0) zůstává silnější → malé dialogy dál v jednom sloupci.
`investra_theme` je v `web.assets_backend` po `web` (závisí jen na `web`).

---

## 4. Dlouhé popisky (> ~28 znaků) v těchto formulářích

Zjištěno skriptem nad všemi poli 11 pohledů + 7 dědění (efektivní popisek = `string` v pohledu, jinak v Pythonu); znaky, ne bajty.

| Model | Pole | Dnes (znaků) | Návrh (znaků) | Kde změnit |
|---|---|---|---|---|
| investra.fund.class | shares_common | Podílí se na společných položkách (33) | Podílí se na spol. položkách (28) | investra_fund/models/fund.py:231 (hláška `investra_nav/models/fund_class.py:48` cituje starý název – sjednotit) |
| investra.fund.class | rounding_owner | Rozdíl ze zaokrouhlení kusů (27) | Rozdíl ze zaokr. nese (21) | investra_fund/models/fund.py:225 (příklad ze zadání) |
| investra.instrument | accrual_note | Zdůvodnění lineárního úročení (29) | Důvod lineárního úročení (24) | investra_instruments/models/instrument.py:193 |
| investra.instrument.repayment | remaining_before | Zbývající jistina před splátkou (31) | Zbývající jistina před (22) | investra_nav/models/instrument_accrual.py:373 |
| investra.instrument.repayment | remaining_after | Zbývající jistina po splátce (28) | Zbývající jistina po (20) | investra_nav/models/instrument_accrual.py:374 |
| investra.dividend | excess_amount | Přeplatek nad smluvní sazbou (28) | Přeplatek nad sml. sazbou (25) | investra_nav/models/dividend.py:72 |
| investra.trade | derecognition_reason | Důvod úpravy ceny odúčtování (28) | Důvod jiné ceny odúčtování (26) | investra_nav/models/trade_position.py:39 |
| investra.class.movement | capital_amount_class | Změna kapitálu třídy (měna kurzu) (33, `string` v pohledu) | Změna kapitálu (měna kurzu) (27) | pohled `investra_nav/views/nav_views.xml:939` (Python `movement.py:111` má „Změna kapitálu v měně kurzu“ – neměnit) |
| investra.class.movement | capital_amount | Změna kapitálu třídy (funkční měna) (35, pohled) | Změna kapitálu (funkční) (24) | pohled `nav_views.xml:940` |
| investra.class.movement | amount | Hrubá částka ve funkční měně (28, Python) | Hrubá částka (funkční) (22) | doplnit `string` v pohledu `nav_views.xml:941` (Python `movement.py:92` ponechat kvůli seznamu/historii) |

Dlouhé, ale bez popisku ve formuláři (alert / text v řádku) – neměnit: `investra.trade.settlement_fx_note` (30, instrument.py:733),
`investra.trade.average_cost_price` (29, trade_position.py:24), `investra.fee.rule.no_common_class_warning` (30, fee_rule.py:167),
`investra.instrument.classification_gap` (27, instrument_master/models/instrument.py:69).
Neměnit kvůli testům historie: `investra.fund.class.entry_fee_statute_ref` „Vstupní poplatek – článek statutu“ (fund.py:240; formulář má
`string` „Článek statutu“), `investra.instrument.max_price_age` „Maximální stáří ceny (dny)“ (26, instrument.py:156).
Testy na nové kratší texty jsem nenašel (grep v `*/tests`); změna `string` v Pythonu mění i texty historie (chatter) a záhlaví seznamů.

---

## Nejasnosti (rozhodne Martin / Claude)

> **Rozhodl Martin 2026-11-20 (platí přednostně před texty N1–N13 níže):**
> - N1, N3, N7, N9: **ano**, smíš přidat jen zobrazovací pole v Pythonu (nestored related/computed, `_compute_display_name`), bez
>   migrace a bez změny výpočtů: related `instrument_isin`/`instrument_name` pro nadpis Obchodu, Splátky a Dividend (název šedě);
>   computed `settlement_date` na derivátu (nejpozdější datum vypořádání z `leg_ids`) pro šedý podnadpis; čitelný `display_name`
>   pro `investra.trade` („Nákup/Prodej ISIN název, kusy, datum“), `investra.instrument.repayment` („ISIN druh datum“) a
>   `investra.valuation.external` („účet/třída, částka, datum“), datum dd.MM.yyyy; computed popisek „Kurz za {množství} {měna}“.
>   **Pozor:** změna `display_name` nesmí rozbít testy, které ho porovnávají – spusť testy dotčeného modulu; když spadnou kvůli textu, uprav test jen tehdy,
>   pokud ověřuje právě název; jinak název nech a použij related pole v dialogu.
> - N2: druh splátky v nadpisu ne (test `test_accrual.py:404`), zůstává v pásu.
> - N4: Historie = chatter, žádná záložka navíc. N5: v pásu „Aktivní“ (`active`), „Způsob“ = `method`.
> - N6: **ano**, texty „Co se stane“ v Pythonu přepiš na krátký seznam (HTML `<ul><li>`), zachovej podřetězce, které hledají testy.
> - N8 + N11: Ember u storna (obchod, pohyb, splátka), vrácení ocenění a ukončení opravy; ostatní primární. Text na Emberu Petroleum 0.
> - N10: ponechat. N12: versálky zrušit **i** v pásu ocenění (`valuation_summary.scss:75`). N13: ověř v prohlížeči a uveď ve zprávě.
> - Oddíl 2.2 „ostatní formuláře“: projdi `grep -L "oe_title" addons/custom/*/views/*.xml` jen u formulářů modelů s polem `name`;
>   doplň nadpis `<div class="oe_title"><h1><field name="name"/></h1></div>` a `string=` u skupin bez nadpisu. Max 1 commit, seznam do ZJ-26.

- **N1** Nadpis „ISIN + název, název menším šedým“ u Obchodu, Splátky a Dividend: v h1 je many2one `instrument_id`, jehož `display_name`
  je „ISIN název“ jedním písmem. Oddělené šedé písmo vyžaduje nová zobrazovací pole (např. related `instrument_id.isin` / `.name`) =
  Python, oranžová zóna podle zásad. Podklad je bez nich (nadpis zůstává „ISIN název“ jedním písmem). U Nástroje jde čistě v XML (1.5).
- **N2** Splátka „+ šedě druh splátky“ v nadpisu: `kind` v nadpisu by v arch předběhl `fund_id` → test `test_accrual.py:404` spadne.
  Vynecháno; druh je v pásu.
- **N3** Derivát „+ šedě datum vypořádání“: model `investra.derivative` nemá pole data vypořádání (je na nohách `leg_ids`) → nové pole
  v Pythonu. Vynecháno.
- **N4** „Záložka Historie“ (Pravidlo úplaty, Daňové pravidlo): historie je chatter (ZJ-10), test vyžaduje jeden `<chatter`. Podklad
  ponechává chatter vedle formuláře; záložka Historie nevzniká.
- **N5** Daňové pravidlo „Stav“: model nemá `state`, použito `active` (popisek „Aktivní“). „Metoda“ = pole `method` s popiskem „Způsob“
  (ponecháno podle Pythonu a filtru „Způsob“).
- **N6** „Co se stane“ jako seznam: u průvodců 1, 2, 3, 6, 9 je text v Pythonu (`effect`, jeden odstavec; testy hledají podřetězce
  „bez storna“, „2030-01-01: 0.0201644 → 0.0252055“). Seznam vyžaduje úpravu textů v Pythonu; podklad text jen zbavuje rámečku.
- **N7** První řádek dialogu: `investra.trade`, `investra.instrument.repayment` a `investra.valuation.external` nemají `name` ani
  `_compute_display_name` → zobrazí technický název; pohyb ukazuje datum ISO. Čitelný řádek (ISIN, název, kusy, datum) vyžaduje
  `_compute_display_name` nebo related pole v Pythonu.
- **N8** Které akce jsou „nevratné“ (Ember): storna a vrácení ano; Ukončit opravu, Ruční kurz („nejde změnit ani smazat“) a Založit knihu
  (měna a rámec nejdou změnit) – nerozhodnuto; podklad: Ukončit opravu Ember, ostatní Petroleum.
- **N9** „Kurz za {množství} {měna}“ jako jeden dynamický popisek nejde v XML (popisky jsou statické); podklad řeší řádkem
  „Kurz za | [100] HUF = [kurz] vyhlášený …“. Doslovný popisek = nové výpočtové pole v Pythonu.
- **N10** Import číselníku má „Zpět“ na předchozí krok a „Zavřít“; jednotné „Zpět“ = zavřít by kolidovalo. Ponecháno.
- **N11** Bílý text na Ember má kontrast 3,5 : 1 (pod 4,5 : 1); podklad používá text Petroleum 0 (4,5 : 1). Potvrdit s paletou.
- **N12** Pás ocenění (`valuation_summary.scss:75`) má také versálky; bod 3 zásad popisuje právě tento pás → doporučuji změnit také,
  zadání to výslovně neuvádí. Snímek 35/39 jsou data ocenění, CSS ho neovlivní.
- **N13** Šířka nadpisu s ISIN a názvem (`o_investra_title`) a pozice pole v pásu u boolean `active` – ověřit v prohlížeči (vstupy
  v h1 Odoo roztahuje; CSS výše to omezuje, ale nebylo spuštěno).
