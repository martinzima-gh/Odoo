# Investra Chart Fund

Šablona osnovy fondů `investra_fund` (vyhláška 501/2002 Sb.), mapování rolí účtů na účty šablony
a průvodce **Nová účetní kniha**.

## Průvodce Nová účetní kniha (MN-01)

Investra › Nastavení › Fondy › Nová účetní kniha, nebo tlačítko v seznamu Účetní knihy. Jen pro správce
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
| Nadřazená kniha | – | u podfondu povinně SICAV |

Před založením průvodce zkontroluje, že jsou nainstalované moduly osnovy a lokalizace země. Jinak by je Odoo
doinstalovalo uprostřed požadavku, potvrdilo transakci a při pozdější chybě by zůstala polovičatá společnost.
Po založení se nová společnost připojí uživateli a otevře se formulář knihy.
