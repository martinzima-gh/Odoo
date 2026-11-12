# Návrh: náhled zaúčtování obchodu a kontrola kalendáře dluhopisu

Schválil uživatel 12. 11. 2026 (všechna doporučení). Zóna: červená (realizace a NAV), provádí Claude;
upozornění na formuláři nástroje (bod 3) zelená, zadání AG-016 pro Copilota.

## Proč

- Výsledek prodeje dnes zaúčtuje až ocenění; při zadání obchodu ho uživatel nevidí a překlep v ceně projde.
- Dluhopis bez kalendáře toků má naběhlý úrok obchodu 0 bez upozornění a ocenění úrok pozice tiše vynechá.

## 1. Záložka „Očekávané zaúčtování“ ve formuláři obchodu (návrh obchodu)

Jen výpočet, nic se neúčtuje.

**Doklad obchodu** (nákup i prodej): řádky dokladů, které vzniknou při Zaúčtovat a Vypořádat
(účet, MD, D, částka v měně nástroje). Zaúčtování i náhled používají jednu funkci `_planned_postings`
(`investra_instruments`), takže se nemohou rozejít.

**Očekávaný výsledek prodeje** (jen prodej v reálné hodnotě): stejný výpočet jako ocenění (`_realised_ccy`,
`_cost_walk` v `valuation.py`) pro pozici k datu zařazení obchodu, jednou s obchodem a jednou bez něj; rozdíl je
příspěvek obchodu:

| Řádek | Zdroj |
|---|---|
| Výnos z prodeje bez úroku | kusy × cena × kurz zaúčtování |
| Účetní hodnota prodávaných kusů | výnos − realizovaný výsledek ceny |
| Realizovaný výsledek ceny | `_realised_ccy` (proti účetní hodnotě k minulému ocenění) |
| Realizovaný kurzový rozdíl | `_cost_walk` (proti pořizovací ceně), jen cizí měna |
| Pro informaci: pořizovací cena a výsledek proti ní | `_cost_walk` |

Odhad platí při ocenění k datu obchodu bez dalších prodejů a splátek. Naběhlá hodnota: jen doklad a poznámka,
výsledek dopočítá ocenění. Úrok vydělaný do data prodeje dopočítá ocenění (není součástí realizace).

## 2. Kalendář dluhopisu

- **Formulář obchodu** (návrh, dluhopis): upozornění, když nástroj nemá žádné toky („naběhlý úrok se
  nepředvyplnil“), nebo když datum sjednání leží mimo kupónová období. Bezkupónový dluhopis (jen jistina) bez upozornění.
  Neblokuje.
- **Ocenění**: nová kontrola `bond_calendar` (upozornění, neblokuje): pozice dluhopisu bez toků kalendáře.

## Ověření

Testy: náhled dokladu = skutečný doklad (okamžité i odložené vypořádání, obě nastavení zařazení); odhad výsledku
= výsledek zaúčtovaný oceněním (koruny i cizí měna, částečný prodej po přecenění); upozornění na kalendář
(bez toků, jen jistina, mimo období); kontrola ocenění. Celá sada na čisté databázi `investra_ci_*`.
