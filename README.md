# Investra – Odoo účetnictví a NAV

Soukromý repozitář platformy na Odoo 20 Community pro účetnictví společností skupiny Investra
a pro účetnictví a výpočet NAV investičních fondů. Vypořádání úpisů a odkupů a evidenci držitelů
řeší samostatný informační systém (IS).

## Kde co je

| Soubor | Obsah |
|---|---|
| [CLAUDE.md](CLAUDE.md) | pravidla projektu, prostředí, bezpečnost |
| [docs/architektura.md](docs/architektura.md) | export architektury z Claude Doc |
| [docs/rozhodnuti.md](docs/rozhodnuti.md) | deník rozhodnutí |
| [docs/otevrene-body.md](docs/otevrene-body.md) | otevřené body a rizika |
| [docs/kontrola-zadani.md](docs/kontrola-zadani.md) | zadání pro kontrolora; zprávy v `docs/kontroly/` |
| [docs/cnb/](docs/cnb/README.md) | katalog výkazů, položek, kontrol a číselníků ČNB (rámec Fondy) |
| `addons/custom/` | vlastní moduly `investra_*` |
| `docker-compose.investra.yml` | databázový server a obraz Odoo 20; pracovní instance `investra-web` na http://127.0.0.1:8071 |
| `tools/demo_data/` | založení a naplnění pracovní databáze smyšlenými ukázkami (README ve složce) |

## Spuštění pracovní instance

1. Zkopírujte `.env.example` do `.env` a doplňte hesla.
2. Databázový server: `docker compose -f docker-compose.investra.yml up -d db`
3. Pracovní instance nad databází `investra` (http://127.0.0.1:8071):

   ```
   docker compose -f docker-compose.investra.yml run -d --no-deps --name investra-web -p 127.0.0.1:8071:8069 odoo \
     odoo --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
     -d investra --db-filter='^investra$' --max-cron-threads=0
   ```

   Po změně kódu modulu: `docker stop investra-web && docker rm investra-web`, upgrade modulu v `investra`
   (`-u modul --stop-after-init`, po dohodě a se zálohou) a znovu příkaz výše.
4. Testy modulu: `tools/run_tests.sh <modul[,modul]|all>` (každý běh na nové dočasné `investra_ci_<čas>`, která se po
   testu smaže; celý log v `.test-logs/`; popis v hlavičce skriptu).

## Přístup k databázi pro čtení

Databáze jsou pro DBeaver dostupné jen z tohoto počítače na `127.0.0.1:5433` (zachované `investra_dev`
a `investra_test`; v pracovní `investra` má účet `dbeaver_ro` stejná práva, skript `tools/db/dbeaver_ro_grants.sql`).
Účet `dbeaver_ro` smí pouze číst a nevidí hesla ani tajné údaje; heslo je v `.env`.
Ukázkové dotazy jsou v `docs/sql/`.
