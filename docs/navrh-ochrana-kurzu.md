# Návrh: ochrana kurzů v účetnictví

Plán ke schválení, červená zóna (`investra_rates`). Stav 10. 11. 2026, připravil Claude na pokyn uživatele.
Nic z toho není naprogramované.

**Doporučení:** Kurzy Odoo (`res.currency.rate`) se zapisují jen z evidence kurzů Investra (`investra.rate`).
Každý jiný kurz, ruční přepis vyhlášeného kurzu nebo kurz měny, kterou zdroj nevyhlašuje, vznikne jako záznam
v evidenci. Zapíše ho jen uživatel se skupinou **Investra: schvalování ocenění**, vždy s důvodem. Účetnictví i ocenění
tak používají stejný kurz a každá výjimka je dohledatelná. Kdo smí kurz přepsat, rozhodl uživatel 10. 11. 2026
(varianta 2: skupina schvalování ocenění, bez čtyř očí).

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
| A. Úplný zámek | `res.currency.rate` zapisuje jen stahování; ruční kurz nejde zadat vůbec | nejjednodušší | nejde zadat kurz měny, kterou zdroj nevyhlašuje, ani opravit chybu zdroje |
| B. Jen kontrola | nic nezakazuje; kontrola vypíše rozdíly | žádné omezení práce | chyba se zjistí až po zaúčtování; oprava storno a nové doklady |
| **C. Vše přes evidenci** (doporučeno) | `res.currency.rate` zapisuje jen evidence; ruční kurz a přepis jsou záznamy evidence s důvodem | jeden zdroj pro účetnictví i ocenění, auditní stopa | nová pole v `investra.rate` a víc testů |

## Návrh řešení (varianta C)

Vše v modulu `investra_rates`, bez zásahu do jádra Odoo.

1. **Druh kurzu v evidenci.** Nové pole `origin` (Vyhlášený / Ruční přepis / Ruční kurz, výchozí Vyhlášený),
   `reason` (povinný u ručních), `overridden_id` (u přepisu odkaz na vyhlášený kurz). Pole `source` zůstává
   a u ručního záznamu určuje základ (ČNB = CZK, ECB = EUR), do kterých knih se kurz promítne.
   Jedinečnost se rozšíří na `(source, date, currency_id, origin)`.
2. **Kdo zapisuje.** Ruční přepis a ruční kurz založí jen skupina `investra_entity.group_valuation_approver`
   přes formulář s povinným důvodem. Záznam se pak nemění ani nemaže, stejně jako vyhlášený kurz.
   Oprava přepisu = nový přepis; platí poslední.
   - Ruční kurz jde zadat jen tam, kde vyhlášený kurz k datu neexistuje; jinak je to přepis.
   - Přepis k datu, ke kterému existuje schválené nebo pozdější ocenění fondu s touto knihou, se odmítne.
3. **Který kurz platí.** `get_rate` a `_publish` vezmou k datu nejdřív poslední ruční přepis, jinak vyhlášený
   nebo ruční kurz. Ocenění ukáže u řádku portfolia, že kurz je ruční (zdroj kurzu už v portfoliu je).
4. **Zámek kurzů Odoo.** Dědičnost `res.currency.rate`: `create`, `write` a `unlink` projdou jen ze zápisu evidence
   (příznak v kontextu) nebo pro kód běžící jako superuživatel (`env.su`). Ruční zápis v nastavení měn se odmítne
   hláškou s odkazem na evidenci kurzů. Tím odpadají rizika 1 a 3.
5. **Žádné tiché přeskočení.** `_publish_value` při existujícím kurzu přepíše hodnotu jen u přepisu z evidence;
   jinak rozdíl ohlásí v logu i ve výsledku stahování a kurz nechá. Odpadá riziko 2.
6. **Kniha se zdrojem ECB (riziko 4).** Nejdřív test, který chování potvrdí nebo vyvrátí; řešení podle výsledku
   ke schválení zvlášť.
7. **Plánovaná úloha (riziko 5).** Zůstane v datech modulu vypnutá; zapnutí v `investra_dev` je krok nasazení
   se souhlasem uživatele.
8. **Obrazovka** (zelená, po modelu): seznam kurzů dostane sloupec Druh a filtr „Ruční“; tlačítko „Přepsat kurz“
   a „Nový ruční kurz“ jen pro skupinu schvalování ocenění.

**Testy** (nové, v `investra_rates/tests/`):
ruční změna a smazání kurzu Odoo se odmítne; stažení kurz zapíše; přepis založí jen skupina schvalování ocenění
a bez důvodu se odmítne; přepis se promítne do kurzu Odoo a `get_rate` ho vrátí; přepis k datu schváleného ocenění
se odmítne; ruční kurz pro den s vyhlášeným kurzem se odmítne; stažení nad odlišným existujícím kurzem ohlásí rozdíl;
kniha ECB a měna mimo ECB (riziko 4). Existující testy a jejich očekávané hodnoty se nemění.

## Dopad na data a účetnictví

- Existující doklady ani kurzy se nemění. Přepis platí pro doklady a ocenění vytvořené po něm; už zaúčtované
  doklady se opravují stornem a novým dokladem.
- Před nasazením Claude ověří dotazem SELECT v `investra_dev`, zda už v `res.currency.rate` není kurz odlišný
  od `investra.rate`. Nalezené rozdíly předloží uživateli; opravují se jen přes Odoo, nikdy příkazem nad databází.
- Nasazení znamená aktualizaci modulu `investra_rates`, ke které Claude požádá o souhlas.

## Otázky pro uživatele

1. Je potřeba zadávat kurzy měn, které ČNB vyhlašuje jen měsíčně (kurzy ostatních měn)? Pokud ano, navrhuji
   doplnit jejich stahování jako další zdroj místo ručního kurzu.
2. Má se ruční přepis kurzu zobrazit i jako upozornění v kontrolách ocenění? To je změna `investra_nav`
   a samostatný krok.

## Zóna a provedení

Červená zóna: provede Claude po schválení uživatelem, ne Antigravity (kromě bodu 8). Odhad: dvě třídy modelu,
tři nová pole, osm až deset testů, bez migrace dat (nové pole má výchozí hodnotu).

## Provedení 2026-11-10

Schváleno uživatelem 10. 11. 2026 (deník: „Ochrana kurzů“, „Přepis kurzu“). Provedl Claude v `feature/nav-prototyp`.

- **Body 1–5 a 8 hotové.** Evidence má druh kurzu (Vyhlášený / Ruční přepis / Ruční kurz), důvod a odkaz na přepsaný
  kurz. Ruční záznam zakládá jen skupina schvalování ocenění přes okno „Nový ruční kurz“ (seznam kurzů) nebo
  „Přepsat kurz“ (detail kurzu). Platí poslední přepis k datu. Kurzy Odoo (`res.currency.rate`) zapisuje jen evidence
  jako systém; ruční zápis, změna i smazání se odmítne. Stažený kurz existující odlišnou hodnotu v Odoo nepřepíše
  a rozdíl zapíše do logu (WARNING).
- **Přepis po schváleném ocenění:** modul ocenění odmítne ruční kurz k datu, ke kterému nebo po kterém existuje
  ocenění fondu se stejným zdrojem kurzů ve stavu Schváleno a dál.
- **Měsíční kurzy ČNB** (kurzy ostatních měn) se stahují za minulý a běžný měsíc. Odchylka: nejsou samostatný zdroj,
  ale zdroj ČNB se značkou „měsíční“ (stejný vydavatel i základ CZK; samostatný zdroj by komplikoval nastavení knih).
  Platí až 35 dní. Kurz 0,000 (zdroj měnu nevyhlašuje) se neukládá.
- **Upozornění v ocenění:** kontrola „Ocenění používá jen vyhlášené kurzy“ se závažností Upozornění vypíše ruční kurzy
  měn portfolia, tříd a fondu s důvodem.
- **Jedinečnost v databázi:** `UNIQUE NULLS NOT DISTINCT (source, date, currency_id, origin, overridden_id)` – jeden
  vyhlášený a jeden ruční kurz k datu, přepisy v řetězu.
- **Test fondu se zdrojem ECB (bod 6) zatím neproveden** – zůstává otevřený.
- Test `investra_fx_revaluation/tests/test_fx_run.py` zakládá kurzy Odoo pomocníkem testů Odoo; nově ho volá jako
  systém. Očekávané hodnoty se nezměnily.

Testy: `investra_rates/tests/test_protection.py` (10), `investra_nav/tests/test_manual_rate.py` (4); všech 311 testů
modulů Investry prošlo. V `investra_dev` začne ochrana platit až po aktualizaci modulu `investra_rates` (se souhlasem).
