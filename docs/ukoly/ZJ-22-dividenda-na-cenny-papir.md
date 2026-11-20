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

Hotovo 2026-11-20 (Sonnet 5.5), commit „ZJ-22“ na větvi `ukol/ZJ-20-poznamky`.

- **Model** `investra.dividend.event` (`models/dividend_event.py`; cenný papír, ISIN, ex-datum, výplata, dividenda na kus, druh, výchozí
  sazby, stav z řádků, součty, chatter). Řádky = dosavadní `investra.dividend` s novým polem `dividend_event_id`; účtování, výplata, storno,
  náhled a doklady zůstaly po řádcích v knize fondu.
- **Akce:** Načíst držitele (z `Trade._holdings` k ex-datu − 1 přes všechny fondy viditelné uživateli, existující řádky nepřepíše),
  Zaúčtovat vše, Zaplaceno (po řádcích, každý v savepointu; chybný řádek nezastaví ostatní, vypíše se). Smí zpracovatel (role přípravy).
- **Jedna událost = cenný papír + ex-datum**, kontrola proti duplicitě platí jen vůči nestornovaným událostem; po stornu všech řádků
  jde zadat opravu novou událostí. Změna ex-data a nástroje po zaúčtování řádku je zakázaná; datum výplaty se přenáší i do zaúčtovaných.
- **Oprávnění:** `ir.access.csv` (čtení účetní, zápis zpracovatel) a pravidlo události podle společnosti řádků; řádky dál podle společnosti.
- **Odchylky od plánu:** (1) Řádek dividendy založený mimo událost (testy, import) si událost při založení najde nebo vytvoří – pole
  zůstává nepovinné, aby se nerozbily stávající cesty. (2) Opravena latentní chyba `_account` v řádku dividendy: kód účtu je závislý na
  společnosti, při práci ve více knihách najednou se hledal ve špatné; teď `with_company`. (3) Menu: Portfolio › Dividendy otevírá
  události, původní seznam řádků je v nabídce Řádky dividend (chytré tlačítko na nástroji beze změny, ukazuje řádky).
- **Migrace** 20.0.0.41.0 (`migrations/20.0.0.41.0/post-migration.py`): řádky bez události se seskupí podle nástroje a ex-data, stornované
  mají vlastní událost. Zkoušena testem na vytvořených řádcích a na kopii pracovní databáze (tam žádné dividendy nejsou).
- **Testy:** `TestDividendEvent` (8) a `TestDividend` bez chyby (dva fondy drží, třetí ne; zaúčtování po fondech; částečné při omezených
  právech; storno jednoho řádku a oprava; zahraniční se zápočtem; propagace a zámek hlavičky; migrace). Snímek 35/39 shodný.
- **Pro Copilota (pohledy):** formulář a seznam události (`dividend_views.xml`: `view_dividend_event_*`), vložená tabulka držitelů
  (fond, portfolio, třída, kusy, hrubá, srážka, čistá, stav), tlačítka Načíst držitele / Zaúčtovat vše / Zaplaceno, nabídky Dividendy a
  Řádky dividend, text pod tabulkou.

## Převzetí

Doplní Claude.
