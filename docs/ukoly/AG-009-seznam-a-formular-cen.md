# AG-009 Seznam a formulář cen

Model `investra.instrument.price` nemá vlastní seznam ani formulář: seznam ukazuje jen název záznamu (poznámka 10
z 10. 11. 2026) a schválit cenu z obrazovky nejde, i když model metodu `action_approve` má. Úkol doplní oba pohledy
z existujících polí.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `revize/claude-app` |
| Větev úkolu | `ag/AG-009-ceny` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-006 (nezávisí na něm, lze dělat souběžně) |

**Cíl:** Seznam cen ukáže datum, nástroj, fond, cenu, zdroj, stav, kdo cenu zadal a kdo ji schválil. Označené
ceny v návrhu půjde schválit tlačítkem v seznamu i ve formuláři. Pravidla schvalování (skupina, čtyři oči,
společnost) hlídá model, pohled je nemění.

**Rozsah souborů:** `addons/custom/investra_instruments/views/instrument_views.xml` (jen dva nové záznamy)
a sekce Výsledek v tomto souboru.

**Změna.** Vlož celý blok těsně před řádek `<record id="view_price_search" model="ir.ui.view">`:

```xml
    <record id="view_price_list" model="ir.ui.view">
        <field name="name">investra.instrument.price.list</field>
        <field name="model">investra.instrument.price</field>
        <field name="arch" type="xml">
            <list>
                <header>
                    <button name="action_approve" type="object" string="Schválit"/>
                </header>
                <field name="date" string="Datum"/>
                <field name="instrument_id" string="Nástroj"/>
                <field name="fund_id" string="Fond"/>
                <field name="price" string="Cena"/>
                <field name="source"/>
                <field name="state" string="Stav" widget="badge" decoration-warning="state == 'draft'" decoration-success="state == 'approved'"/>
                <field name="entered_by" string="Zadal" optional="show"/>
                <field name="approved_by" string="Schválil" optional="show"/>
            </list>
        </field>
    </record>
    <record id="view_price_form" model="ir.ui.view">
        <field name="name">investra.instrument.price.form</field>
        <field name="model">investra.instrument.price</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_approve" type="object" string="Schválit" class="btn-primary" invisible="state != 'draft'"/>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <group>
                            <field name="instrument_id" string="Nástroj" readonly="state == 'approved'"/>
                            <field name="fund_id" string="Fond" readonly="state == 'approved'"/>
                            <field name="date" string="Datum" readonly="state == 'approved'"/>
                        </group>
                        <group>
                            <field name="price" string="Cena" readonly="state == 'approved'"/>
                            <field name="source" readonly="state == 'approved'"/>
                            <field name="entered_by" string="Zadal"/>
                            <field name="approved_by" string="Schválil"/>
                        </group>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
```

Když `view_price_list` nebo `view_price_form` už existuje, zastav se a napiš to do výsledku. Akci `action_price`
ani vyhledávání neměň. Nic jiného neměň.

**Mimo rozsah:** měna ceny (potřebuje nové související pole), sdílená tržní cena přes fondy a cena z posudku
na fondu (změna modelu, červená zóna, samostatný plán), modely, Python, testy, nabídky.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“ (kontroluje seznam; formulář skript nepokrývá).

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons/custom/investra_instruments/views/instrument_views.xml'); print('XML OK')"
```
Vypíše `XML OK`.

```bash
grep -c 'id="view_price_list"\|id="view_price_form"' addons/custom/investra_instruments/views/instrument_views.xml
```
Vypíše `2`.

```bash
git diff --check && git diff --stat revize/claude-app
```
Bez chyb; mění se jen `instrument_views.xml` a tento soubor.

**Kritéria přijetí:**
- Příkazy výše projdou; všechna pole existují na modelu (`investra_instruments/models/instrument.py`,
  třída `InvestraInstrumentPrice`).
- Při převzetí Claude (se souhlasem uživatele) aktualizuje `investra_instruments` v `investra_test`, spustí testy
  a ověří: seznam se sloupci, schválení z formuláře uživatelem se skupinou schvalování ocenění, odmítnutí
  schválení vlastní ceny (čtyři oči).

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
