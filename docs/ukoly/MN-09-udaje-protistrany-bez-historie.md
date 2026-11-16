# MN-09 Údaje protistrany bez historie (jeden profil na kontakt)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová až červená (změna datového modelu protistrany, kterou čte klasifikace a evidence emitentů; účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | rozhodnutí Martina 2026-11-16 „Údaje protistrany bez historie“ (`docs/rozhodnuti.md`), mění část rozhodnutí 2026-11-15 „Evidence nástrojů – rozšíření místo paralelních modelů“; poznámka Martina 13 |

**Rozhodnutí:** údaje protistrany (země, sektor ESA, kód sektoru ESA, LEI) se nevedou s platností od data. Každý kontakt má
nejvýš jeden záznam; změna se přepíše. Stopu změn drží historie záznamu (tracking v chatteru: kdo, kdy, stará a nová hodnota).
Odeslané výkazy ČNB se archivují (požadavek do etapy CN), takže starý výkaz se nedopočítává znovu ze změněných údajů.

**Stav (ověřeno 16. 11. 2026):** `investra.counterparty.profile` (`investra_counterparty`) má `valid_from` a omezení
`unique(partner_id, valid_from)`; `investra_instrument_master/models/issuer.py` přidává verze (`is_latest`, `review_state`,
`reviewed_by`, `change_reason`, `source`). Profil k datu hledají `_counterparty_profile(day)` (res.partner), `_issuer_profile(day)`
(nástroj) a `investra_counterparty/models/classification.py`. V `investra` je 11 profilů na 11 kontaktů (žádný kontakt nemá
víc verzí), všechny `is_latest`.

**Plán (od Clauda; Opus ověří a odchylky popíše):**

1. Model: omezení `unique(partner_id)`; pole `valid_from` a `is_latest` zrušit (u stávajících volání `day` ignorovat, signatury
   `_counterparty_profile(day)` a `_issuer_profile(day)` ponechat, ať se nemusí měnit volající). Posoudit a doporučit, zda profil
   nechat jako samostatný model 1:1 ke kontaktu (méně změn), nebo pole přesunout na `res.partner`; bez schválení Martina
   zůstává samostatný model.
2. Kontrola verze (`review_state`, Zkontroloval, Důvod změny) zůstává na jediném záznamu: změna údaje vrací stav na
   „Ke kontrole“ (zjistit, jak to funguje dnes, a zachovat).
3. Všechna pole profilu s `tracking=True` (doplnit, kde chybí), aby přepis byl vidět v historii záznamu.
4. Migrace: pokud by kontakt měl víc profilů, ponechat nejnovější a hodnoty starších zapsat jako poznámku do historie
   ponechaného záznamu; starší pak odstranit přes ORM. V `investra` se to nemá týkat nikoho (ověřit SELECTem před i po);
   pokud by se týkalo, zastavit a napsat Martinovi. Sloupce `valid_from` a `is_latest` odstranit (souhlas v promptu).
5. Formuláře a seznamy: bez Platí od; tlačítko Údaje protistrany v knize otevře jediný záznam (nebo nový). Navázat na MN-06,
   pokud už proběhlo (průvodce zakládá profil bez data).
6. Testy: druhý profil téhož kontaktu odmítnut; změna sektoru je v historii záznamu a vrátí stav na Ke kontrole; klasifikace
   a profil emitentu k libovolnému datu vrací jediný záznam; migrace se dvěma profily na dočasné databázi.
7. Nasazení: povýšení dotčených modulů v `investra` se zálohou do `zalohy/`, restart 8071. Seed upravit, pokud zakládá profil s datem.
8. Manuál: `01-spolecnost-a-kniha.md` – údaje protistrany jsou jeden záznam, změny v historii záznamu.

**Rozsah souborů:** `investra_counterparty`, `investra_instrument_master` (profil, emitent, klasifikace), migrace, testy, verze,
README, `tools/demo_data/seed.py` (jen profil), manuál kap. 1, tento soubor (Výsledek), předávka.

**Mimo rozsah:** členství zemí v EU/EHP s platností (`investra.country.group.membership`) zůstává s historií; archiv výkazů ČNB (etapa CN).

**Kritéria přijetí:** testy `all` bez selhání na `investra_ci_*`; v `investra` 11 profilů beze změny hodnot; Výsledek uvádí
všechna místa, která četla profil k datu, a co zůstalo neověřené v prohlížeči.

## Výsledek

Provedl Claude (Opus 5.5) 16. 11. 2026 ve větvi `ukol/MN-manual`.

- **Změněné soubory:**
  - `investra_counterparty` (verze 20.0.0.4.0): `models/counterparty.py` – bez `valid_from`, omezení `unique(partner_id)`,
    `partner_id` s trackingem; `_counterparty_profile(day=None)` a `_issuer_profile(day=None)` datum ignorují (signatury
    zůstaly); LEI a sektor knihy bez data; tlačítko Údaje protistrany otevře formulář jediného záznamu, nebo nový
    s předvyplněným kontaktem a zemí. `models/classification.py` (jen komentář), `views/counterparty_views.xml` (bez
    Platí od), nová migrace `migrations/20.0.0.4.0/post-migration.py`, testy.
  - `investra_instrument_master` (verze 20.0.0.7.0): `models/issuer.py` – zrušeno `is_latest`, `_refresh_latest`
    a kontrola důvodu podle dřívější verze; tracking i u Zkontroloval, Zkontrolováno dne a Zdroj; `views/issuer_views.xml`
    (bez filtru Aktuální a pole Aktuální verze, tlačítko „Potvrdit údaje“, nový text upozornění), `__init__.py` a manifest
    (zrušen `post_init_hook`, který plnil `is_latest`), README, testy.
  - `tools/demo_data/seed.py`, `tools/nav_demo/demo_vklad.py` (profil bez data), `docs/sql/18-protistrany.sql`,
    `docs/sql/23-evidence-nastroju.sql`, `docs/manual/01-spolecnost-a-kniha.md`.
- **Místa, která četla profil k datu:** `res.partner._counterparty_profile(day)`; `investra.instrument._issuer_profile(day)`
  (volá jen test); `investra.portfolio.classification._proposal_role` (repo s nebankou podle sektoru k datu zařazení – nyní
  podle jediného záznamu); `investra.entity._compute_counterparty_profile` (k dnešku); `is_latest` ve filtru Aktuální
  a v SQL příkladech 23; `_check_change_reason` (dřívější verze); SQL příklad 18/4 (LATERAL k datu klasifikace).
- **Odchylka od dosavadního chování (bod 2):** potvrzený záznam dřív nešel změnit (změna = nová verze). Teď jde přepsat:
  změna údaje (kontakt, země, sektor, kód ESA, LEI) vyžaduje v témže zápisu nový Důvod změny, jinak chyba; po změně se
  stav vrátí na Ke kontrole a smaže Zkontroloval a datum (superuživatelem, aby to prošlo i přípravě). Zápis beze změny
  hodnot stav nemění. Mazání potvrzeného záznamu zůstává zakázané.
- **Doporučení k bodu 1:** ponechat samostatný model 1:1 ke kontaktu (tak je provedeno). Přesun na `res.partner` by
  přenesl kontrolu (Ke kontrole / Zkontrolováno), zámek a historii na obecný kontakt, který mění i fakturace a nákup,
  a vyžádal by si přepis práv, pohledů a migraci dat bez věcného přínosu.
- **Migrace:** post-migrace sloučí víc záznamů kontaktu do nejnovějšího (největší Platí od, pak id), hodnoty starších
  zapíše jako poznámku do historie ponechaného a starší odstraní přes ORM; omezení `unique(partner_id)` Odoo při
  duplicitách odloží a přidá na konci upgradu. Sloupce `valid_from` a `is_latest` odstranilo Odoo spolu s definicemi polí.
- **Ověřeno (příkaz a výsledek):**
  - `tools/run_tests.sh investra_counterparty,investra_instrument_master`: 0 failed, 0 error(s) of 94 tests.
  - `tools/run_tests.sh all`: 0 failed, 0 error(s) of 757 tests (varování jen prostředí a dvě stará v `investra_nav`);
    po poslední úpravě migrace znovu oba dotčené moduly: 0 failed of 94.
  - Zkouška migrace na `investra_ci_mig_*` obnovené ze zálohy `zalohy/investra-2026-11-16-pred-MN09.dump` s vloženým
    druhým profilem kontaktu 12: po `-u investra_counterparty,investra_instrument_master` 11 záznamů na 11 kontaktů,
    poznámka s hodnotami obou záznamů v historii ponechaného, omezení `investra_counterparty_profile_partner_uniq`
    existuje, sloupce zmizely, hodnoty ostatních záznamů shodné; kopie smazána.
  - `investra`: SELECT před upgradem 11 profilů na 11 kontaktů, žádný kontakt s víc záznamy; záloha
    `zalohy/investra-2026-11-16-pred-MN09.dump` (ověřena `pg_restore -l`); `-u investra_counterparty,investra_instrument_master`
    bez chyb a varování, migrace „odstraněno 0“; po upgradu 11 profilů a hodnoty (kontakt, země, sektor, kód ESA, LEI,
    stav, důvod, zdroj) shodné se stavem před upgradem; omezení existuje, sloupce `valid_from` a `is_latest` nejsou;
    verze modulů 20.0.0.4.0 a 20.0.0.7.0; 8071 restartována, přihlašovací stránka odpovídá 200.
- **Neověřeno:** v prohlížeči jsem nic neproklikal – formulář a seznam údajů protistrany bez Platí od, tlačítko Údaje
  protistrany v knize (otevře formulář jediného záznamu), zobrazení změny a poznámky v historii záznamu, hláška
  při změně potvrzených údajů bez důvodu. Pohledy prošly validací při upgradu a testy volají metody, ne UI.
- **Otevřené otázky a návrhy mimo rozsah:**
  - Návrh role repo v klasifikaci teď bere aktuální sektor protistrany i u zařazení s dřívějším datem; uložená role
    zařazení se tím nemění (počítá se jen při návrhu). Archiv odeslaných výkazů řeší etapa CN.
  - `docs/navrh-evidence-nastroju.md` a `docs/plan-dalsiho-vyvoje.md` ještě popisují verze profilu „platí od“
    (historické návrhy, neupravoval jsem je).
