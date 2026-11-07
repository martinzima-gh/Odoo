# Edice Odoo a hosting

Stav 2026-11-07. Podklad pro schůzku s Janem Polanem a Martinem Olivou, brána 20. 11. 2026. Rozhodují oni a Martin Zíma.

**Doporučení:** Odoo Enterprise, plán Custom, na vlastním hostingu v EU. Licence je levnější než vlastní vývoj rozvahy, výsledovky, hlavní knihy a bankovních funkcí. Před podpisem ověřit v ukázce Enterprise body níže.

## Edice

| Hledisko | Community | Enterprise (Custom) |
|---|---|---|
| Licence | LGPL-3, zdarma | Předplatné za uživatele, licence po dobu smlouvy |
| Cena | 0 Kč, ale vlastní vývoj | Web Odoo 2026-11-07: 22,90 až 27,90 € za uživatele a měsíc při ročním placení, 33,90 € měsíčně; závazně až nabídka |
| Výkazy | V naší instalaci rozvaha, výsledovka, hlavní kniha a saldokonto nejsou | Součást Accounting, ověřit na české osnově |
| Banka | Import a párování v menu nejsou | Součást, české formáty ověřit |
| DPH | Bez zobrazení přiznání a exportu EPO | Neověřeno, českou dokumentaci Odoo se načíst nepodařilo |
| Multi-company | Ano | Ano, v plánu Custom; licence je za uživatele, ne za společnost |
| Podpora a upgrady | Vlastní | Odoo opravuje chyby a nabízí upgrade; kryté jsou 3 poslední hlavní verze |
| Vlastní moduly | Ano | Ano, ale jejich upgrade je naše odpovědnost |

Fondové moduly jsou nad `account`, takže na edici přímo nezávisí. Závisí na ní vrstvy českého účetnictví pro Investra Services a sestavy.
Ověřit na Enterprise: změnu chování `_post`, zámků a hashů z `docs/analyza-odoo20-nav.md`; všech 186 testů je zatím jen na Community.

**Orientačně:** 5 uživatelů za 27,90 € je asi 1 674 € ročně bez DPH. Počet uživatelů je předpoklad, doplnit.

## Hosting

| Varianta | Pro | Proti |
|---|---|---|
| Odoo Online | Bez správy | Vlastní moduly prakticky nejdou; pro nás nevhodné |
| Odoo.sh | Správa, staging, vlastní moduly | Dodavatel provozuje data; účtuje se zvlášť; podmínky DORA vyjednat s Odoo SA |
| Vlastní nebo pronajatý hosting v EU | Kontrola nad daty, zálohami, sítí, SDAT certifikáty | Provoz a bezpečnost jsou na nás |

Pro kritickou nebo důležitou funkci je potřeba u poskytovatele IKT zajistit požadavky DORA.

## Kritéria hostingu

| Kritérium | Požadavek k ověření | Zdroj |
|---|---|---|
| Smlouva | Popis služeb, subdodavatelé a jejich podmínky, místa zpracování a uložení dat, oznámení změn | DORA čl. 30 |
| Registr | Smlouva zapsaná v registru informací s označením kritické funkce | DORA čl. 28 |
| Ukončení | Strategie odchodu a přechodné období, export dat a záloh | DORA čl. 28 a 30 (znění ověřit) |
| Audit | Právo přístupu a auditu pro nás a ČNB | DORA čl. 30 (znění ověřit) |
| Obnova | Doba obnovy a ztráta dat podle vnitřních předpisů, test obnovy | Harmonogram, akceptace přechodu |
| Bezpečnost | Šifrování, MFA, oddělení prostředí, logy, správa klíčů a certifikátů | Bezpečnostní standardy projektu |
| Síť | Odchozí přístup jen na povolené služby, TLS 1.2 a vyšší | Specifikace SDAT |
| Umístění | Data v EU | Interní požadavek, potvrdit |

## Otázky na schůzku

1. Kolik uživatelů a kolik společností bude v prvním roce?
2. Je Odoo kritická nebo důležitá funkce podle DORA? Předpoklad: ano.
3. Kdo je správce provozu a kdo drží klíče?
4. Může Jan Polan dodat českou lokalizaci nad Enterprise a kdo ji bude udržovat?
5. Můžeme dostat testovací Enterprise pro spuštění našich testů?

## Zdroje

- [Ceník Odoo](https://www.odoo.com/pricing), [Podmínky Odoo Enterprise, verze 13](https://www.odoo.com/documentation/19.0/legal/terms/enterprise.html)
- [DORA 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng), [ITS k registru informací](https://www.esma.europa.eu/sites/default/files/2024-01/JC_2023_85_-_Final_report_on_draft_ITS_on_Register_of_Information.pdf): z výňatků.
- Srovnání funkcí Community a Enterprise: naše kontrola v `docs/ceska-lokalizace.md`; funkce Enterprise jsou z popisů, ne z vyzkoušení.
