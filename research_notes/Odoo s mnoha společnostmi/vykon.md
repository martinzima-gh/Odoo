# Výkon a škálování Odoo s desítkami až stovkami společností v jedné databázi

Stav k 7. 11. 2026. Třídy důkazů použité v poznámkách:

- **[A]** měření nebo plán dotazu v PR, případně přímo přečtený kód,
- **[B]** oficiální dokumentace,
- **[C]** zkušenost pojmenovaných praktiků (OCA mailing list),
- **[D]** nedoložené tvrzení dodavatele nebo fóra.

Kód Odoo 20 jsem četl jen pro čtení v kontejneru `odoo:20.0-20261102`. Odkazy vedou na veřejnou větev `20.0` (ověřeno, že soubory existují); čísla řádků platí pro zmíněný obraz a na větvi se mohou lišit.

Pokrytí GitHubu je neúplné: veřejné vyhledávací API odmítlo dotazy (rate limit) a `gh` tu není. Issues a PR jsem hledal jen webovým vyhledáváním. Že něco nebylo nalezeno, tedy neznamená, že to neexistuje.

## Jsou zdokumentované limity nebo reálné zkušenosti s 50, 100 a 500+ společnostmi?

### Takeaway
Tvrdý limit nikde doložený není a benchmark podle počtu společností pro Odoo 17 až 20 jsem nenašel. Nejlepší doložené zkušenosti jsou 89 a 96 společností bez zpomalení, ale z roku 2022, u 96 společností na verzi 12 (u 89 je verze neuvedená). O 200 a více společnostech jsem nenašel žádnou věrohodnou zprávu.

### Cited Findings
- **[C]** Vlákno „multi company: how many companies is too many?“ (OCA contributors, 10. 5. 2022) je nejlepší veřejný zdroj. Ptal se Alexandre Fayolle (Camptocamp), kdy se začne projevovat degradace kvůli record rules nebo company properties — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/multi-company-how-many-companies-is-too-many-10517?mode=date). Jde o testovací zrcadlo archivu; adresa na hlavní doméně vrátila 404.
- **[C]** Sylvain Le Gal (GRAP): 96 společností na Odoo V12, „Didn't observed performance degradation due to the quantity of companies“. Pomalost vznikala v konkrétních funkcích (validace skladových pohybů u velkých objednávek, velmi velké faktury). Sám uvádí, že jeho šetření je omezené — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/multi-company-how-many-companies-is-too-many-10517?mode=date).
- **[C]** Pedro M. Baeza (Tecnativa): „We have one with 89 without a performance penalty.“ Verzi neuvádí; případný problém podezírá v konkrétním neoptimalizovaném pravidle — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/re-multi-company-how-many-companies-is-too-many-10520?mode=date).
- **[C]** Graeme Gellatly naopak vidí problémy už při 10 společnostech, ale s „wildly different data distributions and the largest table at 50,000,000 lines“. Rozhodující je tedy rozložení dat, ne počet společností — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/re-multi-company-how-many-companies-is-too-many-10520?mode=date).
- **[A]** Nejbližší měření podle počtu společností pochází ze skladu, ne z účetnictví. PR #287906 (cíl 19.0): výpočet termínů orderpointů při 3 společnostech 575 ms, při 15 společnostech 8,95 s, při 30 společnostech 2,2 min. Spolu s počtem společností ale rostly i počty lokací a pohybů (30 společností = 300 000 otevřených pohybů). Oprava snižuje časy na 591 ms / 2,00 s / 15,15 s. K 7. 11. 2026 je PR otevřený a neslitý — [PR #287906](https://github.com/odoo/odoo/pull/287906).
- **[D]** Ecosire: „Implementations with 50–100+ companies exist“, „databases with 30–50 companies run efficiently“, nad to doporučuje testovat. Článek neuvádí žádné zdroje, jména ani podmínky testu — [Ecosire](https://ecosire.com/blog/odoo-multi-company-setup-guide).
- **[D]** Braincuber: „Performance stays reliable up to 10-15 entities on standard hosting“, bez dat a bez definice hostingu. Je to v rozporu s Ecosire a oba údaje jsou nedoložené — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices).
- **[D]** Poradenský přehled: „Odoo publishes no size band“. Údaje o limitu společností ani benchmarky neobsahuje — [Onetribe](https://www.onetribeadvisory.com/knowledge-hub/erp/odoo/).
- **[A]** Odoo UI počítá s více než 9 společnostmi: vyhledávací pole v přepínači se zobrazí, když `allowedCompaniesWithAncestors.length > 9`. Žádnou horní mez jsem v přepínači ani v `session_info` nenašel — [switch_company_menu.js](https://github.com/odoo/odoo/blob/20.0/addons/web/static/src/webclient/switch_company_menu/switch_company_menu.js), [ir_http.py](https://github.com/odoo/odoo/blob/20.0/addons/web/models/ir_http.py).

### Inferences
- Rozsah 50 až 100 společností není mimo známou praxi, doložené případy jsou však staré: předcházejí uložení company-dependent polí v jsonb (18.0) i sdíleným účtům. Nelze je beze změny přenášet na Odoo 20.
- Čísla v článcích dodavatelů (10–15, 30–50) nemají důkazní hodnotu. Pro rozhodnutí by měla sloužit jen jako podnět k vlastnímu měření.
- Účetní zátěž fondů (málo uživatelů, málo dokladů na společnost, podobná velikost společností) by měla být příznivější než Gellatlyho případ. To je předpoklad; závisí na tom, zda jeden fond nebude objemem výrazně převažovat.

### Gaps
- Pro Odoo 17 až 20 jsem nenašel žádnou zprávu s konkrétním počtem společností nad 30. Pro Odoo 20 neexistuje veřejný benchmark tohoto typu, který bych našel.
- Pro 200, 300, 500+ společností nebyla nalezena žádná věrohodná zmínka.
- U případu 89 společností není známa verze, objem dat ani počet uživatelů. U 96 společností (GRAP) není znám objem dat.

## Co se s rostoucím počtem společností zpomaluje?

### Takeaway
Hlavní riziko není samotné vyhodnocení pravidel, ale špatné plány PostgreSQL na velkých tabulkách s nerovnoměrným rozložením `company_id` a kód, který pracuje po jednotlivých společnostech. Přepínač, session a cookie rostou lineárně a podle kódu to do stovek společností nevypadá jako problém; změřené to ale není. Zakládání společností má cenu lineární, se skladem v součtu kvadratickou.

### Cited Findings
**Record rules (v Odoo 20 už přístupová pravidla `ir.access`)**
- **[A]** V Odoo 20 je `ir.rule` nahrazené modelem v `ir_access.py`. Pravidla jsou v `security/ir.access.csv`, kontext domény obsahuje `company_ids = self.env.companies.ids` (aktivní, ne všechny povolené společnosti) — [ir_access.py](https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/models/ir_access.py).
- **[A]** Doklady a položky: `[('company_id', 'in', company_ids)]`. Účty a deníky: `('company_ids', 'parent_of', company_ids)` a `('company_id', 'parent_of', company_ids)` — [ir.access.csv](https://github.com/odoo/odoo/blob/20.0/addons/account/security/ir.access.csv).
- **[A]** `parent_of` se rozkládá v Pythonu přes `parent_path` na množinu ID, tedy do SQL nejde rekurze — [domains.py](https://github.com/odoo/odoo/blob/20.0/odoo/orm/domains.py).
- **[C]** „Record rules make little difference, neither does properties in my experience.“ Platí pro verze do roku 2022 — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/re-multi-company-how-many-companies-is-too-many-10520?mode=date).
- **[D, zastaralé]** Issue z éry 8.0 popisuje pravidlo na many2many poli společností, které do SQL rozepisovalo dlouhé seznamy ID. Čteno jen z úryvku vyhledávání — [#12801](https://github.com/odoo/odoo/issues/12801). Podobně 13.0: pomalé pohledy POS kvůli nestorovanému `company_id` v pravidle — [#58546](https://github.com/odoo/odoo/issues/58546).

**Plány PostgreSQL (nejsilnější doložený mechanismus)**
- **[C]** Gellatly: „truly awful query planning“ na podivně tvarovaných dotazech kvůli rozložení `company_id` ve velkých tabulkách. Nejhorší jsou Enterprise reporty na tabulkách kolem 5 mil. řádků (reconcile, závislé na datu a společnosti, velké joiny) — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/re-multi-company-how-many-companies-is-too-many-10520?mode=date).
- **[A]** PR #286948 (2026, forward-port z #285096, slitý): nová společnost bez položek v databázi s mnoha položkami. Vnořený dotaz na `res_company` zabránil plánovači znát ID, zvolil Seq Scan + nested loop (asi 5 573 ms); po opravě Index Only Scan (asi 2 ms). `_existing_accounting`: 10 mil. řádků 700 ms → 500 µs, 100 mil. řádků 5,3 s → 1,3 ms; pokud obě společnosti mají 20 mil. řádků, jen 2 ms → 1,3 ms. Spouštěcí místo v PR je otevření PoS — [PR #286948](https://github.com/odoo/odoo/pull/286948).
- **[A]** V Odoo 20 je `_existing_accounting` už dvoukrokový (nejdřív ID společností, pak `search_count`), tedy oprava je v obrazu — [company.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/company.py).
- **[A]** PR #290208 (cíl 20.0, září 2026): výchozí řazení `account.account` joinuje agregaci přes cesty předků. U čerstvě vytvořené společnosti plánovač předpokládá jediný účet a agregaci opakuje pro každý účet. Oprava v testovacím načtení osnovy: `ANALYZE` (Peru TestSequence 120–132 s → 4,3–7,2 s). Přepis dotazu by podle autora zpomalil produkční vyhledávání. Problém je popsán pro testy, ne pro produkci — [PR #290208](https://github.com/odoo/odoo/pull/290208).
- **[A]** Výchozí řazení v Odoo 20 je `_order = "code_path, account_type, name_path, id"` — [account_account.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_account.py).

**Kód po jednotlivých společnostech**
- **[A]** PR #287906 (viz výše): dva `_read_group` na společnost, tedy čas roste s počtem společností — [PR #287906](https://github.com/odoo/odoo/pull/287906).
- **[A]** Cron `_cron_post_stock_valuation` prochází filtrované společnosti v Python cyklu. Jde o ukázku vzoru, ne o úplný seznam — [company.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/company.py).

**Web klient, přihlášení, session**
- **[A]** `session_info` posílá pro každou povolenou společnost `id, name, sequence, child_ids, parent_id, currency_id`, navíc nepovolené předky — [ir_http.py](https://github.com/odoo/odoo/blob/20.0/addons/web/models/ir_http.py).
- **[A]** Aktivní společnosti se ukládají do cookie `cids` ve tvaru ID spojených pomlčkou — [user.js](https://github.com/odoo/odoo/blob/20.0/addons/web/static/src/core/user.js).
- **[A]** `res.company` je v Odoo 20 `CachedModel`: pole `name, active, sequence, currency_id, parent_id, partner_id` jsou ve stabilní cache a jejich zápis ji invaliduje — [res_company.py](https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/models/res_company.py), [models_cached.py](https://github.com/odoo/odoo/blob/20.0/odoo/orm/models_cached.py).
- **[A]** Invalidace `stable` zasahuje i cache `default` a `templates.cached_values`. Velikosti LRU: `default` 8192, `stable` 1024 — [registry.py](https://github.com/odoo/odoo/blob/20.0/odoo/orm/registry.py).
- **[A]** `__accessible_branches` má ormcache s klíčem `frozenset(env.companies.ids), self.id, uid`: každá kombinace výběru, společnosti a uživatele je samostatná položka — [res_company.py](https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/models/res_company.py).

**Zakládání společnosti a instalace osnovy**
- **[A]** České šablony mají 323 řádků v `account.account-cz.csv` a 149 v `account.tax-cz.csv` včetně záhlaví (řádek CSV nemusí být jeden záznam) — [l10n_cz šablona](https://github.com/odoo/odoo/blob/20.0/addons/l10n_cz/data/template/account.account-cz.csv).
- **[A]** U společnosti s `parent_id` (pobočka) se načítají jen data `res.company` ze šablony, účty a daně se nezakládají — [chart_template.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/chart_template.py).
- **[A]** S modulem `stock` zakládá každá nová společnost lokace, sekvence, typy pohybů a pravidla. Navíc `_set_per_company_inter_company_locations` zapisuje na partnery všech ostatních společností a v cyklu přes všechny ostatní společnosti, protože „the env company must be different every time“ — [stock res_company.py](https://github.com/odoo/odoo/blob/20.0/addons/stock/models/res_company.py).

### Inferences
- **Přepínač a session:** 100 společností je zhruba 100 malých objektů v JSON a asi 500 bajtů v cookie, což je hluboko pod obvyklým limitem cookie (kolem 4 kB, nezdrojováno). Při trojciferných ID (4 znaky včetně pomlčky) a výběru všech společností by se limit přiblížil zhruba u 1 000 aktivních společností. Přihlášení by se tedy nemělo zhoršit znatelně; ověřit to na datech ještě zbývá.
- **Pravidla:** seznam až 100 ID v `IN` je pro PostgreSQL běžný. Zátěž roste hlavně tím, že uživatel s aktivními všemi společnostmi vidí celou tabulku, ne tím, že je seznam dlouhý.
- **Sestavy:** konsolidace přes všechny společnosti nese objem všech fondů. Práce v jedné společnosti je levná jen tehdy, když plán skutečně použije `company_id`; u malých společností vedle jedné velké hrozí chybný odhad (přesně mechanismus z PR #286948).
- **Cache:** časté přepínání výběru u více uživatelů spotřebovává LRU `default`. Hromadné zakládání nebo přejmenovávání společností za provozu vyprázdní cache ve všech workerech. Doporučení: provádět to mimo špičku.
- **Účtová osnova:** bez sdílení je 100 společností řádově 32 000 řádků `account_account` (100 × 322), pořád malá tabulka. Dotazy nad ní ale běží všude (pole účtu, řazení), proto na plánu a statistikách záleží víc než na velikosti.
- **Zakládání se skladem:** celková cena založení N společností roste kvadraticky. Pokud platforma `stock` neinstaluje, tato položka odpadá.
- **Vlastní moduly:** výpočty NAV a výkazy ČNB mohou snadno opakovat vzor „cyklus přes společnosti“. V naší vlastní kódové bázi je to pravděpodobně větší riziko než core.

### Gaps
- Čas instalace `l10n_cz` na jednu společnost a závislost na počtu společností nejsou nikde veřejně změřeny.
- Nezměřeno: doba přihlášení, otevření přepínače a vykreslení menu při 100+ společnostech. Virtualizaci seznamu v přepínači jsem neověřoval.
- Menu ani seznamy nemají doložený vztah k počtu společností; v kódu jsem jej cíleně neprocházel.
- Enterprise účetní výkazy nejsou v Community kódu a nemohl jsem je ověřit. Projekt běží na Community.
- Úplný seznam cronů s cyklem přes společnosti není zpracován; viděl jsem jen účetní crony a jeden příklad.

## Známé issues a PR k výkonu při více společnostech (hlavně 17 až 20)

### Takeaway
Odoo S.A. aktivně opravuje jednotlivá místa, kde výkon závisí na počtu společností nebo rozložení dat (2026: #286948, #287906, #290208). Přesun na jsonb (18.0) a sdílené účty změnily strukturu dat, ale jejich PR neobsahují žádná měření pro mnoho společností. Index jsonb polí není per-company.

### Cited Findings
- **[A]** PR #175627 (18.0, „[IMP] core: jsonb company dependent“): company-dependent pole jsou uložená jsonb pole s hodnotami `{"1": val}`, fallbacky se přesunuly do `ir_default.json_value`, many2one pole dostávají výchozí index `btree_not_null`. Slitý commit `ba34d853`, nasazený 23. 9. 2024. PR neobsahuje žádné benchmarky — [PR #175627](https://github.com/odoo/odoo/pull/175627).
- **[A]** Recenzent kmagusiak v tom PR zpochybnil, zda se index reálně používá; index po společnostech byl navržen pro budoucí PR — [PR #175627](https://github.com/odoo/odoo/pull/175627).
- **[A]** V Odoo 20 zůstává výchozí `index='btree_not_null'` a `prefetch='company_dependent'`; `_column_type` je jsonb — [fields.py](https://github.com/odoo/odoo/blob/20.0/odoo/orm/fields.py).
- **[D]** Odpověď na fóru: hodnota se ukládá, jen když se liší od výchozí — [Odoo fórum](https://odoo.com/forum/help-1/where-i-can-find-company-properties-in-odoo-18-266446). Podle PR #175627 je fallback v `ir_default`, tvrzení tomu odpovídá, ale přímo jsem ho v kódu neověřoval.
- **[A]** Migrace na jsonb má mezery: OCA `contract` potřeboval doplnění hodnot z `ir_property` — [OCA/contract #1410](https://github.com/OCA/contract/pull/1410); openupgradelib zapisoval boolean hodnoty chybně — [openupgradelib #474](https://github.com/OCA/openupgradelib/issues/474). Pro nás relevantní jen obecně, začínáme bez migrace.
- **[A]** `account.account` v Odoo 20: `code_store = fields.Char(company_dependent=True)`, `company_ids` many2many, `code_mapping_ids`. Kód se čte a zapisuje přes `env.company.root_id`, tedy kódy jsou po kořenových společnostech a pobočky je sdílejí — [account_account.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_account.py).
- **[A]** Související opravy 18.0: zápis kódu přes `code_mapping_ids` a přepsání `_ensure_code_is_unique` — [PR #183695](https://github.com/odoo/odoo/pull/183695); synchronizace kódů mezi pobočkami a kořenem kvůli cache — [PR #188686](https://github.com/odoo/odoo/pull/188686). Stav slití jsem neověřoval.
- **[A]** Dopad na externí moduly: OCA výkazy dostávaly `False` kód účtu bez `with_company()` — [OCA PR #1490](https://github.com/OCA/account-financial-reporting/pull/1490).
- **[B]** Sdílený účet vzniká sloučením v osnově a lze ho zase rozdělit — [Odoo 18 konsolidace](https://www.odoo.com/documentation/18.0/applications/finance/accounting/get_started/consolidation.html).
- **[A]** Kód účtu kontroluje `asset_cash` s více společnostmi; bankovní a pokladní účty tedy nejsou určeny ke sdílení (přečtena podmínka, ne hláška) — [account_account.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_account.py).
- **[A]** Další relevantní PERF PR podle názvu, nečteno: [#285252](https://github.com/odoo/odoo/pull/285252) (`_get_last_sequence_domain`), [#183438](https://github.com/odoo/odoo/pull/183438) (dashboard `_count_results_and_sum_amounts`).
- **[A, starší]** 2019: `child_of` byl odstraněn z multi-company pravidel — [PR #31943](https://github.com/odoo/odoo/pull/31943/files). Výběr aktivních společností zavedl commit [a5b6f31](https://github.com/odoo/odoo/commit/a5b6f31cf28e5381e1c85f66730bcdb55998e643).

### Inferences
- Sdílený partner nebo produkt s hodnotami pro 100 společností má jsonb se 100 klíči, čte se celý a zapisuje se celý. U často měněných polí to znamená větší řádky a více práce pro autovacuum. Bez měření jde o hypotézu; u fondů se týká hlavně sdílených partnerů.
- Index `btree_not_null` pomáhá u `IS NOT NULL`, ne u hledání podle hodnoty v konkrétní společnosti. Filtrování podle company-dependent pole ve velkých tabulkách může vést na sekvenční čtení. Kód ani PR to neměří.
- Sdílené účty snižují počet řádků, ale svazují osnovu fondů dohromady. Je to tedy účetní a metodické rozhodnutí, ne výkonové.

### Gaps
- Nenašel jsem PR se srovnáním výkonu `ir.property` a jsonb.
- Nenašel jsem PR, který sdílené účty zavedl, ani jeho výkonové důvody. Zmínka o account merge nástroji (#177296) je jen v PR #175627.
- Nenašel jsem issue přímo o pomalosti přepínače nebo přihlášení při mnoha společnostech, ale systematické prohledání GitHubu nebylo možné (viz úvod).
- Pro verzi 17 jsem nenašel specifické výkonové PR k více společnostem.

## Doporučuje Odoo S.A. nebo partneři, kdy rozdělit na více databází?

### Takeaway
Oficiální číselnou hranici jsem nenašel. Partneři rozhodují podle sdílených dat, vlastnictví a izolace, ne podle počtu společností. Provozní omezení (jedna záloha, jedna verze, jeden upgrade) jsou pro rozhodnutí průkaznější než výkon.

### Cited Findings
- **[B]** Dokumentace multi-company 19.0 popisuje přepínač, sdílené záznamy a mezipodnikové transakce. V přečtené části nic o výkonu, limitu ani hranici pro rozdělení; nedočteno posledních asi 3 000 znaků a sekce „Use cases“ se v převodu nezobrazila — [Odoo 19 multi-company](https://www.odoo.com/documentation/19.0/applications/general/companies/multi_company.html).
- **[B]** Vývojářská příručka řeší správnost (`check_company`, `with_company`, pravidla), výkonu se nevěnuje — [Multi-company Guidelines](https://www.odoo.com/documentation/19.0/developer/howtos/company.html).
- **[D]** Braincuber: jednu databázi doporučuje, pokud společnosti sdílejí produkty, dodavatele, zákazníky nebo sklady; výjimka jsou zcela odlišná odvětví bez sdílených dat — [Braincuber](https://www.braincuber.com/blog/odoo-multi-company-setup-best-practices).
- **[D]** Pixelmechanics (jen z úryvku vyhledávání): oddělené databáze při různých vlastnících, ničem sdíleném a oddělených release cyklech — [Pixelmechanics](https://www.pixelmechanics.tech/en-int/blog/digitization-blog-2/odoo-multi-tenancy-options-232).
- **[D]** OEC.sh (jen z úryvku vyhledávání): nelze zálohovat jednu společnost bez ostatních, nelze mít různé verze Odoo po společnostech a chybné pravidlo může odhalit data mezi společnostmi; pro externí platící klienty doporučuje alespoň více databází — [OEC.sh](https://oec.sh/guides/odoo-multi-tenant).
- **[D]** Onetribe: hranice konsolidace v produktu je databáze („The boundary is the database“); skupina rozložená do více databází potřebuje reportingovou vrstvu nad nimi — [Onetribe](https://www.onetribeadvisory.com/knowledge-hub/erp/odoo/).

### Inferences
- Výkon sám o sobě pro desítky společností rozdělení neodůvodňuje. Důvodem by byly spíš tyto situace: požadavek na obnovu jednoho fondu z historie, přebírání a předávání fondů mezi administrátory, různá rizika izolace dat nebo různé termíny upgradu.
- Vícedatabázové řešení ale ztrácí jednotné číselníky a vyžaduje řešení společných dat a konsolidace mimo Odoo. Vhodná je varianta se skupinami fondů po databázích, kterou lze zvolit později, pokud modul nebude spoléhat na vazby mezi fondy.

### Gaps
- Veřejná přednáška z Odoo Experience k tomuto tématu nebyla nalezena (hledáno jen webovým vyhledáváním, archiv YouTube jsem neprocházel).
- Oficiální stanovisko Odoo S.A. by se dalo získat jen dotazem na Odoo nebo partnera; Community nemá podporu Odoo, takže cesta vede přes partnera.
- Regulatorní dopady oddělení dat fondů jsem nezkoumal (mimo zadání).

## Jaká jsou opatření: indexy, PostgreSQL, omezení povolených společností, workery?

### Takeaway
Nejlépe podložené jsou: aktuální statistiky (`ANALYZE`), složené nebo částečné indexy podle `company_id` a co nejmenší výběr aktivních společností. Důležitější než všechna ladění je vlastní zátěžový test se syntetickými společnostmi, protože veřejná data pro Odoo 20 neexistují.

### Cited Findings
- **[C]** Částečné indexy: jeden pro velkou společnost, druhý pro všechny ostatní, a složené indexy s `company_id`. Pozor na NULL případ u částečných indexů — [OCA vlákno](https://test.odoo-community.org/groups/contributors-69/re-multi-company-how-many-companies-is-too-many-10520?mode=date).
- **[A]** Statistiky: `ANALYZE` po načtení osnovy zásadně změnil plán (viz PR #290208) — [PR #290208](https://github.com/odoo/odoo/pull/290208).
- **[A]** Odoo 20 už má na `account_move` složený index `(journal_id, company_id, date)` a kód se na něj výslovně odkazuje (dashboard přidává společnosti do dotazu, aby ho využil) — [account_move.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_move.py), [account_journal_dashboard.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_journal_dashboard.py).
- **[A]** Vzor pro vlastní kód: nejdřív zjistit ID společností a do dotazu je předat jako literály, ne jako poddotaz — [PR #286948](https://github.com/odoo/odoo/pull/286948). Dávkovat výpočty přes všechny společnosti, ne je opakovat v cyklu — [PR #287906](https://github.com/odoo/odoo/pull/287906).
- **[A]** Odoo 20 umožňuje vlastní indexy deklarativně přes `models.Index` (použito v core), tedy vlastním addonem, bez zásahu do core — [account_move.py](https://github.com/odoo/odoo/blob/20.0/addons/account/models/account_move.py).
- **[B]** Workery (dokumentace 19.0): teoretické maximum `(#CPU * 2) + 1`, asi 6 souběžných uživatelů na worker, RAM `#worker * (0,8 × 150 MB + 0,2 × 1024 MB)`, ukázka 9 workerů ≈ 3 GB. Ukázková konfigurace pro 4 CPU: `workers = 8`, `max_cron_threads = 1`, `limit_time_cpu = 600`, `limit_time_real = 1200`, `limit_request = 8192`, `limit_memory_soft = 629145600`, `limit_memory_hard = 1677721600`; `postgresql.conf` ukázkově `max_connections = 80` — [Odoo deploy](https://www.odoo.com/documentation/19.0/administration/on_premise/deploy.html). Vzorec nebere v úvahu počet společností.
- **[D]** Obecné tipy dodavatelů: PostgreSQL na samostatném serveru, pooler, ladění autovacuum pro největší tabulky, `pg_stat_statements` a `EXPLAIN ANALYZE` na nejhorší dotazy — [Dixmit](https://www.dixmit.com/en/blog/our-blog-1/my-odoo-is-too-slow-what-can-i-do-51), [Stormatics](https://stormatics.medium.com/improve-odoos-database-performance-by-1000x-22012fb0404c). Čteno jen z úryvků vyhledávání; netestováno pro mnoho společností.
- **[D]** Modul třetí strany na omezení výběru společností existuje, nečetl jsem ho a nedoporučuji ho na základě názvu — [obl_multi_company_restrict](https://apps.odoo.com/apps/modules/17.0/obl_multi_company_restrict).

### Inferences
- **Povolené společnosti (`res.users.company_ids`):** nastavit každému uživateli jen to, co potřebuje. Zmenšuje to `session_info` a rozsah dotazů. Ještě větší účinek má počet aktivních společností, protože pravidla pracují s `env.companies`. U administrátora fondů s přístupem ke všem pomůže výchozí jedna aktivní společnost; cookie `cids` si výběr pamatuje.
- **Statistiky:** po hromadném založení společností nebo importu spustit `ANALYZE` (je to údržba PostgreSQL, ne zápis dat). Při silně nerovnoměrném `company_id` zvážit vyšší `statistics target` pro sloupec. To je běžná technika PostgreSQL, zde bez zdroje z Odoo.
- **Indexy:** přidávat až podle `pg_stat_statements` a `EXPLAIN`, přes vlastní addon. Podle pravidel projektu je to změna schématu, tedy nejdřív souhlas. Částečné indexy podle konkrétní společnosti jsou smysluplné až při výrazném nepoměru mezi fondy.
- **Crony:** samostatné cron workery a plán mimo špičku. Dlouhý cyklus přes 100+ společností může narazit na časové limity; vlastní crony psát dávkově a s průběžným commitem. Konkrétní limit cronů jsem neověřoval.
- **Zakládání:** společnosti zakládat dávkově mimo provoz, ideálně bez modulu `stock`, pokud není potřeba. Pobočky a sdílená osnova jsou výkonově levnější, ale zda je fond smí být pobočkou, je metodická a legislativní otázka, ne výkonová (pobočka přebírá osnovu a kódy kořenové společnosti).
- **Vlastní měření (doporučení):** na testovací databázi založit syntetické společnosti v krocích 10 / 50 / 100 / 200 a na každém kroku měřit: čas založení a instalace osnovy, přihlášení a `session_info`, otevření seznamu dokladů, výpočet NAV, souhrnné výkazy, doby cronů, `pg_stat_statements`, velikost tabulek. Data mít nerovnoměrná (jeden velký a mnoho malých fondů). Vyžaduje to zápis do testovací DB, proto to tento výzkum nespustil.

### Gaps
- Pro Odoo 20 chybí veřejná doporučení k PostgreSQL pro mnoho společností. Pro verzi 20 jsem dokumentaci nasazení nečetl (použita 19.0).
- `db_maxconn` se v přečtené části dokumentace nevyskytuje.
- Partitioning `account_move_line` podle společnosti: nenašel jsem žádný doložený postup pro Odoo. Neověřeno, zda je reálný.
- Účinnost částečných indexů je doložena jen jedním praktikem (2022), bez čísel.
