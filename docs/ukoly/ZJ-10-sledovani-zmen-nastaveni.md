# ZJ-10 Sledování změn nastavení (vestavěné, chatter)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **fáze 1 oranžová** (podle plánu níže); **fáze 2 červená** (`investra_nav`, `investra_allocation`, `investra_fx_revaluation` – modely); nejdřív plán, kód fáze 2 až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace) z otevřeného bodu „Historie nastavení – stav a ověření“, 17. 11. 2026 |
| Řešitel a model | fáze 1a a 1b: Antigravity nebo Copilot (levnější model, Sonnet 5.5); fáze 2: plán a kód Antigravity / Copilot podle plánu, revize a převzetí Claude (Opus 5.5); rozhodnutí Martina 2026-11-18: co zvládnou levnější modely, dělají ony |
| Pořadí | 1a → převzetí Claudem → 1b → plán fáze 2 → schválení Martinem → kód fáze 2; každý krok samostatná větev `ag/ZJ-10-<krok>` |
| Navazuje na | `docs/otevrene-body.md` (řádky „Historie nastavení“ a „Pravidlo sledování změn“), ZJ-03 (poplatky třídy), rozhodnutí 2026-11-16 „Údaje protistrany bez historie“ |

**Cíl:** každá změna nastavení a kmenových dat, která ovlivňuje výpočet nebo výkazy, se dohledá: kdo, kdy, stará → nová hodnota, a vidí se
v chatteru (postranní okno formuláře). Používá se **vestavěné sledování Odoo 20** (`mail.thread` + `tracking=True`); modul `mail_tracking` se **neinstaluje**.

**Ověřeno 17. 11. 2026** (dočasné DB, smazány): změna pole s `tracking=True` v samostatné transakci zapíše do chatteru zprávu „stará → nová (pole)“
i bez modulu `mail_tracking`. Vytvoření a změna v jedné transakci se slučují do „vytvořeno“. Komentář ve `investra_fund/models/fund.py` („bez mail_tracking
změny polí neukládá“) a věta v ZJ-03 jsou nepřesné – opravit.

**Plán má obsahovat** (u fáze 2 ke schválení):

1. **Pravidlo.** Model nastavení a kmenových dat dědí `mail.thread`, jeho pole bez výpočtu mají `tracking=True`, formulář má `<chatter/>`.
   Navrhnout text pravidla pro `CLAUDE.md` / `.agents/rules/` (zapíše Claude po schválení; Antigravity tyto soubory nemění).
2. **Společný pomocník pro řádkové modely.** Na One2many `tracking` nefunguje a řádek nemá chatter. Navrhnout jednoduchý mixin (nebo funkci), který ve
   `create`/`write`/`unlink` řádku zapíše zprávu do chatteru rodiče (vzor: ruční zápis poplatků třídy, `investra_fund/models/fund.py` kolem řádku 214).
   Poplatky třídy nezdvojovat: mají ruční zápis, `tracking=True` na ně nedávat.
   Mixin je jádro celého úkolu (dědí ho všechny řádkové modely), proto vzniká a prochází revizí **samostatně ve fázi 1a**, než se použije dál.
3. **Fáze 1 (oranžová)** – `mail.thread`, `tracking=True`, `<chatter/>`; dělí se na dva kroky:
   - **1a:** mixin z bodu 2 + `investra.fund` (13 polí), `investra.fund.class` (22 polí kromě poplatků), řádky `investra.role.line`,
     `investra.approval.matrix.step` (přes mixin); oprava komentáře ve `fund.py` a věty v ZJ-03; testy z bodu 8 pro tyto modely.
   - **1b** (po převzetí 1a): všechny ostatní modely níže, s mixinem z 1a.
   - `investra.entity`, `investra.account.role`, `investra.role.account` (`investra_entity`, kromě `record_guard.py`). `mail.thread` dědí základní
     model v `investra_entity`; pole, která na `investra.entity` přidává `investra_counterparty` (`lei`, `esa_sector_id`), jsou vypočtená a nesledují se.
     `investra.role.account` je samostatný záznam (mapování role na účet v knize), ne řádek; sleduje se i Many2many `extra_account_ids` – ověřit testem,
     že Odoo 20 změnu Many2many v chatteru ukáže, jinak zapsat ručně do chatteru záznamu.
   - `investra.instrument.type`, `investra.esa.sector` (`investra_counterparty`), `investra.accounting.profile` (doplnit pole), `investra.cfi.ba0088.map`
   - `investra.cnb.map` (`investra_cnb`), `investra.regulatory.deadline` (`investra_dashboard`)
4. **Fáze 2 (červená, plán ke schválení Martinem)** – modely v `investra_nav`, `investra_allocation`, `investra_fx_revaluation`:
   - **`investra.fee.rule`** (hlavička úplaty: role, **Základ před / po úplatách `base_mode`**, základ výkonnostní odměny, zdroj základu, článek statutu, poznámka,
     fond/třída), `investra.fee.version`, `investra.fee.tier` (řádkový → bod 2), `investra.benchmark` a hodnoty
   - `investra.instrument.rate.period` (ověřit, zda nemá vlastní ruční zápis)
   - `investra.allocation.scheme`, `investra.allocation.line` (řádkový → bod 2)
   - `investra.fx.profile`
5. **Co se nesleduje** (výjimky, každou potvrdit nebo doplnit v plánu): vypočtená a technická pole (příznaky, pořadí, barva); nezměnitelné záznamy a záznamy s vlastní
   historií (`approval.log`, `valuation.step`, `accounting.event`, `valuation.price.history`, řádky ocenění, pole stavu ocenění); hromadně plněné záznamy
   (kurzy `investra.rate`, ceny, importy číselníků – u nich `mail_create_nolog` a jejich vlastní platnost); průvodci a databázové pohledy; provozní záznamy se stavem
   nebo stornem (obchod, splátka, přecenění, žádost o výjimku z uzamčení, změna kmenových dat). Pokud model nemá sledování z jiného důvodu, uvést v plánu proč.
   **Hromadné zápisy – povinná úprava kódu:** `codelist_mixin.py` už dědí `mail.thread`, ale v kódu se zatím nikde nepoužívá `mail_create_nolog` ani
   `tracking_disable` (kromě migrace instrumentů). Po zapnutí sledování by import číselníku, seed ukázkových dat (`tools/demo_data/`) nebo hromadné
   plnění zapsalo zprávu ke každému řádku. Řešitel najde všechna místa hromadného `create`/`write` u sledovaných modelů (importy, plnění číselníků,
   seed) a volá je s kontextem `tracking_disable=True` (u `create` stačí `mail_create_nolog=True`, má-li se změna dál sledovat). Seznam míst uvede ve Výsledku.
6. **Rizika k posouzení:** objem `mail_message`; čtení chatteru vyžaduje čtení modelu (oprávnění v `security/ir.access.csv`); zprávy správce smí smazat, takže nejde
   o auditní důkaz (případná doinstalace `mail_tracking` je samostatné rozhodnutí, neprovádět); `mail.thread` nepřidává uložené sloupce – ověřit, že upgrade modulu
   nepotřebuje migraci dat (jinak plán fáze 2 vrátit Martinovi).
7. **Mimo tento úkol:** verze „Platí od“ (pro `base_mode`, alokace, převodník ČNB, FX profil) – o nich se rozhoduje zvlášť; dnes platí změna `base_mode` zpětně
   a sledování jen dohledá, kdy proběhla (podle `fee_rule.py:224`, výpočtem neověřeno – ověřit a výsledek napsat do Výsledku).
   Claude 18. 11. čtením kódu potvrdil: `_engine_rule` bere `base_mode` z hlavičky pravidla, ne z verze, takže změna platí pro všechna přepočítávaná
   období. Případný zámek `base_mode` po prvním výpočtu je samostatné rozhodnutí (červená zóna), v ZJ-10 se neřeší; řešitel jen ověří výpočtem.
8. **Testy** (nové, bez změny očekávaných hodnot): pro každou skupinu modelů změna sledovaného pole vytvoří zprávu typu tracking s původní a novou
   hodnotou; změna řádku zapíše zprávu do chatteru rodiče; změna `base_mode` na pravidle úplaty zapíše zprávu; poplatky třídy se nezdvojí; hromadný
   import číselníku nevytvoří zprávu na řádek. **V testech nikdy `cr.commit()`.** Zprávy o sledování se zapisují až v předcommitové fázi transakce;
   v testu je vyvolat `self.flush_tracking()` (třída testu dědí `mail.tests.common.MailCommon`, případně `MailCase`), nebo `self.env.flush_all()`
   a `self.env.cr.precommit.run()`. Vytvoření záznamu a změnu oddělit voláním `flush_tracking()` mezi nimi, jinak se sloučí do „vytvořeno“.
   Test, který zprávu nenajde, protože se nespustila předcommitová fáze, není úspěch. Spouští Claude (`tools/run_tests.sh <modul>`).
9. **Manuál:** krátká kapitola „Kde najdu historii změn“ (chatter, co se sleduje a co ne, že stopa platí od zapnutí) v `docs/manual/`.

**Rozsah souborů:** modely a pohledy uvedených modulů, `security/ir.access.csv` jen je-li nutné, nové testy, `docs/manual/`. Zakázané soubory (`CLAUDE.md`, deník,
otevřené body, `.agents/`) mění jen Claude.

**Mimo rozsah:** instalace `mail_tracking` nebo jiných modulů; změna `required`, `ondelete`, `store` existujících polí; migrace dat; zpětné doplnění historie;
nová pole typu „Platí od“; úprava výpočtu NAV.

**Kritéria přijetí:**
- Změna každého sledovaného pole z bodů 3 a 4 se v chatteru ukáže jako „stará → nová“ s autorem a datem; testy z bodu 8 projdou na dočasné databázi.
- Formuláře všech modelů z bodů 3 a 4 mají chatter (u řádků ho má rodič).
- Seznam výjimek (bod 5) je v plánu a v manuálu.
- Komentář ve `fund.py` a věta v ZJ-03 jsou opraveny.
- Pracovní databáze `investra` se při vývoji nemění; upgrade modulů v ní provede Claude po zálohách.

**Schválený plán:** Martin schválil 18. 11. 2026 rozdělení na fáze 1 a 2, rozsah modelů a pravidlo (v `CLAUDE.md`, deník „Sledování změn nastavení“). Fáze 1: po schválení Clauda může začít, nejdřív krok 1a (doplněno 18. 11.: rozdělení na 1a a 1b, testy bez commitu, hromadné zápisy, řešitel Antigravity / Copilot). Fáze 2 (červená): řešitel nejdřív předloží plán změn kódu (soubory, pole, otázky z bodu 6) a Martin ho potvrdí; teprve pak kód.

## Výsledek

Doplní řešitel.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
