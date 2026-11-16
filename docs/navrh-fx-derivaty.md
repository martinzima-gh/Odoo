# FX forward a FX swap – zjednodušené řešení (návrh)

Stav: zásady schválil Martin 15. 11. 2026 (varianta B). Nahrazuje pro tyto dva nástroje model „současná hodnota toků“
z `docs/navrh-oceneni-derivatu.md`; ten zůstává cílovým stavem. Účetní jednotka: fond, vyhláška č. 501/2002 Sb.

## Rozsah

Měnový forward a měnový swap, mimoburzovní, vypořádání dodáním obou měn. **Mimo:** zajišťovací účetnictví a přiřazení
výsledku třídě (rozhodnutí Martina: zatím ne), diskontování, úrokové sazby měn, kolaterál, NDF, opce, předčasné ukončení.

## Evidence

- Nový modul `investra_derivative` (závisí na `investra_nav`), nabídka Portfolio → Deriváty.
- **Smlouva** (`investra.derivative`): fond, portfolio, protistrana, druh (forward / swap), datum sjednání, číslo
  smlouvy, stav (Návrh → Sjednáno → Vypořádáno; Stornováno). Ke smlouvě vzniká 1 : 1 nástroj typu `derivative_otc`
  (už existuje: role `derivative`, FVTPL, list ČNB DOFO31_22), aby fungovalo portfolio, zařazení a výkazy.
- **Noha** (`investra.derivative.leg`): datum vypořádání, kupovaná měna a částka, prodávaná měna a částka, sjednaný
  kurz (dopočtený), stav (Otevřená / Vypořádaná). Forward má jednu nohu, swap dvě (blízkou a vzdálenou).
- **Ruční hodnota** (`investra.derivative.value`): smlouva, datum ocenění, částka a měna, zdroj, příloha nebo důvod.

## Podrozvaha

Při sjednání se za každou nohu zapíše pohledávka v kupované měně a závazek v prodávané měně v nominálech, přepočtené
kurzem dne sjednání; rozdíl jde na vyrovnávací účet podrozvahy. Při ocenění se cizoměnové nominály přepočtou kurzem
ocenění proti vyrovnávacímu účtu, při vypořádání se noha odúčtuje. Účty typu `off_balance` (Odoo je má, do FK
nevstupují: ocenění sčítá jen aktiva a závazky). Osnova fondu podrozvahové účty zatím nemá – doplnit.

## Reálná hodnota (varianta B)

Pro otevřenou nohu, `k(t)` = kurz měny k funkční měně fondu ze zdroje kurzů ocenění:

- `V(t) = kupovaná částka × k_kup(t) − prodávaná částka × k_prod(t)`
- `B0 = V(den sjednání)` – forwardové body ve funkční měně, uloží se na noze při sjednání
- `RH(t) = V(t) − B0 × zbývající dny / dny celkem` (dny od sjednání do vypořádání; po splatnosti 0)

První den je RH nulová, v den vypořádání rovna `V`. RH smlouvy = součet otevřených noh. Ruční hodnota k datu ocenění
má přednost, ocenění ukáže obě a rozdíl. Výpočet je čistá funkce s uloženými vstupy (půjde nahradit sazbami měn).

## Účtování

| Okamžik | Zápis | Kde |
|---|---|---|
| Sjednání | podrozvaha: MD pohledávka, D závazek, rozdíl vyrovnávací účet | tlačítko Sjednat, náhled |
| Ocenění | přepočet podrozvahy; rozvaha: změna RH proti minulému stavu – kladná RH MD `derivative`, záporná D nová role `derivative_liability`, proti výsledku (nové role `gain_derivative`, `loss_derivative`) | návrh dokladu v ocenění |
| Vypořádání nohy | dopočet RH na `V` ke dni vypořádání, oba peněžní toky na bankovních účtech, zrušení RH, storno podrozvahy nohy | tlačítko na noze, náhled |
| Storno | storna dokladů přes `_reverse_events` | tlačítko, důvod |

Vše přes účetní události (`investra.accounting.event`) a `investra.posting.preview`. Výsledek se dělí mezi třídy
jako běžný výsledek fondu. Smlouva se účtuje brutto (kladná a záporná RH různých smluv se nezapočítává).

## Příklad (fond v CZK, FX swap, čísla smyšlená)

Sjednáno 30. 9. 2026 při kurzu 25,00. Blízká noha 2. 10.: koupě 1 000 000 EUR za 25 000 000 Kč (B0 = 0, při vypořádání
prostá směna). Vzdálená noha 31. 12. (92 dnů): prodej 1 000 000 EUR za 24 900 000 Kč, B0 = 24 900 000 − 25 000 000 = −100 000.

| Den | Kurz | V | Zbývá dnů | RH | Změna do výsledku |
|---|---|---|---|---|---|
| 30. 9. sjednání | 25,00 | −100 000,00 | 92 | 0,00 | – |
| 31. 10. ocenění | 24,80 | 100 000,00 | 61 | 166 304,35 | +166 304,35 |
| 30. 11. ocenění | 25,10 | −200 000,00 | 31 | −166 304,35 | −332 608,70 |
| 31. 12. vypořádání | 25,20 | −300 000,00 | 0 | −300 000,00 | −133 695,65 |

Součet změn −300 000,00 = 24 900 000 − 1 000 000 × 25,20. Zápisy vzdálené nohy:

- 30. 9. podrozvaha: MD pohledávka 24 900 000; D závazek 25 000 000; MD vyrovnávací 100 000.
- 31. 10.: podrozvaha MD závazek 200 000 / D vyrovnávací 200 000; rozvaha MD `derivative` 166 304,35 / D `gain_derivative`.
- 30. 11.: podrozvaha D závazek 300 000 / MD vyrovnávací; rozvaha D `derivative` 166 304,35, D `derivative_liability`
  166 304,35, MD `loss_derivative` 332 608,70.
- 31. 12.: MD `loss_derivative` 133 695,65 / D `derivative_liability`; MD banka CZK 24 900 000, MD `derivative_liability`
  300 000, D banka EUR 25 200 000 (1 000 000 EUR); podrozvaha nohy odúčtována.

## Kontroly ocenění

Noha po datu vypořádání nevypořádaná (chyba); chybí kurz měny (chyba); ruční hodnota bez přílohy a důvodu (chyba);
rozdíl ruční a spočtené hodnoty nad tolerancí (upozornění); smlouva ve stavu Návrh s datem sjednání do dne ocenění (upozornění).

## Testy

Výpočet RH proti tabulce příkladu na haléř; RH = 0 v den sjednání; ruční hodnota má přednost jen pro své datum;
sjednání a storno podrozvahy (zůstatky 0); přepočet podrozvahy; dvě ocenění a vypořádání dají zápisy příkladu;
FK = aktiva − závazky po každém kroku; podrozvaha FK nemění; opakovaný výpočet nic nezdvojí; fond s funkční měnou EUR.

## Neověřeno a otevřené

- Ověřeno v DE-03 (16. 11. 2026): podrozvaha od sjednání v hodnotě podkladového nástroje – vyhláška č. 501/2002 Sb.
  § 35 a § 41, ČÚS pro finanční instituce č. 110 body 7 a 8; RH v rozvaze, kladná v ostatních aktivech (§ 14 odst. 1),
  záporná v ostatních pasivech (§ 20 odst. 1), změny do skupin 61 / 71 (ČÚS 110 body 9 a 11); spot do 2 dnů není
  derivát (ČÚS 110 bod 1 c), třída 9 bod 7), jeho kurzové rozdíly jdou do 61 / 71 proti skupině 35 (ČÚS 105 bod 3).
  Čísla účtů schválil Martin 16. 11. 2026, viz deník. Neověřeno: výjimka z ČÚS 110 pro jednotky podle § 2 odst. 1
  vyhlášky (bod 37) ve vztahu k fondu, vazba § 4a vyhlášky na IFRS a novely vyhlášky po 1. 1. 2024.
- RH bez diskontování a tržních forwardových bodů je zjednodušení proti IFRS 13 a vnitřním Pravidlům oceňování
  (Příloha 1): před prvním skutečným fondem ověřit s auditorem; do té doby jen ukázková data.
- EMIR (nařízení (EU) č. 648/2012) a limity ZISIF a NV č. 243/2013 Sb.: dopad na evidenci neověřen, mimo první verzi.
- Řádky výkazů ČNB pro zápornou RH a podrozvahu: návrh mapování v DE-05, rozhodnutí v etapě CN.
