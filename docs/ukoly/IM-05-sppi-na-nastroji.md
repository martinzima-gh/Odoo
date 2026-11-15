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

Hotovo 15. 11. 2026 (Claude Code, Opus 5.5), plán schválil Martin. `investra_instruments` 20.0.0.15.0.

**Změněné soubory**
- `investra_instruments/models/portfolio.py` – nástroj: `sppi_status` (not_assessed / pass / fail / na), `sppi_note`,
  `sppi_version`, `sppi_assessed_on`, `sppi_assessed_by` (jen ke čtení), pomocná `sppi_applicable`, `sppi_locked`;
  kontroly (SPPI jen u dluhu a podílových listů, odůvodnění a znění u vyhodnoceného, od 1. 1. 2026 znění (EU) 2025/1047
  podle data posouzení); zámek po prvním obchodu s nástrojem (hláška z plánu, odd. 7); změna SPPI znovu zkontroluje
  zařazení nástroje. Zařazení: `sppi`, `sppi_note`, `sppi_version` uložená vypočtená z nástroje, zápis do nich se odmítne
  („Test SPPI se posuzuje na nástroji; zařazení ho přebírá.“). Rozhodovací strom a text zdůvodnění beze změny.
- `investra_instruments/views/instrument_views.xml` – formulář nástroje: skupina „Test SPPI“ (jen u nástroje, kde se SPPI
  hodnotí, po obchodu jen ke čtení); formulář zařazení: pole SPPI jen ke čtení. Nové styly ani přesuny nejsou.
- `investra_instruments/migrations/20.0.0.15.0/` (pre: snímek zařazení; post: přenos, přepočet, kontrola kategorií, smazání snímku).
- Testy (jen zadání, očekávané hodnoty beze změny): `tests/common.py` (`assess_sppi`: zadání SPPI z `classify` zapíše
  na nástroj s datem posouzení = den zařazení, takže znění vychází jako dřív), `tests/test_instrument.py`,
  `tests/test_classification.py` (2 testy přesunuly zadání SPPI na nástroj; nová třída `TestSppiOnInstrument`, 6 testů),
  `investra_nav/tests/common.py` (stejná pomocná funkce).
- `tools/nav_demo/demo_vklad.py` (SPPI zadané na vkladu), `docs/sql/11-klasifikace.sql` (SELECT 9 a kontrola 10).

**Testy** – čistá dočasná databáze `investra_ci_master` podle oddílu 2 plánu (instalace všech 16 modulů `investra_*`,
`l10n_cz`, pak `-u` všech s `--test-tags /investra_…`): **625 testů, 0 selhání, 0 chyb**
(log `.test-logs/20261115-080554-im05-3c-tests.log`). `investra_vat_identified` se přeskočí sám (v databázi fondů není
společnost s českou osnovou), stejně jako dřív. Dva předchozí běhy odhalily dvě chyby, obě jsou opravené:
uložené vypočtené `sppi` nesmí mít `required` (NOT NULL při vložení) a SPPI nesmí být mezi spouštěči
`_check_classification` (Odoo 20 po výpočtu pole spouští navázané kontroly, a ta se pak spustila uprostřed výpočtu kategorie).

**Migrace** – kopie `investra_test` (pg_dump, zdroj jen čten) v dočasné `investra_ci_im05`, `-u investra_instruments`;
po konečném kódu ověřeno znovu (log `.test-logs/20261115-080843-im05-migrace-3.log`):
- zařazení podle SPPI před: Nehodnotí se 8, Splněn 1; po: stejně;
- všech 9 zařazení: SPPI, znění, povinná, vypočtená i výsledná kategorie a způsob ocenění beze změny; kontrola 10 prázdná;
- přeneseno na 4 nástroje (vklad: Splněn, (EU) 2025/1047, posouzeno 2026-09-15; 3 akcie: Nehodnotí se);
  4 dluhopisy jen v portfoliích Reálná hodnota zůstaly „Neposouzeno“;
- **nástroje s rozdílným SPPI ve více zařazeních: žádné.**
Dočasné databáze `investra_ci_im05` a `investra_ci_master` včetně filestore jsou smazané. `investra_test` ani
`investra_vzhled` se nezměnily.

**Odchylky (zdůvodnění)**
- Zařazení přebírá SPPI jen u povahy, u níž se hodnotí (dluh, podílový list); jinak „Nehodnotí se“. Výsledek stromu je
  stejný, jen podílový list posouzený jako kapitálový nástroj nenarazí na SPPI nástroje.
- Každá změna posouzení je nové posouzení: posoudil = přihlášený uživatel, datum dnes (nezadá-li se), znění podle data.
- Migrace: „Nehodnotí se“ v zařazení dluhového nástroje se přenáší jako „Neposouzeno“ (v portfoliu Reálná hodnota ho
  nikdo neposuzoval); u akcií, derivátů a účastí jako „Nehodnotí se“. Nástroj s konfliktem zůstane „Neposouzeno“,
  jeho zařazení se nepřepočtou a vypíše se do logu.
- `_default_sppi_version` na zařazení zůstává jen kvůli staré migraci 20.0.0.5.0.

**Neověřeno / neuděláno**
- Formuláře jen přes testy (`Form`) a načtení pohledů při upgradu; v prohlížeči neprohlédnuto.
- `classification_gap` v `investra_instrument_master` (komentář „doplní IM-05“) jsem nezměnil: modul není v rozsahu
  souborů úkolu a jeho test čeká u dluhopisu prázdnou mezeru. Návrh: doplnit v IM-06 („posouzení SPPI“ u dluhového
  nástroje s `not_assessed`).
- Ve filestore zůstaly složky `investra_ci_knihy` a `investra_ci_poplatky` ze starších relací (bez databází); nemazal jsem je.

## Převzetí

- 15. 11. 2026 (IM-12): kód nainstalován do `investra_test` (`investra_instrument_master` 20.0.0.6.0 installed; `investra_instruments` 20.0.0.15.0). `investra_vzhled` zatím ne, viz Výsledek IM-12. Ověřeno jen stavem modulů, logem a SELECTem, ne průchodem v UI.
