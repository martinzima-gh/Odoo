# AG-022 Splátky nástrojů a deriváty

Zadání pro Antigravity (druhý vývojář). Pravidla jsou v `.agents/rules/`, role v `CLAUDE.md` (Role agentů).
Původní označení v plánu z 19. 11. 2026: AG-013 (číslo je obsazené úkolem Nápovědy a nabídka Ocenění). Pořadí provádění:
AG-020 → AG-021 → **AG-022**. Navazuje na AG-020 (názvy, nabídka) a AG-021 (předvyplnění kurzu podle R3).

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (podle schváleného plánu níže); zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*`, sjednání derivátu a náhledy zaúčtování se **nemění** |
| Výchozí větev | `main` (po převzetí AG-021) |
| Větev úkolu | `ag/AG-022-splatky-a-derivaty` |
| Zadal, dne | Martin, 19. 11. 2026 (plán schválil Martin 19. 11. 2026) |
| Navazuje na | rozhodnutí 2026-11-19 „Předvyplnění kurzu a data vypořádání“; AG-020, AG-021 |

**Cíl:** Splátka nástroje a derivát se zadávají v pořadí podle práce, s předvyplněným kurzem a nohami derivátu; zaúčtování
a kontroly se nemění.

**Rozsah souborů:** `investra_nav/views/nav_views.xml` (splátka), `investra_nav/models/instrument_accrual.py` (jen onchange,
výchozí hodnoty a zobrazení), `investra_derivative/views/derivative_views.xml`, `investra_derivative/models/derivative.py`
(jen onchange, výchozí hodnoty a zobrazení), testy, překlady.

**Upřesnění (19. 11. 2026, na dotaz Copilota):** stávající Form test `test_swap_saves_in_form` v `investra_derivative/tests/test_derivative.py`
po volbě swapu přidává dvě nohy ručně; s automatickým založením by jich vznikly čtyři. Test se **smí upravit** (je to záměrná změna
chování, ne oslabení kontroly): místo `leg_ids.new()` se nohy po volbě druhu **upraví** (`with form.leg_ids.edit(0)` a `edit(1)`);
kontroly (počet nohou 2, instrument, portfolio) zůstávají. Totéž u dalších testů, které po volbě druhu přidávají nohy ručně
(`grep "leg_ids.new" tests/`). Žádný jiný stávající test se neoslabuje; jakoukoli další změnu očekávané hodnoty zapsat do otevřených otázek.

**Mimo rozsah:** zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*`, sjednání a vypořádání derivátu;
spot T+2 se nezavádí. Když by úprava vyžadovala jejich změnu, **zastavit a úkol vrátit Claudovi** (červená zóna). Testy Odoo,
commit, push a povýšení modulu dělá Claude při převzetí.

**Kritéria přijetí:** body 1–4 níže; testy z dolní části; předvyplněné záznamy projdou Zaúčtovat / Sjednat stejnými kontrolami;
stávající testy beze změny; `python3 tools/view_check/check_views.py` bez chyb.

**Schválený plán** (schválil Martin 19. 11. 2026):

**Rozhodnutí společné pro AG-020 až AG-022:**

- **R1 Názvy:** pole `portfolio_id` se všude jmenuje **Portfolio**; „Obchodní model“ je jen pole `business_model`.
- **R3 Kurz měny se předvyplní** u splátky (k datu splátky) ze zdroje kurzů knihy fondu – stejnou funkcí jako u úpisů
  a derivátů (`fund._fx_at(měna nástroje, den)`). Uživatel ho smí přepsat; u nástroje v měně fondu se pole skryje (zůstává 1).
  Zaúčtování beze změny (bere pole, jak je).

### Splátka

1. **Seznam:** výchozí filtr Nezaúčtováno, seskupení Nástroj; tlačítko „Návrhy podle kalendáře“ ponechat.
2. **Formulář:**
   - Druh (podle kalendáře / mimořádná) jako první – ovlivňuje předvyplnění;
   - pak Fond, Nástroj, (Portfolio jen když je nástroj ve dvou portfoliích);
   - částky Jistina, Úrok, Poplatek, Výplata v jednom bloku a vedle Zbývající jistina před / po;
   - Uzavírá pozici jen u mimořádné;
   - Kurz jen u cizí měny, předvyplnit podle R3;
   - Účetní událost, Opravuje splátku a Důvod storna jen když jsou vyplněné.

### Derivát

3. **Nohy:** po volbě Druhu spot nebo forward založit jednu nohu, u swapu dvě (prázdné). V noze předvyplnit jednu měnu =
   funkční měna fondu (kontrola to stejně vyžaduje). U swapu po vyplnění blízké nohy předvyplnit vzdálenou opačně (měny
   prohozené, částky stejné jako výchozí návrh, datum prázdné). Spot T+2 se nezavádí.
4. **Zobrazení podle stavu:** v návrhu skrýt skupinu Evidence (Nástroj, Účetní událost), sloupce b0 a kurzy nohy a záložku
   Ruční hodnoty; ukázat je od Sjednáno. Skupinu „Evidence“ přejmenovat na „Po sjednání“. Statusbar ukázat i Stornováno.

**Testy (Form):** splátka v cizí měně s předvyplněným kurzem, mimořádná splátka (pořadí a viditelnost), derivát forward s jednou
nohou a funkční měnou, swap s předvyplněnou vzdálenou nohou, předvyplněné záznamy projdou Zaúčtovat / Sjednat stejnými kontrolami.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
