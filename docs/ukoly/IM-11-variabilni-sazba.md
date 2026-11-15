# IM-11 Variabilní úroková sazba

| Položka | Hodnota |
|---|---|
| Model | **Opus 5.5** |
| Zóna | červená (naběhlá hodnota, EIR, kalendář toků) – plán schvaluje Martin; úkol má dva kroky se zastávkou |
| Závisí na | IM-10 |
| Číst | `addons/custom/investra_nav/models/instrument_accrual.py`, `addons/custom/investra_nav/engine.py` (funkce `amortised_cost`, `linear_accrual`, `year_fraction`), model `investra.instrument.cashflow` v `investra_instruments/models/instrument.py`, model splátek `investra.instrument.repayment`, `docs/predpisy-a-standardy.md` |

**Stav dnes (ověřeno v kódu 15. 11. 2026):** nástroj má jednu sazbu `coupon_rate`; generátor z ní spočítá všechny toky
najednou; po první splátce kalendář nejde přegenerovat; `amortised_cost` počítá EIR z pořizovací částky a všech toků
od nákupu. Změna budoucích toků by tak zpětně změnila EIR i naběhlou hodnotu minulých dnů. Variabilní sazba tedy
dnes není podporovaná.

**Požadavek uživatele 15. 11. 2026:** uživatel musí umět sazbu měnit; budoucí toky se odhadují poslední známou sazbou;
při změně sazby se budoucí toky upraví (kvůli EIR).

**Návrh k rozhodnutí (doporučená varianta):**
1. Nástroj: `rate_type` (pevná / variabilní, výchozí pevná). U variabilní tabulka období sazeb
   `investra.instrument.rate.period`: platí od, sazba % p.a., poznámka (např. referenční sazba a marže, jen informativně),
   zadal, kdy. První řádek = dnešní `coupon_rate`; `coupon_rate` u variabilní ukazuje poslední známou sazbu (jen ke čtení).
2. Tok kalendáře dostane příznak „odhad“ (`estimated`). Generátor: období se známou sazbou počítá touto sazbou
   (období přes změnu sazby po částech), budoucí období poslední známou sazbou a označí je jako odhad.
3. Nová sazba: tlačítko „Zadat novou sazbu“ (průvodce: platí od, sazba, poznámka) přepočítá jen toky Úrok s datem
   po „platí od“, které nejsou splacené; splacené a minulé toky a jistina se nemění. Změna se zapíše do historie nástroje.
4. EIR: u variabilní sazby se efektivní míra přepočítá prospektivně ke dni změny sazby z naběhlé hodnoty k tomuto dni
   a nových odhadovaných toků; ke dni změny nevzniká výsledkový rozdíl a naběhlá hodnota minulých dnů se nemění.
   Opora: IFRS 9 odst. B5.4.5 (pravidelné přecenění toků u nástroje s pohyblivou sazbou mění efektivní úrokovou míru);
   jiné změny odhadu toků by šly podle B5.4.6 (úprava hrubé účetní hodnoty do výsledku) – ty tento úkol neřeší.
   **Odkazy jsou z paměti; krok 1 je ověří proti znění IFRS 9 přijatému EU a neověřené označí.**
5. Schválená ocenění a zaúčtované doklady se zpětně nemění; nová sazba se projeví od nejbližšího ocenění. Nová sazba
   s „platí od“ před datem posledního schváleného ocenění fondu, který nástroj drží, se odmítne s hláškou.

**Varianty k bodu 4 (krok 1 je popíše s dopadem na čísla):** (a) prospektivní přepočet EIR podle B5.4.5 – doporučeno;
(b) ponechat původní EIR a rozdíl dát do výsledku podle B5.4.6 – u běžné pohyblivé sazby nepřiléhavé.

**Krok 1 – jen návrh, bez kódu:** ověřit body 1–5 proti kódu a standardu, sepsat `docs/navrh-variabilni-sazba.md`
(nejvýš 80 řádků: datový model, algoritmus přepočtu, dopad na lineární úročení, na nástroje v reálné hodnotě –
kupónová období a naběhlý úrok obchodu –, na prodej, migrace, seznam testů s číselným příkladem), commit, **zastavit se**
a počkat na schválení Martina.

**Krok 2 – implementace po schválení** (nová relace, Opus): podle schváleného návrhu; testy všech modulů `investra_*`
na dočasné `investra_ci_master`; očekávané hodnoty stávajících referenčních scénářů se nesmí změnit (nástroje s pevnou
sazbou počítají stejně jako dosud).

**Mimo rozsah:** automatické stahování referenčních sazeb, ECL, deriváty, změny účtování a účetních rolí.

**Commit:** krok 1 `Návrh variabilní sazby`; krok 2 `Variabilní sazba: období sazeb, odhad toků a přepočet EIR`

## Výsledek

**Krok 2 hotový 15. 11. 2026** (Opus 5.5) podle schváleného návrhu: 1) EIR varianta a), 2) archivace nahrazených toků,
3) „platí od“ kterýkoli den, mimo začátek kupónového období upozornění. Rozhodnutí v `docs/rozhodnuti.md`
(„Variabilní úroková sazba“), ověření IFRS 9 B5.4.5/B5.4.6 v `docs/otevrene-body.md` – **odkazy dál NEOVĚŘENÉ**.

Změněné soubory (vše `addons/custom/investra_nav`, verze 20.0.0.28.9 → 20.0.0.29.0):
- `models/instrument_rate.py` (nový): `rate_type`, model `investra.instrument.rate.period`, průvodce
  `investra.instrument.rate.wizard` („Zadat novou sazbu“, text Co se stane, náhled toků, upozornění), pole toku
  `active`, `estimated`, `superseded_on`, `introduced_on`; přepočet a návrat toků, kontroly, historie nástroje.
- `models/instrument_accrual.py`: generátor po částech u variabilní sazby (pevná větev beze změny, data kupónů jen
  vytažena do `_schedule_days`); `_accrued_value` po úsecích (EIR i lineárně); `_earned_coupon_unit` po úsecích.
- `engine.py`: `amortised_cost_segments`. `views/nav_views.xml`: jen XPath (Druh sazby, tlačítko, sloupec Odhad,
  záložky Období sazeb a Nahrazené toky, formulář průvodce). `security/ir.access.csv`, `migrations/20.0.0.29.0`.
- `tests/test_variable_rate.py` (13 testů), `tests/__init__.py`.

Číselný příklad návrhu (test `test_design_example`, posunutý do 2029 se stejnými počty dní, act365): nákup
1 000 000 ks za 0,98, pololetně 4 %, od 1. 7. nová sazba 5 %. Kupón 1. 7. 19 835,62 beze změny, kupón 1. 1.
20 164,38 → 25 205,48 (původní tok archivován, nahrazen od 1. 7.). AC 1. 4. = 994 608,63 před i po změně,
AC 1. 7. = 989 765,37 (bez skoku), EIR1 = 7,228004 %, AC 1. 10. = 1 007 329,58.

Testy (dočasná čistá `investra_ci_master`, instalace všech 16 modulů `investra_*` + `l10n_cz`, pak `-u` všech
s `--test-enable --test-tags /investra_*`): **0 failed, 0 error(s) of 675 tests** (z toho `investra_nav` 388).
Dva řádky ERROR v logu vyvolávají testy záměrně (`investra_instrument_master` test povinného důvodu průvodce,
`investra_rates` test neúspěšného stažení kurzů); s touto změnou nesouvisí. Očekávané hodnoty stávajících
referenčních scénářů ani testů se neměnily.

Migrace na kopii `investra_test` (dočasná `investra_ci_migrace` přes pg_dump, zdroj jen čten): upgrade bez chyb,
9 nástrojů pevná sazba, 9 toků platných, 0 období. Snímek 288 výpočtů (naběhlá hodnota, úrok v RH, naběhlý kupón
pro všechny pozice ke 30 datům, toky, kupónová období) před upgradem se starým kódem a po něm: **0 rozdílů**.
Obě dočasné databáze i filestore smazány. `investra_test` ani `investra_vzhled` se nezměnily.

Odchylky od návrhu: (1) tok má navíc `introduced_on` (od které změny platí) – bez něj nejde po dvou změnách složit
kalendář úseku; (2) migrace nezakládá období sazby u pevné sazby, vznikne až přechodem na variabilní (u pevné by
zastarávalo); (3) sazba platná od D se uplatní na úrok od D, kupón splatný v den D zůstává podle staré sazby
(odpovídá příkladu návrhu); (4) příznak Odhad = kupónové období začíná po posledním „platí od“.

Neověřeno: UI v prohlížeči (formulář, průvodce) – jen testy a instalace pohledů; znění IFRS 9; prodej v naběhlé
hodnotě dál nepodporovaný. Generátor u variabilní sazby s nahrazenými toky odmítne (sazba jen průvodcem).
Návrh vzhledu: žádný.

## Převzetí
