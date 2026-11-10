# AG-011 Účty rolí a role účtů v Nastavení

Účetní události zaúčtují řádky podle rolí účtů (`investra.account.role`) a účet role v knize hledají
v mapování `investra.role.account`. Mapování dnes nemá žádnou obrazovku: u fondové knihy ho založí šablona
a jinak ho nejde zobrazit ani doplnit (dotaz uživatele z 10. 11. 2026). Úkol doplní seznamy a nabídku.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen XML pohledů; přístupová práva už existují v `investra_entity/security/ir.access.csv`) |
| Výchozí větev | `revize/claude-app` po sloučení AG-006 |
| Větev úkolu | `ag/AG-011-ucty-roli` (vytvoří Claude při převzetí) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-006 (nabídka `menu_setup_audit` musí existovat; začni až po jeho sloučení) |

**Cíl:** V Nastavení → Účtování uvidí uživatel:
- **Účty rolí:** kniha, role a účet. Účetní manažer může řádky přidávat a měnit přímo v seznamu,
  ostatní účetní je jen čtou.
- **Role účtů:** číselník rolí jen ke čtení. Kód role používá program, proto se v aplikaci nezakládá, nemaže ani neupravuje.

**Účetní dopad:** žádný při nasazení. Změna účtu u role po nasazení platí jen pro nově vytvořené návrhy dokladů;
existující doklady se nemění.

**Rozsah souborů:** `addons/custom/investra_entity/views/entity_views.xml` a sekce Výsledek v tomto souboru.

**1. Pohledy a akce.** Vlož celý blok těsně před řádek
`    <menuitem id="menu_root" name="Investra" web_icon="account,static/description/icon.png" groups="account.group_account_readonly"/>`:

```xml
    <record id="view_role_account_list" model="ir.ui.view">
        <field name="name">investra.role.account.list</field>
        <field name="model">investra.role.account</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="company_id" string="Kniha" options="{'no_create': True, 'no_open': True}"/>
                <field name="role_id" string="Role" options="{'no_create': True, 'no_open': True}"/>
                <field name="account_id" string="Účet" options="{'no_create': True, 'no_open': True}"/>
            </list>
        </field>
    </record>
    <record id="view_role_account_search" model="ir.ui.view">
        <field name="name">investra.role.account.search</field>
        <field name="model">investra.role.account</field>
        <field name="arch" type="xml">
            <search>
                <field name="role_id"/>
                <field name="account_id"/>
                <field name="company_id"/>
                <filter name="filter_asset" string="Aktiva" domain="[('role_id.category', '=', 'asset')]"/>
                <filter name="filter_liability" string="Závazky" domain="[('role_id.category', '=', 'liability')]"/>
                <filter name="filter_equity" string="Vlastní kapitál" domain="[('role_id.category', '=', 'equity')]"/>
                <filter name="filter_income" string="Výnosy" domain="[('role_id.category', '=', 'income')]"/>
                <filter name="filter_expense" string="Náklady" domain="[('role_id.category', '=', 'expense')]"/>
                <group>
                    <filter name="group_by_company" string="Kniha" context="{'group_by': 'company_id'}"/>
                    <filter name="group_by_role" string="Role" context="{'group_by': 'role_id'}"/>
                </group>
            </search>
        </field>
    </record>
    <record id="action_role_account" model="ir.actions.act_window">
        <field name="name">Účty rolí</field>
        <field name="res_model">investra.role.account</field>
        <field name="view_mode">list</field>
        <field name="search_view_id" ref="view_role_account_search"/>
    </record>
    <record id="view_account_role_list" model="ir.ui.view">
        <field name="name">investra.account.role.list</field>
        <field name="model">investra.account.role</field>
        <field name="arch" type="xml">
            <list create="false" edit="false" delete="false">
                <field name="code" string="Kód"/>
                <field name="name" string="Název"/>
                <field name="category" string="Druh"/>
            </list>
        </field>
    </record>
    <record id="view_account_role_search" model="ir.ui.view">
        <field name="name">investra.account.role.search</field>
        <field name="model">investra.account.role</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
                <field name="code"/>
                <filter name="filter_archived" string="Archivováno" domain="[('active', '=', False)]" context="{'active_test': False}"/>
                <group>
                    <filter name="group_by_category" string="Druh" context="{'group_by': 'category'}"/>
                </group>
            </search>
        </field>
    </record>
    <record id="action_account_role" model="ir.actions.act_window">
        <field name="name">Role účtů</field>
        <field name="res_model">investra.account.role</field>
        <field name="view_mode">list</field>
        <field name="search_view_id" ref="view_account_role_search"/>
    </record>
```

**2. Nabídka.** Vlož tři řádky hned za řádek z AG-006
`    <menuitem id="menu_setup_audit" name="Auditní stopa" parent="menu_setup" sequence="40"/>`:

```xml
    <menuitem id="menu_setup_accounting" name="Účtování" parent="menu_setup" sequence="35"/>
    <menuitem id="menu_role_account" name="Účty rolí" parent="menu_setup_accounting" action="action_role_account" sequence="10"/>
    <menuitem id="menu_account_role" name="Role účtů" parent="menu_setup_accounting" action="action_account_role" sequence="20"/>
```

Výsledné pořadí v Nastavení: Fondy (10), Nástroje (20), ČNB (30), Účtování (35), Auditní stopa (40).

Když řádek `menu_setup_audit` v souboru není (AG-006 ještě není sloučený) nebo některé nové `id` už existuje,
zastav se a napiš to do výsledku. Nic jiného v souboru neměň.

**Mimo rozsah:** zámek nebo schválení změny účtu role po prvním zaúčtování (změna modelu, červená zóna,
samostatný plán), kontrola úplnosti mapování knihy, hromadné mapování podle předpony účtu, přístupová práva,
modely, Python, testy, data rolí.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“ a v `entity_views.xml` jsou o čtyři zkontrolované pohledy víc.

```bash
grep -c 'id="view_role_account_list"\|id="view_role_account_search"\|id="view_account_role_list"\|id="view_account_role_search"\|id="action_role_account"\|id="action_account_role"\|id="menu_setup_accounting"\|id="menu_role_account"\|id="menu_account_role"' addons/custom/investra_entity/views/entity_views.xml
```
Vypíše `9`.

```bash
git diff --check && git diff --stat revize/claude-app
```
Bez chyb; mění se jen `entity_views.xml` a tento soubor.

Strom nabídky: stejný skript jako v AG-006. Pod Nastavení přibude „Účtování (35)“ se dvěma položkami
a poslední řádek zůstane `Bez rodiče: žádné`.

**Kritéria přijetí:**
- Příkazy výše projdou; všechna pole existují na modelech v `investra_entity/models/account_role.py`.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje `investra_entity` v `investra_test`, spustí testy
  a ověří: účetní manažer upraví účet role v seznamu, uživatel jen ke čtení nemůže, výběr účtu nabízí jen účty
  vybrané knihy, druhý řádek se stejnou knihou a rolí odmítne model.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
