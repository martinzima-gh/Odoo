# MN-01 Průvodce „Nová účetní kniha“

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (průvodce nad hotovou funkcí `create_book`; funkční měna a osnova, proto Opus) |
| Výchozí větev | `main` |
| Větev úkolu | `ukol/MN-manual` (stejná větev jako MN-02, úkoly jdou po sobě) |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | rozhodnutí Martina 16. 11. 2026: manuál založení fondu, nejdřív průvodce; funkční měna jen při založení (deník 2026-11-15) |

**Proč:** společnost s účetní knihou dnes zakládá jen kód (`investra.entity.create_book`, volá ho `tools/demo_data/seed.py`).
Ruční založení přes Nastavení Odoo by vynechalo: načtení osnovy bez přepsání funkční měny (kontext `chart_template_load`),
`restrictive_audit_trail`, zámek (hash) obecných deníků u fondů, zdroj kurzů podle měny a mapování rolí účtů fondu
(`investra_chart_fund/models/entity.py`). Uživatel musí knihu založit v aplikaci stejně jako seed.

**Cíl:** v nabídce Investra › Nastavení › Fondy › Účetní knihy tlačítko a položka „Nová účetní kniha“. Průvodce založí
společnost a knihu jediným voláním `create_book`; výsledek je totožný s knihou ze seedu.

**Plán (od Clauda, Opus ho smí upřesnit, odchylky popsat ve Výsledku):**

1. Přechodný model (`TransientModel`) průvodce v `investra_chart_fund` (zná obě šablony a mapování rolí). Pole: název,
   druh jednotky, účetní rámec, funkční měna (výchozí CZK), země (výchozí CZ), nadřazená kniha, zakladatel.
   Šablona osnovy se neodvozuje od uživatele: SICAV, fond a podfond → `investra_fund`, ostatní → `cz`.
   Výchozí rámec podle druhu: servisní společnost → `cas500`, ostatní → `cas501`; kombinaci mimo tato pravidla nepovolit
   (rámce se nemíchají).
2. Upozornění v průvodci: funkční měnu, rámec ani společnost nejde po prvním zaúčtování změnit; zdroj kurzů se řídí měnou.
3. Po založení přidat novou společnost aktuálnímu uživateli (`company_ids`) a otevřít formulář nové knihy.
4. Práva: průvodce jen pro správce (návrh `base.group_system`; jinou skupinu zdůvodnit). Řádek do `security/ir.access.csv`.
5. Transakce: `try_loading` při prvním načtení šablony umí potvrdit transakci a přenačíst registr (viz
   `tools/demo_data/README.md`, `account_peppol`). Ověřit, že průvodce v požadavku z prohlížeče nespadne a při chybě
   nezůstane polovičatá společnost; jinak zvolit bezpečné řešení (kontrola předpokladů před založením, srozumitelná chyba).
6. Testy (`investra_chart_fund/tests`): kniha fondu v CZK a v EUR (měna, zdroj kurzů ČNB / ECB, hash obecných deníků,
   audit trail, namapované role), kniha investiční společnosti (šablona `cz`, bez hashe), zákaz nepovolené kombinace,
   uživatel má po založení přístup ke společnosti.
7. Povýšení `investra_chart_fund` v `investra` se zálohou do `zalohy/` (souhlas je v promptu), restart jen webové instance 8071.

**Rozsah souborů:** `addons/custom/investra_chart_fund/` (wizard, views, security, tests, verze v manifestu, README modulu),
tento soubor (Výsledek), předávka. Seed neměnit.

**Mimo rozsah:** změna `create_book`, osnovy a rolí; založení fondu a tříd (to je formulář Fondy); manuál (MN-02).

**Kritéria přijetí:** testy modulu projdou na `investra_ci_*`; v `investra` je průvodce vidět; ve Výsledku krátký
popis kroků v UI pro manuál (pole, výchozí hodnoty, upozornění) a co zůstalo neověřené v prohlížeči.

## Výsledek

Provedl Claude (Opus 5.5), 16. 11. 2026. Plán dodržen; upřesnění níže.

- **Změněné soubory:** `investra_chart_fund/wizard/` (`new_book.py` – přechodný model `investra.new.book.wizard`,
  `new_book_views.xml` – formulář, akce, tlačítko v seznamu knih, nabídka), `security/ir.access.csv` (nový, jen
  `base.group_system`), `tests/test_new_book.py` (9 testů), `__manifest__.py` (verze 20.0.0.10.0, `data`), `README.md` (nový).
  `create_book`, osnova, role ani seed se nezměnily; migrace není potřeba (jen nový model a pohledy).
- **Upřesnění plánu:**
  - Rámec se po výběru druhu předvyplní; ruční změna na jinou kombinaci (i IFRS) se odmítne chybou před založením.
  - Bod 5 (transakce): jediné potvrzení transakce v cestě `create_book` je doinstalace modulu šablony v
    `account.chart.template._load` (`button_immediate_install`); automatickou instalaci lokalizace při založení společnosti
    vypíná kontext `chart_template_load`. Průvodce proto před založením zkontroluje, že modul šablony i moduly lokalizace
    země (`uninstalled_l10n_module_ids`) jsou nainstalované, jinak skončí chybou „Nejdřív nainstalujte moduly… Nic se
    nezaložilo.“ Ostatní chyby (název společnosti už existuje, podfond bez SICAV, rámec) se kontrolují také předem; kdyby
    přesto něco selhalo až v `create_book`, Odoo vrátí celý požadavek (commit v cestě není).
  - Bod 3: `res.company.create` připojí společnost uživateli sám, průvodce to dělá výslovně znovu. Vrácená akce otevře
    formulář knihy s novou společností v `allowed_company_ids` (kontext akce přebije kontext klienta), jinak by formulář
    zablokovalo pravidlo „Knihy podle společnosti“.
  - Skupina `base.group_system`: Odoo načtení osnovy jiným než správcům nedovolí (`_load` → AccessError).
- **Kroky v UI pro manuál (MN-02):** Investra › Nastavení › Fondy › Nová účetní kniha (nebo tlačítko „Nová účetní kniha“
  v seznamu Účetní knihy; vidí jen správce). Nahoře žluté upozornění: funkční měnu, rámec ani společnost nejde po prvním
  zaúčtování změnit; zdroj kurzů se řídí měnou (CZK – ČNB, EUR – ECB); šablona podle druhu jednotky. Pole: Název
  společnosti, Druh jednotky (výchozí Fond), Účetní rámec (podle druhu: servisní 500/2002, ostatní 501/2002), Nadřazená
  kniha (u podfondu povinně SICAV), Zakladatel; vpravo Funkční měna (výchozí CZK), Země (výchozí Česko) a jen pro čtení
  Šablona osnovy a Zdroj kurzů. Tlačítko „Založit knihu“ se zeptá na potvrzení, pak se otevře formulář nové knihy.
- **Ověřeno (příkaz a výsledek):**
  - `tools/run_tests.sh investra_chart_fund` → 0 failed, 0 error z 21 testů (9 nových: fond CZK/ČNB a EUR/ECB s hashem
    obecných deníků, audit trailem a rolemi; investiční společnost se šablonou `cz` bez hashe; SICAV a podfond; výchozí
    rámec a šablona; odmítnutí fond+500, servisní+501, fond+IFRS bez založené společnosti; podfond bez SICAV; duplicitní
    název; uživatel jen s `account.group_account_manager` průvodce neotevře; admin má po založení společnost v `company_ids`).
    Dočasná DB smazána.
  - `tools/run_tests.sh all` → 0 failed, 0 error ze 742 testů (16 modulů); 6 varování jen z prostředí (cesta
    `/mnt/extra-addons`, `--without-demo`, `markdown2`). Dočasná DB smazána.
  - `investra`: záloha `zalohy/investra-2026-11-16-pred-MN01.dump` (čitelná přes `pg_restore -l`), `-u investra_chart_fund`
    rc=0 (log `.test-logs/upgrade-investra-MN01.log`; jen předchozí hlášky: README `investra_instrument_master`, popisky polí
    `investra_nav`), modul 20.0.0.10.0, průvodce, akce, nabídka a právo v DB; instance 8071 znovu běží (`/web/login` 200).
  - `investra` nanečisto (`odoo shell` s rollbackem): chybějící moduly lokalizace CZ žádné, kontroly fondu + 501 projdou,
    fond + 500 odmítnut; počet knih beze změny (7).
- **Neověřeno:** průchod v prohlížeči (tlačítko v seznamu, nabídka, upozornění, otevření formuláře nové knihy bez
  přepnutí firmy a viditelnost pro uživatele bez správce). V `investra` jsem žádnou knihu nezaložil.
- **Otevřené otázky a návrhy mimo rozsah:**
  - Nová společnost se v přepínači firem neaktivuje trvale; po odchodu z formuláře ji uživatel zaškrtne sám.
  - Měny: nabízejí se jen aktivní; pro jinou než CZK/EUR je zdroj kurzů ČNB a pravidlo měny se nekontroluje (stav `create_book`).
  - Nadřazená kniha u fondu a SICAV nemá omezení druhu (stav modelu); obchodní význam vazby fond → investiční společnost
    neurčuji.
