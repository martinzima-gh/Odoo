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

## Převzetí
