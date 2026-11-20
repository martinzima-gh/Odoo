# 11. Daň

*Ověřeno v kódu; ověření formulářů v prohlížeči čeká na převzetí.*

Daňové pravidlo určuje druh základu, způsob výpočtu, sazbu a účty. Pravidla jsou společná pro fondy; použití se nastavuje u každého
fondu zvlášť. Výpočet se provádí v ocenění, na záložce **Úplaty**. Bez výchozího pravidla fondu se daň nepočítá a ocenění zobrazí
upozornění.

## Daňové pravidlo

V nabídce **Investra › Nastavení › Daně › Daňová pravidla** vytvořte pravidlo a jeho sazby:

| Pole | Význam |
|---|---|
| **Název** | Srozumitelný název pravidla. |
| **Aktivní** | Neaktivní pravidlo se nenabízí pro nová nastavení. |
| **Druh** | **Obecný základ**, **Samostatný základ** nebo **Mimo základ daně**. |
| **Způsob** | **Splatná – výsledek od začátku účetního období** nebo **Odložená – zůstatek k datu**. |
| **Účet daně** | Kód účtu daně v knize fondu; u odložené daně z OCI může jít o účet vlastního kapitálu. |
| **Rozvahový účet** | Kód účtu závazku či odložené daně v knize fondu. |
| **Započíst daň z účtu** | Volitelný účet zahraniční daně k zápočtu u splatného pravidla. |
| **Vykázat i pohledávku** | U odložené daně určuje, zda se vykáže také pohledávka. |
| **Sazby** | Řádky s poli **Platí od**, **Sazba** a **Předpis**. Sazba se zadává jako zlomek, například 0,21 pro 21 %. |
| **Poznámka** | Důvod a podklady pravidla. |

Pravidlo **Mimo základ daně** nemá sazby ani účty. Použité sazby se zpětně nemění; pro změnu založte novou verzi s novým datem
platnosti. Výběr sazby a účetního rámce musí odpovídat schválené daňové metodice fondu.

## Daň fondu a výjimky

Ve formuláři fondu otevřete záložku **Daň**:

- **Výchozí daňové pravidlo** platí pro výsledkové účty bez výjimky.
- **Aktuální sazba** se přebírá z právě platné verze pravidla.
- **Základ: po kroku** určuje, zda daň zohlední žádné úplaty, úplaty, nebo úplaty i výkonnostní odměnu. Účetní výjimka má přednost.
- Tabulka **Výjimky** přiřazuje účet k jinému pravidlu a případně jen k části jeho pohybu.

Pole tabulky jsou **Účet**, **Daňové pravidlo**, **Podíl**, **Neuznatelné náklady (% z výnosu)**, **Pohyb od začátku období**
a **Poznámka**. Neuznatelné náklady lze zadat pouze u výnosového účtu. Pohyb je od začátku účetního období fondu a zobrazuje
výnosy kladně (kredit = plus).

Tlačítko **Přidat běžné výjimky** doplní běžné výjimky pro dividendy, penále a reprezentaci; již nastavené výjimky nepřepíše.
Pokud fond používá FVOCI, doplní také výjimku pro odloženou daň z OCI a pro realizované přecenění akcií FVOCI. Tlačítko nepřidává
výjimku pro ECL.

Účet daně se nesmí zaměnit s výnosem nebo nákladem, který vstupuje do základu. Účty používaných daňových pravidel musí být v knize
fondu založené a přiřazené k odpovídajícím rolím. Opravu daně zadávejte přes ocenění; ruční doklad používejte jen pro případy mimo
výpočet.

## Rozpad daně a kontroly

Na ocenění otevřete **Úplaty**. Pod tabulkou pravidel se zobrazí **Rozpad daně**: pravidlo, základ, sazba, požadovaná daň,
zaúčtovaná daň a pohyb. U výchozího pravidla rozpad doplňuje vstupy ze začátku účetního období, výjimky, neuznatelné náklady,
volbu **Základ: po kroku** a opravy základu. U pravidla se zápočtem ukazuje částku zápočtu, použitou část a část, která propadá.
Rozpad je informativní; nic nepočítá ani neúčtuje.

Kontrola **Fond má výchozí daňové pravidlo** upozorní, pokud daň nelze počítat. Kontrola **Zápočet zahraniční daně je celý využitý**
upozorní na propadající část zápočtu. Tyto kontroly nejsou polem pro změnu nastavení; opravte nastavení fondu nebo podklady dividendy.

## FVOCI, odložená daň a ECL

U FVOCI se oceňovací rozdíl účtuje do vlastního kapitálu. Výjimka na účtu **Oceňovací rozdíly FVOCI** používá odložené pravidlo
a počítá kumulativní zůstatek k datu. Odložená daň se podle nastavení účtuje na účet vlastního kapitálu. Při prodeji akcie FVOCI se
realizované přecenění zahrne do základu splatné daně podle výjimky na účtu **Realizované přecenění FVOCI**. Jeho pohyb se počítá od
začátku účetního období. Zařazení daně z realizace do výsledku versus kapitálu je otevřená účetní otázka; ověřte schválenou metodiku.

ECL dluhu FVOCI se účtuje ručním dokladem. Doporučený daňový postup je výjimka nákladu **Opravné položky ECL** s pravidlem **Mimo
základ daně**; potvrďte ho s daňovým poradcem. Výpočet cílového zůstatku OCI tuto ruční opravnou položku nezahrnuje.

## Oprava vypočtené daně

V návrhu nebo spočteném ocenění otevřete záložku **Úplaty** a na řádku daně stiskněte **Opravit**. Zadejte opravu částky nebo základu,
platnost, povinnou **Poznámku** a případný soubor s výpočtem. **Daňové pravidlo** je výchozí pravidlo fondu; při opravě daně lze
vybrat pravidlo použité ve výjimce fondu. Poté ocenění znovu spočítejte a zkontrolujte rozpad daně i účetní náhled.

Daňové výpočty a zápočty se počítají od začátku účetního období, které má fond nastavené v účetní knize. Změna nastavení se projeví
dalším výpočtem; rozdíl se doúčtuje. Daňová ztráta minulých let se automaticky nepřenáší, případnou úpravu základu zadá uživatel podle
schváleného postupu.
