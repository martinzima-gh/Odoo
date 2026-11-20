# ZJ-19 Dividendy a ex-kupón dluhopisů

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, ocenění, NAV); plán schválil Martin 19. 11. 2026 |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (z `main` po sloučení ZJ-13, ZJ-14, AG-019 až AG-022) |
| Větev úkolu | `ukol/ZJ-07-dane-a-tridy` (celá dávka ZJ-07 až ZJ-19) |
| Zadal, dne | Claude (hlavní relace) podle dávky ze 19. 11. 2026, založeno 20. 11. 2026 |
| Navazuje na | `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`; deník 2026-11-19 (dávka ZJ-07 až ZJ-19) |
| Model | běh 3 (Sonnet 5.5), viz `docs/ukoly/podklady/davka-ZJ-07-19/00-prehled.md` |

**Cíl:** Dividenda jako záznam s ex-datem, srážkou a zápočtem (`investra.dividend`), zaúčtovaná na 714100/714200/714300, 681100, 681400 a pohledávky (D14); ex-kupónová lhůta dluhopisu se záporným naběhlým úrokem. Výnos patří držiteli k ex-datu − 1 den.

**Rozsah souborů:** `investra_nav` (nový model, oprávnění, náhled, testy), `investra_instruments` (ex_coupon_days, ex_date toku, naběhlý úrok obchodu), `investra_chart_fund` (analytické účty pohledávek), formuláře (běh 6), manuál.

**Mimo rozsah:** Výplata dividend investorům dividendové třídy (IS).

**Kritéria přijetí:** Testy dividendy (česká, zahraniční se zápočtem a přeplatkem, výplata s kurzovým rozdílem, storno) a `test_ex_coupon.py` (nákup a prodej v ex-lhůtě, ocenění bez skoku, lhůta 0 = dnešní chování); referenční scénáře beze změny.

**Schválený plán:** `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 7 (s „Přednostmi“ a oddílem 1). Obsah se sem nekopíruje;
odchylky od něj se zapisují do Výsledku.

## Výsledek

Běh 3 dávky (Claude Sonnet 5.5, 20. 11. 2026), větev `ukol/ZJ-07-dane-a-tridy`. Plán: oddíl 7 zadání dávky.

- **Změněné soubory:** nový `investra_nav/models/dividend.py` (model `investra.dividend`), `security/ir.access.csv`; `models/instrument_accrual.py`
  (ex-kupón: `_accrued_coupon_unit`, `_accrued_value`, `_schedule`, `_held_positions`, `_ex_entitled_units`, `_validate`, `_expected`,
  `_missing_scheduled`), `models/valuation.py` (uzavřená pozice s nevyplaceným kupónem, profil přecenění), `models/posting_preview.py`
  (náhled bere analytický účet řádku); `investra_instruments/models/instrument.py` (`ex_coupon_days`, `cashflow.ex_date`, kontrola
  znaménka naběhlého úroku); `investra_posting/models/event.py` (druhy události `dividend`, `dividend_payment`); `investra_chart_fund`
  (účty 714100–714300, 667300/667400, 681100–682000, 347300, 348000, 341210, 341220; `EXTRA_ROLE_ACCOUNTS`; migrace 20.0.0.13.0);
  `investra_nav/migrations/20.0.0.39.0` (účty pohledávek do profilů přecenění); testy `test_dividend.py` (15), `test_ex_coupon.py` (7),
  upravený `test_fx_profile_valuation.py`.
- **Ověřeno:** `investra_chart_fund,investra_fund,investra_posting+` (1037 testů, po úpravě testu profilu 0 selhání); snímek ocenění 35
  shodný. Dividendy: česká 10 000 / 15 % (714100, 681100, pohledávka 8 500), zahraniční 7 000 EUR / 27,5 % / smluvní 10 % (681400 700,
  pohledávka k vrácení 1 225 EUR, kurz 25 → 24 ztráta z kurzu), USD s kurzovým ziskem, přeplatek jako náklad, nárok k ex-datu − 1
  (nákup v ex-datu bez nároku, prodej v ex-datu nárok neubere), portfolio třídy B, storno vyplacené dividendy, NAV s pohledávkou, náhled.
  Ex-kupón: nákup v ex-lhůtě (záporný naběhlý úrok −27,78, ocenění 20. 6. a 30. 6. bez skoku, kupón nedostane), prodej v ex-lhůtě
  (kupón 500 dostane prodávající, návrh splátky i pro prodanou pozici, pozice po výplatě 0), kontrola znaménka, lhůta 0 = dnešní chování.
- **Neověřeno:** ex-kupón u nástroje v naběhlé hodnotě (kód `_accrued_value` je upravený, bez testu); dividenda v portfoliu s kategorií
  FVOCI (běh 5); migrace na kopii ze zálohy (běh 7).
- **Odchylky od plánu:**
  1. Druh dividendy: země emitenta z `issuer_id.country_id` (modul Instrument master, je-li nainstalován), jinak z prvních dvou znaků ISIN;
     nástroj bez ISIN = česká. Sražená sazba výchozí 15 % u české, 0 u zahraniční (sazby jsou v procentech, ne zlomek).
  2. Typ nástroje v nabídce: `type_id.kind` akcie, fond, účast (v kódu nejsou skupiny equity/fund).
  3. Nezapočitatelný přeplatek zahraniční daně jako náklad jde na hlavní účet role `expense_other` (667000); **daňovou uznatelnost určí
     metodik** (podle § 25/1/s ZDP je daň z příjmů neuznatelná – výjimka „Mimo základ“ na účtu, běh 4/5).
  4. Pohledávky: 341210 „Pohledávky z dividend a kupónů“ a 341220 „Pohledávky – zahraniční daň k vrácení“ jsou pracovní čísla (další
     účty role `receivable_other`), **k potvrzení Martinem**. Obě jsou v profilu přecenění fondu.
  5. Storno dividendy bez schvalovací matice (nová činnost matice `dividend_reverse` by zasáhla `investra_fund`, ZJ-01/02): vyžaduje roli
     přípravy a důvod. Návrh k rozhodnutí.
  6. Řádky výnosu a daně nemají měnu (jen pohledávky a banka), stejně jako poplatek obchodu.
  7. Prodaná pozice s nevyplaceným kupónem (jen nástroje s ex-kupónovou lhůtou) drží kupón na účtu nástroje a ocenění pro ni založí řádek
     bez kusů (hodnota = nevyplacený kupón); bez ex-lhůty se chování nemění. Zbytek do 2 haléřů z zaokrouhlení naběhlých úroků obchodů.
  8. Kontrola součtů dividendy (sražená ≤ hrubá, započitatelná ≤ sražená) je při zaúčtování, ne při uložení (přepočet polí by ji při
     změně kusů zablokoval).
  9. Předvyplnění splátky u kupujícího v ex-lhůtě beze změny (kupón mu návrhy podle kalendáře nezaloží); pevná kontrola „úrok ≤ nárok“ není.
- **Otevřené otázky a návrhy mimo rozsah:** dividenda z dceřiné společnosti (osvobození § 19) – účty a daň ručně; výplata dividend investorům (IS).

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
