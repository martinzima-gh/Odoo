# ZADÁNÍ PRO AGENTA – ZJ-25 Ocenění · ZJ-27 Zařazení z obchodu · ZJ-26 Jednotný vzhled formulářů a dialogů

Zadal Martin 2026-11-20 (návrh připravila relace „poradce“, schváleno na plátně návrhů). Ulož do
`docs/ukoly/podklady/zadani-ZJ-25-26-oceneni-a-vzhled.md`; z něj založ `docs/ukoly/ZJ-25-….md` , `docs/ukoly/ZJ-27-….md` a `docs/ukoly/ZJ-26-….md` podle `_sablona.md`.
Platí CLAUDE.md, `.agents/rules/10-zony.md` a `docs/vzhled/zasady-obrazovek.md`. Čísla v příkladech jsou ilustrační, do kódu ani dat je nepřebírej.

## 0. Pravidla pro obě úlohy
- Větve navazují (nic se neslučuje do konce): `ukol/ZJ-24-hlasky-a-sazby` → `ukol/ZJ-24-bod-15` → `ukol/ZJ-25-oceneni-kontroly-rozpad` → `ukol/ZJ-27-zarazeni-z-obchodu` →
  `ukol/ZJ-26-vzhled` (ZJ-24 obsahuje `sign_hint`; ZJ-25, ZJ-27 a ZJ-26 mění tytéž pohledy, proto za sebou; vzhled ZJ-26 až na konečných polích po ZJ-27). Postup: `davka-ZJ-24-27/00-prehled.md`.
- **Do `main` nic neslučuj.** Na konci pushni větev a napiš zprávu (commity, odchylky, testy, snímek 35/39, co ověřit v prohlížeči). Martin ji
  dá zkontrolovat a sloučení povolí sám.
- Provádí Sonnet (medium; část ZJ-27 high) v jedné relaci podle technických plánů v `davka-ZJ-24-27/`; oddíl 1.6 (plán) je hotový v `plan-ZJ-25-technicky.md`.
- Snímek ocenění 35 a 39 a referenční scénáře se nesmí změnit (`tools/snimek_na_kopii.sh`). Když se změní, zastav a napiš proč.
- Vzhled: jen paleta `$investra-*`, datum dd.MM.yyyy, čísla `tabular-nums` vpravo. Nemazat pole, méně důležitá přesunout.

## 1. ZJ-25 Ocenění (červená zóna – kód jen podle plánu `davka-ZJ-24-27/plan-ZJ-25-technicky.md`, který připravil poradce; Martin ho schvaluje před spuštěním relace a schválení je zapsané v hlavičce plánu – bez něj STOP)

### 1.1 Rozpad tříd – detail přemostění (`view_valuation_class_form`, otevírá se jako dnes z řádku záložky Třídy)
- Záložka Třídy na ocenění se nemění. Formulář přemostění dostane záložky: **Přemostění** (dnešní obsah beze změny), **Účty**, **Úpisy a odkupy**, **Úplaty třídy**.
- **Účty** – změna účtů za období (`date > _period_start`, `<= date`, filtr přesně jako `_line_domain`, tedy i návrhy dokladů tohoto ocenění):
  - výchozí pohled **Rozvaha** (tak počítá výpočet: `_delta` = rozvahové řádky s třídou; společná část z NFK = aktiva + závazky bez tříd):
    sloupce Účet | Název | Společné – fond (řádky bez třídy) | Podíl třídy × alokační poměr | Specifické – třída | Vliv na FK třídy;
    skupiny Aktiva, Závazky, „Kapitálové pohyby (nejsou výsledek)“ = − úpisy + odkupy tříd; řádek Zaokrouhlení podílu;
  - přepínač **Podle výsledovky**: tatáž změna přes výnosové, nákladové a OCI účty (stejný součet);
  - pod tabulkou kontrola shody: součet společných = Změna společná, specifických = Změna specifická, celkem = výsledek přemostění (✓/✗).
- Klik na účet → standardní seznam **Položky deníku** s filtrem (účet, období, řádky bez třídy i této třídy), seskupený podle nástroje (ISIN),
  sloupce Třída („Společné“ = bez třídy, jinak kód), Doklad, **Zdroj** (z `investra.accounting.event.res_model/res_id`, otevře obchod, úpis, splátku, ocenění…), Částka.
- Úpisy a odkupy: seznam pohybů období (datum, pohyb, zdroj IS/ruční, kusy, cena, změna kapitálu). Úplaty třídy: řádky úplat této třídy.
- Výpočet rozpadu jedna funkce, použitá obrazovkou i souborem (1.2) i kontrolou (1.3).

### 1.2 Soubor pro depozitáře (`models/package.py`)
- List **Předvaha** rozšířit (dnes `_trial_balance` jen MD/D/zůstatek): všechny účty se zůstatkem nebo pohybem; sloupce Účet | Název |
  Zůstatek k minulému ocenění | Pohyb období: Společné (bez třídy) | Třída A | Třída B … | Pohyb celkem | Zůstatek k datu ocenění; součtový řádek = 0.
- Nový list **Rozpad tříd**: jako záložka Účty (rozvaha) pro všechny třídy vedle sebe (Společné, podíl každé třídy, specifické každé třídy,
  vliv na FK každé třídy) + řádek kontroly proti listu Přemostění tříd. List s řádky hlavní knihy **nepřidávat**.

### 1.3 Kontroly ocenění (`_check`, `investra.valuation.check`, záložka Kontroly)
- Nová kontrola **„Rozpad tříd po účtech = přemostění“** při každém výpočtu (stop při rozdílu nad 0,01).
- Katalog podle kódu kontroly: jedna věta **Co se kontroluje** a **Jak opravit** pro každou ze všech dnešních kontrol (44 kódů: 39 v `investra_nav`, 5 v `investra_derivative`) i nové (texty navrhni v plánu).
- Model kontroly doplnit o strukturovaný výsledek: Očekáváno, Skutečnost, Rozdíl (formátovaná čísla nebo text, např. „≤ 5 dní“) a seznam
  **co nesedí** (položka, hodnoty, odkaz na záznam: nástroj, obchod, třída, pravidlo, doklad). Starý `detail` ponech pro starší ocenění.
- Záložka Kontroly: pás tří čísel Stop – brání odeslání | Upozornění | V pořádku; nahoře problémy seskupené podle oblasti (Kapitál a třídy,
  Portfolio a obchody, Ceny a kurzy, Úpisy a odkupy, Úplaty a daň, Účetnictví, Schvalování); sloupce Kontrola | Výsledek | Očekáváno |
  Skutečnost | Rozdíl | Co dělat (odkaz); rozbalení ukáže Co se kontroluje, tabulku Co nesedí, Jak opravit; „V pořádku (n)“ sbalené.
- Souhrn ocenění: do řádku údajů pod nadpisem odkaz „Kontroly: 1 stop, 2 upozornění“ (jen když nějaké jsou) a tečka u záložky.

### 1.4 Texty v detailu ocenění (ponechat vše, co vede k akci)
- Ponechat: upozornění na žádost, vrácení, balíček, neaktuální výpočet; „změna kapitálu ≠ výkonnost“; karty tříd s grafem beze změny.
- Souhrn: pod „FK fondu“ vypustit „celkový kapitál k datu ocenění“.
- Úplaty – rozpad daně (`tax_breakdown.py`): poznámku psát jako výpočet „výsledek od zač. období X − výjimky Y + neuznatelné Z = základ W · po kroku N“;
  „Výjimky fondu“ → jen výjimky s nenulovým pohybem, sbalené „▸ Použité výjimky (n)“.
- Převzaté opravy: jedna věta „Opravy dřívějších ocenění platné do konce období. Ukončíte je tlačítkem Ukončit opravu.“, zbytek do nápovědy.
- Ručně doložené úplaty: dva rámečky nahradit šedou větou „Kladná částka = náklad, záporná = výnos (např. vratka). Účtuje se k datu ocenění
  proti závazku z úplat; prázdná třída = celý fond.“; „(ZJ-03)“ pryč; pořadí výpočtu, povinná poznámka a „jiné případy ručně“ do nápovědy a manuálu kap. 9;
  upozornění ke znaménku jen u řádku (`sign_hint`).

### 1.5 Portfolio
- Volitelné sloupce **Změna ceny** a **z toho kurz** (od minulého ocenění) u řádků portfolia.

### 1.6 Plán (připravil poradce v `plan-ZJ-25-technicky.md`; níže původní požadavky na jeho obsah)
Zapiš do `docs/ukoly/ZJ-25-…md` plán: funkce rozpadu (vstupy, shoda s `_shared_neutral`/`_delta`, OCI a ostatní pohyby mimo výsledovku,
zaokrouhlení), nová pole a migrace, katalog kontrol (všechny texty), změny `package.py`, testy (shoda rozpadu s přemostěním na referenčních
scénářích, více tříd, třída bez podílu, cizí měna, starší ocenění bez nových polí), dopad na snímek 35/39. Agent ověří, že hlavička plánu obsahuje schválení Martinem s datem; jinak STOP.

## 2. ZJ-26 Jednotný vzhled (zelená: CSS, pohledy i zkrácení popisků polí v Pythonu; jedna relace Sonnet)

### 2.1 Pravidla (doplnit do `docs/vzhled/zasady-obrazovek.md`, oddíl „Formuláře se zadáním“)
1. Nadpis = hlavní záznam; u cenných papírů **„ISIN + název“** (název menším šedým písmem). Pod nadpisem jeden pás údajů (malý šedý popisek nad hodnotou).
2. Co je v pásu nahoře, se v sekcích neopakuje.
3. Upozornění hned pod pásem, ne mezi poli.
4. Sekce s nadpisem normálním písmem; **varianta B**: dvojice podobných sekcí vedle sebe, jinak pod sebou.
5. Popisky v pevném sloupci **200 px** ve všech skupinách (CSS v `investra_theme/static/src/scss/theme.scss`), pole začínají na stejném místě.
   Popisky, které se nevejdou, zkrátit (např. „Podílí se na spol. položkách“, „Rozdíl ze zaokr. nese“).
6. Štítky pásu čísel normálním písmem (ne versálky) – upravit i bod 3 zásad. Číslování sekcí 1.–3. jen u Úpisu a odkupu (postup zadání).
7. Podrobnosti a tabulky v záložkách.

### 2.2 Obrazovky (každá: nadpis, pás, sekce B podle návrhu)
- **Obchod** (`view_trade_form` + dědění): nadpis ISIN + název; pás Fond, Portfolio, Nákup/prodej, Datum obchodu; pás čísel Kusy, Drženo, Prodat vše;
  Cena | Vypořádání, Poplatek | Zařazení; Cena za kus jako ostatní pole (popisek vlevo).
- **Úpis a odkup** (`view_movement_form`): pás Typ, Datum, Měna, Stav; upozornění pod pásem; sekce Zdroj, 1. Zadání, 2. Poplatek, 3. Výsledek pod sebou.
- **Pravidlo úplaty** (`view_fee_rule_form`): nadpis název; pás Fond, Druh, Článek statutu; upozornění; Komu se účtuje | Výpočet; záložky Verze sazby, Historie.
- **Třída fondu** (`view_fund_class_form`): nadpis „kód – název“; pás Fond, Měna, ISIN; Třída | Kurz a kusy; Vstupní poplatek | Výstupní poplatek; „Sazba“ v %.
- **Nástroj** (`view_instrument_form`): nadpis ISIN + název; pás Typ, Měna, Splatnost, Trh; obě upozornění nahoře; Identifikace | Ocenění a klasifikace; Úročení | Test SPPI.
- **Splátka** (`view_repayment_form`): nadpis nástroj (u CP ISIN + název) + šedě druh splátky; pás Fond, Portfolio, Druh, Datum; pás čísel Jistina, Úrok,
  Poplatek, Celkem; Splátka (zbývající jistina před/po, kurz) | Záznam.
- **Derivát** (`view_derivative_form`): nadpis druh a měnový pár + šedě datum vypořádání; pás Fond, Portfolio, Číslo smlouvy, Datum obchodu; Druh výběrem; Smlouva | Po sjednání.
- **Dividenda** (`view_dividend_event_form`, obdobně `view_dividend_form`): nadpis ISIN + název; pás čísel Hrubá, Srážka, Čistá; Nárok | Srážka; držitelé v záložce se součtovým řádkem.
- **Účetní událost** (`view_event_form`): pás Fond/kniha, Datum, Druh, Zdroj (odkaz); pás čísel Částka, Doklad, Storno doklad; řádky v záložce.
- **Daňové pravidlo** (`view_tax_rule_form`): nadpis název; pás Druh, Metoda, Sazba dnes, Stav (jen tam); sekce Účty; záložky Sazby, Poznámka, Historie.
- Ostatní formuláře (nastavení, číselníky): jen CSS; kde má záznam název a chybí nadpis, dát ho do nadpisu; skupiny bez nadpisu pojmenovat.

### 2.3 Dialogy (všechny průvodce – `TransientModel`, dnes ve 13 souborech; nejdřív vypiš seznam, nedialogové vynech s důvodem)
Nadpis = sloveso a co („Stornovat obchod“, „Vrátit ocenění k přepracování“); první řádek = o jaký záznam jde čitelně (ISIN, název, kusy, datum);
„Co se stane“ jako krátký seznam bez žlutého rámečku; pole v jednom sloupci (popisky 200 px), povinná s *; hlavní tlačítko pojmenované akcí,
u nevratných akcí (storno, vrácení) v barvě Ember; druhé tlačítko „Zpět“. Ruční kurz: „Kurz za {množství} {měna}“, vyhlášený kurz šedě vedle.

### 2.4 Kritéria přijetí
Testy `all` bez chyb; snímek 35/39 beze změny; v prohlížeči projít obrazovky z 2.2 a oddílu 0 podkladu (po ZJ-27) a všechny dialogy a vypsat je ve zprávě jako seznam ke kontrole.

## 3. ZJ-27 Zařazení z obchodu (červená zóna – kód jen podle `davka-ZJ-24-27/plan-ZJ-27-technicky.md`; bez „Schválil Martin“ v hlavičce STOP)
Cíl: zařazení nástroje do portfolia vzniká samo při zaúčtování obchodu a nic se v něm ručně nevyplňuje. Kategorie z portfolia (povinná, obchod
jen do schváleného portfolia, žádné výchozí portfolio fondu), způsob ocenění z nástroje (nové „Určení reálné hodnoty“), role z pravidel účetních
profilů (i pro konkrétní ISIN; detail role ukazuje účty, pravidla a události). Ruší se ruční kategorie, odchylky od návrhu, reklasifikace a „Trh“.
Přibývá cena v % jmenovité hodnoty, místo obchodu, tlačítko Účetní zůstatky a přehled Pravidla účtování. Stávající testovací data doplní agent
sám a vypíše změny. Provádí se **před ZJ-26**; vzhled nových a změněných obrazovek řeší ZJ-26 podle oddílu 0 podkladu obrazovek.
