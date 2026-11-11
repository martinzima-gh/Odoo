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

## Riziko 4 – plán řešení (2026-11-11, ke schválení)

**Zjištění:** test `test_ecb_book_mixes_cnb_rate_for_currency_outside_ecb` potvrdil, že kniha ECB přepočte měnu
mimo ECB společným kurzem ČNB (1000 JPY = 151,23 „EUR“, ve skutečnosti CZK). Podle kódu Odoo (`_get_rates`) platí
pro všechny knihy také: měna bez kurzu má kurz 1,0 a před prvním kurzem se vezme pozdější kurz.

**Rozhodnutí uživatele 11. 11. 2026:** varianta B (zámek) + C (ruční kurz s důvodem). Zámek platí pro knihy ČNB
i ECB, kurzovní lístky se mají chovat shodně. Křížový kurz mezi lístky se nepoužívá, ČNB a ECB jsou nezávislé zdroje.

**Návrh provedení** (červená zóna, `investra_rates/models/currency.py`):

1. Dědičnost `res.currency._get_conversion_rate`. Přes tuto metodu berou kurz všechny doklady účetnictví Odoo
   (řádky dokladů, platby, kurzové rozdíly při párování); jiné čtení kurzů modul `account` nemá (ověřeno prohledáním).
   Pro společnost, která je knihou (`investra.entity`), vrátí poměr z evidence:
   `get_rate(zdroj knihy, z měny, den) / get_rate(zdroj knihy, do měny, den)`. Je to stejná funkce jako u ocenění,
   přecenění FX a pohybů: poslední kurz do data včetně, nikdy pozdější, maximální stáří 5 dní (měsíční kurzy 35).
   Chybějící nebo starý kurz se odmítne hláškou „Chybí kurz X ke dni …“. Pro společnost bez knihy zůstává chování Odoo.
2. Ruční kurz (C) se nemění: zadává ho skupina schvalování ocenění s důvodem v okně „Nový ruční kurz“; pro knihu ECB
   jako kurz zdroje ECB (např. XDR). Hláška zámku na okno odkáže.
3. Kurzy Odoo (`res.currency.rate`) se dál zapisují z evidence. Slouží pro zobrazení v nastavení měn; v knize ECB tam
   u měny mimo ECB dál uvidíme smíšený kurz (jen zobrazení, doklady ho nepoužijí).
4. Úprava `_get_rates` o den navíc zůstane kvůli zobrazení; pro doklady ji nahradí bod 1.

**Dopad:** doklad v měně bez platného kurzu nejde založit ani zaúčtovat, dokud se kurz nestáhne nebo nezadá ručně.
Existující doklady a jejich kurzy se nemění; koncept si drží kurz řádku, dokud se nezmění datum nebo měna.

**Testy:** charakterizační test se obrátí (kniha ECB a JPY: odmítnutí; po ručním kurzu ECB správný přepočet);
nově kniha ČNB a měna bez kurzu (odmítnutí místo 1,0), kurz jen po datu dokladu (odmítnutí), starý kurz (odmítnutí),
faktura v cizí měně a kurzový rozdíl při párování z evidence. Testy, které zakládají jen kurz Odoo bez evidence
(např. `investra_fx_revaluation/tests/test_fx_run.py`), se převedou na kurz v evidenci; očekávané hodnoty se nemění.
Poté všechny testy modulů Investry v `investra_test`.

**Nasazení:** aktualizace `investra_rates` v `investra_test`; v `investra_dev` až se souhlasem.

**Otázky:** (1) Stačí pro doklady maximální stáří kurzu 5 dní (měsíční 35), jako výchozí u ocenění?
(2) Ponechat smíšený kurz v zobrazení nastavení měn (bod 3), nebo ho v knize ECB skrýt?

### Upřesnění 2026-11-11 po odpovědích uživatele (ke schválení)

Odpovědi uživatele: (1) maximální stáří kurzu má být parametr měny a kurzovního lístku; (2) žádné smíšené kurzy,
ani v zobrazení; (3) křížový kurz mezi ČNB a ECB se nepoužívá ani výjimečně, v krajním případě se zadá ruční kurz.
Tím se mění body 3 a 4 návrhu výše a otázky (1) a (2) jsou zodpovězené.

**A. Platnost kurzu podle lístku a měny** (`investra_rates`, nový model `investra.rate.validity`, nabídka
Investra → Nastavení → Účtování → Platnost kurzů):
- Řádek = kurzovní lístek (ČNB denní, ČNB měsíční, ECB) + měna (prázdná = výchozí pro lístek) + nejvyšší stáří ve dnech
  (kalendářních, jako dnes). Výchozí řádky: ČNB denní 5, ČNB měsíční 35, ECB 5; měny jen výjimky.
- `get_rate` bere stáří z řádku pro měnu, jinak z výchozího řádku lístku; lístek se určí podle vyhlášení kurzu
  (denní / měsíční). Ruční kurz a ruční přepis mají platnost lístku, ke kterému patří (ruční kurz XDR ve zdroji ECB
  = lístek ECB). Konstanta `MONTHLY_MAX_AGE_DAYS` zanikne.
- Jedno nastavení pro všechny: doklady, ocenění, přecenění FX, úpisy a odkupy. Pole „Nejvyšší stáří kurzu“ na fondu
  (`investra.fund.max_rate_age_days`) a na profilu přecenění (`investra.fx.profile.max_rate_age_days`) se odstraní;
  dnes mají všude hodnotu 5 (`investra_test`: 5 fondů, 1 profil; `investra_dev` je ještě nemá), takže se výsledky nezmění.
- Změnu tabulky smí jen skupina schvalování ocenění; změny se zaznamenávají (chatter), řádky nejde mazat, jen archivovat.

**B. Žádné smíšené kurzy** (`investra_rates/models/currency.py`):
- Doklady: zámek podle bodu 1 návrhu (`_get_conversion_rate` z evidence zdroje knihy).
- Zobrazení a souhrny: pro knihu (`investra.entity`) se `res.currency._get_rates` nahradí čtením z evidence zdroje
  knihy (poslední kurz do data včetně). Týká se nastavení měn (aktuální kurz) a souhrnů v cizí měně v analýze faktur
  a analytických účtech (agregace `sum_currency`, ověřeno v Odoo 20). Měna bez kurzu zdroje knihy: nastavení měn ukáže
  „Kurz ECB chybí“ místo čísla, souhrn v cizí měně skončí hláškou „Chybí kurz X“ (ne kurzem 1,0 ani kurzem ČNB).
  Bod 4 (den navíc) pro knihy zanikne; pro společnost bez knihy zůstává.
- Seznam kurzů v nastavení měn knihy ECB nebude ukazovat společné kurzy ČNB (pravidlo záznamů na `res.currency.rate`).
- Ukládání kurzů do Odoo (`_publish`) se nemění: ČNB jako společné kurzy, ECB do knih ECB. Nic se nemaže.
- Společnost bez knihy (dnes `investra_dev` společnost 1, `investra_test` společnosti 1 a 2) zůstává na chování Odoo.

**C. Křížový kurz** se nepoužívá v žádné podobě. Měnu, kterou ECB nevyhlašuje, řeší v knize ECB jen ruční kurz s důvodem.

**Testy navíc:** výjimka pro měnu přebije výchozí stáří lístku; měsíční lístek 35 dní bez konstanty; nastavení měn
v knize ECB nezobrazí kurz JPY; souhrn analýzy faktur v JPY v knize ECB skončí hláškou; ocenění a přecenění FX berou
stáří z tabulky (stávající očekávané hodnoty beze změny).

**Migrace:** `investra_rates` (výchozí řádky tabulky), `investra_nav` a `investra_fx_revaluation` (odstranění polí;
sloupce v databázi Odoo nemaže, nečíst je). Aktualizace v `investra_test` se souhlasem, v `investra_dev` zvlášť se souhlasem.

**Rozhodnuto 11. 11. 2026:** stáří kurzu na fondu a profilu přecenění se odstraní, jediné místo nastavení je tabulka
Platnost kurzů. Zámek a část B upřesnění zrušeny rozhodnutím níže.

### Rozhodnutí 2026-11-11 (odpoledne): neohýbat standard Odoo, riziko 4 akceptováno

Uživatel: „pokud je to standardní funkčnost Odoo, neohýbej“; kurzy ČNB zůstanou společné, riziko natažení kurzu
ČNB do knihy ECB akceptuje; den navíc v `_get_rates` (bod 4) zůstává.

- **Ruší se:** zámek v `_get_conversion_rate` (bod 1 návrhu), náhrada `_get_rates` pro knihy a skrytí společných kurzů
  v zobrazení (Upřesnění, část B). Doklady, zobrazení a souhrny Odoo počítají standardně: kurz knihy, jinak společný;
  bez kurzu 1,0; před prvním kurzem pozdější kurz.
- **Zůstává:** ruční kurz s důvodem (bod 2, C) – v knize ECB jím uživatel doplní měnu, kterou ECB nevyhlašuje;
  den navíc v `_get_rates` (kurz platí v den vyhlášení, § 24 odst. 6 zákona o účetnictví – znění neověřeno);
  ukládání kurzů beze změny (ČNB společně, ECB do knih ECB).
- **Zůstává k provedení:** tabulka Platnost kurzů (Upřesnění, část A) pro ocenění, přecenění FX a úpisy a odkupy,
  a odstranění stáří kurzu z fondu a profilu přecenění. Pro doklady Odoo se nepoužije. Provedení čeká na schválení.
- Charakterizační test `test_ecb_book_mixes_cnb_rate_for_currency_outside_ecb` zůstává jako doklad akceptovaného chování
  (při upgradu Odoo upozorní na změnu).

### Provedení – Platnost kurzů (2026-11-11)

Schválil uživatel 11. 11. 2026. Model `investra.rate.validity` (`investra_rates` 20.0.0.2.0, nabídka Nastavení → Účtování →
Platnost kurzů): výchozí řádky ČNB denní 5, ČNB měsíční 35, ECB 5 (`data/validity.xml`, noupdate), výjimky pro měny;
mění jen skupina schvalování ocenění, chatter, mazání zakázané (archivace). `get_rate` bere stáří z tabulky
(parametr `max_age_days` a konstanta `MONTHLY_MAX_AGE_DAYS` zanikly). Pole stáří na fondu a profilu přecenění odstraněna
(sloupce v databázi zůstaly, nečíst je).

Odchylky: (1) čtení tabulky má jen skupina `account.group_account_readonly` jako evidence kurzů; správce účetnictví bez
této skupiny ji nevidí. (2) Testy přecenění mění výchozí stáří denního lístku, ne výjimku měny: kontroluje se i kurz
funkční měny společnosti, stejně jako dřív u pole na profilu.

Testy: nové `investra_rates/tests/test_validity.py` (10). Všech 362 testů modulů Investry prošlo v kopii
`investra_test_kontrola` (obnova zálohy `zalohy/investra_test-2026-11-11-pred-platnosti-kurzu.dump`). V `investra_test`
prošly `investra_rates` a `investra_nav`; testy přecenění tam padají už v přípravě testovací knihovny Odoo `account`
(MissingError u kopie účtu), i s kódem před změnou – otevřený bod. `investra_dev` beze změny.
