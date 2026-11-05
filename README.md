# Investra – Odoo účetnictví a NAV

Soukromý repozitář platformy na Odoo 20 Community pro účetnictví společností skupiny Investra
a pro účetnictví a výpočet NAV investičních fondů. Vypořádání úpisů a odkupů a evidenci držitelů
řeší samostatný informační systém Asetiq.

## Kde co je

| Soubor | Obsah |
|---|---|
| [CLAUDE.md](CLAUDE.md) | pravidla projektu, prostředí, bezpečnost |
| [docs/architektura.md](docs/architektura.md) | export architektury z Claude Doc |
| [docs/rozhodnuti.md](docs/rozhodnuti.md) | deník rozhodnutí |
| [docs/otevrene-body.md](docs/otevrene-body.md) | otevřené body a rizika |
| [docs/kontrola-zadani.md](docs/kontrola-zadani.md) | zadání pro kontrolora; zprávy v `docs/kontroly/` |
| `addons/custom/` | vlastní moduly `investra_*` |
| `docker-compose.investra.yml` | vývojová instance (Odoo 20, http://127.0.0.1:8070) |

## Spuštění vývojové instance

1. Zkopírujte `.env.example` do `.env` a doplňte hesla.
2. `docker compose -f docker-compose.investra.yml up -d`
3. Testy modulu: `docker compose -f docker-compose.investra.yml run --rm --no-deps odoo odoo --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom -d investra_dev -u <modul> --test-tags /<modul> --stop-after-init --http-port 8099`
