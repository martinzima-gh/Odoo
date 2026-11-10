# AG-013 Nápovědy u prázdných seznamů a nabídka Ocenění

Prázdný seznam dnes jen ukáže „žádné záznamy“. Úkol doplní u šesti hlavních seznamů krátké vysvětlení, k čemu
seznam je a co udělat. Navíc nabídka Ocenění, která má po přesunu kurzů jedinou položku, se změní na přímou položku.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-013-napovedy` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-006, rozhodnutí „Kurzy měn v nabídce“ (2026-11-10) |

**Cíl:**
- Ceny, Obchody, Úpisy a odkupy, Ocenění, Splátky nástrojů a Účetní události mají u prázdného seznamu vysvětlení.
- V hlavní nabídce je „Ocenění“ přímo seznam ocenění, bez podnabídky s jedinou položkou.

**Rozsah souborů:** `addons/custom/investra_instruments/views/instrument_views.xml`,
`addons/custom/investra_nav/views/nav_views.xml`, `addons/custom/investra_posting/views/posting_views.xml`,
`addons/custom/investra_entity/views/entity_views.xml` a sekce Výsledek v tomto souboru.

**Pravidla:** každý blok „Bylo“ nahraď blokem „Bude“ přesně. Když blok „Bylo“ nenajdeš přesně, zastav se
a napiš to do výsledku. Nic jiného neměň.

### 1. Ceny (`instrument_views.xml`)

Bylo:
```xml
        <field name="name">Ceny</field><field name="res_model">investra.instrument.price</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_price_search"/>
```
Bude:
```xml
        <field name="name">Ceny</field><field name="res_model">investra.instrument.price</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_price_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádná cena</p>
            <p>Cena nástroje k datu pro fond. Do ocenění vstupuje jen schválená cena; schválit ji musí jiný uživatel, než který ji zadal.</p>
        </field>
```

### 2. Obchody (`instrument_views.xml`)

Bylo:
```xml
        <field name="name">Obchody</field><field name="res_model">investra.trade</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_trade_search"/>
```
Bude:
```xml
        <field name="name">Obchody</field><field name="res_model">investra.trade</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_trade_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádný obchod</p>
            <p>Nákupy a prodeje nástrojů fondu. Pozice ve fondu se počítají z obchodů, ručně se nezadávají.</p>
        </field>
```

### 3. Úpisy a odkupy (`nav_views.xml`)

Bylo:
```xml
        <field name="name">Úpisy a odkupy</field><field name="res_model">investra.class.movement</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_movement_search"/>
```
Bude:
```xml
        <field name="name">Úpisy a odkupy</field><field name="res_model">investra.class.movement</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_movement_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádný úpis ani odkup</p>
            <p>Pohyby kapitálu a kusů tříd fondu. Dokud nepřicházejí z IS, zadávají se ručně; zaúčtují se jako účetní událost a vstupují do dalšího ocenění.</p>
        </field>
```

### 4. Ocenění (`nav_views.xml`)

Bylo:
```xml
        <field name="res_model">investra.valuation</field>
        <field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_valuation_search"/>
```
Bude:
```xml
        <field name="res_model">investra.valuation</field>
        <field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_valuation_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádné ocenění</p>
            <p>Ocenění fondu k datu. Připravovatel založí ocenění, stiskne Spočítat a po kontrolách ho odešle ke schválení; zaúčtovat lze jen ocenění schválené druhou osobou.</p>
        </field>
```

### 5. Splátky nástrojů (`nav_views.xml`)

Bylo:
```xml
        <field name="name">Splátky nástrojů</field><field name="res_model">investra.instrument.repayment</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_repayment_search"/>
```
Bude:
```xml
        <field name="name">Splátky nástrojů</field><field name="res_model">investra.instrument.repayment</field><field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_repayment_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádná splátka</p>
            <p>Skutečné splátky nástrojů oceňovaných naběhlou hodnotou, například úvěru nebo termínovaného vkladu. Splátka vytvoří účetní událost; rozdíl proti očekávané splátce doúčtuje ocenění.</p>
        </field>
```

### 6. Účetní události (`posting_views.xml`)

Bylo:
```xml
        <field name="res_model">investra.accounting.event</field>
        <field name="view_mode">list</field>
        <field name="search_view_id" ref="view_event_search"/>
```
Bude:
```xml
        <field name="res_model">investra.accounting.event</field>
        <field name="view_mode">list</field>
        <field name="search_view_id" ref="view_event_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">Zatím tu není žádná účetní událost</p>
            <p>Původ každého dokladu, který vytvořily moduly Investra. Události vznikají automaticky a nejdou měnit; oprava se dělá ve zdrojovém záznamu stornem a novou verzí.</p>
        </field>
```

### 7. Nabídka Ocenění bez podnabídky

`entity_views.xml` – Bylo:
```xml
    <menuitem id="menu_valuation_section" name="Ocenění" parent="menu_root" sequence="10"/>
```
Bude: řádek smaž (nabídka zůstane jen jako položka z modulu ocenění).

`nav_views.xml` – Bylo:
```xml
    <menuitem id="menu_valuation" name="Ocenění" parent="investra_entity.menu_valuation_section" action="action_valuation" sequence="10"/>
```
Bude:
```xml
    <menuitem id="menu_valuation" name="Ocenění" parent="investra_entity.menu_root" action="action_valuation" sequence="10"/>
```

Před smazáním řádku v `entity_views.xml` ověř, že `menu_valuation_section` nikde jinde nepoužívá:
```bash
grep -rn "menu_valuation_section" addons/custom
```
Po úpravě nevypíše nic. Když najdeš jiné použití, zastav se a napiš to do výsledku.

**Mimo rozsah:** modely, Python, testy, práva, ostatní akce a nabídky, texty v Účetnictví.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“.

```bash
for f in addons/custom/investra_instruments/views/instrument_views.xml addons/custom/investra_nav/views/nav_views.xml addons/custom/investra_posting/views/posting_views.xml addons/custom/investra_entity/views/entity_views.xml; do python3 -c "import xml.etree.ElementTree as ET,sys; ET.parse(sys.argv[1])" "$f" && echo "XML OK $f"; done
```
Čtyřikrát `XML OK`.

```bash
grep -c 'o_view_nocontent_smiling_face' addons/custom/investra_instruments/views/instrument_views.xml addons/custom/investra_nav/views/nav_views.xml addons/custom/investra_posting/views/posting_views.xml
```
Vypíše `2`, `3` a `1`.

Strom nabídky: skript z AG-006. Pod Investra je `Ocenění (10)  investra_nav.menu_valuation` přímo (bez podnabídky)
a poslední řádek je `Bez rodiče: žádné`.

```bash
git diff --check && git diff --stat HEAD
```
Bez chyb; mění se jen čtyři soubory z Rozsahu a tento soubor.

**Kritéria přijetí:**
- Příkazy výše projdou.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje dotčené moduly v `investra_test`, spustí testy
  a ověří, že stará podnabídka zmizela.

## Výsledek

Úkol provedl Copilot.

- **Změněné soubory:** `addons/custom/investra_instruments/views/instrument_views.xml`, `addons/custom/investra_nav/views/nav_views.xml`, `addons/custom/investra_posting/views/posting_views.xml`, `addons/custom/investra_entity/views/entity_views.xml` a tento soubor (jen sekce Výsledek).
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — Zkontrolováno souborů: 11, chyb: 0; XML parser — všechny čtyři soubory `XML OK`; `grep -c 'o_view_nocontent_smiling_face' ...` — 2, 3 a 1; `grep -rn "menu_valuation_section" addons/custom` po změně — bez výstupu (návratový kód 1, očekávaný při nulových shodách). Strom nabídky obsahuje `Ocenění (10) investra_nav.menu_valuation` přímo pod Investra, Kurzy měn jsou mimo tuto nabídku a poslední řádek je `Bez rodiče: žádné`. `git diff --check` — bez chyb; finální `git diff --stat HEAD` ověřil čtyři XML soubory a toto zadání.
- **Neověřeno:** vzhled nápověd a nabídky v běžícím Odoo; aktualizace modulů a Odoo testy. Docker ani databáze nebyly spuštěny.
- **Otevřené otázky a návrhy mimo rozsah:** žádné.

## Převzetí

- **Datum:** 2026-11-10
- **Provedl:** GitHub Copilot (režim Agent v okně na `~/odoo-review`) podle rozhodnutí 2026-11-09 „Copilot jako náhradní
  vývojář“. Commit `aab3484` s autorem „Copilot“ udělal Claude v klonu.
- **Sloučení:** `aab3484` do `feature/nav-prototyp` (fast-forward).
- **Revize:** diff mění jen bloky ze zadání (zelená zóna); všech šest nápověd a nová nabídka jsou v souborech beze změny
  znaků, `menu_valuation_section` zmizel. Nálezy: žádné.
- **Testy:** `check_views.py` – chyb: 0; `-u investra_entity,investra_instruments,investra_nav,investra_posting`
  s jejich testy nad `investra_test` – 0 failed, 0 error(s) of 202 tests.
- **Databáze `investra_test`:** záznam `menu_valuation_section` odstraněn, Ocenění je přímo pod Investra (pořadí 10),
  všech šest akcí má nápovědu.
- **Neověřeno:** vzhled nápověd v prohlížeči.
