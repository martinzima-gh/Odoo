# 8. První úpis a odkup; převzetí fondu

*Ověřeno v kódu, v prohlížeči neověřeno.*

Kapitola popisuje **pohyb kapitálu třídy**: úpis (investor vkládá peníze a získává kusy třídy) a odkup (investor vrací kusy a dostává peníze).
Navazuje na kap. 2–4 (fond, třídy, ocenění a matice) a kap. 7 (kurzy). **Převzetí fondu od jiného administrátora zatím v systému
neexistuje** – viz poslední oddíl.

## Zadávání pohybů

### Zdroj IS: jen kontrola a zaúčtování

Pokud úpisy a odkupy zpracovává **informační systém (IS)**, Odoo je jen kontroluje a účtuje.
Kusy, cenu, hrubou částku, poplatek a rozdíl ze zaokrouhlení kusů určuje IS; Odoo je přebírá beze změny.
Do napojení IS se pohyb zadává ručně (zdroj **Ruční zadání**, s povinným důvodem).

### Ruční zadání: formulář navrhne hodnoty

U zdroje **Ruční zadání** formulář při každé změně vstupních polí sám dopočítá závislé hodnoty –
uživatel je může přepsat. Po přepsání zůstane nová hodnota, dokud se nezmění vstup, který ji ovlivňuje.

| Situace | Co formulář navrhne |
|---|---|
| Výběr třídy a data | Cenu za kus ze zveřejněného ocenění fondu k datu; kurz z vyhlášeného kurzu (u třídy v cizí měně). |
| Úpis – zadání přijaté platby | Poplatek ze sazby třídy; kusy zaokrouhlené podle pravidla třídy; rozdíl ze zaokrouhlení. |
| Odkup – zadání kusů | Hrubou částku (kusy × cena), poplatek ze sazby, výplatu investorovi. |
| Třída bez sazby (0 %) | Poplatek 0,00 – lze zadat ručně; příjemce je pak povinný. |
| První úpis třídy (bez zveřejněného ocenění) | Cena se nepředvyplní; v poli Důvod odlišné ceny se objeví nápověda „První úpis třídy". |

Výpočetní pravidla jsou stejná jako kontroly před zaúčtováním – předvyplněný pohyb projde **Zaúčtovat** beze změny.

Vzorce pro součet:

- **Úpis:** hrubá částka (přijatá platba) = kusy × cena + poplatek + rozdíl ze zaokrouhlení + zbytek.
- **Odkup:** hrubá částka = kusy × cena + zbytek; výplata investorovi = hrubá částka − poplatek − rozdíl ze zaokrouhlení.
- Kusy × cena se zaokrouhlí na haléře matematicky. **Zbytek** je nesoulad dat do 0,01; větší nesoulad zaúčtování zastaví.

## Nabídka a práva

**Investra › Úpisy a odkupy.** Seznam je řazen od nejnovějšího data, stavy: **Nezaúčtováno**, **Zaúčtováno**, **Stornováno**.
Tlačítka **Zaúčtovat**, **Opravit** a **Stornovat** vidí jen skupina **Investra: příprava ocenění** (kap. 5; členství ve skupině schvalování
ocenění samo nestačí). Pohyb jiné společnosti, než kterou má uživatel zapnutou, systém při použití tlačítka odmítne („Pohyb patří jiné společnosti.“). Tlačítko Zaúčtovat se ukáže, až když je pohyb uložen.

## Formulář pohybu

Pole lze měnit jen ve stavu **Nezaúčtováno**. Zaúčtovaný pohyb nejde změnit ani smazat; opravuje se stornem (viz dále).

| Pole | Povinné | Význam |
|---|---|---|
| **Třída** | ano | Třída fondu. Z ní se doplní Fond a Měna kurzu. |
| **Typ** | ano | Úpis nebo Odkup. |
| **Zdroj** | ano | **Ruční zadání** (výchozí) nebo **IS**. |
| **Identifikátor z IS** | u zdroje IS | Dávka a řádek z IS; ve fondu jedinečný („Identifikátor z IS už ve fondu existuje.“). |
| **Důvod ručního zadání** | u ručního zadání | Bez důvodu: „Ruční zadání úpisu nebo odkupu vyžaduje důvod.“ |
| **Datum** | ano | Den pohybu; podle něj pohyb vstupuje do ocenění a podle něj se hledá kurz. |
| **Kusy** | ano | Kladné; nejvýše tolik desetinných míst, kolik má třída (kap. 3). |
| **Cena za kus** | pro zaúčtování | Cena v měně kurzu. Bez ceny pohyb nejde zaúčtovat („chybí cena za kus“). |
| **Hrubá částka v měně kurzu** | ano (nebo částka ve funkční měně) | Úpis: přijatá platba. Odkup: kusy × cena před poplatkem. |
| **Kurz** | ne | Funkční měna za jednotku měny třídy. Prázdný = vyhlášený kurz k Datu (kap. 7). U třídy ve funkční měně fondu se nepoužije. |
| **Hrubá částka ve funkční měně** | dopočte se | Při uložení = hrubá částka v měně kurzu × Kurz. |
| **Důvod odlišné ceny** | podle kontroly | Viz „Kontrola ceny“ níže. |
| **Poplatek** | ne | V měně kurzu. Při ručním zadání se předvyplní ze sazby třídy (vstupní u úpisu, výstupní u odkupu); lze přepsat. |
| **Poplatek podle sazby** | jen čtení | Hrubá částka × sazba třídy; slouží ke kontrole ocenění. |
| **Příjemce poplatku** | je-li poplatek | Předvyplní se z třídy: **Obhospodařovatel** a **Distributor** (závazek, platí se ven), **Fond – výnos** (výnos fondu, dělí se mezi třídy poměrem), **Třída – výnos**, **Třída – kapitál**. |
| **Příjemce (partner)** | ne | Kontakt příjemce u závazku. |
| **Rozdíl ze zaokrouhlení kusů** | ne | Rozdíl, který určil IS. |
| **Rozdíl patří** | předvyplní se | **Zůstává ve fondu** (kapitál třídy) nebo **Vrací se investorovi** (závazek, výplatu zadává IS). Výchozí je hodnota třídy. |
| **Kusy × cena**, **Zbytek**, **Výplata investorovi** (jen odkup), **Změna kapitálu třídy**, **Změna kapitálu v měně kurzu** | jen čtení | Výsledky výpočtu podle vzorců výše. Změna kapitálu třídy (ve funkční měně) je číslo, které vstupuje do ocenění. |
| **Opravuje pohyb**, **Ocenění s cenou**, **Účetní událost**, **Důvod storna** | jen čtení | Vyplní systém (oprava, zaúčtování, storno). |

## Zaúčtování

Záložka **Zaúčtování** ukazuje **náhled dokladu** ze stejné funkce, která účtuje; po zaúčtování tytéž skutečné doklady včetně storen.
Náhled vyžaduje cenu a vyplněné údaje (třída, typ, datum, kusy, částka).

Tlačítko **Zaúčtovat**:

1. Pohyb ze zdroje **Ruční zadání** projde schvalovací maticí, činnost „Ruční zadání úpisu a odkupu“ (kap. 4). Výchozí pravidlo je Příprava,
   jeden člověk – pohyb se zaúčtuje hned. Je-li v matici nastavena druhá osoba, vznikne žádost ke schválení a na formuláři se zobrazí
   upozornění „Čeká na potvrzení v Žádostech ke schválení“. Pohyb ze zdroje IS matici neprochází.
2. Kontroly před zaúčtováním (hlášky):
   - „Částky nesedí, zbytek … je větší než 0,01. Zkontrolujte data z IS.“
   - „Poplatek musí mít příjemce.“
   - **Úpis:** „Kusy … neodpovídají zaokrouhlení třídy (…)“ – kusy musí být (hrubá částka − poplatek) ÷ cena, zaokrouhlené podle třídy
     (dolů, matematicky, nahoru; kap. 3). **Odkup** tuto kontrolu nemá.
   - „Kusy mají víc než … desetinných míst třídy.“
   - Zámek ocenění: pokud je ocenění fondu od stavu Ke schválení do Potvrzeno depozitářem a jeho datum je stejné nebo pozdější než Datum pohybu,
     pohyb nejde zadat, změnit ani smazat; ocenění je nutné vrátit, nebo použít pozdější datum.
3. Vznikne účetní událost a doklady, pohyb dostane stav **Zaúčtováno**.

### Kontrola ceny

Cena se porovná s kurzem třídy z **posledního zveřejněného ocenění** fondu k Datu pohybu. Liší-li se, nebo žádné zveřejněné ocenění ještě
neexistuje, je nutné vyplnit **Důvod odlišné ceny**, jinak: „Cena … se liší od zveřejněného kurzu třídy (…). Uveďte důvod odlišné ceny.“
U **prvního úpisu do nového fondu** proto důvod vyplňte vždy (např. „První úpis, počáteční cena třídy“).

### Co doklad obsahuje

Úpis: banka (v měně kurzu, je-li jiná než funkční) proti kapitálu třídy; poplatek na vlastním řádku podle příjemce (závazek vůči příjemci,
výnos fondu, výnos třídy nebo kapitál třídy); rozdíl ze zaokrouhlení buď zůstává v kapitálu třídy, nebo je závazkem vůči investorovi;
zbytek do 0,01 jde na výnos nebo náklad ze zaokrouhlení. Odkup jde opačným směrem a banka se snižuje o výplatu (hrubá částka − poplatek − rozdíl).

## Vazba na ocenění

Do předběžného kapitálu a počtu kusů třídy vstupují všechny **nestornované** pohyby s datem v období ocenění (od předchozího ocenění
do data ocenění). Stornované pohyby nevstupují. Nezaúčtovaný pohyb ale ocenění nepustí dál (první kontrola níže), takže ke schválení se
dostanou jen zaúčtované. Kontroly ocenění (kap. 4):

Období prvního ocenění začíná Datem vzniku fondu; pohyb s Datem rovným datu vzniku do něj nevstoupí (počítají se pohyby s datem **po** začátku období).

- **Zastaví** předložení: v období je nezaúčtovaný pohyb („Úpisy a odkupy období jsou zaúčtované“). Nejdřív jej zaúčtujte.
- **Upozornění:** poplatek se liší od sazby třídy o víc než 0,01; pohyb má vyplněný Důvod odlišné ceny.

## Storno a oprava

Zaúčtovaný pohyb má tlačítka **Opravit** a **Stornovat**; obě otevřou okno s povinným **Důvodem** a textem „Co se stane“.

| Akce | Co se stane |
|---|---|
| **Stornovat** | Doklad pohybu se stornuje k datu pohybu. Pohyb dostane stav **Stornováno** a zobrazí Důvod storna. Do ocenění už nevstoupí. Žádný nový pohyb nevzniká. |
| **Opravit** | Totéž jako storno a navíc vznikne **nový pohyb v návrhu** (zdroj Ruční zadání, bez identifikátoru z IS, důvod „Oprava pohybu …: důvod“) s kopií údajů a odkazem **Opravuje pohyb**. Upravte chybné hodnoty a zaúčtujte. |

Oprava ani storno nevytváří opačný pohyb (odkup k úpisu). Obě akce jdou u každého pohybu, i z IS, přes matici činnosti „Ruční zadání úpisu
a odkupu“ (výchozí: Příprava, jeden člověk). Storno i oprava podléhají zámku ocenění stejně jako zadání pohybu.

**Příklad opravy.** Zaúčtovaný úpis měl cenu 100,00, správně měla být 101,00. Otevřete pohyb › **Opravit** › důvod „chybná cena“. Původní pohyb
je Stornován, vznikne nový návrh s odkazem na něj. Opravte Cenu a Hrubou částku (a kusy podle kontroly), případně Důvod odlišné ceny, a
zaúčtujte. Pokud je mezitím ocenění k tomuto datu uzamčeno, oprava ani storno neproběhnou, dokud ocenění nevrátíte.

## Příklad: první úpis do fondu

Fond **Alfa Růst** (CZK), třída **A** v CZK, 3 desetinná místa kusů, zaokrouhlení kusů dolů, vstupní poplatek 1,5 %, příjemce Obhospodařovatel
(kap. 2–3). Fond ještě nemá zveřejněné ocenění. Uživatel je ve skupině Investra: příprava ocenění. Datum vzniku fondu je 1. 1. 2027.

1. **Investra › Úpisy a odkupy › Nový.** Třída: Alfa Růst A; Typ: Úpis; Zdroj: Ruční zadání.
2. Datum 4. 1. 2027; Důvod ručního zadání: „První úpis, podklad z IS“.
3. Hrubá částka v měně kurzu: 1 000 000,00. Poplatek se předvyplní na 15 000,00 (1,5 %), příjemce Obhospodařovatel.
4. Cena za kus: 100,00. Kusy: (1 000 000 − 15 000) ÷ 100 = **9 850,000**.
5. Důvod odlišné ceny: „První úpis, počáteční cena třídy“ (zveřejněné ocenění ještě není).
6. Uložit. Zkontrolujte pole jen pro čtení: Kusy × cena 985 000,00; Zbytek 0,00; Změna kapitálu třídy 985 000,00. Záložka **Zaúčtování** ukáže
   náhled: banka 1 000 000 proti kapitálu třídy 985 000 a závazku vůči obhospodařovateli 15 000.
7. **Zaúčtovat.** Výchozí matice je Příprava, jeden člověk, takže se pohyb zaúčtuje hned (stav Zaúčtováno, vyplněná Účetní událost).
8. K datu prvního ocenění (kap. 4) se pohyb započte do kapitálu a kusů třídy; kontrola „Úpisy a odkupy období jsou zaúčtované“ projde.
   Poplatek odpovídá sazbě, takže upozornění na poplatek není. Důvod odlišné ceny vyvolá jen upozornění, ocenění nezastaví.

*Čísla jsou ukázková, bez vazby na skutečný fond.*

## Převzetí fondu od jiného administrátora

**Tato funkce zatím není hotová.** Je naplánována jako samostatná etapa (návrh: den přechodu, počáteční rozvaha, pozice po nástrojích
s pořizovací cenou a kurzem, třídy a počty podílů, poslední kurz, importní šablony a protokol o odsouhlasení; `docs/plan-dalsiho-vyvoje.md`,
etapa 2). Do jejího dokončení platí:

- **Úpis nepoužívejte jako počáteční stav.** Zaúčtuje peníze na bankovní účet proti kapitálu třídy, nezaloží pozice v nástrojích a nevytvoří
  historii kapitálu převzatého fondu.
- Převzatá historická ocenění brání pravidla pořadí ocenění (nové ocenění až po zveřejnění předchozího, kap. 4); řešení je otevřený bod.
- Postup převzetí proto před nasazením ostrého fondu vyžaduje rozhodnutí podle návrhu etapy; kapitola se doplní po jeho schválení a provedení.

## Příklad: vzorový úpis s přesným výpočtem

Třída **B** v CZK, 6 desetinných míst kusů, zaokrouhlení dolů, vstupní poplatek 1 %, zveřejněný kurz 1 036,6444 CZK/kus.

| Položka | Hodnota | Výpočet |
|---|---|---|
| Přijatá platba | 1 000 000,00 CZK | zadáno |
| Cena za kus | 1 036,6444 | předvyplněna ze zveřejněného kurzu |
| Poplatek (1 %) | 10 000,00 | 1 000 000 × 0,01 |
| Čistá platba | 990 000,00 | 1 000 000 − 10 000 |
| Kusy (dolů, 6 míst) | 955,004437 | 990 000 ÷ 1 036,6444, dolů na 6 míst |
| Kusy × cena | 990 000,00 | 955,004437 × 1 036,6444 (na haléře) |
| Rozdíl ze zaokrouhlení | 0,00 | 990 000 − 990 000 |
| Zbytek | 0,00 | (kontrola součtu) |

Všechny hodnoty formulář dopočítá automaticky; zbývá jen zadat Důvod ručního zadání a stisknout **Zaúčtovat**.

## Příklad: odkup podle kusů

Třída **B**, kurz 1 050,00 CZK, výstupní poplatek 1 %, investor vrací 100 kusů.

| Položka | Hodnota | Výpočet |
|---|---|---|
| Kusy | 100,000000 | zadáno |
| Cena za kus | 1 050,00 | předvyplněna |
| Hrubá částka | 105 000,00 | 100 × 1 050 |
| Poplatek (1 %) | 1 050,00 | 105 000 × 0,01 |
| Výplata investorovi | 103 950,00 | 105 000 − 1 050 |
| Zbytek | 0,00 | (kontrola součtu) |

*Čísla jsou ukázková, bez vazby na skutečný fond.*
