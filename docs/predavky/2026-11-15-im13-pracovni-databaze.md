# Předávka 2026-11-15: IM-13 pracovní databáze `investra` (zastaveno na chybě modulu)

**Cíl:** jedna pracovní databáze `investra` (8071, bez lišty) s ukázkami fondů A–E a Investra Services s.r.o.

**Stav:** větev `feature/instrument-master`; databáze `investra` ani kontejnery se zatím neměnily.

**Hotové**
- Zálohy `zalohy/investra_test-2026-11-15-pred-IM13.dump` a `zalohy/investra_vzhled-2026-11-15-pred-IM13.dump`
  (pg_dump -Fc, `pg_restore -l` čitelné, 10 773 položek obsahu každá).
- `tools/demo_data/seed.py`: fondy A–E, emitenti s ESA a LEI, nástroje s BA0088, CFI, SPPI a potvrzením, portfolia
  s kategorií, účetní profily, variabilní sazba se 2 změnami, výplata Nepravidelně, prodej, kupóny, splátka jistiny,
  úpisy a odkupy, úplaty; matice investiční společnosti „jeden člověk“. Na dočasné DB doběhl: ocenění 14/12/6/4/1,
  poslední u A a B spočtené, kontroly jen upozornění. Dočasné DB smazané i s filestore.
- Databáze se musí zakládat i s `account_peppol` (jinak první načtení osnovy přenačte registr uprostřed skriptu).

**Chyba modulu, která brání naplnění (neopraveno)**
- Odoo 20 při `res.company.create` se zemí CZ zaregistruje odložené načtení osnovy (`install_l10n_modules` →
  `cr.precommit`, account/models/company.py ř. 1120–1131). `investra.entity.create_book` osnovu načte sám, ale odložený
  krok proběhne při nejbližším flush/commit znovu s odhadnutou šablonou (`investra_fund`) a přepíše měnu na CZK.
- Dopad: kniha v EUR (fond C) se po commitu účtuje v CZK; kniha investiční společnosti i Investra Services dostanou
  osnovu `investra_fund` místo `cz` (v `investra_test` má „Investra Services s.r.o.“ `chart_template = investra_fund`).
  Testy to nezachytí, protože necommitují. Totéž hrozí v UI (commit na konci požadavku).
- Návrh zadání (zóna dle Martina): v `create_book` zakládat společnost s kontextem `chart_template_load=True`
  (Odoo pak odložené načtení nepřidá) a test, který spustí `env.cr.precommit.run()` a ověří měnu a `chart_template`.

**Zbývá (první krok: schválit a opravit `create_book`)**
1. Oprava výše + testy na dočasné DB. 2. Část Investra Services (osnova 500/2002 Sb. čtením z `investra_dev`).
3. Krok 3–7 úkolu: DB `investra`, kontejner 8071, zastavení starých, `run_tests.sh` na dočasné DB, SQL, deník, Doc.

**Rozhodnutí:** funkční měna se nastavuje jen při založení knihy (výchozí CZK), po zaúčtování se nemění (Martin).

**Otevřené:** v repozitáři souběžně pracovala jiná relace (commity 177b93a–4da3a53); souhlas s převzetím jejích změn.

**Číst:** `CLAUDE.md`, `docs/ukoly/IM-13-nova-databaze-s-ukazkami.md`, `tools/demo_data/seed.py`,
`addons/custom/investra_entity/models/entity.py` (`create_book`).
