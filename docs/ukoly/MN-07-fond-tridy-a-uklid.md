# MN-07 Fond a třídy: zámky, pořadí, nápovědy, ISIN; úklid po MN-05

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (zámky polí třídy, migrace odstraní prázdný sloupec; účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` (po MN-06 a MN-09) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | nálezy MN-02 3, 4, 7; rozhodnutí 2026-11-16 „Poznámky ze zakládání fondu“; Martinovy souhlasy 16. 11. 2026 (My Company, sloupec `founder_id`) |

**Plán (od Clauda):**

1. **Zámek třídy (nález 3, rozhodnutí Martina):** po prvním zaúčtovaném pohybu třídy (úpis, odkup, převzetí – zjistit v `investra_nav`,
   co je „zaúčtovaný pohyb“) nejde změnit Kód, Měna zveřejnění kurzu, Desetinná místa a Zaokrouhlení kurzu, Desetinná místa
   a Zaokrouhlení kusů. Poplatky a jejich příjemci zůstávají měnitelné. Ve formuláři pole jen pro čtení, `write` odmítne
   srozumitelnou chybou (vzor: zámek data vzniku z MN-03, `launch_locked`).
2. **Seznam tříd (nález 4):** úchyt pro řazení (`sequence`, `widget="handle"`) a skrytý sloupec Aktivní (archivace).
3. **Nápovědy (nález 7):** `help=` u Kód, Název, ISIN, Rozdělování výnosu (třída), Frekvence ocenění, Úročení nástrojů
   v naběhlé hodnotě a Kalendáře ocenění (fond). Text z kódu a deníku, obchodní význam nevymýšlet; co nejde odvodit, uvést
   ve Výsledku.
4. **ISIN třídy:** kontrola formátu (2 písmena země, 9 znaků, kontrolní číslice podle ISO 6166 / Luhn). Pomocnou funkci dát tam,
   kde ji mohou později použít i nástroje (dnes kontrolují jen přítomnost ISIN); nástroje teď neměnit.
5. **My Company (souhlas Martina):** seed nastaví výchozí firmě (`base.main_company`) zemi Česko. V `investra` SELECTem
   ověřit zemi; pokud není Česko, nastavit ji přes ORM (`odoo shell`, souhlas v promptu).
6. **Sloupec `founder_id` (souhlas Martina se změnou schématu):** migrace `investra_entity` (`pre-migrate`,
   `ALTER TABLE investra_entity DROP COLUMN IF EXISTS founder_id`) s novou verzí modulu; ověřit na kopii `investra`
   ze zálohy (dočasná `investra_ci_*`) a pak v `investra`.
6a. **Předvyplnění kódu ESA v průvodci (rozhodnutí Martina 16. 11. 2026):** fond, SICAV a podfond → kód **1240200**,
   investiční společnost → **1260200** (oba „soukromé národní“), servisní společnost → prázdné; kód jde přepsat.
   Upřesnit `_default_esa_code` (`investra_instrument_master/wizard/new_book.py`, MN-06); kód hledat v číselníku podle
   hodnoty, ne podle id.
6b. **IČO a DIČ v seedu (rozhodnutí Martina):** `tools/demo_data/seed.py` (a `seed_services.py` u Investra Services, pokud
   to jde bez zásahu do `services_config.json`) doplní ukázkovým knihám smyšlené IČO s platnou kontrolní číslicí (mod 11)
   a DIČ „CZ“ + IČO. Smyšlenost ověřit: IČO nesmí patřit skutečné firmě – použít řadu, kterou nelze zaměnit (např. začínající
   99), a zmínit ji v README ukázek. Do `investra` se nepromítá (seed běží jen na nové databázi); ve Výsledku uvést.
7. **Testy:** zámek třídy (před a po prvním pohybu, poplatek jde změnit i po pohybu), kontrola ISIN (platný, neplatná
   číslice, špatný formát), předvyplnění kódu ESA podle druhu, seed na čisté databázi nastaví zemi My Company a IČO/DIČ knih
   (ověřit dočasnou `investra_ci_*` přes `run_seed.sh`, pak smazat).
8. **Nasazení:** povýšení dotčených modulů v `investra` se zálohou do `zalohy/`, restart 8071.
9. **Manuál:** `02-fond.md`, `03-tridy.md` (co nejde po prvním pohybu změnit, ISIN, řazení a archivace tříd).

**Rozsah souborů:** `investra_fund`, `investra_nav` (jen zámek třídy, pokud tam patří zjištění pohybu), `investra_entity` (migrace),
`tools/demo_data/seed.py` a případně `seed_services.py` (země My Company, IČO a DIČ), README ukázek, `investra_instrument_master/wizard/new_book.py` (jen `_default_esa_code`), testy, verze, `docs/manual/02-*.md`, `03-*.md`, tento soubor, předávka.

**Mimo rozsah:** změna poplatků v čase s platností od data; kontrola ISIN u nástrojů; identifikace (MN-06); kurzy (MN-08).

**Kritéria přijetí:** testy dotčených modulů a `all` bez selhání na `investra_ci_*`; v `investra` sloupec `founder_id` neexistuje
a My Company má Česko; Výsledek uvádí, co zůstalo neověřené v prohlížeči.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:** `investra_fund` (`models/fund.py`: `isin_is_valid`, kontrola ISIN, nápovědy; `views/fund_views.xml`: úchyt a sloupec Aktivní; test), `investra_nav` (nový `models/fund_class.py` – zámek, `views/nav_views.xml`, `tests/test_class_lock.py`), `investra_entity` (migrace `20.0.0.12.0/pre-migration.py`), `investra_instrument_master` (`_default_esa_code`, test), `tools/demo_data/seed.py`, `seed_services.py`, README ukázek, manuál `01`–`03`, deník rozhodnutí; verze entity 12.0, fund 8.4, nav 31.0, instrument_master 8.1.
- **Ověřeno (příkaz a výsledek):**
  - `tools/run_tests.sh all` na dočasné `investra_ci_*`: 787 testů, jediná chyba byla můj test ISIN založený v nesprávné třídě; po přesunu `tools/run_tests.sh investra_fund`: 16 testů OK. Ostatní moduly po opravě znovu nespouštěny (oprava se týkala jen testu).
  - Zámek třídy (před/po pohybu, návrh nezamyká, stornovaný drží, poplatky jdou, formulář má `readonly="movement_locked"`), ISIN (platný, špatná číslice, špatný formát), kód ESA podle druhu – testy výše.
  - Seed přes `run_seed.sh` na dočasné databázi: My Company má zemi CZ, všech 7 knih má IČO 99000016…99000903 a DIČ CZ+IČO; databáze smazána. První běh selhal (DIČ řady 99 neprojde kontrolou Odoo) → `no_vat_validation` v seedu.
  - Záloha `zalohy/investra-2026-11-16-pred-MN07.dump`; migrace vyzkoušena na kopii ze zálohy (do kopie jsem přidal sloupec `founder_id`, po upgradu zmizel; kopie smazána). Pak upgrade `investra_entity,investra_fund,investra_nav,investra_instrument_master` v `investra`, restart 8071 (HTTP 200).
  - V `investra` sloupec `founder_id` neexistoval už před migrací; My Company už měla Česko (SELECT), nic jsem tedy nenastavoval ani nezakládal.
- **Neověřeno:** chování v prohlížeči (úchyt řazení, readonly polí v řádku seznamu, skrytý sloupec Aktivní, chybová hláška při zápisu); nápovědy `help=` jsou odvozené z kódu a deníku a účinek **Frekvence ocenění** a **Kalendáře ocenění** na ocenění jsem v kódu nenašel, proto jsou popsány jen jako plánovaná četnost a plánovaná data; u **Rozdělování výnosu** je odkaz na rozhodnutí 2026-11-04. Kontrola ISIN se zatím týká jen tříd, nástroje beze změny.
- **Otevřené otázky a návrhy mimo rozsah:** (1) Archivovanou třídu nejde ve formuláři fondu vrátit (o2m neukazuje neaktivní řádky); chce Martin samostatný seznam tříd? (2) Seed IČO: DIČ řady 99 je bez kontroly formátu, případně použít jinou řadu, ale její neexistenci nejde z repozitáře ověřit. (3) Zámek nechrání před změnou kódu přes SQL ani import s `sudo` (jen `write`).
