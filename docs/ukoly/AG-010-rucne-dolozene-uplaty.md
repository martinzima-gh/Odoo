# AG-010 Ručně doložené úplaty v ocenění

Záložka „Výpočty mimo Odoo“ ve formuláři ocenění není srozumitelná (poznámka 17 z 10. 11. 2026). Jde o výjimku:
částka úplaty po třídách spočtená mimo Odoo, s důvodem a povinnou přílohou, která vstoupí do ocenění jako úplata
a zaúčtuje se s oceněním po schválení.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `revize/claude-app` |
| Větev úkolu | `ag/AG-010-rucne-dolozene-uplaty` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-008 (stejný soubor `nav_views.xml`; začni až po jeho sloučení) |

**Cíl:** Záložka se jmenuje „Ručně doložené úplaty“, nahoře má upozornění, že jde o výjimku, a u ocenění
od stavu Ke schválení dál se bez záznamů nezobrazuje. Filtr v pravidlech úplat má stejný název.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml` (jen dva řádky níže) a sekce Výsledek
v tomto souboru. Modul `investra_nav` je jinak v červené zóně: `models/` a `engine.py` jen čti.

**1. Záložka ve formuláři ocenění** (`view_valuation_form`).

Bylo:
```xml
                        <page string="Výpočty mimo Odoo"><field name="external_fee_ids"><list editable="bottom">
```
Bude:
```xml
                        <page string="Ručně doložené úplaty" invisible="not external_fee_ids and state in ('submitted', 'approved', 'posted', 'sent', 'confirmed', 'published')">
                            <div class="alert alert-warning" role="alert">Výjimka: úplata spočtená mimo Odoo. Každý řádek potřebuje důvod a přílohu s výpočtem. Částka vstoupí do ocenění jako úplata a zaúčtuje se s oceněním po schválení.</div>
                            <field name="external_fee_ids"><list editable="bottom">
```

Konec téže záložky zůstává beze změny (`</list></field></page>` na následujícím řádku stále uzavírá `list`,
`field` a `page`).

**2. Filtr v pravidlech úplat** (`view_fee_rule_search`).

Bylo:
```xml
                <filter name="filter_external" string="Výpočet mimo Odoo" domain="[('kind', '=', 'external')]"/>
```
Bude:
```xml
                <filter name="filter_external" string="Ručně doložená úplata" domain="[('kind', '=', 'external')]"/>
```

Když se některý blok „Bylo“ nenajde přesně, zastav se a napiš to do výsledku. Nic jiného neměň.

**Mimo rozsah:** popisek hodnoty `external` ve výběru druhu pravidla („Výpočet mimo Odoo s doložením“ v
`investra_nav/models/fee_rule.py`) je v červené zóně; přejmenuje ho Claude v samostatném plánu. Dále skrytí záložky
podle toho, zda fond takové pravidlo má (potřebuje nové pole), modely, Python, testy.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“.

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons/custom/investra_nav/views/nav_views.xml'); print('XML OK')"
```
Vypíše `XML OK` (ověří, že záložka je správně uzavřená).

```bash
grep -c "Výpočty mimo Odoo\|Výpočet mimo Odoo" addons/custom/investra_nav/views/nav_views.xml
```
Vypíše `0`.

```bash
git diff --check && git diff --stat revize/claude-app
```
Bez chyb; mění se jen `nav_views.xml` a tento soubor.

**Kritéria přijetí:**
- Příkazy výše projdou.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje `investra_nav` v `investra_test`, spustí jeho testy
  a ověří záložku v návrhu ocenění (vidět) a ve schváleném ocenění bez záznamů (skrytá).

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
