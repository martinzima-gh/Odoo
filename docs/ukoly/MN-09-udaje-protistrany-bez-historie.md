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

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
