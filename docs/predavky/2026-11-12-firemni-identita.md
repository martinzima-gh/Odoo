# Předávka 2026-11-12 – firemní identita ve vzhledu Odoo

## Cíl
Přenést firemní identitu Investra (Brand manuál 1.0) do vzhledu Odoo; vzhled upravuje uživatel s Copilotem v zelené zóně.

## Stav
- Větev `feature/nav-prototyp` (pushnuto); pravidla `bdfa76a`, modul `investra_theme` v následujícím commitu.
- Pravidla pro Copilota: `.github/copilot-instructions.md`, oddíl „Firemní identita ve vzhledu Odoo“.
- Rozhodnutí v `docs/rozhodnuti.md` a v Claude Doc; logo v `docs/otevrene-body.md` (Chybějící podklady).
- Copilotův necommitnutý návrh v `~/odoo-review` (větev AG-016) převzat a vrácen, klon je čistý.

## Hotové
- Barvy a role podle manuálu ověřené, kontrasty spočítané (WCAG 2.2 AA): text jen Petroleum 0/Petroleum/Petroleum 2, Lagoon, Graphite, Graphite 2; Ember 3,5 : 1 jen akcent.
- Písmo Montserrat (rozhodl uživatel; Investra Sans z šablony Wordu ne), základ Regular 400, `tabular-nums`, bez CDN.

## Zbývá
1. Hotovo: modul `investra_theme` 20.0.0.1.0 nainstalován v `investra_test`, 3 testy OK (zkompilované CSS má Petroleum, Lagoon a Montserrat z modulu `web`, bez CDN). Vizuálně zkontroluje uživatel (http://127.0.0.1:8071; lišta tam zůstává červená kvůli `investra_env_banner`).
2. Instalace do `investra_dev` jen na pokyn uživatele.
3. Logo až po dodání vektoru od Investry.

## Otevřené otázky
- Rozpor manuál (Montserrat) × šablona Wordu 02 (Investra Sans) – pro Odoo platí manuál; sjednocení je věc Investry.

## Soubory pro novou relaci
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.agents/rules/10-zony.md`
