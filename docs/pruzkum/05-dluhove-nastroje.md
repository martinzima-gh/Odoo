# Dluhové nástroje a peněžní trh

Stav 2026-11-07. Návrh, nic není naprogramované. Rámec: fond, IFRS 9, reálná hodnota podle § 196 ZISIF. Odstavce IFRS 9 u variabilní sazby a repa jsou z paměti, ověřit v textu standardu.

**Návrh:** vklady, repo, dluhopisy a úvěry budou mít jeden model peněžních toků a jedno účtování úroku. Liší se jen parametry a smluvní registr, ne výpočet.

## Co už máme

Typy nástrojů, konvence dnů, EIR a lineární úročení, smluvní toky na jednotku, parametr Trade date a Settlement date. Chybí generování kalendáře, změna sazby, účtování úroku a splátek a registr úvěrů.

## Společný model

| Prvek | Obsah |
|---|---|
| Smluvní podmínky | Jistina, měna, sazba pevná nebo referenční a marže, konvence, frekvence, pracovní kalendář, splatnost |
| Kalendář toků | Generovaný z podmínek, verzovaný, s ruční úpravou a důvodem |
| Stav | Jistina, naběhlý úrok, nerozpuštěný rozdíl, opravná položka |
| Události | Pořízení, naběhnutí úroku, kupón, splátka, změna sazby, prodej, odpis |

## Podle nástroje

| Nástroj | Ocenění | Zvláštnosti |
|---|---|---|
| Termínovaný vklad | Naběhlá hodnota, EIR nebo lineárně | Protistrana, automatické obnovení, předčasné ukončení. Vykázat zvlášť od běžného účtu |
| Reverzní repo | Pohledávka v naběhlé hodnotě | Kolaterál se neúčtuje jako aktivum fondu, jen eviduje; cena zpětného prodeje, rozdíl je úrok; přecenění kolaterálu a dozajištění |
| Repo | Závazek v naběhlé hodnotě | Převedený cenný papír zůstává v rozvaze fondu, označit jako zatížený; dnes typ v číselníku není |
| Dluhopis v RH | Čistá cena a naběhlý úrok zvlášť | Výnos úroku a změna RH odděleně; ACT/ACT ICMA potřebuje kalendář kupónů |
| Dluhopis v naběhlé hodnotě | EIR | Jen pokud to dovolí obchodní model a ZISIF |
| Úvěr s pevnou sazbou | Model nebo EIR | Registr, čerpání, splátky, poplatky jako součást EIR |
| Úvěr s variabilní sazbou | Model nebo EIR | Při změně sazby přepočet EIR a toků dopředu, bez zpětného dopadu |

## Účtování

Úrok se účtuje v každém ocenění jako doplatek do potřebného zůstatku, stejně jako přecenění, takže opakovaný výpočet nic nezdvojí.

| Událost | MD | D |
|---|---|---|
| Naběhnutí úroku | Nástroj nebo naběhlý úrok | Úrokové výnosy |
| Přijetí kupónu | Banka | Naběhlý úrok |
| Splátka jistiny | Banka | Nástroj |
| Změna RH u dluhopisu | Nástroj | Zisk z přecenění |
| Kurzový rozdíl | Nástroj | Kurzový zisk, z naběhlé hodnoty |

Potřebné nové role: naběhlý úrok aktivní, závazek z repa, opravná položka.
Vzorec FX v architektuře platí jen bez úročení; u úročených nástrojů se počítá z naběhlé hodnoty v měně nástroje.

## Co přinese novela ZISIF

Registr úvěrů musí unést dlužníka a propojené osoby, koncentraci, 5% retenci při postoupení, posouzení rizika a ukazatel podílu úvěrů na FK. Viz `02-regulatorni-zmeny.md`.

## Etapy

1. Termínovaný vklad: kalendář, úrok v ocenění, splacení; odstraní dnešní zastavení ocenění.
2. Dluhopis v RH: čistá cena, naběhlý úrok, kupóny.
3. Reverzní repo s kolaterálem.
4. Úvěry: registr, variabilní sazba, přepočet EIR.
5. Repo a opravné položky podle použití ve fondech.

Každou etapu otestovat proti ručně spočítanému příkladu. Rozhodnout: má být lineární úročení povolené i pro úvěry, nebo jen pro krátké nástroje? Oceňování v reálné hodnotě u úvěrů potvrdit s auditorem.
