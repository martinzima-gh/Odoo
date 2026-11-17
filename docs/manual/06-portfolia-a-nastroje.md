# 6. Portfolia a nástroje

*Ověřeno v kódu, v prohlížeči neověřeno.*

Portfolio zde znamená obchodní model fondu podle IFRS 9. Určuje zařazení nástrojů ve fondu; nejde o další účetní knihu. Nový fond automaticky dostane portfolio **Hlavní** s obchodním modelem **Řízení na reálnou hodnotu**.

## Portfolio fondu

**Investra › Portfolio › Obchodní modely**, případně záložka **Obchodní modely** ve formuláři fondu.

| Pole | Povinné / výchozí | Význam |
|---|---|---|
| **Fond** | ano | Fond, kterému portfolio náleží. |
| **Název** | ano | Název portfolia; ve fondu musí být jedinečný. |
| **Obchodní model** | ano / **Řízení na reálnou hodnotu** | Řízení na reálnou hodnotu, Držet pro inkaso, Držet pro inkaso i prodej nebo Obchodování. |
| **Posouzení modelu** | ne | Záznam, kdo a proč obchodní model určil; vyplňte podle účetního posouzení. |

V seznamu portfolií se navíc zobrazuje **Pořadí** (přesouvá se úchytem). V kartě portfolia je i seznam **Zařazení nástrojů**; vlastní formulář zařazení popisuje níže. Po prvním obchodu nelze **Obchodní model** portfolia změnit, protože změna je reklasifikace, která zatím není podporovaná. Portfolio s obchody nelze smazat.

## Nástroje

**Investra › Nastavení › Nástroje › Nástroje**. Nástroj s ISIN je sdílený napříč fondy a patří do knihy investiční společnosti (po jejím založení). Nástroj bez ISIN patří jednomu fondu; po založení je jeho fond pevný. Měnu a typ po prvním obchodu nelze změnit.

### Identifikace a ocenění

| Pole | Povinné / zobrazení | Význam |
|---|---|---|
| **Název** | ano | Název nástroje. |
| **Typ** | ano | Typ nástroje určuje jeho skupinu, druh a výchozí návrhy pro klasifikaci. Typy spravuje nabídka **Typy nástrojů**. |
| **ISIN** | podle typu | Pokud typ ISIN vyžaduje, musí se vyplnit. Nástroj s ISIN je sdílený pro všechny fondy. |
| **Měna** | ano | Měna nástroje; po prvním obchodu neměnná. |
| **Emitent** | ne; podle BA0088 může být nutný | Odkaz na kontakt emitenta, jehož identifikační údaje se udržují v **Emitenti a protistrany**. |
| **Kód** | systémový, jen pro čtení | Přidělí systém při založení. |
| **Skupina** | odvozená | Skupina určená z Typu. |
| **Druh identifikátoru**, **Identifikátor** | povinné bez ISIN | Druh může být Číslo smlouvy, IČO nebo LEI společnosti, Reference obchodu nebo Jiný. |
| **Fond** | povinný bez ISIN | Vyplní se jen u nástroje bez ISIN; po uložení se nemění. |
| **Kniha** | jen pro čtení; zobrazení dle více společností | Kniha, do které nástroj patří. |
| **Trh** | pro skupinu Kótované | Název trhu. |
| **Protistrana** | pro Peněžní trh, Úvěry a Deriváty | Kontakt protistrany. |
| **Kolaterál** | pro Peněžní trh | Popis zajištění. |
| **List ČNB** | ne | Návrh mapování pro výkaznictví; upozornění se zobrazí, pokud se liší od návrhu typu. |
| **Maximální stáří ceny (dny)** | ne | Ocenění upozorní na schválenou cenu starší než tento limit; upozornění samo ocenění nezastaví. |
| **Úroveň RH** | ne | Úroveň reálné hodnoty. |
| **Upozornění na knihu**, **Odchylka od návrhu typu** | systémová | Informace o společnosti v přepínači a o odchylce od návrhu typu. |

### Specifické údaje a úročení

Pole ve skupině **Ostatní podíl** jsou viditelná jen pro tento druh nástroje:

- **Třída** – související třída fondu.
- **Typ investice** – Cenné papíry nebo Podíly; povinné pro ostatní podíl.
- **Upisovací závazek** – částka v měně nástroje; nula znamená bez závazku.
- **Zakázka** – reference smlouvy či zakázky.

Pole ve skupině **Úročení** jsou pro Dluhopisy, Peněžní trh a Úvěry:

| Pole | Výchozí / podmínka | Význam |
|---|---|---|
| **Jistina na jednotku** | ne | Jistina, kterou představuje jeden kus; používá se při smluvních tocích a splátkách. |
| **Začátek úročení** | ne | Začátek výpočtu úroku. |
| **Výplata úroku** | **Ve splatnosti** | Ve splatnosti, Ročně, Pololetně, Čtvrtletně, Měsíčně nebo Nepravidelně. Nepravidelné toky se zadávají ručně. |
| **Splatnost** | ne | Datum splatnosti nástroje. |
| **Druh sazby** | **Pevná** | Pevná nebo Variabilní. Variabilní sazba se mění tlačítkem **Zadat novou sazbu**. |
| **Sazba %** | ne | Sazba nástroje; při variabilní sazbě se mění jen průvodcem nové sazby. |
| **Konvence dnů** | **ACT/365** | ACT/365, ACT/360, ACT/ACT ISDA, 30E/360 nebo 30/360 US. |
| **Cena bez naběhlého úroku** | odvozeno, lze přepsat | Určuje, zda se k ceně dluhopisu přičte naběhlý úrok; u vkladů a úvěrů je úrok zahrnut v ceně. |
| **Úročení** | **Podle fondu** | Podle fondu, Efektivní úroková míra nebo Lineárně. |
| **Zdůvodnění lineárního úročení** | povinné při Lineárně | Zobrazí se a vyžaduje jen při volbě Lineárně. |

Pro variabilní sazbu se zobrazí záložka **Období sazeb** (Platí od, Sazba % p.a., Poznámka, Zadal, Kdy). Průvodce **Zadat novou sazbu** ukazuje nástroj (jen pro čtení), **Platí od** (výchozí dnešek), **Sazba % p.a.**, **Poznámka**, upozornění a náhled dopadu. Novou sazbu lze zadat od určeného dne; přepočtou se budoucí smluvní toky Úrok, staré zůstávají v záložce **Nahrazené toky**. Změna sama nic neúčtuje a nemění schválená ocenění ani zaúčtované doklady. Změna sazby je citlivá na datum účinnosti a uzamčená ocenění; před uložením zkontrolujte náhled dopadu v průvodci.

U dluhových nástrojů a podílových listů se zobrazuje **Test SPPI** (výchozí Neposouzeno), **Odůvodnění SPPI**, **Posouzeno dne**, **Znění IFRS 9 pro SPPI** a **Posoudil**. Odůvodnění je povinné při Splněn nebo Nesplněn; datum, znění a osoba se zaznamenají při posouzení. Po prvním obchodu s nástrojem se posouzení SPPI zamkne.

### Klasifikace ČNB a záložky

Modul kmenových dat doplňuje **Druh ČNB (BA0088)**, odvozenou **Rodinu**, **CFI**, **Zdůvodnění druhu**, **Pákový**, **Datum emise**, **Nominál**, **Druh kupónu**, **Pořadí pohledávky**, **Vyměnitelný**, **Bez splatnosti**, **Podkladové aktivum** a **Podkladový nástroj**. BA0088 je řízený číselník, CFI musí mít šest velkých písmen. Podle BA0088 může být nutný Emitent, Splatnost nebo Zdůvodnění druhu; údaj o pákovosti se musí řídit pravidlem kódu. Při potvrzení klasifikace tlačítkem **Potvrdit klasifikaci** zkontroluje schvalovatel požadované údaje. Potvrzené údaje se mění přes **Změnit klasifikaci**; změna se zaznamená do historie.

Pole **Zdroj údajů** má výchozí **Ručně**; další volby jsou Import, LEI a SDAT. **Stav klasifikace** začíná **Ke kontrole**; **Potvrdil** a **Potvrzeno dne** jsou systémové údaje. Varování na formuláři upozorní na chybějící údaje nebo nesoulad ISIN/CFI.

- **Zařazení ve fondech** je na nástroji pouze pro čtení. Záznam založte v **Investra › Portfolio › Zařazení nástrojů** nebo na portfoliu.
- **Smluvní peněžní toky** obsahují **Datum**, **Druh** (výchozí Jistina; volby Jistina/Úrok) a **Částku na jednotku**. Pro pravidelné kupóny lze použít **Vygenerovat kalendář**; nepravidelné toky zadejte ručně. To je kalendář peněžních toků nástroje, nikoli dřívější kalendář ocenění fondu.
- U variabilní sazby se v řádcích toků ukazuje i příznak **Odhad**. Záložka **Nahrazené toky** uchovává datum, druh, částku na jednotku, odhad a data, od kdy tok platil a kdy byl nahrazen.

### Zařazení nástroje do portfolia

V portfoliu přidejte řádek **Zařazení nástrojů**. Formulář obsahuje **Portfolio**, **Fond** a **Nástroj**; **Druh** se převezme z typu nástroje. **Platí od** je povinné (výchozí dnešek), **Platí do** doplní jen reklasifikace. **Povaha nástroje** je povinná; **Posouzení povahy** doloží odlišnou povahu od druhu nástroje.

Z nástroje se přebírá **Test SPPI**, **Odůvodnění SPPI** a **Znění IFRS 9 pro SPPI**; z portfolia **Obchodní model**. **Povinná klasifikace**, **Vypočtená kategorie**, **Kategorie IFRS 9** a **Zdůvodnění klasifikace** jsou výsledky rozhodovacího stromu. **Určení / volba** je povinné (výchozí **Žádné**); odlišné určení vyžaduje **Odůvodnění určení**. Uživatel doplní **Způsob ocenění** a **Role účtu**; volitelně **Poznámka**. **Odchylka od návrhu** je systémová informace. Tlačítko **Ruční kategorie…** otevře průvodce, kde se zadá **Ruční kategorie** a povinné **Zdůvodnění přepsání**; změna podléhá schvalovací matici.

Portfolio určuje obchodní model, nástroj dává kmenové údaje a zařazení spojuje konkrétní nástroj s konkrétním fondem. Kategorie a způsob ocenění vždy vycházejí z politiky účetní jednotky; aplikace nenahrazuje toto účetní posouzení.

## Kmenová data

- **Investra › Nastavení › Číselníky** obsahuje Druhy CP (BA0088), Skupiny BA0088, Sektory ESA (detail), Typy emitenta, Členství zemí v EU/EHP, Oceňovací kategorie a Důvody klasifikace. V rozbalovacích polích nástroje se vybírá z těchto řízených hodnot, nové hodnoty nevytvářejte přímo ve formuláři nástroje.
- **Investra › Nastavení › Nástroje › Emitenti a protistrany** je místo pro údaje kontaktu emitenta, včetně země, sektoru ESA, kódu sektoru ESA a LEI. Emitent v nástroji na tento kontakt odkazuje; nevkládejte jeho identifikační údaje znovu do nástroje.
- Číselníky a jejich změny spravuje skupina **Investra: správce číselníků**; potvrzení klasifikace nástroje provádí **Investra: schvalování ocenění**.

Příklady v [ukázkových datech](../../tools/demo_data/seed.py) jsou smyšlené.
