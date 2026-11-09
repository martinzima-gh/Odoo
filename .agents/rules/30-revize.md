---
trigger: model_decision
description: Použij při code review, kontrole změn, diagnostice chyby nebo když uživatel žádá druhý názor na práci Clauda nebo Copilota.
---

# Nezávislá revize a diagnostika

- Revize a diagnostika jen čtou. Výsledek napiš do chatu; soubory neměň, pokud o změnu nejde v zadání úkolu.
- Nejdřív zjisti, co se změnilo a proč (`git log`, `git diff` mezi commity), pak nezávisle ověř tvrzení podle kódu,
  testů a dokumentace v `docs/`.
- Nepředpokládej, že práce Clauda nebo Copilota je správná. Nesouhlas zdůvodni, souhlas řekni výslovně. Nevymýšlej nálezy.
- Priority:
  - architektura Odoo 20 (ORM, dědičnost, `ir.access` místo record rules, views, manifesty, migrace),
  - účetní a finanční logika (MD/D, vyrovnanost, měny a funkční měna, kurz a jeho datum, FX, NAV, třídy, alokace,
    zaokrouhlení, reverzace, auditní stopa),
  - integrita dat (idempotence, souběh, mazání, přesnost),
  - bezpečnost (`sudo()`, oprávnění podle společnosti, nedůvěryhodné vstupy, tajemství),
  - testy a regrese (hraniční případy, více měn, chybějící kurz, multi-company).
- Funkční kód ani zelený test nedokazuje správnost účetní logiky; chybějící účetní pravidlo označ jako otevřenou otázku.

## Formát nálezů

- Řaď podle závažnosti: **CRITICAL**, **HIGH**, **MEDIUM**, **LOW**.
- Každý nález označ jako **OVĚŘENÁ CHYBA**, **PRAVDĚPODOBNÝ PROBLÉM**, **POTENCIÁLNÍ RIZIKO** nebo **DOPORUČENÍ**
  a uveď soubor a řádek nebo model, problém, dopad a návrh opravy. Odděl ověřená fakta od hypotéz.
- Bez významných problémů napiš: **„Žádné zásadní nálezy.“**
