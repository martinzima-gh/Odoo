# IM-10 Výplata úroku „Nepravidelně“

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | červená (`investra_nav`, kalendář toků je vstup naběhlé hodnoty) – plán níže schvaluje Martin v promptu |
| Číst | `addons/custom/investra_nav/models/instrument_accrual.py` (ř. 1–90), `addons/custom/investra_nav/views/nav_views.xml` (ř. 575–590) |

**Rozhodnutí uživatele 15. 11. 2026:** výplata úroku má mít i možnost „Nepravidelně“; toky pak uživatel zadá ručně
na záložce Smluvní peněžní toky.

**Plán:**
1. `coupon_frequency`: nová hodnota `("irregular", "Nepravidelně")` na konci výběru; nápověda pole doplněna o větu
   „Nepravidelně: toky se zadají ručně na záložce Smluvní peněžní toky.“
2. `action_generate_schedule`: u `irregular` nic negeneruje ani nemaže a vyhodí `UserError`
   „Při nepravidelné výplatě úroku se kalendář negeneruje; zadejte toky ručně na záložce Smluvní peněžní toky: %s.“
   `COUPON_MONTHS` nesmí pro novou hodnotu spadnout na `KeyError`.
3. Tlačítko „Vygenerovat kalendář“ skrýt při `coupon_frequency == 'irregular'`.
4. Výpočet naběhlé hodnoty, kupónových období, obchod, ocenění a účtování se nemění: pracují s toky kalendáře,
   ať vznikly generátorem nebo ručně.

**Rozsah souborů:** `investra_nav/models/instrument_accrual.py`, `investra_nav/views/nav_views.xml`, nový test v
`investra_nav/tests/` (nebo doplnění stávajícího testu generátoru), verze modulu +0.0.1 bez migrace.

**Mimo rozsah:** variabilní sazba (IM-11), `engine.py`, očekávané hodnoty referenčních scénářů, vzhled.

**Kritéria přijetí:**
- Nástroj s `irregular` a ručně zadanými toky (dva kupóny v nestejných rozestupech + jistina) dá stejnou naběhlou
  hodnotu a naběhlý úrok obchodu jako nástroj se stejnými toky a jinou výplatou.
- Generátor u `irregular` skončí uvedenou hláškou a stávající toky nezmění.
- Ostatní hodnoty výplaty generují kalendář jako dosud (stávající testy beze změny).
- Testy `investra_nav,investra_instruments,investra_instrument_master` na dočasné `investra_ci_master` podle oddílu 2
  plánu: 0 selhání, 0 chyb; databázi po testech smazat.

**Commit:** `Výplata úroku: možnost Nepravidelně (toky ručně)`

## Výsledek

## Převzetí
