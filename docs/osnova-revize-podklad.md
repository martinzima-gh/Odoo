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

## Bod 1: uzávěrka

Odoo výsledek období nezapisuje dokladem, počítá ho z výnosů a nákladů a ukazuje na účtu typu nerozdělený zisk, zde 431000.
Pravidlo je ověřené ve zdrojovém kódu (`_check_off_balance`). Průběh roční uzávěrky v Odoo zatím ověřený není.

| Varianta | Co znamená | Riziko |
|---|---|---|
| A: účty 70x a 710 nepoužívat | Závěrka se opře o sestavy, rozdělení zisku účetní zaúčtuje ručně | Ověřit, že to stačí pro uzavření účetních knih podle zákona o účetnictví |
| B: změnit účty na rozvahový typ | Uzavírací zápisy půjdou zaúčtovat | Odoo výsledek počítá i tak, hrozí dvojí zobrazení; nutný test |

Doporučení: A, ověřit na zkušební účetní uzávěrce a s auditorem. Text § 17 zákona o účetnictví jsem pro tento bod nečetl.

## Co se tím neřeší

- Výkazy podle vyhlášky 500 v Community chybí a souvisí s rozhodnutím o edici.
- Režim DPH a účty 343xxx čekají na potvrzení registrace.
- Jednotná osnova fondů je zvlášť (`docs/osnova-fondu.md`), rámec vyhlášky 501.
