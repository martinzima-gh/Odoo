# Návrh: sdílené nástroje a pravidlo knihy

Stav 13. 11. 2026, připravil Claude k otevřenému bodu „Sdílené nástroje bez pravidla společnosti“.
Uživatel 13. 11. 2026 zvolil variantu B a plán schválil (odpovědi níže). **Naprogramováno 13. 11. 2026** (`investra_instruments` 0.14.0, `investra_nav` 0.24.0); interní kód a identifikátor nástroje bez ISIN doplněny podle odpovědí.
Červená zóna (pravidla přístupu, `record_guard`, údaje vstupující do NAV, migrace).

## Jak to funguje dnes (ověřeno v kódu a v `investra_test` 13. 11. 2026)

- `investra.instrument` nemá knihu ani pravidlo záznamu (`ir.rule`). Skupina Příprava ocenění smí číst, zakládat
  a měnit **každý** nástroj: sdílený (bez fondu) i nástroj jiného fondu (`fund_id` vyplněný).
- Smluvní peněžní toky (`investra.instrument.cashflow`) smí příprava kteréhokoli fondu zakládat, měnit i mazat.
  Změny toků se nikde nezaznamenávají (nejsou v chatteru).
- Po prvním obchodu je zamčený jen typ nástroje (`LOCKED_AFTER_TRADE = {"type_id"}`).
- Údaje nástroje, které vstupují do NAV jiného fondu: měna (16 míst v kódu), splatnost (8), toky (5), konvence dnů,
  sazba, metoda úročení (volba na nástroji má přednost před fondem), cena bez naběhlého úroku, maximální stáří ceny.
- `investra_test`: 8 nástrojů, všechny sdílené. 1 drží víc fondů, 6 jen jeden fond, 9 toků.
  **Kniha investiční společnosti tam není** (stejně jako u sdílených cen).
- Vzor: sdílené ceny (rozhodnutí 2026-11-11). Cena bez fondu patří knize investiční společnosti
  (`_shared_price_company`), pravidla jsou `cud`: vlastní kniha, `r`: sdílené nebo vlastní kniha.

## Riziko

Příprava fondu X změní tok, splatnost nebo měnu sdíleného nástroje. Naběhlý úrok a ocenění fondu Y se změní
bez upozornění a bez stopy. Totéž platí pro nástroj, který patří jen fondu Y.

## Návrh (varianta B)

1. **Kniha nástroje.** Nové uložené pole `company_id` („Kniha“): u nástroje fondu kniha fondu, u sdíleného
   kniha investiční společnosti. Nastaví se při založení, stejně jako u ceny. Nástroj dědí `investra.record.guard`
   s `_book_fields = ("fund_id", "company_id")`, takže ho nejde přesunout mezi fondy ani ze sdíleného na fondový.
2. **Pravidla záznamů** (stejně jako ceny):
   - `cud`: `company_id in company_ids`. Sdílený nástroj tedy mění jen uživatel s aktivní knihou investiční
     společnosti, nástroj fondu jen uživatel s knihou fondu.
   - `r`: sdílený nástroj nebo vlastní kniha. Nástroj jiného fondu přestane být vidět.
   - Toky nástroje: stejná pravidla přes `instrument_id.company_id`.
3. **Stopa změn.** Sledování (tracking) se doplní na pole vstupující do NAV (měna, splatnost, sazba, konvence dnů,
   metoda úročení, cena bez naběhlého úroku, maximální stáří ceny). Založení, změna a smazání toku se zapíše
   do chatteru nástroje (datum, druh, částka před a po).
4. **Kontrola ocenění** `instrument_changes` „Údaje nástrojů v portfoliu se od minulého ocenění nezměnily“
   (upozornění). Vypíše nástroje, které fond držel k minulému nebo k tomuto ocenění, se změnou údajů nebo toků
   po kontrolách minulého ocenění (`_since_previous`, stejně jako u kontroly matice): kdo, kdy, které pole.
   Platí pro sdílené i fondové nástroje.
5. **Migrace** `investra_instruments` 0.13.0 → 0.14.0: `company_id` = kniha fondu, jinak kniha investiční společnosti,
   jinak prázdné (viz otázka 2). `investra_nav` 0.23.0 → 0.24.0 (nová kontrola), bez migrace.
6. **Testy:** přístup (příprava fondu X nezmění sdílený nástroj ani nástroj fondu Y a nevidí ho; uživatel s knihou
   investiční společnosti sdílený nástroj změní), přesun mezi knihami, chatter toků, kontrola ocenění, migrace.
   Celá sada na čisté DB a pak `investra_test` se zálohou a porovnáním (doklady, součty MD/D, NAV, stavy ocenění).
7. Deník rozhodnutí, otevřené body, Claude Doc. Bod „Oddělení uživatelů podle fondů“ na tento plán navazuje.

## Otázky k rozhodnutí

1. **Kdo mění sdílený nástroj?**
   **(a) Doporučuji:** uživatel s aktivní knihou investiční společnosti, stejně jako u sdílené ceny. Jedno pravidlo
   „sdílené vede investiční společnost“, bez nové skupiny. (b) Nová skupina „Správa sdílených nástrojů“ nezávislá
   na knize. Je jednodušší pro testovací DB, ale jde o druhý pojem vedle knihy.
2. **Než vznikne kniha investiční společnosti:** sdílený nástroj nepůjde založit ani změnit („Založte nástroj
   fondu“), stejně jako sdílená cena. V `investra_test` by 7 sdílených nástrojů zůstalo jen ke čtení.
   **Doporučuji** po migraci založit v `investra_test` knihu investiční společnosti (testovací data, se zálohou
   a s vaším souhlasem) a nástroje na ni převést. Bez ní nejde v testovací DB vyzkoušet ani sdílené ceny.
3. **Skrýt nástroje jiných fondů při čtení?** **Doporučuji ano.** Je to začátek izolace knih. Ocenění a výkazy
   čtou přes `sudo`, takže výpočet se nezmění; ověří to testy.
4. **Zamknout po prvním obchodu i měnu nástroje?** Změna měny drženého nástroje přepočte pozice všech fondů.
   **Doporučuji ano** (`LOCKED_AFTER_TRADE` rozšířit o `currency_id`). Ostatní pole jen hlídat kontrolou z bodu 4,
   protože splatnost a toky se legitimně mění (prodloužení, mimořádná splátka).
5. **Závažnost kontroly `instrument_changes`:** **doporučuji upozornění.** Změna může být oprávněná a schvalovatel
   ji má vidět, ne být zablokován.

## Odpovědi uživatele 13. 11. 2026

1. Sdílený nástroj mění uživatel s knihou investiční společnosti. 2. V `investra_test` po záloze založit knihu
investiční společnosti a sdílené nástroje převést na ni. 3. Nástroje jiných fondů skrýt i při čtení.
4. Po prvním obchodu zamknout i měnu. 5. Kontrola `instrument_changes` je upozornění.
Navíc: **hlídat jedinečnost ISIN + měna a obojí musí být vyplněné.**

## Jedinečnost ISIN + měna (doplněno 13. 11. 2026)

Zjištěno v `investra_test`: duplicity 29/45 („Ukázkový dluhopis“, CZ0000000001, CZK) a 30/46 („Ukázková akcie“,
XS0000000001, EUR). Vznikly opakovaným spuštěním `tools/nav_demo` pro fondy 200 a 339 a každá kopie má obchody
s doklady. Bez ISIN jsou nástroje 466, 467 (dluhopisy) a 1561 (termínovaný vklad). Nástroj 5710 má ISIN „ISIN TEST TEST“.
Testovací ISINy nemají platnou kontrolní číslici. Typ „Ostatní podíl (fond bez ISIN)“ už v číselníku je.

Návrh:
- Typ nástroje dostane příznak „Vyžaduje ISIN“. Výchozí je zapnutý u akcií, dluhopisů a fondů, vypnutý u vkladů,
  úvěrů, rep, derivátů, účastí a ostatních podílů. Měna je povinná už dnes.
- ISIN se ukládá velkými písmeny bez mezer a kontroluje se formát a kontrolní číslice podle ISO 6166.
- Jedinečnost (ISIN, měna) hlídá omezení v databázi.
- **Nástroj s ISIN je vždy sdílený, nástroj bez ISIN musí mít fond.** Jinak by fondový nástroj s ISIN, který ostatní
  fondy nevidí, zablokoval založení téhož titulu jako sdíleného.
- Migrace data neopravuje sama. Když najde duplicitu, chybějící nebo neplatný ISIN, zastaví se se seznamem nástrojů.
- `tools/nav_demo` nástroj podle ISIN a měny najde, a teprve když neexistuje, založí ho. Testy dostanou platné fiktivní ISINy.
- Úprava `investra_test` před migrací (testovací data, se zálohou, přes ORM): 45 a 46 dostanou jiný platný fiktivní ISIN,
  sloučení obchodů s doklady se nedělá. 466, 467 a 5710 dostanou platný fiktivní ISIN. 1561 se stane nástrojem fondu 2931,
  jediného, který ho drží.

## Mimo rozsah

Schvalování změn nástroje čtyřma očima (případně později jako činnost matice), přidělení uživatelů ke knihám
(otevřený bod „Oddělení uživatelů podle fondů“) a typy nástrojů (mění je jen správce účetnictví už dnes).
