# OC-01 Ocenění: zákaz data před existujícím oceněním a zrušení návrhu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (postup ocenění, NAV) – plán níže schvaluje Martin v promptu |
| Výchozí větev | `feature/instrument-master` po sloučení ST-03 (po ST-01 `main`) |
| Větev úkolu | `ukol/OC-01` |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-14 „nové ocenění až po zveřejnění předchozího“ (varianta A); hlášení Martina 15. 11. 2026 |

**Co se stalo (ověřeno čtením databáze `investra`):** fond C má zveřejněná ocenění do 31. 10. 2026 a uživatel založil
a spočetl ocenění k 1. 9. 2026 (id 39, stav Spočteno, verze 1). Výpočet k němu vytvořil 3 návrhy dokladů (přecenění
portfolia a dvě úplaty, deník MISC, nezaúčtované). Nic zaúčtovaného nevzniklo.

**Proč to prošlo:** `_check_previous_published` v `investra_nav/models/valuation.py` hlídá jen to, že **dřívější**
ocenění je zveřejněné (31. 8. je), pozdější ocenění nekontroluje.

**Proč to nejde odstranit:** role zpracovatele má k `investra.valuation` práva `cru` (bez mazání) a `unlink` modelu
návrhy dokladů neodstraní (`_discard_events` volá jen přepočet a vrácení). Vrácení (`action_return`) je až od stavu
Ke schválení.

**Cíl:**

1. Nové ocenění nejde založit ani přesunout na datum, po kterém už fond má jiné platné ocenění.
2. Návrh ocenění (stav Návrh nebo Spočteno) jde čistě zrušit tlačítkem, včetně návrhů dokladů.

**Schválený plán** (návrh Clauda; schválení Martina a datum doplní provádějící relace podle promptu):

- **Pravidlo data:** rozšířit kontrolu při založení a při změně data nebo fondu (verze 1): existuje-li u fondu ocenění
  s pozdějším datem ve stavu jiném než Vráceno a Stornováno, vyhodit chybu „Fond už má ocenění k pozdějšímu datu
  %(date)s. Nové ocenění lze založit jen po posledním ocenění.“ Nové verze k témuž datu (po vrácení nebo stornu) vznikají
  dál beze změny – opravu staršího ocenění řeší storno, ne nové ocenění. Stávající záznamy se zpětně nekontrolují.
- **Zrušení návrhu:** akce `action_cancel_draft` s tlačítkem „Zrušit návrh“ ve formuláři, jen stavy Návrh a Spočteno,
  role zpracovatele (`PREPARER`), s potvrzením. Odstraní návrhy dokladů (`_discard_events` jako při přepočtu), pak
  záznam ocenění smaže a zapíše do historie fondu, kdo, kdy a které ocenění zrušil. Nový stav „Zrušeno“ se nezavádí
  (zasahoval by do pořadí verzí a všech filtrů stavů); odchylku od tohoto bodu jen navrhnout, neprovádět.
- **Mazání:** `unlink` nejdřív odstraní návrhy dokladů, aby po smazání nezůstaly osiřelé; právo mazat se rolím
  nepřidává (maže jen akce po kontrole role). Zaúčtovaná ocenění dál mazat nejde.
- **Účetní dopad:** žádný – ruší se jen nezaúčtované návrhy. Náhled zaúčtování se netýká.

**Postup:** ověřit v kódu, že návrhy dokladů ocenění jdou vždy přes `event_ids` (jinak se zastavit a napsat); testy;
verze `investra_nav` 20.0.0.29.1; `tools/run_tests.sh investra_nav` a pak `all` na dočasné databázi.

**Testy (nové):** založení před existujícím zveřejněným oceněním selže; před rozpracovaným pozdějším selže; pozdější
jen Vrácené nebo Stornované neblokuje; změna data návrhu dozadu selže; první ocenění fondu a běžné navazující ocenění
projdou; zrušení Spočteného ocenění smaže záznam i návrhy dokladů a nezmění žádný zaúčtovaný doklad; zrušení ve stavu
Ke schválení a dál selže; uživatel bez role zpracovatele nezruší.

**Rozsah souborů:** `investra_nav/models/valuation.py`, pohled formuláře ocenění, `investra_nav/tests/`, `__manifest__.py`
(verze), `docs/rozhodnuti.md`, tento soubor, předávka. Ukázková data (`seed.py`) jen pokud by nové pravidlo porušila.

**Mimo rozsah:** výpočet ocenění a účtování, storno zveřejněného ocenění, práva rolí v `ir.access.csv`, SQL zápisy
do databáze, výjimka pro převzetí fondu (historická ocenění řeší etapa PF – jen poznamenat do otevřených bodů).

**Nasazení do `investra`:** jen se souhlasem Martina v promptu: záloha do `zalohy/`, `-u investra_nav`, kontrola logu.
Ocenění id 39 fondu C pak zruší Martin tlačítkem (ne skript, ne SQL).

**Kritéria přijetí:** všechny testy bez selhání (číslo z výstupu); v `investra` nejde založit ocenění fondu C k datu
před 31. 10. 2026; po zrušení id 39 nezbude žádný návrh dokladu fondu C k 1. 9. 2026 (SELECT ve Výsledku); deník
rozhodnutí doplněný.

## Výsledek

Doplní provádějící relace.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí
