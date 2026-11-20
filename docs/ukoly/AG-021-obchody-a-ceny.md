# AG-021 Obchody a ceny

Zadání pro Antigravity (druhý vývojář). Pravidla jsou v `.agents/rules/`, role v `CLAUDE.md` (Role agentů).
Původní označení v plánu z 19. 11. 2026: AG-012 (číslo je obsazené úkolem České názvy polí). Pořadí provádění:
AG-020 → **AG-021** → AG-022. Navazuje na AG-020 (názvy Portfolio, nabídka).

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (podle schváleného plánu níže); zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*` a náhledy zaúčtování se **nemění** |
| Výchozí větev | `main` (po převzetí AG-020) |
| Větev úkolu | `ag/AG-021-obchody-a-ceny` |
| Zadal, dne | Martin, 19. 11. 2026 (plán schválil Martin 19. 11. 2026) |
| Navazuje na | rozhodnutí 2026-11-19 „Portfolio – názvy a nabídka“, „Předvyplnění kurzu a data vypořádání“; AG-020 |

**Cíl:** Obchod a cena se zadávají v pořadí podle práce, s předvyplněnými hodnotami a nápovědami; zaúčtování se nemění.

**Rozsah souborů:** `investra_instruments/views/instrument_views.xml` (obchod, cena), `investra_nav/views/trade_views.xml`,
`investra_instruments/models/instrument.py` (jen onchange, výchozí hodnoty a computed pro zobrazení),
`investra_nav/models/trade_preview.py` (jen zobrazení), testy, překlady.

**Upřesnění rozsahu (19. 11. 2026, na dotaz Copilota):** do `investra_instruments/models/instrument.py` smějí přibýt dvě úzké obslužné metody tlačítek:
(a) „Prodat vše“ na obchodu: jen u nezaúčtovaného obchodu s `side = sell` zapíše `units :=` držené kusy k datu (stejná výpočetní funkce
jako nápověda „Drženo k datu“, nová logika držení se nevytváří); nic dalšího nemění a nezaúčtovává;
(b) hromadné „Schválit“ v seznamu cen: metoda, která z vybraných cen vezme jen ty ve stavu návrh a pro ně **zavolá nezměněnou**
`action_approve`; ostatní vynechá bez chyby (volitelně zpráva „Vynecháno N cen mimo návrh“). `action_approve` ani schvalovací
matice se nemění; kdo cenu smí schválit, rozhoduje dál matice. Obě metody mají test (včetně výběru smíšených stavů). Cokoli dalšího
v modelu zůstává mimo rozsah.

**Mimo rozsah:** zaúčtování, kontroly (constraints), `_book*`, `_validate`, `_check*`, logika náhledu zaúčtování; konvence T+n
se nezavádí. Když by úprava vyžadovala jejich změnu, **zastavit a úkol vrátit Claudovi** (červená zóna). Testy Odoo, commit, push
a povýšení modulu dělá Claude při převzetí.

**Kritéria přijetí:** body 1–5 níže; testy z dolní části; předvyplněný obchod projde `action_book` stejnými kontrolami;
stávající testy beze změny; `python3 tools/view_check/check_views.py` bez chyb.

**Schválený plán** (schválil Martin 19. 11. 2026):

**Rozhodnutí společná pro AG-020 až AG-022:**

- **R1 Názvy:** pole `portfolio_id` se všude jmenuje **Portfolio**; „Obchodní model“ je jen pole `business_model`.
- **R3 Kurz měny se předvyplní** u obchodu (k datu sjednání; kurz vypořádání k datu vypořádání) a u splátky (k datu splátky)
  ze zdroje kurzů knihy fondu – stejnou funkcí jako u úpisů a derivátů (`fund._fx_at(měna nástroje, den)`). Uživatel ho smí
  přepsat; u nástroje v měně fondu se pole skryje (zůstává 1). Zaúčtování beze změny (bere pole, jak je).
- **R4 Datum vypořádání obchodu** se předvyplní datem sjednání (dnes prázdné = totéž). Konvence T+n se nezavádí.

### Obchod

1. **Seznam:** tlačítka „Nový nákup“ a „Nový prodej“ (default side). Sloupce: Datum sjednání, Stav, Fond, Nástroj, Směr, Kusy,
   Cena, Měna (měna nástroje), Datum vypořádání; Portfolio, Kategorie IFRS 9, Kurz, Naběhlý úrok jako volitelné skryté.
2. **Formulář, pořadí podle práce:**
   - nadpis „Nákup / Prodej“ + Datum sjednání; Nástroj;
   - Fond (předvyplnit, má-li uživatel jediný fond v aktivní knize);
   - Portfolio (skrýt, má-li fond jediné);
   - Kusy (u prodeje vedle „Drženo k datu: N ks“ a tlačítko „Prodat vše“ = kusy := držené);
   - Cena s měnou nástroje a nápovědou „poslední schválená cena k datu: X“ (jen nápověda, ne výchozí hodnota; dotaz jako
     dashboard: instrument, date <= den, state approved, fond nebo sdílená);
   - Naběhlý úrok hned pod cenou (jen dluhopis, už se předvyplňuje z kalendáře);
   - Datum vypořádání (R4);
   - Kurz a Kurz vypořádání jen u cizí měny, předvyplnit podle R3;
   - Zařazení a kategorie IFRS 9 jako jeden řádek jen pro čtení („Zařazení: FVTPL, portfolio Hlavní“);
   - skupinu Účetní události zobrazit až po zaúčtování;
   - nástroj typu „ostatní podíl“ (`other_holding`) vyřadit z domény nástroje (stejně ho nejde zaúčtovat).
3. **Výchozí:** datum sjednání = dnes, směr z tlačítka.

### Cena

4. **Formulář:** Nástroj → Fond (u nástroje bez ISIN předvyplnit `instrument.fund_id`) → Datum (výchozí dnes) → Cena s měnou
   nástroje (měna jen pro čtení po výběru nástroje) → nápověda „předchozí schválená cena: X k datu Y (změna Z %)“ → Zdroj
   (výchozí poslední zdroj použitý u nástroje) → Důvod odchylky (jen cena fondu). Rozsah ve formuláři skrýt; Zadal a Schválil
   jen když jsou vyplněné.
5. **Seznam:** tlačítko Schválit jen nad vybranými řádky v návrhu (bez chyby u ostatních); sloupec Rozsah volitelný skrytý.

**Testy (Form):** nový nákup s výchozími hodnotami, kurz předvyplněn u cizí měny a skryt u domácí, datum vypořádání = sjednání,
prodat vše, nápověda ceny, cena fondu u nástroje bez ISIN, předvyplněný obchod projde `action_book` stejnými kontrolami.

## Výsledek

- **Změněné soubory:**
  - `addons/custom/investra_instruments/models/instrument.py` — výchozí hodnoty, nápověda předchozí ceny, předvyplnění kurzů, obsluha tlačítek „Prodat vše“ a hromadné schválení.
  - `addons/custom/investra_instruments/views/instrument_views.xml` — pořadí a sloupce obchodu/ceny, tlačítka nákupu a prodeje, skrytá pole a filtrování nástroje.
  - `addons/custom/investra_instruments/tests/test_instrument.py` — smíšený výběr návrhů a schválených cen.
  - `addons/custom/investra_nav/models/trade_preview.py` — pouze nápověda ceny a souhrn zařazení.
  - `addons/custom/investra_nav/views/trade_views.xml` — zobrazení nápovědy a souhrnu v obchodním formuláři.
  - `addons/custom/investra_nav/tests/test_trade_preview.py` — Form testy výchozího obchodu, kurzů, prodeje všeho, nápovědy a ceny fondu.
- **Ověřeno (příkaz a výsledek):**
  - `python3 tools/view_check/check_views.py` — 25 souborů, 0 chyb.
  - `python3 -m py_compile ...` pro čtyři změněné Python soubory — úspěšně.
- **Neověřeno:** Odoo Form testy a běh `action_book`; podle zadání je spustí Claude při převzetí.
- **Otevřené otázky a návrhy mimo rozsah:** Žádné.

## Převzetí

Převzal Claude 19. 11. 2026 z pracovní kopie `~/odoo-review` (Copilot zastoupil Antigravity; společný souhrn `docs/ukoly/CP-2026-11-19-AG020-022.md`), větev `ukol/ZJ-13-14`. Ověřeno: testy Odoo `investra_instruments+` (838 testů, 0 selhání, 0 chyb), `check_views.py` bez chyb. Nález revize: onchange kurzu volal `fund._fx_at` z `investra_instruments`, funkce je ale v `investra_nav` (vrací Decimal a při chybějícím kurzu hází chybu) → onchange cizí měny přesunut do rozšíření obchodu v `investra_nav/models/trade_preview.py` (`float()`, chybějící kurz formulář nezastaví). Nález: výchozí datum vypořádání v `default_get` platilo i při `create` bez pole (test s pozdějším sjednáním padal na kontrole data) → předvyplnění jen přes onchange (`trade_date`, `instrument_id`). Skryté Portfolio při jediném portfoliu fondu: tři starší testy už portfolio do Formu nezadávají. Omezení: při opakované změně data sjednání v novém formuláři se datum vypořádání přepíše jen poprvé (dále je považováno za ruční). Povýšení `investra` ani migrace se nedělá (bez nových uložených polí).
