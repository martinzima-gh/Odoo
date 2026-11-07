# Lhůty výkazů ČNB za fond

Stav 2026-11-07. Přečteno: vyhlášky 267/2020 Sb. a 314/2013 Sb. ve znění od 1. 7. 2025 na zakonyprolidi.cz.
Jen podklad pro kontrolu. Zdrojem termínů a výkazů v systému bude SDAT, odkud se budou stahovat; tato tabulka se do Odoo nenahrává.

| Výkaz | Formulář | Období | Lhůta | Pro koho | Zdroj |
|---|---|---|---|---|---|
| RISIFI30 | FKI (ČNB) 1-12 | Měsíc | 25 dnů následujícího měsíce | FKI, speciální, standardní, ne fond peněžního trhu | § 4 odst. 2 a 3 vyhlášky 314/2013 Sb. |
| RISIFI33 | FKI (ČNB) 3-12 | Měsíc | 25 dnů následujícího měsíce | FKI, speciální, standardní, ne fond peněžního trhu | § 4 odst. 2 a 3 vyhlášky 314/2013 Sb. |
| TISIFI10 | FKI (ČNB) 4-12 | Měsíc | 25 dnů následujícího měsíce | FKI, speciální, standardní, ne fond peněžního trhu | § 4 odst. 2 a 3 vyhlášky 314/2013 Sb. |
| RISIFI30_MMF | FKI (ČNB) 1-12 | Měsíc | 15 dnů následujícího měsíce | FKI, speciální, standardní, jen fond peněžního trhu | § 4 odst. 3 vyhlášky 314/2013 Sb. |
| RISIFI33_MMF | FKI (ČNB) 3-12 | Měsíc | 15 dnů následujícího měsíce | FKI, speciální, standardní, jen fond peněžního trhu | § 4 odst. 3 vyhlášky 314/2013 Sb. |
| TISIFI10_MMF | FKI (ČNB) 4-12 | Měsíc | 15 dnů následujícího měsíce | FKI, speciální, standardní, jen fond peněžního trhu | § 4 odst. 3 vyhlášky 314/2013 Sb. |
| VISIFI10 | IF (ČNB) 10-12 | Měsíc | 25 dnů následujícího měsíce | FKI, speciální, standardní, ne fond peněžního trhu | § 4 odst. 2, 3 a 6 vyhlášky 314/2013 Sb. |
| RISIFI37 | FKI (ČNB) 5-12 | Měsíc | 30 dnů následujícího měsíce | FKI | § 4 odst. 4 vyhlášky 314/2013 Sb. |
| VISIFI20 | IF (ČNB) 20-01 | Rok | Do konce 4. měsíce | FKI, speciální, standardní, ne fond peněžního trhu | § 4 odst. 5 a 6 vyhlášky 314/2013 Sb. |
| ROFOS10_FKI | OFZ (ČNB) 10-04 | Rok | Do konce 4. měsíce | FKI | § 5 odst. 1 vyhlášky 267/2020 Sb. |
| VYFOS20_FKI | OFZ (ČNB) 20-04 | Rok | Do konce 4. měsíce | FKI | § 5 odst. 1 vyhlášky 267/2020 Sb. |
| ROFOS13 | OFZ (ČNB) 34-01 | Rok | Do konce 4. měsíce | FKI | § 5 odst. 1 vyhlášky 267/2020 Sb. |
| ROFOS11 | OFZ (ČNB) 11-12 | Měsíc | 30 dnů | speciální, standardní | § 4 odst. 1 písm. a) vyhlášky 267/2020 Sb. |
| ROFOS10 | OFZ (ČNB) 10-04 | Čtvrtletí | 35 dnů, po roce 50 dnů | speciální, standardní | § 4 odst. 1 písm. b) vyhlášky 267/2020 Sb. |
| VYFOS20 | OFZ (ČNB) 20-04 | Čtvrtletí | 35 dnů, po roce 50 dnů | speciální, standardní | § 4 odst. 1 písm. b) vyhlášky 267/2020 Sb. |
| DOFOS31 | OFZ (ČNB) 31-04 | Čtvrtletí | 40 dnů, po roce 55 dnů | speciální, standardní | § 4 odst. 1 písm. c) vyhlášky 267/2020 Sb. |
| DOFOS40 | OFZ (ČNB) 40-04 | Čtvrtletí | 40 dnů, po roce 55 dnů | speciální, jen nemovitostní | § 4 odst. 3 vyhlášky 267/2020 Sb. |
| DOFOS70 | OFZ (ČNB) 70-01 | Rok | Do konce 1. měsíce | FKI, speciální, standardní | § 7 odst. 1 vyhlášky 267/2020 Sb. |
| ROFOS37 | OFZ (ČNB) 37-01 | Rok | Do konce 1. měsíce | FKI, speciální, podlimitní správce | § 6 odst. 2 vyhlášky 267/2020 Sb. |

## Poznámky

- **Termíny se neposouvají:** ani jedna vyhláška neřeší konec lhůty ve dnech pracovního klidu, v tabulce je proto kalendářní datum, tedy opatrnější varianta.
- **Únor:** „do 30 dnů následujícího měsíce“ je pro únor nejvýše jeho poslední den, opět opatrnější výklad.
- **Nadlimitní správce:** ROFOS33 a ROFOS35 mají lhůty podle čl. 110 odst. 3 AIFMR a závisí na objemu.
- **Výkazy za společnost:** ROFOS10, VYFOS20, DOFOS50, DOFOS60, ROFOS36 a DOFOS15 za obhospodařovatele nebo správce sem nepatří.
- **KLISIFI10:** podává se při vzniku fondu nebo změně klasifikace do 25 dnů po konci měsíce, je to událost, ne období.
- **Podfondy:** výkazy se podávají za každý podfond; v modelu je podfond samostatný fond.
- **Opravy:** opravný výkaz bez zbytečného odkladu, po auditu do 30 dnů (§ 11 vyhlášky 267/2020 Sb.).

## K ověření

- Katalog FOFI20261201 uvádí pro `OFZ (ČNB) 11-12` jiný název než vyhláška; výkaz `OFZ (ČNB) 32-04` v aktuálním znění vyhlášky ani v katalogu není.
- Znění a účinnost vyhlášky 314/2013 Sb. v e-Sbírce.
- Kdy se povinnost pro nově vzniklý fond poprvé použije.
