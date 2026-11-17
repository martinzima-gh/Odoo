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

## Výsledek

## Převzetí
