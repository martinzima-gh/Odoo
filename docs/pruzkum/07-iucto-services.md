# iÚčto pro Investra Services: porovnání s Odoo

Stav 2026-11-08. Podklad, ne rozhodnutí. Údaje o iÚčtu jsou z jeho veřejného webu; aplikaci jsme nezkoušeli.
Údaje o Odoo jsou z naší kontroly Odoo 20 Community (`docs/ceska-lokalizace.md`) a průzkumu edice (`01-edice-hosting.md`).

## Závěr

- **Pro Investra Services je iÚčto vážná varianta.** Většinu funkcí, které Community chybí (rozvaha, výsledovka, banka, podání DPH), má hotovou za stovky korun měsíčně.
- **Jako samostatný fondový systém iÚčto doložené není.** Veřejný web neuvádí fondové NAV, portfolio ani výkazy ČNB. To ale nevylučuje variantu, kdy iÚčto vede účetní knihy a fondovou agendu zajišťuje vlastní aplikace.
- **K posouzení jsou tři architektury:** vše v Odoo; Services v iÚčtu a investiční společnost s fondy v Odoo; nebo iÚčto jako účetní systém všech společností a fondů plus vlastní fondová aplikace bez Odoo. Poslední varianta mění rozhodnutí „Odoo je jediný účetní systém od začátku“ z 2026-11-04 i samotný cíl projektu.
- Žádná varianta zatím není tímto průzkumem schválena. iÚčto ani jeho API nebylo prakticky testováno; před rozhodnutím je nutné ověřit účetní použitelnost, API, bezpečnost, export a celkové náklady.
- Před rozhodnutím ověřit body v části „Ověřit u iÚčta pro Services“ a v „Blokující ověření u iÚčta“, zejména bezpečnost, účetní použitelnost fondů, API a uzamčení období.

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

## Varianta: iÚčto pro účetnictví, vlastní fondová aplikace

V této variantě se Odoo nepoužívá. iÚčto vede účetnictví Investra Services, investiční společnosti, SICAV, fondů a podfondů. Samostatně vyvinutá aplikace spravuje fondové procesy a předává schválené účetní zápisy do příslušné knihy v iÚčtu.

| Oblast | Systém odpovědnosti v návrhu |
|---|---|
| Účetní knihy a zaúčtované zápisy | iÚčto; je zdrojem pravdy pro stav hlavní knihy |
| Instrumenty, portfolio, ceny a vstupy ocenění | Vlastní fondová aplikace |
| Výpočet NAV, třídy a alokace | Vlastní fondová aplikace; výsledek se musí pravidelně porovnávat s účetní knihou |
| Schvalování ocenění a auditní stopa výpočtu | Vlastní fondová aplikace, pokud to potvrdí metodika a audit |
| Výkazy ČNB | Vlastní fondová aplikace by je připravovala a případně podávala; zdrojem účetních zůstatků zůstává iÚčto |
| Úpisy, odkupy a držitelé | Samostatný IS podle dosavadního návrhu; přesné rozhraní s fondovou aplikací je nutné definovat |

Toto rozdělení je návrh k ověření, nikoli potvrzená účetní ani regulatorní architektura. Odpovědné osoby musí potvrdit, zda je přijatelné, aby schválení a podklady k NAV byly v jiné aplikaci než účetní kniha a jakou právní evidenční váhu mají záznamy obou systémů.

### Výhody a náklady

- Odpadá závislost na Odoo, jeho edici a vlastních Odoo addonech. iÚčto může dodat hotové běžné účetní funkce; použitelnost pro účetnictví fondů a finanční instituce ale není doložena.
- Fondová aplikace může být navržena přesně podle workflow, dat a výkazů fondů. Současně bude nutné od začátku vytvořit a dlouhodobě udržovat aplikaci, integraci, přístupová práva, schvalování, auditní stopu, monitoring, zálohování a obnovu.
- Přenos zápisů přes API neznamená, že je vyřešena jejich účetní správnost, auditovatelnost ani návaznost na NAV. Vzniká kritická hranice mezi dvěma systémy a potřeba průběžné rekonciliace.
- iÚčto veřejně uvádí účtování po jednotlivých firmách a tarify na jednu firmu. Je třeba ověřit počet knih/firem, cenu pro všechny fondy, správu uživatelů a případné limity API.

### Srovnání architektur

| Varianta | Silná stránka | Hlavní náklad nebo riziko | Stav poznání |
|---|---|---|---|
| Odoo pro účetnictví i fondy | Jedna databáze a přímá vazba mezi NAV a účetními zápisy | Vývoj a údržba českého účetnictví, fondových funkcí a provozní infrastruktury | Existuje prototyp, ne produkční řešení |
| iÚčto pro Services; Odoo pro investiční společnost a fondy | Omezení vývoje běžného účetnictví Services | Dva účetní systémy a přenos dokladů mezi nimi; Odoo zůstává pro fondy | iÚčto nevyzkoušeno |
| iÚčto pro všechny účetní knihy; vlastní fondová aplikace | Hotové účetnictví oddělené od specializovaných fondových procesů; bez Odoo | Vlastní vývoj celé fondové aplikace a kritické API integrace; kompatibilita iÚčta s fondovými knihami neověřena | Zatím architektonická hypotéza |

Tabulka není cenové ani technické vyhodnocení. Celkové náklady musí zahrnout licence za všechny firmy a uživatele, implementaci, vlastní vývoj, integraci, bezpečnost, provoz a dlouhodobou údržbu.

### Blokující ověření u iÚčta

1. **Účetní použitelnost fondů:** lze vést samostatnou knihu pro každý fond/podfond a zvolit požadovaný účtový rozvrh, analytiky, měny, účetní rámec a případné specifické výkazy? Jaké jsou limity tarifu a celková cena pro očekávaný počet knih?
2. **Účetní zápis přes API:** jaký je přesný datový model deníkového zápisu? Lze předat účty, MD/D, účetní datum, měnu, kurz, částku v cizí měně, analytické údaje, přílohy a externí identifikátor ocenění?
3. **Stav a opakování:** API vrací-li chybu nebo vyprší-li spojení po přijetí požadavku, jak zjistí klient, zda zápis vznikl? Je podporován idempotency key nebo bezpečné vyhledání podle externího ID? Lze oddělit přijetí návrhu od skutečného zaúčtování?
4. **Opravy a období:** jak fungují zámky, storna, opravy a zápisy do uzavřených období, včetně zachování původního data a historie?
5. **Testování a bezpečnost:** dodavatel uvádí, že API nemá sandbox a klíč má široký přístup k účetnictví firmy. Lze zřídit izolovanou testovací firmu, oddělený klíč a bezpečně jej odvolat? Jaká oprávnění API přebírá a jak se jeho činnost loguje?
6. **Provoz a odchod:** jaké jsou hosting, zálohy, obnova, dostupnost, oznamování incidentů a úplný export účetnictví i příloh při ukončení služby?

### Požadavky na účetní a fondovou aplikaci

- Metodik a auditor musí určit, co je účetní doklad, co schvaluje druhá osoba, kdy se výsledky NAV zaúčtují a jak se řeší vrácení po schválení, po zaúčtování a po stanovisku depozitáře.
- Pro každou účetní knihu je nutné určit rámec, osnovu, role účtů, účetní měnu, pravidla FX, analytiku a mapování do výkazů ČNB.
- Fondová aplikace musí uchovat vstupy, verzi metodiky a parametrů, reprodukovatelný výpočet, průběh schválení, původní i opravené výsledky a vazbu na identifikátory účetních zápisů v iÚčtu.
- Musí existovat rekonciliace NAV proti účetní knize a kontrola úplnosti přenosů: žádný zápis navíc, žádný chybějící zápis, shoda částek a měn i stavů.
- Compliance a právník musí posoudit umístění a role dodavatelů, přístup k datům, smlouvy, auditní práva, uchování záznamů a regulatorní dopad včetně DORA. Konkrétní povinnosti je třeba ověřit podle aktuálních pravidel; tento průzkum je právně neposuzuje.

### Doporučený pilot a stop podmínky

Pilot dělat výhradně s umělými daty a až poté, co dodavatel potvrdí bezpečný testovací postup. Nezkoušet API proti ostré účetní firmě.

1. **Odpovědi a návrh rozhraní:** získat odpovědi na blokující otázky, specifikaci API a cenovou nabídku pro počet knih a uživatelů. Pokračovat pouze tehdy, pokud API umí vytvořit a zpětně jednoznačně identifikovat potřebný účetní zápis.
2. **Ruční test v oddělené firmě:** ověřit osnovu, měny, reporty, období, storno a export na smyšleném fondu. Pokračovat jen při potvrzení účetní použitelnosti a dohledatelnosti.
3. **Technická zkouška integrace:** přenést jeden malý schválený scénář s více měnami; zopakovat požadavek, simulovat timeout, zkusit chybný účet a uzavřené období, ověřit načtení stavu a opravu/storno. Kritériem je žádné duplicitní ani tiché chybné zaúčtování a úplný auditní záznam v obou systémech.
4. **Rekonciliace a nezávislé posouzení:** porovnat účetní knihu, portfolio, NAV a výstup ČNB na předem připravených scénářích; účetní metodik a nezávislý reviewer potvrdí výsledky a vysvětlí všechny rozdíly.
5. **Ekonomika a provozní brána:** porovnat celkové náklady a plán údržby s alternativami; ověřit zálohu, obnovu, oprávnění, správu klíčů a postup odchodu.

**Zastavit nebo změnit variantu**, pokud iÚčto nepotvrdí požadované knihy či účtové rozvrhy, API neumí bezpečně rozlišit a dohledat zápisy nebo zabránit jejich duplicitám, neexistuje bezpečný testovací postup, nelze rekoncilovat účetnictví s NAV, nebo se nepodaří přijmoutelně vyřešit auditní, regulatorní a provozní odpovědnosti.

## Co by hybrid (Services v iÚčtu, fondy v Odoo) znamenal

- **Úplaty Services fondům:** Services fakturuje, fondy v Odoo účtují náklad. Vydanou fakturu přenést do Odoo ručně, nebo přes API iÚčta.
- **Dvě sady znalostí a dva systémy** pro jedny účetní. U Services ale odpadá vlastní vývoj české lokalizace, který je dnes největší položkou.
- **Investiční společnost** (vyhláška 501, výkazy ČNB) by šla do Odoo stejně jako fondy. Odoo by tedy českou lokalizaci podnikatele nepotřebovalo vůbec, ale potřebovalo by svoji pro finanční instituce.
- **DORA:** pro investiční společnost je Services poskytovatel služeb. Pokud Services přes iÚčto zpracovává data pro investiční společnost, je iÚčto další ICT dodavatel v řetězci. Posoudit při mapě DORA.
- **Přechod později:** z iÚčta do Odoo jde převést počáteční stavy k začátku roku; formát exportu ověřit.

## Ověřit u iÚčta pro Services

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
