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

- **Změněné soubory:**
  - `addons/custom/investra_nav/models/instrument_accrual.py` — předvyplnění kurzu splátky, příznak cizí měny a název pole Portfolio.
  - `addons/custom/investra_nav/views/nav_views.xml` — pořadí a blok částek splátky, podmíněná pole, výchozí filtr a seskupení.
  - `addons/custom/investra_nav/tests/test_accrual.py` — Form testy kurzů, mimořádné splátky a pořadí polí.
  - `addons/custom/investra_derivative/models/derivative.py` — výchozí nohy a funkční měna, předvyplnění vzdálené nohy swapu, název pole Portfolio.
  - `addons/custom/investra_derivative/views/derivative_views.xml` — zobrazení evidence, ručních hodnot a stavových kurzů.
  - `addons/custom/investra_derivative/tests/test_derivative.py` — Form testy forwardu/swapu; upraven jediný test nalezený přes `grep "leg_ids.new"` dle upřesnění.
- **Ověřeno (příkaz a výsledek):**
  - `python3 tools/view_check/check_views.py` — 25 souborů, 0 chyb.
  - `python3 -m py_compile ...` pro čtyři změněné Python soubory v AG-022 — úspěšně.
  - `rg "leg_ids\\.new" addons/custom/investra_derivative/tests` — bez dalších výskytů.
- **Neověřeno:** Odoo Form testy a zaúčtování/sjednání; podle zadání je spustí Claude při převzetí.
- **Otevřené otázky a návrhy mimo rozsah:** Žádné.

## Převzetí

Převzal Claude 19. 11. 2026 z pracovní kopie `~/odoo-review` (Copilot zastoupil Antigravity; společný souhrn `docs/ukoly/CP-2026-11-19-AG020-022.md`), větev `ukol/ZJ-13-14`. Ověřeno: testy Odoo `investra_instruments+` (838 testů, 0 selhání, 0 chyb), `check_views.py` bez chyb. Nález revize: předvyplnění vzdálené nohy swapu v onchange nohy nefungovalo (noha nevidí ostatní nohy) → onchange přesunut na `leg_ids` derivátu. Kurz splátky: `float()` a ošetření chybějícího kurzu jako u obchodu. Upozornění: výchozí nohy v `default_get` se použijí i při `create` bez `leg_ids`; stávající testy to neovlivnilo (všechny prošly). Povýšení `investra` ani migrace se nedělá (bez nových uložených polí).
