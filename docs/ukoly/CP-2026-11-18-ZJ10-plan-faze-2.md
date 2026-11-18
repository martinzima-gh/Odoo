# CP-2026-11-18 – ZJ-10: Plán sledování nastavení, fáze 2

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | Červená |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Větev úkolu | `cp/ZJ-10-2-plan` |
| Zadal, dne | Martin, 18. 11. 2026 |
| Navazuje na | [ZJ-10 – Sledování změn nastavení](ZJ-10-sledovani-zmen-nastaveni.md), body 2 a 4–8; převzetí kroků 1a a 1b |

**Cíl:** Po schválení doplnit historii změn nastavení fáze 2 v chatteru podle pravidel ZJ-10, bez změny výpočtů, účetních dat nebo významu stávajících ručních záznamů.

**Rozsah souborů:** Plánované modely a formulářové pohledy v `addons/custom/investra_nav/`, `addons/custom/investra_allocation/` a `addons/custom/investra_fx_revaluation/`; případně přímá závislost `investra_nav` na `investra_fund` a odpovídající testy. Sdílený mixin je v `investra_fund`; jeho rozšíření by vyžadovalo zvláštní schválení rozsahu.

**Mimo rozsah:** Jakákoli změna kódu před schválením tohoto plánu; výpočty NAV, účetní zápisy, změna platnosti „od“, databázová migrace, zpětné doplnění historie, `mail_tracking` a změna záznamů v pracovní databázi.

## Plán změn

### 1. Modely, sledovaná pole, chatter a testovací očekávání

Pravidlo pro hlavičky: `mail.thread`, `tracking=True` na níže uvedených nepočítaných polích a právě jeden `<chatter/>` na formuláři. Relace `related`, `compute` a One2many nejsou sledovány na hlavičce; jejich řádky se řeší samostatně. Popisky jsou opsané z deklarací polí v kódu.

U hlavičkových modelů očekávat standardní text Odoo 20 v těle `mail.message`, např. `Před úplatami → <b>Po všech úplatách</b> <i>(Základ před/po úplatách)</i>`. V testu oddělit vytvoření od změny a mezi nimi vyvolat `flush_tracking()` / precommit, bez `cr.commit()`.

| Model; soubor a třída | Typ, současný chatter / ruční zápis | Pole sledovat; nesledovat a proč | Formulář | Test: přesná očekávaná zpráva |
|---|---|---|---|---|
| `investra.fee.rule`; `investra_nav/models/fee_rule.py`, `InvestraFeeRule` (model od ř. 14) | Hlavička. Nedědí `mail.thread`; vlastní `message_post` nemá. | Sledovat: `fund_id` (Fond), `name` (Název), `active` (Aktivní), `statute_ref` (Statut a poznámka), `kind` (Druh), `basis` (Konvence dnů), `base_source` (Základ), `base_mode` (Základ před/po úplatách), `perf_base` (Základ výkonnostní odměny), `class_ids` (Platí třídy), `expense_role` (Nákladová role), `recipient_share` (Podíl příjemcům z tříd), `recipient_class_ids` (Přijímající třídy), `cover_class_id` (Třída krytí), `crystallisation` (Krystalizace). Nesledovat: `company_id` (related), `version_ids` (One2many; vlastní model/verze), `overlap_warning` (compute). M2M lze sledovat: krok 1b potvrdil podporu Many2many v Odoo 20. | `investra_nav/views/nav_views.xml`, `view_fee_rule_form` (ř. 427–515): chatter chybí; přidat jeden. Formulář fondu má chatter z jiného view, ale to není formulář pravidla. | Změnit `base_mode`: `Před úplatami → <b>Po všech úplatách</b> <i>(Základ před/po úplatách)</i>`. |
| `investra.fee.version`; `investra_nav/models/fee_rule.py`, `InvestraFeeVersion` (ř. 237–329) | Technicky řádkový záznam `rule_id`/`version_ids`, ale zároveň samostatná datovaná verze a přímý rodič pásem. Bez `mail.thread` i ručního zápisu. | Sledovat: `valid_from` (Platí od), `decision_ref` (Rozhodnutí nebo změna statutu), `rate` (Sazba p. a.), `threshold` (Práh základu), `fixed_monthly` (Pevná částka měsíčně), `fixed_mode` (Výpočet za období), `step_size` (Velikost pásma), `step_amount` (Příplatek za pásmo), `included_classes` (Tříd v ceně), `extra_class_monthly` (Příplatek za třídu), `min_annual` (Minimum ročně), `max_annual` (Maximum ročně), `perf_measure` (Měřítko výkonnosti), `perf_use_hwm` (High-water mark), `initial_reference` (Počáteční srovnávací hodnota), `hurdle_kind` (Překážka (hurdle)), `hurdle_rate` (Sazba překážky), `hurdle_margin` (Marže nad index), `hurdle_type` (Typ překážky), `catch_up` (Dohánění (catch-up)), `hurdle_floor_zero` (Záporný etalon počítat jako nulu), `benchmark_id` (Benchmark), `require_positive_return` (Jen při kladném výnosu), `probability` (Váha pravděpodobnosti dohadu), `cap_rate` (Strop z hodnoty). Nesledovat: `rule_id` (strukturální odkaz na rodiče), `company_id` (related), `tier_ids` (One2many, sledují se řádky pásem), `validity_state` (compute). | Vnořený `<form>` pod `version_ids` v `view_fee_rule_form` (ř. 455–500), bez chatteru i samostatného formuláře. **Rozhodovací hrana:** současný mixin posílá řádky jen přímo rodiči s `message_post`; pásmo má rodiče verzi. Doporučená jednoduchá varianta je dát verzi vlastní `mail.thread` a chatter do jejího vnořeného formuláře, aby `fee.tier` mohl použít existující mixin. To je výjimka z čistého pravidla „One2many řádek → mixin“ a možnost chatteru ve vnořeném formuláři není ověřena. Alternativa: rozšířit mixin v `investra_fund` o směrování vnořených řádků na hlavičku; to je změna mimo výslovný rozsah fáze 2. Martin musí vybrat variantu. | Při variantě vlastního chatteru: změnit `rate` `0.01 → <b>0.02</b> <i>(Sazba p. a.)</i>` na verzi; ověřit, že zpráva je v chatteru právě této verze. |
| `investra.fee.tier`; `investra_nav/models/fee_rule.py`, `InvestraFeeTier` (ř. 332–340) | Řádkový model One2many `tier_ids`; nedědí `mail.thread`, nemá ruční zápis. Doporučen existující `investra.line.tracking.mixin`, rodič `version_id`. | Sledovat: `amount_from` (Od částky), `rate` (Sazba). Nesledovat: `version_id` (odkaz na rodiče), `company_id` (related). | Jen editovatelný seznam vnořený do formuláře verze (`nav_views.xml:497`); bez vlastního chatteru. Zpráva jde do chatteru rodičovské verze podle schválené varianty výše. | Upravit sazbu: tělo obsahuje `Sazba: 0.01 → 0.02` (mixinu odpovídá formát `<li>{popis řádku} – {Popisek}: stará → nová</li>`); vytvoření navíc `Přidáno` a popisky nového řádku. |
| `investra.benchmark`; `investra_nav/models/fee_rule.py`, `InvestraBenchmark` (ř. 343–355) | Hlavička. Bez `mail.thread` a ručního zápisu. | Sledovat: `name` (Název). Nesledovat: `value_ids` (One2many, řádky níže). | Ve zdrojích nejsou nalezeny žádné formulářové/listové pohledy ani akce pro benchmark; pole ve verzi úplaty má `no_create`. Plánovat nový přístupný formulář/list/akci pro benchmark s jediným `<chatter/>` a seznamem hodnot. | `Index A → <b>Index B</b> <i>(Název)</i>`. |
| `investra.benchmark.value`; `investra_nav/models/fee_rule.py`, `InvestraBenchmarkValue` (ř. 358–366) | Řádkový model One2many `value_ids`; bez `mail.thread` a ručního zápisu. Doporučen mixin, rodič `benchmark_id`. | Sledovat: `date` (Datum), `value` (Hodnota), `source` (Zdroj). Nesledovat: `benchmark_id` (strukturální odkaz na rodiče). | Není samostatný pohled; doplnit řádkový formulář/seznam v novém formuláři benchmarku. Bez druhého chatteru na řádku. | Upravit hodnotu: tělo rodičovské zprávy obsahuje `Hodnota benchmarku – Hodnota: 100 → 101`; přidání řádku obsahuje `Přidáno` a `Datum`, `Hodnota`, případně `Zdroj`. |
| `investra.instrument.rate.period`; `investra_nav/models/instrument_rate.py`, `InvestraInstrumentRatePeriod` (ř. 270–320) | Řádek One2many nástroje. Model nemá `mail.thread` ani vlastní `message_post`; nástroj dědí `mail.thread` (`investra_instruments/models/instrument.py:123–124`) a helper `_log_cashflow_change` zapisuje do jeho chatteru. Změnu/přidání sazby už popisují `_apply_rate_change` (ř. 189–212), `unlink` (ř. 303–320) a změnu druhu sazby `write` (ř. 65). | Sledovat: `valid_from` (Platí od), `rate` (Sazba % p.a.), `note` (Poznámka). Nesledovat: `instrument_id` (rodič), `company_id` (related). Poznámku smí běžný uživatel měnit; ostatní změny `write` zakazuje. | Řádky jsou jen pro čtení v `nav_views.xml:746–775`; formulář nástroje má již jeden chatter v základním view `investra_instruments/views/instrument_views.xml:121`. Nepřidávat druhý. | Změna poznámky přes mixin: rodičovský chatter obsahuje `Poznámka: původní → nová`. Změna sazby přes wizard má již ruční text `Nová sazba 6 % p.a. platí od …; Toky Úrok: …`; smazání `Smazána sazba 6 % p.a. platná od …`. **Nedublovat** tyto zprávy mixinem; konkrétní `tracking_disable` a rozsah polí při create/unlink sladit s ponechaným ručním záznamem. Ruční text pro novou sazbu neobsahuje starou sazbu v obecném formátu `stará → nová (Popisek)`; schválení, zda jej rozšířit, je otevřená otázka. |
| `investra.allocation.scheme`; `investra_allocation/models/allocation.py`, `InvestraAllocationScheme` (ř. 12–29) | Hlavička. Bez `mail.thread` a ručního zápisu. Modul přímo závisí na `investra_fund` (`__manifest__.py:8`). | Sledovat: `fund_id` (Fond), `valid_from` (Platí od), `method` (Metoda rozdělení), `statute_ref` (Článek statutu), `residual_pro_rata` (Část zbytku podle kapitálů). Nesledovat: `company_id` (related), `line_ids` (One2many, řádky níže). | `investra_allocation/views/allocation_views.xml`, `view_scheme_form` (ř. 3–15), bez chatteru; doplnit jeden. | Změnit `method`: `Alokační poměr → <b>Pořadí nároků</b> <i>(Metoda rozdělení)</i>`. |
| `investra.allocation.line`; `investra_allocation/models/allocation.py`, `InvestraAllocationLine` (ř. 32–43) | Řádkový One2many `line_ids`; bez `mail.thread` i ručního zápisu. Doporučen mixin z `investra_fund`, rodič `scheme_id`; přímá závislost modulu na mixinu existuje. | Sledovat: `class_id` (Třída), `rank` (Pořadí nároku), `target_rate` (Cílový výnos p. a.), `residual_share` (Podíl na zbytku), `loss_rank` (Pořadí ve ztrátě). Nesledovat: `scheme_id` (strukturální odkaz), `company_id` (related). | Vnořený editovatelný seznam ve formuláři schématu (`allocation_views.xml:11–15`); zprávy mixinu jdou do chatteru schématu. | Změnit výnos: tělo rodičovské zprávy obsahuje `Nárok třídy – Cílový výnos p. a.: 0.04 → 0.05`. Ověřit i přidání a odebrání řádku včetně popisu řádku. |
| `investra.fx.profile`; `investra_fx_revaluation/models/fx_profile.py`, `InvestraFxProfile`, doplnění `fund_id` v `investra_nav/models/valuation.py`, `InvestraFxProfile` (ř. 116–119) | Hlavička. Bez `mail.thread` a ručního zápisu. | Sledovat: `name` (Název), `active` (Aktivní), `company_id` (Společnost), `fund_id` (Fond; readonly vazba pro automaticky založený profil), `account_ids` (Přeceňované účty), `gain_account_id` (Účet zisku z přecenění), `loss_account_id` (Účet ztráty z přecenění), `journal_id` (Deník), `rate_source` (Zdroj kurzu). Nesledovat: žádné z těchto polí nejsou deklarována jako `compute`/`related`; `rate_source` má default/onchange a kontrolu, ale není computed field. | `investra_fx_revaluation/views/fx_views.xml`, `view_fx_profile_form` (ř. 9–21), bez chatteru; doplnit jeden. M2M lze sledovat podle ověření kroku 1b. | Změnit `name`: `Profil A → <b>Profil B</b> <i>(Název)</i>`. Dodat samostatné ověření změny `account_ids` s očekávaným popiskem `(Přeceňované účty)` podle chování Odoo 20. |

### 2. Řádkový mixin a závislost

- `investra_allocation` přímo závisí na `investra_fund` a může mixin používat.
- `investra_nav` **nemá přímou** závislost `investra_fund` v manifestu (`depends` obsahuje `investra_instruments`, `investra_allocation`, `investra_fx_revaluation`). Závislost je nyní tranzitivní: `investra_instruments` i `investra_allocation` přímo závisí na `investra_fund`. Doporučení: doplnit přímou závislost `investra_fund` do manifestu `investra_nav`, protože nav modely budou přímo používat jeho mixin. Změna nevytváří cyklus podle současných manifestů (fund závisí jen na `investra_entity`). **Otázka pro Martina:** schválit přímou závislost?
- Mixin z `investra_fund/models/line_tracking_mixin.py` zapisuje `create`/`write`/`unlink` na rodiči a respektuje `tracking_disable` a `mail_create_nolog`. Při změně formátování zprávy má test odpovídat skutečnému formátu mixinu (`{popis řádku} – {Popisek}: stará → nová`), nikoli standardnímu HTML trackingu hlavičky.
- Otevřený návrh v tabulce pro `fee.version`/`fee.tier`: stávající mixin neumí trasovat vnořenou rodičovskou cestu `tier → version → rule`. Před kódem je nutné schválit buď chatter verze jako rodiče pásma, nebo samostatně rozšířit společný mixin (včetně rozsahu v `investra_fund`).

### 3. Hromadné a automatické zápisy

| Místo / zjištění | Plán |
|---|---|
| `tools/demo_data/seed.py:120,339` | Seed používá `UA` s `tracking_disable=True, mail_create_nolog=True`; vytvoření pravidla úplaty je pod tímto kontextem. Zachovat. |
| `tools/nav_demo/demo.py:30,58`, `demo_prehled.py:29`, `demo_vklad.py:28` | Prostředí demo skriptů už má `tracking_disable=True, mail_create_nolog=True`; zachovat. |
| `investra_nav/models/valuation.py:85–104`, `_ensure_fx_profile()` | Automaticky zakládá profil přes `Profile.create()` při založení fondu bez tracking kontextu. Doplnit `tracking_disable=True, mail_create_nolog=True`, aby automatická konfigurace nevytvářela šum v novém chatteru profilu. |
| `investra_nav/models/instrument_rate.py:71–80, 189–212, 384` | Počáteční sazba i sazba z wizardu jsou automaticky vytvořeny a současně je na nástroji ruční zpráva o změně sazby a tocích. Při zavedení mixinu potlačit pouze jeho duplicitní záznam na `create`/`unlink` cestě; zachovat `_log_cashflow_change`. Změnu `note` neztichovat. Konkrétní kontext sladit s implementací a otestovat. |
| Generování/verze pravidel, kopie pravidel, benchmarky, alokace, importy | V prohledaných `addons/custom/` a `tools/` nebyl nalezen další hromadný generátor/kopírování těchto modelů ani import fáze 2. Verze se vytvářejí přes vnořený formulář; benchmarky jsou použité v testech. Pokud implementace přidá hromadnou operaci, volat její ORM create/write s `tracking_disable=True` (u samotného create lze podle záměru použít `mail_create_nolog=True`). |
| `addons/custom/investra_instrument_master/wizard/codelist_import.py:130` | Import číselníků má již `tracking_disable=True, mail_create_nolog=True`, ale prohledaný kód nedokládá, že zapisuje některý model fáze 2. Neměnit kvůli této fázi bez nového důkazu. |

### 4. Rizika z bodu 6

- **Objem `mail_message`: neověřený/nezměřený.** Bez přístupu k pracovní databázi nelze zjistit počet stávajících zpráv ani odhadnout reálnou četnost změn. Každá změna hlavičky vytvoří tracking zprávu; mixin může seskupit více změněných polí/řádků do zprávy rodiče. Nejde o auditní důkaz; správce může zprávy smazat. `mail_tracking` se neinstaluje.
- **Čtení chatteru a ACL:** v příslušných `security/ir.access.csv` již existuje read ACL pro `account.group_account_readonly` u fee rule/version/tier, benchmark/value a rate period (`investra_nav/security/ir.access.csv:2,5,8,11,13,50`), alokační schéma/řádek (`investra_allocation/security/ir.access.csv:2,5`) a FX profil (`investra_fx_revaluation/security/ir.access.csv:2`). Připravovatelé mají u benchmarků a sazeb odpovídající ACL `cru`/`crud`. Není zatím doložen důvod měnit tato ACL. Chatter navíc podléhá standardním pravidlům modelu `mail.message` a přístupu k cílovému záznamu; efektivní čtení pro konkrétní uživatele nebylo možné ověřit pouze čtením těchto CSV. Při implementaci ověřit účty s `account.group_account_readonly` a připravovatele na testovací DB; nepřidávat plošné oprávnění k `mail.message`.
- **Migrace dat:** `mail.thread` a `tracking=True` podle ZJ-10 nepřidávají uložená pole do obchodních modelů; zprávy jsou v mailových modelech. Z pohledu zde čtených deklarací není důvod pro datovou migraci ani zpětné doplnění historie. Skutečný upgrade nebyl spuštěn (plánovací fáze; bez DB). Pokud implementace zjistí potřebu nového uloženého pole nebo migrace, zastavit a vrátit plán Martinovi.

### 5. Změna `base_mode` zpětně (bod 7)

**Potvrzeno pro nově přepočítávaná období:** `investra.fee.rule.base_mode` je pole hlavičky pravidla (`investra_nav/models/fee_rule.py:71–74`). `_engine_rule()` vrací aktuální `self.base_mode` spolu se seznamem verzí (`fee_rule.py:219–224`); pole není uloženo ve `investra.fee.version`. Engine pak větev pro `after` vybírá podle předané hodnoty (`investra_nav/engine.py:140–156`). Ocenění navíc rozděluje pravidla podle aktuálního `rule.base_mode` (`investra_nav/models/valuation.py:904–960`). Proto změna nastavení platí při každém následném přepočtu i pro historické období, jehož výpočet znovu načte toto pravidlo; neplatí jen pro nově založenou verzi sazby.

To samo o sobě **neznamená automatickou změnu již uložených/zaúčtovaných výsledků**: v tomto plánu není ověřeno, že se historická ocenění po změně pravidla sama přepočtou. Samostatně otestovat změnu `base_mode` na pravidle a nový výpočet historického období; test nesmí měnit očekávané hodnoty referenčních scénářů. Žádné automatické zpětné přepočítání ani úpravu účetních záznamů nenavrhuji.

### 6. Testy po schválení

Přidat testy k existujícím testům modulů. Změnu záznamu oddělit od jeho vytvoření vyvoláním `flush_tracking()` (viz `investra_fund/tests/test_tracking.py:24–28`); ověřovat `message.body`, nikoli pouze existenci `tracking_value_ids`. Nikde nevolat `cr.commit()`.

1. Každá hlavička v tabulce: zapsat původní hodnotu, flush, změnit jedno sledované pole, znovu flush; ověřit autora/datum a přesný fragment ve zprávě. Zahrnout `fee.rule.base_mode`, `fee.version.rate`, `benchmark.name`, `allocation.scheme.method`, `fx.profile.name`.
2. `fee.tier`, `benchmark.value`, `allocation.line` a `instrument.rate.period`: změnit jednotlivá sledovaná pole a ověřit příslušný fragment v chatteru rodiče; u mixinu navíc ověřit `Přidáno` a `Odebráno`. Pro rate period odděleně ověřit, že stávající ruční zpráva o změně sazby zůstane a duplicitní zpráva nevznikne.
3. Ověřit M2M změnu `fee.rule.class_ids` nebo `fx.profile.account_ids` v chatteru; Odoo 20 Many2many tracking potvrdil krok 1b, ale tyto konkrétní modely dosud netestoval.
4. `tracking_disable=True` na bulk fixture zápisu potlačí automatické tracking zprávy; explicitní ruční `message_post` v rate-period toku zůstane zachován.
5. Změřit, že jedna změna více polí téhož hlavičkového zápisu nevytváří neočekávané duplicitní zprávy; ověřit správu chatteru jen přes existující business ACL. Odoo testy spouští Claude přes `tools/run_tests.sh`, ne Copilot.
6. Staticky ověřit, že každý příslušný formulář má nejvýše jeden chatter; zvláštní pozornost dát existujícímu instrument view a novému/nested benchmark/version pohledu.

**Neověřeno:** zda Odoo 20 renderuje `<chatter/>` ve vnořeném formuláři One2many verze; skutečný počet `mail_message`; účinná ACL `mail.message` pro všechny skupiny; migrace/upgrade na DB; runtime výpočet historického ocenění. Tyto body nelze uzavřít pouhým čtením zdrojového kódu.

## Kritéria přijetí plánu

- Martin schválí řešení vnořeného vztahu `fee.version` → `fee.tier`, přímou závislost `investra_nav` na `investra_fund` a zachování ruční historie sazeb nástrojů bez duplicit.
- Kód se začne měnit až po tomto schválení a zůstane v červené zóně schváleného rozsahu.
- Každý nový test ověřuje konkrétní text zprávy a testy nezavádějí `cr.commit()` ani změny očekávaných hodnot scénářů.

**Schválený plán:** Čeká na Martina. Tento dokument je návrh; není souhlasem s implementací.

## Výsledek

- **Změněné soubory:** pouze tento plánovací záznam; žádný kód nebyl změněn.
- **Ověřeno:** `git status --short --branch` ukázal větev `cp/ZJ-10-2-plan` a čistý pracovní strom; přečteny instrukce Copilota, zadání ZJ-10 včetně převzetí 1a/1b, šablona, relevantní modely, pohledy, manifesty, ACL a související zápisy.
- **Neověřeno:** Odoo testy, upgrade databáze, reálný objem `mail_message` a živé ACL/renderování chatteru. Nebyl spuštěn Odoo test ani žádný zásah do databáze.
- **Otevřené otázky:** varianty pro vnořené verze/pásma; přímá závislost `investra_nav` na `investra_fund`; formát a potlačení duplicit ručního záznamu sazeb.

## Převzetí

**Revize plánu** – Claude (Opus 5.5) 18. 11. 2026, převzato commitem `87cfbd2` (autor Copilot).

- Ověřeno v kódu: `investra_nav` závisí na `investra_fund` jen nepřímo (manifest ř. 8); benchmark nemá žádný pohled; ruční zápisy sazeb
  nástroje (`instrument_rate.py` ř. 65, 210, 318).
- **Varianta „chatter na verzi úplaty“ nefunguje:** Odoo 20 chatter ve vnořeném formuláři (dialogu) nevykreslí –
  `mail/static/src/chatter/web/form_compiler.js:27` (`t-if: !env.inDialog`). Zprávy verze by v aplikaci nebyly vidět.
  Doporučení Clauda: rozšířit mixin v `investra_fund` o rodiče přes cestu (např. `_line_tracking_parent = "version_id.rule_id"`);
  verze i pásma pak píšou do chatteru pravidla úplaty, celá historie úplaty je na jednom místě.
- Ostatní body plánu bez námitek.

**Schváleno Martinem 18. 11. 2026** (plán s těmito úpravami; kód smí začít):
1. **Verze a pásma úplaty → chatter pravidla.** Mixin `investra.line.tracking.mixin` (`investra_fund`) se rozšíří o rodiče zadaného cestou
   (`"rule_id"` u verze, `"version_id.rule_id"` u pásma); stávající použití (`role_id`, `matrix_id`) se nemění. Verze se nesleduje vlastním chatterem.
2. **Přímá závislost** `investra_fund` v manifestu `investra_nav`.
3. **Sazby nástroje:** ruční zprávy (`_log_cashflow_change`) zůstávají beze změny; mixin sleduje jen `note` (`_line_tracking_fields = ("note",)`),
   create a unlink sazby probíhají s `tracking_disable=True`, aby nevznikly duplicity.
4. **Benchmark:** přidat seznam, formulář s hodnotami a chatterem a akci v nastavení úplat (práva podle stávajícího `ir.access.csv`).
- Řešitel kódu: červená zóna – Copilot podle svých pravidel kód nepíše; Antigravity (po obnovení kreditů) nebo Claude.

**Provedení** – Claude (Sonnet 5.5) 18. 11. 2026, commit `2a93615`: plán realizován včetně schválených úprav 1–4; podrobnosti, testy a nasazení
v sekci „Fáze 2“ v `ZJ-10-sledovani-zmen-nastaveni.md`.
