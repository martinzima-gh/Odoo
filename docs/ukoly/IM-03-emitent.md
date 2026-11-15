# IM-03 Emitent: detailní ESA a odvozené údaje

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová |
| Plán | oddíly 2, 3.3, 5, 6 (Emitenti a protistrany), 7 |
| Číst | `addons/custom/investra_counterparty/models/counterparty.py`, `views/counterparty_views.xml`, `tests/test_counterparty.py` |

**Cíl:** profil protistrany nese detailní ESA kód; R/NR, typ emitenta a region se odvodí; schvalovatel verzi potvrdí.

**Rozsah souborů:** v novém addonu `models/issuer.py`, `views/issuer_views.xml`, `tests/test_issuer.py`, manifest.
Modul `investra_counterparty` se nemění (pohledy rozšířit přes `inherit_id`, nabídku přejmenovat záznamem v novém addonu
jen pokud to jde bez zásahu do cizího souboru; jinak nechat název a napsat to do Výsledku).

**Mimo rozsah:** změna `required` u stávajících polí, `BANK_SECTORS`, síťové ověřování LEI.

**Kritéria přijetí:**
- CZ + 1311000 → R, CZ, VLI; DE + 2002212 → NR, EU, BANK; US + 2001002 → NR, mimo EU, NFP.
- CZ + kód začínající 2 a DE + kód začínající 1 skončí chybou podle oddílu 7.
- `sector_id` se doplní z ESA kódu; testy `investra_counterparty` projdou beze změny (repo s bankou zůstává `repo`).
- Region se mění s členstvím země k datu (`_eu_status_at`), ne s ESA.
- Potvrzenou verzi nejde změnit; nová verze vyžaduje důvod změny; stejný LEI u jiné protistrany se odmítne.

**Commit:** `Emitent: detailní ESA, odvozené údaje a kontrola`

## Výsledek

**Změněné soubory** (vše v `addons/custom/investra_instrument_master/`): `models/issuer.py` (nový), `views/issuer_views.xml` (nový),
`tests/test_issuer.py` (nový), `models/__init__.py`, `tests/__init__.py`, `__init__.py` (`post_init_hook`), `__manifest__.py`
(verze `20.0.0.2.0`, pohledy, hook). Modul `investra_counterparty` beze změny.

**Testy:** dočasná databáze `investra_ci_master` (postup z oddílu 2 plánu: instalace modulu, `l10n_cz`, pak
`-u investra_instrument_master,investra_counterparty --test-enable --test-tags /investra_instrument_master,/investra_counterparty`):
`0 failed, 0 error(s) of 39 tests` = 14 nových (`TestIssuerProfile`) + 10 stávajících `investra_counterparty`
(beze změny, včetně repo s bankou) + 15 stávajících číselníků a práv. Databáze i filestore po testech smazány. Logy v `.test-logs/im03-*.log`.

**Ověřeno testem:** CZ+1311000 → R/cz/VLI, DE+2002212 → NR/eu/BANK, US+2001002 → NR/non_eu/NFP; chyby ESA × země (obě hlášky
podle oddílu 7); `sector_id` z ESA kódu (create i write, ručně zadaný sektor se zachová); region podle členství k datu
(`_eu_status_at`) a přepočet uloženého regionu při změně členství, ESA se nemění; potvrzení jen schvalovatelem, zámek potvrzené
verze (write i unlink); důvod změny u další verze; `is_latest` při create/write/unlink; LEI jedinečný napříč protistranami.

**Neověřeno:** vzhled pohledů v prohlížeči (XML se jen načetlo bez chyby; seznam, filtry, hlavička s tlačítkem a pruh nebyly
vizuálně zkontrolovány); instalace do `investra_test` / `investra_vzhled` se nedělala (podle IM-00 až po dokončení modulu).

**Odchylky a rozhodnutí k potvrzení:**
- `esa_code_id` je povinné jen ve formuláři (`required="1"` v pohledu), ne v databázi; dříve založené profily ESA kód nemají.
- Důvod změny se vyžaduje jen u verze s ESA kódem, která má dřívější verzi (jinak by padaly stávající testy `investra_counterparty`,
  které zakládají dvě verze bez důvodu). Starší profily bez ESA kódu se tím nezablokují.
- ESA kód bez přiřazeného sektoru ESA 2010 (např. 1443000) vyžaduje ruční zadání `sector_id`; jinak hláška místo chyby databáze (nad rámec plánu).
- Nabídka a akce „Protistrany“ jsou přejmenovány na „Emitenti a protistrany“ záznamem v novém addonu (bez zásahu do souborů
  `investra_counterparty`); výchozí filtr „Aktuální“ je v kontextu akce přepsán tamtéž.
- Potvrzení zapisuje přes `sudo` po kontrole skupiny schvalovatele (schvalovatel nemá právo zápisu na profil); zámek se na `sudo` nevztahuje (konvence z oddílu 2).
- `eu_status` je uložen „k dnešku“ a přepočítá se při změně země a členství; s plynutím času sám nepřepočítá (nové členství s budoucím „Platí od“ se projeví až po přepočtu). Případný cron by byl nad rámec úkolu.
- `is_latest` u existujících profilů nastavuje `post_init_hook` při instalaci; při upgradu z `20.0.0.1.0` by hook neběžel (modul zatím nikde nainstalován není).
- Zdroj `lei`/`sdat` jsou jen hodnoty výběru; žádné síťové ověřování.

## Převzetí

- 15. 11. 2026 (IM-12): kód nainstalován do `investra_test` (`investra_instrument_master` 20.0.0.6.0 installed; `investra_instruments` 20.0.0.15.0). `investra_vzhled` zatím ne, viz Výsledek IM-12. Ověřeno jen stavem modulů, logem a SELECTem, ne průchodem v UI.
