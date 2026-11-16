# 3. Třídy fondu

*Ověřeno v kódu, v prohlížeči neověřeno.*

Fond je vícetřídový od začátku: kapitál, kurz a pohyby se vedou po třídách. Třídy se zakládají ve formuláři fondu na záložce **Třídy**
(**Investra › Nastavení › Fondy › Fondy › [fond] › Třídy**), přímo v řádcích seznamu (řádek **Přidat řádek**).

## Příklad

Fond Alfa Růst (funkční měna CZK), tři třídy:

| Kód | Název | Měna zveřejnění kurzu | Místa kurzu | Rozdělování | Vstupní / výstupní poplatek |
|---|---|---|---|---|---|
| A | Třída A retailová CZK | CZK | 4 | Růstová | 2 % / 0 %, příjemce Distributor |
| B | Třída B EUR | EUR | 4 | Růstová | 2 % / 0 %, příjemce Distributor |
| I | Třída I institucionální CZK | CZK | 4 | Růstová | 0 % / 0 % |

Třída B je v EUR při funkční měně fondu CZK: kurz se zveřejňuje v EUR, kapitál třídy a NAV zůstávají v CZK.
Třída I přepíše poplatky na 0 (výchozí hodnoty fondu zůstávají jiné). Čísla jsou smyšlená.

## Pole třídy

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Kód** | ano | – | ve fondu jedinečný: „Kód třídy musí být ve fondu jedinečný.“ |
| **Název** | ano | – | |
| **Měna zveřejnění kurzu** | ano | – | v ní se zveřejňuje kurz a probíhají úpisy a odkupy; nemění funkční měnu fondu |
| **Desetinná místa kurzu** | ano | z fondu (nový řádek ho předvyplní) | 0 až 18: „Počet desetinných míst kurzu musí být 0 až 18.“ |
| **ISIN** | ne | – | bez kontroly formátu |
| **Rozdělování výnosu** | ano | Růstová | Růstová, Dividendová |
| **Desetinná místa kusů** | ano | z fondu | 0 až 6: „Počet desetinných míst kusů musí být 0 až 6.“ |
| **Zaokrouhlení kurzu** | ano | z fondu | sloupec skrytý (zapnete v nabídce sloupců) |
| **Zaokrouhlení kusů** | ano | z fondu | skrytý sloupec |
| **Rozdíl ze zaokrouhlení kusů** | ano | z fondu | skrytý sloupec; Zůstává ve fondu / Vrací se investorovi |
| **Vstupní poplatek (%)** | ne | z fondu | 0 až 100: „Sazba poplatku musí být 0 až 100 %.“ |
| **Příjemce vstupního poplatku** | ano | z fondu | skrytý sloupec |
| **Výstupní poplatek (%)** | ne | z fondu | 0 až 100 |
| **Příjemce výstupního poplatku** | ano | z fondu | skrytý sloupec |
| **Pořadí**, **Aktivní** | ne | 10, ano | v řádku seznamu nejsou; Aktivní = archivace třídy |

## Co třída dědí z fondu a co přepisuje

Při **založení** třídy se z fondu zkopírují: desetinná místa a zaokrouhlení kurzu, desetinná místa a zaokrouhlení kusů,
vlastník rozdílu ze zaokrouhlení, oba poplatky a oba příjemci. Nápověda „Bez zadání platí hodnota fondu“ platí jen při založení. Třída je pak samostatná: později změněný fond ji nepřepíše,
změněná třída fond nezmění. Přepis na třídě je úprava hodnoty v řádku.

## Měna třídy

Měna třídy = **měna zveřejnění kurzu** (rozhodnutí 7. 11. 2026). Úpisy a odkupy se vedou v ní; kapitál třídy a NAV zůstávají ve funkční měně fondu.
U třídy v jiné měně než funkční se kurz převádí kurzem ze zdroje knihy (CZK – ČNB, EUR – ECB). Kurzy: kap. 7.

## Co nejde změnit

Aplikace zatím **nehlídá změnu polí třídy po prvním pohybu** (měna, desetinná místa, poplatky, kód); je to nález pro pročištění.
Do opravy změnu po prvním pohybu nedělejte: starší zaúčtované pohyby se nepřepočítají.
Chráněné je tohle: třída s pohyby nejde smazat (vazba je chráněná); zaúčtovaný pohyb nejde změnit ani smazat, opravuje se stornem.
Třídu, kterou už nepotřebujete, archivujte (**Aktivní**).

## Další krok

Kalendář ocenění a schvalovací matice (kap. 4), pak uživatelé a role (kap. 5).
