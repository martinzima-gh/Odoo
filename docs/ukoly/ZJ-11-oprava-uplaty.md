# ZJ-11 Oprava úplaty ruční úplatou

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **červená** (`investra_nav`: účtování úplat, `_apply_manual_fees`, `_book_fee`); jen plán, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Martin, 18. 11. 2026 (návrh Claude, upravený podle jeho připomínek) |
| Řešitel | Claude (kroky 1–2, červená zóna); krok 3 (tlačítko a protokol) může převzít Antigravity / Copilot po plánu |
| Nahrazuje | otevřený bod „Ruční úprava vypočtené úplaty se zdůvodněním“ (`docs/otevrene-body.md`) |

> **Upraveno 2026-11-18 zadáním ZJ-12** (`docs/ukoly/ZJ-12-zaklad-uplat-a-opravy.md`): upřesnění (a) „opravit jde jen časově rozlišenou úplatu“ nahrazuje
> ZJ-12 (opravy všech druhů s platností); rozhodnutí 3 se upřesňuje – oprava = pevná částka „vypočteno bez opravy + oprava“; bod 6 (chatter) nahrazuje
> souhrn oprav v krocích ocenění; krok 3 (protokol a XLS) se provede spolu s krokem 6 ZJ-12. Kroky 1–2 zůstávají hotové a platí do doby, než je ZJ-12 přepíše.

**Cíl:** vypočtenou úplatu lze opravit (zaokrouhlení podle faktury obhospodařovatele, dohoda s depozitářem) se zdůvodněním, stopou a viditelností
pro depozitáře, aniž vznikne nový model ani druhý způsob účtování. Oprava je **záporná nebo kladná ruční úplata** (ZJ-03) navázaná na pravidlo úplaty.

## Rozhodnutí z 18. 11. 2026

1. **Zámek `base_mode`:** zámek patří výsledku ocenění (schválené, zaúčtované a zveřejněné ocenění se samo nepřepočítá), ne definici pravidla.
   Na pravidle se zámek nezavádí; změna `base_mode` se projeví až dalším výpočtem (test `TestBaseModeRetroactive` platí beze změny).
2. **Oprava = ruční úplata**, ne samostatná „úprava“ řádku úplaty. Důvod: ruční úplata už umí zápornou částku, třídu nebo celý fond, povinnou
   poznámku, přílohu, cizí měnu, zámek po odeslání ke schválení a schvaluje se s oceněním; přepočet ji nesmaže (smaže ji uživatel v Návrhu nebo Spočteno).
3. **Úplata „po“ (`base_mode = after`):** ruční úplaty se účtují před dopočtem úplat „po“, takže jejich základ s opravou počítá správně; NAV odpovídá
   čistému výpočtu z opravené částky. Výkonnostní odměna a daň se počítají po nich.
4. **Průměrný FK:** další ocenění odečítá zaúčtované částky jen z řádků s pravidlem; ruční úplata pravidlo nemá, takže se nedorovnává a rozdíl
   zůstává trvale (varianta „oprava platí trvale“).
5. **Kdo smí opravovat:** kdo smí ocenění připravit (stejně jako ruční úplatu). Druhá osoba přes schvalovací matici, výchozí bez druhé osoby.

## Návrh

1. **Pole „Opravuje úplatu“** na `investra.valuation.external` (volitelné, odkaz na `investra.fee.rule`).
2. **Účtování přes `_book_fee`**, když je pole vyplněné: nákladová role pravidla a rozdělení příjemcům z tříd (`recipient_share`) jako u původní úplaty;
   nákladový účet se pak nezadává. Bez pole se ruční úplata chová jako dnes (účet, expense_other, závazek).
3. **Kontrola** `_check_fund`: u opravy účet odpadá, třída musí být mezi třídami pravidla (nebo prázdná = celý fond jako u pravidla), poznámka zůstává povinná.
4. **Tlačítko „Opravit“** na řádku úplaty v ocenění: založí ruční úplatu s polem Opravuje úplatu, třídou plátce a výzvou k doplnění částky
   a zdůvodnění; v rozpisu úplat a v protokolu se oprava ukáže vedle původní úplaty.
5. **Protokol a XLS pro depozitáře:** sloupce Vypočteno / Oprava / Zdůvodnění (zjistit, kde se protokol generuje; oranžová zóna).
6. **Chatter:** zápis opravy do chatteru ocenění, pokud ocenění dědí `mail.thread` (ověřit).

## Rizika a ověření

- `_book_fee` a `engine.split_amount` se zápornou částkou dnes nejsou zkoušené; ověřit zaokrouhlení (součet nákladu a přesunu = oprava).
- Změna schématu: jeden nový nepovinný sloupec; záloha pracovní DB a zkouška na kopii před povýšením.
- Referenční scénáře bez opravy se nesmí změnit.

## Testy

- záporná oprava u `before`, `after` a průměrného FK (rozdíl trvale zůstane, příští ocenění ho nedorovná),
- oprava úplaty s příjemci: náklad + přesun mezi třídami = oprava; bez příjemců stejné doklady jako dnes,
- zamčení po odeslání ke schválení; přepočet řádek zachová,
- chybějící poznámka a třída mimo pravidlo se zamítnou,
- regrese: všechny referenční scénáře beze změny; `investra_nav` → `modul+`, `all` až před `main`.

## Postup

1. Pole, účtování, kontrola, testy (červená, Claude) → schválení.
2. Tlačítko a zobrazení (oranžová).
3. Protokol a XLS pro depozitáře, manuál (postup „oprava úplaty“ v `docs/manual/`), deník rozhodnutí.

## Stav

**Krok 1 hotový 2026-11-18 (Claude). Upřesnění (b) a (c) schválil Martin 2026-11-18; upřesnění (a) nahrazuje ZJ-12.** Záloha před změnou schématu: `zalohy/investra-2026-11-18-pred-ZJ11.dump`.
Pracovní databáze `investra` zatím **není povýšená** (modul 20.0.0.36.0, nový sloupec `corrects_rule_id`); povýšení na pokyn.

- Pole `corrects_rule_id` („Opravuje úplatu“) na `investra.valuation.external`; v seznamu ručních úplat sloupec a účet povinný jen bez opravy
  (nutné minimum, aby šla oprava zadat; tlačítko „Opravit“ je krok 2).
- `_apply_manual_fees`: s polem účtuje přes `_book_fee` (role pravidla, příjemci z tříd), klíč dokladu `fee:<pravidlo>:<třída>:manual:<id>`,
  název „Oprava úplaty …“; řádek rozpisu bez pravidla, takže průměrný FK opravu nedorovná.
- `_check_correction`: pravidlo fondu ocenění; třída podle pravidla (pravidlo tříd → jedna z nich, pravidlo fondu → prázdná); poznámka
  a nenulová částka jako dosud.
- **Upřesnění navíc oproti plánu (ke schválení):** (a) opravit jde jen časově rozlišenou úplatu, ne výkonnostní odměnu ani daň
  (počítají se jako doplatek do požadovaného stavu, oprava by se dalším oceněním dorovnala); (b) oprava jen v měně fondu (`_book_fee`
  nenese cizí měnu); (c) vyplněný nákladový účet se u opravy odmítne, ne tiše ignoruje.
- Testy `tests/test_fee_correction.py` (6): before, after, průměrný FK, příjemci (náklad + přesun = oprava, vnitřní zúčtování nulové),
  přepočet a zámek, zamítnutí. `investra_nav` 17/17, `investra_nav+` 494/494 OK.

**Krok 2 hotový 2026-11-18 (Claude).** Na řádku rozpisu úplaty (záložka Úplaty) tlačítko „Opravit“ (`investra.valuation.fee.action_correct`,
vidět jen u řádku s pravidlem `kind == 'periodic'` v ocenění Návrh/Spočteno; jinak `UserError`). Otevře dialog formuláře ruční úplaty
(`view_valuation_external_correction_form`) s kontextem ocenění, opravované úplaty, třídy řádku a měny fondu; uloží se až s částkou a poznámkou.
Řazení rozpisu: nová uložená pole `group_key` a `is_correction`, `_order = valuation_id, group_key, is_correction, id` – oprava hned pod původní úplatou,
ruční úplaty bez opravy na konci. Účtování beze změny. Testy +3 (kontext a uložení, řazení, zákaz mimo draft/computed);
`investra_nav` 423/423, `investra_nav+` 497/497 OK. Nová uložená pole se doplní při povýšení na 20.0.0.36.0 (verzi jsem nezvyšoval,
`investra` ještě není povýšená). Zbývá krok 3 (protokol, XLS, manuál, deník).

**Krok 3 hotový 2026-11-18 (Claude, spolu se ZJ-12 krokem 6).** Protokol pro depozitáře = list Úplaty XLS balíčku (jiný protokol v modulu není): u ocenění
s opravou sloupce Vypočteno, Oprava, Výsledek, Zdůvodnění, Převzato z / Ukončuje opravu, hodnoty ze snímku detailu (commit ddcb48d, `test_package_fees`).
Manuál kap. 9 část 3 (oprava úplaty) a 4 (zrušení úplaty), commit 4f7dddd. Deník: rozhodnutí 2026-11-18 „ZJ-12 krok 5 – odchylky rozhraní a omezení náhledu“.
Pracovní `investra` povýšená na 20.0.0.37.0 (ZJ-11 i ZJ-12), stav v ZJ-12 „Povýšení pracovní databáze a zkouška rozhraní“. Úkol ZJ-11 je tím hotový; sloučení
do `main` spolu se ZJ-12 na Martinův pokyn.

## Převzetí

Kroky 1–3 udělal Claude přímo ve větvi `ukol/ZJ-zjednoduseni`; práce jiného agenta k převzetí není. Ověření: `investra_nav` 494/494 (2026-11-18), povýšení `investra` s kontrolou ocenění 35 a 39 beze změny.
