# AG-023 Pořadí polí ve formulářích: fond, třída, potom ostatní

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `views/*.xml`, nová `tests`, `docs/manual`) |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` |
| Větev úkolu | `ag/AG-023-poradi-poli` |
| Zadal, dne | Martin (poznámky) / Claude, 2026-11-20 |
| Navazuje na | `docs/ukoly/ZJ-20-poznamky-zpracovani.md`, bod 2 |

**Cíl:** Při zadávání jakéhokoli záznamu je nejdůležitější **fond**, potom **třída**, potom ostatní pole. To musí být vidět ve všech
zadávacích formulářích: fond první, pod ním třída (kde se vybírá), potom zbytek v logickém pořadí. Uživatel tak nejdřív určí, čí
záznam je, a teprve potom vyplňuje podrobnosti.

**Postup:**
1. Projdi formuláře zadávání: obchod, úpis a odkup, splátka, derivát, dividenda, ruční úplata a oprava, přecenění kurzu,
   ocenění, kurz a cena (kde je fond), pravidlo úplaty, alokační schéma. Soupis (formulář, soubor, dnešní pořadí, navrhované pořadí)
   napiš do Výsledku jako tabulku, nejdřív před úpravou.
2. Fond je ve formuláři první a pod hlavičkou (stavy, tlačítka). Třída hned pod ním. Portfolio, nástroj a další až potom.
3. Žádná změna logiky: jen pořadí, seskupení a `invisible`/`readonly` podle už existujících polí. Pole `invisible` nebo `readonly`
   neměň. Pokud formulář nemá pole fond (např. sdílená cena), nic nevymýšlej a zapiš ho do výsledku.
4. Obchod: pořadí fond → třída portfolia (jen čtení, už existuje) → portfolio → nástroj → směr, kusy, cena.

**Rozsah souborů:** `addons/custom/*/views/*.xml` zadávacích formulářů; `docs/manual/*.md` jen popisky pořadí.

**Mimo rozsah:** Python, nová pole, oprávnění, data, seznamy a vyhledávání (to je AG-024). Dividendy se v ZJ-22 přestavují – formulář
dividendy zatím jen zapiš do soupisu, neupravuj.

**Kritéria přijetí:** soupis ve Výsledku; každý zadávací formulář má fond první; moduly se povýší bez chyby
(`tools/run_tests.sh` spouští jen Claude); žádná změna Pythonu (`git diff --stat`).

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
