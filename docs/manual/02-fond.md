# 2. Fond

*Ověřeno v kódu, v prohlížeči neověřeno.*

Fond je záznam navázaný na účetní knihu (kap. 1). Kniha může mít **jen jeden fond** („Kniha může mít jen jeden fond.“)
a musí být druhu Fond, Podfond nebo SICAV („Fond musí stát na knize fondu, podfondu nebo SICAV.“).
Předpoklad: nová společnost je zaškrtnutá v přepínači firem, jinak fond nevytvoříte ani neuvidíte.

## Založení

**Investra › Nastavení › Fondy › Fondy › Nový.** Vyplňte hlavičku a parametry, uložte. Třídy přidáte na záložce (kap. 3); další ocenění se počítá z Data vzniku a frekvence (kap. 4).
Při uložení vznikne automaticky portfolio **Hlavní** (obchodní model Řízení na reálnou hodnotu; posouzení je potřeba doplnit, kap. 6)
a profil FX přecenění fondu.

## Hlavička

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Účetní kniha** | ano | – | kniha fondu z kap. 1 (nabízí se jen druh Fond, Podfond a SICAV); po výběru se doplní funkční měna |
| **Funkční měna** | jen čtení | z knihy | v ní se vede účetnictví a NAV |
| **Obhospodařovatel** | ne | prázdné | kniha druhu Investiční společnost („Obhospodařovatel musí být kniha druhu Investiční společnost.“); schvalovací matici neovlivňuje, ta je od zjednodušení (ZJ-01) jedna pro celou aplikaci (kap. 4) |

## Základní parametry

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Frekvence ocenění** | ano | Měsíčně | Denně, Týdně, Měsíčně, Čtvrtletně, Ročně; z ní a z Data vzniku se počítá další ocenění (kap. 4) |
| **Výchozí desetinná místa kurzu** | ano | 4 | nová třída je převezme; na třídě 0 až 18 |
| **Výchozí zaokrouhlení kurzu** | ano | Dolů | Dolů, Matematicky, Nahoru; nová třída je převezme |
| **Zaúčtování obchodu** | ano | Trade date accounting | alternativa Settlement date accounting (IFRS 9 odst. 3.1.2); **po prvním obchodu fondu nejde změnit** („Po prvním obchodu fondu nejde způsob zaúčtování změnit.“) |

## Úpisy a odkupy – výchozí hodnoty tříd

Hodnoty se **zkopírují do nové třídy při jejím založení**; pozdější změna ve fondu už stávající třídy nemění.

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Výchozí desetinná místa kusů** | ano | 6 | na třídě 0 až 6 (kusy se ukládají nejvýš na 6 míst) |
| **Výchozí zaokrouhlení kusů** | ano | Dolů | Dolů, Matematicky, Nahoru |
| **Výchozí: rozdíl ze zaokrouhlení kusů** | ano | Zůstává ve fondu | Zůstává ve fondu = kapitál třídy; Vrací se investorovi = závazek, výplatu zadává IS |

**Vstupní a výstupní poplatek ve fondu už není.** Sazbu, příjemce, článek statutu a poznámku zadáváte jen na třídě (kap. 3);
výchozí hodnoty ve fondu zrušilo ZJ-03 (rozhodnutí 2026-11-17 „Poplatky fondu a tříd“), nová třída začíná na 0 % a příjemci Obhospodařovatel.

## Úročení nástrojů

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Úročení nástrojů v naběhlé hodnotě** | ano | Efektivní úroková míra | druhá volba Lineárně |
| **Zdůvodnění lineárního úročení** | při Lineárně | – | zobrazí se jen u Lineárně; bez něj „Lineární úročení fondu musí mít zdůvodnění.“ |
| **Tolerance ruční hodnoty derivátu (% nominálu)** | ne | výchozí z modulu derivátů | ocenění upozorní, když se ruční hodnota FX derivátu liší od spočtené o víc než toto procento nominálu otevřených noh |

## Účetní období

Účetní období fondu se řídí nastavením jeho účetní knihy (koncem fiskálního roku ve společnosti Odoo). Může jít o kalendářní i
hospodářský rok. Výpočty označené „od začátku účetního období“ začínají prvním dnem tohoto období, ne automaticky 1. ledna.
Toto období používá také výpočet daně fondu.

Ve formuláři fondu (záložka Obecné, skupina Základní parametry) je jen pro čtení pole **Konec účetního období**. Mění se v nastavení účetnictví knihy fondu, ne ve fondu.

## Záložky

- **Třídy:** kap. 3.
- **Úplaty:** pravidla úplat fondu (správa, depozitář, výkonnostní odměna ad.) – sloupce Název, Druh, Nákladová role, Třídy,
  Článek statutu a **Souběh**. Pravidlo se otevře šipkou na řádku; formulář má Článek statutu a **Poznámku** (později se ukážou i v XLS
  pro depozitáře, otevřený bod). Souběh jen **upozorní** (žlutý pruh ve formuláři pravidla, sloupec Souběh a kontrola ocenění „Úplaty téže role
  nejsou zároveň na fondu a na třídách“ jako varování): úplata téže nákladové role je na celém fondu i na třídě, nebo má třída dvě pravidla téže role.
  Uložení ani výpočet se nezastaví; daň se neposuzuje. Úplatu, kterou Odoo nespočte, zadáte v ocenění jako ručně doloženou (kap. 4, část 4).
- **Schéma výpočtu:** volba Základ všech pravidel fondu, předvolby a náhled s čísly (kap. 9, část 2).
- **Obchodní modely:** portfolia fondu (kap. 6).
- Pod formulářem je **historie** (chatter).

## Datum vzniku

Pole **Datum vzniku** (začátek prvního oceňovacího období) je ve formuláři fondu u Frekvence ocenění. Povinné není, ale
bez něj první ocenění skončí chybou „Fond nemá datum vzniku.“, takže ho vyplňte před prvním oceněním.
Po prvním ocenění fondu, které není stornované, je pole jen pro čtení a změna skončí chybou „Datum vzniku fondu … nejde změnit,
protože fond má ocenění, které není stornované.“ Po stornu všech ocenění jde změnit znovu.

## Co nejde po zaúčtování nebo prvním pohybu změnit

- **Zaúčtování obchodu** po prvním obchodu fondu.
- Kniha fondu: rámec ani společnost po zaúčtovaném dokladu (kap. 1).
- Třída po prvním zaúčtovaném úpisu nebo odkupu: kód a měna zveřejnění kurzu (kap. 3). Poplatky třídy, zaokrouhlení a desetinná místa kurzu a kusů jdou měnit (místa kusů snížit jen do přesnosti zaúčtovaných pohybů); zaúčtované pohyby a uložená ocenění se nepřepočítají.
- Výchozí hodnoty fondu (zaokrouhlení, desetinná místa) jdou měnit kdykoli; stávající třídy se jimi nemění.
- Fond s třídami nejde smazat (vazba tříd na fond je chráněná).

## Další krok

Přidejte třídy, kap. 3.
