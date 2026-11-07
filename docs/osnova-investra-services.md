# Osnova Investra Services (návrh)

Stav 2026-11-07. Účetní rámec: vyhláška č. 500/2002 Sb., podnikatel, CZK. Výchozí bod je standardní česká osnova Odoo 20
(328 účtů, 6místné kódy, `investra_dev`). Směrná účtová osnova je v příloze č. 4 vyhlášky; účtový rozvrh určuje účetní jednotka.
Nic z toho zatím není v Odoo provedené; změny se udělají v testovací společnosti přes Odoo, až se návrh potvrdí.

## Co ponechat

Čísla účtů, šestimístný formát, účty 311, 321, 331, 336, 342, 343, 381 až 389, 411 až 431, 518xxx, 521 až 528, 563, 663 a technické účty banky.

## Co opravit

**Typy účtů.** Typ určuje zařazení v rozvaze, u těchto účtů je ve standardu nesprávný:

| Účet | Dnes | Navrhuji |
|---|---|---|
| 231 Krátkodobé úvěry, 232 Eskontní úvěry | Aktivum | Krátkodobý závazek |
| 241 Emitované krátkodobé dluhopisy, 249 Ostatní krátkodobé finanční výpomoci | Aktivum | Krátkodobý závazek |
| 451, 452, 453, 459 Rezervy | Vlastní kapitál | Závazek |
| 461 Dlouhodobé úvěry | Vlastní kapitál | Dlouhodobý závazek |

Dále zkontrolovat smíšené účty 373, 395 a 481, jejichž znaménko může být aktivní i pasivní.

**Výchozí účty deníků.** Prodejní deník dnes míří na 604000 Tržby za zboží a nákupní deník na 504000 Prodané zboží. Pro servisní firmu navrhuji 602100 a 518000.

**Názvy:** překlepy opravit, například 347 „dodace“ a 563 „Kursové ztráty“.

## Co skrýt

Účty nepotřebné pro servisní společnost se nemažou, jen se vyřadí z běžné nabídky, pokud je Odoo umožní: zásoby a výroba (třída 1, 581 až 588), zemědělství (025, 026, 085, 086), část majetku a dluhopisů podle skutečné činnosti, POS účet 311001.

## Co doplnit

| Účet | Účel |
|---|---|
| 336100, 336200 | Sociální a zdravotní pojištění pro import mezd |
| 342100, 342200 | Záloha na daň a srážková daň ze mzdy |
| 343xxx | Daň k odvodu v režimu registrované osoby; návrh po potvrzení režimu |
| 518xxx | Audit, IT služby a licence, podle skutečných nákladů |

Přesné analytiky doplnit po dohodě s dodavatelem mezd a podle rozpočtu.

## DPH

Registrace zatím nepřišla, proto Services účtuje jako neplátce. Režim se nastaví k datu účinnosti, ne zpětně bez ověření.
U registrované osoby se předpokládá přiznání daně bez nároku na odpočet, takže daň jde do nákladů. Daňové nastavení a povinná podání ověřit před zapnutím.

## Mzdy

Externí dodavatel dodá účetní zápis. Import vytvoří návrh dokladu, účetní ho zkontroluje a zaúčtuje. Účty a formát se domluví s dodavatelem.

## Vazba na fondy

Fondy budou mít vlastní osnovu pro rámec 501, ne tuto. Společné budou role účtů a šestimístný formát, aby Dashboard, přehledy a výkazy pracovaly stejně.
Cílem je jedna šablona pro všechny fondy. Převzatý fond se ke dni přechodu převede převodovou tabulkou a původní číslo účtu se uchová jako odkaz.
Třídy a části fondu zůstávají pole na účetním řádku, ne účty.
