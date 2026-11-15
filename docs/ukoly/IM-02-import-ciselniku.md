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

Hotovo 15. 11. 2026 (Claude Code), větev `feature/instrument-master`. Verze addonu `20.0.0.6.0`.

**Změněné soubory** (addon `investra_instrument_master`): nové `wizard/codelist_import.py`, `wizard/codelist_import_views.xml`,
`tests/test_code_list_import.py`; upraveny `wizard/__init__.py`, `tests/__init__.py`, `security/ir.access.csv`
(průvodce a řádky: jen správce číselníků, crud), `__manifest__.py`. Nabídka Nastavení → Číselníky → Import číselníku (jen správce).

**Chování:** soubor CSV ve formátu `domena;nazev_domeny_nebo_hierarchie;kod;hodnota` (doména se zadá, výchozí `D_S_RNBD_4`) nebo
ve formátu katalogu BA0088 (`…;typ;kod;nazev`, bere jen `polozka`). Náhled po řádcích: nový / změněný název / beze změny / chybí
v nové verzi / konflikt (`locally_modified` a jiný název); zapisují se zaškrtnuté řádky (konflikt a beze změny nejdou zaškrtnout).
Zápis s kontextem `investra_codelist_import`, nic se nemaže; chybějící kód dostane `valid_to` = den před „Platí od“; výsledek vypíše
počty a konflikty. Nový ESA kód: rezidentství z první číslice (jiná číslice → chyba), typ emitenta se doplní v náhledu, bez něj zápis
odmítnut. Nový kód BA0088: `parent_code` = nejdelší kratší existující kód, `selectable` vypnuto.

**Testy** (dočasná DB `investra_ci_master`, postup oddílu 2 plánu: instalace → `l10n_cz` → `-u` s testy):
`0 failed, 0 error(s) of 79 tests` (71 dřívějších + 8 nových). Nová kritéria: druhý import téhož souboru nic nemění; ručně upravený
řádek = konflikt a zůstane; chybějící kód dostane `valid_to`, nesmaže se a podruhé se nenavrhuje; nový ESA kód bez typu emitenta
nebo s chybnou číslicí se odmítne; formát katalogu BA0088 (souhrnné řádky se přeskočí, `parent_code`); chybné soubory; čtenář
průvodce nezaloží. Jediný ERROR v logu je známý `null value … reason` ze stávajícího testu IM-04. DB i filestore smazány.

**Neověřeno:** vzhled a ovládání průvodce v prohlížeči (pohled se jen načetl při instalaci); import skutečného nového vydání metodiky;
velký soubor (výkon); jen výchozí kódování UTF-8; instalace do `investra_test`/`investra_vzhled` se nedělala.

**Odchylky:** hlídání práv je v modelu (`has_group` v metodách) i v tabulce práv; `valid_to` navrhuje den před „Platí od“ (zadání den neurčuje);
řádek „chybí“ s již ukončenou platností se bere jako beze změny; u ESA se `esa2010_sector_id` u nových kódů nevyplňuje (potvrdí metodik);
změna názvu přepíše i „Zdroj metodiky“. README addonu nadále uvádí průvodce jako nehotový – opraví se v další dokumentační úpravě.

## Převzetí
