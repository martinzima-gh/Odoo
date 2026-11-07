# Provozní praxe: mnoho společností v jedné databázi Odoo a mnoho fondů ve fondovém softwaru

Stav k 2026-11-07. Značení důkazů u každého bodu:
- **[KÓD/DOK]** = primární zdroj, zdrojový kód nebo oficiální dokumentace, čteno přímo (GitHub `odoo/odoo`, `odoo/documentation`, `OCA/*`).
- **[VENDOR]** = marketing výrobce nebo implementačního partnera, tvrzení bez nezávislého ověření.
- **[KOMUNITA]** = fórum, recenze, názor uživatele; nezávislé, ale neověřené.
- **[ÚRYVEK]** = známe jen z výsledku vyhledávání, stránku se nepodařilo přečíst celou.

## 1. Reálné případy Odoo s mnoha společnostmi

### Takeaway
Veřejně doložený, jménem pojmenovaný provoz Odoo s více než asi 30 subjekty jsem nenašel. Nejbližší analogie je správcovská společnost Squale Capital (Lucembursko, asi 30 společností a fondů), ale její reference neříká nic o NAV ani o architektuře databáze. Běžně citované limity (10–15, 30–50, 50–100+ společností) jsou nepodložené odhady poradenských firem a navzájem si odporují, takže strop pro náš případ musí určit vlastní zátěžový test.

### Cited Findings

**Pojmenované případy (všechny jsou vendor/partner, žádný není nezávislý audit):**
- **Squale Capital**, Lucembursko, správcovská společnost (ManCo), „around 30 companies and funds“. Aplikace: Accounting, Invoicing, Documents, Sign, Knowledge, WhatsApp, Dashboard. Výchozí problém: standardní balíček Odoo neodpovídal fondovým procesům, chyběla podpora složitých fondových struktur, regulatorního souladu a přehledu v reálném čase. Přínosy jsou bez čísel. Stránka neuvádí verzi, edici, jednu versus více databází, datum ani způsob výpočtu NAV. **[VENDOR]** — [Captivea: Squale Capital](https://www.captivea.com/customers/squale-capital-1070105)
- **TBRM Group**, Nizozemsko, inkubátor pro strojírenství a služby. Růst z 5 na 20 subjektů, Odoo.sh ze 1 na 4 servery, 30+ uživatelů, 50+ zaměstnanců, implementace asi 2 měsíce (start únor 2020). Nové společnosti se přidávají snadno, začíná se účetnictvím. Co přesně běží na oněch 4 serverech, článek neříká. **[VENDOR, blog Odoo, 2025-06-03]** — [Odoo: TBRM Group](https://www.odoo.com/blog/customer-reviews-6/how-tbrm-group-streamlined-intercompany-management-with-odoo-1718)
- **Grupo Bibo**: 5 společností. Centrální CRM, sklad, výroba, účetnictví více společností, reporting přes Dashboard Ninja (doplněk třetí strany). Výchozí problémy: datová sila, nekonzistentní kmenová data, roztříštěné reporty. Přínosy bez čísel. **[VENDOR, Vauxoo, 2025-08-07]** — [Vauxoo: Grupo Bibo](https://www.vauxoo.com/en_US/blog/customer-cases-5/grupo-bibo-how-a-multi-company-business-conquered-operational-complexity-with-odoo-271)
- **ABL S.A.**, Lucembursko, subjekty v LU, BE, ES, ZA, samostatná účtová osnova pro každý subjekt. Nasazení za 3 měsíce a 50 konzultantských hodin. Autor a datum neuvedeny. **[VENDOR/neurčeno]** — [CaseStudies.com: ABL](https://www.casestudies.com/company/odoo/case-study/odoos-multi-company-approach-simplifies-abls-complex-business-environment)
- **POC Real Estate** (BE/PL): rozptýlená data, dvojí zadávání, pomalé reporty, nasazení 2024–2025, pod 50 uživatelů. Počet SPV (účelových společností) nezjištěn. **[VENDOR, ÚRYVEK]** — [Odoo: POC Real Estate](https://www.odoo.com/blog/customer-reviews-6/from-fragmentation-to-centralization-how-poc-real-estate-is-building-efficiency-with-odoo-1916)
- **VSH United Nederland B.V.**: nizozemský holding skupiny působící v NL, Surinamu a USA; více struktury ve finančním řetězci. Počet subjektů neuveden. **[VENDOR, ÚRYVEK]** — [OdooExperts: VSH United](https://cdn.odooexperts.nl/en_US/odoo-reference/vsh-united-nederland-b-v-12106)
- Developer na Kypru, v Srbsku a SAE (51–200 zaměstnanců): přechod z oddělených nástrojů na multi-company platformu. Klient nejmenován. **[VENDOR, ÚRYVEK]** — [VentorTech](https://ventor.tech/?p=14779)

**Tvrzení o počtech společností (nepodložená, vzájemně nekonzistentní):**
- „No hard limit“, „implementations with 50–100+ companies exist“, 30–50 společností běží efektivně při vyladěném PostgreSQL; nad to „dedicated performance testing“. Bez zdroje a benchmarku. **[VENDOR, 2026-03]** — [ECOSIRE](https://ecosire.com/blog/odoo-multi-company-setup-guide)
- „No hard cap“, ale spolehlivě „up to 10-15 entities on standard hosting“. Bez měření; článek si odporuje i ve vlastních nákladových číslech ($3 900 versus $4 200 měsíčně). **[VENDOR]** — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices)
- Tvrzení, že výkon závisí hlavně na objemu transakcí, ne na počtu subjektů, a že existuje organizace s 50+ subjekty; tentýž článek ale tvrdí, že Community podporuje jen jednu společnost, což je **chybně** (viz vývojářská dokumentace Odoo k multi-company a existence repozitáře OCA/multi-company). Zdroj je tedy nespolehlivý. **[VENDOR, ÚRYVEK]** — [ECOSIRE: multi-entity accounting](https://ecosire.com/zh/blog/odoo-multi-entity-accounting); protiklad: [Odoo developer howto: company](https://github.com/odoo/documentation/blob/20.0/content/developer/howtos/company.rst)
- Fórum Odoo k volbě jedna databáze versus izolované instance: jen obecné rady (jedna DB pro podobné činnosti a logiku, oddělené pro odlišné provozy), žádná čísla ani popis selhání. **[KOMUNITA, Odoo 14, bez data]** — [Odoo forum 182313](https://www.odoo.com/forum/help-1/one-database-with-multiple-companies-or-isolated-instances-182313)

**Doložené bolesti a mechanismy:**
- Oficiální dokumentace: při přihlášení do více společností naráz lze vytvořit prodejní objednávku ve společnosti A s produktem společnosti B a chyba přístupu se projeví až po odhlášení z B; špatně řízený multi-company je „source of a lot of inconsistent multi-company behaviors“. **[KÓD/DOK]** — [Odoo developer howto: company](https://github.com/odoo/documentation/blob/20.0/content/developer/howtos/company.rst)
- Záznamy vytvořené při jiné aktivní společnosti se „připnou“ k té společnosti a ostatní je nevidí; autor tomu přičítá 9 z 10 „chyb“ multi-company. Doporučuje kontrolu `company_id` u produktů a partnerů jedním SQL dotazem před ostrým startem. **[VENDOR, ale praktická zkušenost, 2026-07-16]** — [Code Agency](https://codeagency.be/blog/odoo-multi-company)
- Vyčlenění jedné společnosti ze sdílené databáze je bolestivé (due diligence, prodej). Dodatečná změna struktury je „the most expensive cleanup job in ERP“. **[VENDOR]** — [Code Agency](https://codeagency.be/blog/odoo-multi-company)
- Výkon pravidel záznamů (ir.rule): v OCA PR zaznívá, že pravidlo nad `company_id` zpomaluje vyhodnocení a že doplnění větve `('company_id','=',False)` vrací zrychlení zpět. **[ÚRYVEK; přiřazení citace ke konkrétnímu PR jsem neověřil]** — [OCA PR 123](https://github.com/OCA/multi-company/pull/123), [OCA PR 270](https://github.com/OCA/multi-company/pull/270), [OCA PR 624](https://github.com/OCA/multi-company/pull/624)
- Přispěvatel OCA upozornil, že některé multi-company chyby se musí řešit v jádře, protože je spouštějí i cron úlohy běžící pod adminem. Vlákno se při načtení vrátilo jako 404. **[ÚRYVEK]** — [OCA contributors list](https://odoo-community.org/groups/contributors-15/contributors-60272)
- Vícenásobně aktivní společnosti zviditelňují záznamy napříč subjekty; doporučení držet aktivních co nejméně. Riziko: široká admin práva přes všechny subjekty. **[VENDOR]** — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices)
- Forum Odoo 16: e-mailové adresy druhé společnosti se objevily v dokladech první; jde o konfiguraci izolace, ne o výkon. **[KOMUNITA, ÚRYVEK]** — [Odoo forum 221516](https://www.odoo.com/forum/help-1/odoo-16-enterprise-multi-company-221516)

**Srovnávací strop z jiného ERP:** NetSuite OneWorld má dokumentovaný limit 250 poboček včetně kořenové; vyšší počet po dohodě. Eliminační a neaktivní pobočky se do limitu nepočítají. **[KÓD/DOK]** — [Oracle NetSuite Help](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N268563.html); starší čísla 125 v [komunitních zdrojích](https://archive.netsuiteprofessionals.com/t/23434492/is-there-a-limitation-around-the-number-of-subsidiaries-that) tomu odporují, primární dokumentace má přednost.

### Inferences
- Případ správce fondů na Odoo existuje (Squale), ale nedokazuje, že NAV běží v Odoo. Jeho hodnota je jen v tom, že řád „desítky fondů a společností“ je na Odoo prakticky provozovaný.
- Absence veřejných příběhů se stovkami společností je sama signál: buď takové provozy nejsou, nebo se o nich nepíše. Nedá se to brát jako důkaz, že to nejde.
- Stropem bude spíš kombinace objemu dokladů, počtu současně vybraných společností, pravidel záznamů a cron úloh než samotný počet řádků v `res_company`. Je to moje odvození z mechanismu, ne naměřený fakt.
- U TBRM růst ze 1 na 4 servery Odoo.sh naznačuje, že ani 20 subjektů nemuselo být triviální, ale článek neříká, zda jde o produkční servery, nebo o rozdělení do více databází.

### Gaps
- Žádná nezávislá zpráva o selhání nebo opuštění velkého multi-company Odoo. Žádný veřejný benchmark Odoo pro desítky a stovky společností.
- Squale Capital: nezjištěno, zda jde o jednu databázi, kde se počítá NAV a která edice běží. Ověřit lze jen dotazem u Captivea.
- Nenašel jsem doložené franšízové nasazení Odoo se stovkami subjektů ani případ skupiny SPV s Odoo; zůstává neověřené, zda tyto provozy existují.

## 2. Účetní firmy a sdílená servisní centra: jedna databáze, nebo jedna na klienta

### Takeaway
Oficiální program Odoo pro účetní firmy stojí na **databázi na klienta** a na centrálním správci databází, nikoli na jedné multi-company databázi; je ale vázaný na SaaS Odoo Online, takže pro Community na vlastním serveru neplatí. Rozdíl oproti nám je zásadní: klienti účetní firmy jsou nezávislí, zatímco fondy jednoho správce sdílejí tým, metodiku a potřebu souhrnů.

### Cited Findings
- Program Odoo Accountants Network: bezplatný přístup k klientským databázím Odoo Online, centrální dashboard pro všechny klienty, přidání zaměstnanců do více databází jedním krokem a odebrání oprávnění, klíčové ukazatele všech klientů naráz. Finanční konzultant Odoo pomáhá nastavit **šablonové databáze** a migrovat data. Podmínka: nejméně 2 aktivní klienti v Odoo. Text výslovně „databáze na klienta“ neříká, plyne to z formulace „clients' Odoo Online (SaaS) databases“. Community a on-premise nezmiňuje. **[VENDOR, 2026-08-17, verze pro Německo]** — [Odoo blog: Accountants Network](https://www.odoo.com/blog/odoo-news-5/digital-connected-efficient-the-official-odoo-accountants-network-2378)
- Neomezený počet bezplatných SaaS databází pro klienty, 2FA vynutitelná napříč klientskými databázemi, zámky období podle role, asi 5 000 účetních firem na Odoo, PwC/Deloitte/KPMG Belgie pro klientskou práci, KPMG převedla přes 1 000 klientů. Program popsán pro USA a Kanadu, regiony se liší. **[VENDOR, 2026-07-15, čísla neověřená]** — [Odoo blog: QuickBooks alternative](https://www.odoo.com/blog/business-hacks-1/quickbooks-alternative-2323)
- Španělská verze programu naopak říká „spravovat více společností ze stejného systému“, aniž by určila model; bez čísel. **[VENDOR, 2026-03-11]** — [Odoo blog: Programa de firmas contables](https://www.odoo.com/blog/business-hacks-1/odoo-accounting-firms-program-digitize-and-scale-your-accounting-firm-2095)
- Podmínky se liší podle regionu: Německo vyžaduje 2 klienty, pro USA/Kanadu komunitní odpověď uvádí, že minimum není. **[KOMUNITA, ÚRYVEK]** — [Odoo forum 284370](https://www.odoo.com/forum/help-1/extra-user-subscription-required-for-an-external-odoo-recognized-accountant-yes-or-no-284370)
- Režim „Accounting Firms“ v Accounting ‣ Configuration ‣ Settings: editovatelné číselné řady dokladů, pole celkové částky s daní pro rychlé zadání, předvyplněná data dokladů, Quick encoding. Je to režim zápisu, ne nástroj správy mnoha klientů. **[KÓD/DOK]** — [Odoo 19 Accounting docs](https://www.odoo.com/documentation/19.0/applications/finance/accounting.html)
- Tamtéž: účetnictví lze zobrazovat za více společností současně, ale pracovat „only on a single company's accounting at a time“. **[KÓD/DOK]** — [Odoo 19 Accounting docs](https://www.odoo.com/documentation/19.0/applications/finance/accounting.html)
- Srovnání architektur: multi-company nemá izolaci nad rámec přístupových práv, jedinou verzi, nelze zálohovat jednu společnost samostatně. Multi-database izoluje na úrovni DB a umožňuje `pg_dump` na klienta, sdílí workery a verzi. Kontejner na klienta umožňuje různé verze. Sizing je vydáván za výchozí hodnoty, ne benchmarky. **[VENDOR, hostingový prodejce, 2026]** — [OEC.sh: multi-tenant](https://oec.sh/guides/odoo-multi-tenant)
- Multi-database „zabíjí“ nativní mezipodnikovou automatizaci. **[VENDOR]** — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices)
- Kdy oddělit databázi: možný prodej subjektu, nesouvisející byznysy, odlišné cykly upgradů. Pravidlo: bez sdíleného provozu dostanete jen sdílený „blast radius“. **[VENDOR, 2026-07-16]** — [Code Agency](https://codeagency.be/blog/odoo-multi-company)
- Sdílený multi-company systém soustředí uživatele, reporty, integrace a automatické úlohy; větší výpadek může postihnout všechny společnosti. **[VENDOR, ÚRYVEK; souhrn vyhledávání, přesnou stránku jsem nepřiřadil, odkazy jsou orientační]** — [Red Bee Software](https://redbeesoftware.com/blog/running-multiple-companies-on-one-system-how-odoos-multi-company-setup-works), [Altapete](https://www.altapetesolutions.com/blog/odoo-multi-company-vs-multiple-instances)

### Inferences
- Pro fondy správce neplatí hlavní důvody účetních firem pro oddělené databáze (nezávislí klienti, různé licence, odchod klienta), s jednou výjimkou: **přenos správy fondu k jinému administrátorovi** je obdoba „prodeje subjektu“, proto je potřeba mít od začátku definovaný export jedné knihy.
- Odoo Online nástroje (správce databází, hromadné přidání uživatelů) na Community na vlastním serveru nedostaneme. Pokud by se zvolil model více databází, je nutné je postavit vlastními skripty.
- Dokumentační věta o práci „jen v jedné společnosti naráz“ se týká účetních záznamů; pracovní model zaměstnance je tedy přepínání knih, nikoli zápis napříč knihami.

### Gaps
- Veřejně jsem nenašel, kolik klientů mají účetní firmy typicky v jedné multi-company databázi ani jak dopadly firmy, které to zkusily. Přednáška Odoo Experience 2026 má na stránce jen anotaci bez čísel — [Odoo Experience 2026](https://www.odoo.com/event/odoo-experience-2026-americas-10327/track/spotlight-how-accounting-firms-win-with-odoo-10814).
- Oficiální doporučení „jedna databáze na klienta“ jsem v doslovném znění nenašel; je to odvození z popisu programu.
- Nenašel jsem veřejný případ sdíleného servisního centra na Odoo.

## 3. Reporting napříč společnostmi: co je reálně dostupné v Community 20

### Takeaway
Community Odoo 20 nemá modul `account_reports` ani konsolidaci, a klíčové moduly OCA pro verzi 20.0 zatím nejsou hotové: `mis_builder` je na větvi 20.0 `installable: False` a migrace je otevřený PR. Souhrny přes fondy tedy dnes znamenají buď čekat a pomoci s migrací OCA, nebo stavět vlastní SQL/BI vrstvu nad PostgreSQL. Pro fondy je to méně bolestivé, než se zdá, protože souhrn fondů není účetní konsolidace.

### Cited Findings

**Stav k 2026-11-07, ověřeno přímo na GitHubu:**
- V `odoo/odoo` větev 20.0 existuje a ve složce `addons` není `account_reports`, `account_accountant`, `account_consolidation` ani moduly mezipodnikových pravidel. Je tam `spreadsheet_account` a `account_payment_interco`. **[KÓD/DOK]** — [odoo/odoo 20.0 addons](https://github.com/odoo/odoo/tree/20.0/addons)
- Community modul `account` obsahuje model `account.report` a soubory `account_code_mapping.py` a `res_currency_rate_consolidation_mixin.py`, tedy datové základy; samotné zobrazení finančních výkazů je mimo Community (modul `account_reports` v addons chybí). **[KÓD/DOK]** — [odoo/odoo 20.0 account/models](https://github.com/odoo/odoo/tree/20.0/addons/account/models)
- `OCA/mis-builder` větev 20.0: manifest má verzi 19.0.1.2.1 a `installable: False`; PR migrace `mis_builder` je otevřený od 2026-09-30, `mis_builder_budget` od 2026-10-27. Na 19.0 je modul ve stavu Production/Stable. **[KÓD/DOK]** — [mis_builder manifest 20.0](https://github.com/OCA/mis-builder/blob/20.0/mis_builder/__manifest__.py), [PR na 20.0](https://github.com/OCA/mis-builder/pulls?q=is%3Apr+base%3A20.0)
- `OCA/account-financial-reporting` 20.0 je prázdná; `account_financial_report` má otevřený migrační PR, jeden předchozí byl zavřen. Na 19.0 existují `account_financial_report`, `account_tax_balance`, `partner_statement`, `mis_builder_cash_flow`. **[KÓD/DOK]** — [OCA/account-financial-reporting](https://github.com/OCA/account-financial-reporting/pulls?q=is%3Apr+base%3A20.0)
- `OCA/account-consolidation`: modul je jen na větvích 12.0 (`account_consolidation`) a 14.0 (`account_consolidation_oca`), na 13.0 a 15.0–19.0 nic. Prakticky je opuštěný. **[KÓD/DOK]** — [OCA/account-consolidation](https://github.com/OCA/account-consolidation)
- OCA modul `account_consolidation` funguje přelitím položek do konsolidační společnosti (konsolidační deník, rozdílový účet, profily dceřiných společností). **[KOMUNITA, starší verze, ÚRYVEK]** — [OCA Apps: Account Consolidation](https://apps.odoo-community.org/modules/account_consolidation)

**mis_builder (funkce, starší položky changelogu před 2022 označeny):**
- Od Odoo 13: na instanci reportu lze uvést více povolených společností; report pracuje s **průnikem** společností reportu a společností vybraných v kontextu uživatele. **[KÓD/DOK, starší]** — [mis_builder README](https://github.com/OCA/mis-builder/blob/20.0/mis_builder/README.rst)
- Konsolidace s převodem měny, kurz ke konci vykazovaného období (jeden kurz, nikoli historický a průměrný). Eliminace modul neřeší. **[KÓD/DOK, před 2022]** — [mis_builder README](https://github.com/OCA/mis-builder/blob/20.0/mis_builder/README.rst), [issue #7](https://github.com/OCA/mis-builder/issues/7)
- Podpora poboček (branch) od 17.0.1.0.2 (2024-11-11). Alternativní zdroje dat musí mít pole `company_id`. **[KÓD/DOK]** — [mis_builder README](https://github.com/OCA/mis-builder/blob/20.0/mis_builder/README.rst)
- Oprava zobrazení účtů v multi-company režimu sloučena 2026-05-27; souvisí se změnou modelu účtů (viz níže). **[KÓD/DOK]** — [mis-builder PR 790](https://github.com/OCA/mis-builder/pull/790)
- Otázka, zda mis_builder vytvoří konsolidovanou rozvahu matky a dcery, je v issue bez jasné odpovědi. **[KOMUNITA, Odoo 11, starší]** — [issue #218](https://github.com/OCA/mis-builder/issues/218)

**Enterprise (pro porovnání):**
- Dokumentace 20.0 popisuje konsolidaci jako kombinaci nástrojů: mapování účtů, Multi-Ledgers (konsolidační kniha obsahující úpravové deníky ostatních společností), výběr společností v selektoru a přepočet měn (vlastní kapitál historickým kurzem, P&L váženým průměrem, ostatní rozvaha závěrkovým kurzem). Slovo „elimination“ se na stránce nevyskytuje ani jednou. **[KÓD/DOK]** — [consolidation.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/applications/finance/accounting/get_started/consolidation.rst)
- Starší samostatná aplikace Consolidation: uživatel Florian Pichl tvrdí, že mezipodnikové položky jen vypouští, nerekonciliuje, měnový přepočet je omezený a jde o manažerskou, nikoli zákonnou konsolidaci; zaměstnanec Odoo tvrdí opak a uvádí podporu menšinových podílů; analytika v aplikaci není. Verze a data nejasné (tagy v14/v15), proto spíše historický kontext. **[KOMUNITA, možná před 2022]** — [Odoo forum 170044](https://www.odoo.com/forum/help-1/does-odoo-support-consolidation-or-financial-data-from-more-than-one-company-to-get-consolidated-financials-170044)
- ECOSIRE tvrdí, že „Odoo 19's consolidation module automates most eliminations“. To je v rozporu s tím, že dokumentace 20.0 eliminace nezmiňuje; tvrzení nepřebírat. **[VENDOR]** — [ECOSIRE](https://ecosire.com/blog/odoo-multi-company-setup-guide)
- Community doplňky mimo OCA existují (např. `gb_multi_company_consolidation_lite`, 18.0, 19.0), neprověřeno. **[VENDOR]** — [Odoo Apps](https://apps.odoo.com/apps/modules/19.0/gb_multi_company_consolidation_lite)

**Změna modelu účtů důležitá pro reporting:**
- Od Odoo 18 má `account.account` pole `company_ids` (Many2many), kód účtu je v `code_store` (`company_dependent`). Sdílet účet lze mezi společnostmi, ale „Bank & Cash accounts cannot be shared between companies“. Změna kódu se propisuje všem společnostem se stejným `root_id`. **[KÓD/DOK]** — [account_account.py 20.0](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_account.py)
- Praktický dopad: účet se může při zobrazení z kontextu jiné společnosti jevit bez kódu. **[ÚRYVEK]** — [mis-builder PR 790](https://github.com/OCA/mis-builder/pull/790)
- Sloučení účtů napříč společnostmi lze vrátit, ale „will not unmerge the chatters“: historie změn zůstane sloučená natrvalo. **[KÓD/DOK]** — [consolidation.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/applications/finance/accounting/get_started/consolidation.rst)

**BI nad PostgreSQL:**
- Přímé připojení na PostgreSQL obchází pravidla záznamů Odoo, protože běží v ORM, ne jako row-level security databáze. Doporučení: read-only role omezená na potřebné tabulky, kurátorované pohledy filtrované podle společnosti, RLS v BI nástroji, čtecí replika. **[VENDOR, 2026-08-07]** — [Octura](https://octurasolutions.com/resources/connect-odoo-to-power-bi-tableau-or-apache-superset)
- Zapomenutý filtr `company_id` „silently consolidate[s] entities“. Přeložitelná pole jsou od Odoo 16 JSONB. **[VENDOR]** — [Octura](https://octurasolutions.com/resources/connect-odoo-to-power-bi-tableau-or-apache-superset)
- Tvrzení Octury, že Odoo 20 odstraní XML-RPC i JSON-RPC, **je nepřesné**: dokumentace 20.0 říká, že služba `db` byla odstraněna v Odoo 20, služby `common` a `object` mají být odstraněny v Odoo 22 (podzim 2028), obě API jsou zastaralá a náhradou je JSON-2. **[KÓD/DOK]** — [external_api.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/developer/reference/external_api.rst)
- OCA `bi_sql_editor` (SQL pohledy jako modely Odoo) a `sql_request_abstract` jsou na 19.0, `reporting-engine` větev 20.0 je prázdná. **[KÓD/DOK]** — [OCA/reporting-engine](https://github.com/OCA/reporting-engine)
- Oficiální přehled pro uživatele: vybrané společnosti lze zobrazovat naráz a vidět agregace „without switching interfaces“. **[KÓD/DOK]** — [multi_company.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/applications/general/companies/multi_company.rst)

### Inferences
- Pro přehledy vedení nad fondy jde většinou o **agregaci** (AUM, NAV, poplatky, stav uzávěrek), ne o konsolidaci s eliminacemi. Absence nástrojů pro eliminace proto pravděpodobně vadí jen u skupinové účetní závěrky vlastních společností. Rámec účtování fondů versus společností je třeba posoudit odděleně, tady se neposuzuje.
- Doporučený směr: vlastní vrstva SQL pohledů (read-only role, pohledy filtrované podle knihy, čtecí replika nebo noční kopie) je jediná varianta, která dnes na Odoo 20 Community nezávisí na nedokončené migraci OCA. `mis_builder` je vhodný doplněk, až se migrace dokončí; migrace je aktivní, ale termín nelze odvodit.
- Sdílení účtů přes `company_ids` je pro mnoho knih lákavé (jedna údržba osnovy), ale změna kódu se propíše všude a sloučení historie je nevratné. Před použitím otestovat, včetně dopadu na výkazy ČNB.
- Průnik společností v `mis_builder` znamená, že výsledek reportu závisí na tom, co má uživatel právě zaškrtnuté v selektoru. Riziko pro opakovatelnost výkazů.

### Gaps
- Výkon `mis_builder` při desítkách společností: nenašel jsem data.
- Není ověřeno, zda je Multi-Ledgers dostupné v Community; dokumentace edici neuvádí. Ověřit na instalaci.
- Nezávislé benchmarky pro Metabase/Superset nad Odoo: nenalezeny, zdroje jsou prodejci integrací.

## 4. Správa: šíření konfigurace, změny osnovy, nastavení modulů, uživatelé

### Takeaway
Odoo ani OCA nemají hotový nástroj „šablona společnosti plus hromadné promítnutí změn“. Existují dílčí kousky (`account_chart_update`, `account_multicompany_easy_creation`, `base_user_role_company`), které na větvi 20.0 ještě nejsou, takže šíření konfigurace bude vlastní skript nebo addon nad ORM. Na odstranění RPC je potřeba myslet od začátku: nové skripty psát proti JSON-2 API.

### Cited Findings

**Dostupnost modulů OCA k 2026-11-07:**

| Modul | Účel | 18.0 | 19.0 | 20.0 |
|---|---|---|---|---|
| `account_chart_update` | porovná osnovu se šablonou, vytvoří nebo přepíše účty, daně, fiskální pozice | ano | ano | otevřený PR |
| `account_multicompany_easy_creation` | průvodce vytvořením společnosti | ano | ne | otevřený PR (2026-11-03) |
| `base_user_role` / `base_user_role_company` | role uživatelů, role podle společnosti | ano | ano | otevřený PR (`base_user_role`) |
| `base_multi_company`, `partner_multi_company`, `product_multi_company` | sdílení záznamů pro vybrané společnosti | ano | ano | otevřené PR (říjen až listopad 2026) |
| `account_invoice_inter_company` | mezipodnikové faktury | ano | ano | otevřený PR |
| `res_company_active` | archivace společností (v 20.0 je archivace v jádře) | ano | ano | není v seznamu PR |
| `res_company_category`, `res_company_code`, `res_company_search_view` | kategorie, kód, hledání společností | ano | jen `search_view` | PR u `code`, `search_view` |
| `auditlog` | auditní stopa | ano | ano | na 20.0 zatím není |
| `auto_backup` | zálohy | ano | ano | **ano** |

Zdroj tabulky: přímý výpis větví a PR přes GitHub API. **[KÓD/DOK]** — [OCA/multi-company](https://github.com/OCA/multi-company), [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools), [OCA/server-backend](https://github.com/OCA/server-backend), [OCA/server-tools](https://github.com/OCA/server-tools)

- `account_chart_update`: „update Odoo installations after tax reforms… or to apply fixes performed on the chart template“; porovnává a umí přepsat účty, daně a fiskální pozice. **[KÓD/DOK]** — [README 19.0](https://github.com/OCA/account-financial-tools/blob/19.0/account_chart_update/README.rst)
- `base_user_role_company`: role platí jen tehdy, je-li nastavena pro **všechny** aktuálně vybrané společnosti. Uživatel se rolí pro A a vybranými A + B tu roli nemá. **[KÓD/DOK]** — [README 19.0](https://github.com/OCA/server-backend/blob/19.0/base_user_role_company/README.rst)
- Na větvi 20.0 je otevřený PR „[FIX] base_user_role: don't let roles impose…“ (text názvu zkrácen); role tedy na 20.0 ještě nejsou stabilní. **[KÓD/DOK]** — [OCA/server-backend PR](https://github.com/OCA/server-backend/pulls?q=is%3Apr+base%3A20.0)
- `multicompany_configuration` (formulář pro partnery a produkty) existuje jen pro 14.0–16.0, stav Beta. **[KÓD/DOK]** — [PyPI](https://pypi.org/project/odoo-addon-multicompany-configuration/)
- `res_company_category` přidává kategorie společností pro statistiku v multi-company prostředí (jen 18.0). `res_company_active` přidává archivaci společností, ale dokumentace 20.0 popisuje archivaci přímo v jádře, takže na 20.0 zřejmě není potřeba. **[KÓD/DOK]** — [OCA/multi-company](https://github.com/OCA/multi-company), [multi_company.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/applications/general/companies/multi_company.rst)
- Jádro Odoo 20: společnosti lze archivovat přímo v UI, nové produkty a kontakty jsou v multi-company databázi implicitně sdílené, jednotlivé vlastnosti sdíleného záznamu mohou být specifické pro společnost. **[KÓD/DOK]** — [multi_company.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/applications/general/companies/multi_company.rst)
- Funkce „Inter-Company Transactions“ popsaná v dokumentaci není v Community addons 20.0 (viz otázka 3). **[KÓD/DOK]** — [odoo/odoo 20.0 addons](https://github.com/odoo/odoo/tree/20.0/addons)
- Vývojářské nástroje konzistence: `company_dependent`, `_check_company_auto = True`, `check_company=True`, kontrola je striktní. **[KÓD/DOK]** — [company howto 20.0](https://github.com/odoo/documentation/blob/20.0/content/developer/howtos/company.rst)
- Vlastní skripty: XML-RPC a JSON-RPC jsou zastaralé, služba `db` je v Odoo 20 odstraněna, transakce JSON-2 je vždy jen jedno volání. Hromadnou změnu přes API tedy nelze zabalit do jedné transakce. **[KÓD/DOK]** — [external_api.rst 20.0](https://github.com/odoo/documentation/blob/20.0/content/developer/reference/external_api.rst)
- Šablonové databáze pro klienty pro účetní firmy nastavuje finanční konzultant Odoo; je to tedy běžná praxe, ale služba pro SaaS. **[VENDOR]** — [Odoo blog: Accountants Network](https://www.odoo.com/blog/odoo-news-5/digital-connected-efficient-the-official-odoo-accountants-network-2378)
- Praxe: rozhodnout první den, které společnosti budou v databázi do 3 let. Účetnictví striktně podle společnosti, kontakty a produkty sdílet vědomě. Automatické protidoklady nechat začínat jako koncept. **[VENDOR]** — [Code Agency](https://codeagency.be/blog/odoo-multi-company)
- Testovat mezipodnikové toky, oprávnění a konsolidované reporty před ostrým během. **[VENDOR]** — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices)

### Inferences
- Pro fondy dává smysl vlastní addon typu „definice knihy jako kód“: idempotentní založení společnosti (osnova, deníky, číselné řady, daně, zámky období, role) a `diff` proti šabloně po vzoru `account_chart_update`. Běh uvnitř ORM (Odoo shell nebo cron) řeší i problém, že JSON-2 nemá transakci přes více volání.
- Logika `base_user_role_company` (role jen při shodě ve všech vybraných společnostech) je přísná, ale pro přístup k více fondům bezpečná. Nevýhoda: zaměstnanec se zaškrtnutými všemi knihami ztratí roli, pokud je v jediné knize nemá. Ověřit v testu.
- Závislost na OCA pro verzi 20.0 je reálné projektové riziko: migrace běží, ale v listopadu 2026 je většina potřebných modulů v PR. Možnosti: přispět do migrace, používat nesloučený PR s rizikem, nebo řešit vlastním addonem. Rozhodnutí patří uživateli.
- Neautomatizovaná správa roste lineárně s počtem knih; každá ruční změna nastavení v N společnostech je riziko rozjezdu konfigurace. Potřebná je pravidelná kontrola rozdílů mezi knihou a šablonou.

### Gaps
- Nenašel jsem veřejný popis správy desítek společností skriptem (`click-odoo`, Odoo shell, IaC) z provozní praxe.
- Neověřeno, jak se chová `account_chart_update` s modelem sdílených účtů od Odoo 18 v mnoha společnostech.
- Neověřeno, zda jádro Odoo 20 omezuje počet společností v selektoru nebo jak se UI chová při stovkách položek. Ověřit testem na DEV.

## 5. Fondový software: jedna hlavní kniha s dimenzí, nebo oddělené knihy

### Takeaway
Veřejné materiály ukazují převládající vzor: **jedna platforma a jedna sada kmenových dat, nad nimi samostatná, plně vyvážená kniha pro každý právní subjekt nebo fond**, s bezpečností na úrovni fondu a s nástrojem šablon fondů. Čistá „jedna kniha s dimenzí fondu“ se pro fondy jako doložený model neukázala. Datové modely výrobci nezveřejňují, takže závěr opírám o marketing a dokumentaci obecných ERP, ne o schémata.

### Cited Findings

**Fondový software (téměř vše VENDOR; nezávislá dokumentace datových modelů neexistuje veřejně):**
- **FundCount**: „running hundreds of client books“ na „one investment-grade ledger“, každá kniha klienta „logically isolated“, „one team, one console“, rekonciliační rozdíly v „exception queue with drill-down to source“. Investiční záznam a hlavní kniha jsou tentýž záznam. **[VENDOR]** — [FundCount: Fund Administration](https://fundcount.com/fund-administration)
- FundCount uvádí multi-currency a multi-book účetnictví, IFRS i GAAP, konsolidaci subjektů; strukturu subjektů nevysvětluje. Srovnávací stránka je od konkurenta Investranu. **[VENDOR]** — [FundCount vs Investran](https://fundcount.com/fundcount-vs-investran/)
- **SS&C Geneva**: Fund Designer vytváří master-feeder, mini-master, AIV, SPV, blocker; fondové šablony zjednodušují založení nové struktury; role s oprávněními **po fondu**; NAV na podíl podle tranše investora. **[VENDOR, konzultační partner]** — [IVP: Geneva](https://www.ivp.in/resources/blogs/enhance-the-power-of-geneva-world-investor-with-ivp-geneva-consulting/)
- Geneva: předvaha a NAV automaticky pro každý právní subjekt, otevřené, uzavřené i hybridní struktury (známe jen z úryvku, PDF se nepodařilo přečíst). **[VENDOR, ÚRYVEK]** — [Advent: Geneva Private Markets brief](https://cdn.advent.com/assets/21udsyef/geneva-private-markets-product-brief.pdf)
- Geneva umí pohled na knihy podle portfolio manažera a custodiana a alokaci nákladů (2020, starší). **[VENDOR, před 2022]** — [Advent blog](https://www.advent.com/news-and-insights/blog/multi-manager-fund-structures-grow-and-operational-challenges-grow-with-them/)
- **Allvue**: „true general ledger“, multi-fund prostředí „from a single instance“, standardy a postupy jednotně napříč fondy, fondové a manažerské knihy v jednom zdroji; platforma na Microsoft Dynamics 365 Business Central, stejná stránka ale uvádí i Dynamics NAV (vnitřní rozpor). Workflow kapitálového volání účtuje do GL bez přepisování. **[VENDOR]** — [Allvue: Fund Accounting](https://www.allvuesystems.com/solutions/fund-accounting)
- Allvue: kniha se vede na úrovni fondu nebo právního subjektu (ABOR). Jedno kapitálové volání se účtuje na každé úrovni struktury. **[VENDOR, ÚRYVEK]** — [Allvue: Investment Accounting](https://allvuesystems.com/solutions/investment-accounting), [Allvue in Action](https://www.allvuesystems.com/allvue-in-action/)
- **Temenos Multifonds**: ABOR a IBOR na jedné platformě, přes 350 konfigurovatelných kontrol, zpracování po výjimkách, více a ad-hoc ocenění a NAV denně. Testimoniál Standard Chartered: asi 10% zlepšení vydávání NAV. **[VENDOR]** — [Multifonds pro administrátory](https://www.multifonds.com/?p=643)
- Multifonds uvádí přes 40 000 fondů a přes 35 jurisdikcí (tvrzení firmy, 2026-08-12). **[VENDOR]** — [Fintech.ca](https://www.fintech.ca/?p=5844)
- Canada Life: přes 700 fondů a přes 2 000 tříd na jedné platformě. **[VENDOR, ÚRYVEK; souhrn vyhledávání, přesnou stránku jsem nepřiřadil, odkaz je orientační]** — [Temenos Multifonds](https://www.temenos.com/?p=87280)
- DBS: alokace P&L podle třídy nebo master segmentu s rabaty poplatků. **[VENDOR, 2025-11-05]** — [Multifonds: DBS](https://www.multifonds.com/news/2025/11/05/multifonds-helps-dbs-to-drive-scalable-automation-and-future-growth-in-the-regions-asset-management-industry/)
- **FIS Investran** (dnes Private Capital Suite): zákazníci chválí „robust general ledger“ a flexibilitu struktur; tyto citace jsou staré (éra SunGard). **[VENDOR, před 2022, ÚRYVEK]** — [Private Equity Wire](https://www.privateequitywire.co.uk/investindustrial-selects-sungards-investran/). Stránka uvádí zaměření na multi-entity GL a uzávěrky. **[třetí strana, ÚRYVEK]** — [FitGap: Investran](https://us.fitgap.com/products/041512/investran)
- Recenze G2 na Investran: chvála pro účetnictví PE, stížnosti na timeouty relace a nutnost dlouhého školení; malý vzorek, stránku se nepodařilo načíst (403). **[KOMUNITA, ÚRYVEK]** — [G2: Investran](https://www.g2.com/products/investran/reviews)
- Dva ledgery u PE: fondová a manažerská (operační) kniha; některé platformy je sjednocují, jiné rekonciliují. **[VENDOR, ÚRYVEK; souhrn vyhledávání, přesnou stránku jsem nepřiřadil, odkazy jsou orientační]** — [FundCount](https://fundcount.com/best-fund-administration-software-solutions), [Ceviche](https://www.ceviche.ai/resources/best-fund-accounting-software-private-equity)
- Allvue uvedlo GP Accounting pro rozpor mezi knihami fondů a GP subjektů. **[VENDOR, ÚRYVEK]** — [IT Brief](https://itbrief.news/story/allvue-launches-gp-accounting-for-private-capital-firms)

**Multi-entity v obecných a realitních systémech:**
- **Sage Intacct**: entita je „a separate tax identification or a separately secured, fully balancing set of books“. Sdílené seznamy (uživatelé, osnova, zákazníci, dodavatelé) se nastaví jednou nahoře; uživatele lze omezit na entity. Příklad: správa nemovitostí, kde každá nemovitost je entita. Glosář výslovně uvádí „self-balancing fund“ jako typ entity. **[KÓD/DOK; glosář ÚRYVEK]** — [Sage: multi-entity overview](https://www.intacct.com/ia/docs/en_US/help_action/Company/Multi-Entity_upgrade/overview-single-vs-multi-entity.htm), [Sage: terms](https://www.intacct.com/ia/docs/en_GB/help_action/Intacct_basics/New_to_Sage_Intacct/top-terms.htm)
- Sage přesouvá segmenty z čísla účtu do dimenzí, takže osnova zůstává krátká. **[VENDOR/partner]** — [BCS ProSoft](https://www.bcsprosoft.com/dimensional-accounting-in-sage-intacct/)
- Mapování mezientitních účtů musí mít účty založené předem, jinak chyby při účtování. **[KÓD/DOK, ÚRYVEK]** — [Sage: inter-entity mapping](https://www.intacct.com/ia/docs/en_AU/help_action/Multi-entity/Inter-entity_transactions/inter-entity-account-map-plans.htm)
- **Oracle EBS**: sdílejí-li právní subjekty jeden ledger, jediný způsob zabezpečení dat subjektu jsou data access sets nad vyvažovacím segmentem. **[KÓD/DOK, ÚRYVEK]** — [Oracle docs](https://docs.oracle.com/cd/E18727_01/doc.121/e13425/T348488T348494.htm)
- **Dynamics 365 Finance**: více právních subjektů může sdílet jednu osnovu, výjimky přes přepsání pro subjekt; osnovu po zaúčtování v subjektu nelze změnit. **[KÓD/DOK, ÚRYVEK]** — [Microsoft: Configure ledgers](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/configure-ledger)
- **Yardi Voyager**: více sad knih, nastavení finančních subjektů, stromy účtů, alokace GL, mezipodnikové účtování. Velká portfolia mohou trvat rok a více. **[třetí strana, ÚRYVEK]** — [ERP Research](https://www.erpresearch.com/erp/yardi-voyager/financial-management)
- Pravidlo „1 home ledger per entity“ a „intercompany is the join; a second copy of the same GL is the failure“. **[VENDOR, blog, není standard Yardi]** — [US Tech Automations](https://ustechautomations.com/resources/blog/yardi-voyager-vs-quickbooks-online-construction-multi-entity-2026)
- **ERPNext** (open source): každý právní subjekt je Company s vlastní osnovou a měnou; eliminace ručně přes eliminační společnost nebo dimenzi. **[VENDOR, ÚRYVEK]** — [ECOSIRE: ERPNext guide](https://ecosire.com/hi/blog/erpnext-accounting-module-guide)
- Fund accounting přes analytické účty v Odoo: tento vzor platí pro neziskovky (fondy jako účelové prostředky), ne pro právně samostatné fondy. **[VENDOR, ÚRYVEK]** — [Custom Pixel Design](https://custompixeldesign.com/blog/the-pixel-brief-1/how-nonprofits-and-mission-driven-organizations-can-use-odoo-to-run-more-efficiently-31)

**Kontrola NAV napříč fondy:**
- NAV oversight: porovnání NAV administrátora s interními záznamy, doporučené přehledy přes fondy. **[VENDOR, ÚRYVEK; plná stránka vrátila 429]** — [Arcesium](https://www.arcesium.com/blog/optimizing-nav-oversight)
- Temenos prodává nezávislou kontrolu NAV a záložní výpočet pro výpadek administrátora. **[VENDOR, ÚRYVEK]** — [IBS Intelligence](https://ibsintelligence.com/ibsi-news/temenos-launches-a-dynamic-nav-oversight-and-contingency-solution-for-asset-managers/)

**Přenositelné poučení (shrnutí vzorů, viz Inferences):**

| Vzor v oboru | Doloženo u | Ekvivalent v Odoo |
|---|---|---|
| Vyvážená samostatná kniha na subjekt | Sage, Geneva, Allvue | `res.company` na fond nebo podfond |
| Sdílené kmenové seznamy | Sage, Dynamics | Partneři a instrumenty bez `company_id` |
| Jedna osnova, výjimky u subjektu | Sage, Dynamics | Sdílené účty (`company_ids`) nebo šablona + `diff` |
| Šablona fondu | Geneva Fund Designer | Vlastní addon; hotový nástroj neexistuje |
| Oprávnění po fondu | Geneva, Sage | `company_ids` uživatele, role |
| Práce po výjimkách | FundCount, Multifonds | Vlastní fronta kontrol; není hotová |
| Jedna akce účtuje na více úrovních | Allvue | Vlastní logika nad `account.move` |

### Inferences
- Rozhodnutí „fond nebo podfond = samostatná společnost v Odoo“ odpovídá oborovému vzoru „samostatná vyvážená kniha“. Sdílený ledger s dimenzí podle Oraclu vyžaduje bezpečnost nad segmentem a neřeší samostatné uzávěrky, sekvence ani zámky období. To je moje vyhodnocení, ne citace.
- Největší rozdíl fondového softwaru proti holému Odoo není datový model, ale **provozní vrstva nad knihami**: konzole přes fondy, fronta výjimek, šablony fondů a kontroly NAV (Multifonds uvádí 350+ kontrol). Tuhle vrstvu je potřeba navrhnout vědomě, jinak se pracovní doba rozpadne na přepínání společností.
- Třída fondu je podle DBS a Canada Life úroveň **pod** fondem (alokace P&L), ne samostatná kniha: 700 fondů a 2 000 tříd na jedné platformě. Pro Odoo to mluví proti tvorbě společnosti na třídu; zda to platí pro tento projekt, musí potvrdit deník rozhodnutí.
- Poměr jeden tým a jedna konzole znamená, že rozhodující metrikou není počet společností, ale čas uzávěrky jedné knihy krát počet knih. Vyplatí se ho měřit od prvního fondu.
- Dvojí kniha správce a fondů u PE je běžná. Účetní rámce vlastní společnosti a fondů se nemají míchat, oddělené knihy to podporují přirozeně.

### Gaps
- Skutečné datové modely Investran, Geneva, Multifonds, FundCount a Allvue nejsou veřejné; přímá odpověď „jedna tabulka s dimenzí versus oddělená úložiště“ se doložit nedá. FundCountovo „one ledger… logically isolated“ může technicky znamenat obojí.
- Investran: produktový list FIS se nepodařilo načíst (403), dokumentace k legal entity není veřejná — [FIS product sheet](https://fisglobal.com/-/media/fisglobal/files/pdf/product-sheet/fis-investran-product-sheet.pdf).
- Geneva brief: PDF nešlo v tomto prostředí převést na text, tvrzení je z úryvku.
- Nezávislé srovnání fondového softwaru jsem nenašel; srovnávací stránky píše hlavně FundCount, konkurent porovnávaných produktů.
- Yardi: vlastní dokumentace nastavení entit není veřejná bez přístupu, k SPV konkrétně nic oficiálního.
