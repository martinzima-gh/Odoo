# MN-15 Manuál kap. 5: uživatelé a role

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `docs/manual/`) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | `cp/MN-15` nebo bez větve; Copilot zapisuje do klonu `~/odoo-review`, bez commitu |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-13 (vzor kapitoly), osnova `docs/manual/README.md` (kap. 5 – plán) |

**Cíl:** `docs/manual/05-uzivatele-a-role.md`: jak založit uživatele a přidělit mu práva k fondům a činnostem. Čtenář: účetní a administrátor fondu.

**Obsah:**
1. Skupiny/role aplikace: seznam z `addons/custom/*/security/` (`*.xml` s `res.groups`, `ir.access.csv`) – název přesně jako v aplikaci, co skupina smí a nesmí (jednou větou), jak spolu souvisí (implikace).
2. Postup: kde se uživatel zakládá, kde se přidělují skupiny, co se děje u nové knihy/fondu (jaké skupiny musí existovat, aby šlo ocenění schválit čtyřma očima – navazuje na kap. 4, matice).
3. Kontrolní seznam „minimální obsazení rolí pro první ocenění“ (odkaz na kap. 4, bod 4).
4. Co se nedá obejít (kontroly s textem chyby z kódu).

**Formát a pravidla:** jako kap. 1–4 (README, Konvence): cesta v nabídce, pole v tučném písmu, výchozí/povinné, štítek „Ověřeno v kódu, v prohlížeči neověřeno“, bez obrázků, smyšlená jména, bez důvěrných textů, bez obchodního názvu IS. Názvy přebírat přesně z XML a `string=`, nevymýšlet. Nesrovnalosti v aplikaci neopravovat, zapsat do Výsledku jako číslovaný seznam.

**Rozsah souborů:** `docs/manual/05-uzivatele-a-role.md`, řádek kap. 5 v `docs/manual/README.md` (stav „koncept“), sekce Výsledek. Kód ani databázi neměnit, testy nespouštět.

**Kritéria přijetí:** každá skupina z `security/` je popsaná nebo výslovně vynechaná s důvodem; kontrolní seznam; nálezy ve Výsledku.

## Výsledek

Doplní provádějící agent.

## Převzetí

Doplní Claude.
