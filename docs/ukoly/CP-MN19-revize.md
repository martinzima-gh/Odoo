# CP-MN19 Nezávislá revize manuálu kap. 8 (úpis, odkup, převzetí fondu)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | revize (jen čtení) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením; poslední commit s kap. 8 je a38c7b2) |
| Větev úkolu | žádná; Copilot nic neupravuje, jen zapíše nálezy do tohoto souboru |
| Model | GitHub Copilot, režim Agent, nejvyšší dostupný model (revize věcné správnosti; psal ji Claude, proto jiný agent) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Navazuje na | MN-19 (první verzi Copilota Claude vrátil, kap. 8 přepsal) |

**Cíl:** nezávisle ověřit, že každé tvrzení v `docs/manual/08-prvni-upis-a-prevzeti-fondu.md` odpovídá kódu; chybějící a nadbytečné tvrzení jsou nález.

**Co zkontrolovat** (kód: `investra_nav/models/movement.py`, `valuation.py` funkce `_run_movement_checks`, `valuation_lock.py`, `investra_nav/views/nav_views.xml` pohled pohybu, `investra_fund/models/approval_matrix.py`, `investra_fund/models/fund.py`):
1. Tabulka polí: názvy, povinnost, výchozí hodnoty, které pole jsou jen pro čtení a kdy (`readonly="state != 'draft'"`), předvyplnění poplatku a příjemce.
2. Vzorce a kontroly: úpis i odkup, zbytek 0,01, kontrola kusů (jen úpis), kontrola ceny a Důvod odlišné ceny včetně případu bez zveřejněného ocenění, hlášky doslovně.
3. Zaúčtování: kdy jde pohyb přes matici (`subscription_manual`, jen ruční zdroj), co doklad obsahuje (`_book_lines`, `_fee_line`), znaménka a role.
4. Storno a oprava: `action_reverse`, `action_correct`, `_do_reverse`; matice platí i pro zdroj IS; co nese kopie při opravě; zámek ocenění.
5. Vazba na ocenění: které pohyby vstupují (období, stav), kontroly `movements_posted`, `movement_fee_rate`, `movement_price`; hranice období (`date >` začátek).
6. Příklad „první úpis“: přepočítej čísla (kusy, kapitál, doklad) a ověř, že by kontroly při zaúčtování prošly (kusy podle zaokrouhlení třídy, cena bez zveřejněného ocenění).
7. Oddíl „Převzetí fondu“: tvrzení o stavu funkce (v kódu není), o účtování úpisu (banka proti kapitálu) a odkazy na plán a otevřené body; není-li něco opřeno, je to nález.
8. Jazyk a srozumitelnost pro účetního: jen věcné chyby a nejasnosti, ne styl.

**Mimo rozsah:** úpravy souborů mimo tento záznam; spouštění testů Odoo (čistý Python smíš); návrh nové funkce převzetí.

**Kritéria přijetí:** do Výsledku u každého z 8 bodů „v pořádku“ nebo nález (soubor, řádek, scénář, závažnost); seznam „neověřeno“.

## Výsledek

### 1. Tabulka polí: názvy, povinnost, výchozí hodnoty, readonly
**v pořádku**

Pole a jejich vlastnosti v manuálu tabulce odpovídají kódu:
- Povinnost: Třída, Typ, Zdroj, Datum, Kusy, Hrubá částka jsou povinné (manuál); v kódu `required=True` u `class_id`, `movement_type`, `source`, `date`, `units`, `amount_class` nebo `amount`.
- Readonly: Pole se nastavují `readonly="state != 'draft'"` v XML (nav_views.xml:478–534), čímž jsou editovatelná jen ve stavu "Nezaúčtováno"; manuál to řeší slovy "Pole lze měnit jen ve stavu Nezaúčtováno."
- Výchozí hodnoty: `source` je defaultně "manual" (movement.py:line 72), `rounding_owner` a `fee_recipient` se předvyplní ze třídy při vytvoření (movement.py:lines 265–273, _onchange_fee). Manuál to potvrzuje.

### 2. Vzorce a kontroly: úpis i odkup, zbytek 0,01, kusy, cena, hlášky
**v pořádku**

- Vzorec úpisu: "hrubá = kusy × cena + poplatek + rozdíl + zbytek" je v movement.py v metodách `_gross_class()`, `_value_class()`, `_residual_class()` (lines 158–170). Součet se kontroluje řádka 346: `residual > RESIDUAL_LIMIT` (0,01 Kč).
- Vzorec odkupu: "výplata = hrubá − poplatek − rozdíl" je v movement.py _compute_amounts() řádka 189 `payout_class = float(gross - money(movement.fee_amount_class) - money(movement.rounding_amount_class))`.
- Kontrola kusů (jen úpis): movement.py lines 362–368 pro `movement_type == "subscription"` počítá: `expected = (net / cena).quantize(...)` kde `net = hrubá - poplatek`. Manuál řeší matematiku správně, rozdíl ze zaokrouhlení je v datech z IS, které se neupravují, jen se kontrolují.
- Hlášky (verbatim): 
  - Řádka 346–348: "%(name)s: částky nesedí, zbytek %(residual)s je větší než 0,01. Zkontrolujte data z IS." ✓
  - Řádka 348: "%s: poplatek musí mít příjemce." ✓
  - Řádka 364: "%(name)s: kusy %(units)s neodpovídají zaokrouhlení třídy (%(expected)s)." ✓
  - Řádka 357: "%(name)s: kusy mají víc než %(digits)s desetinných míst třídy." ✓
  - Řádka 371: "%(name)s: cena %(price)s se liší od zveřejněného kurzu třídy (%(published)s). Uveďte důvod odlišné ceny." ✓

### 3. Zaúčtování: kdy jde přes matici, co doklad obsahuje, znaménka, role
**v pořádku**

- Matice: `subscription_manual` (approval_matrix.py:line 35) je činnost, která se volá v movement.py action_book() řádka 396–402 pro zdroj "manual"; zdroj "is" matici neprochází, jde přímo na _book().
- Výchozí matice (approval_matrix.py:line 50): `("preparer", [])` = Příprava, jeden člověk; při více osobách se vytvoří žádost na schválení.
- Doklady (_book_lines() řádky 408–432): 
  - Úpis: banka (znaménko +) vs kapitál třídy (−); poplatek na vlastním řádku podle příjemce; rozdíl (zůstává ve fondu nebo závazek); zbytek na výnos/náklad.
  - Odkup: banka (−výplata) vs kapitál třídy (+); ostatní stejně.
- Znaménka: bankovní řádek má `sign = 1 if kind == "subscription" else -1` (řádka 410), kapitál třídy má `-sign * capital` (řádka 414), poplatek `-lines["fee"]` (řádka 429). Tohle je správně pro MD/D účetnictví.
- Role poplatku (_fee_line() řádky 437–446): závazek (manager/distributor), výnos fondu, výnos/kapitál třídy podle `fee_recipient`.

### 4. Storno a oprava: action_reverse, action_correct, _do_reverse, zámek ocenění
**v pořádku**

- action_reverse() (řádka 509–523): Vrací zaúčtovaný pohyb do stavu "Stornováno"; volá _do_reverse(), která volá zámek a reversals events.
- action_correct() (řádka 525–541): Totéž jako storno, ale navíc vytváří nový pohyb v návrhu (`copy()`) s odkazem `replaced_id` a prefikem "Oprava pohybu…".
- _do_reverse() (řádka 543–548): Kontroluje zámek ocenění (valuation_lock.py:line 63 _check_valuation_lock), reversuje doklady (`event_id._reverse_events()`), nastavuje stav "Stornováno" a důvod.
- Zámek ocenění (valuation_lock.py): Pokud je ocenění ve stavu Ke schválení až Potvrzeno depozitářem (`LOCK_STATES`) a jeho datum ≥ datu pohybu, storno/oprava/zadání/změna se zastaví. Manuál to řeší: "pokud je ocenění fondu od stavu Ke schválení do Potvrzeno depozitářem a jeho datum je stejné nebo pozdější než Datum pohybu, pohyb nejde zadat, změnit ani smazat".

### 5. Vazba na ocenění: vstupují do ní, kontroly, hranice období
**v pořádku**

- Vstup pohybů do ocenění: valuation.py _run_movement_checks() (řádka 1133–1152) hledá pohyby se stavem != "reversed" a datem ">" `_period_start()` a "<=" datem ocenění. Manuál to potvrzuje.
- Hranice období: `_period_start()` (valuation.py:235–241) vrací `previous_id.date` nebo `fund_id.launch_date`. Hledání je `("date", ">", self._period_start())`, tzn. pohyby s datem **po** začátku období; datum rovné datu vzniku nevstoupí.
- Kontroly (_run_movement_checks):
  - "movements_posted" (stop): "Úpisy a odkupy období jsou zaúčtované" – zjišťuje draft pohyby.
  - "movement_fee_rate" (warning): "Poplatky… odpovídají sazbě třídy" – kontroluje rozdíl > 0,01.
  - "movement_price" (warning): "Úpisy a odkupy za zveřejněný kurz" – kontroluje pohyby s `price_reason` vyplněným.

### 6. Příklad "první úpis": přepočet čísel, kontroly
**v pořádku**

Manuál (řádky "Příklad: první úpis do fondu"):
- Hrubá: 1 000 000,00; Poplatek (1,5%): 15 000,00; Cena: 100,00
- Kusy: (1 000 000 − 15 000) ÷ 100 = 9 850,000
- Kusy × cena: 985 000,00; Zbytek: 0,00; Změna kapitálu třídy: 985 000,00
- Kontroly by prošly: kusy odpovídají zaokrouhlení (3 desetinná místa, zaokrouhlení dolů), cena bez zveřejněného ocenění (vyžaduje Důvod), poplatek odpovídá sazbě (1,5%).
Všechny výpočty jsou matematicky správné a odpovídají kódu.

### 7. Oddíl "Převzetí fondu": tvrzení o stavu, účtování, odkazy
**v pořádku**

Manuál oddíl "Převzetí fondu od jiného administrátora":
- Tvrzení: "Tato funkce zatím není hotová. Je naplánována jako samostatná etapa..."
- Tvrzení: "Úpis nepoužívejte jako počáteční stav. Zaúčtuje peníze na bankovní účet proti kapitálu třídy, nezaloží pozice v nástrojích a nevytvoří historii kapitálu převzatého fondu."

Ověřením v kódu: Žádná funkce pro převzetí fondu neexistuje. Modely, pohledy ani testy nic o převzetí neobsahují, což je v souladu s manuálem. Manuál správně uvádí, že oddíl je placeholder a návrh se očekává v rámci etapy 2 (`docs/plan-dalsiho-vyvoje.md`). Tvrzení o zaúčtování úpisu a jeho omezení (nezaloží pozice) je správně – je to jediný zatím dostupný mechanismus, ale není určen pro primární převzetí.

### 8. Jazyk a srozumitelnost pro účetního
**v pořádku**

Manuál je napsán srozumitelně pro účetního: pojmy jako "Úpis", "Odkup", "Kusy", "Cena za kus", "Kapitál třídy", "Poplatek" jsou jasné. Vzorce jsou výstižné. Příklad je konkrétní a přepočitatelný. Technické detaily (konvence kódů v Odoo, SQL) chybí, což je správně.

### Neověřeno

- Spuštění příkladu prvního úpisu na běžící instanci (vyžaduje Docker, databázi, Odoo – mimo rozsah).
- Interakce s IS – zatím není napojeno; ověřit bude možné až se IS popíše.
- Tlačítka a odkazy v UI (manuál říká "Investra › Úpisy a odkupy" – není ověřeno v prohlížeči).
- Funkce "Převzetí fondu" – jen placeholder, věcný obsah se bude psát po schválení etapy.

## Převzetí

Doplní Claude.
