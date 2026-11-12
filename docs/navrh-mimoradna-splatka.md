# Návrh: mimořádná splátka nástroje v naběhlé hodnotě

Stav: **druhy 1 a 2 schváleny a provedeny 12. 11. 2026** (`investra_nav` 0.11.0); druh 3 otevřený. Zóna: červená (účtování, ocenění). Navazuje na `docs/navrh-splatky-jistiny.md`
(rozhodnutí 4: přepočet EIR zatím neřešit) a otevřený bod „Mimořádná splátka v naběhlé hodnotě“.

**Citace IFRS a IAS nejsou ověřené** – EUR-Lex (nařízení (EU) 2023/1803) automatické čtení odmítl (12. 11. 2026).
Před schválením ověřit znění a výklad s auditorem: IFRS 9 odst. B5.4.6 (změna odhadu toků, přepočet původní EIR,
rozdíl do výsledku), 5.4.3 (modifikace), 3.2.2 (odúčtování části aktiva), IAS 1 odst. 82(aa) (zisk/ztráta
z odúčtování aktiv v naběhlé hodnotě samostatně).

## Jak to je dnes

- Naběhlá hodnota = současná hodnota zbývajících toků kalendáře při EIR spočtené z obchodu a kalendáře
  (`_accrued_value`). EIR se **neukládá** – každá změna kalendáře by ji zpětně změnila.
- Splátka jistiny snižuje kusy; ocenění doúčtuje rozdíl účetní a požadované hodnoty (u naběhlé hodnoty do úrokových výnosů),
  pozici bez kusů se zůstatkem doúčtuje na nulu.
- Server přijme jen jistinu splatnou podle kalendáře do data splátky.
- Reálná hodnota mimořádnou splátku už umí (kusy se sníží, ocení se zbytek cenou).

## Tři situace z praxe

| Situace | Příklad | Návrh |
|---|---|---|
| **1. Předčasné ukončení** celé pozice | Vklad vypovězen před splatností, banka vyplatí jistinu a krácený úrok | Splátka celé zbývající jistiny se povolí; pozice zmizí, ocenění doúčtuje zbytek naběhlé hodnoty |
| **2. Částečná mimořádná splátka, toky se poměrně sníží** | Dlužník splatí část úvěru, zbylé splátky se úměrně sníží | Koeficient zbývající jistiny: požadovaná hodnota = naběhlá hodnota podle kalendáře × (skutečná zbývající jistina / zbývající jistina podle kalendáře); původní EIR beze změny |
| **3. Nový splátkový kalendář** | Splátka zkrátí splatnost, banka vydá nový rozpis | Nový kalendář platný od data splátky, původní EIR uložená u obchodu, rozdíl (catch-up) do výsledku |

### 1. Předčasné ukončení (doporučeno hned)

- Na splátce volba **Druh: Podle kalendáře / Předčasné ukončení**. Předčasné ukončení musí splatit celou zbývající jistinu.
- Účtování: MD 119100 / D nástroj (jistina + vyplacený úrok); pozice nemá kusy, ocenění doúčtuje zbývající účetní hodnotu.
- Ilustrace (zaokrouhleno, vklad 5 000 000 od 15. 9. do 15. 12., úrok 45 500): k 12. 11. naběhlo cca 29 000.
  Banka vyplatí 5 000 000 + krácený úrok 10 000 → MD 119100 5 010 000 / D 132000 5 010 000; na 132000 zbude cca 19 000,
  ocenění ho odúčtuje proti výsledku.
- **K rozhodnutí:** zbytek do úrokových výnosů (jako dnes), nebo samostatně jako ztráta z odúčtování (IAS 1 82(aa),
  neověřeno) – nový účet a role, mapování ČNB (VYFO) potvrdí metodik.

### 2. Poměrné snížení (doporučeno hned)

- Druh **Mimořádná – poměrné snížení**: jistina smí být vyšší než splatná podle kalendáře (do zbývající jistiny).
- Ocenění: naběhlá hodnota z původního kalendáře a původní EIR, vynásobená koeficientem zbývající jistiny. Odpovídá
  smlouvě, kde se zbylé toky úměrně sníží; EIR zůstává původní, takže catch-up vzniká jen z rozdílu vyplaceného úroku
  a případného poplatku.
- Poplatek za předčasné splacení: třetí složka splátky (výnos), nebo součást rozdílu doúčtovaného oceněním – k rozhodnutí.

### 3. Nový kalendář (později, až bude první takový úvěr)

- Kalendář s platností od data (verze), EIR uložená u obchodu při pořízení; naběhlá hodnota = PV nových toků při původní EIR.
- Rozdíl při změně kalendáře doúčtuje ocenění (catch-up). Podstatná změna podmínek může být modifikace nebo odúčtování
  (IFRS 9 5.4.3, 3.2.3 – neověřeno) – posoudit s auditorem případ od případu.

## Doporučení

1. Hned: druhy 1 a 2 (bez ukládání EIR, změna jen ve splátce a v `_accrued_value` – koeficient).
2. Později: druh 3 s uložením EIR u obchodu a verzováním kalendáře.
3. Ověřit citace a prezentaci zbytku (úrok vs. samostatný řádek) s auditorem a metodikem ČNB výkazů.

## Otázky k rozhodnutí

1. Provést druhy 1 a 2 hned?
2. Zbytek při předčasném ukončení do úrokových výnosů, nebo samostatný účet „zisk/ztráta z odúčtování“?
3. Poplatek za předčasné splacení jako samostatná složka splátky?

## Rozhodnutí uživatele 12. 11. 2026

1. Druhy 1 (předčasné ukončení) a 2 (poměrné snížení) provést hned – provedeno.
2. Zbytek při předčasném ukončení zatím do úrokových výnosů (samostatný řádek podle IAS 1 82(aa) ověřit s auditorem).
3. Poplatek jako samostatná složka splátky mezi poplatky: náklad fondu na bankovní poplatky (612000), o který je výplata
   na inkasa na cestě nižší. Poplatek, který by fondu platila protistrana (výnos), zatím nemá roli – otevřený bod.

## Provedení

- Splátka: pole Druh a Poplatek; výplata = jistina + úrok − poplatek. Zaúčtování MD 119100 výplata, MD 612000 poplatek,
  D nástroj jistina a úrok.
- Poměrné snížení: koeficient Π (zbývající jistina − splátka) / zbývající jistina násobí kusy obchodů v `_accrued_value`;
  kontrola splátky podle kalendáře: po splátce musí zůstat koeficient × kalendářem nesplatná jistina; předvyplnění stejně.
- Předčasné ukončení: pozice zmizí z `_holdings` bez ohledu na zadanou jistinu (diskont, krácený úrok); zbytek doúčtuje
  ocenění jako u splacené pozice.
- Testy: čistá DB, 460 testů (všechny moduly), nové testy splátek 38/38.

## Úprava 12. 11. 2026: jeden druh Mimořádná

Druhy „Mimořádná – poměrné snížení“ a „Předčasné ukončení“ sloučeny (rozhodl uživatel): druh **Mimořádná** se zaškrtávátkem
**Uzavírá pozici**. Zaškrtne se samo, když jistina pokryje zbývající jistinu; při nižší jistině se zruší a splátka je
poměrné snížení. Ručně se zaškrtne jen u diskontu nebo vyrovnání – formulář pak ukáže neuhrazenou jistinu, kterou ocenění
odúčtuje do výsledku. Migrace `investra_nav` 0.12.0 převede staré druhy. Testy na čisté DB: `investra_nav` 237, 0 chyb.
