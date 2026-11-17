# ZJ-10 Sledování změn nastavení (vestavěné, chatter)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | **fáze 1 oranžová** (podle plánu níže); **fáze 2 červená** (`investra_nav`, `investra_allocation`, `investra_fx_revaluation` – modely); nejdřív plán, kód fáze 2 až po schválení Martinem |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace) z otevřeného bodu „Historie nastavení – stav a ověření“, 17. 11. 2026 |
| Model | fáze 1 Sonnet 5.5, fáze 2 Opus 5.5 (návrh; rozhodne Martin) |
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
3. **Fáze 1 (oranžová)** – `mail.thread`, `tracking=True`, `<chatter/>`:
   - `investra.fund` (13 polí), `investra.fund.class` (22 polí kromě poplatků), `investra.role.line`, `investra.approval.matrix.step` (řádkové → bod 2)
   - `investra.entity`, `investra.account.role`, `investra.role.account` (`investra_entity`, kromě `record_guard.py`)
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
6. **Rizika k posouzení:** objem `mail_message`; čtení chatteru vyžaduje čtení modelu (oprávnění v `security/ir.access.csv`); zprávy správce smí smazat, takže nejde
   o auditní důkaz (případná doinstalace `mail_tracking` je samostatné rozhodnutí, neprovádět); `mail.thread` nepřidává uložené sloupce – ověřit, že upgrade modulu
   nepotřebuje migraci dat (jinak plán fáze 2 vrátit Martinovi).
7. **Mimo tento úkol:** verze „Platí od“ (pro `base_mode`, alokace, převodník ČNB, FX profil) – o nich se rozhoduje zvlášť; dnes platí změna `base_mode` zpětně
   a sledování jen dohledá, kdy proběhla (podle `fee_rule.py:224`, výpočtem neověřeno – ověřit a výsledek napsat do Výsledku).
8. **Testy** (nové, bez změny očekávaných hodnot): pro každou skupinu modelů změna sledovaného pole **ve zvláštní transakci** (po `flush` a `commit` nebo samostatný
   `TransactionCase` krok) vytvoří zprávu typu tracking s původní a novou hodnotou; změna řádku zapíše zprávu do chatteru rodiče; změna `base_mode` na pravidle
   úplaty zapíše zprávu; poplatky třídy se nezdvojí. Spouští Claude (`tools/run_tests.sh <modul>`).
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

**Schválený plán:** fáze 1 – čeká na Claude; fáze 2 – čeká na plán a schválení Martina.

## Výsledek

Doplní řešitel.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
