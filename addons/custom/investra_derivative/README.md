# investra_derivative – FX spot, forward a swap

Evidence, účtování a ocenění měnových derivátů fondu (vyhláška č. 501/2002 Sb.). Návrh a čísla příkladu:
`docs/navrh-fx-derivaty.md`; zadání a rozhodnutí: `docs/ukoly/DE-02` až `DE-05`, deník rozhodnutí 2026-11-15 a 2026-11-16.
Rozsah: mimoburzovní, vypořádání dodáním obou měn; jedna z měn nohy je funkční měna fondu. Mimo: zajišťovací
účetnictví, diskontování, NDF, opce, předčasné ukončení.

## Postup v aplikaci (Portfolio → Deriváty)

1. **Sjednat:** nová smlouva (fond, protistrana, druh, datum sjednání, číslo smlouvy, nohy: datum vypořádání, kupovaná
   a prodávaná měna s částkami). Forward má jednu nohu, swap dvě opačné. Tlačítko **Sjednat** zapíše podrozvahu
   (rozvaha ani FK se nemění); před zaúčtováním je náhled dokladů.
2. **Ocenit:** v ocenění fondu se při Spočítat přidá řádek za každou smlouvu s otevřenou nohou: spočtená RH (varianta B),
   případná ruční hodnota, rozdíl a změna do výsledku; ocenění zaúčtuje změnu RH a přepočet podrozvahy. Kurzy bere ze
   zdroje kurzů ocenění fondu; chybí-li kurz, je to chyba kontroly.
3. **Ruční hodnota (potvrzení banky):** na smlouvě záložka Ruční hodnoty: datum ocenění, částka a měna, zdroj,
   příloha nebo důvod. Má přednost před spočtenou hodnotou jen pro své datum; rozdíl nad tolerancí fondu
   (pole „Tolerance ruční hodnoty derivátu“ na fondu, návrh 0,10 % nominálu) je upozornění, bez přílohy a důvodu je to chyba.
   Zadat ji je nutné **před** Spočítat; ruční hodnotu už použitou v ocenění nejde změnit.
4. **Vypořádat nohu:** tlačítko na noze, výběr bankovních účtů, náhled; vzniknou dva doklady (peněžní toky a RH,
   odúčtování podrozvahy nohy). Po vypořádání všech noh je smlouva Vypořádaná.
5. **Storno:** vypořádání poslední nohy nebo celé smlouvy s důvodem; stornují se doklady k jejich datům.

Nahlížení bez zápisu: `docs/sql/25-derivaty.sql` (smlouvy, nohy, RH po oceněních, podrozvaha, kontrola MD = D a FK).
Testy: `tools/run_tests.sh investra_derivative`. Ukázka: swap fondu A v `tools/demo_data/seed.py`.
