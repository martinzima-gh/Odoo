# AG-006 Nabídka podle práce

Přestavba nabídky Investra podle návrhu schváleného uživatelem 10. 11. 2026 (poznámky 7, 11, 12, 13 a 15 a princip
„nabídka podle práce, číselníky a nastavení do Nastavení“). Mění se jen záznamy `menuitem`.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `menuitem` v XML pohledů) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-006-nabidka` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | AG-005, návrh nabídky schválený 2026-11-10 |

**Cíl:** Nahoře budou jen pracovní nabídky: Přehled, Ocenění, Portfolio, Úpisy a odkupy, Výkazy, Nastavení.
Fondy, nástroje, typy nástrojů, protistrany, číselníky a účetní události budou v Nastavení.

**Cílová struktura** (v závorce `sequence`, vpravo XML id):

```
Investra
├── Přehled (1)                      investra_dashboard.menu_fund_dashboard
├── Ocenění (10)                     investra_entity.menu_valuation_section  (nové, bez akce)
│   ├── Ocenění (10)                 investra_nav.menu_valuation
│   └── Kurzy měn (20)               investra_rates.menu_rate
├── Portfolio (20)                   investra_instruments.menu_instruments   (beze změny)
│   ├── Obchody (10)                 investra_instruments.menu_trade
│   ├── Ceny (20)                    investra_instruments.menu_price
│   └── Splátky nástrojů (30)        investra_nav.menu_repayment
├── Úpisy a odkupy (30)              investra_nav.menu_movement
├── Výkazy (40)                      investra_entity.menu_reports            (nové, bez akce)
│   └── Termíny ČNB (10)             investra_dashboard.menu_deadline
└── Nastavení (90)                   investra_entity.menu_setup
    ├── Fondy (10)                   investra_entity.menu_setup_funds        (nové, nadpis skupiny)
    │   ├── Fondy (10)               investra_fund.menu_fund
    │   ├── Účetní knihy (20)        investra_entity.menu_entity
    │   ├── Pravidla úplat (30)      investra_nav.menu_fee_rule
    │   └── Alokační schémata (40)   investra_allocation.menu_scheme
    ├── Nástroje (20)                investra_entity.menu_setup_instruments  (nové)
    │   ├── Nástroje (10)            investra_instruments.menu_instrument
    │   ├── Typy nástrojů (20)       investra_instruments.menu_instrument_type
    │   └── Protistrany (30)         investra_counterparty.menu_profile
    ├── ČNB (30)                     investra_entity.menu_setup_cnb          (nové)
    │   └── Převodová tabulka ČNB (10) investra_cnb.menu_cnb_map
    └── Auditní stopa (40)           investra_entity.menu_setup_audit        (nové)
        └── Účetní události (10)     investra_posting.menu_event
```

Nové nadřazené nabídky jsou v `investra_entity`, protože na něm závisí všechny ostatní moduly Investra
(nevznikají nové závislosti). Nabídky přecenění cizích měn v Účetnictví (`investra_fx_revaluation`) se nemění.

**Rozsah souborů:**
`addons/custom/investra_entity/views/entity_views.xml`, `addons/custom/investra_dashboard/views/dashboard_views.xml`,
`addons/custom/investra_fund/views/fund_views.xml`, `addons/custom/investra_instruments/views/instrument_views.xml`,
`addons/custom/investra_nav/views/nav_views.xml`, `addons/custom/investra_rates/views/rate_views.xml`,
`addons/custom/investra_counterparty/views/counterparty_views.xml`, `addons/custom/investra_allocation/views/allocation_views.xml`,
`addons/custom/investra_cnb/views/cnb_views.xml`, `addons/custom/investra_posting/views/posting_views.xml`
a sekce Výsledek v tomto souboru.

**Pravidla:**
- Měň jen řádky `<menuitem …/>` uvedené níže. Žádné `id` existující nabídky neměň ani nemaž: Odoo by založilo
  novou nabídku a starou nechalo viset.
- Každý blok „Bylo“ nahraď blokem „Bude“ přesně. Když se blok „Bylo“ v souboru nenajde, zastav se a napiš to do výsledku.
- Nic jiného v souborech neměň (ani formátování ostatních záznamů).

### 1. `investra_entity/views/entity_views.xml`

Bylo:
```xml
    <menuitem id="menu_root" name="Investra" web_icon="account,static/description/icon.png" groups="account.group_account_readonly"/>
    <menuitem id="menu_setup" name="Nastavení" parent="menu_root" sequence="90"/>
    <menuitem id="menu_entity" name="Účetní knihy" parent="menu_setup" action="action_entity"/>
```
Bude:
```xml
    <menuitem id="menu_root" name="Investra" web_icon="account,static/description/icon.png" groups="account.group_account_readonly"/>
    <menuitem id="menu_valuation_section" name="Ocenění" parent="menu_root" sequence="10"/>
    <menuitem id="menu_reports" name="Výkazy" parent="menu_root" sequence="40"/>
    <menuitem id="menu_setup" name="Nastavení" parent="menu_root" sequence="90"/>
    <menuitem id="menu_setup_funds" name="Fondy" parent="menu_setup" sequence="10"/>
    <menuitem id="menu_setup_instruments" name="Nástroje" parent="menu_setup" sequence="20"/>
    <menuitem id="menu_setup_cnb" name="ČNB" parent="menu_setup" sequence="30"/>
    <menuitem id="menu_setup_audit" name="Auditní stopa" parent="menu_setup" sequence="40"/>
    <menuitem id="menu_entity" name="Účetní knihy" parent="menu_setup_funds" action="action_entity" sequence="20"/>
```

### 2. `investra_dashboard/views/dashboard_views.xml`

Bylo:
```xml
    <menuitem id="menu_fund_dashboard" name="Přehled fondů" parent="investra_entity.menu_root" action="action_fund_dashboard" sequence="1"/>
    <menuitem id="menu_deadline" name="Termíny ČNB" parent="investra_entity.menu_root" action="action_deadline" sequence="90"/>
```
Bude:
```xml
    <menuitem id="menu_fund_dashboard" name="Přehled" parent="investra_entity.menu_root" action="action_fund_dashboard" sequence="1"/>
    <menuitem id="menu_deadline" name="Termíny ČNB" parent="investra_entity.menu_reports" action="action_deadline" sequence="10"/>
```

### 3. `investra_fund/views/fund_views.xml`

Bylo:
```xml
    <menuitem id="menu_fund" name="Fondy" parent="investra_entity.menu_root" action="action_fund" sequence="10"/>
```
Bude:
```xml
    <menuitem id="menu_fund" name="Fondy" parent="investra_entity.menu_setup_funds" action="action_fund" sequence="10"/>
```

### 4. `investra_instruments/views/instrument_views.xml`

Bylo:
```xml
    <menuitem id="menu_instruments" name="Portfolio" parent="investra_entity.menu_root" sequence="20"/>
    <menuitem id="menu_instrument" name="Nástroje" parent="menu_instruments" action="action_instrument"/>
    <menuitem id="menu_instrument_type" name="Typy nástrojů" parent="menu_instruments" action="action_instrument_type"/>
    <menuitem id="menu_price" name="Ceny" parent="menu_instruments" action="action_price"/>
    <menuitem id="menu_trade" name="Obchody" parent="menu_instruments" action="action_trade"/>
```
Bude:
```xml
    <menuitem id="menu_instruments" name="Portfolio" parent="investra_entity.menu_root" sequence="20"/>
    <menuitem id="menu_instrument" name="Nástroje" parent="investra_entity.menu_setup_instruments" action="action_instrument" sequence="10"/>
    <menuitem id="menu_instrument_type" name="Typy nástrojů" parent="investra_entity.menu_setup_instruments" action="action_instrument_type" sequence="20"/>
    <menuitem id="menu_price" name="Ceny" parent="menu_instruments" action="action_price" sequence="20"/>
    <menuitem id="menu_trade" name="Obchody" parent="menu_instruments" action="action_trade" sequence="10"/>
```

### 5. `investra_nav/views/nav_views.xml`

Bylo:
```xml
    <menuitem id="menu_repayment" name="Splátky nástrojů" parent="investra_instruments.menu_instruments" action="action_repayment" sequence="40"/>
    <menuitem id="menu_valuation" name="Ocenění" parent="investra_entity.menu_root" action="action_valuation" sequence="5"/>
    <menuitem id="menu_movement" name="Úpisy a odkupy" parent="investra_entity.menu_root" action="action_movement" sequence="15"/>
    <menuitem id="menu_fee_rule" name="Pravidla úplat" parent="investra_entity.menu_setup" action="action_fee_rule"/>
```
Bude:
```xml
    <menuitem id="menu_repayment" name="Splátky nástrojů" parent="investra_instruments.menu_instruments" action="action_repayment" sequence="30"/>
    <menuitem id="menu_valuation" name="Ocenění" parent="investra_entity.menu_valuation_section" action="action_valuation" sequence="10"/>
    <menuitem id="menu_movement" name="Úpisy a odkupy" parent="investra_entity.menu_root" action="action_movement" sequence="30"/>
    <menuitem id="menu_fee_rule" name="Pravidla úplat" parent="investra_entity.menu_setup_funds" action="action_fee_rule" sequence="30"/>
```

### 6. `investra_rates/views/rate_views.xml`

Bylo:
```xml
    <menuitem id="menu_rate" name="Vyhlášené kurzy" parent="investra_entity.menu_setup" action="action_rate"/>
```
Bude:
```xml
    <menuitem id="menu_rate" name="Kurzy měn" parent="investra_entity.menu_valuation_section" action="action_rate" sequence="20"/>
```

### 7. `investra_counterparty/views/counterparty_views.xml`

Bylo:
```xml
    <menuitem id="menu_profile" name="Protistrany" parent="investra_instruments.menu_instruments" action="action_profile" sequence="30"/>
```
Bude:
```xml
    <menuitem id="menu_profile" name="Protistrany" parent="investra_entity.menu_setup_instruments" action="action_profile" sequence="30"/>
```

### 8. `investra_allocation/views/allocation_views.xml`

Bylo:
```xml
    <menuitem id="menu_scheme" name="Alokační schémata" parent="investra_entity.menu_setup" action="action_scheme"/>
```
Bude:
```xml
    <menuitem id="menu_scheme" name="Alokační schémata" parent="investra_entity.menu_setup_funds" action="action_scheme" sequence="40"/>
```

### 9. `investra_cnb/views/cnb_views.xml`

Bylo:
```xml
    <menuitem id="menu_cnb_map" name="Převodová tabulka ČNB" parent="investra_entity.menu_setup" action="action_cnb_map"/>
```
Bude:
```xml
    <menuitem id="menu_cnb_map" name="Převodová tabulka ČNB" parent="investra_entity.menu_setup_cnb" action="action_cnb_map" sequence="10"/>
```

### 10. `investra_posting/views/posting_views.xml`

Bylo:
```xml
    <menuitem id="menu_event" name="Účetní události" parent="investra_entity.menu_root" action="action_event" sequence="30"/>
```
Bude:
```xml
    <menuitem id="menu_event" name="Účetní události" parent="investra_entity.menu_setup_audit" action="action_event" sequence="10"/>
```

**Mimo rozsah:** akce, pohledy, názvy akcí (záhlaví seznamu kurzů zůstává „Vyhlášené kurzy“), modely, Python,
testy, nabídky v Účetnictví, `__manifest__.py`.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“.

```bash
git diff --check
```
Bez výstupu.

```bash
git diff --stat HEAD
```
Jen deset souborů z Rozsahu a tento soubor.

Strom nabídky ze zdrojových XML (porovnej s Cílovou strukturou; skript se nikam neukládá):
```bash
python3 - <<'EOF'
import glob
import xml.etree.ElementTree as ET
from pathlib import Path

menus = {}
for path in sorted(glob.glob("addons/custom/*/views/*.xml")):
    module = Path(path).parts[2]
    full = lambda ref: ref if "." in ref else f"{module}.{ref}"
    for m in ET.parse(path).getroot().iter("menuitem"):
        parent = full(m.get("parent")) if m.get("parent") else None
        menus[full(m.get("id"))] = (parent, int(m.get("sequence", 10)), m.get("name"))

def show(parent, depth):
    for key, (p, seq, name) in sorted(menus.items(), key=lambda kv: kv[1][1]):
        if p == parent:
            print("  " * depth + f"{name} ({seq})  {key}")
            show(key, depth + 1)

show(None, 0)
orphans = [k for k, (p, _, _) in menus.items() if p and p not in menus and not p.startswith("account.")]
print("Bez rodiče:", orphans or "žádné")
EOF
```
Výstup začíná `Investra (10)  investra_entity.menu_root`, pod ním je šest položek v pořadí Přehled, Ocenění,
Portfolio, Úpisy a odkupy, Výkazy, Nastavení, a poslední řádek je `Bez rodiče: žádné`.

**Kritéria přijetí:**
- Všechny příkazy výše projdou a strom odpovídá Cílové struktuře.
- Diff mění jen řádky `menuitem`.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje dotčené moduly v `investra_test`, spustí testy Odoo
  a projde nabídku v prohlížeči.

## Výsledek

Úkol provedl Copilot.

- **Změněné soubory:** deset XML souborů z Rozsahu souborů a tento soubor (pouze sekce Výsledek).
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — Zkontrolováno souborů: 11, chyb: 0; `git diff --check` — bez výstupu; `git diff --stat HEAD` — deset XML souborů z Rozsahu a tento soubor. Strom nabídky ze zadaného skriptu odpovídá Cílové struktuře, včetně `Bez rodiče: žádné`. Kontrola diffu potvrdila, že v XML jsou změněné jen řádky `<menuitem>`.
- **Neověřeno:** nabídka v běžícím Odoo; testy Odoo a upgrade modulů (při převzetí provede Claude). Docker ani databáze nebyly spuštěny.
- **Otevřené otázky a návrhy mimo rozsah:** žádné.

## Převzetí

- **Datum:** 2026-11-10
- **Provedl:** GitHub Copilot (režim Agent v okně na `~/odoo-review`) podle rozhodnutí 2026-11-09 „Copilot jako náhradní
  vývojář“. Commit `6320010` s autorem „Copilot“ udělal Claude v klonu.
- **Sloučení:** `6320010` do `feature/nav-prototyp` (fast-forward).
- **Revize:** diff mění jen deset souborů pohledů z Rozsahu (pouze řádky `<menuitem>`) a sekci Výsledek (zelená zóna).
  Všech deset bloků „Bude“ je v souborech beze změny znaků. Strom nabídky ze zdrojových XML odpovídá Cílové struktuře,
  bez položek bez rodiče. Nálezy: žádné.
- **Testy:** `check_views.py` – chyb: 0; `-u` deseti dotčených modulů s jejich testy nad `investra_test` –
  0 failed, 0 error(s) of 243 tests (testy běžely ve všech deseti modulech). Řádka ERROR „Stažení kurzů selhalo“
  pochází z existujícího testu `test_rate` a s úkolem nesouvisí.
- **Databáze `investra_test`:** 28 nabídek Investry má rodiče a pořadí podle Cílové struktury, žádná stará nabídka
  nezůstala; přecenění cizích měn zůstává pod Účetnictvím. Dotaz je v `docs/sql/09-nabidka.sql`.
- **Neověřeno:** vzhled nabídky v prohlížeči (testovací web na portu 8071).
