# ZJ-09 Portfolio a bankovní účet společné, nebo jen pro třídu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování obchodů, ocenění, úroků, derivátů, kurzové přecenění, alokace); nejdřív plán, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-08) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Opus 5.5 |

**Kontext:** obchody, pozice ani smlouvy derivátů dnes třídu nenesou, takže položky jen pro třídu (např. měnové zajištění třídy) se do ΔT nedostanou.
Pole `class_id` na `investra.instrument` je ve formuláři, ale nic ho při účtování nepoužívá. Pozice se už vedou po dvojici nástroj a portfolio
(`investra.trade._holdings`); ocenění, naběhlé úroky i uzavírání pozic pracují po této dvojici; smlouva derivátu má portfolio.

**Rozhodnuto 17. 11. 2026 (Martin), deník „Třída portfolia“:** portfolio fondu má pole **Třída** – prázdné = společné portfolio (dělí se mezi třídy
podílející se na výsledku, viz ZJ-08), vyplněné = portfolio jen této třídy. Stejný nástroj může být ve společném portfoliu i v portfoliu třídy.
Nahrazuje varianty A, A2 a B z otevřeného bodu „Obchody a pozice na třídu“.
Martin potvrdil 17. 11. 2026 a doplnil: **i bankovní účet může být specifický pro třídu** (deník „Bankovní účet třídy“). Bankovní deník fondu má pole Třída
se stejným významem; řádky na jeho účtu nesou třídu. Platba mezi bankou třídy a společným majetkem (nebo portfoliem jiné třídy) jde přes vnitřní zúčtování.

**Plán má obsahovat:**
1. Pole Třída na `investra.fund.portfolio` (doména na třídy fondu), zámek po prvním obchodu (`_has_trades`) a po prvním dokladu derivátu.
2. Doplnění `class_id` na rozvahové řádky: obchod (nákup, prodej, vypořádání), storno a oprava obchodu, ocenění pozic, naběhlý úrok, splátky,
   deriváty (forward, swap, spot, obě nohy, podrozvaha). Peníze přes vnitřní zúčtování (`internal_clearing`); banka bez třídy zůstává společná (bod 2b).
2b. Bankovní účet třídy: pole Třída na bankovním deníku fondu (`account.journal`, typ banka), zámek po prvním pohybu; třída na řádcích bankovního účtu
   z plateb, výpisů a vypořádání obchodů; automatické vnitřní zúčtování, když se třída banky liší od třídy protistrany (společné portfolio, jiná třída);
   úpisy a odkupy třídy z IS (vypořádání na banku třídy i na společnou banku); párování výpisů. Varianty a doporučení, kde vnitřní zúčtování vzniká
   (při zaúčtování dokladu obecně, nebo v každém zdroji zvlášť).
3. Kurzové přecenění (`investra_fx_revaluation`) po třídách, aby se třída na zůstatcích neztratila.
4. Náhled zaúčtování (`investra.posting.preview`) ukazuje třídu na řádcích.
5. Zrušení pole Třída na nástroji (data v `investra` ověřit SELECTem; při zrušení pole Odoo sloupec smaže).
6. Výkazy ČNB a přehledy portfolia: součet přes portfolia beze změny – ověřit.
7. Manuál: portfolio = obchodní model IFRS 9 a zároveň „kapsa“ třídy; třída se dvěma obchodními modely má dvě portfolia.
8. Testy: zajištění třídy B forwardem (přecenění jen do ΔT třídy B), stejný nástroj ve společném portfoliu a v portfoliu třídy,
   storno obchodu v portfoliu třídy, úrok a splátka, kurzové přecenění, nákup do společného portfolia placený z banky třídy, úpis třídy na banku třídy; referenční scénáře beze změny.

## Výsledek

## Převzetí
