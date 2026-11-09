# Předání projektu Odoo

**Stav k:** 4. 11. 2026  
**Účel:** předat kontext jiné AI a plynule pokračovat ve výuce a vyhodnocování Odoo.

## 1. Uživatel a způsob spolupráce

- Uživatel je finančník a bývalý účetní metodik; dobře rozumí financím a účetnictví, ale učí se Odoo, Docker, PostgreSQL, Git a Python.
- Nyní chce především pochopit běžné používání Odoo, účetní logiku, datový model a chování modulů. Vývoj vlastních modulů je až pozdější cíl.
- Komunikovat česky, stručně a srozumitelně. Nevysvětlovat zbytečně účetní základy, ale objasňovat vazby mezi objekty a procesy Odoo.
- Při práci v UI dávat konkrétní, ověřené kroky pro skutečnou instalaci a rovnou uvést, co má uživatel udělat dál. Neposílat ho hledat neověřené či skryté položky menu.
- Agent nevidí živé Odoo UI; může pracovat se screenshoty, které uživatel pošle, a s read-only diagnostikou.
- Uživatel upozornil, že opakované mezikroky a žádosti o screenshoty zpomalují výuku. Postupovat svižně a screenshot žádat jen tehdy, když skutečně pomůže ověřit nejasnou obrazovku.
- U každé akce s účetním dopadem jasně sdělit, co se stane. Rozlišovat návrh od zaúčtovaného dokladu. Uživatel výslovně potvrdil, že databáze `odoo_cz` je testovací a lze v ní dělat dohodnuté testovací operace.
- Při nejistotě ověřit skutečné menu, stav modulu nebo databázový záznam; nepředpokládat vanilla Odoo chování.

## 2. Cíl projektu

Vyhodnotit Odoo pro české společnosti (např. s.r.o., a.s., SICAV) a případné fondy/podfondy. Dlouhodobě zvažované fondové domény:

- instrumenty, transakce, pozice, ceny a FX,
- ocenění, účetní klasifikace IFRS 9, P&L/OCI a NAV,
- návaznost na účetnictví Odoo.

Zatím se nemá automaticky začínat vývoj těchto modulů. Nejdříve pochopit standardní Odoo a nainstalované addony, definovat účetní politiku a požadavky a pak rozhodnout mezi vlastním modulem a specializovaným fondovým/portfoliovým systémem.

## 3. Prostředí a architektura

- Odoo **19.0 Community** běží lokálně v Dockeru.
- PostgreSQL **16** běží v Dockeru.
- Databáze: `odoo_cz`.
- Webové rozhraní: `http://localhost:8069`.
- PostgreSQL port je mapovaný pouze na localhost (`127.0.0.1:5432`).
- Konfigurace: [docker-compose.yml](./docker-compose.yml). Neuvádět ani znovu nevypisovat lokální přihlašovací hesla.
- Odoo addons path v Compose zahrnuje Odoo core a `/mnt/extra-addons/third_party/odoomates`.
- Addony třetích stran jsou oddělené v `addons/third_party/odoomates/`. Vlastní moduly `investra_*` jsou v `addons/custom/` a používá je vývojová instance Odoo 20 (`docker-compose.investra.yml`), ne tato výuková instance.
- Standardní Odoo core neupravovat. Neměnit zdrojový kód Odoo Mates, není-li k tomu závažný důvod. Vlastní funkce řešit samostatným addonem.
- V repozitáři jsou už existující staged/unstaged změny a soubory z předchozí práce. Před jakýmkoli úklidem, přepisem nebo commitem zkontrolovat Git status; cizí změny nevracet ani necommitovat bez pokynu.
- Záloha databáze a filestoru před dřívější restrukturalizací jsou v lokálním session storage, nikoli určené ke commitu:
  - `~/.copilot/session-state/63da3a27-55f4-4011-b113-cc33f5d8f14b/files/odoo_cz_before_addon_restructure.dump`
  - `~/.copilot/session-state/63da3a27-55f4-4011-b113-cc33f5d8f14b/files/odoo_cz_filestore_before_addon_restructure.tar.gz`

### Addon oddělení

- V minulosti uživatel výslovně schválil přesun Odoo Mates modulů do `addons/third_party/odoomates/` a úpravu addons path. Kopie byla ověřena před odstraněním starých kopií.
- `addons/custom/` obsahuje vlastní moduly a v addons path výukové instance není.
- Fondové a NAV moduly jsou ve větvi `feature/nav-prototyp`, stav popisuje `docs/prototyp-nav.md`.

## 4. Co je nainstalováno

Databázová kontrola k 4. 11. 2026: **76 nainstalovaných Odoo modulů**, z toho **17 modulů Odoo Mates**.

### Důležité standardní moduly a česká lokalizace

- `account` – účetnictví.
- `analytic` – analytické účetnictví; funkce byla během výuky výslovně povolena v nastavení.
- `l10n_cz` – česká lokalizace.
- `base_import` – obecná funkce importu.
- `account_edi_ubl_cii` – strukturovaná e-fakturace UBL/CII; není to OCR.
- Standardní Odoo moduly zahrnují mimo jiné faktury, platby, bankovní výpisy, měny, partnery, produkty, e-mail a webové rozhraní.

### Nainstalované Odoo Mates moduly

- `om_account_accountant`
- `om_account_asset`
- `om_account_bank_statement_import`
- `om_account_budget`
- `om_account_cash_forecast`
- `om_account_check_printing`
- `om_account_daily_reports`
- `om_account_followup`
- `om_account_reconcile`
- `om_currency_rate_update`
- `om_currency_revaluation`
- `om_fiscal_year`
- `om_recurring_payments`
- `om_spreadsheet_account`
- `om_spreadsheet_account_asset`
- `om_spreadsheet_account_budget`
- `om_spreadsheet_account_followup`

Nainstalován je také `accounting_pdf_reports`.

### Neinstalováno / nepotvrzeno jako dostupná funkce

- **Odoo Enterprise není nainstalováno**; běží Community.
- **Vlastní fund/NAV/portfolio modul neexistuje.**
- Nebyla nalezena OCR/digitalizace faktur; přiložení PDF k faktuře samo o sobě doklad nevytěžuje. Odoo OCR je samostatná IAP služba na kredity a není v této instalaci ověřená/aktivní.
- Živá synchronizace bankovních účtů není nastavena. Bankovní výpisy byly do testovací databáze importovány ze souborů.
- `hr_expense` je v databázi označen jako odinstalovaný.
- Přes databázový seznam modulů nebyla ověřena dostupnost specializovaného enterprise reportingu/XLSX ani OCR modulů. Nainstalované PDF reporty a spreadsheet moduly nepovažovat za důkaz konkrétního požadovaného reportu.
- ČNB kurzovní zdroj v modulu Odoo Mates nebyl nalezen. `om_currency_rate_update` nabízí mj. ECB a další poskytovatele; nastavení zdroje je na úrovni společnosti. To neznamená dvě paralelní kurzovní sady pro jednu společnost.

### Úplný seznam nainstalovaných modulů

```text
account
account_add_gln
account_check_printing
account_edi_proxy_client
account_edi_ubl_cii
account_payment
account_peppol
account_peppol_response
account_qr_code_sepa
accounting_pdf_reports
analytic
api_doc
auth_passkey
auth_passkey_portal
auth_signup
auth_totp
auth_totp_mail
auth_totp_portal
base
base_iban
base_import
base_import_module
base_install_request
base_setup
base_vat
bus
certificate
digest
google_gmail
html_editor
http_routing
iap
iap_mail
l10n_cz
mail
mail_bot
microsoft_outlook
om_account_accountant
om_account_asset
om_account_bank_statement_import
om_account_budget
om_account_cash_forecast
om_account_check_printing
om_account_daily_reports
om_account_followup
om_account_reconcile
om_currency_rate_update
om_currency_revaluation
om_fiscal_year
om_recurring_payments
om_spreadsheet_account
om_spreadsheet_account_asset
om_spreadsheet_account_budget
om_spreadsheet_account_followup
onboarding
partner_autocomplete
payment
payment_stripe
phone_validation
portal
privacy_lookup
product
resource
resource_mail
rpc
sms
snailmail
snailmail_account
spreadsheet
spreadsheet_account
spreadsheet_dashboard
spreadsheet_dashboard_account
uom
web
web_tour
web_unsplash
```

## 5. Aktuální testovací data a dosavadní lekce

Databáze obsahuje fiktivní testovací doklady a partnery. Kontrola 4. 11. 2026:

- 12 účetních dokladů (`account_move`), 26 účetních položek (`account_move_line`).
- 2 bankovní výpisy a 4 řádky výpisů.
- 1 záznam `account_payment`.
- 8 partnerů.
- 3 kurzové záznamy.
- 1 analytická položka.

### Faktury a měny

- `FA/2026/00001`: zákaznická faktura 12 100 Kč, zaúčtovaná, částečně uhrazená 5 000 Kč, zůstatek 7 100 Kč. Účetní řádky: výnos 604000 (10 000 Kč), DPH 343221 (2 100 Kč), pohledávka 311000 (12 100 Kč).
- `FA/2026/00002`: zákaznická faktura 1 210 EUR, zaúčtovaná a zaplacená. Při kurzu 24,20 zaúčtována v CZK za 29 282 Kč; kurzová revalvace +363 Kč a storno −363 Kč; realizovaný kurzový zisk při úhradě 605 Kč.
- `FA/2026/00003`: drobná testovací pohledávka 1 Kč, neuhrazená.
- Do databáze byly vloženy dva syntetické CAMT.053 bankovní výpisy. První obsahuje příchozí platbu 5 000 Kč a bankovní poplatek 50 Kč; druhý úhradu dodavatelské faktury 5 000 Kč.
- První testovací výpis je `TRAINING-20261102-001`; druhý `TRAINING-VENDOR-20261102-001`.
- Dodavatelská faktura `PŘIJA/2026/11/0001`, reference `DEMO-2026-001`, je zaúčtovaná a zaplacená (5 000 Kč, 518000 / 321000).
- Testovací data obsahují i účetní zápisy se zvláštními daty, včetně 15. 11. 2026, tedy pozdějšími než některá data reportů. Při vysvětlování historických reportů zkontrolovat datum zaúčtování i datum párování.
- Příklady jsou syntetické; nejsou to skutečné faktury ani skuteční obchodní partneři.

### Analytické účetnictví – poslední dokončená lekce

- Uživatel povolil analytické účetnictví v **Fakturace → Konfigurace → Nastavení → Accounting → Analytické účetnictví**. Tím zpřístupnil analytické plány a účty; samo nastavení nezaúčtovalo doklady.
- Existující plán se jmenuje **Projekty**, jeho výchozí použitelnost je volitelná.
- Uživatel vytvořil analytický účet **DEMO – Projekt A** v plánu Projekty.
- Vytvořil a výslovně schválil zaúčtování dodavatelské testovací faktury:
  - číslo `PŘIJA/2026/11/0002`,
  - reference `DEMO-ANALYTIKA-2026-001`,
  - 1 000 Kč bez daně,
  - řádek nákladu „DEMO – test analytické distribuce“ na 518000,
  - analytická distribuce 100 % na DEMO – Projekt A.
- Faktura je **zaúčtovaná a nezaplacená**; skutečně zvýšila náklady o 1 000 Kč a závazek 321000 o 1 000 Kč v testovací databázi. Nejde už o návrh.
- Databázová kontrola potvrdila analytickou položku propojenou s řádkem faktury na 518000, částka 1 000 Kč a analytický účet DEMO – Projekt A.
- Uživatel již otevřel a viděl seznam **Analytické položky** a potvrdil, že položku vidí.
- Plánovaný další krok je dokončit pohled/report analytického účetnictví a porovnat ho s hlavní knihou. Ověřit přesnou viditelnou cestu menu před instrukcemi; menu v této instalaci obsahuje položku **Hospodářské výsledky** v analytických výkazech. Zatím není potvrzeno, že byl tento report už otevřen.
- Poté vhodné pokračovat ručním účetním zápisem a deníky, importy, FX v praxi, majetkem/časovým rozlišením, uzávěrkou a více společnostmi. Uživatel se již ptal na tyto oblasti; nepředpokládat, že jde o nové téma.

### Související výukové koncepty již probrané

- `account.move` je účetní doklad/hlavička; `account.move.line` jsou jeho účetní řádky v hlavní knize.
- Faktura a její účetní zápis jsou propojené; zaúčtování vytvoří účetní dopad.
- Párování pohledávek/závazků propojuje konkrétní otevřené položky; samo o sobě není novým samostatným účetním dokladem.
- Analytika doplňuje hlavní knihu: účet říká typ nákladu/výnosu, analytický účet rozšiřuje pohled o projekt či jinou dimenzi. Není to náhrada oddělené hlavní knihy fondu/podfondu.
- Bankovní výpis není totéž co účetní zápis; v UI je potřeba otevřít bankovní transakci/výpis nebo účetní záznam podle toho, co chceme ukázat.

## 6. Odoo Mates, cizí měny a fondové účetnictví

### Odoo Mates revalvace

Z inspekce `om_currency_revaluation`:

- Průvodce vybírá měny, ne libovolný seznam účtů nebo jednotlivé investiční pozice.
- Pohledávky a závazky přeceňuje na základě otevřených zůstatků; ostatní účty zohledňuje, pokud jsou vedeny s konkrétní měnou.
- Pro společnost jsou nastaveny obecné účty pro FX zisk a ztrátu; není k dispozici pravidlové mapování per účet/instrument do P&L nebo OCI.
- Při budoucí customizaci zachovat auditní stopu, storno a kontrolu proti dvojímu zaúčtování.

### IFRS a návrh řešení

- IFRS 9 klasifikace (amortizované náklady, FVOCI, FVTPL) a IAS 21 kurzové rozdíly znamenají, že OCI nelze bezpečně určit prostou mapou účtů bez účetní politiky a dat o instrumentu.
- Nejdříve specifikovat typ účetní jednotky, funkční měnu, účetní období, klasifikaci instrumentu a zacházení se změnou reálné hodnoty a FX; až poté navrhnout automatizaci.
- Odoo multi-company může vést oddělená účetnictví právních společností a konsolidované výstupy; samo o sobě však není fondový NAV engine, instrumentový subledger ani evidence investorů/podfondů.
- Pravděpodobná volba pro specifická pravidla je samostatný custom addon nebo specializovaný fondový systém jako subledger napojený na Odoo. Nezasahovat do core/Mates.

## 7. Enterprise, cloud a čeští dodavatelé – předchozí zjištění

- Odoo Online Standard (ceník v době dotazu ukazoval 11,90 €/uživatel/měsíc) nepodporuje vlastní Python addony ani moduly z Odoo Apps Store.
- Odoo Online má One App Free pro jednu aplikaci, ale není vhodné pro současné Mates moduly a budoucí custom addon.
- Odoo.sh/On-premise a vlastní moduly jsou podle ceníku spojeny s plánem Custom; hosting Odoo.sh se účtuje zvlášť. Před nákupem ověřit aktuální cenu/licenční podmínky.
- Community lze provozovat bez Enterprise licence na vlastním nebo externím hostingu, ale správu hostingu a provozu pak zajišťuje uživatel/dodavatel.
- Enterprise může přinést OCR/IAP, dynamické reporty, exporty, API a další provozní funkce. Neřeší samo per-position FX/OCI, instrumentový subledger, NAV ani účetnictví fondu.
- Přechod edice by vyžadoval kontrolu kompatibility/licencí současných Mates addonů a migračního postupu; nic zatím nepřepínat ani neinstalovat.
- Veřejný průzkum českých dodavatelů: 26HOUSE je relevantní kandidát pro českou účetní lokalizaci a majetek, ale zveřejněná reference na PE skupinu nedokládá fund/SICAV/IFRS securities/NAV. CyberMindNet veřejně popisuje české Community moduly pro Odoo 18, ne doložený fundový systém pro Odoo 19. ITMAN uvádí obecné Odoo služby. V ohraničeném průzkumu nebylo nalezeno veřejně doložené hotové české Odoo řešení SICAV/podfond/IFRS/NAV; privátní reference nebyly vyloučeny.
- Doporučený rozhodovací postup: požadavková matice → demo/reference pro SICAV/podfond, OCI/P&L a NAV → srovnat Odoo + lokalizace/custom addon proti specializovanému portfolio systému + Odoo GL.

## 8. Poznámky k možným budoucím customizacím

Seznam je uložen mimo repozitář v session storage:

`~/.copilot/session-state/63da3a27-55f4-4011-b113-cc33f5d8f14b/files/customization_ideas.txt`

Dosud zapsané náměty; nejde o schválení k vývoji:

1. Kurzy ČNB a možnost ECB pro společnost s funkční měnou EUR.
2. Česká čísla bankovních účtů a jejich validace.
3. VS/SS/KS, bankovní výpisy a pravidla párování.
4. Schvalování a vytěžování přijatých faktur.

Před jakoukoli implementací ověřit standardní Odoo a instalované addony, upřesnit požadavek a získat souhlas uživatele.

## 9. Důležité uživatelské bezpečnostní preference

Bez zvláštního souhlasu lze číst projekt, Docker konfiguraci/logy, stav Git, provádět read-only diagnostiku, SQL `SELECT`, analýzu a bezpečné testy.

Předem vyžádat souhlas pro změny Docker Compose, přesuny/mazání modulů, instalaci/odinstalaci/upgrade modulů, restart/stop služeb s dopadem na provoz, změnu databázového schématu, migraci/obnovu DB a změny s účetním či historickým dopadem.

Nikdy bez výslovného souhlasu neprovádět nad databází `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `DROP TABLE` ani `DROP DATABASE`; nikdy nemaž Docker volumes. Účetní data upravovat standardním Odoo ORM/UI, ne přímými zápisy do PostgreSQL.

## 10. Skill české finanční regulace

Osobní Copilot skill `regulation` je uložen mimo projekt:

`~/.copilot/skills/regulation/SKILL.md`

Obsahuje rámec pro přípravu/posuzování českých regulatorních podání a odkazy na ZPKT, ZISIF, AML, účetní předpisy a IFRS. Při regulatorních/ČNB tématech se jím řídit a aktuální znění práva vždy ověřit. Pro jinou AI může být nutné soubor předat nebo vložit jeho relevantní instrukce; jiné AI nemusí mít přístup k této lokální cestě.

## 11. Doporučené bezprostřední pokračování

1. Dokončit analytický pohled/report pro **DEMO – Projekt A** a ověřit částku proti účtu 518000 v hlavní knize.
2. Vysvětlit, že analytická dimenze obohacuje řádek hlavní knihy, ale není samostatným účetním okruhem.
3. Poté přejít na ruční účetní zápisy a deníky; před každým zaúčtováním uvést účetní dopad.
4. Později řešit importy, FX, majetek/časové rozlišení, uzávěrku a více společností.
5. Fondový modul zatím pouze analyzovat a specifikovat; nezakládat automaticky modely Fund/Instrument/Position/NAV.
