# Návrh: evidence emitentů, nástrojů a portfolií (číselníky ČNB, IFRS 9, účetní profil)

Stav 15. 11. 2026. Připravil Claude podle zadání uživatele ze 14. 11. 2026; doporučení a odpovědi na blokující otázky
schválil uživatel 14.–15. 11. 2026 (oddíl 1). Úkoly k provedení jsou v `docs/ukoly/IM-*.md`, rozdělení mezi modely
v `docs/ukoly/IM-00-prehled.md`.

**Účtování zůstává funkční a tato etapa ho nemění.** Obchody, vypořádání, úročení (lineárně i efektivní mírou), splátky,
přecenění portfolia a NAV dál počítá a účtuje `investra_nav` podle zařazení nástroje v portfoliu (role účtu → účet knihy).
Etapa doplňuje evidenci a kontroly kolem toho; do výpočtů a zápisů nesahá.
Co systém neumí dnes a tato etapa to nepřidává (samostatné plány): účtování FVOCI do vlastního kapitálu (otevřený bod
„Účtování FVOCI“), očekávané úvěrové ztráty (ECL), reklasifikace mezi portfolii, výkazy SDAT.

## 1. Schválená rozhodnutí

1. **Žádné paralelní modely.** Emitent = `res.partner` + `investra.counterparty.profile`; nástroj = `investra.instrument`;
   portfolio = `investra.fund.portfolio`; zařazení nástroje v portfoliu = `investra.portfolio.classification`.
2. **Nový addon `investra_instrument_master`** (závislost `investra_counterparty`): číselníky a rozšíření stávajících modelů
   přes `_inherit`. Výjimka je přesun SPPI (bod 4), který se dělá přímo v `investra_instruments`.
3. **Portfolio určuje oceňovací kategorii** (AC, FVOCI_D, FVOCI_E, FVTPL). Stávající rozhodovací strom IFRS 9 v zařazení
   zůstává a slouží jako serverová kontrola kompatibility: vypočtená kategorie zařazení se musí rovnat kategorii portfolia.
   Tentýž nástroj může být v jednom portfoliu AC a v jiném FVTPL (rozhoduje obchodní model portfolia).
   Upřesňuje rozhodnutí 2026-11-11 „Obchodní model fondu a zařazení nástroje“.
4. **SPPI je vlastnost nástroje**, společná pro všechny fondy (uživatel 15. 11. 2026). Zařazení ji přebírá z nástroje.
   Povaha nástroje, určení a volby (4.1.5, 5.7.5) a držení k obchodování zůstávají na zařazení a portfoliu.
5. **Typ nástroje (`type_id`) zůstává** pro NAV. BA0088 je regulatorní druh vedle něj; povinný je až při potvrzení
   klasifikace nástroje a jen u typů s příznakem „Vyžaduje BA0088“.
6. **Seed BA0088** jen z kódů uložených v `docs/cnb/`. Celý číselník BA0088 (verze 023.000, platnost od 1. 1. 2024,
   84 položek a 35 souhrnných) je od 15. 11. 2026 v `docs/cnb/ciselnik-BA0088-v023.csv`. U nástroje se nabízí 52 kódů
   ze zadání (příznak „Nabízet u nástroje“); nadřazené a podrobnější položky jsou v číselníku jen pro úplnost.
7. **Jedna nová skupina** „Investra: správce číselníků“. Ostatní role: čtení = `account.group_account_readonly`,
   příprava = `investra_entity.group_valuation_preparer`, kontrola a schválení = `investra_entity.group_valuation_approver`.
8. Nová pole **nejsou povinná v databázi** (stávající testy zakládají nástroje a portfolia bez nich); povinnost se vynucuje
   ve formuláři a při potvrzení nebo schválení.
9. Kontrolní číslice ISIN je jen upozornění (rozhodnutí 2026-11-13 zůstává). Portfolio má stavy Návrh / Schváleno /
   Uzavřeno; „v užívání“ ukazuje zámek po prvním obchodu.
10. Účetní profil odkazuje na roli účtu (`investra.account.role`), ne na účet. V této etapě se jen vybírá a porovnává
    s rolí zařazení; účtování se nemění.

## 2. Konvence (platí pro všechny úkoly)

- Odoo 20 Community, obraz připnutý. Jádro Odoo, `addons/third_party` ani moduly mimo rozsah úkolu se nemění.
- Práva: `security/ir.access.csv`, sloupce `id,name,model_id,group_id/id,operation,domain`; vzor
  `addons/custom/investra_counterparty/security/ir.access.csv`.
- Omezení přes `models.Constraint` a `models.UniqueIndex`; chyby česky přes `self.env._()`; popisky polí česky.
- Zákazy ve `write`/`create` neplatí pro superuživatele (`self.env.su`), stejně jako ve stávajícím kódu.
- `@api.constrains` se nespouští při přepočtu uloženého computed pole: kontroly navazovat na vstupní pole.
- V kódu, testech, komentářích a commitech neuvádět názvy neveřejných podkladů ani cizích systémů.
- **Vzhled zachovat** (pokyn uživatele 15. 11. 2026): grafika aplikace je odladěná v `investra_theme` a ve stávajících
  pohledech. Nové obrazovky přebírají stávající třídy a rozvržení (`o_investra_*`, hlavička s řádkem údajů jako ve
  formuláři nástroje, pruhy `alert alert-warning`, barevné štítky stavů jako v seznamu Ocenění). Do stávajících formulářů
  se jen přidává přes XPath; nic se nepřesouvá, nepřejmenovává ani neodstraňuje. Žádné nové styly, barvy ani úpravy
  `investra_theme`; návrhy v `docs/vzhled/` (`navrh-detail-nastroje.html`, `navrh-seznam-nastroju.html`,
  `navrh-seznamu-obchodnich-modelu.html`) jsou závazný vzor. Zlepšení vzhledu jen jako návrh ve výsledku úkolu.
- Verze nového addonu `20.0.0.1.0`; každý další úkol zvýší třetí číslo (`20.0.0.2.0` …), migrace jen kde je uvedena.

### Testy na čisté databázi (ověřený postup)

`tools/run_tests.sh` je napevno na `investra_test` a instalace nového modulu tam je změna schématu: jen se souhlasem
uživatele. Do té doby dočasná databáze `investra_ci_master` (po testech smazat včetně filestore a napsat to ve zprávě):

```
C="docker compose -f docker-compose.investra.yml run --rm --no-deps -T odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d investra_ci_master --db-filter=^investra_ci_master$ --stop-after-init --no-http --max-cron-threads=0"
$C -i investra_instrument_master --without-demo=all      # 1) instalace bez testů
$C -i l10n_cz                                            # 2) jinak padají testy zakládající knihu
$C -u investra_instrument_master --test-enable --test-tags /investra_instrument_master   # 3) testy
```

„0 testů“ ani ERROR v logu není úspěch. Log ukládat do `.test-logs/` a číst jen při neúspěchu.

## 3. Datový model

### 3.1 `investra.codelist.mixin` (abstraktní; modely číselníků dědí i `mail.thread`)

| Pole | Typ | Pozn. |
|---|---|---|
| `code` | Char, required, index, tracking | `unique(code)`; po založení mění jen superuživatel |
| `name` | Char, required, tracking | |
| `active` | Boolean, default True, tracking | |
| `sequence` | Integer, default 10 | `_order = "sequence, code"` |
| `valid_from`, `valid_to` | Date, tracking | kontrola do ≥ od |
| `source_methodology` | Char, tracking | např. `FOFI20261201 / D_S_RNBD_4 v004.000` |
| `note` | Text | |
| `locally_modified` | Boolean, readonly | nastaví `write` bez kontextu `investra_codelist_import` |

`display_name` = „kód název“. Mazání: žádná skupina nemá právo `d`; vazby `ondelete="restrict"`.

### 3.2 Číselníky

| Model | Pole navíc |
|---|---|
| `investra.ba0088.code` | `selectable` Boolean „Nabízet u nástroje“ (doména pole `ba0088_id` nástroje); `asset_family` Selection (debt, equity, fund, certificate, bill, coupon, direct_equity, derivative, other), povinné u `selectable`; `parent_code` Char; `group_id` M2O `investra.ba0088.group`; `requires_issuer`, `requires_maturity`, `requires_justification` Boolean; `leverage_rule` Selection (none, must_true, must_false), default none |
| `investra.ba0088.group` | — |
| `investra.esa.aggregate.sector` | `help_text` Text |
| `investra.esa.code` | `aggregate_sector_id` M2O required tracking; `residency` Selection (r „Rezident“, nr „Nerezident“) required tracking; `residency_warning` Char computed (první číslice 1 ≠ r, 2 ≠ nr); `esa2010_sector_id` M2O `investra.esa.sector`; `any_country` Boolean |
| `investra.country.group.membership` (bez mixinu, s `mail.thread`) | `country_id` M2O `res.country` required; `group` Selection (eu „EU“, eea „EHP mimo EU“) required; `valid_from` Date required; `valid_to`; `source` Char; kontrola: období stejné země a skupiny se nepřekrývají |
| `investra.measurement.category` | `help_text`; `ifrs9_category` Selection (fvtpl, fvoci, amortised) required; záznamy zakládá jen modul |
| `investra.classification.reason` | `help_text`; `requires_note` Boolean |
| `investra.cfi.ba0088.map` (bez mixinu) | `cfi_prefix` Char required; `ba0088_id` M2O required; `valid_from`, `valid_to`; `source`; bez seed dat |

### 3.3 `investra.counterparty.profile` (rozšíření)

| Pole | Typ | Pozn. |
|---|---|---|
| `esa_code_id` | M2O `investra.esa.code`, tracking | ve formuláři povinné; kontrola: residency r ⇒ země CZ; nr ⇒ země ≠ CZ, kromě `any_country` |
| `sector_id` (stávající, required) | | při zadání `esa_code_id` se doplní z `esa_code_id.esa2010_sector_id` (onchange + create/write, když není v hodnotách) |
| `resident_status` | related `esa_code_id.residency`, store | |
| `issuer_type_id` | related `esa_code_id.aggregate_sector_id`, store | |
| `eu_status` | Selection (cz, eu, eea, non_eu, unknown), compute, store | k dnešku; metoda `_eu_status_at(day)`; přepočet při změně země a členství |
| `derivation_note` | Char compute | „Odvozeno z ESA 2002212; region ze země DE a členství v EU“ |
| `review_state` | Selection (draft „Ke kontrole“, reviewed „Zkontrolováno“), tracking | tlačítko jen pro schvalovatele; potvrzenou verzi nejde měnit, změna = nová verze s „Platí od“ |
| `reviewed_by`, `reviewed_on` | M2O `res.users`, Date, readonly | |
| `change_reason` | Char, tracking | povinné u druhé a další verze protistrany |
| `source` | Selection (manual, import, lei, sdat), default manual | |
| `is_latest` | Boolean store | udržuje create/write/unlink sourozenců |
| `lei` (stávající) | | navíc: stejný LEI nesmí mít jiná protistrana |

### 3.4 `investra.instrument` a typ (rozšíření)

| Pole | Typ | Pozn. |
|---|---|---|
| `ba0088_id` | M2O restrict, index, tracking | |
| `asset_family` | related `ba0088_id.asset_family`, store | řídí viditelnost polí |
| `cfi_code` | Char(6), tracking | převod na velká písmena, kontrola `^[A-Z]{6}$` |
| `ba0088_note` | Text, tracking | povinné, když `ba0088_id.requires_justification` |
| `leverage_flag` | Boolean, tracking | kontrola podle `leverage_rule` |
| `issue_date` | Date | ≤ `maturity_date` |
| `nominal_value` | Monetary (`currency_id`) | ≥ 0 |
| `coupon_type` | Selection (none, fixed, floating, zero, other) | |
| `seniority` | Selection (senior, subordinated, at1, other) | |
| `convertible`, `perpetual` | Boolean | |
| `underlying_description` | Char | |
| `underlying_instrument_id` | M2O `investra.instrument` | samostatné kupóny |
| `isin_warning` | Char compute | `stdnum.isin.is_valid`; neblokuje |
| `cfi_warning` | Char compute | podle `investra.cfi.ba0088.map`; neblokuje |
| `master_source` | Selection (manual, import, lei, sdat), default manual | |
| `review_state`, `reviewed_by`, `reviewed_on` | jako u profilu | po potvrzení se `ba0088_id`, `cfi_code`, `isin`, `issuer_id` mění jen průvodcem s důvodem |
| `classification_gap` | Char compute | chybí posouzení SPPI u dluhového nástroje |
| SPPI (úkol IM-05, v `investra_instruments`) | `sppi_status` Selection (not_assessed, pass, fail, na), default not_assessed, tracking; `sppi_note` Char; `sppi_version` Selection (stávající hodnoty); `sppi_assessed_by`, `sppi_assessed_on` | zamčeno po prvním obchodu s nástrojem |

`investra.instrument.type`: `ba0088_required` Boolean (seed: vypnuto u `deposit`, `repo`, `loan`).

Nepřidává se: `internal_code` (je `code`), `other_id` (je `identifier`), `active`.

`investra.masterdata.change` (jen čtení, zakládá průvodce `investra.masterdata.change.wizard`): `res_model`, `res_id`,
`record_name`, `field_name`, `old_value`, `new_value`, `effective_date`, `reason` (required), `user_id`, `create_date`.

### 3.5 `investra.fund.portfolio` (rozšíření)

| Pole | Typ | Pozn. |
|---|---|---|
| `code` | Char, tracking | jedinečný ve fondu, je-li vyplněn (`UniqueIndex … WHERE code IS NOT NULL`) |
| `measurement_category_id` | M2O, tracking | zamčeno po prvním obchodu |
| `business_model` (stávající) | `selection_add=[("na", "Nepoužije se")]` | zamčeno už dnes |
| `classification_reason_id` | M2O, tracking | zamčeno po prvním obchodu |
| `reason_help` | Text related `classification_reason_id.help_text` | vysvětlení pod polem |
| `assessment` (stávající) | | slouží jako odborné zdůvodnění |
| `strategy_description`, `sales_policy_description` | Text, tracking | |
| `valid_from`, `valid_to` | Date, tracking | |
| `state` | Selection (draft, approved, closed), default draft, readonly, tracking | mění jen tlačítka |
| `approved_by`, `approved_on` | M2O, Datetime, readonly | |
| `review_frequency` | Selection (annual, semiannual, ad_hoc) | |
| `last_review_date`, `next_review_date` | Date | |
| `is_locked`, `lock_date` | compute, neuložené | první obchod portfolia (`investra.trade`, `sudo`) |
| `profile_assignment_ids` | O2M | |

Kategorie × obchodní model: AC ⇒ `hold_to_collect`; FVOCI_D ⇒ `hold_collect_sell`; FVOCI_E ⇒ `na`; FVTPL ⇒ cokoli.
Schválení vyžaduje `code`, kategorii, důvod, `assessment`, `valid_from`.

### 3.6 `investra.portfolio.classification` (rozšíření)

- Kontrola kompatibility (jen když má portfolio kategorii): `ifrs9_category` zařazení = `measurement_category_id.ifrs9_category`;
  u FVOCI_D navíc povaha `debt`/`puttable`, u FVOCI_E `designation == "fvoci_equity"`. Spouští se i při změně kategorie
  portfolia (z `write` portfolia nad jeho zařazeními).
- `accounting_profile_id` (compute), `profile_state` Selection (ok, missing, deviates).

### 3.7 Účetní profil

- `investra.accounting.profile`: mixin + `role_id` M2O `investra.account.role`.
- `investra.accounting.profile.assignment`: `company_id` required (default z portfolia); `portfolio_id`; `ba0088_id`;
  `ba0088_group_id` (ne obojí zároveň); `accounting_profile_id` required; `priority` Integer default 10; `valid_from`
  required; `valid_to`; `note`. Kontrola: dvě časově se překrývající pravidla se stejnou společností, portfoliem,
  kódem, skupinou a prioritou nejdou uložit.
- Výběr `_select(company, portfolio, ba0088, day)`: pravidla společnosti platná k datu, kde portfolio sedí nebo je prázdné
  a kód sedí, sedí jeho skupina, nebo jsou oba prázdné. Pořadí: `priority` vzestupně, pak kód před skupinou před prázdným,
  pak konkrétní portfolio před prázdným. Bez výsledku: `profile_state = missing`; metoda `_require_profile()` vyhodí
  chybu „Pro portfolio %s a druh %s není nastaven účetní profil.“ (pro budoucí účtování).

## 4. Seed data

| Soubor | Obsah | Zdroj |
|---|---|---|
| `data/esa_aggregate_sector.xml` | VLI Vládní instituce, BANK Banky a obdobné úvěrové instituce, FIN Ostatní finanční instituce, NFP Nefinanční podniky, OST Ostatní | zadání |
| `data/esa_code.xml` | 80 kódů `D_S_RNBD_4`, názvy doslova z katalogu | `docs/cnb/ciselniky-FOFI20261201.csv`, generuje `tools/codelist_seed.py` |
| `data/ba0088_group.xml` | GOV_BONDS, OTHER_BONDS, CERTIFICATES, EQUITIES, FUND_SECURITIES, OTHER_EQUITY_SECURITIES, BILLS_COUPONS, FORWARDS_FUTURES, SWAPS, OPTIONS_AND_OTHER_DERIVATIVES, OTHER_INSTRUMENTS | zadání |
| `data/ba0088.xml` | 84 položek číselníku BA0088 v023.000 (souhrnné `S_…` se nezakládají); `parent_code` = nejdelší existující kratší kód se stejným začátkem; `selectable` u 52 kódů níže | `docs/cnb/ciselnik-BA0088-v023.csv`, generuje `tools/codelist_seed.py` |
| `data/measurement_category.xml` | AC (amortised), FVOCI_D (fvoci), FVOCI_E (fvoci), FVTPL (fvtpl) | zadání |
| `data/classification_reason.xml` | BUSINESS_MODEL, SPPI_FAIL, MANDATORY_FVTPL, FVTPL_DESIGNATION, EQUITY_FVOCI_ELECTION, OTHER (`requires_note`) | zadání |
| `data/country_membership.xml` | EU: 27 zemí standardní skupiny `base.europe`, platí od 2020-02-01 | standard Odoo; EHP nezakládat (chybí zdroj) |

Všechny soubory `noupdate="1"` (úpravy uživatele přežijí upgrade); nové verze metodiky jdou průvodcem importu.

**ESA → typ emitenta** (ověřeno, pokrývá všech 80 kódů): VLI = 1311000–1314000, 2003110–2003140 (8); BANK = 1210000,
122xxxx, 2002100, 20022xx (18); FIN = 123xxxx–129xxxx, 20023xx–20029xx (42); NFP = 110xxxx, 2001xxx (6);
OST = 1443000, 1500000, 2004430, 2005000, 2009031, 2009035 (6). Kódy 2009031 a 2009035 mají `any_country`.

**ESA → `Z_ESA2010`** (`esa2010_sector_id`): rezidenti prvními třemi číslicemi + `0000` (1221200 → 1220000), vládní
instituce shodný kód; nerezidenti prvními pěti číslicemi + `00` (2002212 → 2002200), 2001001–3 → 2001000, vládní shodný
kód, 2009031 a 2009035 → 2009030. Kódy 1443000 a 2004430 nechat prázdné (potvrdí metodik).

**BA0088 → rodina a skupina** (52 kódů s `selectable`; ostatní položky bez rodiny a skupiny): 111, 112, 141 → debt,
GOV_BONDS; 12, 13, 142, 149, 15, 41, 42, 17, 199 → debt, OTHER_BONDS; 191, 63 → certificate, CERTIFICATES (191
`leverage_rule` must_false, 63 must_true); 211, 212, 219 → equity, EQUITIES; 217, 218, 225, 226 → fund, FUND_SECURITIES;
23, 24, 27, 29 → equity, OTHER_EQUITY_SECURITIES; 8 → direct_equity, OTHER_EQUITY_SECURITIES; 311, 312 → bill,
BILLS_COUPONS; 36, 37 → coupon, BILLS_COUPONS; 6111, 6112, 6119, 612 → derivative, FORWARDS_FUTURES; 6131–6136, 6139 →
derivative, SWAPS; 6191, 6192, 6199, 6211, 6212, 6221, 6222, 623, 629, 69 → derivative, OPTIONS_AND_OTHER_DERIVATIVES;
7 → other, OTHER_INSTRUMENTS (`requires_justification`). `requires_issuer` u všech kromě derivátů; `requires_maturity`
u debt a bill.

**Nápovědy důvodů klasifikace** (`help_text`):
- BUSINESS_MODEL: Kategorie vychází ze způsobu řízení portfolia a u dluhových nástrojů z výsledku testu SPPI.
- SPPI_FAIL: Smluvní peněžní toky nesplňují test SPPI, proto nástroj nemůže být v naběhlé hodnotě ani ve FVOCI.
- MANDATORY_FVTPL: Reálná hodnota do výsledku je povinná podle povahy nástroje nebo doloženého odborného posouzení.
- FVTPL_DESIGNATION: Dobrovolná neodvolatelná volba při prvotním zachycení, typicky k odstranění účetního nesouladu.
- EQUITY_FVOCI_ELECTION: Neodvolatelná volba FVOCI pro kapitálový nástroj, který není držen k obchodování.
- OTHER: Jiný doložený důvod; vyžaduje textové vysvětlení a schválení.

## 5. Oprávnění

| Model | čtení účetnictví | příprava | schvalování | správce číselníků |
|---|---|---|---|---|
| číselníky, CFI mapa, členství zemí, účetní profil a přiřazení | r | r | r | cru |
| `investra.masterdata.change` | r | r | r | r |
| průvodce importem číselníku | — | — | — | crud |
| průvodce změnou klasifikace | — | crud | crud | — |

Pravidlo záznamů jen pro přiřazení profilů: `[('company_id', 'in', company_ids)]`. Tlačítka „Potvrdit klasifikaci“
a „Schválit“ jen pro skupinu schvalování; stejná kontrola i v metodě.

## 6. Uživatelské rozhraní

- **Nastavení → Číselníky** (nová skupina pod `investra_entity.menu_setup`, pořadí 25): Druhy CP (BA0088), Skupiny BA0088,
  Sektory ESA (detail), Typy emitenta, Členství zemí v EU/EHP, Oceňovací kategorie, Důvody klasifikace, Import číselníku.
  Seznamy `editable="bottom"`, hledání podle kódu, názvu, aktivity; formulář s chatterem; `code` readonly po uložení.
- **Nastavení → Účtování:** Účetní profily, Přiřazení účetních profilů.
- **Emitenti a protistrany** (stávající nabídka Protistrany): seznam Protistrana, LEI, Země, ESA kód, R/NR, Region, Typ
  emitenta, Platí od, Stav kontroly; filtry Aktuální (výchozí), Chybí ESA, Chybí LEI, Nezkontrolováno, Rezident,
  Nerezident, EU, Mimo EU; formulář: Identifikace · Regulatorní klasifikace · Odvozené hodnoty · Kontrola.
- **Nástroj** (XPath do `investra_instruments.view_instrument_form`): v hlavičce za Typ pole Druh ČNB (BA0088) a CFI;
  skupina „Klasifikace ČNB“ (BA0088, rodina, CFI, zdůvodnění u kódu s `requires_justification`, páka u rodiny certificate);
  skupina „Emitent“ s aktuálním ESA, typem a regionem; skupina „Test SPPI“ u dluhových; záložka „Detail“; pruhy
  upozornění (`classification_gap`, `isin_warning`, `cfi_warning`). Seznam a filtry: Chybí BA0088, Chybí CFI, Bez emitenta,
  Kategorie 7, Nezkontrolováno, Po splatnosti.
- **Portfolia** (stávající Obchodní modely): seznam Fond, Kód, Název, Kategorie, Obchodní model, Stav, Platí od/do,
  Uzamčeno; formulář se záložkami Identifikace · Klasifikace IFRS 9 · Řízení a kontrola · Účetní profil · Zařazení nástrojů;
  pruh po zámku: „Portfolio je v užívání od {datum}. Kategorii, obchodní model a důvod klasifikace nejde změnit; založte
  nové portfolio a toto uzavřete.“

## 7. Kontroly a hlášky

| Kontrola | Hláška |
|---|---|
| CFI | „CFI musí mít přesně 6 velkých písmen A–Z: %s.“ |
| ESA × země | „ESA kód %s je pro rezidenty; země emitenta musí být Česká republika.“ / „ESA kód %s je pro nerezidenty; země emitenta nesmí být Česká republika.“ |
| LEI | „LEI %s už má protistrana %s.“ |
| Páka | „Druh %s vyžaduje zaškrtnutou páku.“ / „Druh %s páku nepřipouští.“ |
| Zdůvodnění | „Druh %s vyžaduje zdůvodnění.“ |
| Potvrzení nástroje | „Před potvrzením doplňte: %s.“ (BA0088 u typu s `ba0088_required`; emitent, splatnost podle BA0088) |
| Změna po potvrzení | „Klasifikace je potvrzená. Použijte Změnit klasifikaci a uveďte důvod.“ |
| SPPI po obchodu | „Po prvním obchodu s nástrojem nejde posouzení SPPI změnit.“ |
| AC/FVOCI_D bez SPPI | „Portfolio %s vyžaduje u nástroje splněný test SPPI; nástroj %s ho má %s.“ |
| AC/FVOCI_D + SPPI nesplněn | „Nástroj s nesplněným testem SPPI nelze zařadit do portfolia %s. Zařaďte ho do portfolia FVTPL.“ |
| Nekompatibilní kategorie | „Nástroj %(n)s vychází podle IFRS 9 jako %(c)s, portfolio %(p)s je %(k)s. Zařaďte ho do portfolia s kategorií %(c)s.“ |
| FVOCI_E bez volby | „Do portfolia FVOCI kapitálových nástrojů patří jen kapitálový nástroj s volbou podle IFRS 9 5.7.5.“ |
| Kategorie × model | „Kategorie %s vyžaduje obchodní model %s.“ |
| Zámek portfolia | „Po prvním obchodu nejde změnit kategorii, obchodní model ani důvod klasifikace.“ |
| Schválení portfolia | „Před schválením doplňte: %s.“ |
| Konflikt pravidel profilu | „Pro tuto kombinaci a prioritu už platí pravidlo %s.“ |

## 8. Otevřené body této etapy

- Číselník BA0088 je stažený z testovacího portálu SDAT (`sdatt.cnb.cz`); před ostrým provozem porovnat verzi
  s produkčním portálem. Složení domény `D_S_CPMKT_1` staženo není; 52 nabízených kódů je podle zadání.
- Členové EHP mimo EU a historie členství v EU před 1. 2. 2020 (zdroj).
- Vazba 1443000 a 2004430 na `Z_ESA2010`.
- Mezinárodní instituce: profil dál vyžaduje zemi (změna `required` je červená zóna).
- `BANK_SECTORS` v `investra_counterparty` neobsahuje nerezidentní banky (2002100, 2002200): ověřit s metodikem.
- Instalace `investra_instrument_master` do `investra_test` a `investra_vzhled`: se souhlasem uživatele a zálohou.
- Později (červená zóna): návrh role účtu zařazení z účetního profilu; povinnost kategorie portfolia v databázi.
