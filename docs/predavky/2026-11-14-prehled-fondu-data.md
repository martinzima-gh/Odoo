# Předávka 2026-11-14 – Přehled fondů: data a stavy karty

## Cíl
Doplnit kartu Přehledu fondů (`investra_dashboard`) o poslední a další ocenění, termín ČNB, FK a Výsledek za období.

## Stav
- Větev `feature/nav-prototyp`, commit „Přehled fondů: data a stavy karty“ (pushnuto).
- `investra_dashboard` 0.2.0, jen počítaná pole, bez migrace. Testy na čisté DB 19/0; `investra_test` NEpovýšena
  (později povýšena se souhlasem, viz Zbývá 2).

## Hotové
- Model a pohledy podle rozhodnutí 2026-11-14 „Přehled fondů – data a stavy karty“ (deník i Claude Doc rev 339).
- Kurzy tříd z karty i modelu odstraněny; test podaných termínů přepsán (Podáno se ukazuje, výjimku nevyvolá).

## Zbývá
1. Hotovo: seznam Ocenění jen s aktuální verzí (rozhodnutí 2026-11-14, `investra_nav` 0.28.1), testy čistá DB 332/0.
   Hotovo: graf kurzu kreslí změnu od předchozího ocenění v barvě změny (vizuálně neověřeno, Odoo s klonem odoo-dev neběží).
2. Hotovo: klon `~/odoo-review` (cp/vzhled) sloučen s větví; `investra_vzhled` a `investra_test` povýšené
   (zálohy `zalohy/*-2026-11-14-pred-upgradem.dump`); `investra_test` 332/0.
3. Hotovo: sloupec Změna FK (0.28.2) a pravidlo „nové ocenění až po zveřejnění předchozího“ (0.28.3); obě DB
   povýšené (zálohy `*-pred-upgradem-2.dump`), `investra_test` 338/0.
4. **Vzhled karty Přehledu podle `docs/vzhled/navrh-prehledu-fondu.html`** – Copilot udělal jen HTML návrh, v Odoo
   není; čeká na volbu uživatele (Claude hned, nebo úkol pro Copilota).
5. Export Claude Doc do `docs/architektura.md` (poslední export rev 333, Doc je na rev 343).
6. Z předchozí předávky: návrh `docs/vzhled/navrh-seznam-upisu-odkupu.html` (řazení, znaménko); `theme.scss`
   `.o_investra_metric_item` `#ffffff` → barva palety (Copilot); karta Přehledu ve firemních barvách (Copilot, zelená zóna).

## Číst
- `addons/custom/investra_dashboard/models/dashboard.py`
- `docs/rozhodnuti.md` (poslední řádek)
- `addons/custom/investra_nav/models/valuation.py` (`action_return`, `_new_version`)
