# Regulatorní změny 2026 a 2027

Stav 2026-11-07. Přehled pro návrh systému. Část je z odborných článků; před použitím ověřit ve Sbírce zákonů, EUR-Lex a u ČNB.

**Závěr:** největší dopad má novela ZISIF k AIFMD II, zákon č. 130/2026 Sb., která je podle aktuálního znění účinná od 1. 9. 2026. Model je potřeba rozšířit hlavně o fondové úvěry, nástroje likvidity a depozitáře z EU. Nové výkaznictví AIFMD přijde nejdřív v roce 2029, IFRS 18 od roku 2027.

| Změna | Stav | Účinnost | Dopad na nás |
|---|---|---|---|
| Novela ZISIF (AIFMD II) | Zákon č. 130/2026 Sb., znění ZISIF od 1. 9. 2026 přečteno na zakonyprolidi.cz | Účinná od 1. 9. 2026, část otevřených fondů do 16. 4. 2027, přechody do 16. 4. 2029 | Viz níže |
| AIFMD II, rozšířené hlášení | Směrnice 2024/927; ESMA v květnu 2026 navrhla společný rámec | Povinnosti od 16. 4. 2027, technické normy do dubna 2027, spuštění nejdřív v 1. pololetí 2029 podle odborných zdrojů | Dnešní šablony platí dál, mapování držet jako nastavení |
| IFRS 18 | Přijato EU nařízením 2026/338 | Roky od 1. 1. 2027, se srovnávacími údaji | Účetní závěrky v IFRS; dopad na fondy upřesnit s auditorem |
| Metodika FOFI20261201 | Publikována v SDAT | 1. 12. 2026 | Máme v `docs/cnb` |
| Vyhláška 267/2020 Sb. | Aktuální znění od 1. 7. 2025 | Platí | Promítnuto v `docs/cnb/lhuty.md` |
| NV 243/2013 Sb. | Aktuální znění od 25. 6. 2026; text 103/2026 Sb. samostatně nečten | Platí | § 13: OTC derivát standardního fondu se oceňuje spolehlivě a ověřitelně každý pracovní den |
| Nařízení ECB 2024/1988 | Přijato | Viz architektura | Statistické výkazy, ověřit dopad |
| EMIR 3 | Neověřeno | | Jen pokud fondy budou mít OTC deriváty |

## Co novela ZISIF mění pro model

| Oblast | Podle článku | Dopad v systému |
|---|---|---|
| Fondové úvěry | Nabývání pohledávek z fondových úvěrů, zásady a posuzování rizika, koncentrace, zákaz některých dlužníků | Registr úvěrů, propojené osoby, limity |
| Retence | Ponechání 5 % jmenovité hodnoty vybraných postoupených pohledávek | Evidence při postoupení |
| Fond nabývající úvěry | Strategie, nebo nejméně 50 % FK; uzavřená forma, u otevřeného průkaz likvidity | Ukazatel podílu na FK, upozornění |
| Pákový efekt | 175 % otevřený, 300 % uzavřený fond nabývající úvěry | Výpočet a kontrola limitu |
| Likvidita | Nástroje řízení likvidity, část od 16. 4. 2027 | Parametr fondu a dopad na úpisy a odkupy, vazba na IS |
| Depozitář | Za podmínek zahraniční banka z EU bez pobočky | Balíček a formáty nesmí být vázané na jednoho depozitáře |
| Pověřování | Širší pravidla | Vazba na smlouvy a DORA |
| Přechodná ustanovení | Šest měsíců u vybraných povinností, zvláštní pravidla podle vzniku fondu | Posoudit fond po fondu |

**Pozor:** podle jednoho souhrnu novela ruší povinný reporting podle § 15 ZISIF. V aktuálním znění § 15 dál existuje a rozsah změny jsem nedohledal; ověřit.

## Co doporučuji udělat

1. U každého fondu posoudit přechodná ustanovení čl. II zákona 130/2026 Sb. a doplnit `docs/predpisy-a-standardy.md`.
2. Doplnit parametr nástroje likvidity a registr úvěrů do návrhu, viz `05-dluhove-nastroje.md`.
3. Potvrdit s auditorem dopad IFRS 18 na závěrky fondů.

## Zdroje

- Přečteno v originále: [ZISIF, znění od 1. 9. 2026](https://www.zakonyprolidi.cz/cs/2013-240), [NV 243/2013](https://www.zakonyprolidi.cz/cs/2013-243), [vyhláška 267/2020](https://www.zakonyprolidi.cz/cs/2020-267).
- Přečteno: [Novela ZISIF ve světle AIFMD II (epravo, 24. 7. 2026)](https://www.epravo.cz/top/clanky/novela-zisif-ve-svetle-aifmd-ii-co-prinese-spravcum-fondu-121418.html), [Aktuální stav implementace (AK Schejbal, únor 2026)](https://akschejbal.cz/aktualni-stav-implementace-aifmd-ii-do-zisif).
- Z výňatků: [BDO k IFRS 18](https://www.bdo.global/en-gb/news/ifrs-news/the-european-union-endorses-ifrs-18-presentation-and-disclosure-in-financial-statements), [A&O Shearman k ESMA](https://finreg.aoshearman.com/esma-final-report-on-integrated-collection-of-funds-data-under-aifmd-ii), [EY k reportingu](https://www.ey.com/en_lu/insights/financial-services/esma-sets-direction-for-the-future-of-aifmd-ii-and-ucits-vi-reporting).
