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
  Pruh s tlačítkem Spočítat, ne automatický přepočet (uživatel 2026-11-13). Běžný postup: Spočítat → podle
  přecenění doplnit ruční úplaty → Spočítat znovu; každý výpočet zahodí návrhy předchozího a počítá od začátku.
- Po odeslání ke schválení řádky nejde měnit (beze změny). Kontrola fondu pravidla a tříd (2026-11-13) zůstává.

## Část C: jedno univerzální přecenění (uživatel 2026-11-13, **ke schválení**)

Požadavek uživatele: FX přecenění je jedno a univerzální pro Services i fondy. Etapa 1 sdílí jen výběr zůstatků,
zaúčtování je dvojí (událost ocenění a doklad běhu) – to se nahradí.

1. **Jediné přecenění = běh přecenění** (`investra.fx.run`): doúčtování do potřebného zůstatku po účtu, měně a partnerovi
   (u peněžních účtů bez partnera). Zaúčtované přecenění se nikdy nepřepočítává ani nestornuje, další přecenění k němu
   doúčtuje jen rozdíl (doplňkové přecenění podle politiky).
2. **Fond:** Spočítat v ocenění založí nebo přepočítá běh k datu ocenění nad profily knihy fondu (krok mezi ručními
   úplatami bez pravidla a úplatami podle pravidel). Běh je svázaný s oceněním: návrh dokladu je v náhledu a v Doklady
   ocenění, schvaluje se čtyřma očima s oceněním, zaúčtuje se s ním a při vrácení ocenění se stornuje. Do výpočtu jdou
   i nezaúčtované doklady ocenění (závazek z ruční úplaty). Nové Spočítat zahodí návrh předchozího výpočtu a spočítá znovu.
3. **Services:** beze změny postupu – účetní v Přecenění cizích měn vybere profil a datum, Spočítat, Vytvořit doklad,
   zaúčtuje po kontrole (měsíčně a na žádost účetního).
4. **Ruční běh nad profilem fondu** je tentýž běh; existuje-li k datu nezaúčtovaný, ocenění ho převezme. Pojistka:
   na jeden profil smí být jen jeden nezaúčtovaný běh (návrh), ostatní řeší doúčtování (po zaúčtování vyjde nula).
5. **Sjednotit:** (a) kurz a zaokrouhlení – jedno pravidlo pro běh i ocenění (dnes běh float a zdroj profilu, ocenění
   Decimal a kurz fondu; rozdíl v haléřích), ověřit na referenčních scénářích; (b) zaúčtování běhu přes účetní událost
   (`investra.accounting.event`: role, otisk, storno, náhled) místo přímého dokladu Odoo.
6. Vlastní krok přecenění v ocenění (`_fx_revaluation_lines`, etapa 1) se odstraní; profily fondů a `_foreign_balances`
   zůstávají. Červená zóna.

## Etapy

1. Část B (přecenění podle profilu) – hotovo, viz Provedení.
2. Část C (jedno univerzální přecenění) – po schválení.
3. Ruční úplaty: nová pole, migrace, výpočet a pořadí, výzva k přepočtu, náhled zaúčtování.

## Migrace

Stávající řádky: datum = datum ocenění, popis = důvod, měna = měna fondu, druh nákladu a rozdělení z pravidla.

## Provedení

- **Etapa 1 (2026-11-13, commit 31a5cf4):** `investra.fx.profile._foreign_balances` (společný výběr), ocenění přeceňuje
  banky a účty profilů knihy bez účtů nevypořádaných obchodů, banky bez dělení podle partnera, profil fondu
  (`fund_id`) při založení a migrací 20.0.0.28.0. Čistá DB: 343 testů nav + fx a 23 dashboard + cnb bez chyby.
  `investra_test` povýšena (záloha `zalohy/investra_test-2026-11-13-pred-profilem-preceneni.dump`): 6 nových profilů,
  počet a součet řádků dokladů beze změny; 3 známé chyby matice (ruční řádky matice v `investra_test`).
  Ruční profil „TEST“ (119100, 119200 bez role) zůstává a ocenění ho používá.
- **Otevřené:** zákaz samostatného běhu nad profilem fondu uživatel odmítl (2026-11-13) – nahrazuje ho část C.
  Část C čeká na schválení, ruční úplaty na pokyn uživatele.
