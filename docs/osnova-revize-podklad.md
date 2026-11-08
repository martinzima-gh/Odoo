# Revize osnovy Investra Services: podklad k rozhodnutí

Stav 2026-11-07. Doplňuje `docs/osnova-investra-services.md`. Účetní rámec: vyhláška č. 500/2002 Sb., podnikatel, CZK.
Vychází ze čtení `investra_dev` (328 účtů, 0 dokladů) a přílohy č. 4 vyhlášky. V Odoo se zatím nic nezměnilo.
Rozhoduje účetní metodik, doporučení jsou jen návrh. Dotazy k ověření jsou v `docs/sql/08-osnova.sql`.

## Co je v pořádku

- Všech 54 účtových skupin směrné osnovy v Odoo je. Navíc jsou jen technické účty 999997 a 999998 pro slevy při platbě.
- Třídy 0, 1, 5 a 6 mají správné typy. Třída 3 je rozdělená na pohledávky a závazky správně, kromě smíšených účtů.
- Kurzové rozdíly míří na 563000 a 663000, přechodné účty na 261000 a 261001.
- Výchozí daň prodeje a nákupu je prázdná, což odpovídá neplátci.

## Proč to udělat před prvním dokladem

Dnes je 0 dokladů, takže změny typů a párování nic nepřepočítávají. Po prvních dokladech už je změna párování nebo typu pracnější.

Priorita typů je nižší, než říká návrh osnovy. Community nemá rozvahu ani výsledovku, jsou tam jen daňové výkazy.
Typ dnes neovlivňuje výpočet, rozhodne až ve výkazech. Výkazy podle vyhlášky 500 budeme stejně skládat podle čísel účtů, nebo přijdou s edicí.

## Body k rozhodnutí

| # | Bod | Nález | Doporučení |
|--:|---|---|---|
| 1 | Uzávěrkové účty 701, 702, 710 | Mají typ podrozvaha. Odoo nedovolí rozvahový a podrozvahový účet v jednom dokladu, takže klasické uzavírací zápisy nejdou zaúčtovat | Nepoužívat je a výsledek nechat na výpočtu Odoo přes 431000; viz níže |
| 2 | Párování | Vypnuté u všech zúčtovacích účtů kromě 311 až 315, 321, 343001 a 343002. Bez něj nejdou sledovat otevřené položky | Zapnout u 324, 325, 331, 335, 336, 342, 378, 379, 388, 389 |
| 3 | Typy podle návrhu | 231, 232, 241, 249 jsou aktivum; 451 až 459 a 461 vlastní kapitál | Opravit podle `docs/osnova-investra-services.md` |
| 4 | Smíšené účty 373, 395, 481 | Znaménko může být obojí, typ je jen jeden | Nechat typ, zařazení řešit až ve výkazu podle zůstatku |
| 5 | 473200 Vydané krátkodobé dluhopisy | Krátkodobý závazek ve skupině dlouhodobých, 241000 už existuje | Skrýt, Services dluhopisy nevydává |
| 6 | Výchozí účty deníků | Prodej 604000, nákup 504000 | Prodej a nákup podle návrhu osnovy; konkrétní účet potvrdí metodik |
| 7 | Názvy | Překlepy: 347 „dodace“, 358 „združenými“, 563 „Kursové“. 593 uvádí mimořádnou činnost, kterou výkazy už nemají | Opravit názvy, 593000 skrýt |
| 8 | Daně | 32 aktivních daní a 4 fiskální pozice, ač jde o neplátce | Ponechat do potvrzení režimu; ověřit, že účetní nemůže sazbu vybrat omylem |
| 9 | Deníky | Ocenění zásob a Daně na hotovostním základě Services nepotřebuje. Kód nákupního deníku je „PŘIJATÁ FAKTURA“ | Archivovat nepotřebné, kód zkrátit, pokud to nezmění číslování dokladů |
| 10 | Datum otevření účetnictví | V Odoo je 5. 11. 2026, tedy den instalace. Účetní období je kalendářní rok | Doplnit skutečné datum zahájení účetnictví |
| 11 | Účty ke skrytí a doplnění | Seznam je v návrhu osnovy; analytiky mezd závisí na dodavateli | Potvrdit skrytí, analytiky až po dohodě s dodavatelem mezd |

## Bod 5: účet 473200 (rozhodnuto 2026-11-08)

Účet 473200 Vydané krátkodobé dluhopisy je v `investra_dev` archivovaný (bez dokladů, změna přes ORM). Krátkodobé dluhopisy pokrývá 241000 a Services dluhopisy nevydává; archivovaný účet jde kdykoli znovu zapnout.

## Bod 4: smíšené účty 373, 395, 481 (rozhodnuto 2026-11-08)

Nechává se, jak je: 373000 a 395000 aktivum, 481000 dlouhodobý závazek. V Odoo se nic nemění.
Účty se doplní, až budou potřeba (například samostatný účet pro opačné znaménko). Nový účet jde založit kdykoli, i když jsou doklady.
Změna typu existujícího účtu s doklady v Odoo 20 není blokovaná (kromě pohledávek a závazků v prodejních a nákupních deníkách), projeví se ale zpětně ve všech sestavách; proto typ po prvním dokladu neměnit bez posouzení.
Nepřečteno: zařazení zůstatků 373, 395 a 481 do položek rozvahy podle vyhlášky 500 a ČÚS 003.

## Bod 3: typy účtů (rozhodnuto 2026-11-08)

Změněno v `investra_dev` u devíti účtů bez dokladů, žádný nebyl výchozím účtem deníku ani účtem v daních:
krátkodobý závazek: 231000, 232000, 241000, 249000, 453000; dlouhodobý závazek: 451000, 452000, 459000, 461000.
Rezervy 451, 452 a 459 jsou dlouhodobé, rezerva na daň z příjmů krátkodobá. Typ je orientační, ve výkazu rozhoduje zbytková doba splatnosti.

## Bod 2: párování (rozhodnuto 2026-11-08)

Párování zapnuto v `investra_dev` u 324000, 325000, 335000, 342000, 378000, 379000, 388000 a 389000 (bez dokladů, změna přes ORM).
331000 a 336000 zůstávají vypnuté: mzdy vede externí dodavatel a zápisy přijdou v sumě. Zapnout jde později i s doklady; vypnout nejspíš ne, pokud jsou na účtu spárované řádky (neověřeno).
Časové rozlišení 381 až 385 se nepáruje. Community nemá automatický rozpis odložených nákladů a výnosů ani automatické párování dokladů proti sobě; pravidla párování míří na bankovní řádky.

## Bod 1: uzávěrka

Odoo výsledek období nezapisuje dokladem, počítá ho z výnosů a nákladů a ukazuje na účtu typu nerozdělený zisk, zde 431000.
Pravidlo je ověřené ve zdrojovém kódu (`_check_off_balance`). Průběh roční uzávěrky v Odoo zatím ověřený není.

| Varianta | Co znamená | Riziko |
|---|---|---|
| A: účty 70x a 710 nepoužívat | Závěrka se opře o sestavy, rozdělení zisku účetní zaúčtuje ručně | Ověřit, že to stačí pro uzavření účetních knih podle zákona o účetnictví |
| B: změnit účty na rozvahový typ | Uzavírací zápisy půjdou zaúčtovat | Odoo výsledek počítá i tak, hrozí dvojí zobrazení; nutný test |

**Rozhodnuto 2026-11-08: varianta A.** Účty 701000, 702000 a 710000 jsou v `investra_dev` archivované (bez dokladů, změna přes ORM).

- § 17 zákona o účetnictví (znění od 1. 1. 2026) stanoví dny otevření a uzavření knih, ne techniku; odst. 7 zakazuje zápisy do uzavřených knih po schválení závěrky.
- § 4 odst. 8 a příloha 4 vyhlášky 500 předepisují skupiny 70 a 71, ne účty 701, 702, 710. § 4 odst. 10 dovoluje programové vybavení.
- ČÚS 002 popisuje postup přes 701, 702, 710; odchylka podle § 36 odst. 1 je možná, pokud zůstane věrný a poctivý obraz. Úplné aktuální znění ČÚS 002 nebylo přečteno (stránka MF nedostupná), jen změna MF-123342/2013/28.
- Varianta B neprošla: Odoo nemá uzávěrkové období, uzavírací zápisy k 31. 12. by vynulovaly rozvahu k tomu dni a převod 710 na 431 by výsledek započetl dvakrát.

Před první uzávěrkou: popsat postup ve vnitřní směrnici a ověřit s auditorem, archivovat předvahu, rozdělení výsledku z 431 účtovat ručně, po schválení nastavit nevratný zámek období a v SQL předvaze přičíst k 431 výsledek minulých let.

## Co se tím neřeší

- Výkazy podle vyhlášky 500 v Community chybí a souvisí s rozhodnutím o edici.
- Režim DPH a účty 343xxx čekají na potvrzení registrace.
- Jednotná osnova fondů je zvlášť (`docs/osnova-fondu.md`), rámec vyhlášky 501.
