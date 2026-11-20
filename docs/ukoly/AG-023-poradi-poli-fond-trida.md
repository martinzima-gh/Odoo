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

**Původní pořadí při kontrole před změnami; poslední sloupec uvádí výsledek:**

| Formulář | Před úpravou | Výsledek |
|---|---|---|
| Obchod | Směr a datum → nástroj → fond → portfolio → třída | Upraveno na fond → třída portfolia → portfolio → nástroj → směr a datum → kusy → cena. |
| Úpis / odkup | Typ a třída → měna a datum; `fund_id` ve formuláři chyběl | Doplněn existující související fond před třídou; typ a ostatní údaje následují. |
| Splátka | Typ → fond → nástroj → portfolio → datum | Fond přesunut před typ. Model nemá pole třídy. |
| Derivát | Fond → portfolio → smlouva | Beze změny; model ani formulář nemají pole třídy. |
| Dividenda | Nástroj v nadpisu → fond → portfolio → nárok | Beze změny podle výslovného pokynu (formulář se předělává v ZJ-22). |
| Ruční úplata a oprava | Úplata je řádek ocenění; oprava ukazuje pravidlo a třídu, vazba na ocenění je skrytá | Formuláře/řádky nemají vlastní zobrazované pole fondu; nic se nevymýšlelo. |
| Přecenění kurzu FX | Profil → datum → společnost a výsledek | Beze změny; formulář nemá pole fondu. |
| Ocenění | Fond a datum v nadpisu; třídy v záložce Třídy | Beze změny, fond je už první. |
| Kurz měny | Měna, datum a kurz | Beze změny; formulář nemá pole fondu. |
| Cena nástroje | Nástroj → fond → datum a cena | Upraveno na fond → nástroj → datum a cena. |
| Pravidlo úplaty | Fond → název/druh → parametry → třídy | Upraveno na fond → přiřazení tříd → název/druh → parametry. |
| Alokační schéma | Fond → platnost a metoda; třídy v řádcích schématu | Beze změny; třída je již ve výběrových řádcích, nejde o samostatné pole schématu. |

- **Změněné soubory:** `addons/custom/investra_instruments/views/instrument_views.xml`, `addons/custom/investra_nav/views/nav_views.xml`.
- **Ověřeno:** pořadí ve zdrojových XML; ověřeno, že pohyb úpisu/odkupu má související `fund_id` a že obchod již má čtecí `portfolio_class_id`.
- **Neověřeno:** vizuální pořadí na Odoo UI a upgrade modulů.
- **Otevřené otázky a návrhy mimo rozsah:** splátka a derivát nemají přímé pole třídy; ruční úplata/oprava nemají zobrazované vlastní pole fondu. Dividendový formulář zůstává pro ZJ-22.

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
