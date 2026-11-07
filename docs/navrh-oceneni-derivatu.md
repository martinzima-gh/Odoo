# Oceňování derivátů (návrh)

Stav 2026-11-07. Jen návrh, nic z toho není naprogramované. Účetní rámec: fond, vyhláška 501/2002 Sb., IFRS 13 a IFRS 9, reálná hodnota podle § 196 ZISIF.
Modely schvaluje představenstvo a navrhuje oddělení oceňování (Pravidla oceňování majetku a dluhů fondů). Odoo model neurčuje, jen použije schválený.

## Východiska

- **IFRS 13** předepisuje hierarchii vstupů, ne konkrétní model.
- **Vyhláška 244/2013 Sb.**, § 34, řeší jen zvláštní případy; o modelech derivátů v úplném znění z roku 2016 nic není. Pozdější změny ověřit.
- **NV 243/2013 Sb.**, § 13 (podmínky pro OTC deriváty): text jsem nečetl; ověřit v platném znění včetně 103/2026 Sb.
- **Pravidla oceňování:** obchodované deriváty kurzem z aktivního trhu; měnové deriváty podle Přílohy 1; úrokové swapy podle Přílohy 2; opce podle části Opce; opce na svolání podle Přílohy 5.
- **EMIR:** dopad na denní přecenění a hlášení OTC derivátů ověřit podle druhu fondu.

## Pořadí zdrojů hodnoty

1. Kotovaná cena na aktivním trhu (úroveň 1).
2. Schválený model s pozorovatelnými vstupy (úroveň 2).
3. Schválený model s nepozorovatelnými vstupy, nebo externí ocenění (úroveň 3).

Ocenění protistrany je kontrola, ne náhrada modelu. Pro složité nástroje zůstává výpočet mimo Odoo s přílohou a důvodem, stejně jako u úplat.

## Modely

| Nástroj | Model | Hlavní vstupy | Úroveň | Oběh |
|---|---|---|---|---|
| Futures, burzovní opce | Závěrečná cena trhu | Cena | 1 | Přímo |
| FX forward, FX swap, NDF | Současná hodnota toků obou měn | Spot, křivky obou měn | 2 | Příloha 1 |
| FRA, úrokový swap | Forwardové sazby a diskontování | Křivka projekce a diskontní křivka | 2 | Příloha 2 |
| Měnový úrokový swap | Současná hodnota obou nohou, měnová báze | Křivky, spot, báze | 2 | Doplnit metodiku |
| Akciová opce evropská | Black-Scholes-Merton | Spot, volatilita, sazba, dividendy | 2 až 3 | Část Opce |
| Opce americká | Binomický strom | Stejné, plus termíny uplatnění | 2 až 3 | Část Opce |
| Měnová opce | Garman-Kohlhagen; americká stromem | Spot, obě sazby, volatilita | 2 | Doplnit metodiku |
| Cap, floor, swaption | Black-76; při sazbách kolem nuly Bachelier | Forward, volatilita | 2 | Doplnit metodiku |
| Opce na svolání dluhopisu | Ztráta úrokového výnosu | Sazby, volatilita, náklady reemise | 3 | Příloha 5 |
| Opce ve smlouvách o účastech, strukturované produkty | Strom, simulace, nebo externí ocenění | Podle smlouvy | 3 | Rozhodnutí představenstva |

## Společná pravidla

- **Křivky:** podle aktuální referenční sazby měny, u zajištěných obchodů diskontování podle úročení kolaterálu. Přesnou konstrukci a zdroj dat určí metodika.
- **Kurz:** stejný zdroj jako v ocenění fondu.
- **Úvěrové riziko:** CVA a DVA zjednodušeně, nebo nulové při plném zajištění, s limitem významnosti. Postup potvrdit s auditorem.
- **Volatilita:** implikovaná z trhu; historická jen se zdůvodněním a jako úroveň 3.

## Vazba na Odoo

- **Registr derivátu:** obě nohy, nominály, protistrana, zajištění, data sjednání a splatnosti, kód modelu.
- **Tržní data:** křivky a volatility s datem, zdrojem a schválením jako ceny; ocenění uloží použitý snímek.
- **Modely:** čisté funkce ve výpočetním jádru, s číslem verze a platností. Každý model má test proti nezávislému výpočtu.
- **Výsledek:** hodnota po smlouvě, může být záporná, s rozpadem po nohách, úrovní a porovnáním s oceněním protistrany. Překročení tolerance je upozornění pro schvalovatele.
- **Účtování:** brutto po smlouvách, kladná hodnota na aktivní roli, záporná na nové pasivní roli; výsledek přes přecenění. Nominály v podrozvaze vlastním dokladem.
- **Výkazy:** DOFO31_21 a DOFO31_22, list Portfolio se záporným znaménkem.

## Doporučené etapy

1. Registr, tržní data, kotované deriváty, FX forward a swap, úrokový swap, kontrola proti protistraně.
2. Black-Scholes-Merton, Garman-Kohlhagen a binomický strom.
3. Měnový úrokový swap, Black-76 a Bachelier, CVA a DVA.

Ostatní přes externí ocenění. Deriváty nejsou v povinném rozsahu pro první fond, pořadí upřesnit podle jeho skutečných pozic.
