# MN-06 Identifikace společnosti: IČO, DIČ, LEI a ESA v průvodci a knize

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (průvodce, formuláře, odvození sektoru; `create_book` jen nový nepovinný parametr kontaktu; účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` (po MN-09) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | Martinovy poznámky z průchodu zakládání 16. 11. 2026 (8–13), MN-05, MN-05b |

**Stav (ověřeno čtením kódu):**
- Údaje protistrany `investra.counterparty.profile` (`investra_counterparty`): platí od data, země, **Sektor ESA 2010**
  (`sector_id` → `investra.esa.sector`, povinný v DB), LEI (kontrola ISO 17442).
- `investra_instrument_master` (závisí na `investra_counterparty`) přidává **Kód sektoru ESA** (`esa_code_id` → `investra.esa.code`,
  detailní číselník ČNB D_S_RNBD_4, povinný jen ve formuláři) a verze s kontrolou (`review_state`, `is_latest`).
  Kód má vazbu `esa2010_sector_id` na sektor ESA 2010, ale profil ji nepoužívá – uživatel vybírá obojí ručně (poznámka 12).
- Výběr sektoru (vyhledávací okno) ukazuje jen Název, ne kód (poznámka 11; `display_name` kód obsahuje, seznam ne).
- Nový profil má prázdné Platí od a v drobečkové navigaci technický název `investra.counterparty.profile,NewId_…`.
- Průvodce zakládá vždy nový kontakt; IČO a DIČ jsou jen v Nastavení › Společnosti (aplikace Kontakty není nainstalovaná).

**Plán (od Clauda):**

1. **Sektor z kódu (pozn. 12):** v profilu se vybírá jen Kód sektoru ESA; Sektor ESA 2010 se doplní z `esa2010_sector_id`
   (onchange a zároveň v `create`/`write`, ať platí i pro import) a ve formuláři je jen pro čtení, když ho kód určuje. Kód bez
   vazby: sektor zadat ručně jako dnes. Stávající data neměnit; SELECTem v `investra` ve Výsledku uvést počet profilů, kde se
   sektor a kód neshodují.
2. **Číselníky ESA (pozn. 11):** seznamy `investra.esa.sector` a `investra.esa.code` mají kód jako první sloupec; vyhledávání
   podle kódu i názvu (`_rec_names_search = ["code", "name"]`).
3. **Historie profilu (pozn. 13):** Martin rozhodl historii zrušit – řeší MN-09, které běží **před** tímto úkolem (jeden profil
   na kontakt, bez Platí od). Tady jen drobečková navigace „Údaje protistrany – <kontakt>“, u nového záznamu „Nové údaje protistrany“.
4. **Průvodce Nová účetní kniha – skupina Identifikace (pozn. 10):** nepovinná pole IČO (`company_registry`, kontrola 8 číslic
   s kontrolní číslicí mod 11), DIČ (`vat`; u země Česko předvyplnit „CZ“ + IČO, lze přepsat), LEI, Kód sektoru ESA.
   Předvyplnění kódu podle druhu jednotky: fond, SICAV, podfond → rezidentský kód se sektorem „Fondy kolektivního investování
   (kromě FPT)“; investiční společnost → rezidentský kód se sektorem „Pomocné finanční instituce“; servisní → prázdné.
   Kódy vyhledat v číselníku, nevymýšlet; pokud jich odpovídá víc, nechat prázdné a uvést ve Výsledku. Je-li zadané LEI
   nebo kód, průvodce po založení vytvoří profil (země z průvodce). Pole profilu přidá do průvodce
   modul, který zná `esa_code_id` (`investra_instrument_master`) děděním průvodce, ne `investra_chart_fund`.
5. **Existující kontakt (pozn. 8):** v průvodci nepovinné pole Kontakt. Nabízí jen kontakty-firmy, které nejsou kontaktem jiné
   společnosti (`res.company.partner_id`). Vybraný kontakt převezme nová společnost (název z kontaktu, `company_id` kontaktu
   vyprázdnit, aby ho viděly všechny firmy); IČO, DIČ, LEI a kód se předvyplní z kontaktu a jeho aktuálního profilu
   a nový profil se nezakládá. Když se zadá jen Název a kontakt stejného jména existuje, průvodce na to upozorní a nabídne ho.
   `create_book` dostane nepovinný parametr kontaktu (`investra_entity`), bez něj chování beze změny (seed).
6. **Formulář knihy (pozn. 9):** ve skupině Identifikace IČO a DIČ upravitelné (pole společnosti; zápis jen pro toho, kdo smí
   měnit společnost, ostatním jen pro čtení), LEI a sektor dál z profilu s tlačítkem Údaje protistrany.
7. **Testy:** odvození sektoru z kódu (create, write, kód bez vazby), vyhledání sektoru podle kódu, kontrola IČO, předvyplnění
   DIČ, průvodce s identifikací vytvoří profil, průvodce s existujícím kontaktem nezaloží druhý kontakt ani profil, nabídka
   kontaktů vylučuje kontakty společností, upozornění na shodné jméno, seed beze změny (`create_book` bez kontaktu).
8. **Nasazení:** povýšení dotčených modulů v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071. V `investra` nic nezakládat.
9. **Manuál:** `docs/manual/01-spolecnost-a-kniha.md` – Identifikace v průvodci a knize, existující kontakt, proč má profil platnost.

**Pozn. 13:** rozhodnutí 2026-11-16 „Údaje protistrany bez historie“ (MN-09). Vlastní fond je také protistranou
(např. když do něj investuje jiný náš fond), proto používá stejný profil jako ostatní kontakty.

**Rozsah souborů:** `investra_counterparty`, `investra_instrument_master` (profil, číselníky ESA, dědění průvodce), `investra_chart_fund`
(průvodce: kontakt, IČO, DIČ), `investra_entity` (jen parametr kontaktu v `create_book` a pole IČO/DIČ ve formuláři knihy),
jejich testy, verze, README; `docs/manual/01-spolecnost-a-kniha.md`; tento soubor (Výsledek), předávka.

**Mimo rozsah:** zrušení historie profilu; změna kontroly verzí profilu; fond a třídy (MN-07); kurzy (MN-08).

**Kritéria přijetí:** testy dotčených modulů a `all` bez selhání na `investra_ci_*`; Výsledek uvádí kódy ESA pro předvyplnění
a co zůstalo neověřené v prohlížeči.

## Výsledek

Provedl Claude Code, 16. 11. 2026, větev `ukol/MN-manual`.

- **Změněné soubory:**
  - `investra_entity` (20.0.0.11.0): `models/entity.py` (`ico_is_valid`, pole IČO a DIČ, kontrola IČO u české společnosti,
    parametr `partner` v `create_book`), testy.
  - `investra_counterparty` (20.0.0.5.0): `models/counterparty.py` (`_rec_names_search` sektoru, název záznamu
    „Údaje protistrany – kontakt“ / „Nové údaje protistrany“), `views/counterparty_views.xml` (seznam a hledání sektorů
    s kódem, IČO a DIČ ve skupině Identifikace, jen pro čtení u ostatních než správců), testy.
  - `investra_chart_fund` (20.0.0.12.3): `wizard/new_book.py` jen háčky `_extra_book_values` a `_after_book_created`.
  - `investra_instrument_master` (20.0.0.8.0): závislost na `investra_chart_fund`; `models/issuer.py` (pole
    `code_sector_id`, doplnění sektoru z kódu při zápisu), `views/issuer_views.xml` (kód před sektorem, sektor jen pro čtení,
    když ho určuje kód), nové `wizard/new_book.py` a `wizard/new_book_views.xml` (Identifikace a Existující kontakt),
    `tests/test_new_book_identification.py`, `tests/test_issuer.py`.
  - `docs/manual/01-spolecnost-a-kniha.md`, tento soubor, předávka `docs/predavky/2026-11-16-mn06-identifikace.md`.
- **Ověřeno (příkaz a výsledek):**
  - `tools/run_tests.sh investra_entity,investra_counterparty,investra_instrument_master,investra_chart_fund`: 0 selhání ze 153.
  - `tools/run_tests.sh all`: 0 failed, 0 error ze 779 testů (208 s); dočasné `investra_ci_*` se smazaly.
  - SELECT v `investra` před povýšením: 10 profilů, 10 s kódem ESA, **0 s neshodným sektorem**, 0 s kódem bez vazby na sektor.
  - Záloha `zalohy/investra-2026-11-16-pred-MN06.dump` (9 MB, mimo git); `-u` všech čtyř modulů v `investra` bez chyby
    (v logu jen RST varování popisů modulů), nové verze v `ir_module_module`, nové pohledy v databázi, `investra-web`
    znovu spuštěna, http://127.0.0.1:8071/web/login vrací 200. V `investra` nic nezaloženo.
  - **Kódy ESA pro předvyplnění:** hledáním v číselníku vychází pro fond, SICAV a podfond sektor 1240000 a pro investiční
    společnost 1260000; rezidentské kódy jsou ale tři (1240100 veřejné, 1240200 soukromé národní, 1240300 pod zahraniční
    kontrolou; 1260100, 1260200, 1260300). Podle zadání proto předvyplnění zůstává **prázdné** a kód se vybírá ručně
    (hledá se podle čísla i názvu). Logika je hotová a předvyplní kód, jakmile bude pro druh právě jeden.
- **Odchylky od zadání:**
  - IČO: Odoo 20 nemá `company_registry`; IČO je v `additional_identifiers['CZ_EN']` kontaktu (čtou ho i sestavy l10n_cz).
    Pole IČO v knize i průvodci je proto vypočtené s inverzí přes `_set_additional_identifier`. Kontrola mod 11 je naše
    (Odoo CZ_EN nekontroluje).
  - „Kontakty-firmy“: `is_company` je v Odoo 20 vypočtené (pravdivé jen s DIČ), fond bez DIČ by se nenabídl. Nabízejí se
    samostatné kontakty (`parent_id` prázdné), které nejsou kontaktem společnosti.
  - LEI bez kódu ESA průvodce odmítne před založením (profil má sektor povinný v DB); zadání to nepopisovalo.
  - Existuje-li profil kontaktu, LEI a kód v průvodci jsou jen pro čtení; mění se v údajích protistrany.
  - Zápis profilu s kódem bez vazby na sektor u záznamu, který už sektor má, ho ponechá (dřív chyba „zadejte sektor ručně“).
- **Neověřeno:** chování v prohlížeči (průvodce, formulář knihy, formulář profilu, výběr sektoru a kódu, upozornění na
  stejné jméno, tlačítko Použít existující kontakt, `force_save` u jen čteného sektoru). Konfirmační dotaz průvodce
  a podmíněné pole IČO/DIČ pro správce × ostatní pouze podle struktury pohledu. Převzetí kontaktu s nastavenou jinou firmou
  a vícefiremová pravidla kontaktů nejsou testovaná na skutečné databázi.
- **Otevřené otázky a návrhy mimo rozsah:**
  - Který ze tří rezidentských kódů předvyplnit pro fond (např. 1240200 soukromé národní) a pro investiční společnost
    (1260200)? Rozhodnutí Martina; pak stačí upřesnit `_default_esa_code`.
  - Přidat do seedu IČO/DIČ ukázkových knih? Teď beze změny (`create_book` bez kontaktu).
