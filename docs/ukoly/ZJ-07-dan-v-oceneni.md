# ZJ-07 Očekávaná daň v ocenění: daňový profil fondu (návrh)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (`investra_nav/models`, výpočet daně); nejdřív jen návrh, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Opus 5.5 |

**Kontext:** dnešní výpočet (`investra_nav/models/valuation.py`, `_apply_tax`) bere výsledek od začátku roku (výnosy minus náklady bez daně) × sazba verze
a účtuje doplatek do požadovaného zůstatku. Chybí neuznatelné náklady, osvobozené a nezdanitelné výnosy, položky se samostatným základem a jinou
sazbou, ztráta z minulých let, ruční úpravy základu a odložená daň.

**Rozhodnuto 17. 11. 2026 (Martin):** varianta B – **daňový profil fondu**. Obecně platí základní sazba fondu a všechny náklady a výnosy jsou daňové;
zadávají se jen výjimky (účet → režim: neuznatelný náklad, osvobozený nebo nezdanitelný výnos, samostatný základ se sazbou).

**Návrh má obsahovat** (varianty a doporučení, bez kódu):
1. Model profilu a výjimek po účtech, platnost od data, vazba na knihu fondu.
2. Ruční úpravy základu v ocenění (připočitatelné a odčitatelné položky s poznámkou a přílohou, vzor ručně doložené úplaty).
3. Ztráta z minulých let k odečtení.
4. Zobrazení výpočtu daně v ocenění a v náhledu zaúčtování.
5. Právní rámec ověřený ve Sbírce zákonů s přesnými odkazy: zákon č. 586/1992 Sb. (sazba základního investičního fondu a ostatních fondů,
   samostatný základ daně, osvobození, neuznatelné náklady, ztráta); daňový režim změn reálné hodnoty u fondu; účetní rámec fondu pro odloženou daň.
   Co nejde ověřit, označit; nejasný výklad navrhnout k ověření u daňového poradce nebo auditora.

**Otevřené otázky pro Martina:** které fondy budou základní investiční fondy (sazba); odložená daň teď, nebo jako otevřený bod.

**Doplněno 17. 11. 2026 (průchod UI ZJ-06):**
- Pravidlo druhu Očekávaná daň nemá nákladovou roli; doplnit při řešení daní.
- Základ časově rozlišené úplaty „po dani“ (třetí volba Základ před/po, nad rámec ZJ-06, jen administrace a obdobné úplaty): dává smysl, pokud statut bere za základ
  hodnotu fondového kapitálu po naběhlé dani. Vzniká kruh (daň závisí na výsledku po úplatách, úplata na dani); řešení ustálením nebo doúčtováním jako u výkonnostní odměny
  s `perf_base` „Po dani“. Zásah do `engine.py` a pořadí kroků (červená zóna, Opus). Rozhodnout až po návrhu daně a podle statutů konkrétních fondů; zatím nic neměnit.

## Výsledek

## Převzetí
