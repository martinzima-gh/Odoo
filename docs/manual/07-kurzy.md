# 7. Kurzy

*Ověřeno v kódu, v prohlížeči neověřeno.*

## Zdroj kurzu podle účetní knihy

Zdroj je určen funkční měnou účetní knihy; pole **Zdroj kurzů** je ve formuláři knihy jen pro čtení:

| Funkční měna | Zdroj | Rozsah |
|---|---|---|
| CZK | ČNB | Denní kurzovní lístek ČNB; navíc měsíční kurzovní lístek ostatních měn ČNB. |
| EUR | ECB | Denní kurzovní lístek ECB. |
| Jiná měna | **Neimplementováno** | Kurzový zdroj pro tuto funkční měnu není k dispozici. |

Kurzy se stahují automatickou úlohou a ukládají do evidence Investra; do standardních kurzů Odoo se promítají jen podle pravidel příslušného zdroje. Výkazy ČNB se vždy přepočítávají kurzem ČNB. Křížový kurz mezi ČNB a ECB se nepoužívá.

Knihu v jiné funkční měně lze založit, ale dokud pro ni není implementován zdroj, přecenění, ocenění a pohyb třídy v cizí měně skončí chybou. Ruční kurz u jednotlivého pohybu, ocenění ani přecenění chybějící zdroj nenahrazuje. Kniha mimo CZK a EUR proto není připravena pro ostrý provoz.

## Evidence kurzů

**Investra › Nastavení › Účtování › Kurzy měn** otevře **Vyhlášené kurzy**. Záznamy jsou pouze pro čtení a nejdou přímo založit, změnit ani smazat. Formulář ukazuje:

| Pole | Význam |
|---|---|
| **Zdroj**, **Datum**, **Měna** | Kurzovní lístek, den vyhlášení a měna. |
| **Množství**, **Kurz** | ČNB uvádí částku v CZK za Množství jednotek měny; ECB uvádí počet jednotek měny za 1 EUR. |
| **Druh** | Vyhlášený, Ruční přepis nebo Ruční kurz. |
| **Vyhlašování** | Denní nebo Měsíční; měsíční je pro kurz ČNB ostatních měn. |
| **Důvod** | Povinné vysvětlení ručního kurzu nebo přepisu. |
| **Přepisuje kurz** | Předchozí záznam, který ruční přepis nahrazuje. |
| **Zadal**, **Staženo**, **Otisk souboru** | Evidence původu a staženého podkladu; nevyplněný otisk se nezobrazuje. |

Evidence je neměnná. Oprava se provede novým ručním přepisem, který zůstane propojený s předchozím záznamem.

## Ruční kurz nebo přepis

Ruční záznam smí zadat schvalovatel ocenění a vždy vyžaduje důvod. V seznamu použijte **Nový ruční kurz**, nebo na konkrétním kurzu **Přepsat kurz**. Při přepisu se výchozí zdroj, měna, datum, množství a kurz převezmou z původního záznamu.

| Pole ve formuláři **Ruční kurz** | Povinné / výchozí | Význam |
|---|---|---|
| **Druh** | **Ruční přepis vyhlášeného kurzu** | Druhá možnost je **Ruční kurz (zdroj ho nevyhlásil)**. Přepis použijte, jen když kurz zdroje ke dni existuje; jinak zvolte ruční kurz. |
| **Zdroj** | **ČNB** | ČNB nebo ECB, podle zdroje knihy. |
| **Měna**, **Datum** | povinné | Měna a datum, ke kterým záznam platí. |
| **Množství** | **1** | Počet jednotek měny, k němuž se vztahuje kurz. U ČNB může být například 100. |
| **Kurz** | povinný | Základní měna zdroje za zadané množství. Musí být kladný. |
| **Důvod** | povinný | Proč se kurz zadává ručně; uloží se do evidence. |
| **Platný záznam kurzu**, **Platný kurz**, **Druh platného kurzu** | jen pro čtení | Zobrazí se, pokud pro zdroj, měnu a datum existuje odpovídající záznam. |

Tlačítko **Uložit kurz** může podle schvalovací matice založit žádost o potvrzení druhou osobou. Záznam pak nelze editovat ani smazat; další oprava se zadá novým přepisem. Ruční zápis promítne účinný kurz také do standardní evidence kurzů Odoo podle pravidel projektu.

## Platnost kurzu

**Investra › Nastavení › Účtování › Platnost kurzů** nastavuje nejvyšší povolené stáří kurzu pro ocenění, přecenění cizích měn a úpisy a odkupy. Účetní doklady používají standardní kurzování Odoo a touto tabulkou se neřídí.

| Pole | Povinné / výchozí | Význam |
|---|---|---|
| **Zdroj** | ano | ČNB nebo ECB. |
| **Vyhlašování** | ano / **Denní** | Denní nebo Měsíční. ECB připouští jen denní kurzy. |
| **Měna** | ne | Prázdná hodnota je výchozí pravidlo pro celý lístek; vyplněná hodnota je výjimka pro jednu měnu. |
| **Nejvyšší stáří (dny)** | ano | Nejvyšší stáří v kalendářních dnech; nesmí být záporné. |
| **Aktivní** | ano / ano | Neaktivní pravidlo je archivované. |

Platnost kurzu mění jen **Investra: schvalování ocenění**. Záznam nelze smazat; vyřadí se odškrtnutím **Aktivní**. Pro použitý kurz se nejprve hledá aktivní výjimka pro měnu, jinak výchozí řádek zdroje a periodicity. Chybějící nastavení, chybějící kurz nebo překročené stáří zastaví příslušný výpočet; systém tiše nepoužije jiný zdroj.

### Co zůstává neimplementováno

Pro funkční měnu mimo CZK a EUR se nezadává ruční kurz ani přepis u jednotlivé operace. Až bude taková měna skutečně používána, musí se nejprve doplnit schválený zdroj a jeho kontrolní proces; dnešní volby ČNB a ECB to nepokrývají.
