# Předávka 10. 11. 2026: uživatelská přívětivost

Pro relaci Claude Code ve VS Code (hlavní vývojář, `~/odoo-dev`). Práce vznikla v relaci aplikace Claude na Windows
v klonu `TEST\odoo`, větev `revize/claude-app` (z `feature/nav-prototyp` na `11da351`). Podle `CLAUDE.md` se relace
aplikace pro projekt nepoužívá, proto se vše předává sem. Kód se neměnil, jen dokumenty v `docs/`.

## 1. Převzetí větve

Commity za `11da351` (vše jen `docs/`):

| Commit | Obsah |
|---|---|
| `25e501e` | zadání AG-006 až AG-010 |
| `a1cd8cc` | deník: struktura nabídky |
| `05cdf87` | zadání AG-011 účty rolí |
| `8c02bdb` | plán ochrany kurzů (první verze) |
| poslední | plán ochrany kurzů podle rozhodnutí, deník: přepis kurzu, plán přemostění tříd, tato předávka |

Přenos (push nejde): balíček `investra-revize-claude-app-2026-11-10.bundle` ve složce `TEST` na OneDrive.

```bash
git bundle verify ~/<cesta>/investra-revize-claude-app-2026-11-10.bundle
git fetch ~/<cesta>/investra-revize-claude-app-2026-11-10.bundle revize/claude-app:revize/claude-app
git diff --stat feature/nav-prototyp revize/claude-app
```
Diff musí obsahovat jen soubory v `docs/`. Pak sloučit do pracovní větve podle zvyklosti (do `main` jen na Martinovu výzvu).

## 2. Paměť projektu (zapisuje jen tato relace)

- Do Claude Doc, tabulka Přijatá rozhodnutí, doplnit dva řádky z `docs/rozhodnuti.md` z 2026-11-10:
  „Struktura nabídky Investra“ a „Přepis kurzu“. Relace v aplikaci k Doc přístup neměla.
- Pak přepsat `docs/architektura.md` novým exportem Doc.
- Do `docs/otevrene-body.md` zapsat čekající plány z bodu 5 a otázky z bodu 6.

## 3. Zadání pro Antigravity / Copilot (zelená zóna)

Bloky XML byly ověřeny nanečisto proti `11da351`: každý blok „Bylo“ nalezen právě jednou, schémata Odoo 20
31 + 4 pohledy, 0 chyb, strom nabídky bez sirotků. Pokud se `feature/nav-prototyp` v `~/odoo-dev` mezitím pohnula,
před předáním ověřit, že bloky „Bylo“ stále sedí.

| Pořadí | Zadání | Závisí na | Soubory |
|---|---|---|---|
| 1 | `AG-006-nabidka-podle-prace.md` | – | 10 XML, jen `menuitem` |
| 2 | `AG-007-preceneni-vyber-uctu.md` | – | `fx_views.xml` |
| 3 | `AG-008-seznam-upisu-a-odkupu.md` | – | `nav_views.xml` |
| 4 | `AG-009-seznam-a-formular-cen.md` | – | `instrument_views.xml` |
| 5 | `AG-010-rucne-dolozene-uplaty.md` | sloučené AG-008 | `nav_views.xml` |
| 6 | `AG-011-ucty-roli.md` | sloučené AG-006 | `entity_views.xml` |

Postup podle `CLAUDE.md` (Role agentů, Převzetí). Zadání uvádějí výchozí větev `revize/claude-app`; v `~/odoo-review`
použij větev, do které se tato práce sloučí. Pokyn pro agenta (jedno zadání na jedno spuštění):

```
Přečti .agents/rules/ a zadání docs/ukoly/AG-006-nabidka-podle-prace.md a proveď přesně je.
Měň jen soubory z „Rozsahu souborů“. Když se blok „Bylo“ nenajde přesně, zastav se a napiš to do výsledku.
Spusť ověřovací příkazy ze zadání a doplň sekci „Výsledek“. Necommituj, nepřepínej větve, nepushuj.
```

Při převzetí: se souhlasem Martina aktualizovat dotčené moduly v `investra_test`, testy Odoo, projít obrazovky
v prohlížeči (kritéria přijetí v každém zadání).

## 4. Ověření na běžící instanci (Windows to nešlo, instance neběžela)

- Bod 1 podkladu UX: ukazuje výběr účtu zisku a ztráty v profilu přecenění kód účtu? Pokud ne, zkontrolovat kód účtu
  ve společnosti profilu (kód je v Odoo 20 závislý na společnosti).
- Je zapnutá plánovaná úloha „Investra: stažení kurzů“ v `investra_dev` (SELECT nad `ir_cron`)?
- Kde v Odoo 20 Community jde ručně měnit kurzy měn (cesta v UI pro plán ochrany kurzů).
- Jsou v `res_currency_rate` kurzy odlišné od `investra_rate` (SELECT, výsledek Martinovi)?

## 5. Plány čekající na schválení Martinem (červená zóna, provádí Claude)

| Plán | Stav | Otevřené otázky |
|---|---|---|
| `docs/navrh-ochrana-kurzu.md` | doporučena varianta C; kdo přepisuje rozhodnuto (skupina schvalování ocenění) | měsíční kurzy ČNB; upozornění na ruční kurz v kontrolách ocenění |
| `docs/navrh-premosteni-trid.md` | doporučena varianta A (uložené hodnoty) | dividendy jako pohyb třídy; kapitál v měně zveřejnění; rozpad ostatních položek |

Další body z podkladu UX `zadani-ux-2026-11-10.md` (mimo repozitář, ve složce `TEST`), pro které plán ještě není:

| Bod | Téma | Zóna |
|---|---|---|
| 3 | Přehled fondů jako tabulka s filtry stavů, uložený snímek (O3) | oranžová |
| 5.3 | Výpočetní protokol po krocích ukládaný s verzí | červená |
| 8 | Úpisy a odkupy: zdroj, zaokrouhlení, poplatek ve prospěch fondu nebo třídy, historie změn | oranžová / červená |
| 9 | Klasifikace IFRS 9 na obchodu (krok A22 revize) | červená |
| 10 | Sdílené tržní ceny přes fondy; měna ceny | červená |
| 14 | Termínované vklady: obecný nástroj, podmínky na obchodu, průvodce | červená |
| 15 | Účetní události: fond, částka, měna, zdroj s proklikem | červená |
| 16 | Pravidla úplat proti sešitům (hurdle po tranších, pásma, daň, měnové zajištění tříd) | červená |

Doporučené pořadí: 10 a 9 (na nich stojí další obrazovky), pak přemostění tříd, ochrana kurzů, 15, 8, 14, 16, 5.3, 3.

## 6. Další zelená zadání k přípravě

- `i18n/cs.po`: pole bez českého názvu (např. `units` se ukazuje „Units“) ve všech modulech.
- Prázdné stavy: pole `help` u akcí (Ceny, Úpisy a odkupy, Ocenění, Účetní události, Splátky) s vysvětlením „k čemu
  a co udělat“.
- Otázka pro Martina: „Kurzy měn“ přesunout z Ocenění do Nastavení → Účtování (používá je i účetnictví)?

## 7. Upozornění

- Ukázkové sešity NAV jsou důvěrné; plány používají jen obecné poznatky z podkladu UX, žádná data.
- `zadani-ux-2026-11-10.md` je mimo repozitář (složka `TEST` na Windows); obsah je shrnutý v bodech 3, 5 a 6.
