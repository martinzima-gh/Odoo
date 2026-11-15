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

## Převzetí
