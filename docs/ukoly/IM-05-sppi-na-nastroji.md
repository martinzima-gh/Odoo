# IM-05 SPPI z zařazení na nástroj

| Položka | Hodnota |
|---|---|
| Model | **Opus 5.5** |
| Zóna | **červená** – začít až po výslovném schválení uživatele |
| Plán | oddíl 1 bod 4, oddíly 2, 3.4 (řádek SPPI), 7; rozhodnutí uživatele 15. 11. 2026 |
| Číst | `addons/custom/investra_instruments/models/portfolio.py`, `tests/test_classification.py`, `views/instrument_views.xml` (formulář zařazení), poslední migraci v `migrations/` jako vzor |

**Cíl:** test SPPI je vlastnost nástroje společná pro všechny fondy; zařazení ho jen přebírá.

**Rozsah souborů:** `addons/custom/investra_instruments/` (modely, pohledy, testy, nová migrace, verze `20.0.0.15.0`).
Jiné moduly jen tam, kde jejich testy nastavují SPPI na zařazení (upravit zadání testu, ne očekávané hodnoty).

**Řešení:**
- Nástroj: `sppi_status` (not_assessed / pass / fail / na), `sppi_note`, `sppi_version`, `sppi_assessed_by`,
  `sppi_assessed_on`; po prvním obchodu s nástrojem zamčeno.
- Zařazení: `sppi`, `sppi_note`, `sppi_version` jako převzatá uložená pole z nástroje (`not_assessed` se v zařazení chová
  jako `na`); rozhodovací strom a text zdůvodnění beze změny výsledků.
- Znění IFRS 9: podle data posouzení (od 1. 1. 2026 nařízení (EU) 2025/1047), ne podle účetního období fondu.
- Migrace: hodnoty SPPI zařazení přenést na nástroj. Nástroj s rozdílnými hodnotami ve více zařazeních nepřepisovat,
  vypsat do logu migrace a do Výsledku.

**Mimo rozsah:** povaha nástroje, určení a volby (zůstávají na zařazení); účtování; referenční scénáře NAV.

**Kritéria přijetí:**
- Tentýž dluhopis se SPPI „Splněn“ je v portfoliu Držet pro inkaso v naběhlé hodnotě a v portfoliu Řízení na reálnou
  hodnotu ve FVTPL (stávající test `test_same_instrument_in_two_portfolios` drží).
- Model Držet pro inkaso nebo Inkaso i prodej s nástrojem bez posouzení SPPI se odmítne.
- Změna SPPI po prvním obchodu se odmítne.
- Migrace ověřena na kopii `investra_test` v dočasné databázi: počty zařazení podle hodnoty SPPI před a po shodné;
  kategorie IFRS 9 žádného zařazení se nezmění.
- Všechny testy modulů `investra_*` projdou; očekávané hodnoty scénářů beze změny.

**Commit:** `SPPI je vlastnost nástroje; zařazení ho přebírá`

## Výsledek

## Převzetí
