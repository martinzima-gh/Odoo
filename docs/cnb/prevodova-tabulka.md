# Převodová tabulka ČNB: přehled ke kontrole

Pracovní návrh, metodika FOFI20261201, platnost od 1. 12. 2026. Účetní metodik ho musí potvrdit; nic z toho není schválený převod.
Vygenerováno z `investra_test` a `polozky-FOFI20261201.csv`. Zdroj pravdy je `addons/custom/investra_cnb/data/cnb_map.xml`.

Sloupec Znaménko: 1 je zůstatek jak je, -1 obrácený. Součtové řádky jsou řádky listu, do kterých se hodnota přičítá.

## ROFO10_11: Aktiva (ROFOS10)

| Řádek | Položka ČNB | Role účtu | Kategorie IFRS 9 | Období | Znaménko | Znaménko řádku | Součtové řádky |
|--:|---|---|---|---|--:|--:|---|
| 4 | Ostatní vklady splatné na požádání | Bankovní účet | všechny | zůstatek | 1 | 1 | 1, 2 |
| 5 | Finanční aktiva k obchodování | Deriváty | všechny | zůstatek | 1 | 1 | 1 |
| 6 | Finanční aktiva jiná než k obchodování povinně v RH vykázané do zisku nebo ztráty | Investiční nástroje | FVTPL | zůstatek | 1 | 1 | 1 |
| 6 | Finanční aktiva jiná než k obchodování povinně v RH vykázané do zisku nebo ztráty | Dluhové cenné papíry | FVTPL | zůstatek | 1 | 1 | 1 |
| 6 | Finanční aktiva jiná než k obchodování povinně v RH vykázané do zisku nebo ztráty | Ostatní podíly | FVTPL | zůstatek | 1 | 1 | 1 |
| 6 | Finanční aktiva jiná než k obchodování povinně v RH vykázané do zisku nebo ztráty | Poskytnuté úvěry | FVTPL | zůstatek | 1 | 1 | 1 |
| 8 | Finanční aktiva v RH vykázané do úplného výsledku hospodaření | Investiční nástroje | FVOCI | zůstatek | 1 | 1 | 1 |
| 8 | Finanční aktiva v RH vykázané do úplného výsledku hospodaření | Dluhové cenné papíry | FVOCI | zůstatek | 1 | 1 | 1 |
| 8 | Finanční aktiva v RH vykázané do úplného výsledku hospodaření | Ostatní podíly | FVOCI | zůstatek | 1 | 1 | 1 |
| 8 | Finanční aktiva v RH vykázané do úplného výsledku hospodaření | Poskytnuté úvěry | FVOCI | zůstatek | 1 | 1 | 1 |
| 10 | Dluhové cenné papíry v naběhlé hodnotě | Dluhové cenné papíry | Naběhlá hodnota | zůstatek | 1 | 1 | 1, 9 |
| 11 | Úvěry a pohledávky v naběhlé hodnotě | Termínované vklady | Naběhlá hodnota | zůstatek | 1 | 1 | 1, 9 |
| 11 | Úvěry a pohledávky v naběhlé hodnotě | Reverzní repo | Naběhlá hodnota | zůstatek | 1 | 1 | 1, 9 |
| 11 | Úvěry a pohledávky v naběhlé hodnotě | Poskytnuté úvěry | Naběhlá hodnota | zůstatek | 1 | 1 | 1, 9 |
| 14 | Účasti v dceřiných, společných a přidružených podnicích | Účasti | všechny | zůstatek | 1 | 1 | 1 |
| 24 | Ostatní aktiva | Peníze na cestě | všechny | zůstatek | 1 | 1 | 1 |
| 24 | Ostatní aktiva | Ostatní pohledávky | všechny | zůstatek | 1 | 1 | 1 |
| 24 | Ostatní aktiva | Vnitřní zúčtování tříd | všechny | zůstatek | 1 | 1 | 1 |
| 24 | Ostatní aktiva | Pohledávky z nevypořádaných obchodů | všechny | zůstatek | 1 | 1 | 1 |
| 24 | Ostatní aktiva | Změna reálné hodnoty nevypořádaných obchodů | všechny | zůstatek | 1 | 1 | 1 |

## ROFO10_21: Pasiva (ROFOS10)

| Řádek | Položka ČNB | Role účtu | Kategorie IFRS 9 | Období | Znaménko | Znaménko řádku | Součtové řádky |
|--:|---|---|---|---|--:|--:|---|
| 24 | Závazky ze splatné daně | Odložená a splatná daň | všechny | zůstatek | -1 | 1 | 1, 2, 23 |
| 26 | Ostatní závazky | Závazek z úpisu | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Závazek z odkupu | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Závazek z úplat | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Závazek z výkonnostní odměny | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Dohadné položky pasivní | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Neidentifikované platby | všechny | zůstatek | -1 | 1 | 1, 2 |
| 26 | Ostatní závazky | Závazky z nevypořádaných obchodů | všechny | zůstatek | -1 | 1 | 1, 2 |
| 32 | Ostatní vlastní kapitál / Ostatní fondový kapitál | Kapitál třídy | všechny | zůstatek | -1 | 1 | 1, 28 |
| 42 | Nerozdělený zisk nebo neuhrazená ztráta z předchozích období/ Kumulovaný zisk nebo ztráta za předchozí období | Výsledek minulých let | všechny | zůstatek | -1 | 1 | 1, 28 |
| 46 | Zisk nebo ztráta za běžné účetní období | Výsledek běžného období | všechny | zůstatek | -1 | 1 | 1, 28 |

## VYFO20_11: Náklady, výnosy a zisky nebo ztráty (VYFOS20)

| Řádek | Položka ČNB | Role účtu | Kategorie IFRS 9 | Období | Znaménko | Znaménko řádku | Součtové řádky |
|--:|---|---|---|---|--:|--:|---|
| 8 | Úroky z ostatních aktiv | Úrokové výnosy | všechny | od začátku roku | -1 | 1 | 1, 37, 56, 58 |
| 19 | Výnosy z dividend z finančních aktiv jiných než k obchodování povinně v RH vykázané do zisku nebo ztráty | Dividendové výnosy | všechny | od začátku roku | -1 | 1 | 17, 37, 56, 58 |
| 23 | Náklady na poplatky a provize | Úplata za obhospodařování | všechny | od začátku roku | -1 | -1 | 37, 56, 58 |
| 23 | Náklady na poplatky a provize | Úplata depozitáři | všechny | od začátku roku | -1 | -1 | 37, 56, 58 |
| 23 | Náklady na poplatky a provize | Výkonnostní odměna | všechny | od začátku roku | -1 | -1 | 37, 56, 58 |
| 30 | Zisk nebo (-) ztráta z finančních aktiv neurčených k obchodování povinně v RH vykázané do zisku nebo ztráty | Zisk z přecenění na RH | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 30 | Zisk nebo (-) ztráta z finančních aktiv neurčených k obchodování povinně v RH vykázané do zisku nebo ztráty | Ztráta z přecenění na RH | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 30 | Zisk nebo (-) ztráta z finančních aktiv neurčených k obchodování povinně v RH vykázané do zisku nebo ztráty | Realizovaný zisk z nástrojů | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 30 | Zisk nebo (-) ztráta z finančních aktiv neurčených k obchodování povinně v RH vykázané do zisku nebo ztráty | Realizovaná ztráta z nástrojů | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 33 | Kurzové rozdíly - zisk nebo (-) ztráta | Kurzový zisk | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 33 | Kurzové rozdíly - zisk nebo (-) ztráta | Kurzová ztráta | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 35 | Ostatní provozní výnosy | Ostatní výnosy | všechny | od začátku roku | -1 | 1 | 37, 56, 58 |
| 36 | Ostatní provozní náklady | Ostatní náklady | všechny | od začátku roku | -1 | -1 | 37, 56, 58 |
| 40 | Ostatní správní náklady | Úplata za administraci | všechny | od začátku roku | -1 | -1 | 38, 56, 58 |
| 57 | (-) Náklady nebo výnosy na daň z příjmů činností | Daň z příjmů | všechny | od začátku roku | -1 | 1 | 58 |

## RIS30_01: Aktiva v základním členění (RISIFI30)

| Řádek | Položka ČNB | Role účtu | Kategorie IFRS 9 | Období | Znaménko | Znaménko řádku | Součtové řádky |
|--:|---|---|---|---|--:|--:|---|
| 4 | Převoditelné vklady | Bankovní účet | všechny | zůstatek | 1 | 1 | 1, 2, 3 |
| 5 | Ostatní vklady | Termínované vklady | všechny | zůstatek | 1 | 1 | 1, 2, 3 |
| 9 | Úvěry a pohledávky obdobné úvěrům - nad 1 rok | Poskytnuté úvěry | všechny | zůstatek | 1 | 1 | 1, 7 |
| 9 | Úvěry a pohledávky obdobné úvěrům - nad 1 rok | Reverzní repo | všechny | zůstatek | 1 | 1 | 1, 7 |
| 10 | Držené cenné papíry a majetkové účasti | Investiční nástroje | všechny | zůstatek | 1 | 1 | 1 |
| 10 | Držené cenné papíry a majetkové účasti | Dluhové cenné papíry | všechny | zůstatek | 1 | 1 | 1 |
| 10 | Držené cenné papíry a majetkové účasti | Účasti | všechny | zůstatek | 1 | 1 | 1 |
| 10 | Držené cenné papíry a majetkové účasti | Ostatní podíly | všechny | zůstatek | 1 | 1 | 1 |
| 17 | Finanční deriváty - kladná reálná hodnota | Deriváty | všechny | zůstatek | 1 | 1 | 1 |
| 18 | Ostatní aktiva | Peníze na cestě | všechny | zůstatek | 1 | 1 | 1 |
| 18 | Ostatní aktiva | Ostatní pohledávky | všechny | zůstatek | 1 | 1 | 1 |
| 18 | Ostatní aktiva | Vnitřní zúčtování tříd | všechny | zůstatek | 1 | 1 | 1 |
| 18 | Ostatní aktiva | Pohledávky z nevypořádaných obchodů | všechny | zůstatek | 1 | 1 | 1 |
| 18 | Ostatní aktiva | Změna reálné hodnoty nevypořádaných obchodů | všechny | zůstatek | 1 | 1 | 1 |

## RIS30_03: Pasiva v základním členění (RISIFI30)

| Řádek | Položka ČNB | Role účtu | Kategorie IFRS 9 | Období | Znaménko | Znaménko řádku | Součtové řádky |
|--:|---|---|---|---|--:|--:|---|
| 6 | Emitované akcie/podílové listy | Kapitál třídy | všechny | zůstatek | -1 | 1 | 1 |
| 6 | Emitované akcie/podílové listy | Výsledek minulých let | všechny | zůstatek | -1 | 1 | 1 |
| 6 | Emitované akcie/podílové listy | Výsledek běžného období | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Závazek z úpisu | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Závazek z odkupu | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Závazek z úplat | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Závazek z výkonnostní odměny | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Dohadné položky pasivní | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Neidentifikované platby | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Závazky z nevypořádaných obchodů | všechny | zůstatek | -1 | 1 | 1 |
| 8 | Ostatní pasiva | Odložená a splatná daň | všechny | zůstatek | -1 | 1 | 1 |
