# Návrh: zjednodušené ručně zadané úplaty

Stav: **návrh ke schválení** (červená zóna – výpočet ocenění a účtování). Rozhodnutí uživatele 2026-11-13,
deník „Ručně zadané úplaty – zjednodušení“.

## Dnes

- Řádek ručně doložené úplaty (`investra.valuation.external`) musí mít pravidlo druhu „Mimo Odoo“; zaúčtování
  (nákladová role, podíl pro jiné třídy) se bere z pravidla. Důvod a příloha jsou povinné.
- Pravidlo „Mimo Odoo“ bez řádku zastaví výpočet ocenění.
- Částka je jen v měně fondu, doklad nese datum ocenění. Změna řádku po výpočtu stav ocenění nemění.

## Cíl

Jeden řádek = jedna úplata se vším, co je potřeba k zaúčtování; pod tabulkou náhled zaúčtování ze stejné funkce,
která účtuje (vzor `investra.posting.preview`).

| Pole | Povinné | Poznámka |
|---|---|---|
| Datum | ano | datum účetního případu; v období ocenění (po datu předchozího ocenění, nejpozději k datu ocenění) |
| Popis | ano | text dokladu (nahrazuje „Důvod a postup“) |
| Částka, Měna | ano | výchozí měna fondu |
| Druh nákladu | ano | nákladová role (`EXPENSE_ROLES`) |
| Třída | ne | prázdná = společný náklad fondu, dělí se poměrem |
| Podíl pro jiné třídy, Přijímající třídy | ne | jako u pravidla: podíl jde přesunem přes vnitřní zúčtování, mezi více tříd poměrem kapitálu |
| Pravidlo úplaty | ne | výběr doplní druh nákladu, třídu a rozdělení |
| Příloha | ne | bez upozornění, když chybí |

## Zaúčtování

1. K datu případu: MD náklad (role druhu) / D závazek z úplat (`fee_payable`), v cizí měně s částkou v měně
   a kurzem ČNB k datu případu. Podíl pro jiné třídy přesunem mezi třídami (`_transfer_lines`), FK fondu se nemění.
2. K datu ocenění: přecenění závazku v cizí měně na kurz k datu ocenění, rozdíl `gain_fx` / `loss_fx`.
   **Nové:** dnes se přeceňují jen banky (`_compute_bank_fx`); přecenění otevřených závazků z úplat v měně se doplní
   obecně (i v dalších oceněních až do úhrady). Kurzový rozdíl při úhradě řeší párování výpisu (Enterprise, otevřený bod).

## Chování

- Pravidlo „Mimo Odoo“ zůstává jako připomínka: chybí-li k němu řádek, Kontroly ukážou varování, výpočet se nezastaví.
- Přidání, změna nebo smazání řádku ve stavu Spočteno vrátí ocenění do Návrhu a formulář vyzve ke spuštění
  Spočítat (ruční úplata mění základ dalších úplat); Odeslat ke schválení jde až po novém výpočtu.
- Po odeslání ke schválení řádky nejde měnit (beze změny). Kontrola fondu pravidla a tříd (2026-11-13) zůstává.

## K rozhodnutí

- **Pořadí ve výpočtu:** řádek bez pravidla počítat před úplatami podle pravidel (sníží základ procentních úplat),
  řádek s pravidlem v pořadí pravidla. Doporučení: ano.

## Migrace

Stávající řádky: datum = datum ocenění, popis = důvod, měna = měna fondu, druh nákladu a rozdělení z pravidla.
