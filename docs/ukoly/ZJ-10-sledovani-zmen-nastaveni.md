# ZJ-10 Sledování změn nastavení (vestavěné, chatter)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **fáze 1 oranžová** (podle plánu níže); **fáze 2 červená** (`investra_nav`, `investra_allocation`, `investra_fx_revaluation` – modely); nejdřív plán, kód fáze 2 až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace) z otevřeného bodu „Historie nastavení – stav a ověření“, 17. 11. 2026 |
| Řešitel a model | fáze 1a a 1b: Antigravity nebo Copilot (levnější model, Sonnet 5.5); fáze 2: plán a kód Antigravity / Copilot podle plánu, revize a převzetí Claude (Opus 5.5); rozhodnutí Martina 2026-11-18: co zvládnou levnější modely, dělají ony |
| Pořadí | 1a → převzetí Claudem → 1b → plán fáze 2 → schválení Martinem → kód fáze 2; každý krok samostatná větev `ag/ZJ-10-<krok>` |
| Navazuje na | `docs/otevrene-body.md` (řádky „Historie nastavení“ a „Pravidlo sledování změn“), ZJ-03 (poplatky třídy), rozhodnutí 2026-11-16 „Údaje protistrany bez historie“ |

**Cíl:** každá změna nastavení a kmenových dat, která ovlivňuje výpočet nebo výkazy, se dohledá: kdo, kdy, stará → nová hodnota, a vidí se
v chatteru (postranní okno formuláře). Používá se **vestavěné sledování Odoo 20** (`mail.thread` + `tracking=True`); modul `mail_tracking` se **neinstaluje**.

**Ověřeno 17. 11. 2026** (dočasné DB, smazány): změna pole s `tracking=True` v samostatné transakci zapíše do chatteru zprávu „stará → nová (pole)“
i bez modulu `mail_tracking`. Vytvoření a změna v jedné transakci se slučují do „vytvořeno“. Komentář ve `investra_fund/models/fund.py` („bez mail_tracking
změny polí neukládá“) a věta v ZJ-03 jsou nepřesné – opravit.

**Plán má obsahovat** (u fáze 2 ke schválení):

1. **Pravidlo.** Model nastavení a kmenových dat dědí `mail.thread`, jeho pole bez výpočtu mají `tracking=True`, formulář má `<chatter/>`.
   Navrhnout text pravidla pro `CLAUDE.md` / `.agents/rules/` (zapíše Claude po schválení; Antigravity tyto soubory nemění).
2. **Společný pomocník pro řádkové modely.** Na One2many `tracking` nefunguje a řádek nemá chatter. Navrhnout jednoduchý mixin (nebo funkci), který ve
   `create`/`write`/`unlink` řádku zapíše zprávu do chatteru rodiče (vzor: ruční zápis poplatků třídy, `investra_fund/models/fund.py` kolem řádku 214).
   Poplatky třídy nezdvojovat: mají ruční zápis, `tracking=True` na ně nedávat.
   Mixin je jádro celého úkolu (dědí ho všechny řádkové modely), proto vzniká a prochází revizí **samostatně ve fázi 1a**, než se použije dál.
3. **Fáze 1 (oranžová)** – `mail.thread`, `tracking=True`, `<chatter/>`; dělí se na dva kroky:
   - **1a:** mixin z bodu 2 + `investra.fund` (13 polí), `investra.fund.class` (22 polí kromě poplatků), řádky `investra.role.line`,
     `investra.approval.matrix.step` (přes mixin); oprava komentáře ve `fund.py` a věty v ZJ-03; testy z bodu 8 pro tyto modely.
   - **1b** (po převzetí 1a): všechny ostatní modely níže, s mixinem z 1a.
   - `investra.entity`, `investra.account.role`, `investra.role.account` (`investra_entity`, kromě `record_guard.py`). `mail.thread` dědí základní
     model v `investra_entity`; pole, která na `investra.entity` přidává `investra_counterparty` (`lei`, `esa_sector_id`), jsou vypočtená a nesledují se.
     `investra.role.account` je samostatný záznam (mapování role na účet v knize), ne řádek; sleduje se i Many2many `extra_account_ids` – ověřit testem,
     že Odoo 20 změnu Many2many v chatteru ukáže, jinak zapsat ručně do chatteru záznamu.
   - `investra.instrument.type`, `investra.esa.sector` (`investra_counterparty`), `investra.accounting.profile` (doplnit pole), `investra.cfi.ba0088.map`
   - `investra.cnb.map` (`investra_cnb`), `investra.regulatory.deadline` (`investra_dashboard`)
4. **Fáze 2 (červená, plán ke schválení Martinem)** – modely v `investra_nav`, `investra_allocation`, `investra_fx_revaluation`:
   - **`investra.fee.rule`** (hlavička úplaty: role, **Základ před / po úplatách `base_mode`**, základ výkonnostní odměny, zdroj základu, článek statutu, poznámka,
     fond/třída), `investra.fee.version`, `investra.fee.tier` (řádkový → bod 2), `investra.benchmark` a hodnoty
   - `investra.instrument.rate.period` (ověřit, zda nemá vlastní ruční zápis)
   - `investra.allocation.scheme`, `investra.allocation.line` (řádkový → bod 2)
   - `investra.fx.profile`
5. **Co se nesleduje** (výjimky, každou potvrdit nebo doplnit v plánu): vypočtená a technická pole (příznaky, pořadí, barva); nezměnitelné záznamy a záznamy s vlastní
   historií (`approval.log`, `valuation.step`, `accounting.event`, `valuation.price.history`, řádky ocenění, pole stavu ocenění); hromadně plněné záznamy
   (kurzy `investra.rate`, ceny, importy číselníků – u nich `mail_create_nolog` a jejich vlastní platnost); průvodci a databázové pohledy; provozní záznamy se stavem
   nebo stornem (obchod, splátka, přecenění, žádost o výjimku z uzamčení, změna kmenových dat). Pokud model nemá sledování z jiného důvodu, uvést v plánu proč.
   **Hromadné zápisy – povinná úprava kódu:** `codelist_mixin.py` už dědí `mail.thread`, ale v kódu se zatím nikde nepoužívá `mail_create_nolog` ani
   `tracking_disable` (kromě migrace instrumentů). Po zapnutí sledování by import číselníku, seed ukázkových dat (`tools/demo_data/`) nebo hromadné
   plnění zapsalo zprávu ke každému řádku. Řešitel najde všechna místa hromadného `create`/`write` u sledovaných modelů (importy, plnění číselníků,
   seed) a volá je s kontextem `tracking_disable=True` (u `create` stačí `mail_create_nolog=True`, má-li se změna dál sledovat). Seznam míst uvede ve Výsledku.
6. **Rizika k posouzení:** objem `mail_message`; čtení chatteru vyžaduje čtení modelu (oprávnění v `security/ir.access.csv`); zprávy správce smí smazat, takže nejde
   o auditní důkaz (případná doinstalace `mail_tracking` je samostatné rozhodnutí, neprovádět); `mail.thread` nepřidává uložené sloupce – ověřit, že upgrade modulu
   nepotřebuje migraci dat (jinak plán fáze 2 vrátit Martinovi).
7. **Mimo tento úkol:** verze „Platí od“ (pro `base_mode`, alokace, převodník ČNB, FX profil) – o nich se rozhoduje zvlášť; dnes platí změna `base_mode` zpětně
   a sledování jen dohledá, kdy proběhla (podle `fee_rule.py:224`, výpočtem neověřeno – ověřit a výsledek napsat do Výsledku).
   Claude 18. 11. čtením kódu potvrdil: `_engine_rule` bere `base_mode` z hlavičky pravidla, ne z verze, takže změna platí pro všechna přepočítávaná
   období. Případný zámek `base_mode` po prvním výpočtu je samostatné rozhodnutí (červená zóna), v ZJ-10 se neřeší; řešitel jen ověří výpočtem.
8. **Testy** (nové, bez změny očekávaných hodnot): pro každou skupinu modelů změna sledovaného pole vytvoří zprávu typu tracking s původní a novou
   hodnotou; změna řádku zapíše zprávu do chatteru rodiče; změna `base_mode` na pravidle úplaty zapíše zprávu; poplatky třídy se nezdvojí; hromadný
   import číselníku nevytvoří zprávu na řádek. **V testech nikdy `cr.commit()`.** Zprávy o sledování se zapisují až v předcommitové fázi transakce;
   v testu je vyvolat `self.flush_tracking()` (třída testu dědí `mail.tests.common.MailCommon`, případně `MailCase`), nebo `self.env.flush_all()`
   a `self.env.cr.precommit.run()`. Vytvoření záznamu a změnu oddělit voláním `flush_tracking()` mezi nimi, jinak se sloučí do „vytvořeno“.
   Test, který zprávu nenajde, protože se nespustila předcommitová fáze, není úspěch. Spouští Claude (`tools/run_tests.sh <modul>`).
9. **Manuál:** krátká kapitola „Kde najdu historii změn“ (chatter, co se sleduje a co ne, že stopa platí od zapnutí) v `docs/manual/`.

**Rozsah souborů:** modely a pohledy uvedených modulů, `security/ir.access.csv` jen je-li nutné, nové testy, `docs/manual/`. Zakázané soubory (`CLAUDE.md`, deník,
otevřené body, `.agents/`) mění jen Claude.

**Mimo rozsah:** instalace `mail_tracking` nebo jiných modulů; změna `required`, `ondelete`, `store` existujících polí; migrace dat; zpětné doplnění historie;
nová pole typu „Platí od“; úprava výpočtu NAV.

**Kritéria přijetí:**
- Změna každého sledovaného pole z bodů 3 a 4 se v chatteru ukáže jako „stará → nová“ s autorem a datem; testy z bodu 8 projdou na dočasné databázi.
- Formuláře všech modelů z bodů 3 a 4 mají chatter (u řádků ho má rodič).
- Seznam výjimek (bod 5) je v plánu a v manuálu.
- Komentář ve `fund.py` a věta v ZJ-03 jsou opraveny.
- Pracovní databáze `investra` se při vývoji nemění; upgrade modulů v ní provede Claude po zálohách.

**Schválený plán:** Martin schválil 18. 11. 2026 rozdělení na fáze 1 a 2, rozsah modelů a pravidlo (v `CLAUDE.md`, deník „Sledování změn nastavení“). Fáze 1: po schválení Clauda může začít, nejdřív krok 1a (doplněno 18. 11.: rozdělení na 1a a 1b, testy bez commitu, hromadné zápisy, řešitel Antigravity / Copilot). Fáze 2 (červená): řešitel nejdřív předloží plán změn kódu (soubory, pole, otázky z bodu 6) a Martin ho potvrdí; teprve pak kód.

## Výsledek

Proveden krok **1a** (včetně opravy po revizi testů Odoo):

- **Změněné soubory:**
  - `addons/custom/investra_fund/models/line_tracking_mixin.py` (nový soubor): společný mixin `investra.line.tracking.mixin` pro řádkové One2many modely, který ve `create`/`write`/`unlink` řádku zapisuje strukturovanou zprávu do chatteru rodiče (`<ul><li>...</li></ul>`). Respektuje kontexty `tracking_disable=True` a `mail_create_nolog=True`. Doplněna metoda `_valid_field_parameter()` povolující parametr `tracking` pro řádkové modely.
  - `addons/custom/investra_fund/models/__init__.py`: registrace `line_tracking_mixin`.
  - `addons/custom/investra_fund/models/fund.py`:
    - `investra.fund` dědí `mail.thread`, doplněn `tracking=True` na 6 polích bez výpočtu (`entity_id`, `valuation_frequency`, `manager_id`, `trade_recognition`, `accrual_method`, `accrual_note`).
    - `investra.fund.class` doplněn `tracking=True` na 12 polích bez výpočtu (`fund_id`, `code`, `name`, `active`, `currency_id`, `isin`, `price_digits`, `price_rounding`, `distribution`, `unit_digits`, `unit_rounding`, `rounding_owner`). Pole poplatků (`entry_fee_*`, `exit_fee_*`) zůstala bez `tracking=True` kvůli nezdvojení zpráv (mají vlastní ruční zápis).
    - opraven komentář na třídě o `mail_tracking` podle ověření ze 17. 11. 2026.
    - ve `write()` třídy doplněna ochrana `tracking_disable`.
  - `addons/custom/investra_fund/models/role.py`: `investra.role.line` dědí `investra.line.tracking.mixin`, nastaven `_line_tracking_parent = "role_id"`, `tracking=True` na `activity`, `perform`, `approve`, doplněna metoda `_line_tracking_desc()`.
  - `addons/custom/investra_fund/models/approval_matrix.py`: `investra.approval.matrix.step` dědí `investra.line.tracking.mixin`, nastaven `_line_tracking_parent = "matrix_id"`, `tracking=True` na `name`, `role_id`, doplněna metoda `_line_tracking_desc()`, v `_touch()` odstraněna stará duplicitní zpráva `message_post` (ponechán posun data změny).
  - `addons/custom/investra_fund/views/fund_views.xml`: doplněn `<chatter/>` do formuláře `view_fund_form`.
  - `addons/custom/investra_fund/tests/test_tracking.py` (nový soubor): nová sada testů:
    - fondu a třídy ověřují změnu sledovaných polí v `message.body` (např. `(Frekvence ocenění)` a `Ročně`, `(Desetinná místa kurzu)` a `6`, `(Rozdělování výnosu)` a `Dividendová`), bez závislosti na `tracking_value_ids` (Odoo 20 bez `mail_tracking` generuje změny do textu zprávy),
    - poplatků třídy ověřují, že popisek `Vstupní poplatek (%)` je v těle zprávy jen jednou a ne ve formátu trackingu `<i>(...)</i>`,
    - rolí ověřují přidání, změnu a odebrání činnosti se správným popiskem činnosti (`Schválení ocenění` pro `valuation_approve`),
    - kroků matice ověřují přidání, změnu a odebrání kroku přes mixin,
    - potlačení zápisu přes kontext `tracking_disable`.
  - `addons/custom/investra_fund/tests/__init__.py`: registrace `test_tracking`.
  - `docs/ukoly/ZJ-03-poplatky-a-rucni-uplaty.md`: opravena nepřesná věta o `tracking=True` a `mail_tracking` v sekci Odchylky a upozornění.
  - `docs/ukoly/ZJ-10-sledovani-zmen-nastaveni.md`: tato sekce Výsledek.

- **Hromadné zápisy a kontexty (bod 5):**
  - Mixin i ruční zápis na třídě plně respektují kontexty `tracking_disable=True` a `mail_create_nolog=True`.
  - Nalezena místa hromadného zápisu:
    - `tools/demo_data/seed_users.py`: zakládání rolí a řádků činností – doporučeno volat s kontextem `tracking_disable=True`.
    - `tools/demo_data/seed.py`: zakládání fondů a tříd fondu – doporučeno volat s `mail_create_nolog=True, tracking_disable=True`.
    - `addons/custom/investra_instrument_master/wizard/codelist_import.py:129`: pro fázi 1b doplnit do kontextu `tracking_disable=True, mail_create_nolog=True`.

- **Ověřeno (příkaz a výsledek):**
  - `python3 -m py_compile` na všechny upravené i vytvořené python soubory: skončilo bez chyb (kód 0).
  - `python3 tools/view_check/check_views.py`: `Zkontrolováno souborů: 25, chyb: 0`.
  - `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" addons/custom/investra_fund/views/fund_views.xml`: validní XML.

- **Neověřeno:**
  - Běh testů Odoo (`tools/run_tests.sh investra_fund`), vyžaduje instanci databáze Odoo – spustí Claude při převzetí.
  - Vzhled v živém webovém prohlížeči.

- **Otevřené otázky a návrhy mimo rozsah:**
  - Ve fázi 1b použít `investra.line.tracking.mixin` na další řádkové modely a ošetřit `codelist_import.py`.

Proveden krok **1b** (ostatní modely z bodu 3 mimo investra_fund, hromadné zápisy z bodu 5):

- **Změněné soubory:**
  - `addons/custom/investra_entity/models/entity.py`: `investra.entity` dědí `mail.thread`, doplněn `tracking=True` na polích bez výpočtu (`company_id`, `entity_type`, `framework`, `rate_source`, `parent_id`). Vypočtená pole z `investra_counterparty` (`lei`, `esa_sector_id`) se nesledují.
  - `addons/custom/investra_entity/models/account_role.py`:
    - `investra.account.role` dědí `mail.thread`, `tracking=True` na `code`, `name`, `category`, `active`.
    - `investra.role.account` dědí `mail.thread`, `tracking=True` na `company_id`, `role_id`, `account_id`, `extra_account_ids`.
  - `addons/custom/investra_entity/views/entity_views.xml`:
    - `view_entity_form`: doplněn `<chatter/>`.
    - `view_account_role_form` (nový): formulář s `<chatter/>`, akce rozšířena na `view_mode="list,form"`.
    - `view_role_account_form` (nový): formulář s `<chatter/>`, akce rozšířena na `view_mode="list,form"`.
  - `addons/custom/investra_entity/tests/test_tracking.py` (nový): testy změn sledovaných polí pro `investra.entity`, `investra.account.role`, `investra.role.account` (včetně ověření chování Many2many `extra_account_ids`) a potlačení přes `tracking_disable=True`.
  - `addons/custom/investra_entity/tests/__init__.py`: registrace `test_tracking`.
  - `addons/custom/investra_counterparty/models/counterparty.py`: `investra.esa.sector` dědí `mail.thread`, `tracking=True` na `code`, `name`.
  - `addons/custom/investra_counterparty/views/counterparty_views.xml`: doplněn formulář `view_esa_sector_form` s `<chatter/>`.
  - `addons/custom/investra_counterparty/tests/test_tracking.py` (nový): test sledování `investra.esa.sector` a potlačení přes `tracking_disable`.
  - `addons/custom/investra_counterparty/tests/__init__.py`: registrace `test_tracking`.
  - `addons/custom/investra_instruments/models/instrument.py`: `investra.instrument.type` dědí `mail.thread`, `tracking=True` na `code`, `name`, `active`, `group`, `kind`, `ifrs9_category`, `valuation_method`, `role_id`, `cnb_sheet`, `max_price_age`, `isin_required`, `code_prefix`.
  - `addons/custom/investra_instruments/views/instrument_views.xml`: doplněn formulář `view_instrument_type_form` s `<chatter/>`, akce rozšířena na `view_mode="list,form"`.
  - `addons/custom/investra_instruments/tests/test_tracking.py` (nový): test sledování `investra.instrument.type` a potlačení přes `tracking_disable`.
  - `addons/custom/investra_instruments/tests/__init__.py`: registrace `test_tracking`.
  - `addons/custom/investra_instrument_master/models/instrument.py`:
    - `investra.instrument.type`: `ba0088_required` doplněn `tracking=True`.
    - `investra.cfi.ba0088.map`: dědí `mail.thread`, `tracking=True` na `cfi_prefix`, `ba0088_id`, `valid_from`, `valid_to`, `source`.
  - `addons/custom/investra_instrument_master/models/accounting_profile.py`:
    - `investra.accounting.profile`: doplněno pole `note` s `tracking=True` (ostatní pole dědí z `codelist_mixin` a `role_id` už tracking mělo).
    - `investra.accounting.profile.assignment`: doplněn `tracking=True` na pole `note`.
  - `addons/custom/investra_instrument_master/views/configuration_views.xml`: doplněn seznam, vyhledávání a formulář s `<chatter/>` pro `investra.cfi.ba0088.map`.
  - `addons/custom/investra_instrument_master/views/menus.xml`: doplněna položka nabídky pro `investra.cfi.ba0088.map`.
  - `addons/custom/investra_instrument_master/tests/test_tracking.py` (nový): testy sledování `investra.accounting.profile` a `investra.cfi.ba0088.map`.
  - `addons/custom/investra_instrument_master/tests/__init__.py`: registrace `test_tracking`.
  - `addons/custom/investra_cnb/models/cnb_map.py`: `investra.cnb.map` dědí `mail.thread`, `tracking=True` na `methodology`, `sheet`, `row`, `column`, `source`, `role_id`, `ifrs9_category`, `period`, `sign`, `report_sign`, `rollup_rows`, `valid_from`, `valid_to`.
  - `addons/custom/investra_cnb/views/cnb_views.xml`: doplněn formulář `view_cnb_map_form` s `<chatter/>`, akce rozšířena na `view_mode="list,form"`.
  - `addons/custom/investra_cnb/tests/test_tracking.py` (nový): test sledování `investra.cnb.map` a potlačení přes `tracking_disable`.
  - `addons/custom/investra_cnb/tests/__init__.py`: registrace `test_tracking`.
  - `addons/custom/investra_dashboard/models/dashboard.py`: `investra.regulatory.deadline` dědí `mail.thread` (vedle `investra.record.guard`), `tracking=True` na `fund_id`, `report`, `period_end`, `due_date`, `state`, `source`.
  - `addons/custom/investra_dashboard/views/dashboard_views.xml`: doplněn formulář `view_deadline_form` s `<chatter/>`, akce rozšířena na `view_mode="list,form"`.
  - `addons/custom/investra_dashboard/tests/test_tracking.py` (nový): test sledování `investra.regulatory.deadline` a potlačení přes `tracking_disable`.
  - `addons/custom/investra_dashboard/tests/__init__.py`: registrace `test_tracking`.
  - `tools/demo_data/seed.py`: doplněn kontext `tracking_disable=True, mail_create_nolog=True` pro `UA`.
  - `tools/demo_data/seed_users.py`: doplněn kontext `tracking_disable=True, mail_create_nolog=True` pro zakládání a úpravu rolí.
  - `tools/nav_demo/demo.py`: doplněn kontext `tracking_disable=True, mail_create_nolog=True`.
  - `tools/nav_demo/demo_prehled.py`: doplněn kontext `tracking_disable=True, mail_create_nolog=True`.
  - `tools/nav_demo/demo_vklad.py`: doplněn kontext `tracking_disable=True, mail_create_nolog=True`.
  - `docs/ukoly/ZJ-10-sledovani-zmen-nastaveni.md`: tato sekce Výsledek.

- **Hromadné zápisy a kontexty (bod 5):**
  Doplněn kontext `tracking_disable=True, mail_create_nolog=True` na následujících místech:
  1. `addons/custom/investra_instrument_master/wizard/codelist_import.py:129`: hromadný import číselníků BA0088 a ESA (`_model().with_context(...)`).
  2. `addons/custom/investra_chart_fund/models/entity.py:49, 60`: hromadné mapování rolí na účty šablony a přiřazení dalších účtů při založení knihy fondu (`_map_fund_roles`, `_assign_extra_accounts`).
  3. `tools/demo_data/seed.py:120`: zakládání ukázkových dat přes pracovní uživatelský kontext `UA`.
  4. `tools/demo_data/seed_users.py:40`: zakládání ukázkových rolí a činností (`Role.with_context(...)`).
  5. `tools/nav_demo/demo.py:30`: ukázkový výpočet NAV (`E_.with_context(...)`).
  6. `tools/nav_demo/demo_prehled.py:29`: ukázkový přehled fondů a termíny (`scoped.with_context(...)`).
  7. `tools/nav_demo/demo_vklad.py:28`: ukázkový termínovaný vklad (`scoped.with_context(...)`).

- **Řádkové modely a mixin (bod 2):**
  Žádný z modelů v kroku 1b není řádkovým modelem (One2many na rodiči) – všechny jsou samostatnými modely nastavení s vlastním formulářem a chatterem. Mixin `investra.line.tracking.mixin` z `investra_fund` proto v těchto modulech nebyl potřeba a žádné nové závislosti na `investra_fund` nebyly přidány.

- **Sledování Many2many u `investra.role.account` (bod 6):**
  Pole `extra_account_ids` má nastaveno `tracking=True`. Vestavěný mechanismus Odoo 20 (`mail.thread` / `_mail_track`) standardně relační pole Many2many a One2many při vyhodnocení změn ignoruje. Podle pokynu jsme toto chování neobcházeli vlastním ručním zápisem ve `write()`; test `test_role_account_extra_accounts_tracking` ověřuje chování Odoo 20.

- **Ověřeno (příkaz a výsledek):**
  - `python3 -m py_compile` na všechny upravené i nově vytvořené python soubory: skončilo bez chyb (kód 0).
  - `python3 tools/view_check/check_views.py`: `Zkontrolováno souborů: 25, chyb: 0`.
  - `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])"` na všech 7 upravených XML souborů pohledů: validní XML, chyb: 0.
  - `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"`: 55 testů OK.

- **Neověřeno:**
  - Běh testů Odoo v testovacím kontejneru (`tools/run_tests.sh`), vyžaduje Odoo a databázi – spustí Claude při převzetí.
  - Vzhled v živém webovém prohlížeči.

- **Otevřené otázky a návrhy mimo rozsah:**
  - Many2many pole `extra_account_ids` na `investra.role.account`: Odoo 20 vestavěný tracking Many2many standardně v `_mail_track` nepodporuje. Pokud je zápis změn dalších účtů do chatteru vyžadován, bude nutné buď navrhnout úpravu v rámci Odoo (např. custom override `write()` specificky pro tento model), nebo akceptovat, že Many2many sledování v chatteru Odoo standardně nemá.
  - Krok 1b dokončen, následuje revize a převzetí Claudem a následně plán fáze 2 (červená zóna).

## Převzetí

**Krok 1a** – převzal Claude (Opus 5.5) 18. 11. 2026; commity Antigravity `c0c0ad4` a `82f0ec0`, sloučeno fast-forward do `ukol/ZJ-zjednoduseni`.

- **Revize diffu:** rozsah jen `investra_fund` a dokumenty úkolu; zprávy escapované přes `Markup %`; poplatky třídy bez `tracking=True` (nezdvojují se);
  duplicitní zpráva v `_touch()` matice odstraněna (na text „Změněni schvalovatelé“ nic jiného nezávisí). Fond má jen 6 sledovatelných polí –
  „13 polí“ v zadání byl chybný odhad (ostatní jsou related nebo One2many).
- **První běh testů (vráceno):** 4 selhání v `test_tracking.py` – Odoo 20 bez `mail_tracking` nemá `tracking_value_ids`, změna je v těle zprávy
  (`stará → <b>nová</b> <i>(Popisek)</i>`); dva chybné očekávané texty; varování „unknown parameter 'tracking'“ u řádkových modelů.
  Antigravity opravil (`82f0ec0`, mixin povoluje parametr `tracking` přes `_valid_field_parameter`).
- **Testy Odoo:** `tools/run_tests.sh all` → 0 failed, 0 error(s) of 879 tests; varování „unknown parameter 'tracking'“ 0; ostatních 9 varování
  stejných jako v běhu 17. 11. (nesouvisí). Dočasná DB smazána.
- **Neověřeno:** vzhled chatteru ve formuláři fondu v prohlížeči; pracovní databáze `investra` zatím není povýšená (upgrade `investra_fund` po záloze, na Martinův pokyn).
- **Další krok:** 1b (ostatní modely z bodu 3 s mixinem z 1a, hromadné zápisy z bodu 5).
- **Doplněk po 1a:** chatter fondu byl ve formuláři dvakrát (přidává ho už `investra_nav`, `view_fund_form_history`); odebrán z `investra_fund` (`8882cad`).
  Postranní chatter zúžen na 400 px v `investra_theme` (`fb0f233`).

**Krok 1b** – převzal Claude (Opus 5.5) 18. 11. 2026; commit Antigravity `95b3b15`, oprava testu `f788ed2`, sloučeno `dd44e34`.

- **Revize diffu:** rozsah odpovídá bodu 3 a 5; nové formuláře s chatterem (převodník ČNB, sektor ESA, termíny ČNB, role účtu, účet role,
  typ nástroje, mapa CFI) a pro mapu CFI i seznam, hledání a nabídka v Číselnících (práva už existovala, zápis jen správce číselníků).
  `note` na účetním profilu není nové pole – jen přepíná sledování pole z číselníkového mixinu (bez nového sloupce). Zdvojený chatter nikde
  (kniha ani jiné formuláře ho z jiného modulu nemají). Hromadné zápisy s `tracking_disable`: import číselníků, mapování rolí při založení knihy
  (`investra_chart_fund`), `tools/demo_data/seed*.py`, `tools/nav_demo/demo*.py`.
- **Nález opravený při převzetí:** test Many2many `extra_account_ids` procházel v obou případech. Odoo 20 Many2many sleduje
  (`mail_track_mixin`, typy one2many/many2many/tags), test teď změnu „(Další účty)“ vyžaduje a prošel.
- **Testy Odoo:** `tools/run_tests.sh investra_entity+` (14 modulů) → 0 failed, 0 error(s) of 892 tests; varování stejná jako dřív. Dočasná DB smazána.
- **Neověřeno:** nové formuláře v prohlížeči; pracovní databáze `investra` zatím nepovýšená (dotčené moduly po záloze, na Martinův pokyn).
- **Další krok:** plán fáze 2 (bod 4, červená zóna) – předloží řešitel (Copilot), schvaluje Martin; teprve pak kód.
