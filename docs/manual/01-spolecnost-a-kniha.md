# 1. Společnost a účetní kniha

*Ověřeno v kódu, v prohlížeči neověřeno.*

V Investře má každá jednotka (investiční společnost, fond, SICAV, podfond, servisní společnost) **vlastní společnost
Odoo a k ní jednu účetní knihu**. Knihu zakládá průvodce; ruční založení společnosti v Nastavení Odoo nepoužívejte.
Vynechalo by zámek deníků, auditní stopu a mapování rolí účtů a mohlo by přepsat funkční měnu.

## Co potřebujete

- uživatele s právem **správce** (jen ten průvodce otevře; načtení osnovy Odoo jiným uživatelům nedovolí),
- nainstalované moduly osnovy a lokalizace země. Jinak průvodce skončí chybou „Nejdřív nainstalujte moduly: … Nic se nezaložilo.“

## Postup založení

1. **Investra › Nastavení › Fondy › Účetní knihy**, tlačítko **Nová účetní kniha** (samostatná položka nabídky neexistuje).
2. Přečtěte žluté upozornění: funkční měnu, účetní rámec ani společnost nejde po prvním zaúčtování změnit.
3. Vyplňte pole:

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Název společnosti** | ano | – | musí být jedinečný, jinak „Společnost … už existuje.“ |
| **Druh jednotky** | ano | Fond | Servisní společnost, Investiční společnost, SICAV, Fond, Podfond; určuje osnovu a rámec |
| **Účetní rámec** | ano | podle druhu | servisní společnost: Vyhláška 500/2002; ostatní: Vyhláška 501/2002 |
| **Nadřazená kniha** | jen u podfondu | – | viditelná a povinná jen u druhu Podfond, nabízí jen SICAV: „Podfond musí mít nadřazený SICAV.“ |
| **Funkční měna** | ano | CZK | nabízejí se jen aktivní měny |
| **Země** | ano | Česko | |
| **Šablona osnovy** | jen čtení | podle druhu | SICAV, fond, podfond: osnova fondu (`investra_fund`); ostatní: česká osnova (`cz`) |
| **Zdroj kurzů** | jen čtení | podle měny | CZK – ČNB, EUR – ECB; jiná měna: ČNB |
| **Existující kontakt** | ne | – | kontakt, který nová společnost převezme (viz níže) |
| **IČO** | ne | – | 8 číslic s kontrolní číslicí; u země Česko se kontroluje: „Neplatné IČO …“ |
| **DIČ** | ne | CZ + IČO | u země Česko se po zadání platného IČO předvyplní, lze přepsat |
| **Kód sektoru ESA** | ne | podle druhu (viz níže) | detailní číselník ČNB; sektor ESA 2010 se z něj doplní |
| **LEI** | ne | – | kontrola ISO 17442 a jedinečnost; vyžaduje kód sektoru ESA |

4. **Založit knihu**, potvrďte dotaz. Stránka se znovu načte, otevře se formulář nové knihy a nová společnost se sama zapne v přepínači firem.

**Kontrola rámce:** jiná kombinace než v tabulce se odmítne před založením: „Druh jednotky a účetní rámec nejdou dohromady: pro tento druh platí …“
Rámce se nemíchají; IFRS je v seznamu rámců, ale průvodce ho odmítne.

### Identifikace a existující kontakt

- **Skupina Identifikace** je nepovinná. Zadáte-li LEI nebo kód sektoru ESA, průvodce po založení knihy vytvoří
  **údaje protistrany** kontaktu společnosti (země z průvodce). LEI bez kódu sektoru se odmítne před založením: profil
  sektor potřebuje. Chybný IČO, LEI, kód nesouhlasící se zemí (rezident × nerezident) nebo LEI, které už má jiná
  protistrana, se odmítnou před založením, nic se nezaloží.
- **Předvyplnění kódu ESA:** průvodce nabídne rezidentský kód podle druhu (rozhodnutí 16. 11. 2026): fond, SICAV a podfond
  **1240200** (Fondy kolektivního investování – soukromé národní), investiční společnost **1260200** (Pomocné finanční
  instituce – soukromé národní); servisní společnost: nic. Kód lze přepsat (hledá se podle čísla i názvu); chybí-li kód
  v číselníku, pole zůstane prázdné.
- **Existující kontakt:** vyberte ho v poli **Existující kontakt**. Nabízejí se samostatné kontakty (ne osoby pod firmou),
  které ještě nejsou kontaktem žádné společnosti. Nová společnost kontakt převezme (název se vezme z něj, kontakt se
  přestane vázat na jednu firmu a uvidí ho všechny), druhý kontakt se nezakládá. IČO, DIČ, LEI a kód se předvyplní
  z kontaktu a z jeho údajů protistrany; ty už se nezakládají znovu a LEI i kód se pak mění v nich.
- Zadáte-li jen název a kontakt stejného jména existuje, průvodce nahoře upozorní a nabídne **Použít existující kontakt**.
  Bez volby se založí nový kontakt.

## Co průvodce nastaví za vás

- funkční měnu podle zadání (načtení osnovy ji nepřepíše),
- zdroj kurzů podle měny, § 24d zákona o účetnictví,
- zámek zápisů (auditní stopa) společnosti,
- u SICAV, fondu a podfondu hash obecných deníků (zápisy jsou neměnné),
- mapování rolí účtů na účty šablony,
- přidání nové společnosti vašemu uživateli.

## Co nejde později změnit

| Údaj | Pravidlo |
|---|---|
| Funkční měna | jen při založení (rozhodnutí 15. 11. 2026); formulář knihy ji ukazuje jen ke čtení |
| Účetní rámec a společnost | po zaúčtovaném dokladu: „Rámec ani společnost nejde změnit v knize se zaúčtovanými doklady.“ |
| Zdroj kurzů | musí odpovídat měně: „Zdroj kurzu se řídí měnou účetnictví: …“ |

## Kniha investiční společnosti (obhospodařovatele)

Založte ji jako první: **Druh jednotky = Investiční společnost**, rámec 501/2002, funkční měna CZK, šablona `cz`, bez hashe deníků.
Ve formuláři fondu (kap. 2) se pak vybírá jako **Obhospodařovatel**; její schvalovací matice platí pro fond.

## Kniha fondu

Druh **Fond**, rámec 501/2002, měna podle statutu. Příklad: **Fond Alfa Růst**, funkční měna CZK.
Podfond zakládejte až po SICAV a v poli **Nadřazená kniha** SICAV vyberte.

## Po založení

- **Přepínač firem:** po založení se stránka znovu načte a nová společnost se v přepínači (vpravo nahoře) zapne sama.
  Kdyby zapnutá nebyla, zaškrtněte ji ručně, jinak neuvidíte její knihy, fond ani třídy (přístup se řídí zaškrtnutými
  společnostmi).
- **Formulář knihy** (Účetní knihy): skupina **Společnost** (společnost, druh jednotky, účetní rámec, nadřazená kniha jen
  u podfondu), skupina **Měna a kurzy** (funkční měna jen čtení, zdroj kurzů; pod ním text „Výkazy ČNB se vždy přepočítávají
  kurzem ČNB.“) a skupina **Identifikace** (**IČO** a **DIČ** upravitelné jen pro správce, ostatní je vidí jen ke čtení;
  LEI a sektor ESA ze záznamu údajů protistrany, jen čtení). IČO se u české společnosti kontroluje (8 číslic, kontrolní
  číslice). Nad poli je upozornění, že funkční měnu, rámec
  ani společnost nejde po prvním zaúčtování změnit. U polí jsou nápovědy (najeďte myší na popisek).
- **LEI a sektor:** zadávají se v **údajích protistrany** kontaktu společnosti (povinná země, kód sektoru ESA a sektor
  ESA 2010, kontrola ISO 17442). Vybíráte jen **Kód sektoru ESA**; **Sektor ESA 2010** se z něj doplní a ve formuláři je
  jen ke čtení. Kód bez vazby na sektor: sektor zadáte ručně. Číselníky sektorů a kódů ukazují kód v prvním sloupci
  a hledá se podle kódu i názvu. Záhlaví záznamu je „Údaje protistrany – <kontakt>“, nový záznam „Nové údaje protistrany“. Každý kontakt má **jeden záznam** bez data „platí od“: změna se přepíše a stará i nová hodnota (kdo, kdy)
  zůstanou v **historii záznamu** vpravo. Druhý záznam pro stejný kontakt nejde založit. Tlačítko **Údaje protistrany**
  ve formuláři knihy otevře tento záznam, nebo nový s předvyplněným kontaktem a zemí. Změna potvrzených údajů vyžaduje
  **Důvod změny** a vrátí stav na **Ke kontrole**; znovu je potvrdí schvalovatel. U podfondu je LEI nepovinné. V seznamu
  knih lze zapnout sloupec **LEI**.
- **Proč profil nemá „platí od“:** údaje protistrany (země, kód, sektor, LEI) jsou jeden záznam na kontakt; dřívější
  platnost od data se zrušila (rozhodnutí 16. 11. 2026). Co se kdy změnilo, ukazuje historie záznamu vpravo. Vlastní fond je
  také protistranou (investuje do něj jiný náš fond), proto používá stejný záznam jako ostatní kontakty.
- **Popisek DIČ:** u kontaktu společnosti se popisek daňového čísla řídí zemí aktivní firmy. Výchozí firma Odoo
  „My Company“ má zemi USA, proto ukazuje TIN; po nastavení země Česko je popisek DIČ.
- **Osnova:** účty společnosti jsou v účetní části Odoo pod zvolenou společností.
- **Role účtů:** **Investra › Nastavení › Účtování › Účty rolí** ukazuje, který účet plní kterou roli ;
  seznam rolí je v **Role účtů** (jen čtení). Kontrolujte, že všechny role mají u nové knihy účet.

## Role účtů a odchylky od standardu

Každá kniha fondu má vlastní kopii mapování **role → účet** (zkopíruje se ze standardu při založení). Pravidla účtování
berou účet z mapování knihy, proto fond smí mít u některé role jiný účet.

- **Kde je to vidět:** Investra › Nastavení › Účtování › Účty rolí. Sloupec **Standard** má hodnoty *Podle standardu*,
  *Odchylka* (řádek je zvýrazněný) a *Bez standardu* (kniha není ze šablony fondu). Sloupec **Standardní účet** ukazuje,
  jaký účet by role měla podle šablony. Filtr **Odchylka od standardu** vypíše jen výjimky všech fondů.
- **Co se porovnává:** jen hlavní účet role. **Další účty** (další banky, platby na cestě) jsou z povahy věci fondové
  a odchylkou nejsou.
- **Kdy výjimku použít:** jen když fond ze statutu nebo účetního postupu opravdu potřebuje jiný účet. Změnu proveďte
  před prvním zaúčtováním, nebo po dohodě s účetním, a důvod poznamenejte. Při pozdější změně standardu se řádky
  s odchylkou nepřepisují; vypíší se a rozhodnete o nich zvlášť.
- **Vlastní analytika:** nový účet, který má plnit roli, musí být napojený na roli (jinak ho pravidla účtování
  nepoužijí) a zařazený do převodové tabulky ČNB, aby se zobrazil ve výkazech.

## Další krok

Kniha existuje, fond ještě ne. Pokračujte kapitolou 2.
