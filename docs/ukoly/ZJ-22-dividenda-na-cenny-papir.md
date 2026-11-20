# ZJ-22 Dividenda se zadává na cenný papír (ISIN), fondy se doplní podle držení

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (`investra_nav/models`, účtování), pohledy zelené |
| Výchozí větev | `main` (po sloučení dávky ZJ-07 až ZJ-19) |
| Větev úkolu | `ukol/ZJ-22-dividenda-na-cp` |
| Zadal, dne | Martin, 2026-11-20 |
| Navazuje na | ZJ-19 (dnešní `investra.dividend` na fond a portfolio), AG-024 (ISIN), `ZJ-20-poznamky-zpracovani.md` bod 10 |
| Model | Sonnet 5.5, úsilí high (po schválení plánu dne 2026-11-20 nepotřebuje Opus; účtování dividend zůstává stávající) |

**Cíl:** Dividenda je událost cenného papíru. Uživatel zadá **cenný papír (ISIN)**, ex-datum, datum výplaty, měnu a hrubou dividendu
na kus. Fond se nevybírá. Dole se sama ukáže tabulka držitelů k večeru dne před ex-datem (fond, portfolio a třída, kusy s nárokem,
hrubá dividenda, srážka, čistá dividenda) a součty. Zaúčtování proběhne pro každý fond zvlášť v jeho knize.

## Technický plán (návrh k schválení Martinem)

1. **Hlavička** `investra.dividend.event` (mail.thread, jen jeden na cenný papír a ex-datum): nástroj, ex-datum, datum výplaty, měna,
   hrubá dividenda na kus, druh (česká, zahraniční, z dceřiné), výchozí srážka a smluvní sazba (předvyplní řádky).
2. **Řádky** = dnešní `investra.dividend` (fond, portfolio, kusy, srážka, zápočet, stavy, doklady, storno, náhled), vytvořené akcí
   „Načíst držitele“ z `_holdings` k ex-datum − 1 den přes všechny fondy, které nástroj drží. Zaúčtování, výplata a storno zůstávají
   po řádcích, aby kniha a oprávnění zůstaly na úrovni fondu. Řádek jde upravit (kusy jen snížit, srážka, zápočet).
3. **Oprávnění a knihy:** hlavičku vidí uživatel s právem aspoň na jeden fond; řádky jen fondů, ke kterým má přístup
   (pravidlo společnosti jako u obchodu). Zaúčtování z hlavičky jen řádků dostupných uživateli; ostatní zůstávají v návrhu.
4. **Pohled:** hlavička nahoře (nástroj, ex-datum, výplata, dividenda na kus), pod ní tabulka řádků se součty; tlačítka
   Načíst držitele, Zaúčtovat vše, Zaplaceno; nabídka Portfolio › Dividendy; chytré tlačítko na nástroji beze změny.
5. **Migrace:** existující záznamy dividend (zatím jen testovací) se při povýšení zařadí pod hlavičku podle nástroje a ex-data.
6. **Testy:** dva fondy a dvě třídy drží stejnou akcii, třetí fond nedrží; zaúčtování po fondech; částečné zaúčtování při
   omezených právech; storno jednoho řádku; zahraniční dividenda se zápočtem; snímek 35/39 beze změny.

**Otevřené otázky:** potvrdit, že jedna hlavička = jeden cenný papír a ex-datum (opravy dividendy dalším záznamem); kdo smí
„Zaúčtovat vše“ (zpracovatel, nebo schvalovatel).

**Schválení:** plán schválil Martin zprávou „schvaluji“ dne 2026-11-20. Výchozí rozhodnutí: jedna hlavička = jeden cenný papír a
ex-datum (opravy dalším záznamem); „Zaúčtovat vše“ smí zpracovatel (role s činností, ne nutně schvalovatel).

## Pokyny pro Sonnet

- Přečti CLAUDE.md, `docs/ukoly/ZJ-20-poznamky-zpracovani.md` (jen „Testy“ a „Pořadí práce“) a tento úkol. Plán je schválený, návrhy kódu nejsou spuštěné:
  převezmi je, uprav podle skutečného kódu a odchylky zapiš do Výsledku.
- Commit po bodech plánu. Cílený test změněné třídy po každém bodu a snímek ocenění 35/39 (`tools/snimek_na_kopii.sh`) po dokončení;
  `tools/run_tests.sh all` jen na konci. Pracovní databázi `investra` nepovyšuj (povýšení dělá Claude po všech úkolech).
- Zastav se a napiš JEN když: výsledek existujících ocenění (35, 39, referenční scénáře) se bez nového nastavení změní; něco ze
  zadání v kódu nejde; stejný test dvakrát po opravě neprojde (commitni hotové a popiš).
- Na konci napiš krátce: commity, odchylky, testy, snímek, seznam polí a akcí pro Copilota (pohledy), předávku ulož do `docs/predavky/`.

## Výsledek

Doplní Claude po schválení plánu.

## Převzetí

Doplní Claude.
