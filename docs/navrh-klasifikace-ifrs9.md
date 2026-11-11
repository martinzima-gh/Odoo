# Návrh: klasifikace IFRS 9 podle obchodního modelu fondu

Stav 11. 11. 2026, připravil Claude podle bodu 9 podkladu UX z 10. 11. 2026 a rozhodnutí 2026-11-09
„Klasifikace IFRS 9 podle fondu a obchodního modelu“ (krok A22 revize). **Ke schválení uživatelem. Nic není naprogramované.**
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
   zdůvodnění, stav Návrh → Schváleno (čtyři oči jako u cen, skupina schvalování ocenění).
   - Unikátnost: portfolio + nástroj + platnost od; platnosti stejného portfolia a nástroje se nepřekrývají.
   - Návrh hodnot při založení: z typu nástroje a obchodního modelu (tabulka níže); účetní může změnit, odchylka
     od návrhu je vidět stejně jako dnes u nástroje.
   - Po prvním obchodu jsou kategorie, způsob ocenění a role zamčené (přenos `LOCKED_AFTER_TRADE` z nástroje sem).
   - Kontroly: naběhlá hodnota ⇔ kategorie Naběhlá hodnota (jako dnes); naběhlá hodnota a FVOCI dluhu jen se SPPI Splněn;
     FVOCI kapitálového nástroje jen s určením 5.7.5; nástroj vyhrazený fondu (`instrument.fund_id`) jen v portfoliu tohoto fondu.
3. **`investra.trade`**: nové povinné pole `portfolio_id` (výchozí = jediné aktivní portfolio fondu) a vypočtené uložené
   `classification_id` = zařazení platné k datu sjednání. Obchod bez schváleného zařazení nejde zaúčtovat.
   `portfolio_id` patří do `BOOKED_TRADE_FIELDS`. Prodej nesmí z portfolia vzít víc kusů, než v něm k datu je.
4. **`account.move.line`**: nový rozměr `investra_classification_id` vedle `investra_instrument_id`, zahrnutý do
   integritního hashe a po zaúčtování neměnný (stejně jako nástroj).
5. **`investra.instrument`**: pole `ifrs9_category`, `valuation_method`, `role_id` se odstraní (otázka 2);
   `cnb_sheet`, `max_price_age` a ostatní vlastnosti nástroje zůstávají. Typ nástroje dál navrhuje hodnoty.

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
- **FVOCI:** dokud nebude naplánované účtování do OCI (kapitálový fond, recyklace u dluhu, úrok efektivní mírou do výsledku),
  ocenění s pozicí FVOCI **zastaví** kontrolou se závažností Stop. Dnešní tiché účtování do výsledku tím skončí.
- **Reklasifikace (4.4.1):** v tomto kroku jen ochrana: novou verzi zařazení s jinou kategorií po prvním obchodu
  systém odmítne s odkazem na budoucí řízený krok (rozhodnutí 2026-11-07 „Změna klasifikace“). Datum reklasifikace
  podle IFRS 9 je první den následujícího účetního období; samotný krok a jeho účtování budou samostatný plán.
- **Výkazy ČNB:** `investra.cnb.map` filtruje `investra_classification_id.ifrs9_category` místo kategorie nástroje.
  Řádky převodní tabulky se nemění.

### Uživatelské rozhraní

- Fond: záložka Obchodní modely (portfolia) se zařazeními nástrojů.
- Nástroj: místo klasifikace přehled „Zařazení ve fondech“ (jen čtení).
- Obchod: výběr portfolia, vedle zobrazená kategorie a způsob ocenění; upozornění, když zařazení chybí nebo není schválené.
- Seznam zařazení ke schválení (jako u cen).

## Dopad na data a účetnictví

- `investra_dev`: modul nástrojů nemá, nic se tam nemění.
- `investra_test`: migrace (schéma, souhlas uživatele): pro každý fond portfolio „Hlavní“ (`other`); pro každou dvojici
  fond + nástroj s obchodem zařazení s hodnotami z nástroje, platnost od prvního obchodu, stav Schváleno
  (schválil „migrace“, uvedeno v zdůvodnění); doplnění `portfolio_id` u obchodů a `investra_classification_id`
  u zaúčtovaných řádků. Zůstatky ani částky se nemění; doplňuje se jen rozměr.
- Očekávané hodnoty referenčních scénářů se nesmí změnit. Výjimka: scénář s pozicí FVOCI by nově zastavil; pokud
  takový je, ukážu ho před změnou.
- Hash integrity: přidání pole do hashe se týká jen nových dokladů; u migrovaných dokladů ověřím, že kontrola integrity
  Odoo neselže (jinak pole do hashe zapojit jen pro doklady od data migrace).

## Testy (nad `investra_test`)

1. Tentýž nástroj: fond 1 FVTPL, fond 2 naběhlá hodnota; obě ocenění správně a nezávisle.
2. Jeden fond, dvě portfolia (FVTPL a naběhlá hodnota) s týmž dluhopisem: dvě pozice, oddělená účetní hodnota.
3. Prodej z portfolia nad počet kusů v něm → chyba; prodej z druhého portfolia nesníží první.
4. Obchod bez schváleného zařazení nejde zaúčtovat; zadavatel nemůže schválit vlastní zařazení.
5. Po prvním obchodu nejde změnit kategorii, způsob ocenění, roli ani obchodní model portfolia.
6. Pozice FVOCI → ocenění zastaví kontrola Stop.
7. Kontroly SPPI a určení 5.7.5; nástroj vyhrazený fondu nejde zařadit do cizího portfolia.
8. ČNB ROFO10_11 řádky 6, 8, 10, 11 podle kategorie zařazení.
9. Migrace: počty obchodů a řádků s doplněným rozměrem, součty zůstatků po nástrojích před a po beze změny.
10. Všech 328 stávajících testů projde (po úpravě testů, které dnes nastavují klasifikaci na nástroji).

## Otázky pro uživatele

1. Souhlasíte s variantou B (portfolio s obchodním modelem + zařazení nástroje), nebo chcete A či C?
2. Pole klasifikace na nástroji **odstranit** (doporučuji; jinak hrozí, že je někdo bude brát jako platné), nebo nechat
   jako „navržené“ hodnoty mezi typem a zařazením?
3. Má zařazení procházet schválením čtyřma očima jako ceny? (Doporučuji ano: má přímý účetní dopad.)
4. Pozice FVOCI do doby naprogramování OCI: **zastavit ocenění** (doporučuji), nebo jen upozornit?
5. Výchozí portfolio nového fondu „Hlavní“ s modelem Ostatní (FVTPL) – vyhovuje, nebo má fond portfolio zakládat vždy ručně?
6. `cnb_sheet` (list ČNB) nechat na nástroji? Pokud se list liší podle kategorie, přesune se do zařazení.

## Zóna a provedení

Červená zóna, provádí Claude po schválení plánu. Pořadí: modely a migrace → účtování obchodů a úročení → ocenění
a kontrola FVOCI → ČNB → UI → testy a porovnání referenčních scénářů → deník rozhodnutí, Claude Doc, export
`docs/architektura.md`, `docs/sql/` (SELECT na zařazení a pozice po portfoliích). Instalace a upgrade modulů
v `investra_test` jen se souhlasem uživatele.
