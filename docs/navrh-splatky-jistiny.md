# Návrh: splátky jistiny nástrojů – jeden mechanismus pro naběhlou i reálnou hodnotu

Stav: **návrh ke schválení** (12. 11. 2026). Zóna: červená (účtování, ocenění, NAV). Navazuje na rozhodnutí
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
- Úrok: D nástroj (naběhlá hodnota obsahuje naběhlý úrok) – u reálné hodnoty D úrokové výnosy, nebo nástroj, pokud cena
  je „dirty“. **Otázka k rozhodnutí:** zadávají se ceny vkladů a úvěrů v RH s naběhlým úrokem, nebo bez něj?
- Rozdíl proti očekávání doúčtuje ocenění jako dnes (naběhlá hodnota → úrokové výnosy; RH → přecenění).

## D. Naběhlá hodnota (EIR)

- **Splátka podle kalendáře:** kalendář už splátku obsahuje; kusy se nesnižují znovu. Proto v B1 splátka jistiny podle
  kalendáře **nesnižuje kusy**, jen uzavírá tok kalendáře (vazba splátka → tok kalendáře). Kusy snižuje jen **mimořádná**
  splátka mimo kalendář.
- **Mimořádná / předčasná splátka:** změna očekávaných toků; IFRS 9 řeší přepočtem naběhlé hodnoty původní EIR a rozdílem do
  výsledku (odst. 5.4.3 a B5.4.6 – **citace ověřit v EUR-Lex, výklad potvrdit s auditorem**). Návrh pro prototyp:
  mimořádná splátka sníží kusy, zbylé toky se přepočtou poměrně, EIR zůstává původní; rozdíl doúčtuje ocenění.
- Otevřený bod: úvěr s více splátkami a změnou sazby (již v otevřených bodech „Naběhlá hodnota ve fondu“).

## E. Reálná hodnota

Splátka jistiny = odúčtování části pozice podle pravidla „Částečný prodej“ v architektuře: poměrná část pořizovací ceny,
přecenění a kurzového rozdílu; u FVTPL realizovaný výsledek. Ocenění pak oceňuje jen zbývající kusy.

## F. Výběr pozice a kontroly

- Formulář: Fond, Datum, **Pozice** (nástroj – model) z pozic držených k datu; model se nezadává, převezme se z pozice.
  Pokud fond drží nástroj ve dvou modelech, nabídnou se dvě pozice.
- Server: pozice musí být k datu držená; jistina ≤ zbývající jistina (kusy) k datu; součet složek = částka. Kontrola i při
  importu a opravě (`copy`).
- Zámek ocenění, storno a oprava zůstávají (rozhodnutí 2026-11-12); storno vrací kusy.

## G. Migrace a navazující změny

- Stávající splátky: protiúčet zůstane banka (zaúčtované doklady se nemění); nové splátky jdou na 119100.
- `action_generate_schedule`: kalendář na jednotku jistiny; blokace po první nestornované splátce zůstává.
- Nová verze `investra_nav` (a `investra_chart_fund` / `investra_fund` pro novou roli), testy na čisté DB, upgrade
  `investra_test` jen se souhlasem a zálohou.

## Otázky k rozhodnutí

1. Protiúčet 119100 s novou rolí (doporučeno), nebo 119000?
2. Zbývající jistina variantou B1 (kusy = jistina, doporučeno)?
3. Ceny vkladů a úvěrů v reálné hodnotě s naběhlým úrokem, nebo bez?
4. Mimořádná splátka v naběhlé hodnotě podle bodu D jako prototyp s otevřeným bodem k auditorovi?
5. Stávající obchod s vkladem v `investra_test` převést migrací, nebo zadat znovu?
