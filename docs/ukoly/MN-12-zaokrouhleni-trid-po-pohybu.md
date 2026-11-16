# MN-12 Zaokrouhlení a desetinná místa třídy jdou měnit i po prvním pohybu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (kurz a kusy třídy, NAV); plán schválil Martin poznámkou 3 z průchodu 16. 11. 2026 |
| Výchozí větev | `ukol/MN-manual` (po MN-11) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-16 „Poznámky z průchodu 2“ bod 3 (mění rozhodnutí 2026-11-16 „Zámek tříd…“ z MN-07) |

**Požadavek (Martin):** po prvním zaúčtovaném úpisu nebo odkupu třídy jdou dál měnit Zaokrouhlení kurzu, Desetinná místa
kurzu, Zaokrouhlení kusů a Desetinná místa kusů. Už vzniklé transakce se nepřepočítávají. Zamčené zůstávají Kód a Měna
zveřejnění kurzu. Totéž platí pro výchozí hodnoty ve fondu (ty zamčené nejsou, jen ověřit).

**Plán (od Clauda; provádějící model ověří a odchylky popíše):**

1. `investra_nav/models/fund_class.py`: z `LOCKED_FIELDS` vyjmout `price_digits`, `price_rounding`, `unit_digits`,
   `unit_rounding`; upravit komentář a text chyby („… nejde změnit: Kód, Měna zveřejnění kurzu. Poplatky, příjemce,
   zaokrouhlení a desetinná místa změnit jde; zaúčtované pohyby se nepřepočítají.“). Formulář třídy: pole jen pro čtení
   podle `movement_locked` ponechat jen u kódu a měny.
2. Ověřit, že se nic nepřepočítá zpětně: zaúčtované pohyby (kusy, částky), schválená a zveřejněná ocenění (řádky tříd,
   otisk ocenění `valuation.py` kolem ř. 1372), balíček podkladů. Zjistit, zda zobrazení uložených kusů nebo kurzu bere
   počet míst z třídy (pole `digits` odvozené z třídy, `valuation_summary.js`); pokud by snížení míst zkreslilo zobrazení
   starých hodnot, popsat to ve Výsledku a navrhnout řešení – neprogramovat bez Martina.
3. Riziko k popisu: snížení desetinných míst kusů, když držitelé už mají kusy s více místy (stav třídy pak nejde
   vyjádřit v nové přesnosti). Zjistit, zda kód stav kusů třídy zaokrouhluje; doporučit, zda snížení míst pod nejvyšší
   použitou přesnost odmítnout. Rozhoduje Martin – do té doby jen popsat.
4. Testy: po zaúčtovaném pohybu jde změnit zaokrouhlení a místa, kód a měna dál ne; další pohyb použije nové zaokrouhlení;
   starý pohyb a schválené ocenění mají stejné hodnoty jako před změnou. Celá sada `all`.
5. Nasazení: povýšení `investra_nav` (případně `investra_fund`) v `investra` se zálohou, restart 8071. Manuál:
   `docs/manual/02-fond.md` (oddíl „Co nejde po zaúčtování…“) a `03-tridy.md`.

**Rozsah souborů:** `investra_nav` (`fund_class.py`, view třídy, testy, verze), případně `investra_fund`, manuál kap. 2 a 3,
tento soubor, předávka.

**Mimo rozsah:** přepočet historických pohybů a ocenění.

**Kritéria přijetí:** testy `all` bez selhání na `investra_ci_*`; Výsledek obsahuje nález k bodům 2 a 3.

## Výsledek

(doplní provádějící model)
