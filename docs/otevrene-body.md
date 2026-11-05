# Otevřené body a rizika

Stav k 2026-11-05. Zdroj pravdy je Claude Doc (sekce Otevřené body a rizika); tento soubor drží stejný seznam.
Uzavřený bod přesunout do `docs/rozhodnuti.md`.

## Rozhodnutí, která chybí

| Bod | Proč na tom záleží | Doporučení |
|---|---|---|
| Community, nebo Enterprise | Chybí finanční výkazy, bankovní párování a oběh dokladů | Rozhodnout nejpozději po zkušebních knihách (etapa 2), před ostrým startem Investra Services. Kritéria: finanční výkazy, bankovní párování, oběh dokladů, cena licencí a hostingu, kompatibilita vlastních modulů |
| Podrobnosti dividend | Účet pro výplatu, dopad na kurz k rozhodnému dni | Upřesnit |
| Zdroje cen | Jaká aktiva fondy drží, frekvence posudků | Upřesnit |
| Možnosti Asetiqu | Závěrka, identifikátory, příjem číselníku a kurzu, dividendy, API | Získat dokumentaci |
| Aktualizace předpisů | ABRA, funkční měna EUR, schvalování, střediska SICAV v předpisu 12 | Projít později, nyní neměnit |
| Start Investra Services | Současné účetnictví, termín přechodu, plátcovství DPH, mzdy, hosting | Upřesnit |
| Zdrojové systémy fondů | Které systémy, zda mají údaje po pozicích a pořizovací kurzy | Upřesnit u prvních fondů |
| Podrozvaha v Odoo | Podpora ve standardním Odoo neověřená; deriváty a opce jsou u fondů významné | Ověřit v prototypu |
| Okamžik zaúčtování obchodu | Datum sjednání, nebo vypořádání | Určit v účetní politice |
| Evidence aktiv uvnitř SPV | Zda vést i aktiva dceřiných společností, nebo jen účast a úvěr | Upřesnit |
| Automatické testy (CI) | Testy modulů se zatím spouštějí ručně | Po prvním funkčním modulu nastavit GitHub Actions s instalací modulu a testy |
| Pole výkazů ČNB | Struktura a kontroly převzaty z metodiky SDAT FOFI20261201 | Stáhnout kódy položek, číselníky a převodníky z Knihovny SDAT; ověřit termíny RISIFI37 a ROFOS13 |

## Chybějící podklady

- [ ] Dokumentace a API Asetiqu.
- [ ] Kdo a kdy zajistí úpravy Asetiqu.
- [ ] Oceňovací dokumentace, včetně „Výpočtu bonusů pro fondy s delší periodou“.
- [ ] Kódy položek, číselníky a převodníky ČNB z Knihovny SDAT.
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
| Nahrazení ABRA | Větší rozsah: oběh dokladů, výkazy, migrace, předpisy, DORA | Postup po fázích, start na Investra Services |
| Chybějící údaje při převzetí fondu | Bez pořizovacího kurzu nebo údajů po pozicích nejde oddělit FX a FV | Účetní postup pro stanovení hodnot ke dni přechodu |
