# Návrh: zjednodušené ručně zadané úplaty

Stav: **návrh ke schválení** (červená zóna – výpočet ocenění a účtování); pořadí ve výpočtu a varianta A přecenění
odsouhlaseny 2026-11-13. Rozhodnutí uživatele 2026-11-13, deník „Ručně zadané úplaty – zjednodušení“.

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
2. K datu ocenění: závazek v cizí měně přecení společné přecenění ocenění (část B), ruční úplata žádné vlastní nemá.

## Část B: ocenění přeceňuje podle profilu (varianta A, uživatel 2026-11-13)

Dnes ocenění přeceňuje jen banky vlastním výpočtem (`_compute_bank_fx`); modul `investra_fx_revaluation` (profil účtů,
doúčtování do zůstatku po účtu, měně a partnerovi) ocenění nepoužívá. Cíl: jedna logika pro Services i fondy.

1. Výpočet rozdílů z `investra.fx.run.action_compute` se vyčlení do funkce profilu (účty, datum, kurz, doména řádků);
   běh přecenění (Services) ji volá beze změny výsledku.
2. Kniha fondu má profil přecenění; nová kniha ho dostane s účty rolí `bank` (včetně dalších účtů role) a `fee_payable`,
   protiúčty `gain_fx` / `loss_fx`. Další účty (pohledávky, ostatní závazky) přidá uživatel do profilu.
3. Ocenění volá funkci s kurzem fondu (`_fx`) a s řádky včetně vlastních nezaúčtovaných dokladů (`_line_domain`);
   výsledek zaúčtuje jako událost ocenění (`fx_revaluation`), schvaluje se s oceněním čtyřma očima.
   Řádky bank v listu portfolio zůstávají.
4. Pořadí ve výpočtu: portfolio a nevypořádané obchody → ruční úplaty bez pravidla → **přecenění** → úplaty podle
   pravidel (ruční úplaty s pravidlem v jeho pořadí; jejich závazek v měně přecení až další ocenění).
5. Kompatibilita: u bank musí vyjít stejný doklad jako dnes (hlavní účet bez `account_id` v `extra`, aby otisk
   dřívějších ocenění zůstal). Ověření na referenčních scénářích `tools/nav_reference`: stejné NAV a doklady.
   Seskupení i podle partnera u bank nic nemění, bankovní řádky partnera nenesou – ověřit na datech.

## Chování

- Pravidlo „Mimo Odoo“ zůstává jako připomínka: chybí-li k němu řádek, Kontroly ukážou varování, výpočet se nezastaví.
- Přidání, změna nebo smazání řádku ve stavu Spočteno vrátí ocenění do Návrhu a formulář vyzve ke spuštění
  Spočítat (ruční úplata mění základ dalších úplat); Odeslat ke schválení jde až po novém výpočtu.
- Po odeslání ke schválení řádky nejde měnit (beze změny). Kontrola fondu pravidla a tříd (2026-11-13) zůstává.

## Etapy

1. Část B (přecenění podle profilu) – bez změny výsledku u dnešních dat.
2. Ruční úplaty: nová pole, migrace, výpočet a pořadí, výzva k přepočtu, náhled zaúčtování.

## Migrace

Stávající řádky: datum = datum ocenění, popis = důvod, měna = měna fondu, druh nákladu a rozdělení z pravidla.

## Provedení

- **Etapa 1 (2026-11-13, commit 31a5cf4):** `investra.fx.profile._foreign_balances` (společný výběr), ocenění přeceňuje
  banky a účty profilů knihy bez účtů nevypořádaných obchodů, banky bez dělení podle partnera, profil fondu
  (`fund_id`) při založení a migrací 20.0.0.28.0. Čistá DB: 343 testů nav + fx a 23 dashboard + cnb bez chyby.
  `investra_test` povýšena (záloha `zalohy/investra_test-2026-11-13-pred-profilem-preceneni.dump`): 6 nových profilů,
  počet a součet řádků dokladů beze změny; 3 známé chyby matice (ruční řádky matice v `investra_test`).
  Ruční profil „TEST“ (119100, 119200 bez role) zůstává a ocenění ho používá.
- **Otevřené:** zakázat samostatný běh přecenění nad profilem fondu (dvojí přecenění)? Etapa 2 čeká na pokyn uživatele.
