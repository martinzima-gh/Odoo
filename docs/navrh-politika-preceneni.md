# Politika přecenění cizích měn (návrh)

Stav 2026-11-07. Návrh k připomínkám Martina Zímy a auditora, zatím neschválený. Dvě verze, protože rámce se nemíchají: Investra Services podle vyhlášky 500/2002 Sb., fondy podle vyhlášky 501/2002 Sb. a IFRS.
Přečteno: zákon 563/1991 Sb. ve znění od 1. 1. 2026, vyhlášky 500 a 501 ve znění od 1. 1. 2024 na zakonyprolidi.cz. Ověřit v e-Sbírce. ČÚS jsem nečetl, IAS 21 cituji podle architektury.

**Návrh ve zkratce:** obecný kurz ČNB ke dni přepočtu, bez pevného kurzu. Services povinně k rozvahovému dni, fondy při každém ocenění. Rozdíl z přecenění na oddělené účty, doúčtováním do potřebného zůstatku, bez automatického zaúčtování.

## Co říkají předpisy

| Předpis | Pravidlo |
|---|---|
| § 24 odst. 2 ZoÚ | Ocenění k okamžiku účetního případu a ke konci rozvahového dne nebo k jinému okamžiku závěrky; druhé se zaznamená v účetních knihách |
| § 24c ZoÚ | Přepočet obecným kurzem k oběma okamžikům; ke konci rozvahového dne jen položky z § 4 odst. 12. Pevný kurz lze jen k okamžiku účetního případu |
| § 24d odst. 1 ZoÚ | Obecný kurz je kurz centrální banky příslušné pro měnu účetnictví pro den přepočtu |
| § 24d odst. 3 ZoÚ | Za kurz pro den přepočtu lze považovat i kurz vyhlášený pro předcházející den |
| § 24d odst. 4 ZoÚ | Pevný kurz: období určí vnitřní předpis, končí nejpozději posledním dnem účetního období |
| § 24d odst. 5 ZoÚ | Pevný kurz nesmí použít mimo jiné jednotka s povolením investiční společnosti nebo investičního fondu |
| § 24d odst. 6 ZoÚ | Nákup nebo prodej cizí měny lze přepočítat skutečným kurzem obchodu |
| § 60 vyhlášky 500 | Rozdíly do finančních nákladů a výnosů; u postupného splácení a účtů 21, 22, 26 lze až ke konci rozvahového dne; u cenných papírů a podílů součást ocenění |
| § 79 vyhlášky 501 | Rozdíly se vykazují v příslušné položce výkazu zisku a ztráty |

## Rozhodnutí podle účetní jednotky

| Bod | Investra Services | Fond |
|---|---|---|
| Rámec | Vyhláška 500, podnikatel | Vyhláška 501, IFRS, ZISIF |
| Kurz | ČNB ke dni přepočtu | Centrální banka příslušná pro měnu účetnictví; CZK ČNB, EUR ECB (ověřit) |
| Pevný kurz | Přípustný, návrh nepoužívat | Nepřípustný pro jednotky s povolením; u fondu bez povolení ověřit |
| Den kurzu | Ke dni účetního případu, u české společnosti k DUZP; rozhodnuto 2026-11-07 | Ke dni ocenění |
| Kurz předchozího dne | Přípustný, zvolena jiná varianta | Stejně |
| Víkend a svátek | Poslední vyhlášený | Stejně, nejvýše stáří z parametru |
| Nejvyšší stáří kurzu | 5 dní (návrh) | 5 dní (návrh, parametr fondu) |
| Frekvence | K rozvahovému dni a k jinému okamžiku závěrky; měsíčně dobrovolně | Při každém ocenění |
| Co se přeceňuje | Položky z § 4 odst. 12: pohledávky, závazky, peníze a účty v cizí měně | Peněžní položky; nástroje v rámci reálné hodnoty |
| Protiúčty | Oddělené od realizovaných rozdílů, oba ve finančních nákladech a výnosech | Podle matice IFRS 9 a IAS 21 v architektuře |
| Metoda | Doúčtování do potřebného zůstatku | Stejně |
| Dopad | Výsledek | Výsledek; u FVOCI podle matice |
| Schválení | Účetní zaúčtuje návrh dokladu | Součást ocenění se čtyřma očima |

## Účty pro Services (návrh k výběru)

Účty vybírá Martin Zíma, osnova je zatím návrh. Zvážit analytiky 563 a 663 pro přecenění, oddělené od realizovaných rozdílů. Do profilu patří účty 311, 321 a účty v cizí měně ve skupině 22.

## Co potvrdit

1. Má Services mít měsíční přecenění, nebo jen k závěrce? Návrh: jen k závěrce, měsíčně až podle objemu cizí měny.
2. Má fond s měnou účetnictví CZK brát vždy ČNB? Dnešní rozhodnutí připouští ČNB i ECB; § 24d odst. 1 mluví o centrální bance příslušné pro měnu účetnictví. Ověřit s auditorem.
3. Platí pro fond bez vlastního povolení zákaz pevného kurzu? Návrh: pevný kurz nepoužívat vůbec.
4. Nákup cizí měny skutečným kurzem podle § 24d odst. 6: chceme tuto možnost?
5. Stáří 5 dní je pracovní hodnota, ne požadavek předpisu.

Po schválení se bod „Účetní politika přecenění“ uzavře v `docs/otevrene-body.md` a pravidla se zapíšou do vnitřního předpisu.
