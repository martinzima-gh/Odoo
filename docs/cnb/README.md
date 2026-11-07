# Katalog výkazů a kontrol ČNB (rámec Fondy)

Veřejná data z portálu SDAT (https://sdat.cnb.cz/sdat_ext/), metodika **FOFI20261201**, staženo 6. 11. 2026.
Zdrojem pravdy jsou CSV (oddělovač `;`, UTF-8 s BOM, otevřou se i v Excelu). XLSX se z nich generuje ke čtení.
Nová metodika = nové soubory se jménem podle metodiky; rozdíl proti minulé verzi ukáže git.

## Soubory

| Soubor | Obsah | Počet |
|---|---|---|
| `vykazy-*.csv` | Výkazy: akronym, název, verze, platnost, listy, počty kontrol, odkaz do SDAT | 22 |
| `kontroly-*.csv` | Kontroly: kód, název, závažnost, platnost, sémantický a uživatelský tvar, vzorec s názvy položek, chybové hlášení | 705 (633 JVK, 72 MVK) |
| `polozky-*.csv` | Struktura výkazů: list, řádek, sloupec, klíč, název, datový typ nebo číselník, ukazatel | 1 479 (103 listů) |
| `ciselniky-*.csv` | Hodnoty 25 použitých domén a souhrnné položky `S_…` z hierarchií | 1 436 |
| `domeny-*.csv` | Přehled použitých domén | 25 |
| `parametry-*.csv` | Parametry použité ve vzorcích a strukturách (`P0019` apod.) | 50 |
| `ukazatele-*.csv` | Ukazatele použité ve vzorcích (`EAR2592`, `AFO0031` apod.) | 390 |
| `kontroly-*.xlsx` | Vše výše v jednom sešitu, s filtry a listem kontrol pro každý výkaz | |

## Jak číst vzorce

- **Sémantický tvar:** `WITH(P0019=S_VSEMEN, …) [AFO0031] = [AFO0037] + … MARGIN 4000;` Pracuje s ukazateli a parametry.
- **Uživatelský tvar:** `ROFO10_11[1,1] = ROFO10_11[5,1] + …` Tedy `list[řádek,sloupec]`.
- **Vzorec s názvy:** uživatelský tvar doplněný názvy, např. `«ROFO10_11[1,1] Aktiva celkem ∑»`.
- **`MARGIN`** je povolená tolerance.
- **Závažnost:** Závažná = výkaz neprojde, Varování = upozornění, Potvrzení = nutné vysvětlení.
- **`vykazy`** u MVK uvádí všechny výkazy, kterých se kontrola týká.

## Známá omezení

- Ukazatel u položky (`ukazatele_z_kontrol`) je odvozený ze vzorců kontrol, takže je jen u 353 z 929 řádků.
  U položek bez kontroly je potřeba „Definice buňky“ v SDAT. Před exportem z Odoo doplnit.
- Číselníky obsahují jen domény a souhrnné položky použité ve výkazech Fondů, ne celou Knihovnu (1 812 domén).
  Hierarchie jsou uložené ploše: u souhrnné položky je název a kód hierarchie, ne seznam podřízených položek.
- Bez názvu zůstaly tři souhrnné položky: `S_DISINFO`, `S_OBEUAVY`, `S_VSE`.
- Odkazy na dynamické řádky (`ROFO35_01`, `ROFO37_01`, `DOFO70_02`) nemají název řádku, jen sloupce.
- Podmínky `#RESTRICT(@Z_…)` (na které typy fondů se kontrola vztahuje) jsou jen v textu vzorce.
- Převodníky z Knihovny SDAT nejsou součástí katalogu.

## Obnova při nové metodice

SDAT je aplikace ZK, seznamy se načítají až v prohlížeči. Postup:

1. V prohlížeči projít výkazy rámce Fondy a ze seznamů kontrol zjistit ID (záložky „Kontroly JVK a KČŘ“ a „Kontroly MVK“).
2. Detaily kontrol, domén a hierarchií stáhnout přímo (stránky `F2123-kontrola-detail.zul`,
   `F1015-detail-verze-domeny-ciselniku.zul`, `F1014-detail-verze-hierarchie-ciselniku.zul`).
3. Strukturu vyčíst z listů na záložce „Prezentační struktura“.
4. Porovnat počty proti `vykazy-*.csv` a v gitu zkontrolovat rozdíly.
