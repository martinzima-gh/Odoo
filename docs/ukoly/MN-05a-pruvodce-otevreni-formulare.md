# MN-05a Průvodce Nová účetní kniha: chyba prohlížeče po založení

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (návratová akce průvodce; založení knihy se nemění) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-05; poznámka Martina 7 z průchodu zakládání 16. 11. 2026 |

**Chyba (Martin v prohlížeči, 16. 11. 2026 12:34):** po „Založit knihu“
`UncaughtPromiseError > TypeError: undefined is not an object (evaluating 'action.views.map')` v `_preprocessAction` / `doAction`.
Kniha i společnost se přitom založily správně (ověřeno SELECTem: společnost 11, kniha 10, audit trail, hash obecných deníků,
69 rolí); spadne jen otevření formuláře po hlášce.

**Příčina (čtením kódu):** `investra_chart_fund/wizard/new_book.py`, `action_create`: akce `form` předaná jako `params.next`
klientské akci `display_notification` nemá klíč `views`. Akce vrácená jako slovník přímo klientovi (ne přes server) ho
v Odoo 20 musí mít.

**Oprava:** do akce `form` doplnit `"views": [(False, "form")]`. Nic dalšího neměnit. Projít ostatní naše akce vracené přes
`next` nebo `display_notification` (`grep -rn '"next"' addons/custom`) a stejnou chybu opravit i tam, pokud je.

**Test:** v testech průvodce ověřit, že `params.next` obsahuje `views` s pohledem `form` (klienta testy nespouštějí,
proto hlídat strukturu akce). Pokud v `tools/view_check` jde jednoduše doplnit obecnou kontrolu, nedělat; jen navrhnout ve Výsledku.

**Nasazení:** povýšení `investra_chart_fund` v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071.
V `investra` nic nezakládat.

**Rozsah souborů:** `investra_chart_fund/wizard/new_book.py`, jeho testy, verze v manifestu; případně stejná oprava jinde
(uvést ve Výsledku); tento soubor (Výsledek), předávka.

**Kritéria přijetí:** testy `investra_chart_fund` projdou na `investra_ci_*`; Výsledek uvádí, že v prohlížeči neověřeno
(ověří Martin dalším založením knihy).

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:** `addons/custom/investra_chart_fund/wizard/new_book.py` (akce `form` má `"views": [(False, "form")]`),
  `tests/test_new_book.py` (kontrola `views` v `_create`), `__manifest__.py` (20.0.0.12.1), tento soubor, předávka.
  Další akce přes `next`: jen `investra_nav/models/instrument_accrual.py:567` (klientská akce `soft_reload`, `views` nepotřebuje); jinde chyba není.
- **Ověřeno (příkaz a výsledek):** `tools/run_tests.sh investra_chart_fund` → 0 failed, 0 error z 29 testů, dočasná
  `investra_ci_20261116_133738` smazána. Záloha `zalohy/investra-2026-11-16-pred-MN05a.dump` (pg_dump -Fc, 9 MB, mimo git).
  Upgrade `-u investra_chart_fund` v `investra` bez chyby, `investra-web` znovu spuštěna, `/web/login` vrací 200. V `investra` nic nezaloženo.
- **Neověřeno:** chování v prohlížeči (ověří Martin dalším založením knihy). Obecná kontrola akcí v `tools/view_check`
  se nedělala; návrh: hlídat, že každá akce v `params.next` má `views`.
