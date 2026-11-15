# IM-01 Číselníky, práva a seed

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová (nový addon) |
| Plán | `docs/navrh-evidence-nastroju.md`, oddíly 2, 3.1, 3.2, 4, 5, 6 (jen Číselníky) |
| Vzory | `addons/custom/investra_counterparty/` (manifest, `ir.access.csv`, `data/esa_sector.xml`), nabídky v `addons/custom/investra_entity/views/entity_views.xml` |

**Cíl:** addon `addons/custom/investra_instrument_master` (závislost `investra_counterparty`, verze `20.0.0.1.0`) se skupinou
„Investra: správce číselníků“, číselníky a jejich nabídkou.

**Rozsah souborů:** jen nový addon a `tools/codelist_seed.py`.
- `models/codelist_mixin.py`, `models/regulatory_codes.py` (BA0088, skupina BA0088, ESA kód, typ emitenta, členství zemí),
  `models/classification_codes.py` (oceňovací kategorie, důvod klasifikace)
- `security/security.xml`, `security/ir.access.csv`
- `views/configuration_views.xml`, `views/menus.xml`
- `data/*.xml` podle oddílu 4 plánu; `esa_code.xml` a `ba0088.xml` vygeneruje `tools/codelist_seed.py` z
  `docs/cnb/ciselniky-FOFI20261201.csv` (ESA) a `docs/cnb/ciselnik-BA0088-v023.csv` (BA0088); oddělovač `;`, UTF-8 s BOM
- `tests/test_code_lists.py`, `tests/test_security.py`

**Mimo rozsah:** rozšíření emitenta, nástroje a portfolia; import; CFI mapa; jakýkoli kód, který není v `docs/cnb/`.

**Kritéria přijetí:**
- 80 ESA kódů; typy emitenta VLI 8, BANK 18, FIN 42, NFP 6, OST 6; 1311000 → R, VLI; 2002212 → NR, BANK; 1230100 → FIN.
- `residency_warning` se ukáže, když kód začíná 1 a rezidentství je NR.
- 84 položek BA0088, z toho 52 s příznakem „Nabízet u nástroje“, rodinou a skupinou; 63 má páku povinnou, 191 zakázanou, 7 vyžaduje zdůvodnění; 27 zemí EU od 2020-02-01; překryv období členství se odmítne.
- Uživatel s čtením účetnictví číselník nezapíše; správce číselníků založí a upraví; nikdo nemaže; `code` po založení nejde změnit.
- Změna názvu a typu emitenta je v historii záznamu.
- Instalace na čisté databázi bez chyb a varování modulu.

**Commit:** `Číselníky ČNB a IFRS 9: modely, práva a seed`

## Výsledek

Hotovo 15. 11. 2026, větev `feature/instrument-master` (založena z `feature/nav-prototyp`, neexistovala).

**Změněné soubory:** nový addon `addons/custom/investra_instrument_master/` (manifest, `models/` mixin + regulatory_codes +
classification_codes, `security/` skupina a `ir.access.csv`, `data/` 7 souborů, `views/` configuration + menus, `tests/`)
a `tools/codelist_seed.py` (generuje `esa_code.xml`, `ba0088.xml` a `ba0088_group.xml`).

**Testy** (dočasná DB `investra_ci_master`, postup oddílu 2 plánu: instalace → `l10n_cz` → `-u` s testy):
`0 failed, 0 error(s) of 15 tests`. Instalace na čisté DB bez ERROR a bez varování modulu (zůstala jen varování infrastruktury:
`--without-demo=all`, `/mnt/extra-addons`, markdown2). Počty ověřeny testy: ESA 80 (VLI 8, BANK 18, FIN 42, NFP 6, OST 6), příklady
1311000 → R/VLI, 2002212 → NR/BANK (ESA 2010 2002200), 1230100 → FIN; BA0088 84 / 52 nabízených, páka 63 povinná a 191 zakázaná,
zdůvodnění jen kód 7; EU 27 zemí od 2020-02-01, překryv odmítnut; práva (čtenář nezapíše, správce založí a upraví, nikdo nesmaže,
`code` nejde změnit); změna názvu a typu emitenta v historii. Dočasná DB i filestore smazány.

**Neověřeno:** vzhled formulářů v prohlížeči (pohledy jen načteny při instalaci); instalace do `investra_test`/`investra_vzhled` se
podle IM-00 nedělala; moduly `investra_counterparty` a ostatní testy nespuštěny (addon do nich nezasahuje).

**Odchylky a rozhodnutí k potvrzení:**
- Mixin sám dědí `mail.thread` (jinak Odoo hlásí varování u `tracking`).
- Názvy skupin BA0088 (např. „Státní dluhopisy“) a typů emitenta ze zadání plánu; české názvy skupin jsem doplnil sám, v katalogu nejsou.
- `requires_issuer` / `requires_maturity` nastaveno jen u 52 nabízených kódů (ostatní nemají rodinu); splatnost u rodin debt a bill.
- Oceňovací kategorie: dle poznámky „zakládá jen modul“ uživatel nezakládá (přestože tabulka práv dává správci `cru`); upravovat smí.
- `locally_modified` se nastaví při každém zápisu mimo načítání modulu a kontext `investra_codelist_import` (včetně zápisu superuživatele).
- Nabídka Číselníky obsahuje jen sedm uvedených položek; „Import číselníku“ a „Účtování“ patří IM-02 a IM-07.
- Seznam ESA 2010 se ověřuje proti `investra_counterparty/data/esa_sector.xml` (skript skončí chybou, když cílový sektor chybí).

## Převzetí

- 15. 11. 2026 (IM-12): kód nainstalován do `investra_test` (`investra_instrument_master` 20.0.0.6.0 installed; `investra_instruments` 20.0.0.15.0). `investra_vzhled` zatím ne, viz Výsledek IM-12. Ověřeno jen stavem modulů, logem a SELECTem, ne průchodem v UI.
