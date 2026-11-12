# Návrh: splátky jistiny nástrojů – jeden mechanismus pro naběhlou i reálnou hodnotu

Stav: **schváleno uživatelem 12. 11. 2026** (odpovědi na otázky viz konec). Zóna: červená (účtování, ocenění, NAV). Navazuje na rozhodnutí
„Úročení nástrojů“ (2026-11-07), „Klasifikace podle obchodního modelu fondu“ (2026-11-09, 2026-11-11),
„Role s více účty“, „Převody mezi bankami a bankovní poplatky“ a „Zámek a storno splátky“ (2026-11-12).

Rozhodnuto uživatelem 12. 11. 2026 (vstup návrhu):
- jeden mechanismus splátky pro nástroje v naběhlé i reálné hodnotě, s postupnými splátkami a hlídáním zbývající jistiny;
- splátka neúčtuje přímo na banku, ale na peníze na cestě; výpis je pak vynuluje párováním.

## Jak to funguje dnes (ověřeno v kódu 12. 11.)

- `investra.instrument.repayment` (`investra_nav/models/instrument_accrual.py`) vznikl 7. 11. s termínovaným vkladem.
  Doklad MD banka / D účet nástroje; řádek nástroje nese `investra_instrument_id` a `investra_classification_id`.
- Proč samostatný doklad: ocenění (`valuation.py`, přecenění portfolia) bere **účetní hodnotu pozice jen z označených řádků**
  účtu nástroje a rozdíl proti požadované hodnotě doúčtuje. Řádek z výpisu nebo ručního dokladu značku nemá – ocenění by
  splátku nevidělo a doúčtovalo by ji jako ztrátu (v naběhlé hodnotě proti úrokovým výnosům).
- EIR splátku nepoužívá: naběhlá hodnota se počítá z obchodu a smluvního kalendáře (`_accrued_value`). Pozice v naběhlé
  hodnotě „zmizí“, protože po posledním toku kalendáře vyjde hodnota 0, ne kvůli splátce.
- Pozice = (nástroj, obchodní model) a kusy z obchodů (`investra.trade._holdings`). Splátka kusy nesnižuje.

Nedostatky:
1. Jen naběhlá hodnota – v reálné hodnotě (kusy × cena) by pozice po splátce zůstala v plné výši.
2. Jedna splátka, bez zbývající jistiny a bez ochrany proti přeplacení.
3. Nástroj i model se vybírají volně, nekontroluje se držená pozice. Model je přitom daný pozicí (obchodem),
   ne volbou při splátce.
4. MD banka: až přijde výpis, banka by se zaúčtovala podruhé.

## A. Protiúčet: inkasa na cestě 119100

Osnova už má pod rolí `cash_in_transit` účty 119000 (převody mezi bankami), **119100 Inkasa na cestě** (Odoo Outstanding
Receipts, přijaté platby čekající na spárování s výpisem) a 119200 Platby na cestě (`docs/osnova-fondu.md`).

- Splátka: **MD 119100 / D nástroj** (se značkou nástroje a zařazení). Výpis: **MD banka / D 119100**, 119100 se spáruje.
- Doporučení: 119100, ne 119000 – odděluje inkasa od převodů mezi bankami a odpovídá standardní cestě Odoo
  (přijatá platba → outstanding receipts → výpis). Splátka účtuje přes roli, ne číslo účtu: buď nová role
  `cash_in_transit_receipt` (hlavní účet 119100), nebo účet „outstanding receipts“ společnosti. **Doporučuji novou roli**
  (pravidlo „v logice jen role“, výkazy ČNB a kontroly ji sečtou jako ostatní).
- Community: výpis jde na nevyjasněné položky 229000; přeúčtování 229000 → 119100 ručním dokladem (jde, 229000 ani 119100
  nejsou bankovní účty). Enterprise: párování řádku výpisu s otevřenou položkou 119100.
- NAV: do příchodu výpisu je splátka aktivem „peníze na cestě“; kontrola ocenění „Peníze na cestě jsou nulové“ (upozornění)
  ji ukáže – to je žádoucí.
- Navazující bod (mimo tento návrh): vypořádání obchodů stejnou cestou.

## B. Zbývající jistina

**Varianta B1 (doporučuji): kusy pozice = jistina.** U nástrojů s jistinou (vklad, úvěr, dluhopis) se pozice vede v jednotkách
jistiny: kusy = nominál, cena = cena za jednotku nominálu (u vkladu 1,00), kalendář toků na jednotku. Splátka jistiny
**sníží kusy pozice** stejně jako prodej.
- `_holdings`, reálná hodnota (kusy × cena) i kontrola přeplacení (splátka ≤ kusy k datu) fungují beze změny logiky.
- Dopad: obchod s vkladem se zadává jako 5 000 000 ks × 1,00 místo 1 ks × 5 000 000; kalendář na jednotku
  (jistina 1, úrok na 1). Stávající vklad v `investra_test` (obchod 1460) převede migrace, nebo ho uživatel zadá znovu.

**Varianta B2: zvláštní zůstatek jistiny na pozici.** Kusy zůstanou, jistina se vede zvlášť. Ocenění v reálné hodnotě by muselo
počítat s poměrem zůstatku – dvě evidence téhož, víc kódu a riziko nesouladu. Nedoporučuji.

## C. Rozpad splátky

Splátka má složky **jistina** a **úrok** (případně **poplatek**), součet = přijatá částka na 119100.
- Jistina: v B1 snižuje kusy; účetně D nástroj.
- Úrok: D nástroj – snižuje naběhlý úrok (v naběhlé hodnotě i v RH, kde nástroj nese pořizovací cenu, naběhlý úrok
  a přecenění; rozhodnutí 3).
- Rozdíl proti očekávání doúčtuje ocenění jako dnes (naběhlá hodnota → úrokové výnosy; RH → přecenění).

## D. Naběhlá hodnota (EIR)

- **Splátka podle kalendáře:** kalendář už splátku obsahuje; kusy se nesnižují znovu. Proto v B1 splátka jistiny podle
  kalendáře **nesnižuje kusy**, jen uzavírá tok kalendáře (vazba splátka → tok kalendáře). Kusy snižuje jen **mimořádná**
  splátka mimo kalendář.
- **Mimořádná / předčasná splátka:** změna očekávaných toků; IFRS 9 řeší přepočtem naběhlé hodnoty původní EIR a rozdílem do
  výsledku (odst. 5.4.3 a B5.4.6 – **citace ověřit v EUR-Lex, výklad potvrdit s auditorem**). Prototyp ji zatím
  odmítne (rozhodnutí 4); řešení je otevřený bod.
- Otevřený bod: úvěr s více splátkami a změnou sazby (již v otevřených bodech „Naběhlá hodnota ve fondu“).

## E. Reálná hodnota

Splátka jistiny = odúčtování části pozice podle pravidla „Částečný prodej“ v architektuře: poměrná část pořizovací ceny,
přecenění a kurzového rozdílu; u FVTPL realizovaný výsledek. Ocenění pak oceňuje jen zbývající kusy.

## F. Výběr nástroje, předvyplnění a kontroly

- Formulář: Fond, Datum, **Nástroj** – nabídnou se jen nástroje, které fond k datu drží; obchodní model se nezadává,
  doplní se z nákupu. Jen když fond drží tentýž nástroj ve dvou modelech, ukáže se pole Obchodní model s těmito dvěma.
- Po výběru nástroje se ukáže (jen pro čtení) **zbývající jistina k datu** a **zbývající jistina po splátce**; jistina a úrok
  se předvyplní podle kalendáře k nejbližšímu splatnému toku (bez kalendáře celá zbývající jistina), hodnoty jdou přepsat.
- Server: nástroj musí být k datu držený v daném modelu; jistina ≤ zbývající jistina k datu; součet složek = částka.
  Kontrola i při importu a opravě (`copy`).
- Zámek ocenění, storno a oprava zůstávají (rozhodnutí 2026-11-12); storno vrací kusy.

## G. Migrace a navazující změny

- Stávající splátky: protiúčet zůstane banka (zaúčtované doklady se nemění); nové splátky jdou na 119100.
- `action_generate_schedule`: kalendář na jednotku jistiny; blokace po první nestornované splátce zůstává.
- Nová verze `investra_nav` (a `investra_chart_fund` / `investra_fund` pro novou roli), testy na čisté DB, upgrade
  `investra_test` jen se souhlasem a zálohou.

## Rozhodnutí uživatele 12. 11. 2026

1. Protiúčet **119100 Inkasa na cestě** s novou rolí.
2. Zbývající jistina variantou **B1** (kusy = jistina).
3. Nástroj v reálné hodnotě nese **pořizovací cenu (zůstatek jistiny), naběhlý úrok a přecenění** (zbytek do RH).
   Ocenění tedy u úročených nástrojů v RH doúčtuje naběhlý úrok zvlášť (úrokové výnosy) a přecenění až jako rozdíl.
   Úrok ze splátky snižuje naběhlý úrok.
4. **Přepočet EIR se zatím neřeší.** V naběhlé hodnotě prototyp přijme jen splátku podle kalendáře; mimořádná splátka
   skončí chybou „zatím nepodporováno“ (otevřený bod).
5. Převod stávajícího vkladu nechal uživatel na Claudovi: migrace převede obchod a kalendář na jednotku jistiny
   (kusy × jistina na jednotku, cena a toky poměrně), účetní doklady se nemění; zastaví se, pokud k nástroji existuje
   nestornovaná splátka nebo ocenění Ke schválení až Potvrzeno.

## Etapy provedení

1. Splátka: výběr nástroje, předvyplnění a zbývající jistina, rozpad jistina/úrok, protiúčet 119100 (role), snížení kusů,
   kontroly, migrace B1; naběhlá hodnota jen podle kalendáře.
2. Naběhlý úrok u úročených nástrojů v reálné hodnotě v ocenění (bod 3 rozhodnutí) a odúčtování části pozice v RH (bod E).

## Provedení etapy 1 (12. 11. 2026)

- Bod 5 rozhodnut bez migrace obchodů: jistina na jednotku se bere z kalendáře (součet toků Jistina), bez kalendáře
  z pole Jistina na jednotku, jinak 1. Vzorec funguje pro 1 ks × 5 000 000 i pro 5 000 000 ks × 1, takže stávající
  vklad se nepřevádí a obchody ani kalendáře se nemění. Pro nové nástroje je doporučeno kusy = jistina (nápověda pole).
- Kusy pozice po splátkách počítá `investra.trade._holdings` (rozšíření v `investra_nav`): zaúčtovaná jistina se odečte
  v penězích, kusy = zbývající jistina / jistina na jednotku; splacená pozice z pozic zmizí.
- Ocenění doúčtuje na nulu i pozici bez kusů, která má na účtu nástroje zůstatek (dřív ji držely nezměněné kusy).
  Totéž nově platí pro úplně prodanou pozici v RH; realizovaný výsledek zvlášť je etapa 2 (bod E).
- Nová role `cash_in_transit_receipt` (Inkasa na cestě, 119100); migrace `investra_chart_fund` 0.6.0 přesune 119100
  z dalších účtů role `cash_in_transit`, ČNB má pro novou roli stejné řádky (ROFO10_11 ř. 24, RIS30_01 ř. 18).
  Kontrola ocenění „Peníze a inkasa na cestě jsou nulové“ sčítá obě role.
- Migrace `investra_nav` 0.10.0: dosavadní splátky mají celou částku jako jistinu, úrok 0; doklady beze změny.
- Ověřeno: čistá databáze (všechny vlastní moduly 455 testů, po opravě `investra_nav` 229 testů 0 chyb); kopie
  `investra_test` – předvaha a doklady před a po upgradu shodné, mapování rolí podle plánu, zkouška splátky vkladu
  ve fondu Delta (nabídka, předvyplnění 5 000 000 + 45 500, MD 119100 / D 132000, odmítnuté přeplacení).


## Návrh etapy 2: úrok v reálné hodnotě a realizovaný výsledek (schváleno 12. 11. 2026)

Stav dnes (ověřeno v kódu 12. 11.): ocenění v RH účtuje celý rozdíl hodnoty jako přecenění; úrok ze splátky jde na účet
nástroje druhem pohybu `transaction`, takže ho ocenění doplatí jako **zisk z přecenění, ne jako úrok**. Prodej účtuje
D nástroj v prodejní ceně a zbytek ocenění vynuluje jako nerealizované přecenění; role pro realizovaný výsledek není.
Sloupec pořizovací ceny řádku portfolia sčítá i prodeje v prodejní ceně (po částečném prodeji nesedí).

### Část A: úrok u nástrojů v RH

1. **Kupónové nástroje:** naběhlý kupón **lineárně** podle smlouvy (konvence dnů, mezi dvěma toky kalendáře) na
   zbývající kusy, s koeficientem mimořádných splátek. Lineárně proto, aby naběhlý úrok vykryl splátky jen kupónu.
   Diskont nebo prémie proti nominálu se **nerozpouští**; rozdíl proti EIR se projeví v přecenění na RH.
2. **Bezkupónové (diskontní) nástroje** (kalendář bez toků Úrok): diskont přirůstá do úroku **efektivní úrokovou
   mírou** (`engine.amortised_cost`, každý nákup vlastní EIR, jako u naběhlé hodnoty).
3. **Konvence ceny:** pole u typu nástroje (u nástroje jde přepsat) „cena je bez naběhlého úroku“. Dluhopis: cena bez
   úroku, hodnota = kusy × cena + naběhlý úrok. Vklad a úvěr: úrok je v ceně, hodnota = kusy × cena; naběhlý úrok jen
   rozdělí výsledek na úrok a přecenění.
4. **Účtování:** naběhlý kupón i diskont na **stejný účet nástroje** jako pořízení, odlišené druhem pohybu
   `accrued_interest`; žádný samostatný účet. Ocenění nejdřív doúčtuje
   úrok = cílová úroková složka k datu − zaúčtovaná úroková složka (MD nástroj / D `income_interest`), pak přecenění a
   kurzový rozdíl ze zbytku jako dnes. Úrok v cizí měně kurzem dne ocenění, kurzový rozdíl zůstává jeden.
5. **Zaúčtovaná úroková složka** se počítá ze zdrojových záznamů: úrok z ocenění + naběhlý úrok zaplacený při nákupu −
   úrok ze splátek − naběhlý úrok přijatý při prodeji. Zaúčtované splátky se proto nemigrují.
6. **Naběhlý úrok u obchodu:** nové pole obchodu, **jen u dluhopisů** (druh typu `bond`; ne akcie ani ostatní podíly),
   předvyplněné z kalendáře. Platba obchodu = kusy × cena + naběhlý úrok; úroková část jde na účet nástroje
   druhem pohybu `accrued_interest`.

### Část B: realizovaný výsledek v RH

1. **Průměrná pořizovací cena pozice** (pravidlo „Částečný prodej“): kusy a pořizovací cena v měně nástroje i ve funkční
   měně; splátka jistiny = prodej části jednotek za nominál. Opraví i sloupec pořizovací ceny.
2. **Realizovaný výsledek = výnos − poměrná účetní hodnota** (pořizovací cena + přecenění + kurzový rozdíl; úrok řeší
   část A). Dříve zaúčtované přecenění zůstává. Výsledek proti pořizovací ceně jen informativně v přehledu.
3. **Nové role** `gain_realised` / `loss_realised` (účty ve skupině 6/5, ČNB VYFO20_11 ř. 30 jako přecenění);
   realizovaný kurzový rozdíl na `gain_fx` / `loss_fx`.
4. **Účtuje se v ocenění, při přecenění portfolia:** doúčtování snížené nebo uzavřené pozice se rozdělí na realizovanou
   část (prodané a splacené jednotky od minulého ocenění) a nerealizovanou (zbytek). Datum dokladu = datum ocenění.

Mimo etapu 2: FVOCI, prodej v naběhlé hodnotě, nový kalendář s EIR, generátor kalendáře s více kupóny (testovací
kupónový dluhopis se zadá ručně). Citace IFRS 9 odst. 3.2.12, 5.7.1 a IFRS 7 odst. 20(a)(i) **neověřené** – ověřit v
EUR-Lex a výklad s auditorem; daňový dopad rozdělení realizovaný / nerealizovaný ověřit s daňovým poradcem.

**Provedení:** `investra_entity` / `investra_chart_fund` (role a účty, migrace osnovy), `investra_cnb` (mapování),
`investra_instruments` (konvence ceny, naběhlý úrok obchodu), `investra_nav` (úroková složka a realizace v ocenění,
průměrná cena). Testy na čisté DB s předem spočítanými příklady: dluhopis koupený uprostřed kupónu, ocenění, výplata
kupónu, částečný a úplný prodej, bezkupónový dluhopis, vklad v RH se splátkou, cizí měna, storno splátky. Upgrade
`investra_test` se zálohou a souhlasem.

## Provedení etapy 2 (12. 11. 2026)

- Role `gain_realised` / `loss_realised`, účty 715100 / 615100 (analytika pod 715 a 615), ČNB VYFO20_11 ř. 30;
  `investra_entity` 0.7.0, `investra_chart_fund` 0.7.0 (migrace doplní účty a mapování), `investra_cnb` 0.7.0.
- `investra_instruments` 0.9.0: u nástroje pole **Cena bez naběhlého úroku**; u obchodu pole **Naběhlý úrok** (jen dluhopisy,
  kladně; předvyplní se z kalendáře k datu sjednání). Obchod účtuje úrok samostatným řádkem na účet nástroje.
- `investra_nav` 0.15.0: ocenění v RH účtuje úrok od minulého ocenění (MD nástroj / D úrokové výnosy, druh pohybu Naběhlý
  úrok), u dluhopisu přičte naběhlý úrok k hodnotě. Přecenění ze zbytku rozdělí na realizovaný výsledek (prodeje a splátky
  jistiny od minulého ocenění, průměrem) a nerealizované přecenění. Řádek portfolia má nově naběhlý úrok, realizovaný
  výsledek a pořizovací cenu průměrem. U naběhlé hodnoty se naběhlý úrok zaplacený u nákupu dluhopisu přičte k pořizovací částce.
- **Odchylky od návrhu:**
  1. Konvence ceny je pole nástroje, výchozí hodnota se bere z druhu typu (dluhopis), ne nové pole typu. Data typů se proto
     nemusí měnit.
  2. Řádek naběhlého úroku u obchodu má druh pohybu Transakce, ne Naběhlý úrok: jde o platbu, ne o výnos. Úrok se počítá
     ze zdrojových záznamů (obchody, splátky), ne z druhů pohybu.
  3. Prodej bezkupónového nástroje v RH zatím končí chybou „zatím nepodporováno“. Kupón po mimořádné splátce se snižuje
     koeficientem za celé běžné období.
  4. Realizovaný výsledek v cizí měně se přepočte kurzem dne ocenění; kurzový rozdíl zůstává v kurzových účtech.
- Ověřeno: čistá databáze, všechny vlastní moduly 472 testů, 0 chyb (7 nových v `test_fair_value_interest.py`). Změněná
  očekávaná hodnota v `test_same_deposit_in_two_models_values_separately` je důsledek rozhodnutí: diskont vkladu v RH
  24,47 jde do úroku, ne do přecenění. Kopie `investra_test`: předvaha před a po upgradu shodná, všech 5 fondových knih
  má nové účty. SELECTy v `docs/sql/17-urok-rh-realizace.sql`.
