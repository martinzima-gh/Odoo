# AG-008 Seznam úpisů a odkupů

Model `investra.class.movement` nemá vlastní seznam, Odoo proto ukazuje jen název záznamu (poznámka 8
z 10. 11. 2026). Úkol doplní seznam z existujících polí a filtry zaúčtování.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-008-seznam-upisu` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-006 (nezávisí na něm, lze dělat souběžně) |

**Cíl:** V nabídce Úpisy a odkupy uvidí uživatel datum, fond, třídu, typ, kusy, částky, kurz a vazbu na účetní
událost, a vyfiltruje nezaúčtované pohyby.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml` (jen nový záznam `view_movement_list`
a filtry v `view_movement_search`) a sekce Výsledek v tomto souboru. Modul `investra_nav` je jinak v červené zóně:
`models/` a `engine.py` jen čti.

**1. Nový seznam.** Vlož celý blok těsně před řádek `<record id="view_movement_search" model="ir.ui.view">`:

```xml
    <record id="view_movement_list" model="ir.ui.view">
        <field name="name">investra.class.movement.list</field>
        <field name="model">investra.class.movement</field>
        <field name="arch" type="xml">
            <list>
                <field name="date" string="Datum"/>
                <field name="fund_id" string="Fond"/>
                <field name="class_id" string="Třída"/>
                <field name="movement_type" string="Typ"/>
                <field name="units" string="Kusy"/>
                <field name="currency_id" string="Měna kurzu" optional="show"/>
                <field name="amount_class" string="Částka v měně kurzu" optional="show"/>
                <field name="fx_rate" string="Kurz" optional="show"/>
                <field name="amount" string="Částka ve funkční měně"/>
                <field name="event_id" string="Účetní událost" optional="show"/>
            </list>
        </field>
    </record>
```

**2. Filtry zaúčtování** ve `view_movement_search`.

Bylo:
```xml
                <filter name="filter_redemption" string="Odkupy" domain="[('movement_type', '=', 'redemption')]"/>
                <separator/>
```
Bude:
```xml
                <filter name="filter_redemption" string="Odkupy" domain="[('movement_type', '=', 'redemption')]"/>
                <separator/>
                <filter name="filter_unposted" string="Nezaúčtováno" domain="[('event_id', '=', False)]"/>
                <filter name="filter_posted" string="Zaúčtováno" domain="[('event_id', '!=', False)]"/>
                <separator/>
```

Když se blok „Bylo“ nenajde přesně nebo `view_movement_list` už existuje, zastav se a napiš to do výsledku.
Akci `action_movement` neměň (seznam se použije sám, je pro model jediný). Nic jiného neměň.

**Mimo rozsah:** sloupec „zdroj“ (IS / ruční pořízení), zaokrouhlení, poplatek ve prospěch fondu nebo třídy
a historie změn. To jsou nová pole a vazba na výpočet NAV (oranžová a červená zóna), řeší samostatný plán.
Dále formulář, modely, Python, testy, nabídky.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“.

```bash
python3 -c "import sys; sys.path.insert(0, 'tools/view_check'); from check_views import view_archs; print([r for r, _ in view_archs('addons/custom/investra_nav/views/nav_views.xml') if r == 'view_movement_list'])"
```
Vypíše `['view_movement_list']`, tedy nový seznam je mezi pohledy, které skript ověřuje podle schématu.
(Původně „počet pohledů o jeden vyšší“; skript ale vypisuje jen počet souborů, opraveno 2026-11-10.)

```bash
grep -c 'id="view_movement_list"' addons/custom/investra_nav/views/nav_views.xml
```
Vypíše `1`.

```bash
git diff --check && git diff --stat HEAD
```
Bez chyb; mění se jen `nav_views.xml` a tento soubor.

**Kritéria přijetí:**
- Příkazy výše projdou; všechna pole v seznamu existují na modelu (`investra_nav/models/movement.py`).
- Při převzetí Claude (se souhlasem uživatele) aktualizuje `investra_nav` v `investra_test`, spustí jeho testy
  a ověří seznam a oba filtry v prohlížeči.

## Výsledek

Úkol provedl Copilot.

- **Změněné soubory:** `addons/custom/investra_nav/views/nav_views.xml` (nový seznam a filtry v `view_movement_search`) a tento soubor (jen sekce Výsledek).
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — Zkontrolováno souborů: 11, chyb: 0; příkaz pro `view_archs` — `['view_movement_list']`; `grep -c 'id="view_movement_list"' addons/custom/investra_nav/views/nav_views.xml` — `1`; `git diff --check` — bez výstupu; `git diff --stat HEAD` — změny pouze v `nav_views.xml` a tomto souboru zadání. Všechna pole seznamu jsou v `investra_nav/models/movement.py`.
- **Neověřeno:** zobrazení seznamu a funkčnost filtrů v běžícím Odoo; Odoo testy. Docker ani databáze nebyly spuštěny.
- **Otevřené otázky a návrhy mimo rozsah:** žádné.

## Převzetí

- **Datum:** 2026-11-10
- **Provedl:** GitHub Copilot (režim Agent v okně na `~/odoo-review`) podle rozhodnutí 2026-11-09 „Copilot jako náhradní
  vývojář“. Commit `ecab8a0` s autorem „Copilot“ udělal Claude v klonu.
- **Sloučení:** `ecab8a0` do `feature/nav-prototyp` (fast-forward).
- **Revize:** diff přidává jen záznam `view_movement_list` těsně před `view_movement_search` a dva filtry s oddělovačem
  (zelená zóna); oba bloky jsou v souboru beze změny znaků, všech 10 polí seznamu existuje na modelu. Nálezy: žádné.
- **Testy:** `check_views.py` – chyb: 0, `view_movement_list` je mezi ověřenými pohledy; `-u investra_nav` s jeho testy
  nad `investra_test` – 0 failed, 0 error(s) of 121 tests.
- **Databáze `investra_test`:** seznam je uložen jako pohled typu `list`, vyhledávání obsahuje oba filtry. Všech 7
  pohybů v testovacích datech je zaúčtovaných, filtr „Nezaúčtováno“ proto vrátí prázdný seznam.
- **Neověřeno:** vzhled seznamu a filtrů v prohlížeči.
