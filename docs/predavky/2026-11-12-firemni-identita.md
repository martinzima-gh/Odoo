# Předávka 2026-11-12 – firemní identita ve vzhledu Odoo

## Cíl
Přenést firemní identitu Investra (Brand manuál 1.0) do vzhledu Odoo; vzhled upravuje uživatel s Copilotem v zelené zóně.

## Stav
- Větev `feature/nav-prototyp`, commit `bdfa76a` (pushnuto).
- Pravidla pro Copilota: `.github/copilot-instructions.md`, oddíl „Firemní identita ve vzhledu Odoo“.
- Rozhodnutí v `docs/rozhodnuti.md` a v Claude Doc; logo v `docs/otevrene-body.md` (Chybějící podklady).
- Copilotův necommitnutý návrh v `~/odoo-review` (větev AG-016) převzat a vrácen, klon je čistý.

## Hotové
- Barvy a role podle manuálu ověřené, kontrasty spočítané (WCAG 2.2 AA): text jen Petroleum 0/Petroleum/Petroleum 2, Lagoon, Graphite, Graphite 2; Ember 3,5 : 1 jen akcent.
- Písmo Montserrat (rozhodl uživatel; Investra Sans z šablony Wordu ne), základ Regular 400, `tabular-nums`, bez CDN.

## Zbývá
1. Založit modul `investra_theme` (oranžová zóna, Claude): `@font-face` s Montserrat (woff2, SIL OFL, licence přibalit), SCSS proměnné Odoo 20 v `web._assets_primary_variables` s barvami; ověřit na `investra_test` a předat Copilotovi.
2. Logo až po dodání vektoru od Investry.

## Otevřené otázky
- Rozpor manuál (Montserrat) × šablona Wordu 02 (Investra Sans) – pro Odoo platí manuál; sjednocení je věc Investry.

## Soubory pro novou relaci
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.agents/rules/10-zony.md`
