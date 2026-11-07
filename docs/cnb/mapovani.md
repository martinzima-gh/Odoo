# Mapování výkazů ČNB na zdroje dat

Stav 2026-11-07, metodika FOFI20261201. Tabulka všech listů je v `mapovani-FOFI20261201.csv`. Je to pracovní návrh na úrovni listů,
ne buněk: pravidla po buňkách vzniknou v modulu `investra_cnb`. Stavy platí pro prototyp v `investra_test`.

## Výsledek

| Stav | Listů |
|---|--:|
| Základ v prototypu | 3 |
| Část dat | 26 |
| Chybí | 74 |

Prototyp nemá výkazy jako cíl, proto převažuje stav Chybí. Důležité je, že většina listů nestojí na hlavní knize: největší skupina
závisí na portfoliu a atributech nástrojů, další na parametrech fondu a IS.

## Co z toho plyne pro datový model

1. **Protistrana a emitent:** země, sektor, LEI. Dnes chybí, potřebuje je velká část RISIFI30, RISIFI33 a ROFOS35.
2. **Atributy nástroje:** kód CFI, splatnost, vazba na limit. Vazba na limit závisí na fondu, ne jen na nástroji.
3. **Registry:** deriváty po smlouvách, úvěry, účasti, nemovitosti, zatížení aktiv.
4. **Stav „sjednáno, nevypořádáno“:** rozvaha a přehled držených papírů mohou nástroj ukazovat rozdílně.
5. **Data z IS:** datum žádosti, počty investorů podle typů a zemí, dividendy po třídách. Patří do rozhraní s IS.
6. **Šablona výkazu:** buňka je pravidlo s platností od–do a vazbou na metodiku; typy jsou účet, jen kladný zůstatek, absolutní hodnota záporného, součet řádků, údaj z portfolia, filtr podle atributu.
7. **Kladný a záporný zůstatek:** test po nástroji nebo protistraně, ne po účtu.

## K rozhodnutí nebo ověření

- Pravidlo zaokrouhlení výkazů v tis. Kč u fondů v jiné měně: zaokrouhlovat po řádcích a součty dorovnat, nebo počítat součty z nezaokrouhlených hodnot. Návrh: po řádcích z hodnoty v CZK, dopočtené součty podle kontrol s povolenou tolerancí.
- Výklad změn z přecenění u nových derivátů bez vypořádání v TISIFI10: potvrdit u ČNB před implementací.
- Hranici pro pasivní porušení limitu v oznámení ověřit v metodice ČNB.
- Plán výskytů podle typu fondu ověřit v SDAT.
- Transakční reporting a oznámení nejsou v katalogu `docs/cnb`, stáhnout zvlášť.
