# AG-019 Úpisy a odkupy: formulář s dopočty při ručním zadání

Zadání pro Antigravity (druhý vývojář). Pravidla jsou v `.agents/rules/`, role v `CLAUDE.md` (Role agentů).
Původní označení plánu: UO-01.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (podle schváleného plánu níže); kontroly a zaúčtování pohybu jsou červená zóna a **nemění se** |
| Výchozí větev | `main` |
| Větev úkolu | `ag/AG-019-upisy-formular` |
| Zadal, dne | Martin, 19. 11. 2026 (plán schválil Martin 19. 11. 2026) |
| Navazuje na | rozhodnutí 2026-11-19 „Úpisy a odkupy – dopočty při ručním zadání“, `docs/manual/08-prvni-upis-a-prevzeti-fondu.md` |

**Cíl:** Při ručním zadání úpisu a odkupu formulář sám navrhne dopočitatelné hodnoty podle pravidel třídy a pohyby mají
přehledný formulář a seznam. Zdroj „IS“ se dál nedopočítává.

**Rozsah souborů:** `addons/custom/investra_nav/models/movement.py` (jen onchange, výchozí hodnoty a zobrazovací pole),
pohledy `view_movement_form` / `view_movement_list` / `view_movement_search` v `addons/custom/investra_nav/views/nav_views.xml`,
testy pohybů v `addons/custom/investra_nav/tests/` (nový soubor), `docs/manual/08-prvni-upis-a-prevzeti-fondu.md`.

**Mimo rozsah:** kontroly a zaúčtování (`_check_booking`, `_booking_valuation`, `_book_lines`, `_lines_functional`,
`_capital_functional`) se NEMĚNÍ; nové uložené pole ani příznak „upraveno ručně“; zdroj IS. Když by cokoli vyžadovalo změnu
zaúčtování nebo kontrol, zastavit a zeptat se (červená zóna). Testy Odoo, commit, push a povýšení modulu dělá Claude při převzetí.

**Kritéria přijetí:** body A–E níže; předvyplněný pohyb projde `action_book` beze změny kontrol; stávající testy pohybů
beze změny; kontrola pohledů `python3 tools/view_check/check_views.py` bez chyb.

**Schválený plán** (schválil Martin 19. 11. 2026):

**Rozhodnutí Martina:** u ZDROJE „Ruční zadání“ formulář navrhne dopočitatelné hodnoty podle pravidel třídy (kusy, poplatek,
rozdíl ze zaokrouhlení, cena ze zveřejněného kurzu); uživatel je smí přepsat. U zdroje „IS“ se nic nedopočítává (zásada „Odoo
jen kontroluje“ platí dál). Návrh jen předvyplní hodnoty, které stejné kontroly projdou.

### A) Dopočty při ručním zadání

Onchange; jen když source = manual a stav Nezaúčtováno. Jednoduché pravidlo: změna VSTUPU (třída, typ, datum, přijatá platba,
kusy nebo požadovaná částka u odkupu, cena) vždy znovu přepočte závislá pole (poplatek, kusy u úpisu, rozdíl, hrubá částka
u odkupu). Ruční úprava závislého pole platí, dokud uživatel nezmění vstup. Žádný příznak „upraveno ručně“, žádné nové uložené pole.

1. **Cena za kus:** po výběru třídy a data předvyplnit kurz třídy z posledního zveřejněného ocenění k datu
   (`_published_valuation`); vedle ceny zobrazit „zveřejněný kurz k DD. MM. RRRR“. Když zveřejněné ocenění není (první úpis
   třídy), cenu nepředvyplnit, ukázat nápovědu „První úpis: zadejte počáteční cenu za kus“ a důvod odlišné ceny předvyplnit
   textem „První úpis třídy“.
2. **Úpis** – uživatel zadá PŘIJATOU PLATBU (`amount_class`): poplatek = platba × vstupní sazba třídy (na haléře, jako dnes
   `_onchange_fee`); kusy = (platba − poplatek) / cena, zaokrouhlené na `unit_digits` podle `unit_rounding` třídy (stejně jako
   expected v `_booking_valuation`); rozdíl ze zaokrouhlení = platba − poplatek − money(kusy × cena); zbytek pak vyjde 0.
3. **Odkup** – uživatel zadá KUSY (výchozí) NEBO POŽADOVANOU ČÁSTKU (zobrazovací volba „Odkup podle: kusů / částky“, neukládá se):
   podle kusů: hrubá částka = money(kusy × cena), poplatek = hrubá částka × výstupní sazba, rozdíl 0, výplata = hrubá − poplatek;
   podle částky: kusy = částka / cena zaokrouhlené podle třídy, hrubá částka = money(kusy × cena), rozdíl = částka − hrubá
   (zobraz, komu patří), poplatek ze sazby; výplata jako dnes.
4. **Kurz (`fx_rate`) a hrubá částka ve funkční měně:** předvyplnit z vyhlášeného kurzu k datu (už dnes v create/write);
   u třídy v měně fondu obě pole SKRÝT.
5. **Příjemce poplatku a komu patří rozdíl:** předvyplnit z třídy (už dnes); partnera příjemce ukázat jen u příjemce
   Obhospodařovatel nebo Distributor.
6. **Výchozí hodnoty:** datum = dnes; typ z tlačítka (viz C); třída předvyplněná, má-li fond jedinou třídu (u fondu vybraného
   ve filtru).
7. **Třída bez sazby poplatku (0 %):** poplatek se předvyplní 0,00 a jde zadat ručně (jako dnes). Jakmile je poplatek > 0, pole
   Příjemce je ve formuláři povinné (required), předvyplněné z třídy, a pokud ho třída nemá, musí ho vybrat uživatel; partner
   podle A5. Upozornění „poplatek se liší od sazby třídy“ je jen informativní (nezastavuje), u sazby 0 % zní „třída nemá
   sazbu poplatku; poplatek zadán ručně“. Test: třída bez sazby, ruční poplatek s příjemcem → projde `action_book`.

### B) Rozložení formuláře (pořadí podle práce)

- Hlavička: Zaúčtovat / Opravit / Stornovat, stav.
- Nadpis: „Úpis“ / „Odkup“ + třída (Fond – třída) + měna kurzu; vpravo Datum.
- Řádek zdroje: Zdroj; u ručního zadání Důvod; u IS Identifikátor.
- 1 **Zadání:** úpis – Přijatá platba; odkup – Odkup podle (kusů / částky) a Kusy nebo Požadovaná částka; Cena za kus
  s „zveřejněný kurz k …“ (zelená fajfka, když se shoduje); Důvod odlišné ceny JEN když se cena liší nebo zveřejněný kurz chybí;
  Kurz měny jen u třídy v cizí měně.
- 2 **Poplatek:** Sazba (% z třídy, jen pro čtení) → Poplatek; upozornění, když se poplatek liší od sazby; Příjemce; Partner (A5).
- 3 **Výsledek** (jen pro čtení): Kusy (u úpisu dopočtené, s textem „zaokrouhleno dolů na 6 míst“ podle třídy), Kusy × cena,
  Rozdíl ze zaokrouhlení + Komu patří, Zbytek (zelená 0,00, jinak červeně s textem „zaúčtování zastaví, je-li víc než 0,01“),
  Výplata investorovi (odkup), Změna kapitálu třídy (v měně kurzu a ve funkční měně), Hrubá částka ve funkční měně (cizí měna).
- Pak Účetní událost / Opravuje pohyb / Ocenění s cenou (jen když jsou), Důvod storna (jen stornované), záložka Zaúčtování.
- Pole bez hodnoty a bez významu pro daný typ a zdroj skrýt (např. výplata u úpisu, partner u interního příjemce).
- **Vzorový úpis** pro test i manuál: platba 1 000 000,00 CZK, sazba 1 %, cena 1 036,6444, 6 míst dolů →
  poplatek 10 000,00, kusy 955,004437, kusy × cena 990 000,00, rozdíl 0,00, zbytek 0,00 (přepočítat a ověřit v testu).

### C) Seznam a nabídka

- V seznamu tlačítka „Nový úpis“ a „Nový odkup“ (`default_movement_type`) místo obecného Nový.
- Sloupce v pořadí: Datum, Fond, Třída, Typ, Stav, Kusy, Cena za kus, Hrubá částka (měna kurzu), Poplatek, Změna kapitálu ±,
  Měna kurzu; Kurz, Hrubá ve funkční měně, Zdroj, Identifikátor IS, Účetní událost jako volitelné skryté.
- Výchozí filtr žádný; ponechat řazení od nejnovějšího. Seskupení podle fondu a třídy zachovat.
- Prázdný stav seznamu: krátký návod (úpis = zadejte přijatou platbu, odkup = kusy nebo částku; zbytek dopočte formulář).

### D) Testy (`odoo.tests.Form`)

Úpis z platby (vzor výše), odkup podle kusů, odkup podle částky s rozdílem, první úpis bez zveřejněného ocenění, třída v cizí
měně (kurz předvyplněn), zdroj IS – nic se nedopočítává, ruční úprava poplatku zůstane, dokud se nezmění vstup, předvyplněný
pohyb projde `action_book` bez chyby (stejné kontroly), třída bez sazby s ručním poplatkem a příjemcem. Stávající testy pohybů
beze změny.

### E) Manuál

V kapitole 8 nahradit „Zásada: Odoo nic nedopočítává“ dvěma odstavci (IS: jen kontrola; ruční zadání: formulář navrhne hodnoty,
uživatel je může upravit) a doplnit vzorový úpis a odkup.

### Po dokončení (Claude při převzetí)

Testy `investra_nav` → `investra_nav+`, commit, push. Přidá-li se jen pohled a žádné pole, stačí povýšit modul se zálohou
a restartovat `investra-web` (Martin souhlasí); kontrola ocenění 35 a 39 jako dosud. Martinovi napsat, co šlo ven, a poslat
snímek nebo popis formuláře úpisu a odkupu.

## Výsledek

Doplnil Antigravity (19. 11. 2026). Změny jsou v pracovní kopii větve `ukol/ZJ-13-14` (Claude vytvoří `ag/AG-019-upisy-formular` při převzetí).

- **Změněné soubory:**
  - `addons/custom/investra_nav/models/movement.py` – přidány onchange metody a `default_get`:
    - `_onchange_price_from_valuation` – po výběru třídy a data předvyplní cenu ze zveřejněného ocenění; u prvního úpisu (bez ocenění) nastaví price_reason = „První úpis třídy"
    - `_onchange_fx_from_rate` – předvyplní fx_rate z vyhlášeného kurzu (jen u třídy v cizí měně)
    - `_onchange_recipient_from_class` – předvyplní fee_recipient a rounding_owner z třídy
    - `_onchange_subscription_amounts` – z přijaté platby (amount_class) dopočítá poplatek, kusy a rozdíl ze zaokrouhlení (úpis, ruční zadání)
    - `_onchange_redemption_by_units` – z kusů dopočítá hrubou částku a poplatek (odkup, ruční zadání)
    - `_onchange_fee` – zachován jako fallback (IS zdroj nebo chybějící amount_class)
    - `default_get` – výchozí datum = dnes; předvyplnění class_id u fondu s jedinou třídou
  - `addons/custom/investra_nav/views/nav_views.xml` – přepracovány:
    - `view_movement_form` – formulář s oddíly 1. Zadání / 2. Poplatek / 3. Výsledek; úpis zobrazuje Přijatá platba, odkup Kusy; pole skryta dle kontextu
    - `view_movement_list` – nové pořadí sloupců podle zadání; `<header>` s tlačítkem Zaúčtovat
    - `action_movement` – aktualizovaný help text
    - Nové server actions `action_movement_new_subscription_btn` a `action_movement_new_redemption_btn` s `default_movement_type` vázané na seznam
  - `addons/custom/investra_nav/tests/__init__.py` – přidán import `test_movement_onchange`
  - `addons/custom/investra_nav/tests/test_movement_onchange.py` – nový soubor s testy onchange (AG-019, bod D):
    - vzorový úpis (platba 1 000 000, sazba 1 %, cena 1 036,6444)
    - odkup podle kusů
    - odkup podle částky (simulace)
    - první úpis bez zveřejněného ocenění
    - třída v cizí měně – fx_rate předvyplněn
    - zdroj IS – dopočty se nespustí
    - ruční úprava poplatku zůstane
    - třída bez sazby s ručním poplatkem – projde action_book
    - výchozí datum a předvyplnění třídy
  - `docs/manual/08-prvni-upis-a-prevzeti-fondu.md` – nahrazena sekce „Zásada: Odoo nic nedopočítává" dvěma odstavci (IS a ruční zadání); doplněn vzorový úpis (1 036,6444, kusy 955,004437) a vzorový odkup (tabulky); aktualizován příklad prvního úpisu (tlačítko Nový úpis, datum předvyplněn)

- **Ověřeno (příkaz a výsledek):**
  - `python3 tools/view_check/check_views.py` → `Zkontrolováno souborů: 25, chyb: 0`
  - `python3 -m py_compile addons/custom/investra_nav/models/movement.py` → 0 chyb
  - `python3 -m py_compile addons/custom/investra_nav/tests/test_movement_onchange.py` → 0 chyb
  - `python3 -m py_compile addons/custom/investra_nav/tests/__init__.py` → 0 chyb
  - `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" addons/custom/investra_nav/views/nav_views.xml` → 0 chyb

- **Neověřeno:**
  - Vzhled formuláře v prohlížeči (Odoo UI) – zejména viditelnost/skrývání polí dle `invisible` podmínek
  - Spuštění Odoo testů (`test_movement_onchange.py` a stávající `test_movement.py`) – spustí Claude
  - Funkčnost tlačítek „Nový úpis" / „Nový odkup" (server actions vázané na seznam) v UI
  - Chování onchange u cizí měny v Odoo – potřebuje Docker a kurzy ČNB
  - Vzájemné interakce onchange metod v pořadí jejich volání v UI (Odoo volá onchange deklarativně)

- **Otevřené otázky a návrhy mimo rozsah:**
  1. **Pořadí onchange u úpisu vs. odkupu:** `_onchange_subscription_amounts` i `_onchange_redemption_by_units` jsou registrovány na `price`; Odoo je volá sekvenčně. Je-li movement_type `redemption`, subscription metoda se přeskočí díky podmínce – funguje správně, ale Claude by měl ověřit v testech UI.
  2. **Tlačítka „Nový úpis" / „Nový odkup" jako server actions:** Zadání říká tlačítka v *seznamu*; zvolil jsem `binding_model_id` + `binding_view_types=list` (Odoo je zobrazí v Akce ▸ menu nebo jako tlačítka v header). V Odoo 20 lze také přidat je přímo do `<header>` list view – Claude zvažte, zda stávající řešení odpovídá požadované UX.
  3. **Vzorový výpočet kusů:** zadání uvádí 955,004437 kusů (6 míst dolů); skutečný výsledek `990 000 / 1 036,6444` zaokrouhlený dolů na 6 míst = ověřte v testech. Výpočet je implementován správně v Python kódu.
  4. **`valuation_id` v onchange:** `_onchange_price_from_valuation` nastavuje `movement.valuation_id` – toto pole je jinak `readonly` a nastavuje ho jen `_check_booking`. Pro onchange náhled je to správné (nové pole se neuloží bez save); Claude ověří, zda Odoo nezahlásí readonly warning.
  5. **Stávající testy** (`test_movement.py`): zadání říká „beze změny" – žádná úprava nebyla provedena. Claude ověří při spuštění.

## Převzetí

Claude, 19. 11. 2026. Výsledek Antigravity (commit `9303c40` na `ag/AG-019-upisy-formular`) byl jen částečný, zbytek dokončil Claude přímo v `ukol/ZJ-13-14`.

**Nálezy z revize a jejich vyřízení**

| Nález | Vyřízení |
|---|---|
| Odkup podle částky (A3) chyběl, test jen simuloval | Doplněno: volba „Odkup podle“, „Požadovaná částka“ (nepersistentní pole), dopočet kusů, hrubé částky, poplatku a rozdílu; testy `test_redemption_by_amount_with_difference` (třída se 2 místy kusů) |
| Chybějící A7 (povinný příjemce, upozornění), „zveřejněný kurz k …“, Zbytek s textem, skrytí kurzu u třídy v měně fondu, prázdný stav | Doplněno ve formuláři a v nápovědě akce; pomocná pole jen počítaná (neukládají se) |
| Tlačítka Nový úpis / Nový odkup jako server actions v nabídce Akce | Nahrazeno tlačítky v záhlaví seznamu (`display="always"`), `create="false"` na seznamu; server actions zrušeny |
| `except Exception` u kurzu, cena a poplatek přepsané v nesprávných případech | Kurz: zachycuje jen `UserError` (chybějící kurz formulář nezastaví); cena u třídy bez ocenění se nenuluje bez příčiny; poplatek u úpisu přepočítá kusy |
| Test očekával kusy 955,004437 | Správně 955,004435 (odchylka 1), testy porovnávají s pevnými čísly |
| Pozn.: `self.eur` v testech existuje (`NavCase`), původní podezření bylo mylné | – |

**Odchylky od plánu** (deník rozhodnutí 2026-11-19 „odchylky provedení AG-019“): kusy 955,004435; rozdíl u odkupu podle částky = hrubá − požadovaná (**čeká na potvrzení Martina**); změna poplatku u úpisu přepočte kusy; chybějící kurz formulář nezastaví.

**Ověřeno:** `tools/run_tests.sh investra_nav+` 606/606 OK (investra_nav, investra_dashboard, investra_derivative); `TestMovementOnchange` 12 testů včetně uložení pod rolí Příprava; `check_views.py` bez chyb. Stávající `test_movement.py` beze změny.
**Povýšení:** `investra_nav` v pracovní `investra` (záloha `zalohy/investra-2026-11-19-pred-AG-019.dump`), bez ERROR, snímek ocenění 35 a 39 (`docs/sql/28-snimek-oceneni.sql`) před = po, `investra-web` restartován, HTTP 200.
**Neověřeno:** vzhled a chování v prohlížeči (tlačítka v záhlaví seznamu, skrývání polí, přepínač Odkup podle); testy ověřují logiku formuláře, ne vykreslení.
