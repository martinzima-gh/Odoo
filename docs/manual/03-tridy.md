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
Třída I má oba poplatky 0 %. Čísla jsou smyšlená.

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
| **Vstupní poplatek (%)** | ano | 0 | sazba z hrubé platby úpisu; 0 až 100: „Sazba poplatku musí být 0 až 100 %.“ |
| **Příjemce vstupního poplatku** | ano | Obhospodařovatel | skrytý sloupec; viz Poplatky třídy |
| **Výstupní poplatek (%)** | ano | 0 | sazba z hrubé částky odkupu (kusy × cena); 0 až 100 |
| **Příjemce výstupního poplatku** | ano | Obhospodařovatel | skrytý sloupec |
| **Článek statutu**, **Poznámka** | ne | – | zvlášť u vstupního a výstupního poplatku; jen ve formuláři třídy |
| **Pořadí** | ne | 10 | úchyt (☰) na začátku řádku; třídy se přetažením řadí |
| **Aktivní** | ne | ano | sloupec je skrytý (zapnete v nabídce sloupců); odškrtnutím se třída archivuje |

## Co třída dědí z fondu a co přepisuje

Při **založení** třídy se z fondu zkopírují: desetinná místa a zaokrouhlení kurzu, desetinná místa a zaokrouhlení kusů,
vlastník rozdílu ze zaokrouhlení. Poplatky se nekopírují: třída začíná na 0 % s příjemcem Obhospodařovatel. Nápověda „Bez zadání platí hodnota fondu“ platí jen při založení. Třída je pak samostatná: později změněný fond ji nepřepíše,
změněná třída fond nezmění. Přepis na třídě je úprava hodnoty v řádku.

## Poplatky třídy

Vstupní a výstupní poplatek se zadává **jen na třídě** (ve fondu už výchozí hodnoty nejsou). Formulář třídy otevřete **šipkou na začátku řádku**
v seznamu tříd (v řádku seznamu je jen sazba). Vstupní i výstupní poplatek mají **Sazbu (%)**, **Příjemce**, **Článek statutu**
a **Poznámku**; článek a poznámka jsou pro vás a pro depozitáře (do XLS se zatím nepřenášejí, otevřený bod).

**Příjemce poplatku:**

| Volba | Účetní dopad |
|---|---|
| Obhospodařovatel, Distributor | závazek fondu, poplatek se platí ven |
| Fond – výnos | výnos celého fondu, dělí se mezi třídy poměrem |
| Třída – výnos | celý poplatek jen třídě pohybu, jako výnos |
| Třída – kapitál | celý poplatek jen třídě pohybu, jako kapitál třídy |

Volbu řiďte statutem. Kapitál je vždy kapitál třídy, poměrem se dělí jen výnosy a náklady (proto „Fond – kapitál“ neexistuje).

**Historie změn.** Formulář třídy má dole historii (chatter). Změna sazby, příjemce, článku statutu nebo poznámky poplatku se do ní zapíše
jako „staré → nové“ (vlastní kód třídy; modul `mail_tracking` se neinstaluje). Poplatky jdou měnit i po zaúčtovaném pohybu; zaúčtované pohyby
a uložená ocenění se nepřepočítají.

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

**Desetinná místa kusů** jdou snížit jen do přesnosti zaúčtovaných pohybů třídy (stornované a pohyby v návrhu se
nepočítají). Má-li zaúčtovaný pohyb např. 10,123456 ks, snížení na 2 místa skončí chybou „Třída …: desetinná místa
kusů nejde snížit na 2. Zaúčtovaný pohyb … má kusy … (6 míst); po snížení by je nešlo odkoupit. …“. Důvod: odkup
se při zaúčtování kontroluje na místa třídy a kusy s více místy by nešly odkoupit. Zvýšení míst a změna zaokrouhlení
jdou vždy. Souhrn ocenění ukazuje kurz s tolika místy, s kolika byl při ocenění uložen.
Zámek je u každé třídy zvlášť; třída bez pohybu zůstává volná.

Chráněné je i tohle: třída s pohyby nejde smazat (vazba je chráněná); zaúčtovaný pohyb nejde změnit ani smazat, opravuje se stornem.
Třídu, kterou už nepotřebujete, archivujte (**Aktivní**). Archivovaná třída se v seznamu na formuláři fondu nezobrazuje;
vrátit ji do provozu jde jen přes správce (v seznamu fondu k ní není cesta).

## Další krok

Frekvence ocenění a schvalovací matice (kap. 4), pak uživatelé a role (kap. 5).
