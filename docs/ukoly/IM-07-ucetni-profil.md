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

## Převzetí
