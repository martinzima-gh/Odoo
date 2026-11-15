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
4a. **Schvalování jedním uživatelem (pokyn Martina 15. 11. 2026):** v databázi `investra` nastavit schvalovací matici
   a související parametry u všech fondů a operací tak, že stačí jeden uživatel (zadavatel smí sám schválit, „2 oči“).
   Nastavit přes ORM/UI, ne SQL; výchozí hodnoty modulů ani testy čtyř očí neměnit. Ukázkoví schvalovatelé pak nejsou
   nutní; stačí jeden pracovní uživatel. Ve Výsledku vypsat, které parametry se změnily a jak je vrátit.
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
Ocenění projdou celým postupem včetně schválení; schvaluje jeden uživatel (viz krok 4a). Žádná hesla v repozitáři.

**Investra Services s.r.o. – ukázka servisní organizace (doplněno 15. 11. 2026, pokyn Martina):** v databázi `investra`
bude vedle fondů i samostatná společnost Investra Services s.r.o. s osnovou pro podnikatele (vyhláška č. 500/2002 Sb.,
`l10n_cz`) upravenou podle `docs/osnova-investra-services.md` a rozhodnutí v deníku z 2026-11-07 a 2026-11-08 (osnova,
archivované daně a fiskální pozice, identifikovaná osoba – modul `investra_vat_identified`). Nastavení převzít ze
stávající `investra_dev` jen čtením (porovnat účty, daně, deníky); `investra_dev` se nemění. Ukázkové doklady
(smyšlené částky a partneři): několik vydaných faktur za služby, přijaté faktury včetně jedné služby z EU v režimu
identifikované osoby, bankovní výpis s úhradami, jeden interní doklad; období aspoň 3 měsíce. Účetní rámce se nemíchají:
Services účtuje podle 500/2002 Sb., fondy podle 501/2002 Sb., každá jednotka ve své společnosti. Co z nastavení Services
není z dokumentů a `investra_dev` jasné (mzdy, DIČ, kontakty jsou otevřené body), nezakládat a vypsat ve Výsledku.

**Mimo rozsah:** změny modulů (chybu, která brání naplnění, popsat a navrhnout jako zadání, neopravovat potichu),
sloučení do `main`, mazání starých databází, produkční prostředí.

**Kritéria přijetí:**
- http://127.0.0.1:8071 otevře databázi `investra` bez červené lišty; Přehled, Ocenění, Portfolio a Výkazy se načtou.
- 5 fondů; počty ocenění 14 / 12 / 6 / 4 / 1, všechna schválená kromě posledního u fondů A a B (rozpracované, aby bylo
  co zkoušet).
- Stejný dluhopis je ve fondu B a D v různých kategoriích a účtuje se podle zařazení.
- Kontroly ocenění bez chyb (upozornění vyjmenovat ve Výsledku); rozvaha každého fondu vyrovnaná, FK = aktiva − závazky.
- Investra Services s.r.o. je v databázi jako samostatná společnost s osnovou podle 500/2002 Sb.; obratová předvaha
  vyrovnaná, doklady zaúčtované, počty účtů a daní souhlasí s `investra_dev` (rozdíly vyjmenovat).
- `tools/run_tests.sh` nesáhne na `investra`; sada všech modulů na dočasné databázi: 0 selhání, 0 chyb.
- Zálohy starých databází existují a jsou čitelné; kontejnery zastavené, databáze zachované.

**Commit:** `Pracovní databáze investra s ukázkovými daty; testy jen na dočasných databázích`

## Výsledek

Hotovo 15. 11. 2026 (Claude, Opus 5.5). Ověřeno dotazy `docs/sql/24-pracovni-databaze.sql` nad `investra`.

- **Oprava modulu** (souhlas Martina, mimo původní rozsah): `create_book` zakládá společnost s kontextem
  `chart_template_load`; test simuluje odložené kroky jako commit. Bez opravy test selhal (EUR → CZK).
- **Databáze `investra`** (`tools/demo_data/run_seed.sh investra`): 15 modulů `investra_*` bez `investra_env_banner`,
  `l10n_cz`, `account_peppol`, čeština. http://127.0.0.1:8071 vrací přihlášení; 45 nabídek Investra (pohledy a první
  stránka dat) se načte bez chyby (kontrola přes ORM, v prohlížeči neověřeno).
- **Fondy:** ocenění 14 / 12 / 6 / 4 / 1, zveřejněná všechna kromě posledního u A a B (Spočteno). FK posledního
  zveřejněného ocenění = aktiva − závazky u všech pěti fondů na haléř; MD = D v každé knize. Dluhopis Česká
  infrastruktura 4,50/2029: fond B naběhlá hodnota, fond D FVTPL. Obchody 21, z toho 2 prodeje.
- **Upozornění kontrol** (chyby žádné): Ocenění schvaluje druhá osoba; Úkony od minulého ocenění provedla druhá osoba;
  Schvalovací matice se od minulého ocenění nezměnila; Úpisy a odkupy za zveřejněný kurz třídy; u B, C, D také Peníze
  a inkasa na cestě jsou nulové a Údaje nástrojů v portfoliu se od minulého ocenění nezměnily.
- **Krok 4a – parametry „jeden člověk“:** v knize investiční společnosti nové řádky schvalovací matice pro všechny
  činnosti s platností od 15. 11. 2026, `second_person = no`, provádějící role podle výchozí role činnosti.
  Výchozí řádky modulu ani testy se nezměnily. Návrat: nové řádky matice s pozdější platností a `second_person`
  podle výchozího nastavení (v UI Schvalovací matice), nebo databázi založit znovu bez tohoto kroku.
- **Kurzy:** smyšlené kurzy se ukládají do evidence a promítají do kurzů Odoo (`_publish`) jako při stahování;
  výsledky fondů se tím nezměnily (porovnáno se zkušebním během bez promítnutí).
- **Investra Services s.r.o.** (`seed_services.py`): kniha `service`, rámec 500/2002 Sb., osnova `cz`, CZK, otevření
  19. 3. 2026. Nastavení z `investra_dev` jen čtením (`services_config.json`): účty 289 aktivních / 41 archivovaných,
  daně 4 / 32, fiskální pozice a deníky (FA, FP, MISC, EXCH, BNK1; CABA a STJ archivované) shodně. Rozdíly: účty
  518810 a 518950 nejsou v šabloně, skript je založil; `restrictive_audit_trail` je zapnutý (`create_book`), v
  `investra_dev` vypnutý. Doklady srpen–říjen 2026: 5 vydaných faktur (2 neuhrazené), 5 přijatých (všechny uhrazené),
  z toho 1 služba z EU v režimu identifikované osoby (450 EUR, daň 21 % 2 333,96 Kč na 343221 a do nákladu, kurzový
  rozdíl 75,15 Kč), 3 bankovní výpisy, 1 dohadná položka (audit). Předvaha vyrovnaná, nic nezaúčtovaného.
  DIČ dodavatele z EU je vzorové číslo z nápovědy Odoo (DE123456788).
- **Nezaloženo (otevřené body Services):** mzdy a jejich účty, DIČ a kontakty Services, bankovní účet (číslo),
  den účinnosti registrace identifikované osoby.
- **Instance:** `investra-web` na 8071; zastavené `investra-test-web` (8071), `investra-vzhled-web` (8072) a služba
  `odoo` (8070). Databáze `investra_dev`, `investra_test`, `investra_vzhled` i svazky zachované. Zálohy
  `zalohy/*-2026-11-15-pred-IM13.dump` a `*-pred-zastavenim.dump` (10 788 položek, čitelné).
- **Testy:** `tools/run_tests.sh all` na dočasné databázi: 677 testů, 0 selhání, 0 chyb; dočasné databáze smazané.

## Převzetí

- 15. 11. 2026 (ST-01): commit d226d19 (a 177b93a, a80fa4d, 4da3a53), součást `feature/instrument-master`, sloučeno do `main`. Testy v době úkolu 677 (0/0), po sloučení `all`: 685, 0 selhání, 0 chyb. Nález: heslo správce v `investra` změní Martin při prvním přihlášení.
