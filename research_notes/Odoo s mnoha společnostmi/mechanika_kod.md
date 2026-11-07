# Mechanika multi-company v Odoo 20 Community: co stojí každá další res.company

Zdroj: kód obrazu `odoo:20.0-20261102` (verze `20.0.post20261102`), přečtený v běžícím kontejneru. Cesty bez předpony jsou relativní k `/usr/lib/python3/dist-packages/odoo/`; `addons/custom/...` a `tools/...` jsou v repozitáři. Odkazy mají tvar `soubor:řádek`.

Značení:
- **Cited Findings** = přečteno v kódu, nebo změřeno SELECTem.
- **Inferences** = můj závěr z kódu, za běhu neověřený.
- Počty z `investra_test` jsou **testovací, fiktivní data** (7 společností, session s `default_transaction_read_only=on`). Žádný výkon jsem neměřil a Odoo jsem nespouštěl.

## Co vznikne se společností a osnovou; lze sdílet account.account?

### Takeaway
Každá hlavní společnost dostává vlastní kopii osnovy, deníků, daní a fiskálních pozic; loader nic nesdílí. Sdílet mezi hlavními společnostmi jde technicky jen `account.account` (pole `company_ids`, kód v `code_store`), a to ručně a bez účtů banky a pokladny. Deníky, daně a fiskální pozice mají skalární `company_id` a sdílejí se jen dolů po stromu `parent_id`.

### Cited Findings

Vytvoření `res.company`:
- Partner s `company_id=False`, tedy sdílený (`addons/base/models/res_company.py:351-375`).
- Společnost se přidá jen tvůrci a superuserovi, ostatním uživatelům ne (`addons/base/models/res_company.py:385-389`).
- Aktivuje se měna společnosti (`:392`), spustí se `install_l10n_modules()` a `_init_company_defaults()` (`:394-398`).
- Účetní vrstva přidá `ir.sequence` „Group Payments“, `no_gap` s date range (`addons/account/models/company.py:611-628, 642`).
- Má-li kořen šablonu, načte se při precommitu i do nové společnosti (`addons/account/models/company.py:634-641`).
- Modul payment duplikuje *nainstalované* poskytovatele z firmy aktuálního uživatele (`addons/payment/models/res_company.py:44-56`).
- Vzniká kalendář (`addons/resource/models/res_company.py:30-40`).

Načtení osnovy (`_load`, `addons/account/models/chart_template.py:206-283`):
- Běží s `allowed_company_ids=[company.id]` (`:232-238`).
- Pokud společnost nemá účetní záznamy a mění šablonu, **smaže s `force_delete` dosavadní záznamy šablony** (`:244-255`).
- Každý záznam dostane xmlid `account.{company.id}_{xmlid}` s `noupdate=True` (`:746-753`, `:1261-1265`). Osnova se tedy pro každou hlavní společnost duplikuje.
- `_pre_load_data` přepíše měnu společnosti měnou fiskální země (`:530-535, 545`). Proto `create_book` měnu nastavuje znovu (`addons/custom/investra_entity/models/entity.py:82-86`).
- Základní šablona vytváří 7 deníků: sale, purchase, general, exch, caba, bank, inventory_valuation (`:1170-1220`).
- Pomocné účty (suspense, kurzové rozdíly, převod, outstanding) vznikají jen u kořene (`:955-972`).
- `_post_load_data` nastaví výchozí daně a prohledá sdílené produkty (`:785-815`). Založí i onboarding (`:830`, `addons/account/models/company.py:607-609`).

Měření, `investra_test`, testovací data, na jednu společnost (šablona `investra_fund`, id 3363):

| Objekt | Počet | Poznámka |
|---|---|---|
| `account.account` | 47 | starší společnosti 244 a 410 mají 37 |
| `account.journal` | 7 | |
| `account.reconcile.model` | 2 | |
| `account.tax`, `account.fiscal.position` | 0 | |
| `ir.default` | 7 | např. `property_account_payable_id`, `property_account_receivable_id` |
| `ir.sequence` | 1 | |
| `onboarding.progress` | 2 | |
| `product.pricelist` | 1 | |
| `resource.calendar` | 1 | společnost 2 bez osnovy ho nemá |
| `ir.model.data` | 56 | = 47 + 7 + 2 |
| `res.partner` | 1 | |

- `mail.alias` má celkem 18 řádků: 12 `account.move` a 6 `account.journal`, tj. 3 na každou ze 6 společností s osnovou (rozpočet je můj výpočet, po společnostech jsem to nerozlišil).
- `payment.provider`: 25 řádků, všechny ve společnosti 1. Do nových se nekopírují, dokud nejsou nainstalované.
- `generic_coa` (společnost 1): 50 účtů, 4 daně, 2 skupiny daní, 16 repartition lines, 2 fiskální pozice.

Pro srovnání `l10n_cz`, řádky CSV včetně hlavičky: účty 323, daně 149 (nejde o počet daní, CSV obsahuje i rozpad repartition), fiskální pozice 9, skupiny daní 5 (`addons/l10n_cz/data/template/`).

Sdílení účtu:
- `company_ids` je Many2many, výchozí aktivní společnost (`addons/account/models/account_account.py:120-121`).
- Banka a pokladna (`asset_cash`) sdílet nejdou (`:258-259`).
- Odebrat společnost nelze, má-li na účtu položky (`:261-266`).
- Kód je `code_store`, `company_dependent`, klíčovaný **ID kořenové společnosti** (`:47, :314-327`). Testovací řádek: `{"3363": "221100"}`.
- `account.code.mapping` je jen UI, neukládá se (`addons/account/models/account_code_mapping.py:11-18`).
- Jedinečnost kódu se kontroluje po společnostech (`addons/account/models/account_account.py:1111-1135`).
- Kontrola firmy účtu je `company_ids in parents` (`:32`, `orm/models.py:181-196`). Pravidlo přístupu: `company_ids parent_of company_ids` (`addons/account/security/ir.access.csv:58`).
- V testu má všech 265 účtů právě jednu společnost. Loader sdílení nepoužil.

Deníky, daně, fiskální pozice a reconcile modely mají pravidlo `company_id parent_of company_ids` (`addons/account/security/ir.access.csv:18, 49, 61, 73`).

### Inferences
- Jedna společnost s `investra_fund` je řádově 130–140 řádků konfigurace. S plným `cz` by to bylo řádově 1 000 a více (účty + daně + repartition). Pro 100 fondů to objemem není problém; náklad je v údržbě konfigurace, ne v databázi.
- Sdílený účet znamená sdílený název, typ, `reconcile` a tagy napříč fondy; kód může být různý jen po kořenech. Změna jednoho atributu tedy zasáhne všechny fondy. Úspora je malá, riziko pro historii vyšší.
- Změna osnovy po založení fondů je kvůli `noupdate=True` hromadná práce po společnostech, ne centrální úprava šablony.

### Gaps
- **Riziko k ověření v DEV:** při `create` se zemí CZ a bez `chart_template` se registruje precommit `try_loading(_guess_chart_template(CZ))` (`addons/account/models/company.py:1119-1134`). `create_book` načítá `investra_fund` až po tomto kroku (`addons/custom/investra_entity/models/entity.py:77-82`). `_guess_chart_template` bere první šablonu dané země, pořadí mezi `cz` a `investra_fund` závisí na pořadí modulů (`chart_template.py:149-167`, šablona deklaruje `country: cz`).
  - Testovací data přepsání neukazují: 5 CZ společností má stále `investra_fund`; `tools/nav_demo/demo.py` je zakládá přes `odoo shell` s `commit` (`:3, :14, :86`).
  - Proč se to nepřepsalo, jsem za běhu nepotvrdil. Pokud by odhad vrátil `cz`, `_load` by mohl osnovu nahradit, u společnosti bez položek včetně mazání.
- Průvodce `account_merge_wizard.py` jsem nečetl.
- Přesný počet daní a účtů v plném `cz` jsem nezměřil, nebyla v DB žádná společnost s touto šablonou.

## Jak fungují přístupová pravidla a cids

### Takeaway
V Odoo 20 už `ir.rule` není: nahradil ho `ir.access` (`addons/base/models/ir_access.py`; `ir_rule.py` v `addons/base/models` neexistuje). Podmínka s `company_ids` se vyhodnocuje na seznam povolených firem a výsledný SQL filtr roste lineárně s počtem **vybraných** firem, počet podmínek zůstává stejný. V kódu klienta jsem tvrdý limit na počet firem nenašel.

### Cited Findings
- `ir.access` spojuje práva a domény: záznam se skupinou je *permission*, bez skupiny *restriction* (`addons/base/models/ir_access.py:83-87, 128-131`).
- Výsledek: `OR(permissions) & AND(restrictions)` (`orm/models.py:3635-3647`).
- `_get_all_access` je v cache `stable` a předvyhodnotí jen literální domény (`addons/base/models/ir_access.py:282-306`). Domény s `company_ids` se vyhodnotí přes `safe_eval` s `_eval_context` (`:312-324`, `orm/models.py:3638-3641`).
- `_access_domain` je `ormcache` s klíčem `(operation, uid, tuple(allowed_company_ids))` (`orm/models.py:3602`, `orm/environments.py:208-210`, `addons/base/models/ir_access.py:308-310`). Cache `default` má 8192 položek (`orm/registry.py:53-54`).
- Pořadí firem je součástí klíče a `with_company` pořadí mění (`orm/models.py:5493-5500`).
- Read cache je `transaction.access_read[(uid, allowed_company_ids)]` (`orm/environments.py:212-220`).
- `parent_of` se rozbalí z `parent_path` na množinu ID (`orm/domains.py:1898-1910`).
- Typické domény: `account.move` a `account.move.line` `company_id in company_ids`, účet `company_ids parent_of company_ids` (`addons/account/security/ir.access.csv:33, 37, 58`).
- `env.companies` kontroluje, zda je kontext podmnožinou `_get_company_ids`, jinak `AccessError`; bez kontextu vrací všechny firmy uživatele (`orm/environments.py:286-303`). `_get_company_ids` je v ormcache podle uživatele (`addons/base/models/res_users.py:821-825`).
- Cookie `cids`: ID spojená `-`, zapisuje `user.js` (`addons/web/static/src/core/user.js:16-22, 79`), platnost 1 rok (`addons/web/static/src/core/browser/cookie.js:8`), při odhlášení se maže (`addons/web/models/ir_http.py:70`).
- Neplatný seznam spadne na výchozí firmu (`user.js:64-68`).
- Každé RPC nese `allowed_company_ids` v kontextu (`user.js:80`).
- `session_info` při načtení posílá všechny povolené firmy: id, name, sequence, child_ids, parent_id, currency_id (`addons/web/models/ir_http.py:158-174`). Předci bez přístupu jdou zvlášť (`:175-183`).
- Přepínač zobrazí vyhledávání nad 9 firem (`addons/web/static/src/webclient/switch_company_menu/switch_company_menu.js:249-251`), filtr a „vybrat vše“ (`:307-317, :344`).
- Skupinu `base.group_multi_company` Odoo přidává a odebírá podle počtu firem uživatele (`addons/base/models/res_users.py:1441-1449`).

### Inferences
- Pro 100 firem se SQL filtr `company_id IN (…100 čísel…)` neblíží žádné hranici. Problém nečekám ve velikosti rule, ale v tom, co se s tolika vybranými firmami zobrazí.
- Cookie: 100 čtyřmístných ID je asi 500 bajtů, tedy pod běžným limitem prohlížeče kolem 4 KB. Hranice by byla řádově přes 600 firem vybraných najednou. Limit 4 KB není z kódu Odoo.
- Smyčka `with_company` přes 100 fondů se všemi vybranými vytvoří pro každý model a operaci jiný klíč `_access_domain`. Při 8192 položkách LRU to může vytlačovat jiné cache; u sudo se domény nepoužijí, takže dopad je jen u běžného uživatele.
- `res.company` je `CachedModel` (`addons/base/models/res_company.py:60, 68`, `orm/models_cached.py:10-31`) a invalidace `stable` zasahuje i `default` (`orm/registry.py:69`). Hromadné zakládání nebo přejmenování firem tak pravděpodobně vyčistí cache ve workerech. Průběh jsem nečetl do konce.

### Gaps
- Skutečné SQL a plány dotazů se 100 firmami jsem neměřil; DB má 7 firem. Nutný zátěžový test v DEV s reálnými objemy.
- Generovanou podobu SQL pro `company_ids parent_of` (Many2many) jsem neviděl za běhu.
- Chování přepínače se 100 firmami (výkon, stromové zobrazení) jsem neověřil v prohlížeči.

## Které cron úlohy a dávky běží přes všechny společnosti

### Takeaway
Community nemá cron pro kurzy, uzávěrku daní ani zámky. Jediný cron s přímou smyčkou přes `res.company` je uzávěrka zásob, a ta je ve výchozím stavu prázdná. Skutečně s počtem firem rostou dávky mimo cron: instalace a upgrade modulů, překlady, synchronizace kontaktů.

### Cited Findings

Crony (24 aktivních v `investra_test`):

| Oblast | Stav | Odkaz |
|---|---|---|
| Kurzy | Modul `currency_rate_live` v obrazu není (`ls addons`). Vlastní `_cron_fetch` je neaktivní. | `addons/custom/investra_rates/data/cron.xml:3-10` |
| Zápis kurzů Investra | ČNB: jeden společný řádek (`company_id=False`). ECB: smyčka přes všechny knihy se zdrojem ECB včetně EUR = 1. | `addons/custom/investra_rates/models/rate.py:162-171` |
| Zámky | Žádný cron. Hodnoty jsou na firmě, kontrola při účtování. | `addons/account/models/account_move.py:3897, 5961`, `addons/account/models/company.py:751-761, 786-793` |
| Opakované doklady | `_autopost_draft_entries`: jeden dotaz přes všechny firmy, dávka 100, bez smyčky po firmách. | `addons/account/models/account_move.py:7209-7242` |
| Odesílání faktur | Globální fronta, 10 úloh na běh. | `addons/account/models/account_move.py:7245-7265` |
| Uzávěrka zásob | **Smyčka přes firmy**, jen `inventory_period` daily/monthly. Výchozí je `manual`, v testu 7 ze 7. | `addons/account/models/company.py:358-366, 1456-1465` |
| Uzávěrka DPH | `account.return` v `addons/account/models` není, zůstala jen trasa `account_return_dashboard`. | `addons/account/models/company.py:605` |
| Digest | Smyčka po digestech a uživatelích, ne po firmách. V testu 1 digest. | `addons/digest/models/digest.py:153-170, 262-268` |

Dávky mimo cron, O(počet firem):
- Instalace modulu se šablonovými daty projde všechny firmy s osnovou (`addons/account/models/ir_module.py:72-87`).
- `_load_pre_defined_data` totéž (`addons/account/models/chart_template.py:1394-1411`).
- `_load_translations` bez zadaných firem načítá šablonu pro každou firmu (`chart_template.py:1548-1560`).
- Migrace `l10n_cz` jde přes firmy se šablonou `cz` (`addons/l10n_cz/migrations/1.1/end-migrate_update_taxes.py:7`).
- `_company_dependent_commercial_sync`: zápis do **každé** firmy, když se u kontaktu spouští synchronizace s nadřazenou společností (`addons/base/models/res_partner.py:811-834`).
- Nový produkt bez firmy: `_force_default_tax` do všech ostatních firem (`addons/account/models/product.py:298-304`).
- Instalace poskytovatele plateb: kopie do každé kořenové firmy (`addons/payment/models/payment_provider.py:1163-1170`).
- Ceníky: `addons/product/models/res_company.py:15-34`.

### Inferences
- Modul Investra bez šablonových dat upgrade po firmách nezatíží; změna šablony nebo překladů už ano. Délka okna upgradu poroste se 100 firmami, odhad bez měření dát nejde.
- Čistě ploché zapisování kurzů ECB: řádků za den přibývá úměrně `počet ECB knih × (počet měn + EUR)`. ČNB takto neroste. To je vlastní kód, ne Odoo.
- Zámek období pro 100 fondů je 100 zápisů (a kontrol v `_validate_locks`); hromadnou akci je třeba napsat. Community ji nedává.
- Crony běží jako superuser přes všechny firmy; jedna chybná firma v dávce může zdržet ostatní, ale `_autopost_draft_entries` chyby izoluje po dokladech (`account_move.py:7230-7242`).

### Gaps
- Crony Peppol (aktivní v testu, modul `account_peppol`) jsem detailně nečetl; podle zběžného grepu jdou po proxy uživatelích, ne po firmách.
- Crony v modulech, které v `investra_test` nejsou nainstalované, jsem neprocházel.
- Volající `_load_translations` (kdy přesně běží) jsem nečetl.

## Co je sdílené a co po společnostech; company_dependent

### Takeaway
Sdílené je to, co má prázdné `company_id` nebo žádné: měny, partneři bez firmy, produkty bez firmy, uživatelé a kurzy s `company_id = NULL`. Hodnoty závislé na firmě leží v JSONB sloupci téhož záznamu; fallback je v `ir.default` per firma. Fond jako hlavní společnost proto kurzy sdílí jen přes globální řádky.

### Cited Findings

| Model | Vazba na firmu | Viditelnost | Odkaz |
|---|---|---|---|
| `res.currency` | žádná; `name` unikátní, `active` globální | vše | `addons/base/models/res_currency.py:51, 77, 84-86` |
| `res.currency.rate` | `company_id` volitelné, jen kořen; unikát `(currency, company, name) NULLS NOT DISTINCT` | `company parent_of` nebo `False` | `addons/base/models/res_currency.py:426-436, 534-538`, `addons/base/security/ir.access.csv:49` |
| `res.partner` | `company_id` volitelné | `partner_share=False` nebo firma `parent_of` nebo `False` | `addons/base/models/res_partner.py:375`, `addons/base/security/ir.access.csv:59` |
| `res.partner.bank` | volitelné | stejně | `addons/base/security/ir.access.csv:63` |
| `product.template` | volitelné | `parent_of` nebo `False` | `addons/product/models/product_template.py:166-167`, `addons/product/security/ir.access.csv:9` |
| `res.users` | `company_id` + `company_ids` | interní uživatelé všichni | `addons/base/models/res_users.py:233, 237`, `addons/base/security/ir.access.csv:73` |
| `account.account` | `company_ids` | `parent_of` | viz první část |
| `account.journal`, `account.tax` | `company_id` | `parent_of` | `addons/account/security/ir.access.csv:49, 61` |

- `company_dependent`: JSONB sloupec na tabulce modelu, klíč = ID firmy (`orm/fields.py:132-137, 891`). Nesmí být `required` ani přeložitelné (`:501-507`).
- SQL čte `COALESCE(sloupec->'firma', to_jsonb(fallback))` (`orm/fields.py:1378-1400`). Fallback bere `ir.default` pro aktuální firmu (`:914-921`), s ormcache podle firmy (`addons/base/models/ir_default.py:171`).
- Takové pole má partner: `property_account_payable_id`, `property_account_receivable_id`, `property_account_position_id`, platební podmínky (`addons/account/models/partner.py:581-601`). A produkt: příjmové a nákladové účty (`addons/account/models/product.py:16, 23, 92, 97`).
- Výběr kurzu: `_get_rates` vezme kořen (`addons/base/models/res_currency.py:173`), hledá `company_id in (False, root)` s řazením `company_id.id, name DESC`, limit 1 (`:185-187`). Cache je `(root.id, date)` v kurzoru (`:174-177`).
- Testovací data: 20 z 22 partnerů má `company_id` NULL; `res_currency_rate` má 0 řádků.

### Inferences
- Řazení znamená, že **jakýkoli firemní kurz před datem přebije novější globální kurz** (za předpokladu, že NULL je v PostgreSQL při ASC poslední). Dokumentace vlastního kódu `rate.py` uvádí, že firemní kurz má přednost; starý firemní řádek by mohl překrýt nový společný. U ECB knih to platí, jen když ECB zápisy přestanou chodit. Ověřit testem.
- Sdílený partner stojí po firmách jen vyplněné hodnoty v JSONB; chybějící hodnota jde přes `ir.default`, takže nový fond nevyžaduje změnu partnerů.
- Kurzy se ČNB řádkem sdílí napříč fondy bez ohledu na počet; cache je ale po kořenech, takže smyčka přes 100 fondů udělá až 100 dotazů za datum v transakci. Dotaz je malý, důležité to bude až při dávkách.
- Sdílené číselníky (partneři, instrumenty) je nutné zakládat s prázdnou firmou. Vlastní modely se `company_id` povinným se sdílet nedají.

### Gaps
- Neověřil jsem, zda v Odoo 20 zcela chybí model `ir.property`; popsaný způsob ukládání vychází z dokumentace pole a kódu `orm/fields.py`.
- Řazení NULL u `company_id.id` jsem neviděl v hotovém SQL.

## Čtení napříč společnostmi

### Takeaway
Přehled přes fondy je proveditelný, ale musí být vlastní kód. `sudo()` obchází omezení firem, nevypíná však kontrolu konzistence firem při zápisu. Kód účtu závisí na aktivní firmě, takže přes ploché fondy nelze prostě seskupovat podle `code` ani podle `account_id`. V obrazu chybí modul účetních výkazů i konsolidace.

### Cited Findings
- V sudo `env.company` a `env.companies` nekontrolují povolené firmy (`orm/environments.py:246-261, 276-291`).
- `with_company` dá firmu na začátek `allowed_company_ids` (`orm/models.py:5492-5500`). Bez sudo a bez oprávnění vyhodí `AccessError` až při přístupu (`:5482-5486`).
- `_check_company` běží na `create` i `write` jen podle `_check_company_auto`; ve větvi není žádná výjimka pro sudo (`orm/models.py:3351-3415, 3989-3990, 4232-4233`).
- Výchozí doména firmy: `company_id in [firmy, False]` (`orm/models.py:3339-3349`). Varianty `parent_of`: `:162-196`.
- `account.move` má `_check_company_auto` (`addons/account/models/account_move.py:88`), firma dokladu musí ležet pod firmou deníku (`:937-944`).
- Párování mezi kořeny je zakázané: „Entries don't belong to the same company“ (`addons/account/models/account_move_line.py:3021-3025`).
- `account.code` se počítá přes `env.company.root_id` (`addons/account/models/account_account.py:314-322`). `placeholder_code` ukazuje `kód (firma)`, když účet do aktivního kořene nepatří (`:338-346, 384-385`).
- Převod kurzu: `sudo` jen když firma patří mezi kořeny uživatele (`addons/base/models/res_currency.py:350-352`).
- Mixin `res.currency.rate.consolidation.mixin` počítá kurz pro vybrané firmy k `date_to` (`addons/account/models/res_currency_rate_consolidation_mixin.py:27-54`).
- `account_reports`, `account_accountant`, `account_asset`, konsolidace a mezifiremní pravidla v obraze nejsou (`ls addons`, prázdný výsledek). Je tu jen `account_payment_interco` (`addons/account_payment_interco/__manifest__.py`), v testu nenainstalovaný.
- Vlastní kód používá `sudo` agregaci (`addons/custom/investra_cnb/models/cnb_map.py:40`) a `fund.sudo()._dashboard_values` (`addons/custom/investra_dashboard/models/dashboard.py:50`).

### Inferences
- Se 100 vybranými fondy v jednom seznamu bude `account_id.code` prázdné u účtů mimo aktivní kořen. Pro výkaz je třeba číst po firmách přes `with_company`, nebo z `code_store` po kořeni, nebo použít `placeholder_code`.
- Stejný účet ve 100 fondech je 100 různých `account_id`. Agregaci je potřeba dělat přes kód nebo přes roli (`investra.role.account`, `addons/custom/investra_entity/models/account_role.py:42-46`), což vlastní model už umožňuje.
- `company_dependent` hodnota je v jednom prostředí vždy pro jednu firmu; pro přehled je nutná smyčka nebo přímé čtení JSONB.
- `sudo` přehled **sám nefiltruje** podle povolených fondů. Pokud má přehled vidět jen část uživatelů, musí kód omezit firmy výslovně podle `env.user._get_company_ids()`.
- Pohledávky a závazky mezi fondy (hlavní společnosti) se nespárují napříč; každá strana je vlastní doklad ve vlastní firmě.

### Gaps
- Přesnou větev, která v `_search` a `_check_access` přeskakuje domény při `su`, jsem nečetl po řádcích; vycházím z varování v `orm/environments.py` a z běžného chování ORM.
- Které modely dědí konsolidační mixin, jsem neověřil.
- Výkon `_read_group` přes 100 firem jsem neměřil.

## Pobočky (parent_id): co se dědí, může mít jinou měnu?

### Takeaway
Pobočka **nemůže mít jinou měnu**: je delegovaná z kořene a hlídá ji constraint. Dědí se měna, fiskální rok, storno, `tax_exigibility`, osnova, deníky, daně a kurzy. `parent_id` nelze po založení změnit. Podfond s odlišnou funkční měnou tedy pobočkou být nemůže.

### Cited Findings
- Delegovaná pole: `currency_id` (`addons/base/models/res_company.py:163-171`), `fiscalyear_last_day`, `fiscalyear_last_month`, `account_storno`, `tax_exigibility` (`addons/account/models/company.py:401-407`). Jiné přepsání metody v `addons` mimo testy jsem grepem nenašel.
- Při založení se kopírují (`res_company.py:377-381`), změna na kořeni se propíše (`:427-439`), v pohledu jsou jen ke čtení (`:315-320`).
- Constraint vyhodí chybu při odchylce (`:468-475`).
- Změna `parent_id` je zakázaná (`:402-403`). Archivace kořene archivuje pobočky (`:424-425`).
- Kurzy: jen na hlavních společnostech (`addons/base/models/res_currency.py:534-538`); `_get_rates` a `_get_conversion_rate` vždy přecházejí na kořen (`:173, :350`).
- Osnova: pobočka načítá jen data `res.company` (`addons/account/models/chart_template.py:259-262`), pomocné účty kopíruje z kořene (`:955-957`), outstanding nezakládá (`:971-972`), `ref` se vrací ke kořeni (`:1267-1271`).
- Kód účtu je stejný s kořenem, `code_store` je klíčovaný kořenem (`addons/account/models/account_account.py:314-327`).
- Viditelnost: `parent_of` zpřístupní deníky, účty a daně předka (`addons/account/security/ir.access.csv:49, 58, 61`). Předci bez přístupu se v session posílají zvlášť (`addons/web/models/ir_http.py:159, 175-183`).
- Doklad může mít firmu pobočky na deníku kořene (`addons/account/models/account_move.py:937-944`).
- Zámky se berou přes všechny předky (`addons/account/models/company.py:572-576, 751-761`).
- Měnu kořene nelze změnit, má-li položky kořen nebo pobočka (`addons/account/models/company.py:904-906, 1136-1140`).
- Párování je povolené v rámci jednoho kořene (`addons/account/models/account_move_line.py:3021`).
- Další dědění: `company_details` (`addons/base/models/res_company.py:182-186`), barva (`:238-245`), `vat_disabled` (`addons/account/models/company.py:495-499`).

### Inferences
- Pobočky by snížily náklad osnovy a kurzů, ale jen pro podfondy stejné SICAV ve stejné měně a stejném účetním období. Oddělení je slabší: sdílený deník znamená sdílenou číselnou řadu a sdílené nastavení. Vlastní deník na podfond by část úspory vrátil.
- Rozhodnutí je prakticky nevratné, protože strom nelze měnit a měna je svázaná.
- Lockdate kořene zamkne všechny podfondy. Pro nezávislou uzávěrku podfondů je třeba zamykat na pobočce a kořen ponechat otevřený.
- Vlastní kód počítá s `investra.entity.parent_id` odděleně od `res.company.parent_id` (`addons/custom/investra_entity/models/entity.py:40`), hierarchii knih tedy lze vést bez poboček Odoo.

### Gaps
- Nezkoušel jsem pobočku v praxi: vlastní účty pobočky, číslování sdíleného deníku, výkazy po pobočkách.
- Účetní a regulatorní dopad (oddělení majetku podfondů) kód neřeší; patří k ověření u metodika nebo auditora.
