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

Provedl Claude (Opus 5.5), 16. 11. 2026, větev `ukol/MN-manual`. Nasazení do `investra` neproběhlo (udělá hlavní relace
s MN-10 a MN-11).

**Změny (bod 1, bez odchylky od plánu):** `investra_nav/models/fund_class.py` – `LOCKED_FIELDS = ("code", "currency_id")`,
nový komentář a text chyby; `views/nav_views.xml` – `readonly="movement_locked"` zůstal jen u Kódu a Měny (po povýšení
modulu se zděděný pohled přepíše, atributy u míst a zaokrouhlení zmizí); verze `investra_nav` 20.0.0.31.2 (bez migrace,
schéma se nemění). `investra_fund` beze změny: fond nemá `write` ani zámek, výchozí hodnoty jdou měnit kdykoli (ověřeno).
Manuál: kap. 2 (oddíl „Co nejde po zaúčtování…“) a kap. 3 (oddíl „Co nejde změnit po prvním pohybu“, upozornění na snížení míst kusů).

**Bod 2 – zpětný přepočet (nález: nic se nepřepočítá):**
- Pohyb: kusy (`units`, 6 míst) a cena (`price`, 10 míst) jsou uložené. Místa a zaokrouhlení třídy čte jen kontrola
  při zaúčtování (`movement.py` `_booking_valuation`) a náhled, který se počítá jen v návrhu. Storno (`_do_reverse`)
  kontrolu nevolá → starý pohyb jde stornovat i po snížení míst.
- Ocenění: kurz se počítá v `_finish` (`valuation.py` ř. 1012–1014) jen při výpočtu (stav návrh / spočteno) a ukládá
  se jako text s počtem míst platným při výpočtu. Předložené, schválené a zveřejněné ocenění se nepřepočítá; otisk
  (`_fingerprint`) bere uložené kapitál, kusy a kurz řádků tříd, ne nastavení třídy → změna ho neporuší (test).
  Spočtené a nepředložené ocenění použije nová místa až při dalším výpočtu.
- Stav kusů třídy v ocenění (`_class_context`) je prostý součet uložených kusů pohybů, nezaokrouhluje se.
- Balíček podkladů a historie kurzů (`valuation_price_history`, Float 8 míst) berou uložené hodnoty; místa třídy nepoužívají.
- **Zkreslení zobrazení:** jediné místo je souhrn ocenění `static/src/valuation_summary/valuation_summary.js` (ř. 203, 237):
  kurz a změnu kurzu **starého** ocenění formátuje podle **dnešních** `price_digits` třídy. Po snížení míst (4 → 2)
  ukáže 333,6666 jako 333,67 (zaokrouhleno zobrazením, uložená hodnota je správná); po zvýšení doplní nuly. Seznamy
  a formuláře ukazují uložený text kurzu beze změny. **Návrh (neprogramováno, rozhoduje Martin):** v souhrnu brát
  počet míst z uloženého textu kurzu řádku (`line.price`), ne z třídy – zelená/oranžová zóna, jeden řádek JS.

**Bod 3 – snížení míst kusů pod použitou přesnost (riziko, jen popsáno):** kód stav kusů třídy nezaokrouhluje, uložené
kusy zůstávají. Kontrola „kusy mají víc než N desetinných míst třídy“ ale platí i pro **odkup**: držitel s 10,123456 ks
po snížení na 2 místa odkoupí nejvýš 10,12 ks; zbytek 0,003456 ks už v Odoo odkoupit nejde (držitele eviduje IS,
v Odoo by zůstal stav třídy, který nejde vynulovat). Totéž u **opravy** starého pohybu (kopie pohybu se starými kusy neprojde). **Doporučení:** snížení
`unit_digits` odmítnout, pokud má třída zaúčtovaný nestornovaný pohyb s více místy, než je nová hodnota (kontrola
při zápisu třídy, chyba se jménem pohybu). Zvýšení míst a změna způsobu zaokrouhlení jsou bez rizika. U kurzu podobné
riziko není (kurz se ukládá s každým oceněním zvlášť). Rozhoduje Martin; do té doby upozornění v manuálu kap. 3.

**Testy (bod 4):** `test_class_lock.py` – upraven zámek (jen kód a měna, pohled bez readonly u míst) a 3 nové testy:
změna míst a zaokrouhlení po pohybu jde, kód se společným zápisem dál ne; další úpis použije nová místa a zaokrouhlení
nahoru (3333,34 projde, 3333,33 a 3333,333333 ne), starý pohyb má stejné kusy, částky a doklad; schválené a zaúčtované
ocenění má po změně stejný kurz, kusy, kapitál, FK a otisk, další ocenění spočte kurz na 2 místa nahoru (333,67).
Odchylka jen v testovacích číslech: cena 0,3 místo 3, aby setina kusu nepřekročila toleranci zbytku 0,01.
`investra_nav`: 359 testů, 0 selhání. `all`: 799 testů, 0 selhání (`investra_ci_20261116_165511`, po testech smazána).
