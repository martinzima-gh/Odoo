# AG-020 Portfolia, zařazení nástrojů a nabídka Portfolio

Zadání pro Antigravity (druhý vývojář). Pravidla jsou v `.agents/rules/`, role v `CLAUDE.md` (Role agentů).
Původní označení v plánu z 19. 11. 2026: AG-014 (číslo je obsazené úkolem SQL ukázky). Pořadí provádění: **AG-020 → AG-021 → AG-022**,
každý úkol se přebírá zvlášť. Rozbor vycházel z kódu větve `ukol/ZJ-13-14` (5a9b1e5).

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (podle schváleného plánu níže); zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*` a náhledy zaúčtování se **nemění** |
| Výchozí větev | `main` |
| Větev úkolu | `ag/AG-020-portfolia-nabidka` |
| Zadal, dne | Martin, 19. 11. 2026 (plán schválil Martin 19. 11. 2026) |
| Navazuje na | rozhodnutí 2026-11-19 „Portfolio – názvy a nabídka“; navazují AG-021 a AG-022 |

**Cíl:** Jednotné názvy (Portfolio × Obchodní model), nabídka Portfolio v pořadí podle práce a srozumitelné formuláře Portfolia
a Zařazení nástrojů.

**Rozsah souborů:** `investra_instruments/views/instrument_views.xml`, `investra_instrument_master/views/*.xml`, menu
(jen `menuitem`) v `investra_nav/views/nav_views.xml` a `investra_derivative/views/derivative_views.xml`,
`investra_instruments/models/portfolio.py` a `investra_instrument_master/models/portfolio.py` (jen onchange, výchozí hodnoty a popisky; onchange kategorie → model patří do `investra_instrument_master`, kde je definovaná `CATEGORY_MODEL`, protože `investra_instruments` ji nevidí; mapu ani kontrolu na ní nepřesouvat ani neměnit), testy v příslušných modulech, překlady.

**Mimo rozsah:** zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*`, náhledy zaúčtování; mapa `CATEGORY_MODEL`
se jen čte. Když by úprava vyžadovala jejich změnu, **zastavit a úkol vrátit Claudovi** (červená zóna). Testy Odoo, commit, push
a povýšení modulu dělá Claude při převzetí.

**Kritéria přijetí:** body 1–3 níže; testy z dolní části; stávající testy beze změny; `python3 tools/view_check/check_views.py`
bez chyb.

**Schválený plán** (schválil Martin 19. 11. 2026):

**Rozhodnutí společná pro AG-020 až AG-022:**

- **R1 Názvy:** pole odkazující na portfolio fondu (`portfolio_id`) se všude jmenuje **Portfolio**; „Obchodní model“ je jen pole
  `business_model` (hold to collect / collect and sell / ostatní). Nabídka „Obchodní modely“ se přejmenuje na **Portfolia**.
- **R2 Nabídka Portfolio:** Obchody, Splátky nástrojů, Deriváty, Ceny, Zařazení nástrojů (v tomto pořadí, sekvence bez duplicit).
  **Portfolia** se přesunou do Nastavení › Fondy (fond má automaticky portfolio „Hlavní“, běžně se nemění).

### Úpravy

1. **Nabídka a názvy.** Nabídka podle R2; přejmenování podle R1 ve všech pohledech (seznamy, formuláře, seskupení, filtry).
   V seznamu zařazení odstranit kolizi dvou sloupců „Obchodní model“.
2. **Formulář Portfolia.** Pořadí: Fond, Název, Kód → Oceňovací kategorie → Obchodní model (po výběru kategorie předvyplnit
   podle mapy `CATEGORY_MODEL`, která už existuje jako kontrola) → Důvod klasifikace, Vysvětlení, Posouzení modelu.
   Pole potřebná ke Schválit (kód, kategorie, důvod, posouzení, platí od) označit v draftu jako povinná
   (`required="state == 'draft'"` jen ve formuláři, nebo viditelná nápověda „potřeba ke schválení“ – zvolit to, co nerozbije
   stávající testy). Platí od výchozí dnes. Hledání: filtry Fond, Stav, seskupení Fond.
3. **Formulář Zařazení.** Nahoře Portfolio (výchozí jediné portfolio fondu – `_default_portfolio`), Nástroj (doména: sdílené
   nástroje a nástroje fondu portfolia), Platí od. Hned pod tím rámeček **Výsledek**: Kategorie IFRS 9, Způsob ocenění, Role účtu
   (velké, jen pro čtení, kde jsou vypočtené). Postup klasifikace (povaha, SPPI, obchodní model, povinná klasifikace, určení,
   ruční kategorie) přesunout do záložky „Postup klasifikace“; písmena (a)–(f) nahradit slovy. Platí do zobrazit jen když je
   vyplněné, Odchylka od návrhu jen když je pravda, Fond a Druh jako drobný text pod nástrojem. Seznam: výchozí seskupení
   podle fondu.

**Testy:** nabídka (pořadí, umístění Portfolií), onchange kategorie → model, výchozí portfolio a doména nástroje v zařazení.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
