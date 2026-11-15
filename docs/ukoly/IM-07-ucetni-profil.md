# IM-07 Účetní profil a přiřazení

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová (bez účetního dopadu) |
| Plán | oddíl 1 bod 10, oddíly 2, 3.6 (profil), 3.7, 5, 6, 7 |
| Číst | `addons/custom/investra_entity/models/account_role.py` |

**Cíl:** kombinace společnost + portfolio + BA0088 nebo skupina vybere účetní profil; zařazení ukáže vybraný profil
a stav (v pořádku / není nastaven / role se liší).

**Rozsah souborů:** v novém addonu `models/accounting_profile.py`, `views/accounting_profile_views.xml`, záložka Účetní
profil ve formuláři portfolia, pole na formuláři zařazení, `tests/test_accounting_profile.py`, práva, nabídka, manifest.

**Mimo rozsah:** změna návrhu role zařazení, účtování, události; přímá vazba na `account.account`.

**Kritéria přijetí:**
- Ve stejném FVTPL portfoliu dostane BA0088 211 a 149 různé profily.
- Pravidlo na kód má přednost před pravidlem na skupinu a to před obecným; nižší `priority` vyhrává.
- Pravidlo mimo platnost se nepoužije; duplicitní pravidlo se odmítne.
- Bez pravidla je stav „není nastaven“ a `_require_profile()` vyhodí chybu z oddílu 3.7.
- Role profilu odlišná od role zařazení dá stav „role se liší“; nic se nepřepisuje.
- Přiřazení cizí společnosti uživatel nevidí.

**Commit:** `Účetní profil: přiřazení podle portfolia a BA0088`

## Výsledek

**Změněné soubory** (addon `investra_instrument_master`, verze 20.0.0.5.0):
- nové: `models/accounting_profile.py`, `views/accounting_profile_views.xml`, `tests/test_accounting_profile.py`;
- upravené: `__manifest__.py`, `models/__init__.py`, `tests/__init__.py`, `security/ir.access.csv` (práva profilu a přiřazení,
  pravidlo záznamů podle společnosti).
- Obsah: modely `investra.accounting.profile` (role účtu) a `investra.accounting.profile.assignment`; `_select()`;
  na zařazení pole `accounting_profile_id`, `profile_state` a metoda `_require_profile()`; na portfoliu `profile_assignment_ids`
  a záložka Účetní profil; pole profilu a stavu (štítek) pod Rolí účtu ve formuláři zařazení; nabídka Nastavení → Účtování
  (Účetní profily, Přiřazení účetních profilů). Do stávajících formulářů jen XPath, žádné nové styly.

**Testy:** dočasná DB `investra_ci_master` podle oddílu 2 plánu (instalace modulu, `l10n_cz`, pak
`-u investra_instrument_master --test-enable --test-tags /investra_instrument_master`): **71 testů, 0 selhání, 0 chyb**,
z toho 12 nových v `test_accounting_profile.py` (všechna kritéria přijetí). Záznam ERROR v logu u průvodce změnou klasifikace
je očekávaná chyba SQL ze stávajícího testu s `assertRaises`, ne selhání. Databáze i její filestore po testech smazány.
Instalace se stávajícími databázemi (`investra_test`, `investra_vzhled`) se nedělala.

**Neověřeno:** zobrazení nových polí a záložky v prohlížeči (jen se načetly bez chyby při instalaci); chování editovatelného
seznamu pravidel v záložce portfolia u nového, ještě neuloženého portfolia (společnost se bere z portfolia, jinak z aktuální
společnosti).

**Odchylky a rozhodnutí:**
- Datum výběru pro zařazení = dnešek, nebo `valid_from` zařazení, je-li v budoucnosti (plán datum pro zařazení neurčuje).
  `accounting_profile_id` a `profile_state` jsou neuložené, proto se podle nich nedá hledat ani filtrovat.
- Navíc kontrola, že portfolio pravidla patří téže společnosti jako pravidlo (hláška „Portfolio %s patří jiné společnosti…“).
- Pravidlo záznamů je v `ir.access.csv` (Odoo 20), ne v XML.
- Pořadí v manifestu: `accounting_profile_views.xml` je až za `portfolio_views.xml` (dědí jeho formulář); položky nabídky
  Účtování jsou proto v tomto souboru, ne v `menus.xml`.
- Nic se neúčtuje, role zařazení se nepřepisuje, žádná vazba na `account.account`.

## Převzetí
