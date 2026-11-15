# IM-02 Průvodce importem číselníků

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová |
| Plán | oddíly 2, 3.1, 4 (poslední věta o importu), 5 |

**Cíl:** správce číselníků nahraje novou verzi domény ve formátu katalogu ČNB (`domena;nazev_domeny_nebo_hierarchie;kod;hodnota`),
uvidí rozdíl a potvrdí zápis.

**Rozsah souborů:** `wizard/codelist_import.py`, `wizard/codelist_import_views.xml`, `tests/test_code_list_import.py`,
manifest, `security/ir.access.csv`, položka nabídky.

**Chování:**
- Vstup: soubor, cílový číselník (BA0088 nebo ESA), doména ze souboru, metodika, platí od.
- Náhled po řádcích se stavem: nový / změněný název / beze změny / chybí v nové verzi (návrh `valid_to`) / konflikt
  (`locally_modified` a jiný název).
- Zápis s kontextem `investra_codelist_import`; konflikty se nepřepíší a vypíší se ve výsledku; nic se nemaže.
- U nového ESA kódu předvyplnit rezidentství z první číslice; typ emitenta nechat k doplnění a zápis bez něj odmítnout.

**Kritéria přijetí:** druhý import stejného souboru nic nezmění; ručně upravený řádek skončí jako konflikt a zůstane;
chybějící kód dostane `valid_to`, ne smazání; běžný uživatel průvodce nespustí.

**Commit:** `Import číselníků s náhledem a konflikty`

## Výsledek

## Převzetí
