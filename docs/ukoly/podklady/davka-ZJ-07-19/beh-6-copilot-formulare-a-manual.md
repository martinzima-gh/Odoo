# Běh 6 – Copilot (agent mode, libovolný model; alternativa Antigravity): formuláře, nabídky, manuál

Zóna zelená. Copilot nezná CLAUDE.md – vše potřebné je níže. Vlož celé jako jednu zprávu v ~/odoo-dev.

```
Úkol CP-2026-11-xx-ZJ-07-19-formulare. Z větve ukol/ZJ-07-dane-a-tridy založ větev cp/ZJ-07-19-formulare.
Přečti docs/predavky/*-davka-beh-1.md až beh-5.md (oddíl „pro Copilota“: nová pole, modely, akce) a docs/ukoly/podklady/
zadani-davka-ZJ-07-az-19.md jen pasáže o zobrazení: 2.1 A4, 2.2 A3–A5, 3 D4 a D6, 4 F3 a F4, 5 E5, 6.1 B5, 7 (formulář a nabídka
Dividendy, lhůta na nástroji), 8 G2 sloupec OCI, 9.2 C4 a 9.3 C6, oddíl 10.
SMÍŠ měnit jen: addons/custom/*/views/*.xml, __manifest__.py (jen seznam "data" kvůli novým XML), docs/manual/*.md, docs/sql/*.sql.
NESMÍŠ: Python, nová pole, oprávnění, data, migrace. Když pole, které potřebuješ, neexistuje, nevymýšlej ho – zapiš do „Otevřené“.
Udělej:
1. Portfolio: pole Třída pod Fondem s nápovědou „Prázdné = sdílené všemi třídami“. Obchod: pod Portfoliem jen pro čtení text třídy
   portfolia / „Sdílené portfolio“. Náhled zaúčtování: sloupec Třída.
2. Třída fondu: přepínač „Podílí se na společných položkách“; pravidlo úplaty: žlutý pruh s upozorněním (pole z běhu 1, invisible když prázdné).
3. Fond, záložka Obecné: „Konec účetního období“ (jen čtení). Všechny popisky „od 1. 1.“ v XML → „od začátku účetního období“.
4. Obchod: skupina Poplatek (částka, měna, kurz – kurz jen u cizí měny poplatku), text „Účtování poplatku“; seznam obchodů volitelný
   sloupec Poplatek. Prodej: řádek „Odúčtování: průměrná X, použitá Y“, důvod jen při odchylce (invisible podle polí z běhu 2).
5. Dividendy: seznam, formulář (hlavička se stavy a tlačítky akcí z běhu 3, skupiny Nárok, Srážka a zápočet, Výplata, Zaúčtování),
   hledání, nabídka Portfolio › Dividendy, chytré tlačítko na nástroji. Nástroj: „Ex-kupónová lhůta (dny)“ u dluhopisů; tok: Ex-datum.
6. List portfolio v ocenění: sloupec „Oceňovací rozdíl (OCI)“ (volitelný).
7. Daně: Nastavení › Daně › Daňová pravidla – seznam a formulář pravidla (druh, způsob, účty, verze sazeb v řádcích, poznámka, chatter);
   fond záložka „Daň“ (výchozí pravidlo + aktuální sazba, Základ: po kroku, tabulka Výjimky: Účet, Daňové pravidlo, Podíl, Neuznatelné
   % z výnosu, Pohyb od začátku období, Poznámka; tlačítko Přidat běžné výjimky); oprava ocenění pole Daňové pravidlo; ocenění: rozpad
   daně (HTML pole z běhu 5) pod řádkem Daň; nosič v Pravidlech úplat jen pro čtení s textem „Daň se nastavuje ve fondu, záložka Daň“.
8. Manuál: nová docs/manual/10-rozdeleni-mezi-tridy.md podle oddílu 10; doplň kapitoly 06 (portfolio třídy, poplatek, cena odúčtování,
   dividendy, ex-kupón, FVOCI a ruční ECL), 02 (účetní období), 09 nebo nová 11-dan.md (daň podle 9.1 F a oddílu 1 D6–D14).
   Česky, krátké věty, názvy polí přesně jako v UI. SQL: sloupce poplatku a dividend do příslušných ukázek docs/sql.
Ověření: modul se musí povýšit bez chyby – spusť tools/run_tests.sh pro investra_instruments, investra_nav, investra_fund (jen kontrola,
že XML projde). Commit po bodech, push větve cp/…; do docs/ukoly/CP-2026-11-xx-ZJ-07-19-formulare.md zapiš Provedení, Ověření, Otevřené.
```
