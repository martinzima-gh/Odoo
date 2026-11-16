# DE-04 FX derivát v ocenění: reálná hodnota, přepočet podrozvahy, kontroly

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (ocenění, NAV) – plán schvaluje Martin v promptu |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Opus |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Reálná hodnota, Účtování, Příklad, Kontroly ocenění, Testy), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** ocenění fondu spočte reálnou hodnotu otevřených smluv variantou B (nebo vezme ruční hodnotu), zaúčtuje
změnu a přepočte podrozvahu; výsledek je vidět v ocenění a ve FK.

**Schválený plán** (návrh Clauda; plán schválil Martin v promptu relace 15. 11. 2026):

1. **Výpočet** jako čistá funkce bez ORM (vzor výpočetního jádra ocenění), Decimal, zaokrouhlení na haléře až na
   konci: `RH(t) = V(t) − B0 × zbývající dny / dny celkem`. Vstupy (kurzy, B0, dny) se uloží k řádku ocenění.
   Kurzy ze zdroje kurzů ocenění (`_rate_source`, `investra.rate`).
2. **Ruční hodnota** k datu ocenění má přednost; přepočet do funkční měny kurzem ocenění; ocenění uloží spočtenou
   i ruční hodnotu a rozdíl. Tolerance rozdílu jako parametr fondu nebo společnosti (výchozí hodnotu navrhnout).
3. **Zapojení do ocenění** rozšířením `investra.valuation` v modulu `investra_derivative` (výpočet v `investra_nav`
   měnit jen o nezbytné místo napojení, popsat ve Výsledku): smlouvy fondu se stavem Sjednáno a otevřenou nohou
   k datu ocenění; řádek portfolia za smlouvu (hodnota může být záporná); návrh dokladu „Přecenění derivátů“
   se změnou proti zaúčtované RH smlouvy (kladná `derivative`, záporná `derivative_liability`, výsledek
   `gain_derivative` / `loss_derivative`); návrh dokladu „Přepočet podrozvahy“.
4. Opakovaný výpočet návrhy nahradí (`_clear`), vrácení a zrušení návrhu ocenění je odstraní, storno ocenění stornuje.
5. **Kontroly** podle návrhu (chyby a upozornění) do kontrol ocenění.
6. **Testy:** tabulka příkladu na haléř přes dvě ocenění a vypořádání; ostatní body oddílu Testy; stávající testy
   ocenění beze změny výsledků (fond bez derivátů se nesmí změnit ani o haléř).

**Rozsah souborů:** `investra_derivative/`, nezbytné místo napojení v `investra_nav/models/valuation.py` a pohled
ocenění, verze modulů, `docs/rozhodnuti.md`, tento soubor.

**Mimo rozsah:** přiřazení výsledku třídě, diskontování a sazby měn, výkazy ČNB, ukázková data, nasazení do `investra`.

**Kritéria přijetí:** testy `all` bez selhání; příklad sedí na haléř; FK = aktiva − závazky po každém kroku;
u fondu bez derivátů shodné výsledky ocenění jako před změnou (porovnání ve Výsledku).

## Výsledek

Provedl Claude Code (hlavní relace) 16. 11. 2026, větev `etapa/derivaty`.

- **Změněné soubory:** jen `addons/custom/investra_derivative/`: `models/valuation.py` (rozšíření ocenění, řádek
  `investra.valuation.derivative`, tolerance na fondu, zámek použité ruční hodnoty), `views/valuation_views.xml`
  (záložka FX deriváty v ocenění, tolerance ve formuláři fondu), práva, `tests/test_valuation.py`, verze 20.0.0.3.0;
  `docs/rozhodnuti.md`, tento soubor. Výpočet `calc.py` vznikl už v DE-03 (používá ho i vypořádání).
- **Napojení na ocenění:** v `investra_nav` se **nezměnil žádný řádek**. Modul dědí `_compute_unsettled` (za ním
  přecení deriváty), `_clear`, `_position_balance` (přidá účty RH derivátů, aby kontrola „Pozice se rovnají hlavní
  knize“ zahrnula i zápornou RH) a `_run_checks`. Doklady „Přecenění derivátů“ a „Přepočet podrozvahy“ vznikají přes
  `_add_event`, takže je nahrazuje opakovaný výpočet a ruší nebo stornuje stávající postup ocenění.
- **Ověřeno (příkaz a výsledek):** `tools/run_tests.sh investra_derivative` → 0 failed, 0 error(s) of 44 tests;
  `tools/run_tests.sh all` → 0 failed, 0 error(s) of 733 tests (dočasné `investra_ci_*`, smazány). Příklad návrhu na haléř přes dvě ocenění a vypořádání (rok 2025):
  31. 10. MD 313000 / D 719100 166 304,35 a podrozvaha MD 954100 / D 992000 200 000; 30. 11. D 313000 166 304,35,
  D 313100 166 304,35, MD 619100 332 608,70 a podrozvaha D 954100 / MD 992000 300 000; 31. 12. MD 619100 / D 313100
  133 695,65, banka +24 900 000 a −25 200 000, MD 313100 300 000, podrozvaha odúčtována; součet změn −300 000,00.
  Po každém kroku FK ocenění = aktiva − závazky z hlavní knihy a kontroly `positions_ledger` a `classes_sum` v pořádku.
  Dále: RH = 0 v den sjednání, opakovaný výpočet nic nezdvojí, zrušení návrhu odstraní doklady, ruční hodnota má
  přednost jen pro své datum (i v EUR), kontroly, swap po vypořádání blízké nohy, fond v EUR.
- **Fond bez derivátů:** stávající testy ocenění (`investra_nav`, referenční scénáře s očekávanými hodnotami) prošly
  beze změny očekávaných hodnot s nainstalovaným modulem; test `test_fund_without_derivatives_is_untouched` ověřuje,
  že takový fond nemá žádný řádek, doklad ani kontrolu derivátů a FK je roven úpisu.
- **Tolerance (bod 2):** parametr fondu „Tolerance ruční hodnoty derivátu (% nominálu)“, výchozí **0,10 %** nominálu
  otevřených noh ve funkční měně (návrh Clauda; u příkladu 24 900 Kč). Nad tolerancí je upozornění, ne stop.
- **Kontroly:** stop – nevypořádaná noha s datem vypořádání do dne ocenění, chybějící kurz, ruční hodnota bez
  přílohy i důvodu; upozornění – rozdíl ruční a spočtené hodnoty nad tolerancí, smlouva v návrhu s datem sjednání
  do dne ocenění. Kontroly se přidávají jen fondu, který má aspoň jednu smlouvu.
- **Doplněno nad zadání:** ocenění dorovná na nulu zůstatky RH a podrozvahy vypořádaných a stornovaných smluv
  (např. po stornu smlouvy přeceněné dřívějším oceněním); ruční hodnotu použitou oceněním od stavu Ke schválení
  nejde změnit ani smazat; FX spot se oceňuje stejným vzorcem na svých účtech (358, 616 / 716).
- **Neověřeno:** vzhled záložky v prohlížeči; storno zaúčtovaného ocenění s deriváty a oprava zveřejněného ocenění
  nemají vlastní test (jdou stávajícím postupem přes doklady ocenění); dorovnání zůstatků stornované smlouvy dalším
  oceněním nemá vlastní test; chování při novém ocenění k datu před vypořádáním, které už proběhlo, jen úvahou.
- **Otevřené otázky a návrhy mimo rozsah:** tolerance 0,10 % je návrh ke schválení; řádek portfolia za smlouvu má
  měnu fondu a kusy 1 (měnový pár je v názvu); výkazy ČNB a ukázková data jsou DE-05.

## Převzetí
