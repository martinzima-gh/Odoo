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
2. ~~Ruční úpravy základu v ocenění~~ – **přesunuto do ZJ-12** (rozhodnutí 2026-11-18): oprava základu daně je řádek opravy u pravidla daně
   s volbou „Co opravuje: Základ“ (kladná = připočitatelná, záporná = odčitatelná, poznámka povinná, příloha nepovinná, platí do konce roku). ZJ-07 zůstává profil, výjimky po účtech, ztráta a odložená daň.
3. Ztráta z minulých let k odečtení (návrh ZJ-12: údaj daňového profilu na rok; rozhodne se v ZJ-07).
4. Zobrazení výpočtu daně v ocenění a v náhledu zaúčtování.
5. Právní rámec ověřený ve Sbírce zákonů s přesnými odkazy: zákon č. 586/1992 Sb. (sazba základního investičního fondu a ostatních fondů,
   samostatný základ daně, osvobození, neuznatelné náklady, ztráta); daňový režim změn reálné hodnoty u fondu; účetní rámec fondu pro odloženou daň.
   Co nejde ověřit, označit; nejasný výklad navrhnout k ověření u daňového poradce nebo auditora.

**Otevřené otázky pro Martina:** které fondy budou základní investiční fondy (sazba); odložená daň teď, nebo jako otevřený bod.

**Doplněno 17. 11. 2026 (průchod UI ZJ-06):**
- Pravidlo druhu Očekávaná daň nemá nákladovou roli; doplnit při řešení daní.
- ~~Základ časově rozlišené úplaty „po dani“ a cyklus odměny po dani~~ – **vyřešeno rozhodnutími 2026-11-18** (ZJ-12): základ „po kroku 1–4“ a společný dopočet
  s kontrolou konzistence; kruh úplata–daň i odměna–daň se řeší ustálením, ne zvláštními doúčtováními.

## Technický plán

Schváleno Martinem 19. 11. 2026 včetně odchylek C0.1–C0.8: `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 9 (9.1 zadání a referenční příklady, 9.2 technický plán,
9.3 postup a kód) a **Právní rámec** z oddílu 1 (D1–D14). Obsah se sem nekopíruje. DA-01 se do tohoto úkolu slučuje (D1).

- Provedení: běh 4 (účty a daňové modely, Sonnet 5.5) a běh 5 (výpočet daně a migrace, Opus 5.5), viz
  `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md`; zobrazení a manuál běh 6 (Copilot).
- Otázky pro daňového poradce a metodika jsou v `docs/otevrene-body.md` (dávka ZJ-07 až ZJ-19).
- Odchylky od plánu se zapisují do Výsledku.

## Výsledek

## Převzetí
