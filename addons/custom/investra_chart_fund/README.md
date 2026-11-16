# Investra Chart Fund

Šablona osnovy fondů `investra_fund` (vyhláška 501/2002 Sb.), mapování rolí účtů na účty šablony
a průvodce **Nová účetní kniha**.

## Průvodce Nová účetní kniha (MN-01)

Tlačítko **Nová účetní kniha** v seznamu Účetní knihy (samostatná položka nabídky se od MN-05 ruší). Jen pro správce
(`base.group_system`): načtení osnovy Odoo povoluje jen správci (`account.chart.template._load`).

Průvodce volá `investra.entity.create_book` stejně jako `tools/demo_data/seed.py`, takže kniha má:
funkční měnu ze zadání (načtení osnovy ji nepřepíše), zdroj kurzů podle měny (CZK – ČNB, EUR – ECB),
`restrictive_audit_trail`, u SICAV, fondu a podfondu hash obecných deníků a namapované role účtů.

| Pole | Výchozí | Pravidlo |
|---|---|---|
| Druh jednotky | Fond | určuje šablonu: SICAV, fond, podfond → `investra_fund`, ostatní → `cz` |
| Účetní rámec | podle druhu | servisní společnost 500/2002, ostatní 501/2002; jiná kombinace se odmítne |
| Funkční měna | CZK | po prvním zaúčtování nejde změnit |
| Země | Česko | |
| Nadřazená kniha | – | jen u podfondu (jinak skrytá), povinně SICAV |

Před založením průvodce zkontroluje, že jsou nainstalované moduly osnovy a lokalizace země. Jinak by je Odoo
doinstalovalo uprostřed požadavku, potvrdilo transakci a při pozdější chybě by zůstala polovičatá společnost.
Po založení se nová společnost připojí uživateli, otevře se formulář knihy a zobrazí se hláška „Zapněte novou společnost
v přepínači firem“ (přepínač si pamatuje prohlížeč, server ho trvale nezapne). Kniha se zakládá přes `with_company`:
prohlížeč posílá `allowed_company_ids` bez nové společnosti a pravidlo „Knihy podle společnosti“ by jinak zápis odmítlo.
Pole Zakladatel se zrušilo (MN-05).

## Odchylka mapování od standardu (MN-04)

`investra.role.account` má nestorovaná pole **Standard** (Podle standardu / Odchylka / Bez standardu) a **Standardní účet**,
v Účtech rolí je filtr Odchylka od standardu. Porovnává se jen hlavní účet; `account_for` se nemění. Seskupení podle
Standardu nejde (pole není uložené), použijte filtry.

**Změna standardu (`ROLE_ACCOUNTS`):** po změně slovníku vypadá řádek, který odpovídal starému standardu, jako odchylka.
Migrace proto zavolá `env["investra.role.account"]._apply_standard_role(code, old_xmlid="<starý xmlid>")` (po
`_ensure_fund_accounts`, aby nový účet v knihách byl). Řádky se starým standardním účtem převede na nový, chybějící
vytvoří a skutečné odchylky nemění: vrátí je jako záznamy k výpisu do logu migrace. Zatím ji nic nevolá.

