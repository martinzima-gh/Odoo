# ZJ-08 Manažerská třída bez účasti na výsledku portfolia a ruční krystalizace

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (`investra_nav/models/valuation.py`, `engine.py`, alokace tříd); nejdřív plán, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Opus 5.5 |

**Kontext:** fond má např. 5 tříd; 4 sdílejí portfolio, 1 „manažerská“ jen přijímá výkonnostní odměnu (přijímající třída pravidla).
Dnes se alokační poměr počítá z předběžného kapitálu všech tříd (APT = PFKT / PFK), takže manažerská třída by od dalšího ocenění dostávala
podíl na zisku i ztrátě portfolia. Pořadí nároků (`engine.waterfall`) to čistě nevyřeší (zbytek pevnými podíly, ztráta poměrem kapitálů).

**Rozhodnuto 17. 11. 2026 (Martin), deník „Třída bez účasti na výsledku portfolia“ a „Ruční krystalizace“:**
1. Třída má volbu **Neúčastní se výsledku portfolia**. Její kapitál = předchozí kapitál + ΔT (přijaté odměny, úpisy a odkupy třídy,
   položky s třídou). Ostatní třídy si dělí FK − kapitál těchto tříd alokačním poměrem spočteným jen mezi sebou. Kontrola ΣFKT = FK zůstává.
2. Bez výnosu je celý kapitál třídy včetně případného symbolického úpisu (úpis může i nemusí být).
3. Ztrátu nese jen ručně doloženou úplatou (stávající mechanismus); odměny se ve třídě hromadí, odkup je ruční.
4. **Krystalizace „Ručně“:** nová volba u pravidla výkonnostní odměny; krystalizuje se jen v ocenění, kde ji uživatel výslovně vyžádá.

**Plán má obsahovat:**
1. Kde je volba (třída, nebo řádek alokačního schématu s platností od data) – varianty a doporučení; zámek po prvním zaúčtovaném ocenění.
2. Úprava výpočtu v `_compute_all` / `_finish` a v `engine` (vzorec, pořadí kroků, vztah k pořadí nároků – kombinaci buď podpořit, nebo zakázat kontrolou).
3. Ruční krystalizace: kde ji uživatel vyžádá (pole v ocenění ve stavu Návrh, po pravidlech), zápis do historie kroků ocenění, zda jde přes schvalovací matici;
   chování `_is_crystallisation` a srovnávací hodnoty / high-water mark.
4. Zobrazení: karta třídy a přemostění (třída bez podílu na společné změně), XLS pro depozitáře.
5. Testy: příklad 4 + 1 třída (zisk i ztráta portfolia, přijetí odměny, symbolický úpis, odkup manažerské třídy, ruční úplata jako ztráta,
   ruční krystalizace vs. nekrystalizující ocenění); referenční scénáře beze změny.
6. Manuál (kapitola ocenění a třídy).

**Mimo rozsah:** statut a zdanění výnosu manažera (ověří Martin u právníka a daňového poradce); třída portfolia (ZJ-09).

## Technický plán

Schváleno Martinem 19. 11. 2026: `docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md`, oddíl 3 (D1–D6), s „Přednostmi“ a oddílem 1 (D13). Obsah se sem nekopíruje.

- Teď (běh 1, Opus 5.5): body 1–3 – pole „Podílí se na společných položkách“ na třídě, výpočet (poměr 0, kapitál = předchozí
  + pohyby + specifické položky), kontrola na alokačním schématu, upozornění na úplatu z třídy bez podílu (D6, logika).
- Později: **bod 4 ruční krystalizace** (zůstává v tomto zadání, neprogramuje se).
- Běh 6 (Copilot): přepínač ve formuláři třídy, zobrazení upozornění D6 ve formuláři pravidla, manuál.
- Odchylky od plánu se zapisují do Výsledku.

## Výsledek

Běh 1 dávky (Claude Opus 5.5, 20. 11. 2026), body 1–3 a D6; bod 4 (ruční krystalizace) později. Plán: oddíl 3 zadání dávky.

- **Změněné soubory:** `investra_fund/models/fund.py` (pole „Podílí se na společných položkách“, kontrola aspoň jedné třídy s podílem),
  `investra_nav/models/fund_class.py` (zámek), `investra_allocation/models/allocation.py` (třída bez podílu nesmí být ve schématu, obě strany),
  `investra_nav/models/valuation.py` (`_class_context`, `_shared_neutral`, `_class_value`, `_apply_scheme`, `_finish`, přemostění, kontrola
  `fee_no_common_class`), `investra_nav/models/fee_rule.py` (`no_common_class_warning`); testy `test_class_no_common.py`, `test_allocation_examples.py`.
- **Ověřeno:** D5 (zisk a ztráta nemění M, přijatá odměna jen M, daň 21 % nesou A a B, pravidlo s příjemcem M, symbolický úpis, odkup a ruční
  úplata M, pořadí nároků jen mezi A a B, nulový kapitál tříd s podílem zastaví, zámek, upozornění D6); příklady oddílu 10 „Alokační schéma“
  a „Třída bez podílu“ vyšly všechny podle textu (text se neměnil). Snímek 35 a 39 shodný (fond bez třídy bez podílu = dnešní výsledky).
- **Odchylky od plánu:**
  1. `neutral_capital` (NFK) se ukládá jako sdílená část bez kapitálu tříd bez podílu; u fondů bez takové třídy beze změny.
  2. Haléřové zaokrouhlení součtu tříd nese jen třída s podílem na společných položkách.
  3. Kontrola ocenění `fee_no_common_class` vzniká jen u fondu s třídou bez podílu (kontroly ostatních ocenění beze změny); upozorní i na
     úplatu celého fondu (pravidlo bez tříd), jak žádá D6; daň se nehlásí (třídy nemá).
  4. Zámek: změna jen do prvního ocenění fondu ve stavu Zaúčtováno, U depozitáře, Potvrzeno, Zveřejněno nebo Stornováno.
  5. D4 (zobrazení): data přemostění u třídy bez podílu mají Změnu společnou a zaokrouhlení 0; formulář, nápověda a XLS jsou běh 6.
- **Neověřeno:** přepínač ve formuláři třídy a zobrazení upozornění D6 (běh 6); ruční zkouška v UI.
- **Otevřené otázky a návrhy mimo rozsah:** bod 4 ruční krystalizace.

## Převzetí
