# ZJ-24 Hlášky a sazby úplat: poznámky 13 až 16

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | body 13, 14, 16: texty, upozornění a nápověda (zadal Martin přímo); bod 15: **červená** (`engine.split_by_versions`) – jen s plánem schváleným Martinem |
| Výchozí větev | `main` |
| Větev úkolu | `ukol/ZJ-24-hlasky-a-sazby` |
| Zadal, dne | Martin, 2026-11-20 (poznámky 13 až 16 z `docs/ukoly/ZJ-20-poznamky-zpracovani.md`) |
| Vlastník | Claude |

## Provedeno: body 13, 14, 16 (2026-11-20)

- **13 Úpis před vznikem fondu.** Ocenění bere pohyby až po datu vzniku fondu (`date > začátek období`), dřívější úpis proto v prvním
  ocenění chybí a kapitál vyšel nulový. Formulář úpisu a odkupu ukáže žlutý pruh `launch_warning`, když je datum pohybu **dřívější než
  datum vzniku fondu nebo shodné s ním** (`movement.py`, `nav_views.xml`). Ocenění při nulovém kapitálu prvního období a existujícím
  nestornovaném pohybu s takovým datem řekne, o které datum jde a že se pohyb nezapočetl (`valuation._zero_capital_error`); bez takového
  pohybu zůstává dosavadní hláška „Předběžný kapitál fondu je nulový.“
- **14 Chybějící sazba.** Hláška ze `_no_rate_error` (`fee_rule.py`) říká název pravidla, fond, den bez sazby a první platnou verzi. Používá ji
  `_version_at` (úplata, výkonnostní odměna) a nová předkontrola v `_engine_rule` (dřív by engine napsal jen „Pro den … není platná sazba“).
  Daňové pravidlo (`tax_rule._version_at`) má dál vlastní kratší hlášku. **Po bodu 15 předkontrola v `_engine_rule` zanikne**, hláška zůstane
  pro výkonnostní odměnu a daň a její text se použije v informativní kontrole.
- **16 Nápověda Výpočet za období.** Pole `fixed_mode` má v `help` příklad (10 000 měsíčně, 30 dní: Poměrně 9 863,01; Za každý započatý měsíc
  10 000 nebo 20 000 podle toho, zda 30 dní leží v jednom, či ve dvou měsících); stejný příklad je v `docs/manual/09-uplaty-a-opravy.md`.
  Čísla jsou ověřená enginem (Act/365).
- Verze `investra_nav` 20.0.0.43.0. Test `investra_nav/tests/test_zj24_messages.py` (varování ve formuláři, hláška ocenění, obecná hláška beze změny,
  hláška o sazbě). Cílené: `TestZj24Messages`, `TestFees`, `TestFeeStartedMonth` bez chyby (21 testů), dříve i `TestMovement`, `TestMovementOnchange`, `TestLaunchDate`.
- **Neověřeno v prohlížeči:** pruh ve formuláři úpisu a texty hlášek. Pracovní `investra` neupgradována.

## Plán bodu 15 (návrh ke schválení Martinem; kód zatím nepsán)

**Rozhodnutí z 2026-11-20:** pravidlo úplaty se před svou první verzí sazby neúčtuje (nula), ocenění ukáže informativní kontrolu místo
chyby; chyba zůstane pro skutečnou mezeru.

**Zjištění.** `split_by_versions` bere verzi platnou k prvnímu dni úseku (`valid_from <= den`). Verze platí do dne před další, mezera mezi
verzemi proto vzniknout nemůže. Jediný stav „bez platné sazby“ je tedy období (nebo jeho část) **před první verzí**; to je ten případ, který se
mění z chyby na nulu. Chybou zůstane pravidlo **bez jakékoli verze** (to platí už dnes i jako `constrains`).

### Změny

1. **`engine.split_by_versions`** (červená): když pro první den úseku není verze a existuje pozdější, vrátí úsek
   `(cursor, min(end, první valid_from − 1 den), None)` místo `ValueError`. Bez jakékoli verze (`versions` prázdné) dál `ValueError`.
2. **`engine._segment_amount`**: úsek s verzí `None` vrací nulu a řádek rozpisu `{"from", "to", "uncovered": true, "amount": "0"}`.
   Minimum a maximum ročně se uplatní jen na úseky s verzí.
3. **`engine.periodic_fee`**: „první úsek“ pro režim Za každý započatý měsíc je **první úsek s verzí**, ne index 0. Bez toho by pravidlo
   s první verzí od 10. 1. a obdobím 31. 12. – 31. 1. dalo za leden 0 místo 10 000 (měsíc by nikdo nezapočítal). Výsledek dostane klíč
   `uncovered_days` (součet dní bez sazby); ostatní klíče beze změny. **Období plně pokrytá verzemi dávají přesně stejný výsledek jako dnes**,
   takže referenční scénáře, snímek 35/39 a zaúčtovaná ocenění se nemění.
4. **`fee_rule._engine_rule`**: předkontrola z bodu 14 se odstraní; zůstane „Pravidlo … nemá žádnou sazbu“ (bez verzí).
5. **Ocenění** (`valuation._apply_fees`): nová kontrola `fee_not_in_force` „Pravidla úplat začínají až po začátku období“ za periodická pravidla
   fondu s první verzí pozdější než první den období. Text: pravidlo, fond, období, které se neúčtuje (od–do), a první verze. Úplata za nepokrytý
   úsek je 0. Pravidlo s první verzí až po datu ocenění dá úplatu 0 s touto kontrolou, doklad se nezaúčtuje (jako dnes u nulové sazby).
6. **Beze změny:** náhled schématu na fondu (`fee_scheme.py`, pravidlo bez sazby k dnešku se dál vypíše poznámkou), výkonnostní odměna a daň
   (`_version_at` s hláškou z bodu 14).

### K potvrzení Martinem

| # | Otázka | Doporučení |
|---|---|---|
| a | „Skutečná mezera“ = pravidlo bez jakékoli verze (jiná mezera neexistuje, viz Zjištění). Souhlasí? | ano |
| b | Úroveň informativní kontroly: **A** stávající stav `warning` (Upozornění; nemění schéma, objeví se v přehledu kontrol na kartě), **B** nový stav `info` (Informace) – změna výběru `status`, kontroly na kartě a dashboardu | **A**; `info` jen na výslovné přání |
| c | Rozšířit „před první verzí nula“ i na **výkonnostní odměnu** a **daň**? Mají vlastní logiku (naběhlá odměna, počáteční hodnota, daň za rok), nula bez chyby by mohla zakrýt zapomenutou verzi | ne, ponechat chybu s hláškou z bodu 14 |

### Testy a ověření

- Engine: období před první verzí = 0; přes hranici verze = jen pokrytá část; režim měsíc s první verzí uprostřed měsíce (31. 12. – 31. 1.,
  verze od 10. 1. → 1 měsíc); minimum a maximum jen na pokrytém úseku; bez verzí `ValueError`; plně pokrytá období beze změny
  (existující `test_fee_started_month.py`, `test_fees.py`).
- Ocenění: pravidlo od 10. 1., ocenění 31. 1. → úplata za 10.–31. 1. a kontrola; pravidlo od 1. 3., ocenění 31. 1. → úplata 0, bez dokladu, kontrola;
  test hlášky z bodu 14 se přesune na výkonnostní odměnu.
- Regrese červené zóny: `TestFees`, `TestFeeCharacterization`, `TestFeeReferenceModel`, `TestFeeSolver`, `TestFeeAverageClass`, `TestScenarios`
  a snímek ocenění 35/39 (`tools/snimek_na_kopii.sh`) beze změny; potom `modul+` a `all`.
- Migrace není potřeba (žádné pole ani sloupec se nemění).

**Schválení:** čeká na Martina (otázky a až c).
