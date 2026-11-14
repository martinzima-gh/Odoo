# Předávka 2026-11-14 – Přehled fondů: data a stavy karty

## Cíl
Doplnit kartu Přehledu fondů (`investra_dashboard`) o poslední a další ocenění, termín ČNB, FK a Výsledek za období.

## Stav
- Větev `feature/nav-prototyp`, commit „Přehled fondů: data a stavy karty“ (pushnuto).
- `investra_dashboard` 0.2.0, jen počítaná pole, bez migrace. Testy na čisté DB 19/0; `investra_test` NEpovýšena
  (run_tests.sh hlásí rozdíl verze 0.1.0 → 0.2.0, upgrade jen se souhlasem).

## Hotové
- Model a pohledy podle rozhodnutí 2026-11-14 „Přehled fondů – data a stavy karty“ (deník i Claude Doc rev 339).
- Kurzy tříd z karty i modelu odstraněny; test podaných termínů přepsán (Podáno se ukazuje, výjimku nevyvolá).

## Zbývá
1. Hotovo: seznam Ocenění jen s aktuální verzí (rozhodnutí 2026-11-14, `investra_nav` 0.28.1), testy čistá DB 332/0.
   Otevřená otázka uživatele: barva poklesu v grafu kurzu (čísla Ember mají, graf ne) – čeká na volbu varianty.
2. Upgrade `investra_vzhled` a `investra_test` (`investra_dashboard` 0.2.0, `investra_nav` 0.28.1) – se souhlasem.
3. Export Claude Doc do `docs/architektura.md` (poslední export rev 333, Doc je na rev 339).
4. Z předchozí předávky: návrh `docs/vzhled/navrh-seznam-upisu-odkupu.html` (řazení, znaménko); `theme.scss`
   `.o_investra_metric_item` `#ffffff` → barva palety (Copilot); karta Přehledu ve firemních barvách (Copilot, zelená zóna).

## Číst
- `addons/custom/investra_dashboard/models/dashboard.py`
- `docs/rozhodnuti.md` (poslední řádek)
- `addons/custom/investra_nav/models/valuation.py` (`action_return`, `_new_version`)
