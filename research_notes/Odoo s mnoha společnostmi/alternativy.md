# Alternativy k „jedna společnost Odoo na fond“ a jejich soulad s českým právem

Stav k 2026-11-07. Poznámky výzkumníka, nejde o právní stanovisko.

Jak bylo ověřováno (platí pro všechny citace níže):
- Zákony jsem četl na zakonyprolidi.cz přes WebFetch. Nástroj vrací výtah a omezuje doslovné citace na 125 znaků, takže delší ustanovení jsou parafráze nebo úryvky, ne celý text.
- Stažení celého textu přes shell bylo zamítnuto. e-sbirka.gov.cz se nenačetla (chyba DNS). **Znění se tedy nepodařilo porovnat s oficiální e-Sbírkou.** Před použitím v dokumentu pro ČNB nebo auditora je potřeba ho ověřit tam.
- Chování Odoo 20 je ověřené přímo ve zdrojovém kódu běžícího kontejneru `odoo-investra-odoo-1` (obraz `odoo:20.0-20261102`), pouze čtením. Označeno „kód Odoo 20“. Dokumentace Odoo je ve verzi 19.
- Stanoviska ČNB jsou výklad dohledu, ne závazný právní předpis.

Zkratky: ZISIF = zákon č. 240/2013 Sb., ZoÚ = zákon č. 563/1991 Sb., ZDP = zákon č. 586/1992 Sb.

## Co právo vyžaduje o odděleném účetnictví: oddělený systém, nebo oddělené záznamy a závěrky?

### Takeaway
Ve všech přečtených předpisech jde o oddělené účetnictví a závěrky, ne o oddělený IT systém. Žádný z nich nepožaduje samostatnou databázi ani software. Podle ČNB je ale podfond samostatná účetní jednotka, zatímco SICAV bez podfondů je jedna jednotka s vnitřním oddělením. Právě tento rozdíl určuje, kde musí být hranice „knihy“.

### Cited Findings

ZISIF (znění 1. 9. 2026 – 31. 12. 2026, verze 15):
- § 114 (nadpis „Účetnictví“): o majetkových poměrech podílového fondu „se vede účetnictví“ „tak, aby umožnilo sestavení účetní závěrky za každý jednotlivý podílový fond.“ — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 164 odst. 1: SICAV bez podfondů „účetně a majetkově odděluje majetek a dluhy ze své investiční činnosti od svého ostatního jmění.“ Podle odst. 2 lze věřitele a akcionáře z investiční činnosti uspokojit jen z tohoto majetku. Podle odst. 3 se práva z investičních akcií vážou jen k němu. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 164a: SICAV bez podfondů může z investičního majetku a dluhů vytvořit podfondy, pokud to stanovy dovolují. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 165 odst. 1: „Podfond je účetně a majetkově oddělená část jejího jmění“ a účetnictví se vede „tak, aby umožnilo sestavení účetní závěrky za každý jednotlivý podfond.“ — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 165 odst. 4: majetek podfondu „nelze použít ke splnění dluhu, který není dluhem téhož podfondu.“ — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 187: závěrku investičního fondu a jeho jednotlivých podfondů ověřuje auditor. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- § 38 odst. 1 písm. a): vedení účetnictví je činnost administrace. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)

ZoÚ (znění 1. 1. 2026 – 9. 1. 2028, verze 40):
- § 1 odst. 2 písm. k): účetní jednotkou jsou „investiční fondy bez právní osobnosti“. Písm. l): ti, kterým povinnost sestavit závěrku stanoví zvláštní předpis, „nebo které jsou účetní jednotkou podle zvláštního právního předpisu.“ Slovo „podfond“ se v přečtených částech ZoÚ nevyskytuje. — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 4 odst. 9: „Účetní jednotky jsou povinny vést jedno účetnictví za účetní jednotku jako celek.“ — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 4a odst. 2: za vedení účetnictví ostatních investičních fondů bez právní osobnosti odpovídají administrátor a obhospodařovatel společně a nerozdílně. — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 24a odst. 1 a 2: měnou účetnictví je česká měna, nebo jiná měna, pokud je funkční měnou účetní jednotky a jde o euro, americký dolar nebo britskou libru. Funkční měna je „měna primárního ekonomického prostředí, ve kterém účetní jednotka působí.“ — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 24a odst. 4: „Měnu účetnictví lze změnit pouze k prvnímu dni účetního období.“ Návrat z jiné měny na českou je možný, jen když jiná měna přestane být funkční měnou. — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 13 odst. 3: účetní jednotky nesmějí zřizovat účty mimo účtový rozvrh a účetní knihy. § 19 odst. 1: závěrka se sestavuje k rozvahovému dni, kdy se uzavírají knihy. — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)
- § 31 odst. 2: závěrka a výroční zpráva se uschovávají 10 let, doklady a knihy 5 let. § 33 odst. 9: povinnost chránit účetní záznamy. — [ZoÚ](https://www.zakonyprolidi.cz/cs/1991-563)

Výklad ČNB:
- RS2024-16 (19. 4. 2024): SICAV je účetní jednotka podle § 1 odst. 2 písm. a) ZoÚ, podfond podle písm. l) ve spojení s § 165 odst. 1 ZISIF. Jde o dvě samostatné účetní jednotky, které mohou mít odlišné účetní období. Zpráva podfondu nemusí být součástí zprávy SICAV. Podfond nezakládá do sbírky listin. — [ČNB RS2024-16](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2024-16)
- RS2025-20 (22. 7. 2025): u SICAV s podfondy se majetek podfondů do bilanční sumy ani obratu SICAV nezapočítává, bere se jen zakladatelská část. U SICAV bez podfondů je účetní jednotkou celý SICAV. — [ČNB RS2025-20](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2025-20)
- RS2018-04 (23. 3. 2018): SICAV bez podfondů zůstává jedinou účetní jednotkou, oddělení je ve vnitřním účetnictví a nevzniká nová účetní jednotka. Neopodstatněné převody mezi částmi mohou zkreslit výkazy. — [ČNB RS2018-04](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2018-04)
- RS2025-27 (26. 11. 2025): podfond je v poznámce popsán jako samostatná účetní jednotka s vlastní účetní a daňovou subjektivitou. Při zrušení jediného podfondu bez likvidace jdou majetek a dluhy do investiční části SICAV, ne do zakladatelského jmění. Porušení oddělení může být přestupkem podle § 599 odst. 1 písm. b) ZISIF. — [ČNB RS2025-27](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2025-27)

Další předpisy:
- ZDP § 17 odst. 1 písm. c) a d): poplatníkem je podílový fond i „podfond investičního fondu“. Nástroj neukázal verzi znění, aktuálnost je tedy potřeba ověřit. — [ZDP](https://www.zakonyprolidi.cz/cs/1992-586)
- Nařízení (EU) 231/2013, čl. 59 odst. 1: záznamy se vedou tak, aby „all assets and liabilities of the AIF can be directly identified at all times“. Dále: „If an AIF has different investment compartments, separate accounts shall be maintained for those compartments.“ — [EUR-Lex 231/2013](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0231)
- Vyhláška 501/2002 Sb. (zobrazena verze 13, 1. 1. 2024): v přečtených 100 000 znacích se „podfond“ ani „podílový fond“ nevyskytuje. Investiční fondy jsou v § 2 odst. 1 písm. d) a v § 55, § 62. — [Vyhláška 501/2002 Sb.](https://www.zakonyprolidi.cz/cs/2002-501)

### Inferences
- **Oddělený systém se nevyžaduje.** Slova jako „účetně oddělená“, „sestavení účetní závěrky“ a „separate accounts“ míří na účetní výstup a identifikovatelnost. Sdílená databáze ani software tomu nebrání, pokud je každá kniha úplná a průkazná. Je to můj výklad, ne výslovné tvrzení předpisu.
- **Účetní jednotka není totéž co společnost Odoo.** Mapování podle ČNB:

| Subjekt | Účetní jednotka | Vhodné mapování |
|---|---|---|
| Podílový fond | ano (§ 1 odst. 2 písm. k) ZoÚ) | vlastní kniha |
| Podfond SICAV | ano (ČNB, písm. l) ZoÚ) | vlastní kniha |
| SICAV s podfondy (zakladatelská část) | ano, bez majetku podfondů | vlastní kniha |
| SICAV bez podfondů | jedna jednotka, dvě části | jedna kniha a pole části |

- **Rozhodnutí v deníku jsou tímto podložená.** „Kniha = společnost“ (2026-11-04) sedí na podfondy a podílové fondy. „Části SICAV“ (2026-11-05) sedí na SICAV bez podfondů. Záznamy spolu nekolidují, jen deník výslovně neříká, že první platí pro SICAV s podfondy a druhý pro SICAV bez nich. Doporučuji to upřesnit (návrh).
- **Pozor na § 4 odst. 9 ZoÚ.** Jedna účetní jednotka nesmí být rozdělena do více Odoo společností. Investiční a zakladatelskou část SICAV bez podfondů proto nedělit na dvě společnosti.
- **Výkaz „za celek“ u SICAV s podfondy nemá oporu v přečtených zdrojích jako povinná závěrka.** Majetek podfondů do závěrky SICAV nevstupuje (RS2025-20). Záznam „Části SICAV“ s výkazy „za celek“ se týká SICAV s částmi. Podfondy se tedy nemusejí konsolidovat do SICAV kvůli závěrce, přehled za celek je jen manažerský. Jiné povinnosti (například výkazy ČNB) jsem neověřil.
- **Funkční měna podfondu.** § 24a mluví o funkční měně „účetní jednotky“. Je-li podfond účetní jednotkou, plyne z toho, že může mít vlastní funkční měnu odlišnou od SICAV (EUR podfond pod CZK SICAV). Žádný přečtený zdroj to neříká výslovně, je to odvození. Zákonná jiná měna je jen EUR, USD nebo GBP. Podfond v CHF by tedy podle § 24a možný nebyl, pokud jiný předpis nestanoví jinak.
- **Restrukturalizace je reálný případ.** § 164a (vytvoření podfondů) a RS2025-27 (zrušení podfondu) mění mapování mezi „pole části“ a „samostatná kniha“. Systém proto potřebuje postup převodu zůstatků mezi knihami.

### Gaps
- Autoritativní výklad, že podfond může mít vlastní funkční měnu odlišnou od SICAV, jsem nenašel. **Ověřit u auditora nebo ČNB.**
- RS2018-04 podle výtahu odkazuje pro vnitřní rozdělení na § 14 odst. 3 ZoÚ, ale současný § 14 odst. 3 upravuje účtový rozvrh. Může jít o nepřesnost výtahu nebo o změnu číslování, rozpor jsem nevyřešil.
- Zda čl. 59 nařízení 231/2013 dopadá i na správce pod limitem podle § 15 ZISIF, jsem neověřil.
- Vyhlášku 501/2002 Sb. jsem nepřečetl celou (zbývá přibližně 27 000 znaků) a zobrazená verze je z 1. 1. 2024. Zda platí novější znění, neověřeno.
- ZDP verze neověřena. Rozhodnutí NSS o sazbě podfondu jsem jen viděl ve výsledcích hledání, nečetl jsem je.

## Mění novela 130/2026 Sb. tyto paragrafy? Jaké změny se chystají?

### Takeaway
Novela 130/2026 Sb. podle přečteného textu § 114, § 164, § 165 ZISIF ani ZoÚ nemění, jde ale o čtení přes výtah, ne o úplnou kontrolu bod po bodu. Pro architekturu jsou důležitá nová pravidla rozdělení fondu a pověřování administrací. Nový zákon o účetnictví je stále jen návrh.

### Cited Findings
- Zákon č. 130/2026 Sb.: schválen 8. 7. 2026, platnost 23. 7. 2026, účinnost 1. 9. 2026. — [130/2026 Sb.](https://www.zakonyprolidi.cz/cs/2026-130)
- Výjimka z účinnosti: čl. I body 107, 108, 110, 112 až 115 a 160 až 162 nabývají účinnosti 16. dubna 2027 (čl. VIII). — [130/2026 Sb.](https://www.zakonyprolidi.cz/cs/2026-130)
- V obou přečtených částech novely (celý text po částech) nebyl nalezen novelizační bod k § 114, § 164 ani § 165. Mění se ZISIF, zákon č. 15/1998 Sb., zákon č. 256/2004 Sb., zákon č. 634/2004 Sb. a zákon č. 84/2024 Sb. ZoÚ se nemění. — [130/2026 Sb.](https://www.zakonyprolidi.cz/cs/2026-130)
- Bod 95 přepracovává § 373 (přeměna podfondu), body 96 a 101 přidávají rozdělení podílového fondu (§ 381, § 413a–413h). Podle nového § 413g odst. 3 se část jmění rozdělovaného fondu z účetního hlediska považuje za jmění přejímajícího fondu. — [130/2026 Sb.](https://www.zakonyprolidi.cz/cs/2026-130)
- Bod 37 vkládá § 47b (střet zájmů administrátora), bod 38 § 48a a 48b (vedoucí osoby administrátora), bod 40 § 53a (pověřování administrací). — [130/2026 Sb.](https://www.zakonyprolidi.cz/cs/2026-130)
- Zobrazené znění ZISIF končí 31. 12. 2026, od 1. 1. 2027 tedy nastává další změna. Stránka mi neukázala jakou. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240)
- **Návrh, ne platné právo:** nový zákon o účetnictví vláda projednala v listopadu 2025 a míří do Sněmovny. — [EY, 12/2025](https://www.ey.com/cs_cz/technical/tax/tax-alerts/2025/12/novy-zakon-o-ucetnictvi-a-zmenovy-zakon-miri-do-poslanecke-snemovny). Plánovaná účinnost je podle sekundárních zdrojů 1. 1. 2028, prezentace VŠE uvádí 1. 1. 2028/9. — [VŠE, 3/2026](https://ffu.vse.cz/wp-content/uploads/BOVA-Mejzlik-novy-ZoU-19-03-2026.pdf)

### Inferences
- Rozdělení podílového fondu (§ 413a–413h) a přeměna podfondu jsou další důvod mít postup „nová kniha + převod části zůstatků“. V modelu kniha = společnost je to nová společnost a převodní doklady. U dimenze by šlo jen o přeznačení řádků, ale tato výhoda nevyváží ostatní nevýhody.
- § 53a se může týkat role Investra Services, pokud bude administraci vykonávat na základě pověření. Na volbu databáze přímý dopad nečtu, jde o téma k posouzení právníkem.

### Gaps
- Které paragrafy se skrývají za body s účinností 16. 4. 2027, jsem nedohledal.
- Co se v ZISIF mění k 1. 1. 2027, není ověřeno. **Zkontrolovat v e-Sbírce před závěrem.**
- Znění ZoÚ končí k 9. 1. 2028, důvod jsem nezjistil. Datum prvního čtení nového zákona se ve zdrojích liší (březen vs. červen 2026), stav ověřit u Poslanecké sněmovny nebo MF. Dopad návrhu na účetní jednotky typu podfond neznám.

## Jak si alternativy vedou po technické stránce v Odoo 20?

### Takeaway
Větve a analytika/dimenze neobstojí: nemohou nést jinou funkční měnu a větev ani jiné účetní období, což ČNB u podfondu výslovně připouští. Reálně se rozhoduje mezi jednou databází a databází na klienta. Rozdíl je v izolaci a obnově proti přehledu a nákladům na provoz.

### Cited Findings

Fakta pro větve:
- `res.company._get_company_root_delegated_field_names` vrací `currency_id`, modul account přidává `fiscalyear_last_day`, `fiscalyear_last_month`, `account_storno`, `tax_exigibility`. Tato pole jsou na větvích jen ke čtení a kopírují se z kořene. — kód Odoo 20: `base/models/res_company.py` ř. 164–171, `account/models/company.py` ř. 401–407
- Pro větve je `user_hard_lock_date` maximum přes všechny `parent_ids`, měkké uzávěrky procházejí také `parent_ids`. Uzávěrka rodiče tedy platí i pro větve. — kód Odoo 20: `account/models/company.py` ř. 571–577, 759–781
- Deník a daně mají `_check_company_domain = check_company_domain_parent_of`, takže větev smí použít záznamy rodiče. — kód Odoo 20: `account/models/account_journal.py` ř. 48, `account_tax.py` ř. 28
- „Independent subsidiaries should be created as additional companies, not branches.“ Podle dokumentace nelze hlavní společnost později převést na větev. — [Odoo 19 Companies](https://www.odoo.com/documentation/19.0/applications/general/companies.html)

Fakta pro samostatné společnosti:
- Měna je na `res.company`, uzávěrky také (`fiscalyear_lock_date`, `tax_lock_date`, `sale_lock_date`, `purchase_lock_date`, `hard_lock_date`). `hard_lock_date` nejde snížit ani zrušit. — kód Odoo 20: `base/models/res_company.py` ř. 109, `account/models/company.py` ř. 61–100, 711–717
- `restrictive_audit_trail` je nastavení na společnosti (zákaz mazání logů k účetním položkám). `restrict_mode_hash_table` je na deníku. — kód Odoo 20: `account/models/company.py` ř. 280, `account_journal.py` ř. 137
- Číselná řada dokladu se hledá podle `journal_id`, ne podle společnosti. — kód Odoo 20: `account/models/account_move.py` ř. 4334
- Izolace je pravidlo `[('company_id', 'in', company_ids)]` na `account.move` a `account.move.line`, tedy aplikační vrstva. — kód Odoo 20: `account/security/ir.access.csv` ř. 33, 37
- Účet má `company_ids` (Many2many) a kód `code_store` závislý na společnosti, účet tedy může sdílet více společností. — kód Odoo 20: `account/models/account_account.py` ř. 47, 120
- Kontakty a produkty jsou ve výchozím stavu sdílené. „Leave the field blank to make the record accessible to all companies.“ — [Odoo 19 Multi-company](https://www.odoo.com/documentation/19.0/applications/general/companies/multi_company.html)
- Kontejner Community neobsahuje `account_reports`, `account_consolidation` ani modul mezipodnikových pravidel, je jen `account_payment_interco`. — kód Odoo 20: výpis addons

Fakta pro analytiku a dimenzi:
- Měna analytické položky je `related="company_id.currency_id"`, analytika tedy nenese druhou funkční měnu. — kód Odoo 20: `analytic/models/analytic_line.py` ř. 214–215
- `_check_balanced` kontroluje vyrovnanost dokladu. Vyrovnanost po dimenzi jsem ve standardu nehledal. — kód Odoo 20: `account/models/account_move.py` ř. 2945

Fakta pro více databází:
- `-i` a `-u` nelze použít s více databázemi v `db_name`: „Cannot use -i/--init or -u/--update with multiple databases“. Upgrade se tedy spouští po jedné databázi. — kód Odoo 20: `odoo/tools/config.py` ř. 762–763
- `--db-filter` a `--no-database-list` existují pro provoz více databází v jedné instanci. — kód Odoo 20: `odoo/tools/config.py` ř. 313, 454
- Staré endpointy `/xmlrpc`, `/xmlrpc/2`, `/jsonrpc` jsou zastaralé „and scheduled for removal in Odoo 22“. Náhrada je `/json/2`. — kód Odoo 20: `rpc/controllers/__init__.py`, `rpc/controllers/json2.py`

Fakta z projektu:
- `investra.entity` má vlastní `parent_id` (Nadřazená kniha), `founder_id` a vazbu 1:1 na společnost. Podfond musí mít nadřazený SICAV. — `addons/custom/investra_entity/models/entity.py` ř. 18, 40–43, 52–57
- Na více společnostech závisejí záznamy: Fakturace úplat (úplaty automaticky u obou stran), Dashboard (přehled napříč fondy), Databáze (jedna pro všechny zakladatele), Číselník fondů a tříd. — `docs/rozhodnuti.md`
- Evidence držitelů je v IS, ne v Odoo. — `docs/rozhodnuti.md`

### Inferences

Srovnávací tabulka (hodnocení je můj úsudek na základě faktů výše):

| Kritérium | 1. Společnost na fond, jedna DB | 2. Větve | 3. Jedna společnost + dimenze | 4. Více DB (fond/skupina/klient) | 5. Hybrid: DB na klienta, uvnitř společnosti |
|---|---|---|---|---|---|
| Oddělené závěrky | Ano, nativně podle společnosti; v Community vlastní výkazy | Formálně část rodiče, vlastní výkazy nutné | Jen vlastním kódem na každý výkaz | Ano | Ano |
| Jiná funkční měna | Ano | **Ne** (`currency_id` z kořene) | **Ne** | Ano | Ano |
| Jiné účetní období | Ano | **Ne** | **Ne** bez vlastního řešení | Ano | Ano |
| Číselné řady | Ano, deník ve společnosti | Možné, ale lze sdílet s rodičem | Vlastní deníky na fond, jinak jedna řada | Ano | Ano |
| Uzávěrky | Na knihu | Uzávěrka rodiče se přenáší | **Jedna pro všechny** | Na knihu | Na knihu |
| Audit trail | Na společnost | Nastavení rodiče a větve, ověřit | Společný, nelze dělit | Nejsilnější oddělení | Silné mezi klienty |
| Izolace přístupu | Aplikační pravidlo | Aplikační, větev vidí záznamy rodiče | Vlastní pravidla, nejslabší | Skutečná na úrovni DB | Skutečná mezi klienty |
| Přehled napříč fondy | Snadný | Nejsnazší | Nejsnazší | Nutný sklad dat nebo API | Snadný u klienta, mezi klienty API |
| Nasazení a upgrade | 1× | 1× | 1× | N×, po jedné DB | Počet klientů × |
| Záloha a obnova jednoho fondu | **Ne**, jen celá DB; výběr vlastní extrakcí | Ne | Ne | Ano | Na úrovni klienta |
| Předání fondu jinému administrátorovi | Export za společnost | Obtížné | Nejtěžší | Nejsnazší technicky | Export za společnost |
| Sdílené číselníky (nástroje, ceny, kurzy) | Sdílené | Sdílené | Sdílené | Synchronizace | Synchronizace mezi klienty |
| Úplaty mezi společnostmi | Automaticky v jedné DB | Automaticky | Není mezi společnostmi | Integrace přes API | V klientovi ano, se Services přes API |

Selhání jednotlivých variant:
1. **Společnost na fond:** chyba v `sudo()` nebo sdílený záznam ukáže data jiného fondu. Vadná migrace nebo skript zasáhne všechny fondy. Obnova po chybě v jednom fondu vrátí všechny fondy, nebo vyžaduje obnovu do pomocné DB a ruční přenos. S růstem počtu společností se zpomaluje UI a nastavení (riziko je už v `docs/otevrene-body.md`, Velký počet společností). Spolehlivá čísla výkonu pro stovky společností v Odoo jsem nenašel, je nutné změřit.
2. **Větve:** nejde založit EUR podfond pod CZK SICAV. Uzávěrka SICAV by zamkla podfond. Nelze jiné období, které ČNB připouští. Dokumentace varuje, že jde o dělení jednoho podniku, což odporuje samostatné účetní jednotce. Pozdější převod je obtížný. **Vyřazuji.** Hierarchii SICAV → podfond už řeší `investra.entity.parent_id` bez `res.company.parent_id`.
3. **Dimenze:** jedna chybně označená položka míchá fondy, přičemž § 165 odst. 4 ZISIF zakazuje plnit dluhy jiného podfondu. Doklad vyrovnaný celkově nemusí být vyrovnaný v dimenzi. Jedna uzávěrka a jedna měna blokují různá ocenění. Porušuje ducha § 4 odst. 9 ZoÚ (jedno účetnictví za jednotku), protože jedna kniha by obsahovala mnoho jednotek. **Vyřazuji pro samostatné účetní jednotky.** Dimenze je správná jen uvnitř jedné jednotky, tedy pro části SICAV a třídy.
4. **DB na fond:** provoz roste s počtem fondů (upgrade, testy, zálohy, monitoring). Rozcházejí se verze modulů. Číselníky se rozjíždějí. Přehled napříč fondy i dashboard se musí stavět zvlášť. Úplaty vznikající automaticky na obou stranách by musely být integrace s rizikem nesouladu. Pro desítky malých fondů je to nepřiměřené.
5. **Hybrid:** vyžaduje rozhodnout, kde je hranice (zakladatel, obhospodařovatel, klient). Investra Services by byla v jiné DB než fondy, takže fakturace úplat potřebuje integraci. Přesun fondu mezi skupinami je stejný jako migrace mezi systémy. Přidává provoz až se zvyšováním počtu klientů, ale proporcionálně.

Dopad na zvláštní požadavky:
- **Předání fondu:** převzímající administrátor pravděpodobně Odoo nemá. Dump databáze mu tedy nepomůže a potřebný je export čitelný bez Odoo, který už projekt rozhodl (Pravidla archivace). Výhoda více databází je proto u předání menší, než se zdá.
- **Audit trail:** u dimenze i větví je slabší průkaznost, že kniha je úplná. U společnosti je to silnější, protože deníky, řady, uzávěrky i rozvrh patří jedné jednotce.
- **Izolace:** rozdíl mezi 1 a 4 je kvalitativní. U 1 ji zajišťuje kód (pravidla a vlastní moduly), u 4 hranice databáze. Vlastní moduly používají `sudo()`, například při zakládání knihy (`entity.py`), takže test izolace je povinný.

### Gaps
- Výkon Odoo 20 při desítkách až stovkách společností: nenašel jsem spolehlivý zdroj, jen deklarace. Změřit v etapě zkušebních knih.
- Dokumentace „Branch accounting“ se mi nepodařilo načíst (URL vrátila 404), chování větví je z kódu Odoo 20 a dokumentace 19.
- Zda větev může mít vlastní `restrictive_audit_trail` a jak se chová, jsem nezkoumal.
- Nezkoumal jsem OCA moduly pro konsolidaci nebo mezipodnikové účtování v Community pro verzi 20.

## Jsou v DORA nebo GDPR požadavky relevantní pro jednu sdílenou databázi?

### Takeaway
Ani DORA, RTS 2024/1774, ani GDPR ve výtazích, které jsem přečetl, nevyžadují oddělení dat po fondech nebo klientech ani samostatné databáze. Sdílená DB je dovolená, ale musí obstát v obnově, přístupech a posouzení rizika. Jedna DB koncentruje riziko a tento argument je třeba zdokumentovat.

### Cited Findings

Působnost DORA:
- Čl. 2 odst. 1 písm. k) a l) zahrnují správce alternativních investičních fondů a správcovské společnosti. Čl. 2 odst. 3 písm. a) vyjímá správce podle čl. 3 odst. 2 směrnice 2011/61/EU. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- ČNB: DORA se vztahuje na správce i samosprávné fondy (§ 8 odst. 1 ZISIF). Na podfond samotný se nevztahuje. Mikropodnik má méně než 10 osob a obrat nebo bilanční sumu nejvýše 2 mil. EUR (čl. 3 bod 60). — [ČNB RS2025-20](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2025-20)

Požadavky DORA:
- Čl. 4 odst. 1: proporcionalita podle velikosti a rizikového profilu. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- Čl. 9 odst. 4: ochrana dat „including those of their customers, where applicable“ (písm. a), infrastruktura, kterou lze „instantaneously severed or segmented in order to minimise and prevent contagion“ (písm. b), omezení „physical or logical access to information assets“ (písm. c). — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- Čl. 11 odst. 5 a 6: redundance kritických komponent, testování plánů. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- Čl. 12 odst. 1 a), 3, 4, 6: rozsah záloh, obnovovací systémy „physically and logically segregated from the source ICT system“, redundantní kapacity (kromě mikropodniků), cíle doby a bodu obnovy pro každou funkci. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- Čl. 28 odst. 3 a 8: registr ICT smluv, strategie ukončení pro služby podporující kritické nebo důležité funkce. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- Čl. 30 odst. 2 písm. b), c), d): smlouva uvede lokace zpracování, ochranu dat a přístup, obnovu a vrácení dat ve snadno přístupném formátu. Čl. 30 odst. 3 písm. f): exit strategie s přechodným obdobím. — [DORA](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2554)
- RTS 2024/1774: čl. 8 odst. 2 písm. b) bod v (oddělení produkce od vývoje a testů), čl. 13 písm. a) („segregation and segmentation of ICT systems and networks“), čl. 16 odst. 5 písm. a) (mimo produkci jen anonymizovaná, pseudonymizovaná nebo náhodná data), čl. 21 písm. a) (nejmenší nutná oprávnění), čl. 6 odst. 2 písm. a) (šifrování). Výtah neobsahuje požadavek oddělovat data mezi klienty nebo fondy. — [RTS 2024/1774](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1774)

GDPR:
- Čl. 5 odst. 1 písm. f) a odst. 2 (bezpečnost, odpovědnost), čl. 25 odst. 2 (ve výchozím nastavení jen nezbytné údaje). — [GDPR](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679)
- Čl. 28 odst. 3 písm. a) a g): zpracovatel jedná podle pokynů a na konci služby „deletes or returns all the personal data“ podle volby správce. — [GDPR](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679)
- Čl. 32 odst. 1 písm. b), c), d): důvěrnost, integrita, dostupnost a odolnost, včasná obnova, pravidelné testování. Žádné z těchto ustanovení nevyžaduje oddělené databáze na správce. — [GDPR](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679)

### Inferences
- Jedna databáze je bod společného selhání a výpadek zasáhne všechny fondy. Protože projekt nebude mít náhradní aplikaci (rozhodnutí Kontinuita), musí RTO a RPO podle čl. 12 odst. 6 pokrýt scénář „celá DB je špatně“ i „data jednoho fondu jsou špatně“.
- Čl. 9 odst. 4 písm. b) se týká sítě a infrastruktury. Nevykládal bych ho jako požadavek na databázi na fond, ale auditor může chtít zdůvodnění.
- Čl. 9 odst. 4 písm. c) a RTS čl. 21 lze splnit aplikačními právy, ale je třeba dokázat testem. Správci DB a Odoo admin vidí vše, proto jsou nutná oddělená oprávnění a logování.
- Dopad GDPR je omezený, protože držitelé jsou v IS. V Odoo zůstávají protistrany, zaměstnanci a kontaktní osoby. Sdílené `res.partner` je přesto potřeba zkontrolovat. Pokud Investra zpracovává data cizích zakladatelů jako zpracovatel, čl. 28 odst. 3 písm. g) vyžaduje možnost vrátit nebo vymazat data po správci. V jedné DB to znamená export a řízené vymazání, a to narazí na zákonnou úschovu (§ 31 ZoÚ) i zákaz mazání historie. Role správce a zpracovatele jsem neposuzoval.
- Obnova jen jednoho fondu není požadavek zákona, ale praktické riziko. Vyřešit ji lze obnovou do oddělené pomocné DB a nacvičeným postupem.

### Gaps
- Zda se na Investru vztahuje DORA v plném rozsahu, závisí na tom, zda bude správcem nad limitem, nebo podle § 15 ZISIF. RS2025-20 § 15 výslovně neřeší. **Ověřit u ČNB nebo právníka.** Je to již otevřený bod Dopad DORA.
- Postavení Investra Services jako poskytovatele ICT služeb v rámci skupiny jsem neověřoval.
- Výtah RTS uváděl i čl. 40 (roční test záloh), který je podle mého chápání ve zjednodušeném režimu. Neověřeno, proto jej nepoužívám.
- Výklad, že sdílená databáze nemá vadu podle DORA, je negativní zjištění z výtahů, ne stanovisko. Pokyny ESAs, případná stanoviska ČNB a EDPB k multi-tenant řešením jsem nehledal. **Posoudit auditorem nebo compliance.**
- ZISIF a vyhlášky k organizaci, řízení rizik a ochraně informací obhospodařovatele jsem nečetl, tedy možné národní požadavky navíc jsou neověřené.

## Co znamenají licence a hosting pro mnoho databází proti mnoha společnostem?

### Takeaway
V Community je počet databází i společností licenčně bez vlivu, platí se jen provoz. U Enterprise se platí za uživatele a více společností vyžaduje plán Custom, který je stejně nutný pro vlastní moduly a pro hosting mimo Odoo Online. Odoo.sh nese riziko smlouvy kvůli negarantované lokaci dat.

### Cited Findings
- Modul `account` v Community má licenci LGPL-3. — kód Odoo 20: `account/__manifest__.py` ř. 147
- Plán Standard: 14,90 / 18,60 EUR na uživatele a měsíc, pouze Odoo Online. Plán Custom: 27,90 / 33,90 EUR, Odoo Online, Odoo.sh nebo vlastní hosting. Stránka neukazuje, která částka je roční a která měsíční, ani datum ceníku. — [Odoo Pricing](https://www.odoo.com/pricing)
- Custom je nutný pro více společností v jedné databázi, vlastní vývoj, externí API, Studio, Odoo.sh a vlastní hosting. — [Odoo Pricing](https://www.odoo.com/pricing)
- Zapnutí více společností na plánu Standard vyvolá přechod na plán Custom. — [Odoo 19 Multi-company](https://www.odoo.com/documentation/19.0/applications/general/companies/multi_company.html)
- Poplatky jsou „based on the number of Users, Light Users and the Subscription Plan“. Smlouva v poplatcích databáze nezmiňuje, u Covered Extra Modules se počítají řádky kódu. Při vlastním hostingu musí zákazník umožnit Odoo ověření užívání. — [Odoo Enterprise Agreement](https://www.odoo.com/documentation/19.0/legal/terms/enterprise.html)
- Odoo.sh: hosting je placen podle workerů, úložiště a stagingů, „hosting price does not include the enterprise licence“. — [Odoo.sh Pricing](https://www.odoo.sh/pricing)
- Odoo.sh: předplatné Enterprise musí Odoo.sh zahrnovat. Komunita není zmíněna. Stránka popisuje jednu produkční větev a databázi. — [Odoo.sh FAQ](https://www.odoo.sh/faq)
- Odoo.sh zálohy: 14 úplných záloh, až 3 měsíce. Lokality jsou „not contractually guaranteed“, změna může nastat bez upozornění, datacentrum je i v Belgii. — [Odoo.sh FAQ](https://www.odoo.sh/faq)

### Inferences
- **Community, vlastní hosting:** cena více databází je čistě provoz a práce (upgrade po jedné, zálohy, monitoring, testy). Licenční rozdíl nulový.
- **Enterprise, vlastní hosting nebo Odoo.sh:** projekt má vlastní moduly, takže je nutný Custom bez ohledu na variantu. Více společností tedy cenu nezvyšuje. Účetní přistupující do více databází může být počítán opakovaně, viz Gaps. Hybrid s účetním v 5 databázích by tak mohl zvýšit licenci.
- **Odoo.sh a DORA:** věta „not contractually guaranteed“ jde proti čl. 30 odst. 2 písm. b) DORA, který žádá lokace ve smlouvě a předchozí oznámení změny. Může to řešit jiná smlouva, je to tedy bod k ověření, nikoli závěr. Totéž platí pro otevřený bod Hosting.
- Pokud Odoo.sh skutečně pracuje s jednou produkční DB na projekt, stojí každá další DB další projekt. Tím by se hybrid ještě prodražil.

### Gaps
- Zda je licence za uživatele počítána zvlášť za každou databázi: smlouva to neříká přímo. **Vyžádat písemně od Odoo nebo partnera.**
- Počet produkčních DB na projekt Odoo.sh a podpora Community na Odoo.sh: stránky neuvádějí. Známý model (jen Enterprise) je můj předpoklad.
- Text licenčních podmínek je ve verzi 19. Aktuální podmínky pro Odoo 20 neověřeny. Ceník bez data.

## Kdy je která alternativa správná a co doporučit?

### Takeaway
**Návrh:** ponechat variantu 1 jako výchozí a výslovně ji omezit na samostatné účetní jednotky, připravit ji na pozdější přechod na hybrid 5 a stanovit, co přechod spustí. Varianty 2 a 3 pro knihy fondů vyřadit. Zákon žádnou z variant 1, 4, 5 nevylučuje, rozhoduje provoz a riziko.

### Cited Findings
- Odoo doporučuje samostatné společnosti pro nezávislé dceřiné společnosti, větve jen pro dělení podniku. — [Odoo 19 Companies](https://www.odoo.com/documentation/19.0/applications/general/companies.html)
- Zákonné minimum je oddělené účetnictví umožňující závěrku za každý fond a podfond. — [ZISIF](https://www.zakonyprolidi.cz/cs/2013-240). Podfond je samostatná účetní jednotka. — [ČNB RS2024-16](https://www.cnb.cz/cs/dohled-financni-trh/legislativni-zakladna/stanoviska-k-regulaci-financniho-trhu/RS2024-16)
- Deník: jedna databáze pro všechny zakladatele, Kniha = společnost se má ověřit v etapě zkušebních knih. Registr rizik: velký počet společností. — `docs/rozhodnuti.md`, `docs/otevrene-body.md`

### Inferences

Kdy je která varianta správná:

| Varianta | Správná, když | Nevhodná, když |
|---|---|---|
| 1. Společnost na fond, jedna DB | Jeden provozovatel, jeden tým účetních, společný bezpečnostní režim; důležité jsou sdílené číselníky, úplaty a přehled napříč fondy | Klient nebo smlouva vyžaduje oddělení dat; různé cykly upgradu |
| 2. Větve | Jedna právnická osoba a jedna účetní jednotka s provozovnami, stejná měna a stejné období | Jakákoli samostatná účetní jednotka, tedy **všechny fondy a podfondy** |
| 3. Dimenze | Uvnitř jedné účetní jednotky: části SICAV bez podfondů, třídy | Pro více účetních jednotek |
| 4. DB na fond | Výjimečně jeden fond s přísným oddělením nebo plánovaným odprodejem; DB na skupinu fondů je varianta 5 | Běžný stav desítek fondů |
| 5. Hybrid: DB na klienta | Cizí zakladatelé nebo administrace pro třetí strany se smluvním oddělením, různé hostingové nároky, odlišné verze | Jediný provozovatel a malý počet fondů, protože navýší provoz bez zisku |

Doporučený postup (návrh, rozhoduje uživatel):
1. **Zpřesnit deník:** fond a podfond = samostatná společnost, SICAV s podfondy = vlastní společnost pro zakladatelskou část, SICAV bez podfondů = jedna společnost s polem části. Řešení zůstává R do ověření v etapě zkušebních knih.
2. **Nepoužívat `res.company.parent_id`.** Hierarchii drží `investra.entity.parent_id`, `founder_id` může být budoucí hranice databáze.
3. **Dělat knihy přenositelné:** stabilní externí identifikátory, žádné vazby mezi knihami bez důvodu, sdílené číselníky s přirozeným klíčem (například ISIN), export knihy čitelný bez Odoo. Přechod na hybrid pak nebude přepis.
4. **Doplnit do zkušebních knih měřitelná kritéria:** výkon při realistickém počtu společností, automatický test izolace (uživatel knihy A nevidí knihu B, včetně kódu se `sudo()`), nácvik obnovy celé DB i obnovy jedné knihy do pomocné DB, RTO a RPO proti DORA, export za knihu.
5. **Spouštěče přechodu na hybrid:** požadavek klienta nebo auditora na oddělení databází, administrace pro třetí strany s povinností vrátit data, jiný hosting nebo jurisdikce, měřený výkon pod stanovenou hranici, nesplnitelné RTO obnovy. Hranici počtu společností nelze ze zdrojů určit, musí vzejít z měření.
6. **Předem počítat s tím, že Investra Services by při hybridu zůstala mimo DB fondů.** Automatické úplaty pak vyžadují integraci přes `/json/2`.

Co předložit auditorovi, právníkovi nebo ČNB:
- Vlastní funkční měna podfondu odlišná od SICAV a její dopad na výkazy ČNB (auditor, ČNB).
- Rozsah DORA pro Investru a to, zda jedna sdílená DB potřebuje zdůvodnění v registru rizik (compliance, ČNB).
- Soulad se žádostí o povolení, pokud se popisuje oddělení dat (právník, viz otevřený bod Soulad s žádostí o povolení).

### Gaps
- Nemám data o očekávaném počtu fondů, zakladatelů a uživatelů, takže nelze spočítat náklady variant 4 a 5.
- Nenašel jsem veřejné případové studie fondové administrace na Odoo s mnoha společnostmi. Praktická zkušenost tedy chybí.
- Všechny závěry o přípustnosti jsou můj výklad předpisů a stanovisek ČNB, ne právní názor.
