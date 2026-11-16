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

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
