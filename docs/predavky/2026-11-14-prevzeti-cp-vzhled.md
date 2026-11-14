# Předávka 2026-11-14 – převzetí Copilota (vzhled) a navazující úpravy

## Cíl
Převzít práci Copilota z `~/odoo-review` (cp/vzhled) a vyřešit jeho požadavky k rozhodnutí.

## Stav
- Větev `feature/nav-prototyp`, poslední commit `cdb1e6e` (pushnuto). Klon `~/odoo-review` cp/vzhled je obsahově shodný.
- `investra_vzhled` (port 8072) povýšené, běží; kontejner `investra-vzhled-web` založen znovu (moduly z klonu, `--dev=xml`).

## Hotové
- Převzetí CP-2026-11-13 (commit `0b64d12`, autor Copilot): pohledy, `theme.scss`, 20 návrhů `docs/vzhled/`.
- Testy: čistá DB 402/0; `investra_test` jen 5 známých selhání matice.
- Seznam Ocenění: výchozí seskupení podle fondu, řazení z modelu, sloupec Fond skrytý; FK/NFK bez součtu ve skupinách.
- Úpisy a odkupy: datum sestupně, fond abecedně; sloupec „Změna kapitálu ±“ (Lagoon/Ember, jen zobrazení).
- Ceny: kód a ISIN převzaté z nástroje (related, neukládá se).
- Rozhodnutí zapsána v `docs/rozhodnuti.md` i v Claude Doc.

## Zbývá
1. **Přehled fondů – data a stavy (bod 2.3).** První krok: v `investra_dashboard/models/dashboard.py` navrhnout
   (zatím neprogramovat) pole karty: poslední ocenění (datum, stav), další ocenění (datum z kalendáře + stav
   existujícího návrhu, jinak „Nezaloženo“), termín ČNB (Otevřeno / Podáno / Po lhůtě; datum podání model nemá,
   nevymýšlet), FK a Výsledek období ocenění (součet `shared_result` + `delta` tříd posledního zaúčtovaného
   ocenění, výpočet v modelu, u prvního ocenění pomlčka). Navrhnout s variantami, rozhoduje uživatel.
   Pozor: test `test_submitted_deadline_is_ignored` dnes podané výkazy skrývá.
2. Návrh `docs/vzhled/navrh-seznam-upisu-odkupu.html` – staré řazení a chybí znaménko.
3. `theme.scss`: `.o_investra_metric_item` má `#ffffff` místo barvy z palety (úkol pro Copilota).

## Poznámky
- Pro čistou DB: nejdřív `-i` modulů bez testů, pak `-i l10n_cz`, pak `-u` s testy (v paměti).
- Jeden uživatel v `investra_vzhled` má jazyk en_US, a proto vidí datum mm/dd/rrrr.

## Číst
- `docs/ukoly/CP-2026-11-13-vzhled-obrazovek.md` (část Požadavky k rozhodnutí, bod 3)
- `addons/custom/investra_dashboard/models/dashboard.py`
- `docs/vzhled/navrh-prehledu-fondu.html`
- `addons/custom/investra_nav/static/src/valuation_summary/valuation_summary.js`
