# Výkazy ČNB po položkách

Stav 2026-11-07. Výpočet z `docs/cnb/mapovani-FOFI20261201.csv`, stav prototypu je odhad na úrovni listů. Výčet výkazů pro FKI vychází z vyhlášek v `docs/cnb/lhuty.md`.

**Závěr:** FKI s podlimitním správcem se týká 12 výkazů, 45 listů a 760 položek. Hotové jsou 4 položky, 338 má část dat a 418 chybí. Největší díl nevyžaduje nové výpočty, ale registry a atributy protistran a nástrojů.

| Výkaz | Základ | Část dat | Chybí |
|---|---|---|---|
| ROFOS10 Rozvaha | 2 | 104 | 121 |
| RISIFI30 Bilance | 0 | 107 | 33 |
| VYFOS20 Výsledovka | 2 | 59 | 62 |
| ROFOS37 Podlimitní správce, fond | 0 | 11 | 112 |
| DOFOS70 Klíčové informace | 0 | 0 | 50 |
| ROFOS13 Hlášení FKI | 0 | 32 | 12 |
| RISIFI33 Cenné papíry | 0 | 19 | 6 |
| KLISIFI10 Klasifikace | 0 | 0 | 12 |
| VISIFI10 Příjmy | 0 | 3 | 4 |
| TISIFI10 Změny v ocenění | 0 | 4 | 0 |
| RISIFI37 Vydané a odkoupené | 0 | 3 | 0 |
| VISIFI20 Úplaty | 2 | 0 | 0 |

## Co chybí podle povahy dat

| Mezera | Položek | Řešení v modelu |
|---|---|---|
| SICAV bez podfondu, sloupce a sestavy | 142 | Pole část fondu je, doplnit sestavy; jen pokud forma fondu existuje |
| Výnosy a náklady podle role a druhu nástroje | 59 | Mapování z hlavní knihy |
| Země emitenta nebo protistrany | 68 | Registr protistran: země, sektor ESA, LEI |
| Registr úvěrů | 33 | Viz `05-dluhove-nastroje.md` |
| Rozvaha podle rolí a rámce, řádky podle rolí | 63 | Převodová tabulka role na řádek s platností |
| Kategorie IFRS 9 a úroveň RH | 30 | Na nástroji jsou, doplnit sestavu |
| Deriváty | 29 | Odloženo |
| Výkonnost a náklady | 17 | Historie kurzů a rozpis úplat |
| Nástroje bez ISIN, účasti | 14 | Ostatní podíly a účasti |
| Klasifikace fondu, klíčové informace | 23 | Registr fondů, ruční údaje |
| Zatížení aktiv | 10 | Registr zatížení |

Asi 228 položek nemá v mapování poznámku, hlavně textové a správcovské údaje v ROFOS37 a DOFOS70; ty je potřeba projít ručně.

## Doporučené pořadí

1. **Registr protistran:** nejvíc položek jedním krokem a využijí ho i úvěry a deriváty.
2. **Převodová tabulka role na řádek výkazu:** odemkne ROFOS10, VYFOS20 a RISIFI30.
3. **Měsíční výkazy RISIFI30, RISIFI33, TISIFI10, VISIFI10, RISIFI37:** první lhůta přijde hned po převzetí fondu.
4. **Registr fondů:** KLISIFI10, DOFOS70, ROFOS13.
5. **ROFOS37:** projít položky a určit zdroj.

První měsíční výkazy musí být hotové před svou lhůtou, proto tento rozsah patří do etapy Základ a fond. V harmonogramu na něj zatím není samostatná položka.
