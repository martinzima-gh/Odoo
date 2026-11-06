# Otevřené body a rizika

Stav k 2026-11-05. Zdroj pravdy je Claude Doc (sekce Otevřené body a rizika); tento soubor drží stejný seznam.
Uzavřený bod přesunout do `docs/rozhodnuti.md`.

## Rozhodnutí, která chybí

| Bod | Proč na tom záleží | Doporučení |
|---|---|---|
| Community, nebo Enterprise | Chybí finanční výkazy, bankovní párování a oběh dokladů | Rozhodnout nejpozději po zkušebních knihách (etapa 2), před ostrým startem Investra Services. Kritéria: finanční výkazy, bankovní párování, oběh dokladů, cena licencí a hostingu, kompatibilita vlastních modulů |
| Postup ocenění | Kdy účtovat, typovaná pravidla poplatků, pořadí modulů | Rozhodnout; doporučení je v Doc (Postup ocenění v Odoo) |
| Transakční výkazy a oznámení | Katalog pokrývá jen rámec Fondy; hlášení obchodů mají krátkou lhůtu a vlastní data | Ověřit povinnost Investry, pak rozhodnout o rozsahu a doplnit katalog |
| TISIFI10 u nových smluv | Zda je bez vypořádání přeceněním celá změna RH; mění výsledek v měsíci sjednání | Počítat celou změnu; potvrdit s ČNB před implementací |
| Výkazy speciálních fondů | Speciální fondy mohou podávat jiné výkazy než FKI, například ROFOS11 a DOFOS70 | Ověřit v plánu výskytů SDAT a doplnit tabulku výkazů |
| Příplatek mimo základní kapitál | Zda se počítá do CET1 a na který řádek DOFOS60 patří; ovlivňuje vykázaný kapitál | Potvrdit s auditorem nebo ČNB |
| Podrobnosti dividend | Účet pro výplatu, dopad na kurz k rozhodnému dni | Upřesnit |
| Zdroje cen | Jaká aktiva fondy drží, frekvence posudků | Upřesnit |
| Možnosti IS | Závěrka, identifikátory, příjem číselníku a kurzu, dividendy, API | Získat dokumentaci |
| Aktualizace předpisů | Funkční měna EUR, schvalování, střediska SICAV v předpisu 12 | Projít později, nyní neměnit |
| Start Investra Services | Současné účetnictví, termín přechodu, plátcovství DPH, mzdy, hosting | Upřesnit |
| Zdrojové systémy fondů | Které systémy, zda mají údaje po pozicích a pořizovací kurzy | Upřesnit u prvních fondů |
| Podrozvaha v Odoo | Podpora ve standardním Odoo neověřená; deriváty a opce jsou u fondů významné | Ověřit v prototypu |
| Okamžik zaúčtování obchodu | Datum sjednání, nebo vypořádání | Určit v účetní politice |
| Evidence aktiv uvnitř SPV | Zda vést i aktiva dceřiných společností, nebo jen účast a úvěr | Upřesnit |
| Automatické testy (CI) | Testy modulů se zatím spouštějí ručně | Po prvním funkčním modulu nastavit GitHub Actions s instalací modulu a testy |
| Pole výkazů ČNB | Katalog výkazů, položek, kontrol a číselníků je v `docs/cnb/` (metodika FOFI20261201) | Doplnit ukazatele u položek bez kontroly a převodníky z Knihovny SDAT; ověřit termíny RISIFI37 a ROFOS13 |

## Chybějící podklady

- [ ] Dokumentace a API IS.
- [ ] Kdo a kdy zajistí úpravy IS.
- [ ] Oceňovací dokumentace, včetně „Výpočtu bonusů pro fondy s delší periodou“.
- [ ] Zbývající ukazatele u položek a převodníky ČNB z Knihovny SDAT (ostatní je v `docs/cnb/`).
- [ ] Ukázky nastavení tříd a alokací od zakladatelů.
- [ ] Účetní politika přecenění: účty, kurz, frekvence, protiúčty, metoda, P&L a OCI.
- [ ] Naběhlý úrok a klasifikace podle IFRS 9.

## Rizika

| Riziko | Dopad | Opatření |
|---|---|---|
| Vzorce pokrývají jen zjednodušenou variantu | Nepočítá s převodem hodnoty mezi třídami | Ověřit na ukázkách od zakladatelů |
| Vstup nových investorů za starší kurz | Zvýhodnění nebo poškození stávajících investorů | Nastavení podle statutu, přehled ručních úprav |
| Fondové moduly vyvíjené svépomocí | Trvalá práce na migracích a testech při nových verzích Odoo | Testy, minimum zásahů do core |
| Odoo jako NAV systém | Může se ukázat méně vhodné než specializovaný systém | Ověřit prototypem před produkcí |
| Velký počet společností | Pomalejší práce v UI, složitější souhrnné přehledy | Vlastní přehledy, ověřit v etapě 2 |
| Celé účetnictví v Odoo od začátku | Větší rozsah: oběh dokladů, výkazy, předpisy, DORA | Postup po fázích, start na Investra Services |
| Chybějící údaje při převzetí fondu | Bez pořizovacího kurzu nebo údajů po pozicích nejde oddělit FX a FV | Účetní postup pro stanovení hodnot ke dni přechodu |
