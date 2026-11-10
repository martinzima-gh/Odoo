# Příprava schůzky s Janem Polanem 11. 11. 2026

Podklad pro Martina Zímu. Schůzka ve středu 11. 11. 2026 ve 14:00, asi 90 minut. Navazuje na e-mail
Martina Zímy z 6. 11. (body 1 až 3) a na první přípravu `docs/priprava-schuzky-jan-polan.md`.
Jan Polan si připraví poznámky k bodům a poslal report porovnání Odoo 20 Community a Enterprise
z pohledu účetnictví (příloha zatím není v repozitáři).

## Co z jeho e-mailu plyne

- Doporučuje Claude Code a nabízí „supervizi“. Hodí se k otevřenému bodu nezávislé kontroly kódu psaného AI
  (revize R12 a R14); domluvit konkrétní formu.
- 6. 11. předpokládal Odoo 20 Enterprise bez modulů třetích stran. Shoduje se s doporučením
  v `docs/pruzkum/01-edice-hosting.md`, rozhodnuto ale není; rozhoduje se s Martinem Olivou do 20. 11.
- Odoo 20 dovolí zápis na bankovní účet jen z bankovní transakce. Návrh FX přecenění vzniká v deníku ostatních
  operací; u bankovních účtů ho Odoo 20 může odmítnout (neověřeno).

## Program

### 1. Kde jsme (5 min)

- Odoo 20 Community běží lokálně; prototyp fondových modulů (ocenění, třídy, úplaty, účetní události)
  se smyšlenými daty. Vývoj s Claude Code, AI agenti na drobné úkoly a kontrolu.
- Začíná se účetnictvím Investra Services, fondy potom.
- Prototyp lze ukázat na sdílené obrazovce; repozitář a dokumenty zatím neposílat (bod 6).

### 2. Edice a provoz (20 min)

- Co Community chybí pro s.r.o.: rozvaha, výsledovka, hlavní kniha, saldokonto, import a párování banky,
  přiznání DPH pro EPO. Pokryje to Enterprise na české osnově?
- Odoo.sh, nebo vlastní hosting? Kdo dělá zálohy, obnovu, nasazování verzí a sledování provozu?
- Odoo bude pravděpodobně kritická nebo důležitá funkce podle DORA. Umí to Odoo.sh smluvně
  (místa uložení dat, audit, odchod)?
- Lze získat zkušební Enterprise pro spuštění našich testů?
- Kolik uživatelů a společností počítat v prvním roce?

### 3. Česká lokalizace pro Services (20 min)

- Hotové vlastními moduly: kurzy ČNB a ECB, FX přecenění s účty po skupinách účtů, funkční měna EUR,
  DPH identifikované osoby u přijatých služeb.
- Chybí (priorita A v `docs/ceska-lokalizace.md`): faktury s českými náležitostmi, VS/KS/SS, formáty výpisů
  českých bank a platební příkazy, ARES, VIES, nespolehlivý plátce, souhrnné hlášení a přiznání DPH,
  vytěžení a schvalování přijatých faktur, import mezd jako účetního zápisu.
- Co z toho pokryje Enterprise, co by dělal on a s jakým odhadem?

### 4. Banka a FX přecenění v Odoo 20 (5 min)

- Jak přeceňovat cizoměnové bankovní účty, když ruční zápis na banku je omezený? Standardní přecenění Odoo,
  nebo jiný postup?

### 5. Audit log (10 min)

- Přihlášení a neoprávněné pokusy o přístup Odoo neloguje; Jan to dělal pro Partners. Požadavek DORA
  a bezpečnostních standardů.
- Rozsah, kam logy ukládat, jak dlouho, odhad pracnosti.

### 6. Vlastní moduly: zůstane naše práce při jiné edici nebo verzi Odoo? (15 min)

**Jak jsou moduly postavené** (ověřeno v kódu 10. 11. 2026):

- 14 vlastních modulů v `addons/custom/`, jádro Odoo se neupravuje, jen se na něj navazuje.
- Závislosti jen na standardních modulech dostupných i v Community (`account`, `mail`, `web`),
  žádná na Enterprise.
- Zásahy do standardního účetnictví jsou soustředěné hlavně v `investra_posting`: doklad (`account.move`:
  ochrana zaúčtování `_post`, zákaz změny a smazání, storno, hash), řádek dokladu (fondová pole),
  dále kurzy (`res.currency`) a šablona osnovy fondu. Při nové verzi Odoo jsou nejrizikovější.
- Kód je v gitu, přes 250 automatických testů ukáže po přechodu, co přestalo fungovat.

| Změna | Dopad na naše moduly |
|---|---|
| Community → Enterprise (stejná verze) | Enterprise je Community a placené moduly navíc; moduly by měly běžet beze změny. Otestovat, hlavně zaúčtování, zámky a hash; zatím běžely jen na Community |
| Enterprise → zpět na Community | Moduly běží dál, ztratí se funkce Enterprise. Podmínka: vlastní moduly nesmějí záviset na Enterprise; co ho potřebuje, dát do samostatného propojovacího modulu |
| Nová hlavní verze (21, 22…) | Moduly se musí převést: úprava kódu a skripty převodu dat. Převod standardních dat nabízí Odoo u Enterprise, úpravu vlastních modulů dělá vývojář (ověřit v podmínkách). Podpora Odoo kryje poslední 3 hlavní verze |
| Změna hostingu (vlastní ↔ Odoo.sh) | Moduly se nemění. Odoo Online vlastní moduly prakticky nedovolí |
| Odchod dodavatele | Práce zůstane, pokud je kód ve firemním repozitáři, s dokumentací a testy, a smlouva řeší práva ke kódu |

**Co práci chrání** (návrh, část už platí):

1. Firemní repozitář, ne u dodavatele. Smluvně licence nebo převod práv ke kódu včetně práva dalších úprav
   jinými osobami; formu ověřit s právníkem.
2. Moduly mají v manifestu licenci LGPL-3; pro interní použití nevadí. Před případným předáním třetím
   stranám rozhodnout o vlastní licenci. Kód z otevřených lokalizací pod AGPL (Data Dance, OCA) nepřebírat
   bez právního posouzení.
3. Žádné úpravy jádra Odoo (platí); zásahy do standardu v malém počtu modulů a zdokumentované.
4. Testy a CI při každé změně (CI je otevřený bod); při přechodu nejdřív testy na kopii databáze.
5. Pevná verze Odoo (platí); upgrade řízeně: plán, zkušební převod, porovnání NAV a rozvahy se starou
   verzí, ostrý přechod.

**Otázky:**

- Jak pracné je převedení vlastních modulů mezi hlavními verzemi, jaká je zkušenost z 19 → 20?
- Které naše zásahy do standardu (zaúčtování, hash, storno, kurzy) považuje za rizikové a jak je udělat
  bezpečněji?
- Upgrade přes službu Odoo, OpenUpgrade (nástroj OCA pro Community), nebo vlastní skripty?
- Jak často upgradovat a jak dlouho zůstat na jedné verzi?
- Souhlasí s firemním repozitářem a smluvními právy ke kódu?

Ověřeno v kódu: závislosti, licence, místa zásahů. Neověřeno: rozsah služby Odoo při upgradu vlastních modulů
a právní řešení práv ke kódu.

### 7. Spolupráce a supervize (15 min)

- Forma supervize: revize pull requestů, konzultace k architektuře, nebo kontrola po etapách?
  Kolik hodin měsíčně?
- Kapacita na 3 až 6 měsíců. Dubnový odhad NAV byl pro menší rozsah.
- Před přístupem do repozitáře: smlouva a mlčenlivost, zápis do evidence dodavatelů podle DORA,
  firemní repozitář.

### 8. Další kroky (5 min)

- Kdo dodá jaký podklad a do kdy.
- Brána rozhodnutí o edici a hostingu 20. 11. s Martinem Olivou.

## Na co si dát pozor

- Cenu ani termín nedomlouvat bez písemného zadání.
- Neslibovat fondové moduly; role Jana Polana zatím není rozhodnutá.
- Nesdílet důvěrné podklady, žádost o povolení ani interní podklady pro AI.
- Sledovat, zda odlišuje ověřené od předpokladu.

## Výstup po schůzce

Doporučení k edici a hostingu, rozsah české lokalizace a audit logu s odhady, forma supervize, pravidla
pro vlastní moduly a upgrade, další krok. Rozhodnutí zapsat do `docs/rozhodnuti.md` a Claude Doc.
