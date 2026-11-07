# Převzetí fondu

Stav 2026-11-07. Pracovní postup pro převzetí fondu od jiného administrátora, navazuje na akceptaci v `docs/harmonogram.md`. Právní kroky (statut, depozitář, ČNB, smlouvy) posoudí právník, nejsou tu ověřené.

**Princip:** převezme se stav ke dni přechodu, ne historie dokladů. Odoo začíná počátečním dokladem a historie zůstává dostupná jako podklad.

## Postup

| Krok | Výstup | Kontrola |
|---|---|---|
| 1. Příprava | Datum přechodu, odpovědnosti, seznam dat | Schválený plán |
| 2. Nastavení | Kniha, fond, třídy, parametry, úplaty, převodová tabulka účtů | Čtyři oči |
| 3. Zkušební načtení | Data k předchozímu měsíci | Shoda se zdrojem |
| 4. Souběh | Dvě po sobě jdoucí ocenění | NAV a kurz shodné, rozdíly vysvětlené |
| 5. Uzávěrka zdroje | Finální data ke dni přechodu, potvrzená předchozím administrátorem | Předvaha, pozice, kusy |
| 6. Přechod | Počáteční doklad, zámek období, první ocenění | Schválení odpovědnou osobou |
| 7. Po přechodu | První výkazy ČNB, balíček pro audit a depozitáře | Kontroly ČNB |

## Co žádat od předchozího administrátora

| Oblast | Data |
|---|---|
| Účetnictví | Předvaha, účtová osnova, otevřené položky, dohady, časové rozlišení, poslední závěrka a audit |
| Pozice | Nástroje, kusy, pořizovací cena v měně a funkční měně, přecenění, kurzový rozdíl, potvrzení depozitáře |
| Nástroje | ISIN, klasifikace IFRS 9, úroveň RH, oceňovací podklady, smlouvy, kalendáře kupónů, EIR |
| Třídy | Kusy, kurzy, historie NAV, zaokrouhlení, kapitál tříd |
| Úplaty | Sazby a jejich změny, výpočty, nezaplacené závazky, HWM, referenční hodnoty, nasčítané odměny |
| Banka | Účty, zůstatky, nevypořádané platby |
| Obchody | Sjednané nevypořádané obchody, upisovací závazky, podrozvaha |
| Daně | Odložená a splatná daň, přeplatky |
| Regulace | Poslední výkazy ČNB, opravy, hlášení, limity, porušení a jejich stav |
| Dokumenty | Statut, oceňovací podklady, smlouvy, záznamy o incidentech a chybách NAV |

## Na co nezapomenout v Odoo

- **Pořizovací cena a přecenění se načítají zvlášť:** jinak nesedí rozdělení FX a změny RH ani realizovaný výsledek.
- **Zachovat původní číslo účtu** jako odkaz v převodové tabulce.
- **Klasifikace je po prvním obchodu neměnná,** proto ji zkontrolovat před počátečním dokladem. Počáteční stavy zatím neumíme jako obchod bez peněz, doplnit typ události Převzetí.
- **Výkonnostní odměna:** HWM a referenční hodnota se přenášejí pro každou třídu.
- **EIR:** přenést sazbu, ne ji znovu počítat, jinak se změní naběhlá hodnota.
- **Průměrné FK pro úplaty:** potřeba historie z období před přechodem, doplnit vstup.
- **Předchozí ocenění:** první ocenění nemá v Odoo předchůdce; je potřeba výchozí stav tříd.
- **Výkazy:** srovnávací údaje a mezivýkazové kontroly proti minulým obdobím.

Poslední tři body znamenají vývoj: událost Převzetí, výchozí stav tříd a historii FK. Doporučuji je zařadit do etapy Základ a fond.

## Akceptace ke dni přechodu

| Kontrola | Tolerance |
|---|---|
| Předvaha po převodu účtů | Nula |
| Pozice a kusy proti depozitáři | Nula |
| Otevřené položky a banka | Nula |
| FK a kurz každé třídy | Nula, nebo vysvětlený a schválený rozdíl |
| Závazky z úplat a HWM | Nula |
