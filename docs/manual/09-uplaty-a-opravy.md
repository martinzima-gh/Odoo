# 9. Úplaty, odměna a daň v ocenění

*Ověřeno v kódu a průchodem na pracovní databázi přes ORM (18. 11. 2026, zkušební změny vrácené); v prohlížeči neověřeno.*

Kapitola navazuje na pravidla úplat fondu (kap. 2, záložka Úplaty) a na ocenění (kap. 4). Popisuje, z jakého základu se úplaty,
výkonnostní odměna a očekávaná daň počítají, jak je v ocenění ručně opravit a jak úplatu zrušit. Příklady jsou smyšlené.

## 1. Kroky výpočtu a volba Základ

Ocenění počítá úplaty, odměnu a daň ve čtyřech krocích. Každé pravidlo má volbu **Základ: po kroku**, tedy ze kterého stavu NAV k datu ocenění se počítá.

| Krok | Stav NAV po kroku |
|---|---|
| 1 | FK před úplatami a daní |
| 2 | po časově rozlišených a ručních úplatách a opravách (včetně této úplaty) |
| 3 | navíc po výkonnostní odměně |
| 4 | navíc po dani = výsledný (zveřejněný) FK |

Formulář pravidla ukazuje jen přípustné volby a popisky svého druhu (pole **Základ úplaty**, **Základ odměny**, **Základ daně**):

| Druh | Přípustné volby | Výchozí | Poznámka |
|---|---|---|---|
| Časově rozlišená úplata | 1, 2, 3, 4 | 1 | Ze základu **Aktiva** nebo **Bez základu** volba není (ukládá se 1). Pole **Základ** (zdroj: FK, průměrný FK, kapitál třídy, aktiva, bez základu) se zobrazuje jen u této úplaty. |
| Výkonnostní odměna | 1, 2, 4 | 2 | 1: k hodnotě třídy se přičtou úplaty i daň, které třída nesla od začátku období odměny; 2: přičte se jen daň; 4: zveřejněná hodnota. |
| Očekávaná daň | 1, 2, 3 | 3 | Které náklady snižují základ: 1 žádné, 2 úplaty, 3 úplaty i odměna. |

**Změna základu.** U průměrného FK, výkonnostní odměny a daně formulář při změně upozorní: „Změna se projeví i za dosavadní část roku nebo období
odměny; rozdíl se doúčtuje v dalším ocenění.“ U úplaty ze stavu k datu (FK, kapitál třídy) se změna projeví jen v dalších oceněních. Změna se zapíše
do historie pravidla jednou, jako změna pole „Základ: po kroku“.

**Vzájemný dopočet.** Když jsou pravidla navzájem základem (například úplata z výsledného FK a daň po úplatách), ocenění je spočítá společně
(„společný dopočet“) a výsledek se ustálí. Není to chyba. Kontrola ocenění „Společný dopočet úplat je konzistentní“ hlídá, že se výpočet ustálil.

**Pole bez účinku.** U druhu **Daň** formulář pole Platí třídy, Podíl příjemcům, Přijímají třídy a Nákladová role nemá: daň je náklad celého fondu,
účtuje se na roli Daň a mezi třídy ji rozdělí výpočet (poměr a přesun daňového efektu). Formulář pravidla upozorní, když vyplněné pole výpočet
nepoužije: Kapitál třídy bez tříd (počítá se z FK celého fondu), podíl příjemcům bez přijímajících tříd nebo přijímající třídy s podílem 0.

**Průměrný FK po třídách** (ZJ-14). Bez vyplněných Platí třídy je průměrný FK úplata celého fondu z průměru FK. S třídami se počítá za každou
třídu zvlášť z průměru jejího kapitálu (v měně fondu):

- nárok běží od nejpozdějšího z: 31. 12. minulého roku, prvního úpisu třídy, zařazení třídy do pravidla. Zařazení se pozná s přesností na ocenění:
  třída přidaná do pravidla po ocenění k 28. 2. se počítá od 28. 2.;
- body průměru jsou kapitály třídy ze zaúčtovaných ocenění v roce, kdy byla třída v pravidle, a dnešní hodnota třídy po zvoleném kroku; průměr prostý;
- pevné částky, minimum, maximum a příplatky se uplatní za každou třídu zvlášť (jako u Kapitálu třídy);
- ocenění zaúčtuje nárok minus to, co třída v roce z pravidla už nesla; ruční oprava částky platí trvale, oprava základu třídy do konce roku;
- přepnout pravidlo mezi celým fondem a třídami jde jen od začátku účetního období (nebo novým pravidlem), jinak se výpočet zastaví; třídu, která byla
  v roce z pravidla vyřazena a znovu zařazena, ocenění ukáže v kontrolách jako upozornění.

## 2. Schéma výpočtu na fondu

`Investra › Nastavení › Fondy › Fondy › [fond]`, záložka **Schéma výpočtu**:

- **Tabulka pravidel** fondu: název, druh, u úplaty zdroj základu a volba Základ (jen přípustné hodnoty druhu). Volbu jde měnit přímo v tabulce.
- **Předvolby** (obě s potvrzením, mění volbu u všech pravidel fondu):
  - **Standardní fond:** úplaty po kroku 1, odměna po kroku 2, daň po kroku 3.
  - **Úplaty z výsledného FK:** úplaty po kroku 4, daň po kroku 2, odměna zůstane. Úplaty a daň se pak počítají společně.
  Úplata ze základu Aktiva nebo Bez základu se předvolbou nemění.
- **Informace „Vzájemný dopočet“** (modrý pruh): vypíše pravidla, která se počítají společně.
- **Náhled s čísly:** stejná funkce jako ocenění na modelovém fondu: FK po kroku 1 1 000 000, aktuální sazby, výnos za rok +5 %.
  Náhled **nezahrnuje podíly příjemcům z tříd** a u pevných částek ukazuje roční částku, takže u malého modelového FK může vyjít záporný základ daně.
  Slouží k porovnání pořadí kroků, ne k odhadu skutečných částek.

## 3. Ruční oprava vypočtené částky

Vypočtenou úplatu, odměnu nebo daň opravíte v ocenění ve stavu **Návrh** nebo **Spočteno**: `Investra › Ocenění › [ocenění]`, záložka **Úplaty**,
tlačítko **Opravit** na řádku pravidla. Oprava je ruční úplata navázaná na pravidlo (vidíte ji i na záložce Ručně doložené úplaty); účtuje se na
nákladovou roli pravidla, s podílem příjemcům z tříd jako pravidlo.

**Okno Opravit:**

| Pole | Význam |
|---|---|
| **Opravuje úplatu**, **Třída** | pravidlo a třída řádku (jen pro čtení) |
| **Co opravuje** | **Částka** (oprava vypočtené částky) nebo **Základ** (oprava základu pravidla) |
| **Vypočteno** | vypočtená částka v okamžiku zadání (snímek) |
| **Rozdíl (oprava)** ⇄ **Cílová částka** | zadáte jedno, druhé se dopočte: cílová = vypočteno + rozdíl |
| **Vynulovat** | zkratka: cílová částka 0, rozdíl = −vypočteno |
| **Platnost** | jen odměna a daň: **Do konce období** (výchozí) nebo **Jen toto ocenění** |
| **Poznámka** | povinná, důvod opravy (faktura, dohoda s depozitářem) |
| **Soubor s výpočtem** | nepovinná příloha |

Po uložení stiskněte **Spočítat**. Záložka Úplaty má **jeden řádek na pravidlo** se sloupci **Vypočteno**, **Oprava částky** (součet oprav),
**Částka** (výsledek po opravách; pod sloupcem součet), **Zdůvodnění** (poznámky všech oprav), **Zadal** a **Kdy** (poslední oprava); v ocenění bez opravy
jsou sloupce oprav skryté. Samostatné řádky oprav jsou jen na záložce **Ručně doložené úplaty**, kde jde opravu smazat nebo upravit.

**Platnost podle druhu:**

- **Časově rozlišená úplata:** oprava je zaúčtovaná trvale (další ocenění ji neopakuje ani nedorovná; u průměrného FK se rozdíl nevrací).
- **Odměna a daň – Do konce období:** další ocenění v období (odměna od krystalizace, daň od začátku účetního období) opravu **převezme** do výpočtu.
  Krystalizace a konec roku převzetí ukončí.
- **Odměna a daň – Jen toto ocenění:** další ocenění opravu nepřevezme a upozorní „Opravy „jen toto ocenění“ z minulého ocenění skončily“.
- **Oprava základu** se přičte k základu pravidla. U daně je to ruční úprava základu (kladná = připočitatelná, záporná = odčitatelná), platí do konce roku.
  U průměrného FK upravuje celoroční průměr (po třídách průměr dané třídy) a platí do konce roku jako převzatá oprava. U úplaty z FK nebo kapitálu třídy platí jen pro toto ocenění
  a další ocenění upozorní „Oprava základu z minulého ocenění skončila“.

**Záporný výsledek opravy.** Když po opravě vyjde záporný stav pravidla (u úplaty částka řádku pravidla + opravy, u odměny naběhlá odměna, u daně
požadovaná daň), kontrola „Výsledek opravy … je záporný“ je **upozornění**; ocenění nezastaví. Záporný pohyb odměny nebo daně (rozpuštění, vrácení)
sám upozornění nevyvolá.

**Převzaté opravy.** Pod tabulkou záložky Úplaty je seznam **Převzaté opravy** (jen pro čtení): z ocenění, pravidlo, třída, co opravuje, částka,
platnost, poznámka. Kontrola „Obsahuje převzaté opravy (n)“ je upozornění. Tlačítko **Ukončit opravu** otevře okno s povinnou poznámkou a založí
opravu o opačnou částku s odkazem „Ukončuje opravu“; další ocenění ji už nepřevezme.

**Změna vypočtené částky po zadání opravy.** Když se po zadání opravy změní vstupy a vypočtená částka vyjde jinak, kontrola „Vypočtená částka opravených
úplat se od zadání opravy nezměnila“ je **stop** a ocenění nejde odeslat ke schválení. Na řádku opravy rozhodněte:

- **Ponechat rozdíl:** zadaný rozdíl zůstane, výsledek se posune s vypočtenou částkou;
- **Ponechat výsledek:** výsledek zůstane, rozdíl se upraví.

Tlačítka jsou na řádku pravidla a platí pro všechny jeho změněné opravy; uloží nový snímek vypočtené částky a ocenění jednou přepočtou. Kontrola platí jen pro opravy zadané v tomto ocenění, ne pro převzaté.

**Další verze ocenění.** Po vrácení vznikne nová verze bez ručních úplat a oprav předchozí verze. Kontrola „Předchozí verze měla ruční úpravy (n),
které v této verzi nejsou“ (upozornění) je vypíše; tlačítko **Převzít z předchozí verze** v hlavičce je zkopíruje (s odkazem „Převzato z“).
Když je vynecháváte záměrně, upozornění nechte být.

## 4. Jak úplatu zrušit

| Situace | Postup |
|---|---|
| Jen pro toto ocenění | **Opravit** → **Vynulovat** → poznámka → Spočítat. |
| Od určitého data | V pravidle nová **verze sazby 0 %** platná od data dalšího ocenění. Naběhlá odměna se tím rozpustí. |
| Pravidlo bylo založené omylem | **Archivovat** pravidlo. Odměnu nebo daň s naběhlou nebo zaúčtovanou částkou archivovat nejde: „Pravidlo … má z posledního ocenění … Archivované pravidlo by ji už nerozpustilo. Nejdřív nastavte verzi sazby 0 % od data dalšího ocenění, ocenění zaúčtujte a pravidlo archivujte potom.“ Pravidlo bez částky archivovat jde. |

## 5. Očekávaná daň a třídy – zjednodušení

Daň fondu je společná. Daňový efekt položek výsledku, které nese jen jedna třída (výkonnostní odměna, úplaty a ruční úplaty třídy, opravy), se
přesune té třídě přes vnitřní zúčtování; daň celého fondu se tím nemění. **Zjednodušení:** úspora z daňové ztráty minulých let se dělí mezi
třídy poměrem; ztráta se po třídách nesleduje. Přesuny se zaokrouhlují na haléře tak, aby zaúčtované přesuny třídy od začátku účetního období odpovídaly přesnému
součtu (rozdíl nejvýš 0,01): každé ocenění zaúčtuje zaokrouhlený přesný součet od začátku účetního období minus to, co už bylo zaúčtováno.

**Přemostění třídy** (formulář ocenění, řádek třídy, skupina Rozdělení výsledku; list Přemostění tříd v XLS) dělí specifickou změnu na **Úplaty třídy**,
**Výkonnostní odměna** (včetně oprav odměny), **Přesun podle pořadí nároků**, **Daňový efekt specifických položek** (tento přesun; + zvyšuje kapitál
třídy) a **Ostatní specifické**. Ocenění spočtená před verzí 38.0 mají daňový efekt 0 a přesun je v Ostatní specifické.

## 6. Balíček pro depozitáře, list Úplaty

Tlačítko **Balíček pro depozitáře** (po zaúčtování) sestaví XLS. List **Úplaty** má sloupce **Pravidlo**, **Třída**, **Základ** (krok), **Částka základu**,
**Částka** a **Článek statutu**; v ocenění s opravou navíc **Vypočteno**, **Oprava**, **Výsledek**, **Zdůvodnění** a **Převzato z / Ukončuje opravu**.
Hodnoty jsou ze snímku uloženého při výpočtu, ne z dnešního nastavení pravidla. Ocenění spočtená před zavedením volby Základ mají sloupec Základ
prázdný (u ocenění z doby voleb „před/po úplatách“ je převedený na krok). Už sestavené balíčky se nemění; nový sestaví nový soubor.

## 7. Daňová pravidla

Daňové pravidlo, výjimky fondu, rozpad daně a postup opravy jsou popsány v [kapitole 11 – Daň](11-dan.md). Daň se počítá od začátku
účetního období fondu podle nastavení jeho účetní knihy, ne automaticky od 1. ledna.
