# Jednotná osnova fondů (pracovní návrh)

Stav 2026-11-07. Rámec: vyhláška č. 501/2002 Sb., případně IFRS podle knihy. Čísla účtů jsou **pracovní** a nemají oporu v předpisu;
prototyp je používá, aby šlo testovat. Pravidla pracují s rolemi, takže změna čísla nemění výpočty.
Vazbu na položky účetní závěrky a na výkazy ČNB je potřeba ověřit proti aktuálnímu znění vyhlášky, před zápisem do šablony.

## Zásady

- Jedna šablona `investra_fund`, šestimístné kódy, role účtu je povinná.
- Měna ani třída nejsou v čísle účtu: třída, část fondu, nástroj a typ pohybu jsou pole na řádku.
- Převzatý fond se převede převodovou tabulkou; původní číslo zůstává jako odkaz.

## Účty a role

Zdroj pravdy je `addons/custom/investra_chart_fund/data/template/account.account-investra_fund.csv` a mapování rolí v `template_investra_fund.py`.

| Skupina | Role |
|---|---|
| Peníze | bankovní účet, peníze na cestě |
| Investice | investiční nástroje |
| Pohledávky | obchodní, ostatní, vnitřní zúčtování tříd |
| Závazky | obchodní, úpis, odkup, úplaty, výkonnostní odměna, poplatky za úpis a odkup, vůči investorům z rozdílů, dohady, daň |
| Kapitál | kapitál tříd, výsledek minulých let, běžný výsledek |
| Výnosy | přecenění, kurzové, úroky, dividendy, ostatní, rozdíly ze zaokrouhlení úpisů a odkupů |
| Náklady | přecenění, kurzové, obhospodařování, administrace, depozitář, výkonnostní odměna, ostatní, rozdíly ze zaokrouhlení úpisů a odkupů, daň |

## Vzor převodové tabulky

| Původní účet | Původní název | Nový účet | Role | Třída | Poznámka | Schválil |
|---|---|---|---|---|---|---|

## K doplnění

Přečíslování podle osnovy pro finanční instituce (vyhláška 501, otevřený bod 2026-11-11). Rozlišení nástrojů pro výkazy (cenné papíry, účasti, úvěry, deriváty), podrozvaha, opravné položky, rezervy, časové rozlišení, neinvestiční část SICAV.
