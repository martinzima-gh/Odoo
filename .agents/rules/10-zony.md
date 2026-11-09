---
trigger: always_on
---

# Zóny kódu

Zóna se určuje podle cest, které změna mění. Když úkol zasáhne více zón, platí nejpřísnější.
Úkol z jedné zóny nesmí bez nového zadání sahat do přísnější zóny; když to vyžaduje, zastav se a napiš to do výsledku úkolu.

## Zelená: implementuješ samostatně podle zadání

- `addons/custom/*/views/*.xml`: formuláře, seznamy, nabídky, akce, vyhledávání
- `addons/custom/*/i18n/`: překlady
- **nové** testy v `addons/custom/*/tests/` (bez změny očekávaných hodnot existujících testů)
- dokumentace v `docs/` kromě zakázaných souborů níže; `docs/sql/*.sql` jen `SELECT`
- běžné opravy, které nesahají do oranžové ani červené zóny

## Oranžová: implementuješ jen podle plánu schváleného Claudem v zadání úkolu

- `addons/custom/*/security/` (`ir.access.csv`, skupiny)
- nová pole a jednoduché nové modely mimo červenou zónu
- `addons/custom/investra_instruments/`, `investra_counterparty/`, `investra_cnb/`, `investra_dashboard/`,
  `investra_fund/`, `investra_chart_fund/`, `investra_entity/` (kromě `record_guard.py`), `investra_env_banner/` – modely a data
- importy a exporty, `tools/nav_demo/`

## Červená: jen s plánem, který předem schválil uživatel; převzetí vždy reviduje Claude

- `addons/custom/investra_nav/` – `engine.py` a `models/`
- `addons/custom/investra_posting/`, `investra_fx_revaluation/`, `investra_allocation/`, `investra_rates/`,
  `investra_vat_identified/` – modely, data a logika
- `addons/custom/investra_entity/models/record_guard.py`
- `addons/custom/*/migrations/`
- změna nebo odstranění existujícího pole, změna `required`, `ondelete`, `store` u existujících polí
- **očekávané hodnoty** v `addons/custom/investra_nav/tests/scenarios/*.json` a vše v `tools/nav_reference/`
  (test se neopravuje úpravou očekávaného výsledku)

## Zakázané: neměníš nikdy

- `CLAUDE.md`, `docs/rozhodnuti.md`, `docs/otevrene-body.md`, `docs/architektura.md`
- `.agents/`, `.github/`, `.gitignore`, `docker-compose*.yml`, `.env*`
- `addons/third_party/`
- `tools/view_check/` (kontrola pohledů a kopie schémat Odoo)

Návrh změny zakázaného souboru napiš do výsledku úkolu; provede ji Claude.
