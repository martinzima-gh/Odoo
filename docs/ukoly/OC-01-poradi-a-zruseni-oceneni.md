# OC-01 Ocenění: zákaz data před existujícím oceněním a zrušení návrhu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (postup ocenění, NAV) – plán níže schvaluje Martin v promptu |
| Výchozí větev | `feature/instrument-master` po sloučení ST-03 (po ST-01 `main`) |
| Větev úkolu | `ukol/OC-01` |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Schválil | Martin, 15. 11. 2026 (prompt provádějící relace) |
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

Provedl Claude (Opus 5.5), 15. 11. 2026, větev `ukol/OC-01`.

- **Změněné soubory:** `investra_nav/models/valuation.py` (`_check_no_later_valuation` volaná z `create` a `write`;
  `action_cancel_draft`; `unlink` nejdřív zruší návrhy dokladů; fond dědí `mail.thread`), `investra_nav/views/nav_views.xml`
  (tlačítko „Zrušit návrh“ s potvrzením, jen role zpracovatele; chatter ve formuláři fondu `view_fund_form_history`),
  `investra_nav/__manifest__.py` (20.0.0.29.1), `investra_nav/tests/test_valuation_sequence.py`, `docs/rozhodnuti.md`,
  `docs/otevrene-body.md`, tento soubor, předávka.
- **Odchylka od plánu:** fond neměl žádnou historii, proto `investra.fund` dostal `mail.thread` a formulář fondu chatter
  (nový zděděný pohled v `nav_views.xml`, mimo vyjmenované soubory). Zápis: „Zrušen návrh ocenění … (stav …); zrušené
  návrhy dokladů: N“, autor a čas ze zprávy. Zrušené návrhy zůstávají jako události ve stavu `discarded` (doklad smazán).
- **Upravený test:** `test_moving_draft_date_is_checked` zakládal návrh 15. 1. vedle rozpracovaného 31. 1.; to nové
  pravidlo zakazuje. Ověřuje teď posun data návrhu dozadu před zveřejněné ocenění (chyba) a dopředu (projde).
- **Ověřeno (příkaz a výsledek):**
  - kód: návrhy dokladů ocenění vznikají jen v `_add_event` a jdou do `event_ids` (podmínka zadání splněna);
  - `tools/run_tests.sh investra_nav`: 0 failed, 0 error(s) of 344 tests; `tools/run_tests.sh all`: 0 failed,
    0 error(s) of 685 tests; dočasné `investra_ci_*` smazané skriptem;
  - nové testy (třída `TestValuationOrderAndCancel`, 8 testů) pokrývají všechny body zadání; zrušení Spočteného ocenění
    se zkouší i s uzávěrkou období po datu návrhů (jako id 39) a porovnává zaúčtované řádky před a po;
  - `investra`: záloha `zalohy/investra-2026-11-15-pred-OC01.dump` (pg_restore -l čte 10 742 položek),
    `-u investra_nav --stop-after-init` bez ERROR (varování jen stávající), verze 20.0.0.29.1, instance 8071 běží;
  - `investra`, Odoo shell s rollbackem: ocenění fondu C k 15. 10. 2026 odmítnuto („Fond už má ocenění k pozdějšímu datu
    31.10.2026…“), k 15. 9. 2026 odmítnuto pravidlem o zveřejnění předchozího (kvůli id 39); počet ocenění fondu beze změny (7).
  - Stav před zrušením id 39 (SELECT): ocenění 39 `computed`, události 215–217 `draft`, doklady 239–241 `draft`
    k 2026-09-01; uzávěrka společnosti 2026-10-31.
- **Neověřeno:** zrušení id 39 v `investra` (provede Martin tlačítkem). Kontrolní SELECT po zrušení:

      SELECT e.id, e.state, e.move_id FROM investra_accounting_event e
       WHERE e.res_model = 'investra.valuation' AND e.res_id = 39;      -- čekáme 3 řádky, state = discarded, move_id prázdné
      SELECT id FROM account_move WHERE id IN (239, 240, 241);         -- čekáme 0 řádků
      SELECT id FROM investra_valuation WHERE id = 39;                 -- čekáme 0 řádků

- **Otevřené otázky a návrhy mimo rozsah:** zapsané do `docs/otevrene-body.md`: výjimka pro historická ocenění
  při převzetí fondu (etapa PF); zrušení návrhu verze 2+ znemožní k témuž datu založit novou verzi (jedinečnost
  fond–datum–verze) – rozhodnout, zda zrušení verze 2+ zakázat.

## Převzetí
