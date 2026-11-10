# Návrh: ochrana kurzů v účetnictví

Plán ke schválení, červená zóna (`investra_rates`). Stav 10. 11. 2026, připravil Claude na pokyn uživatele.
Nic z toho není naprogramované.

**Doporučení:** varianta C. Kurz, který vyhlásila ČNB nebo ECB, půjde v účetnictví změnit jen stažením
z vyhlášeného zdroje. Ruční kurz zůstane možný jen pro měnu a den, pro které vyhlášený kurz neexistuje,
a zadá ho jen účetní manažer. Rozdíl mezi oběma evidencemi se při stahování nahlásí a nepřeskočí se.

## Jak to funguje dnes

- `investra.rate` je evidence kurzů tak, jak je zdroj vyhlásil: kurz, množství, datum a otisk staženého souboru.
  Záznam nejde změnit ani smazat. Z něj počítá ocenění (`get_rate`).
- Po stažení `_publish` zapíše kurz do `res.currency.rate`, odkud ho berou doklady Odoo:
  ČNB jako společný kurz pro všechny knihy, ECB jako kurz společnosti jen do knih se zdrojem ECB.
- Odoo 20 hledá kurz dokladu přednostně mezi kurzy společnosti, teprve potom mezi společnými.

## Zjištěná rizika

| # | Riziko | Dopad | Jak zjištěno |
|---|---|---|---|
| 1 | Kurz v `res.currency.rate` jde ručně změnit nebo smazat (nastavení měn v Účetnictví) | doklad použije jiný kurz, než jaký počítá ocenění; rozdíl se projeví jako nevysvětlený rozdíl mezi NAV a hlavní knihou | čtení kódu; obrazovku v Odoo 20 ověřit na instanci |
| 2 | `_publish_value` kurz nezapíše, když už k danému dni existuje, a neohlásí to | ručně nebo dřív zadaný kurz tiše vyhraje nad vyhlášeným | čtení kódu (`investra_rates/models/rate.py`) |
| 3 | Kurz zadaný ručně jako kurz společnosti v knize se zdrojem ČNB má přednost před společným kurzem ČNB | stejné jako 1, jen hůř vidět | pořadí hledání kurzu v Odoo; ověřit testem |
| 4 | Kniha se zdrojem ECB a měna, kterou ECB nevyhlašuje (např. XDR): Odoo vezme společný kurz ČNB se základem CZK a smíchá ho se základem EUR | chybný přepočet bez varování | úvaha nad kódem; ověřit testem |
| 5 | Plánovaná úloha stahování je po instalaci vypnutá (`data/cron.xml`, `active` = False, `noupdate`) | bez ručního zapnutí se kurzy nestahují a ocenění skončí chybou „chybí kurz“ | čtení kódu; stav v `investra_dev` ověřit dotazem SELECT |

## Varianty

| Varianta | Co dělá | Pro | Proti |
|---|---|---|---|
| A. Úplný zámek | `res.currency.rate` zapisuje jen stahování kurzů; ruční zápis odmítne každému | nejjednodušší, nejpřísnější | nejde zadat kurz měny, kterou ČNB denně nevyhlašuje (ČNB vede měsíční kurzy ostatních měn); blokuje i jiné moduly a import |
| B. Jen kontrola | nic nezakazuje; denní kontrola a kontrola v ocenění vypíšou rozdíly | žádné omezení práce | chyba se zjistí až po zaúčtování; oprava znamená storno a nové doklady |
| **C. Zámek vyhlášených kurzů + ruční výjimka** | kurz, ke kterému existuje záznam v `investra.rate`, mění jen stahování; ostatní kurzy smí zadat účetní manažer; stahování hlásí rozdíly | chrání to, co počítá ocenění, a nechává cestu pro výjimky | víc pravidel a testů než A |

## Návrh řešení (varianta C)

Vše v modulu `investra_rates`, bez zásahu do jádra Odoo (dědičnost modelu `res.currency.rate`).

1. **Zámek.** Nová třída v `models/currency.py` dědí `res.currency.rate` a přepisuje `create`, `write` a `unlink`:
   - Zápis ze stahování nese příznak v kontextu a projde.
   - Ruční zápis ke dni a měně, pro které existuje `investra.rate` odpovídajícího zdroje, se odmítne hláškou
     „Kurz vyhlášený ČNB/ECB nejde ručně měnit; oprava jen opravou zdroje.“ Odpovídající zdroj je ČNB pro společné
     kurzy a pro knihy se zdrojem ČNB, ECB pro knihy se zdrojem ECB.
   - Kurz společnosti v knize se zdrojem ČNB pro měnu, kterou ČNB vyhlašuje, se odmítne (riziko 3).
   - Ostatní ruční kurzy smí zadat jen `account.group_account_manager`. Kdo a kdy, ukazují standardní údaje
     o vytvoření a změně záznamu.
2. **Žádné tiché přeskočení.** `_publish_value` při existujícím kurzu s jinou hodnotou (rozdíl nad 1e-9)
   zapíše chybu do logu a vrátí ji. Stahování skončí hlášením se seznamem rozdílů. Existující kurz se automaticky
   nepřepisuje, protože podle něj už mohou být zaúčtované doklady.
3. **Kniha se zdrojem ECB (riziko 4).** Nejdřív test, který chování potvrdí nebo vyvrátí. Potvrdí-li se, `_publish`
   do knih ECB zapíše i měny, které ECB nevyhlašuje, nebo přepočet takové měny skončí chybou. Výběr řešení
   přijde zvlášť ke schválení podle výsledku testu.
4. **Plánovaná úloha (riziko 5).** Zůstane vypnutá v datech modulu (instalace do testovací databáze nemá stahovat).
   Zapnutí v `investra_dev` a později v produkci bude krok nasazení se souhlasem uživatele.

**Testy** (nové, v `investra_rates/tests/`):
ruční změna a smazání vyhlášeného kurzu se odmítne; stahování kurz zapíše; ruční kurz měny bez vyhlášeného kurzu
zadá účetní manažer, běžný účetní ne; kurz společnosti v knize ČNB se odmítne; stahování nad existujícím odlišným
kurzem ohlásí rozdíl a kurz nezmění; kniha ECB a měna mimo ECB (riziko 4).
Zámek platí pro zápis uživatele, ne pro kód běžící jako superuživatel (`env.su`), stejně jako u ostatních
ochran v projektu. Existující testy v `test_rate.py`, které kurzy na začátku mažou, se proto nemění.

## Dopad na data a účetnictví

- Existující doklady ani kurzy se nemění.
- Před nasazením Claude ověří dotazem SELECT v `investra_dev`, zda už v `res.currency.rate` není kurz odlišný
  od `investra.rate`. Nalezené rozdíly předloží uživateli; opravují se jen přes Odoo, nikdy příkazem nad databází.
- Nasazení znamená aktualizaci modulu `investra_rates`, ke které Claude požádá o souhlas.

## Otázky pro uživatele

1. Je potřeba zadávat kurzy měn, které ČNB vyhlašuje jen měsíčně (kurzy ostatních měn)? Pokud ano, navrhuji
   doplnit jejich stahování jako další zdroj místo ručního zadání.
2. Stačí pro ruční kurz role účetního manažera, nebo má jít přes čtyři oči jako ruční úpravy v ocenění
   (revize, matice schvalování)?
3. Má se rozdíl kurzů zobrazit i jako kontrola v kroku ocenění? To je změna `investra_nav` a samostatný krok.

## Zóna a provedení

Červená zóna: provede Claude po schválení uživatelem, ne Antigravity. Odhad: jeden model, šest až osm testů,
bez nových polí a bez migrace.
