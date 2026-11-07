# Harmonogram a akceptace (návrh)

Stav 2026-11-07. Plán je sestavený zpětně od cíle: start a převzetí prvních fondů ke konci Q1 2027.
Termíny jsou návrh a platí až po potvrzení. Hlavní neznámé: kapacita vývoje, připravenost IS, edice Odoo a hosting.

## Rozdělení práce

| Oblast | Kdo |
|---|---|
| Česká lokalizace | Jan Polan |
| Fondové moduly, ocenění, výkazy | Martin Zíma s Claude |
| Nezávislá kontrola fondového kódu | Určit druhou osobu; navrženo Jan Polan |

## Etapy

| Období | Etapa | Výstup | Brána |
|---|---|---|---|
| do 20. 11. 2026 | Rozhodnutí | Edice, hosting nebo jeho kritéria, rozsah práce Jana Polana, firemní repozitář, zadání prototypu | Můžeme začít |
| 16. 11. – 18. 12. 2026 | Prototyp NAV | Jeden fond, více tříd, CZK a EUR, celý cyklus včetně zámku, zaúčtování a storna | **18. 12.: pokračovat, změnit rozsah, nebo změnit plán** |
| 16. 11. 2026 – 29. 1. 2027 | Investra Services | Česká lokalizace, osnova, DPH, banka se schválením účetní, šablona společnosti | Zkušební uzávěrka měsíce |
| 4. 1. – 12. 2. 2027 | Základ a fond | Knihy, role účtů, účtování, kurzy, FX, fondy, třídy, nástroje, ceny, pozice, IFRS 9 podle prvních fondů | **12. 2.: připraveno pro zkušební provoz** |
| 18. 1. – 26. 2. 2027 | IS a provoz | Napojení IS, Dashboard, produkce, zálohy, test obnovy, Pravidla archivace, mapa DORA | Test obnovy prošel |
| 15. 2. – 19. 3. 2027 | Zkušební provoz | Přenos prvního fondu, dvě po sobě jdoucí ocenění vedle stávajícího postupu, zkušební výkazy ČNB, manuál | **19. 3.: přechod** |
| konec Q1 2027 | Převzetí | První fond v ostrém provozu; další fondy postupně | Přechod schválen |

## Povinný rozsah a co může počkat

**Nutné pro první fond:** knihy a role účtů, účtování, kurzy a FX, třídy a alokace, nástroje a ceny, ocenění se schválením, IFRS 9 modely prvních fondů, banka, napojení IS, práva, zálohy, Dashboard v základní podobě.

**Může přijít po převzetí:** výroční zprávy, automatické limity, roční výkazy, další modely IFRS 9, které první fondy nepoužívají, AI nad rámec vývoje a faktur. První měsíční výkazy ČNB musí být hotové před svou lhůtou.

## Akceptace prototypu

1. NAV a kurz každé třídy se shodují s nezávislým výpočtem, včetně příkladu performance fee 99,5 / 109,5 a třídy v EUR.
2. Stejné vstupy dávají stejný výsledek a opakovaný výpočet nic nezdvojí.
3. Kontrolní rovnice platí: součet tříd se rovná FK, pozice se rovnají hlavní knize.
4. Bez schválení nejde návrh zaúčtovat ani změnit. Zadavatel si nemůže schválit vlastní ocenění.
5. Vrácení před zaúčtováním vytvoří novou verzi bez storen; vrácení depozitářem stornuje všechny doklady a zaúčtuje novou verzi.
6. Každé číslo jde dohledat k ceně, kurzu, parametru a schvalovateli.

## Akceptace přechodu fondu

1. Předvaha, otevřené položky, pozice a kusy se ke dni přechodu shodují se zdrojem.
2. Ve dvou po sobě jdoucích oceněních souhlasí NAV a kurz třídy; každý rozdíl je vysvětlený a schválený.
3. Zkušební výkazy ČNB projdou závažnými kontrolami bez ruční úpravy; ruční zásah má zdůvodnění.
4. Test obnovy splnil limity podle DORA a vnitřních předpisů.
5. Role, čtyři oči, MFA a neměnnost jsou ověřené na produkčním nastavení.
6. Obě účetní zvládnou ocenění podle manuálu, včetně zastoupení.
7. Balíček pro audit a depozitáře je kompletní.
8. Přechod schválí odpovědná osoba, zápis se založí k fondu.
