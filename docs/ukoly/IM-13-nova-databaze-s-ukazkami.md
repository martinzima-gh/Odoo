# IM-13 Jedna pracovní databáze `investra` s ukázkovými daty

| Položka | Hodnota |
|---|---|
| Model | **Opus 5.5** (jedna relace; při vyčerpání kontextu předávka a pokračování) |
| Zóna | provozní krok + nový skript v `tools/`; kód modulů se nemění |
| Souhlas | Martin 15. 11. 2026: nová databáze `investra` na 8071, staré databáze zálohovat a zastavit (nemazat), lišta bez štítku, rozsah fondů podle tabulky níže |
| Číst | `tools/nav_demo/*.py` (vzor zápisu přes ORM), `tools/run_tests.sh`, `docker-compose.investra.yml`, `addons/custom/investra_instrument_master/README.md`, `docs/navrh-variabilni-sazba.md` |

**Cíl:** jedna databáze, se kterou uživatel pracuje a kterou dál vyvíjí, naplněná smyšlenými ukázkami.

**Stav dnes (ověřeno):** `investra-test-web` (8071) běží příkazem `odoo … -d investra_test --db-filter=^investra_test$`
nad `~/odoo-dev/addons/custom`; `investra_vzhled` (8072) čte kód z `~/odoo-review`; `investra_dev` (8070) se nepoužívá.
Červenou lištu TEST dělá modul `investra_env_banner`.

**Postup:**
1. Záloha `investra_test` a `investra_vzhled` (`pg_dump` custom do `zalohy/`, ověřit `pg_restore -l`).
2. Skript `tools/demo_data/seed.py` (spouští se přes `odoo shell`, jen ORM a metody, které volá uživatel v UI;
   žádné přímé SQL; opakované spuštění nad naplněnou databází skončí hláškou, nic nepřepíše). Nejdřív ho odladit na dočasné
   `investra_ci_demo` (tu po odladění smazat).
3. Nová databáze `investra`: instalace všech modulů `investra_*` **kromě `investra_env_banner`**, `l10n_cz`, bez demo dat
   Odoo; pak `seed.py`.
4. Kontejner na 8071 spouštět nad `investra` (`-d investra --db-filter=^investra$`); kontejnery `investra-test-web`,
   `investra-vzhled-web` a služba `investra_dev` na 8070 zastavit. **Databáze ani svazky nemazat.**
5. `tools/run_tests.sh`: přestat používat pracovní databázi; testy jen na dočasné `investra_ci_*` (vytvořit, otestovat,
   smazat). Upravit `CLAUDE.md` (tabulka Prostředí, věta o testech) a README.
6. Ukázkové SELECTy s počty do `docs/sql/` (fondy, ocenění podle fondu, obchody, zařazení podle kategorie).
7. Deník rozhodnutí, Claude Doc (tabulka Přijatá rozhodnutí), předávka do `docs/predavky/`.

**Ukázková data (vše smyšlené, názvy s „(smyšlený)“; žádná skutečná klientská data ani údaje z důvěrných podkladů):**

| Fond | Zaměření | Ocenění |
|---|---|---|
| A | akcie a podílové listy, funkční měna CZK, třídy CZK a EUR | 14 měsíčních |
| B | dluhopisy: pevná sazba, variabilní sazba (aspoň 2 změny sazby), výplata Nepravidelně; portfolia AC a FVTPL | 12 měsíčních |
| C | úvěry a vklady v naběhlé hodnotě, funkční měna EUR | 6 |
| D | smíšený; drží stejný dluhopis jako fond B v jiné oceňovací kategorii | 4 čtvrtletní |
| E | nový fond: jen úpisy a první obchody | 1 |

K tomu: emitenti s detailním ESA, zemí a LEI ve správném formátu (smyšlené); nástroje s BA0088, CFI, posouzeným SPPI
a potvrzenou klasifikací; schválená portfolia s kategorií a účetním profilem; ceny a kurzy pro každý den ocenění; úpisy
a odkupy v několika obdobích; aspoň jeden prodej, jedna splátka jistiny a jeden kupón; úplaty podle nastavení fondu.
Ocenění projdou celým postupem včetně schválení (schvaluje jiný uživatel než zadavatel, podle schvalovací matice);
založit k tomu ukázkové uživatele bez hesel v repozitáři (hesla nastaví Martin v UI, nebo se vypíší jen jemu mimo git).

**Mimo rozsah:** změny modulů (chybu, která brání naplnění, popsat a navrhnout jako zadání, neopravovat potichu),
sloučení do `main`, mazání starých databází, produkční prostředí.

**Kritéria přijetí:**
- http://127.0.0.1:8071 otevře databázi `investra` bez červené lišty; Přehled, Ocenění, Portfolio a Výkazy se načtou.
- 5 fondů; počty ocenění 14 / 12 / 6 / 4 / 1, všechna schválená kromě posledního u fondů A a B (rozpracované, aby bylo
  co zkoušet).
- Stejný dluhopis je ve fondu B a D v různých kategoriích a účtuje se podle zařazení.
- Kontroly ocenění bez chyb (upozornění vyjmenovat ve Výsledku); rozvaha každého fondu vyrovnaná, FK = aktiva − závazky.
- `tools/run_tests.sh` nesáhne na `investra`; sada všech modulů na dočasné databázi: 0 selhání, 0 chyb.
- Zálohy starých databází existují a jsou čitelné; kontejnery zastavené, databáze zachované.

**Commit:** `Pracovní databáze investra s ukázkovými daty; testy jen na dočasných databázích`

## Výsledek

## Převzetí
