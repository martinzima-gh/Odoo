# Návrh: klasifikace IFRS 9 podle obchodního modelu fondu

Stav 11. 11. 2026, připravil Claude podle bodu 9 podkladu UX z 10. 11. 2026 a rozhodnutí 2026-11-09
„Klasifikace IFRS 9 podle fondu a obchodního modelu“ (krok A22 revize). **Varianta B zvolena uživatelem 11. 11. 2026
(odpovědi níže) a plán schválen týž den.**
Červená zóna: účtování obchodů, NAV, výkazy ČNB, `record_guard`, migrace.

**Bod 9 podkladu UX:** klasifikace IFRS 9 patří k obchodu, ne ke sdílenému nástroji.

**Cíl:** Kategorie IFRS 9, způsob ocenění a role účtu se určí podle obchodního modelu, ve kterém fond nástroj drží,
s platností od. Tentýž nástroj může mít v různých fondech různou klasifikaci a v jednom fondu může být jeden nákup
FVTPL a jiný FVOCI nebo v naběhlé hodnotě. Po prvním obchodu změní klasifikaci jen řízená reklasifikace.

## Účetní rámec

- Účetní jednotka: fond (podfond), který nástroj drží. Klasifikace se neřeší za investiční společnost ani napříč fondy.
- Rámec: zákon o účetnictví a vyhláška 501/2002 Sb., pro finanční nástroje IFRS 9 ve znění přijatém EU
  (nařízení Komise (EU) 2023/1803). Ustanovení vyhlášky, které na IFRS odkazuje, cituji až po ověření ve Sbírce.
- Opora v IFRS 9 (ověřit v aktuálním znění na EUR-Lex):
  - 4.1.1 až 4.1.4: klasifikace podle obchodního modelu a smluvních peněžních toků (test SPPI);
  - B4.1.2: obchodní model se určuje na úrovni skupin aktiv, jedna jednotka může mít víc obchodních modelů;
  - 4.1.5: určení do FVTPL při prvotním zachycení (eliminace účetního nesouladu);
  - 5.7.5: neodvolatelná volba FVOCI u kapitálových nástrojů při prvotním zachycení;
  - 4.4.1 a 5.6.1: reklasifikace jen dluhových aktiv při změně obchodního modelu, prospektivně ode dne reklasifikace.
- **Upozornění na změnu:** novela IFRS 9 a IFRS 7 „Klasifikace a oceňování finančních nástrojů“ (IASB, květen 2024,
  účinnost od 1. 1. 2026) mění test SPPI (např. prvky vázané na ESG). Převzetí do práva EU a číslo nařízení ověřím
  na EUR-Lex před naprogramováním testu SPPI.
- Vztah k § 196 ZISIF (aktiva fondu v reálné hodnotě) je otevřený bod „Naběhlá hodnota ve fondu“; tento plán ho nemění.

## Jak to funguje dnes

- `investra.instrument` (sdílený napříč fondy) nese `ifrs9_category`, `valuation_method`, `role_id` a `cnb_sheet`;
  typ nástroje je jen navrhuje. Po prvním obchodu jsou pole zamčená pro **všechny** fondy (`LOCKED_AFTER_TRADE`).
- `investra.trade` nemá klasifikaci; účtování bere `instrument.role_id`.
- Pozice fondu (`InvestraTrade._positions`) je jen po nástroji. Účetní hodnota v ocenění se čte z hlavní knihy
  filtrem nástroj + účet role (`valuation.py`, `_compute_portfolio`).
- Klasifikaci z nástroje čtou: ocenění portfolia, změna RH nevypořádaných obchodů, úročení a splátky
  (`instrument_accrual.py`), převod na výkazy ČNB (`cnb_map.py` filtruje `investra_instrument_id.ifrs9_category`),
  přehled fondů (`_positions`).

## Zjištěná rizika

1. **Dva fondy s různým modelem:** první obchod zamkne klasifikaci i pro fond, který nástroj ještě nedrží.
2. **Jeden fond, dva modely:** pozice po nástroji sečte kusy i účetní hodnotu FVTPL a naběhlé hodnoty dohromady.
3. **FVOCI se dnes tiše účtuje do výsledku:** ocenění portfolia přeceňuje každou pozici mimo naběhlou hodnotu na
   `gain_fair_value` / `loss_fair_value`; FVOCI zastaví jen změna RH nevypořádaných obchodů. Kapitál (OCI) ani recyklace
   nejsou naprogramované.
4. **Výkazy ČNB** (ROFO10_11, řádky 6, 8, 10, 11) třídí podle kategorie nástroje, takže by po přesunu ukazovaly špatně.

## Varianty

| | A: klasifikace na obchodu | **B: obchodní model fondu a zařazení nástroje** | C: B + volba na obchodu |
|---|---|---|---|
| Kde je klasifikace | každý nákup nese kategorii, způsob ocenění a roli | portfolio (obchodní model) fondu; pro nástroj v něm „zařazení“ s platností od; obchod nese portfolio | jako B; nákup může navíc nést určení (4.1.5, 5.7.5) a tvoří vlastní „los“ |
| IFRS 9 | obchodní model nikde zachycený; snadno vznikne nekonzistence nákupů | odpovídá B4.1.2 (model na úrovni skupiny aktiv) | nejpřesnější |
| Prodej | musí párovat konkrétní nákupy (FIFO po kategoriích) | prodej uvede portfolio, kusy se berou z něj | párování losů |
| Reklasifikace (4.4.1) | přepis klasifikace u každého obchodu | nová verze zařazení s platností od + účetní událost | jako B |
| Pracnost | střední, ale složité prodeje | střední (2 nové modely, nový rozměr v hlavní knize) | vysoká |

Zamítnuto předem: klasifikace jen na dvojici fond + nástroj (odporuje rozhodnutí 2026-11-09, jeden fond může mít obojí).

**Doporučení: varianta B.** Volbu 5.7.5 u akcie i určení 4.1.5 pokryje B tak, že fond založí samostatné portfolio
(např. „Strategické účasti – FVOCI“). Varianta C se dá doplnit později, pokud se objeví potřeba volby po jednotlivých nákupech.

## Návrh řešení (varianta B)

### Datový model

1. **`investra.fund.portfolio` – Obchodní model fondu (portfolio)**: fond, kód, název, obchodní model
   (`hold_to_collect` Držet pro inkaso, `hold_collect_sell` Držet pro inkaso i prodej, `other` Ostatní – řízení na reálnou
   hodnotu / obchodování), popis posouzení (text: kdo a proč model určil, B4.1.1), aktivní.
   Každý fond dostane při založení portfolio „Hlavní“ s modelem `other`. Obchodní model nejde po prvním obchodu změnit
   (změna = reklasifikace).
2. **`investra.portfolio.classification` – Zařazení nástroje**: portfolio, fond (related, uložené), nástroj, platnost od,
   platnost do (vyplní jen reklasifikace), kategorie IFRS 9, způsob ocenění, role účtu, test SPPI
   (Splněn / Nesplněn / Nehodnotí se – kapitálové nástroje a deriváty), určení (Žádné / FVTPL podle 4.1.5 / FVOCI podle 5.7.5),
   zdůvodnění. Bez schvalování čtyřma očima (odpověď 3); změny se sledují v historii záznamu (`mail.thread`).
   - Unikátnost: portfolio + nástroj + platnost od; platnosti stejného portfolia a nástroje se nepřekrývají.
   - Návrh hodnot při založení: z typu nástroje a obchodního modelu (tabulka níže); účetní může změnit, odchylka
     od návrhu je vidět stejně jako dnes u nástroje.
   - Po prvním obchodu jsou kategorie, způsob ocenění a role zamčené (přenos `LOCKED_AFTER_TRADE` z nástroje sem).
   - Kontroly: naběhlá hodnota ⇔ kategorie Naběhlá hodnota (jako dnes); naběhlá hodnota a FVOCI dluhu jen se SPPI Splněn;
     FVOCI kapitálového nástroje jen s určením 5.7.5; nástroj vyhrazený fondu (`instrument.fund_id`) jen v portfoliu tohoto fondu.
3. **`investra.trade`**: nové povinné pole `portfolio_id` (výchozí = jediné aktivní portfolio fondu) a vypočtené uložené
   `classification_id` = zařazení platné k datu sjednání. Obchod bez zařazení nejde zaúčtovat.
   `portfolio_id` patří do `BOOKED_TRADE_FIELDS`. Prodej nesmí z portfolia vzít víc kusů, než v něm k datu je.
4. **`account.move.line`**: nový rozměr `investra_classification_id` vedle `investra_instrument_id`, zahrnutý do
   integritního hashe a po zaúčtování neměnný (stejně jako nástroj).
5. **`investra.instrument`**: pole `ifrs9_category`, `valuation_method`, `role_id` se odstraní (odpověď 2), včetně
   jejich podílu na příznaku „Odchylka od návrhu typu“; `max_price_age` a ostatní vlastnosti nástroje zůstávají.
   `cnb_sheet` zůstává na nástroji (odpověď 6). Typ nástroje dál navrhuje hodnoty, nově pro zařazení.

Návrh kategorie podle obchodního modelu (jen výchozí hodnota, rozhoduje schválené zařazení):

| Druh v typu nástroje | Držet pro inkaso | Inkaso i prodej | Ostatní |
|---|---|---|---|
| Dluhopis, úvěr, vklad, repo (SPPI Splněn) | Naběhlá hodnota | FVOCI | FVTPL |
| Dluhový nástroj se SPPI Nesplněn | FVTPL | FVTPL | FVTPL |
| Akcie, fond, účast, ostatní podíl | FVTPL (FVOCI jen určením 5.7.5) | totéž | totéž |
| Derivát | FVTPL | FVTPL | FVTPL |

### Účtování a ocenění

- Obchod, vypořádání, úročení a splátky berou roli a způsob ocenění ze zařazení obchodu a na řádky dávají
  `investra_classification_id`.
- Pozice: `_positions` vrací klíč (nástroj, portfolio) → kusy; ocenění vezme zařazení platné k datu ocenění.
  Účetní hodnota se čte filtrem nástroj + portfolio zařazení + účet role. Řádek listu portfolio dostane portfolio
  a zařazení; v přehledu fondů a balíčku pro depozitáře se pozice ve dvou portfoliích ukážou jako dva řádky.
- Cena se nemění: sdílená tržní cena nebo cena fondu platí pro všechna portfolia fondu (rozhodnutí 2026-11-11).
- **FVOCI:** mimo rozsah tohoto plánu (odpověď 4). Účtování do OCI (kapitálový fond, recyklace u dluhu, úrok efektivní
  mírou do výsledku) i chování ocenění s pozicí FVOCI do té doby jsou v otevřených bodech. Tento plán dnešní chování
  nemění: změna RH pozice FVOCI jde dál do výsledku, změna RH nevypořádaného obchodu FVOCI dál zastaví.
- **Reklasifikace (4.4.1):** v tomto kroku jen ochrana: novou verzi zařazení s jinou kategorií po prvním obchodu
  systém odmítne s odkazem na budoucí řízený krok (rozhodnutí 2026-11-07 „Změna klasifikace“). Datum reklasifikace
  podle IFRS 9 je první den následujícího účetního období; samotný krok a jeho účtování budou samostatný plán.
- **Výkazy ČNB:** `investra.cnb.map` filtruje `investra_classification_id.ifrs9_category` místo kategorie nástroje.
  Řádky převodní tabulky se nemění.

### Uživatelské rozhraní

- Fond: záložka Obchodní modely (portfolia) se zařazeními nástrojů.
- Nástroj: místo klasifikace přehled „Zařazení ve fondech“ (jen čtení).
- Obchod: výběr portfolia, vedle zobrazená kategorie a způsob ocenění; upozornění, když zařazení chybí nebo není schválené.

## Dopad na data a účetnictví

- `investra_dev`: modul nástrojů nemá, nic se tam nemění.
- `investra_test`: migrace (schéma, souhlas uživatele): pro každý fond portfolio „Hlavní“ (`other`); pro každou dvojici
  fond + nástroj s obchodem zařazení s hodnotami z nástroje, platnost od prvního obchodu (zdůvodnění „migrace“);
  doplnění `portfolio_id` u obchodů a `investra_classification_id` u zaúčtovaných řádků. Zůstatky ani částky se nemění;
  doplňuje se jen rozměr.
- Očekávané hodnoty referenčních scénářů se nesmí změnit.
- Hash integrity: přidání pole do hashe se týká jen nových dokladů; u migrovaných dokladů ověřím, že kontrola integrity
  Odoo neselže (jinak pole do hashe zapojit jen pro doklady od data migrace).

## Testy (nad `investra_test`)

1. Tentýž nástroj: fond 1 FVTPL, fond 2 naběhlá hodnota; obě ocenění správně a nezávisle.
2. Jeden fond, dvě portfolia (FVTPL a naběhlá hodnota) s týmž dluhopisem: dvě pozice, oddělená účetní hodnota.
3. Prodej z portfolia nad počet kusů v něm → chyba; prodej z druhého portfolia nesníží první.
4. Obchod bez zařazení nejde zaúčtovat; nový fond má portfolio „Hlavní“ a obchod ho dostane jako výchozí.
5. Po prvním obchodu nejde změnit kategorii, způsob ocenění, roli ani obchodní model portfolia.
6. Nová verze zařazení s jinou kategorií po prvním obchodu je odmítnuta (reklasifikace zatím není).
7. Kontroly SPPI a určení 5.7.5; nástroj vyhrazený fondu nejde zařadit do cizího portfolia.
8. ČNB ROFO10_11 řádky 6, 8, 10, 11 podle kategorie zařazení.
9. Migrace: počty obchodů a řádků s doplněným rozměrem, součty zůstatků po nástrojích před a po beze změny.
10. Všech 328 stávajících testů projde (po úpravě testů, které dnes nastavují klasifikaci na nástroji).

## Odpovědi uživatele (11. 11. 2026)

1. Varianta B.
2. Pole klasifikace z nástroje odstranit.
3. Zařazení bez schvalování čtyřma očima.
4. FVOCI (účtování do OCI a chování ocenění do té doby) dát do otevřených bodů; mimo rozsah tohoto plánu.
5. Nový fond dostane portfolio „Hlavní“ s modelem Ostatní (FVTPL).
6. `cnb_sheet` (list ČNB) zůstává na nástroji. Je to kód listu položkového výkazu (DOFO31_11 Majetkové CP, DOFO31_12
   Dluhové CP, DOFO31_21/22 deriváty, RIS30_02 Přehled poskytnutých úvěrů, RIS33_13 bez ISIN); list určuje povaha nástroje,
   ne klasifikace (ověřeno v `docs/cnb/polozky-FOFI20261201.csv`). Podle klasifikace se vykazuje rozvaha ROFO10_11/12
   (řádky 6, 8, 9–11) a OCI v ROFO10_21/22 (řádky 34, 39) – ty bere převod ze zařazení. Sloupec „Ocenění reálnou
   hodnotou“ v DOFO31 (ukazatel EFO0244) nemá v SDAT popis; odloženo do otevřených bodů.

Plán schválen uživatelem 11. 11. 2026.

## Zóna a provedení

Červená zóna, provádí Claude po schválení plánu. Pořadí: modely a migrace → účtování obchodů a úročení → ocenění
a kontrola FVOCI → ČNB → UI → testy a porovnání referenčních scénářů → deník rozhodnutí, Claude Doc, export
`docs/architektura.md`, `docs/sql/` (SELECT na zařazení a pozice po portfoliích). Instalace a upgrade modulů
v `investra_test` jen se souhlasem uživatele.

## Provedení 2026-11-11

- Moduly: `investra_instruments` 20.0.0.4.0 (nové modely `investra.fund.portfolio`, `investra.portfolio.classification`,
  obchod s portfoliem, pole klasifikace z nástroje odstraněna), `investra_nav` 20.0.0.2.0 (ocenění, úročení a splátky
  po pozicích nástroj + portfolio), `investra_cnb` (kategorie ze zařazení). Ukázkové skripty `tools/nav_demo` upravené.
- Testy v `investra_test`: 342 testů modulů Investry, 0 chyb (dříve 328; nové v `test_classification.py`,
  dvě portfolia v ocenění v `test_accrual.py` a ve výkazu v `test_cnb_map.py`).
- Migrace `investra_test` (záloha před ní `zalohy/investra_test-2026-11-11-pred-klasifikaci.dump`): 6 fondů s portfoliem
  „Hlavní“, 7 zařazení (vklad ve fondu Delta v novém portfoliu „Držet pro inkaso“), 8 obchodů s portfoliem, 41 zaúčtovaných
  řádků s nástrojem dostalo zařazení. Počet řádků (41), součet (122 022 000,00) i zůstatky po nástrojích jsou před a po stejné.
- Ukázkové SELECTy `docs/sql/11-klasifikace.sql`; dotaz 2 v `docs/sql/04-typy-nastroju.sql` už nečte staré sloupce nástroje.

**Odchylky od plánu:**
1. Zařazení na řádku dokladu (`investra_classification_id`) **není v integritním hashi**. Všech 31 zaúčtovaných dokladů
   v `investra_test` už hash má; přidání pole by změnilo jejich přepočtený hash a kontrola integrity Odoo by selhala.
   Pole chrání zákaz změny po zaúčtování (stejně jako nástroj).
2. Návrh kategorie zařazení se určuje z druhu nástroje a obchodního modelu (tabulka výše); kategorie na typu nástroje se
   pro návrh nepoužívá (zůstává jako „typická“ informace). Dluhový nástroj s typem v naběhlé hodnotě mimo model Držet pro inkaso
   dostane návrh způsobu ocenění „Model nebo znalec“.
3. Řádky listu portfolio hotových ocenění migrace nedoplňuje (historický snímek); nová pole Obchodní model a Zařazení jsou u nich prázdná.
4. Pozice v ocenění se páruje s hlavní knihou přes portfolio zařazení (ne přes konkrétní verzi zařazení), aby vydržela budoucí reklasifikaci.
5. Staré sloupce `ifrs9_category`, `valuation_method`, `role_id` v tabulce `investra_instrument` Odoo nemaže; nečíst je.
6. Obchod fondu s více obchodními modely bez vybraného portfolia systém odmítne; s jediným portfoliem se doplní samo.

## Dodatek 2026-11-11: jen kombinace přípustné podle IFRS 9 (ke schválení)

Stav: plán, nic není naprogramované. Podnět: uživatel v UI vybral u akcie SPPI „Splněn“, určení 4.1.5 a naběhlou hodnotu.
Uživatel 11. 11. schválil směr (kategorie se počítá, model „Ostatní“ rozdělit, účasti jen FVTPL); podrobný plán níže ke schválení.

**Rozhodovací strom (citace neověřené, viz Ověření):**
1. Derivát → FVTPL.
2. Akcie a ostatní podíl → FVTPL; FVOCI jen volbou 5.7.5, a ne u nástroje drženého k obchodování.
3. Podílový list fondu (puttable podle IAS 32 16A–16D) → FVTPL, bez volby 5.7.5 a bez SPPI.
4. Účast → FVTPL (fondy účasti standardně nemají; IFRS 10.31 dceřiné podniky investiční jednotky povinně,
   IAS 28.18 přidružené podniky volbou). Konsolidace ani ekvivalence se v systému neřeší.
5. Dluh (dluhopis, úvěr, vklad, repo): model Držet pro inkaso / Inkaso i prodej + SPPI splněn → naběhlá hodnota / FVOCI;
   SPPI nesplněn nebo jiný model → FVTPL; určení 4.1.5 jen u dluhu se splněným SPPI v modelu Držet pro inkaso nebo Inkaso i prodej.

**Mezery dnešního stavu:** (1) dluh se splněným SPPI v modelu Držet pro inkaso jde uložit jako FVTPL bez určení;
(2) podílový list fondu dovolí volbu FVOCI; (3) volba FVOCI jde i u portfolia k obchodování (model Ostatní to nerozlišuje);
(4) určení 4.1.5 jde i tam, kde je nástroj ve FVTPL sám; (5) formulář nabízí SPPI, určení i kategorii volně;
(6) účast dovolí volbu FVOCI.

**Změny:**
- Obchodní model „Ostatní“ se rozdělí na „Řízení na reálnou hodnotu“ (`fair_value`) a „Obchodování“ (`trading`).
  Portfolio „Hlavní“ nového fondu i stávající portfolia `other` dostanou `fair_value`.
- Kategorie IFRS 9 v zařazení je vypočtená a uložená (druh nástroje, model, SPPI, určení), ručně ji zadat nejde.
- Kontroly: SPPI jen u dluhu, v modelech Držet pro inkaso a Inkaso i prodej povinně vyhodnocený; určení 4.1.5 jen u dluhu
  se splněným SPPI v těchto modelech; volba 5.7.5 jen u akcie a ostatního podílu mimo model Obchodování.
- Způsob ocenění: naběhlá hodnota se nastaví sama, jinak výběr z metod reálné hodnoty (jako dnes).
- Formulář: SPPI jen u dluhu, určení jen u dluhu, akcie a ostatního podílu; kategorie jen ke čtení.
- Migrace `investra_instruments` 20.0.0.5.0: `other` → `fair_value`; přepočet kategorie stávajících zařazení
  a porovnání s uloženou – při rozdílu se aktualizace zastaví (nic se tiše nemění). Stávající data v `investra_test`
  rozdíl mít nemají (6 × FVTPL v modelu Ostatní, 1 × vklad v naběhlé hodnotě se splněným SPPI). Skript 20.0.0.4.0
  se upraví, aby zakládal `fair_value`.
- Testy: každá mezera (1)–(6) vlastním testem; stávající testy s modelem `other` a se zadanou kategorií upravit.
- Dokumentace: deník, Claude Doc, export architektury, `docs/sql/11-klasifikace.sql` beze změny struktury.

**Ověření v IFRS (přijaté EU, nařízení (EU) 2023/1803) – potvrdí uživatel:**
- IFRS 9 4.1.2 a 4.1.2A: naběhlá hodnota a FVOCI jsou u dluhu se splněným SPPI v daném modelu povinné (ne volba),
  FVTPL jen určením 4.1.5.
- IFRS 9 4.1.5: určení jen při prvotním zachycení a jen k odstranění nebo významnému snížení účetního nesouladu.
- IFRS 9 5.7.5 a definice „držený k obchodování“ (příloha A): volba FVOCI je vyloučená u nástrojů k obchodování
  a u podmíněného protiplnění podle IFRS 3; volí se po jednotlivých investicích.
- IAS 32 (odst. 96C nebo obdobný) a závěr IFRIC 2017 k puttable nástrojům: podílový list fondu není pro volbu 5.7.5
  kapitálovým nástrojem a nesplní SPPI.
- IFRS 10.31 a IAS 28.18: dceřiné podniky investiční jednotky povinně FVTPL; přidružené podniky fondů FVTPL volbou.
- Novela IFRS 9/IFRS 7 (květen 2024, účinnost 1. 1. 2026): změna testu SPPI; převzetí do práva EU a číslo nařízení.

**Zóna:** červená (klasifikace, migrace), provede Claude po schválení; aktualizace modulů v `investra_test` se souhlasem.
Rozpracovaná verze modelu je mimo repozitář; do schválení se kód nemění.

### Odpovědi uživatele k dodatku (11. 11. 2026) a upřesněný návrh

Uživatel ověřil body 1–5 vůči IFRS přijatým EU (ANO; u podílových listů nejdřív posoudit IAS 32 u emitenta,
pak IFRS 9 a SPPI; výjimka IAS 32 pro puttable nástroje nezakládá volbu 5.7.5). Bod 6: novela „Amendments to the
Classification and Measurement of Financial Instruments“ převzata nařízením Komise (EU) 2025/1047 z 27. 5. 2025
(Úř. věst. L 28. 5. 2025), povinně od prvního účetního období začínajícího 1. 1. 2026 nebo později – ověřeno jen
ze sekundárního zdroje (OIC, https://www.fondazioneoic.eu/regolamento-ue-2025-1047-della-commissione-del-27-maggio-2025-che-adotta-modifiche-a-ifrs-9-e-ifrs-7/?lang=en);
EUR-Lex se nepodařilo načíst, dřívější použití neověřeno. Pokyn: pokračovat a v kódu oddělit (a)–(f) s doložitelným zdůvodněním.

Zařazení (`investra.portfolio.classification`) ponese odděleně:
- **(a) Povaha nástroje** `instrument_nature`: dluhový / kapitálový (IAS 32.11) / podílový list s právem odkupu nebo závazek
  emitenta (IAS 32 16A–16D) / derivát / účast. Výchozí z druhu typu; změna jen s posouzením `nature_note`.
- **(b) Test SPPI** `sppi` (splněn / nesplněn / nehodnotí se), `sppi_note` (povinné při hodnocení), `sppi_version`
  (IFRS 9 před novelou / ve znění (EU) 2025/1047; pro období od 1. 1. 2026 jen novela). Hodnotí se u dluhových
  nástrojů a podílových listů; v modelech Držet pro inkaso a Inkaso i prodej povinně.
- **(c) Obchodní model** z portfolia (`business_model`, posouzení `assessment`); „Ostatní“ rozděleno na
  Řízení na reálnou hodnotu a Obchodování.
- **(d) Povinná klasifikace** `mandatory_category` (vypočtená): dluh a podílový list se splněným SPPI → naběhlá hodnota
  (4.1.2) / FVOCI (4.1.2A), jinak FVTPL (4.1.4); kapitálový nástroj, derivát a účast → FVTPL.
- **(e) Určení / volba** `designation` + `designation_note` (povinné): 4.1.5 jen u povinné naběhlé hodnoty nebo FVOCI;
  5.7.5 jen u kapitálového nástroje mimo model Obchodování. Podílový list, účast a derivát volbu nemají.
- **(f) Výsledná kategorie** `ifrs9_category` (vypočtená) a **zdůvodnění** `classification_basis` (vypočtený a sledovaný
  text: povaha → SPPI → model → povinná klasifikace → určení → výsledek, s odkazy na odstavce a poznámkami účetní).
- Po prvním obchodu jsou (a), (b), (e) a jejich posouzení zamčené; změna = reklasifikace (zatím není).
- Migrace 20.0.0.5.0: `other` → `fair_value`; povaha z druhu typu; u splněného SPPI poznámka „převzato migrací, potvrdit“
  a znění podle data; přepočet kategorií a porovnání s uloženými – při rozdílu se aktualizace zastaví.
- Ruční úprava (dotaz uživatele 11. 11.): do prvního obchodu může uživatel ručně měnit povahu (s posouzením), SPPI,
  portfolio, určení, způsob ocenění i roli; kategorie se nezadává, plyne z těchto vstupů. Po prvním obchodu platí zámek
  (změna = reklasifikace, zatím není). Uživatel potvrdil, že tak to má zůstat.
- Ruční přepsání kategorie (rozhodnutí uživatele 11. 11.): pole „Ruční kategorie“ s povinným zdůvodněním; vypočtená
  kategorie zůstává uložená vedle (`computed_category`), zdůvodnění (f) přepsání označí jako odchylku od rozhodovacího
  stromu IFRS 9 a ocenění ukáže upozornění `classification_override`. Shodné s vypočtenou nejde; po prvním obchodu zamčené.
  Doporučení Clauda bylo přepsání nepřidávat (všechny přípustné výsledky jdou přes vstupy); rozhodl uživatel.

### Provedení dodatku 2026-11-11

- `investra_instruments` 20.0.0.5.0: zařazení s kroky (a)–(f), vypočtená povinná a výsledná kategorie, ruční přepsání
  se zdůvodněním, text „Zdůvodnění klasifikace“; modely Řízení na reálnou hodnotu a Obchodování; formulář po krocích.
  `investra_nav`: upozornění ocenění `classification_override`.
- Migrace `investra_test` (záloha `zalohy/investra_test-2026-11-11-pred-dodatkem-ifrs9.dump`): 5 portfolií `other` →
  `fair_value`, povaha u 7 zařazení, u vkladu SPPI s poznámkou „převzato migrací, potvrdit“ a zněním (EU) 2025/1047;
  kategorie všech 7 zařazení před a po stejné; 41 řádků dokladů, součet 122 022 000,00 beze změny.
- Testy: 351 testů modulů Investry v `investra_test`, 0 chyb (nové v `TestClassificationRules`, přepsání v `test_accrual.py`).
- Mezera 5 (formulář nabízí jen přípustné volby) je ověřená jen kontrolami při uložení a viditelností polí; v prohlížeči neprověřeno.
