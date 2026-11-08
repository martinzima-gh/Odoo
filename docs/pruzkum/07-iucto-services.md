# iÚčto pro Investra Services: porovnání s Odoo

Stav 2026-11-08. Podklad, ne rozhodnutí. Údaje o iÚčtu jsou z jeho veřejného webu; aplikaci jsme nezkoušeli.
Údaje o Odoo jsou z naší kontroly Odoo 20 Community (`docs/ceska-lokalizace.md`) a průzkumu edice (`01-edice-hosting.md`).

## Závěr

- **Pro Investra Services je iÚčto vážná varianta.** Většinu funkcí, které Community chybí (rozvaha, výsledovka, banka, podání DPH), má hotovou za stovky korun měsíčně.
- **Pro fondy ne.** Web neuvádí vyhlášku 501, IFRS, finanční instituce ani fondy; NAV, nástroje a výkazy ČNB nemá.
- **Volba je tedy mezi „vše v Odoo“ a hybridem** (Services v iÚčtu, investiční společnost a fondy v Odoo). Hybrid mění rozhodnutí „Odoo je jediný účetní systém od začátku“ z 2026-11-04.
- Před rozhodnutím ověřit body v části „Ověřit u iÚčta“, hlavně bezpečnost, uzamčení období a přecenění.

## Porovnání pro Services

Odoo Community = co je v naší instalaci. Odoo Enterprise = podle popisů, nezkoušeno.

| Oblast | iÚčto (web) | Odoo 20 Community | Odoo Enterprise |
|---|---|---|---|
| Podvojné účetnictví s.r.o. | Ano | Ano | Ano |
| Rozvaha a výsledovka | Ano, od tarifu Sólo; podle které vyhlášky a v jakém rozsahu neuvádí | Ne, vlastní sestavy | Ano, česká podoba přes partnera |
| Příloha a uzávěrka | Účetní závěrku zmiňuje, podrobnosti ne | Zámky ano, výkazy ne | Částečně |
| DPH přiznání, KH, SH | Přehledy ve všech tarifech, export pro EPO od tarifu Firma | Řádky přiznání v datech, zobrazení ani EPO ne | Přes českého partnera |
| Neplátce | Ano, hlídá limit obratu | Ano | Ano |
| Banka | Automatické načítání a párování, online napojení na ČS, Fio, KB, Moneta, RB od tarifu Firma | Import výpisů ani párování v menu nejsou | Ano |
| Cizí měny, kurzy ČNB | Doplňkový modul | Ano, náš `investra_rates` | Ano |
| Přecenění k rozvahovému dni | Neuvádí | Ano, náš modul přecenění | Ano |
| Střediska, zakázky | Doplňkový modul | Analytika | Analytika |
| Majetek a odpisy | Neuvádí | Ne | Ano |
| Mzdy | Neuvádí (mzdy vede externí dodavatel, potřebujeme jen import zápisu) | Import zápisu doplnit | Import zápisu doplnit |
| Schvalování přijatých faktur | Neuvádí | Ne | Ano |
| Uzamčení období, historie změn | Historie změn ano; uzamčení neuvádí | Ano, zámky a hash | Ano |
| Uživatelé a práva | Omezená práva ve všech tarifech; současné přístupy: Firma 3, Max neomezeně | Ano | Ano |
| API | REST, čtení i zápis, účetní deník, webhooky, MCP server; bez sandboxu, klíč má plný přístup k firmě | Plný přístup k datům i SQL | Plný přístup |
| Více firem | Tarif je na 1 firmu; spolupráce s účetní kanceláří existuje, cenu neuvádí | Ano | Ano, licence za uživatele |
| Cena | Firma 496 Kč/měs. ročně, Max 595 Kč/měs. ročně; podle výpočtu bez DPH | 0 Kč licence, vlastní vývoj chybějících funkcí | 22,90 až 27,90 € za uživatele a měsíc ročně, plus český partner |
| Provozovatel | Direct Accounting s.r.o., IČ 28499638, Praha | Vlastní provoz | Vlastní provoz nebo Odoo |
| Hosting, certifikace, export dat při odchodu | Neuvádí (nápověda nešla načíst); VOP: uchování dokladů nejméně 5 let, zpracovatelská smlouva podle čl. 28 GDPR | Vlastní | Podle hostingu |

## Co by hybrid znamenal

- **Úplaty Services fondům:** Services fakturuje, fondy v Odoo účtují náklad. Vydanou fakturu přenést do Odoo ručně, nebo přes API iÚčta.
- **Dvě sady znalostí a dva systémy** pro jedny účetní. U Services ale odpadá vlastní vývoj české lokalizace, který je dnes největší položkou.
- **Investiční společnost** (vyhláška 501, výkazy ČNB) by šla do Odoo stejně jako fondy. Odoo by tedy českou lokalizaci podnikatele nepotřebovalo vůbec, ale potřebovalo by svoji pro finanční instituce.
- **DORA:** pro investiční společnost je Services poskytovatel služeb. Pokud Services přes iÚčto zpracovává data pro investiční společnost, je iÚčto další ICT dodavatel v řetězci. Posoudit při mapě DORA.
- **Přechod později:** z iÚčta do Odoo jde převést počáteční stavy k začátku roku; formát exportu ověřit.

## Ověřit u iÚčta

1. Rozvaha a výsledovka podle vyhlášky 500 v plném a zkráceném rozsahu, příloha, uzávěrka a rozdělení výsledku.
2. Uzamčení období a co přesně zaznamenává historie změn.
3. Přecenění cizích měn k rozvahovému dni a kurzové rozdíly.
4. Hosting (země, poskytovatel), zálohy, certifikace, dvoufázové přihlášení.
5. Úplný export dat při odchodu a jeho formát.
6. Import mzdového zápisu od externího dodavatele.
7. Cena pro více firem a přístup externí účetní.
8. Zkušební firma: ověřit na smyšlených datech, ne na Investra Services.

## Zdroje

- [iÚčto: úvod](https://www.iucto.cz/), [funkce](https://www.iucto.cz/funkce/), [účetnictví](https://www.iucto.cz/funkce/ucetnictvi/), [ceník](https://www.iucto.cz/cenik/), [API](https://www.iucto.cz/api/), [obchodní podmínky](https://www.iucto.cz/obchodni-podminky/), čteno 2026-11-08
- Nečteno: [nápověda](https://napoveda.iucto.cz/) (chyba certifikátu), [dokumentace API](https://developers.iucto.cz/), [spolupráce s účetní](https://www.iucto.cz/ucetni-spoluprace/)
