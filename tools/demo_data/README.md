# Ukázková data pracovní databáze `investra`

Vše je smyšlené (názvy s „(smyšlený)“, ISIN s předponou ZZ, LEI s předponou ZZZZ00). Žádná skutečná klientská data
ani údaje z důvěrných podkladů. Zadání: `docs/ukoly/IM-13-nova-databaze-s-ukazkami.md`.

| Soubor | Co dělá |
|---|---|
| `run_seed.sh <databáze>` | založí databázi, pokud neexistuje (všechny `investra_*` kromě `investra_env_banner`, `l10n_cz`, `account_peppol`, čeština, bez demo dat Odoo), pak spustí oba skripty níže |
| `seed.py` | investiční společnost (matice „jeden člověk“), fondy A–E, emitenti, nástroje, portfolia, obchody, úpisy a odkupy, ocenění; kurzy uloží do evidence a promítne do Odoo |
| `seed_services.py` | Investra Services s.r.o.: kniha 500/2002 Sb. s osnovou `cz` upravenou podle `services_config.json`, smyšlené faktury, přijatá služba z EU v režimu identifikované osoby, bankovní výpisy s úhradami, dohadná položka |
| `services_export.sh` | znovu vytvoří `services_config.json` čtením `investra_dev` (jen SELECT v transakci jen pro čtení; účty, daně, fiskální pozice, deníky, datum otevření – žádné doklady, partneři ani DIČ) |

Povolené databáze: `investra` nebo dočasná `investra_ci_*` (zkouška; po ní smazat `odoo db drop`, viz `tools/run_tests.sh`).
Opakované spuštění nad naplněnou databází skončí hláškou a nic nezmění. Log je v `.test-logs/*-seed-<databáze>.log`.

Proč `account_peppol` už při založení: první načtení osnovy na čisté databázi ho jinak doinstaluje a přenačte registr
uprostřed skriptu.
