# 1. Společnost a účetní kniha

*Ověřeno v kódu, v prohlížeči neověřeno.*

V Investře má každá jednotka (investiční společnost, fond, SICAV, podfond, servisní společnost) **vlastní společnost
Odoo a k ní jednu účetní knihu**. Knihu zakládá průvodce; ruční založení společnosti v Nastavení Odoo nepoužívejte.
Vynechalo by zámek deníků, auditní stopu a mapování rolí účtů a mohlo by přepsat funkční měnu.

## Co potřebujete

- uživatele s právem **správce** (jen ten průvodce otevře; načtení osnovy Odoo jiným uživatelům nedovolí),
- nainstalované moduly osnovy a lokalizace země. Jinak průvodce skončí chybou „Nejdřív nainstalujte moduly: … Nic se nezaložilo.“

## Postup založení

1. **Investra › Nastavení › Fondy › Nová účetní kniha** (nebo tlačítko **Nová účetní kniha** v seznamu **Účetní knihy**).
2. Přečtěte žluté upozornění: funkční měnu, účetní rámec ani společnost nejde po prvním zaúčtování změnit.
3. Vyplňte pole:

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Název společnosti** | ano | – | musí být jedinečný, jinak „Společnost … už existuje.“ |
| **Druh jednotky** | ano | Fond | Servisní společnost, Investiční společnost, SICAV, Fond, Podfond; určuje osnovu a rámec |
| **Účetní rámec** | ano | podle druhu | servisní společnost: Vyhláška 500/2002; ostatní: Vyhláška 501/2002 |
| **Nadřazená kniha** | u podfondu | – | podfond musí mít nadřazený SICAV: „Podfond musí mít nadřazený SICAV.“ |
| **Zakladatel** | ne | – | kontakt (partner) zakladatele |
| **Funkční měna** | ano | CZK | nabízejí se jen aktivní měny |
| **Země** | ano | Česko | |
| **Šablona osnovy** | jen čtení | podle druhu | SICAV, fond, podfond: osnova fondu (`investra_fund`); ostatní: česká osnova (`cz`) |
| **Zdroj kurzů** | jen čtení | podle měny | CZK – ČNB, EUR – ECB; jiná měna: ČNB |

4. **Založit knihu**, potvrďte dotaz. Otevře se formulář nové knihy.

**Kontrola rámce:** jiná kombinace než v tabulce se odmítne před založením: „Druh jednotky a účetní rámec nejdou dohromady: pro tento druh platí …“
Rámce se nemíchají; IFRS je v seznamu rámců, ale průvodce ho odmítne.

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

- **Přepínač firem:** nová společnost se v přepínači (vpravo nahoře) trvale nezapne. Po odchodu z formuláře ji zaškrtněte,
  jinak neuvidíte její knihy, fond ani třídy (přístup se řídí zaškrtnutými společnostmi).
- **Formulář knihy** (Účetní knihy): Společnost, Funkční měna (jen čtení), Druh jednotky, Účetní rámec, Zdroj kurzů,
  Nadřazená kniha, Zakladatel.
- **Osnova:** účty společnosti jsou v účetní části Odoo pod zvolenou společností.
- **Role účtů:** **Investra › Nastavení › Účtování › Účty rolí** ukazuje, který účet plní kterou roli ;
  seznam rolí je v **Role účtů** (jen čtení). Kontrolujte, že všechny role mají u nové knihy účet.

## Další krok

Kniha existuje, fond ještě ne. Pokračujte kapitolou 2.
