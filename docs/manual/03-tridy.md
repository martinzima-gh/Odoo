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
| **Kód** | ano | – | ve fondu jedinečný: „Kód třídy musí být ve fondu jedinečný.“; po prvním zaúčtovaném pohybu jen pro čtení |
| **Název** | ano | – | |
| **Měna zveřejnění kurzu** | ano | – | v ní se zveřejňuje kurz a probíhají úpisy a odkupy; nemění funkční měnu fondu |
| **Desetinná místa kurzu** | ano | z fondu (nový řádek ho předvyplní) | 0 až 18: „Počet desetinných míst kurzu musí být 0 až 18.“ |
| **ISIN** | ne | – | 12 znaků velkými písmeny: kód země, 9 znaků a kontrolní číslice podle ISO 6166; jinak „Neplatný ISIN třídy …“ |
| **Rozdělování výnosu** | ano | Růstová | Růstová, Dividendová |
| **Desetinná místa kusů** | ano | z fondu | 0 až 6: „Počet desetinných míst kusů musí být 0 až 6.“ |
| **Zaokrouhlení kurzu** | ano | z fondu | sloupec skrytý (zapnete v nabídce sloupců) |
| **Zaokrouhlení kusů** | ano | z fondu | skrytý sloupec |
| **Rozdíl ze zaokrouhlení kusů** | ano | z fondu | skrytý sloupec; Zůstává ve fondu / Vrací se investorovi |
| **Vstupní poplatek (%)** | ne | z fondu | 0 až 100: „Sazba poplatku musí být 0 až 100 %.“ |
| **Příjemce vstupního poplatku** | ano | z fondu | skrytý sloupec |
| **Výstupní poplatek (%)** | ne | z fondu | 0 až 100 |
| **Příjemce výstupního poplatku** | ano | z fondu | skrytý sloupec |
| **Pořadí** | ne | 10 | úchyt (☰) na začátku řádku; třídy se přetažením řadí |
| **Aktivní** | ne | ano | sloupec je skrytý (zapnete v nabídce sloupců); odškrtnutím se třída archivuje |

## Co třída dědí z fondu a co přepisuje

Při **založení** třídy se z fondu zkopírují: desetinná místa a zaokrouhlení kurzu, desetinná místa a zaokrouhlení kusů,
vlastník rozdílu ze zaokrouhlení, oba poplatky a oba příjemci. Nápověda „Bez zadání platí hodnota fondu“ platí jen při založení. Třída je pak samostatná: později změněný fond ji nepřepíše,
změněná třída fond nezmění. Přepis na třídě je úprava hodnoty v řádku.

## Měna třídy

Měna třídy = **měna zveřejnění kurzu** (rozhodnutí 7. 11. 2026). Úpisy a odkupy se vedou v ní; kapitál třídy a NAV zůstávají ve funkční měně fondu.
U třídy v jiné měně než funkční se kurz převádí kurzem ze zdroje knihy (CZK – ČNB, EUR – ECB). Kurzy: kap. 7.

## Co nejde změnit po prvním pohybu

Po prvním **zaúčtovaném** úpisu nebo odkupu třídy (stav Zaúčtováno; stornovaný pohyb byl zaúčtován také, zámek tedy zůstává)
jsou ve formuláři jen pro čtení a změna skončí chybou „Třída … má zaúčtovaný úpis nebo odkup, proto nejde změnit: …“ pole
**Kód** a **Měna zveřejnění kurzu**.
Pohyb v návrhu třídu nezamyká. Měnit jde dál **Název**, **ISIN**, **Rozdělování výnosu**, **Pořadí**, **Aktivní**,
poplatky a jejich příjemci a také **Desetinná místa kurzu**, **Zaokrouhlení kurzu**, **Desetinná místa kusů**
a **Zaokrouhlení kusů** (od 16. 11. 2026, úkol MN-12). Změna neplatí zpětně od data: zaúčtované pohyby (kusy, částky)
ani uložená ocenění (kurz, kusy) se nepřepočítají. Nová místa a zaokrouhlení použije až další zaúčtovaný úpis
nebo odkup a další výpočet ocenění; ocenění, které je spočtené a ještě nepředložené, je přepočte při novém výpočtu.

Pozor při **snížení desetinných míst kusů**: odkup se při zaúčtování kontroluje na nová místa. Držitel, který má kusy
s více místy (např. 10,123456 při nových 2 místech), nemůže odkoupit celý stav jedním pohybem. Kontrola stav
neopravuje, změnu ani neodmítne; snižte místa jen tehdy, když to stavy držitelů dovolí.
Zámek je u každé třídy zvlášť; třída bez pohybu zůstává volná.

Chráněné je i tohle: třída s pohyby nejde smazat (vazba je chráněná); zaúčtovaný pohyb nejde změnit ani smazat, opravuje se stornem.
Třídu, kterou už nepotřebujete, archivujte (**Aktivní**). Archivovaná třída se v seznamu na formuláři fondu nezobrazuje;
vrátit ji do provozu jde jen přes správce (v seznamu fondu k ní není cesta).

## Další krok

Kalendář ocenění a schvalovací matice (kap. 4), pak uživatelé a role (kap. 5).
