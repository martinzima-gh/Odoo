# IM-06 Portfolio: kategorie, schválení, zámek a kompatibilita

| Položka | Hodnota |
|---|---|
| Model | **Opus 5.5** |
| Zóna | červená (logika klasifikace) – začít až po výslovném schválení uživatele |
| Plán | oddíl 1 bod 3, oddíly 2, 3.5, 3.6 (kompatibilita), 5, 6 (Portfolia), 7 |
| Číst | `addons/custom/investra_instruments/models/portfolio.py`, formulář a seznam portfolia v `views/instrument_views.xml`, `docs/vzhled/navrh-seznamu-obchodnich-modelu.html` |

**Cíl:** portfolio přímo určuje oceňovací kategorii; nástroj nejde zařadit do nekompatibilního portfolia ani přes import
nebo API; po prvním obchodu jsou klasifikační pole zamčená.

**Rozsah souborů:** v novém addonu `models/portfolio.py`, `views/portfolio_views.xml`, `tests/test_portfolio.py`, manifest.
Modul `investra_instruments` se nemění.

**Důležité:**
- Portfolio bez kategorie (stávající data a testy) se chová jako dosud; kontrola kompatibility platí jen s kategorií.
- Kontrolu navázat na vstupní pole zařazení a spustit ji i při změně kategorie portfolia.
- Schválení: tlačítko pro skupinu schvalování, vyplní `approved_by`, `approved_on`; Uzavřít nastaví `valid_to`.
- Zámek rozšiřuje stávající `write` portfolia; `is_locked` a `lock_date` z prvního obchodu bez zásahu do obchodu.

**Mimo rozsah:** reklasifikace, účtování, nová činnost schvalovací matice, povinnost kategorie v databázi.

**Kritéria přijetí** (testy 1–7 a 11 zadání):
1. AC / Držet pro inkaso přijme kupónový dluhopis se SPPI „Splněn“.
2. AC odmítne nástroj se SPPI „Nesplněn“ i „Neposouzeno“.
3. AC odmítne derivát a podílový list s právem odkupu.
4. FVOCI_D / Inkaso i prodej přijme dluhopis se SPPI „Splněn“.
5. FVOCI_E přijme jen kapitálový nástroj s volbou 5.7.5; model Obchodování v něm nejde nastavit.
6. FVTPL přijme derivát; bez důvodu klasifikace nejde schválit.
7. Po prvním obchodu nejde změnit kategorii, obchodní model, důvod ani fond.
8. Důvod klasifikace ukazuje pod polem české vysvětlení.
9. Testy `investra_instruments`, `investra_counterparty`, `investra_nav` a `investra_cnb` projdou beze změny.

**Commit:** `Portfolio: kategorie, schválení, zámek a kompatibilita`

## Výsledek

## Převzetí
