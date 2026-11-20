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

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Odchylky od plánu:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
