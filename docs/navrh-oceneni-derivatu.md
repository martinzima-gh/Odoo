# Oceňování derivátů (návrh)

Stav 2026-11-07. Jen návrh, odložené: nic z toho není naprogramované, stavět až podle pozic prvních fondů. Účetní rámec: fond, vyhláška 501/2002 Sb., IFRS 13 a IFRS 9, reálná hodnota podle § 196 ZISIF.
Modely schvaluje představenstvo a navrhuje oddělení oceňování (Pravidla oceňování majetku a dluhů fondů). Odoo model neurčuje, jen použije schválený.

## Východiska

| Zdroj | Co z něj plyne | Stav ověření |
|---|---|---|
| AIFMR 231/2013, čl. 67 | Metodika pro každý druh aktiva; nový druh aktiva až po určení metodiky | Přečteno z vyhledávání |
| AIFMR, čl. 68 | Model je zdokumentovaný, před použitím ho ověří odborník, který ho nestavěl, a předem ho schválí vrcholné vedení | Přečteno |
| AIFMR, čl. 70 a 71 | Pravidelný přezkum pravidel a přezkum jednotlivých hodnot | Nadpisy přečteny, čl. 71 ze souhrnu |
| EMIR 648/2012, čl. 11 odst. 2 | Finanční protistrany přeceňují OTC smlouvy denně tržně; když to trh neumožní, spolehlivým a obezřetným modelem | Z EUR-Lex a ESMA, ověřit podle EMIR 3 |
| Nařízení 149/2013, čl. 16 a 17 | Kdy jde použít model; model používá tržní data v co největší míře, odpovídá uznávaným metodám a je kalibrovaný a testovaný | Z výňatků |
| Směrnice 2007/16/ES, čl. 8 odst. 4 | UCITS: ocenění se nesmí opírat jen o kotaci protistrany; model s uznanou metodikou; ověření nezávislou třetí stranou, nebo nezávislým útvarem | Přečteno; odkazy na starší směrnici ověřit |
| IFRS 13, odst. 61, 64 až 67 | Co nejvíc pozorovatelných vstupů, kalibrace na transakční cenu, změna techniky jako změna odhadu | Přečteno |
| IFRS 13, odst. 72 až 90, B35, B36 | Úroveň určuje nejnižší významný vstup; u úrovně 2 pozorovatelnost po téměř celou dobu; opce s historickou volatilitou je úroveň 3 | Přečteno, B35 a B36 ze souhrnu |
| IFRS 13, odst. 42, 48, B11 | Riziko neplnění u závazku; portfoliová výjimka; Black-Scholes-Merton a binomický model jako příklady techniky | Přečteno |
| ESMA34-45-1802 (2023) | Slabiny dohledu: nejasná definice a validace modelů, nezávislost oceňování, zachycení chyb; zaměřeno na méně likvidní aktiva, ne na deriváty | Přečteno |
| Basel, pokyny k reálné hodnotě (2009) | Citlivost parametrů a přiměřenost předpokladů modelu; pro banky, jen jako dobrá praxe | Z výňatků |
| IOSCO, zásady 2013 a doporučení FR/03/2026 | Nezávislé ověření a odpovědnost za ocenění; novější text je třeba přečíst | Zásady 2013 z výňatků, FR/03/2026 nedostupné |
| ZISIF, § 196 | Reálná hodnota podle IFRS | Z výňatků |
| Vyhláška 244/2013 Sb. | § 34 o zvláštních případech je v aktuálním znění od 1. 9. 2026 zrušený; o modelech derivátů vyhláška nemluví | Přečteno |
| NV 243/2013 Sb., § 13 | Standardní fond: OTC derivát se oceňuje spolehlivě a ověřitelně každý pracovní den, přípustná protistrana pod dohledem, možnost ukončení za nerovnovážných podmínek vyloučena | Přečteno, znění od 25. 6. 2026 |
| Pravidla oceňování | Část Opce, tabulka metod, Přílohy 1, 2 a 5 | Přečteno |

Druh fondu rozhoduje, co platí: AIFMR pro AIF, směrnice 2007/16/ES pro UCITS. Zda a jak se EMIR vztahuje na konkrétní fond, ověřit právně.

## Řízení modelů

- **Blokace:** derivát bez schváleného modelu nejde založit do ocenění.
- **Stavy modelu:** návrh, validace jinou osobou než autorem, schválení vedením, platný, vyřazený. Odoo eviduje doklady a verze; AI nic neschvaluje.
- **Kalibrace:** při sjednání se model porovná s transakční cenou a rozdíl se vysvětlí.
- **Nezávislé ověření:** ocenění se porovná s protistranou, cena protistrany ale nestačí sama o sobě.
- **Přezkum:** alespoň ročně, s porovnáním výsledků a citlivostí parametrů. Změna modelu je nová verze a změna odhadu.
- **Chyby:** oprava chybného ocenění jde stejným postupem jako oprava NAV, který zbývá doplnit.

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
