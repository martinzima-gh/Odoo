# ZJ-11 Oprava úplaty ruční úplatou

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **červená** (`investra_nav`: účtování úplat, `_apply_manual_fees`, `_book_fee`); jen plán, kód až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Martin, 18. 11. 2026 (návrh Claude, upravený podle jeho připomínek) |
| Řešitel | Claude (kroky 1–2, červená zóna); krok 3 (tlačítko a protokol) může převzít Antigravity / Copilot po plánu |
| Nahrazuje | otevřený bod „Ruční úprava vypočtené úplaty se zdůvodněním“ (`docs/otevrene-body.md`) |

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

## Převzetí

(doplní se po provedení)
