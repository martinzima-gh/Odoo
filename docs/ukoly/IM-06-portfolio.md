# IM-06 Portfolio: kategorie, schválení, zámek a kompatibilita

| Položka | Hodnota |
|---|---|
| Model | **Opus 5.5** |
| Zóna | červená (logika klasifikace) – začít až po výslovném schválení uživatele |
| Plán | oddíl 1 bod 3, oddíly 2, 3.5, 3.6 (kompatibilita), 5, 6 (Portfolia), 7 |
| Číst | `addons/custom/investra_instruments/models/portfolio.py`, formulář a seznam portfolia v `views/instrument_views.xml`, `docs/vzhled/navrh-seznamu-obchodnich-modelu.html` |

**Cíl:** portfolio přímo určuje oceňovací kategorii; nástroj nejde zařadit do nekompatibilního portfolia ani přes import
nebo API; po prvním obchodu jsou klasifikační pole zamčená.

**Rozsah souborů:** v novém addonu `models/portfolio.py`, `views/portfolio_views.xml`, `tests/test_portfolio.py`, manifest.
Modul `investra_instruments` se nemění.

**Důležité:**
- Portfolio bez kategorie (stávající data a testy) se chová jako dosud; kontrola kompatibility platí jen s kategorií.
- Kontrolu navázat na vstupní pole zařazení a spustit ji i při změně kategorie portfolia.
- Schválení: tlačítko pro skupinu schvalování, vyplní `approved_by`, `approved_on`; Uzavřít nastaví `valid_to`.
- Zámek rozšiřuje stávající `write` portfolia; `is_locked` a `lock_date` z prvního obchodu bez zásahu do obchodu.

**Mimo rozsah:** reklasifikace, účtování, nová činnost schvalovací matice, povinnost kategorie v databázi.

**Kritéria přijetí** (testy 1–7 a 11 zadání):
1. AC / Držet pro inkaso přijme kupónový dluhopis se SPPI „Splněn“.
2. AC odmítne nástroj se SPPI „Nesplněn“ i „Neposouzeno“.
3. AC odmítne derivát a podílový list s právem odkupu.
4. FVOCI_D / Inkaso i prodej přijme dluhopis se SPPI „Splněn“.
5. FVOCI_E přijme jen kapitálový nástroj s volbou 5.7.5; model Obchodování v něm nejde nastavit.
6. FVTPL přijme derivát; bez důvodu klasifikace nejde schválit.
7. Po prvním obchodu nejde změnit kategorii, obchodní model, důvod ani fond.
8. Důvod klasifikace ukazuje pod polem české vysvětlení.
9. Testy `investra_instruments`, `investra_counterparty`, `investra_nav` a `investra_cnb` projdou beze změny.

**Commit:** `Portfolio: kategorie, schválení, zámek a kompatibilita`

## Výsledek

Provedl Claude Code (Opus 5.5) 15. 11. 2026 po schválení plánu uživatelem (červená zóna).

**Změněné soubory** (jen nový addon, verze `20.0.0.4.0`, bez migrace):
- `models/portfolio.py` (nový): pole portfolia z oddílu 3.5 (bez `profile_assignment_ids`, to je IM-07), obchodní model
  „Nepoužije se“, kontrola kategorie × model, schválení a uzavření (jen schvalovatel, kontrola i v metodě), stav jen
  tlačítky, zámek po prvním obchodu ve `write`, kontrola kompatibility zařazení (oddíl 3.6) navázaná na vstupní pole
  zařazení, na změnu kategorie a modelu portfolia a na změnu SPPI nástroje.
- `views/portfolio_views.xml` (nový): XPath do formuláře a seznamu portfolia (hlavička se stavy a tlačítky, pruh
  `alert alert-warning` po zámku, kód, kategorie, důvod s vysvětlením pod polem, záložky Klasifikace IFRS 9 a Řízení
  a kontrola; v seznamu Kód, Kategorie, Stav jako štítek, Platí od/do, Uzamčeno).
- `tests/test_portfolio.py` (nový, 14 testů), `tests/__init__.py`, `models/__init__.py`, `__manifest__.py`.

**Testy** na dočasné `investra_ci_master` podle oddílu 2 (instalace `investra_instrument_master,investra_nav,investra_cnb`
bez demo dat, `l10n_cz`, pak `-u` všech pěti modulů s `--test-tags /investra_instrument_master,/investra_instruments,
/investra_counterparty,/investra_nav,/investra_cnb`): **0 failed, 0 error(s) of 482 tests** (master 59, instruments 83,
counterparty 10, nav 319, cnb 11). Stávající testy beze změny. Jediný ERROR v logu je `bad query` z existujícího testu
IM-04 `test_wizard_requires_reason_and_change` (očekávaná chyba NOT NULL bez `mute_logger`), ne selhání. Databáze
i filestore po testech smazané.

**Kritéria:** 1–8 pokrývají testy `test_ac_*`, `test_fvoci_*`, `test_fvtpl_*`, `test_locked_after_first_trade`,
`test_reason_help_under_field`; navíc kategorie × model, přepočet při změně kategorie a SPPI, jedinečný kód, stav jen
tlačítky, portfolio bez kategorie jako dosud. Kritérium 9 viz testy výše.

**Odchylky a rozhodnutí v rámci úkolu:**
- `investra_instruments` skládá zdůvodnění klasifikace z popisků obchodních modelů ve svém modulu; model „Nepoužije se“
  by tam skončil chybou. Nový addon proto přepisuje `_compute_category` jen pro zařazení s tímto modelem (stejný strom
  i text, liší se jen řádek (c)); ostatní zařazení počítá beze změny `investra_instruments`.
- Formulář: záložky Identifikace a Zařazení nástrojů nejsou, protože stávající pole a seznam zařazení se nepřesouvají
  (pravidlo vzhledu); nová pole jsou ve stávající skupině a v nové záložkové části pod ní. Záložka Účetní profil přijde v IM-07.
- Uzavřít smí jen schvalovatel (plán to neurčoval; uzavření ukončuje platnost klasifikace).
- Zámek hlídá jen skutečnou změnu hodnoty (import se stejnou hodnotou projde); zamyká i fond (kritérium 7).

**Neověřeno:** vzhled v prohlížeči (instalace do `investra_vzhled`/`investra_test` je až po dokončení modulu);
chování uzavřeného portfolia u nových obchodů (obchod se neměnil, uzavření obchody neblokuje).

**Doplněk 15. 11. 2026 – podílový list vždy FVTPL** (rozhodnutí uživatele, deník rozhodnutí; červená zóna, schválil Martin):
strom v `investra_instruments/models/portfolio.py` vede povahu „puttable“ vždy do FVTPL (`SPPI_CATEGORY_NATURES = {"debt"}`),
ruční kategorie naběhlá hodnota / FVOCI se u ní odmítne a v modelech s SPPI se u ní SPPI nevyžaduje. Portfolia AC a FVOCI_D
podílový list odmítnou hláškou „Podílový list s právem odkupu se oceňuje vždy reálnou hodnotou do výsledku …“ (kritérium 3
testované s neposouzeným, nesplněným i splněným SPPI). Nový test `test_fund_units_never_amortised_or_fvoci`
v `investra_instruments`. Data: `investra_test` 0 a `investra_vzhled` 3 zařazení podílových listů, žádné v naběhlé hodnotě
ani FVOCI; migrace není. Testy na čisté `investra_ci_master` (postup výše): **0 failed, 0 error(s) of 483 tests**
(master 59, instruments 84, counterparty 10, nav 319, cnb 11); jediný ERROR v logu je známý `bad query` z IM-04.
Databáze i filestore smazané.

## Převzetí
