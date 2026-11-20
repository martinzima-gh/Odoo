# 10. Rozdělení výsledku mezi třídy

*Ověřeno v kódu; ověření formulářů v prohlížeči čeká na převzetí.*

Systém rozlišuje sdílené a specifické položky:

- **Sdílené položky** se rozdělí podle alokačního poměru tříd, které se podílejí na společných položkách.
- **Specifické položky** se přiřadí přímo jedné třídě.
- **Kapitál třídy** = její upravený kapitál + podíl na sdíleném výsledku + specifické položky.

| Obvykle sdílené | Obvykle specifické |
|---|---|
| výsledek sdíleného portfolia, bankovní úroky, kurzové rozdíly peněz | výsledek portfolia přiřazeného třídě, úplata třídy, dividenda třídy |
| náklady účtované celému fondu, daň ze sdíleného výsledku | měnové zajištění třídy, úpisy a odkupy, přesun výkonnostní odměny |

## Alokační schéma

Nastavení je v **Investra › Nastavení › Fondy › Alokační schémata**. Bez schématu se sdílený výsledek dělí podle předběžného kapitálu
tříd s podílem na společných položkách. Schéma **Alokační poměr** toto rozdělení pouze formálně zaznamená. Schéma **Pořadí nároků**
rozděluje zisk a ztrátu podle pořadí a nastavených cílů; rozdíl proti alokačnímu poměru se zaúčtuje jako přesun mezi třídami.

Schéma se zakládá s platností od a nemění historii. Řádky smějí obsahovat jen třídy téhož fondu, které se podílejí na společných
položkách. Schéma s metodou Alokační poměr řádky nepotřebuje.

## Třída bez podílu na společných položkách

Na formuláři třídy je přepínač **Podílí se na společných položkách**, výchozí zapnutý. Vypnutá třída nedostává podíl na sdíleném
výsledku, společných nákladech ani dani ze sdíleného výsledku. Její kapitál se mění jen vlastním počátečním kapitálem, pohyby třídy
a specifickými položkami, například přijatou výkonnostní odměnou. Typickým příkladem je manažerská třída.

Třídu bez podílu nezařazujte do řádků alokačního schématu. Schéma **Pořadí nároků** se vyhodnocuje jen mezi třídami s podílem.
Přepínač lze změnit jen do prvního zaúčtovaného ocenění fondu.

**Příklad:** A má kapitál 60 mil. Kč, B 40 mil. Kč a M 2 mil. Kč. Při zisku 10 mil. Kč, pokud se M nepodílí, připadá A 6 mil. Kč,
B 4 mil. Kč a M žádná část sdíleného zisku. Převede-li se výkonnostní odměna 2 mil. Kč z A a B do M, je to specifická položka M.

Pravidlo úplaty, které zahrnuje třídu bez podílu, zobrazí žluté upozornění v pravidle a kontrole ocenění. Záměrnou částku pro takovou
třídu zadejte jako ruční úplatu.

## Portfolio třídy

Na portfoliu vyplňte **Třída**, pokud má portfolio patřit jen jedné třídě. Prázdná hodnota znamená sdílené portfolio všech tříd.
Obchod třídu nepřebírá od uživatele; určuje ji portfolio. Sdílené bankovní peníze se mezi třídou a fondem vyrovnávají přes vnitřní
zúčtování. Po prvním dokladu portfolia jeho třídu nelze změnit.

## Přemostění a kontrola

Ve formuláři ocenění otevřete záložku **Třídy** a záznam třídy. Přemostění ukazuje počáteční stav, úpisy a odkupy, alokační poměr,
sdílenou změnu, specifickou změnu a konečný kapitál. Specifická změna se dále člení na úplaty třídy, výkonnostní odměnu, přesun podle
pořadí nároků, daňový efekt specifických položek a ostatní specifické položky.

Daň ze sdíleného výsledku nesou jen třídy s podílem. Daňový efekt specifických položek se přiřadí třídě, která položku nese; celková
daň fondu se tím nemění. Podrobnosti nastavení daně jsou v [kapitole 11](11-dan.md).
