# MN-05 Oprava průvodce Nová účetní kniha a formulář knihy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (průvodce, formuláře, zrušení pole; `create_book` jen přidání `with_company`, osnova a účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | Martinovy poznámky z průchodu zakládání 16. 11. 2026 (1, 2, 3, 4, 6) a nálezy MN-02 5, 6, 8, 9; rozhodnutí v `docs/rozhodnuti.md` ze 16. 11. 2026 („Poznámky ze zakládání fondu“) |

**1. Chyba průvodce (blokuje, Martin v prohlížeči):** „Chyba přístupu – Administrator nemá přístup pro ‚vytvořit‘ k Účetní kniha
(investra.entity), company = nová společnost. Blame: Knihy podle společnosti.“ Databáze po chybě čistá (ověřeno SELECTem).
Příčina: `investra.entity.create_book` (`investra_entity/models/entity.py`) zakládá knihu v prostředí, jehož
`allowed_company_ids` posílá prohlížeč a novou společnost neobsahuje. Oprava: knihu vytvořit přes `self.with_company(company)`
(stejně případné navazující zápisy v `investra_chart_fund`, např. `_map_fund_roles`, pokud by narazily). Test musí napodobit
prohlížeč: průvodce spustit s kontextem `allowed_company_ids=[aktuální firma]` a uživatelem, který má víc firem; ověřit, že
test bez opravy selže. Seed volá `create_book` také – po opravě musí dál fungovat (spustit jeho test, pokud existuje, jinak
popsat ve Výsledku).

**2. Nabídka:** odebrat položku nabídky „Nová účetní kniha“ (`investra_chart_fund/wizard/new_book_views.xml`, `menu_new_book`);
tlačítko v seznamu Účetní knihy zůstává.

**3. Zakladatel – zrušit** (rozhodnutí Martina): pole `founder_id` z `investra.entity`, průvodce, vyhledávání a manuálu.
V `investra` ověřit SELECTem, že není vyplněné; sloupec zůstane v databázi (Odoo ho při upgradu nemaže), ve Výsledku uvést.

**4. DIČ místo TIN:** zjistit, odkud popisek TIN pochází (pravděpodobně `res.country.vat_label` u Česka nebo překlad
pole `vat`), a nastavit „DIČ“ nejmenším zásahem v našem modulu (bez úpravy core). Zkontrolovat i popisek IČO
(`company_registry`). Jen popisky, data beze změny.

**5. Vlastní formulář knihy** (`investra_entity/views/entity_views.xml`, dnes jen seznam a vyhledávání):
- skupiny Společnost (název, druh, rámec, nadřazená kniha) a Měna a kurzy (funkční měna, zdroj kurzů);
- upozornění: funkční měnu, rámec ani společnost nejde po prvním zaúčtování změnit (stejný text jako průvodce);
- informace pod zdrojem kurzů: „Výkazy ČNB se vždy přepočítávají kurzem ČNB.“ (jen text, žádná logika);
- nápovědy (`help=`) u druhu, rámce, nadřazené knihy a zdroje kurzů;
- Nadřazená kniha (nález MN-02 8): ve formuláři i průvodci viditelná a povinná jen u podfondu, nabízí jen SICAV; u ostatních skrytá.

**6. LEI a sektor fondu** (rozhodnutí Martina: LEI přes kontakt společnosti): LEI se eviduje v údajích protistrany
(`investra.counterparty.profile`, platí od data, povinná země a sektor ESA, kontrola ISO 17442). V `investra_counterparty`
zdědit formulář knihy: jen pro čtení aktuální LEI a sektor ESA kontaktu společnosti (profil platný k dnešku) a tlačítko
„Údaje protistrany“, které otevře profily kontaktu společnosti s předvyplněným kontaktem a zemí. Model profilu neměnit.
LEI u podfondu nepovinné. V seznamu knih volitelný sloupec LEI.

**7. Fond (nález MN-02 5):** pole Účetní kniha ve formuláři fondu nabízí jen knihy druhu fond, podfond a SICAV (doména).

**8. Po založení (nález MN-02 9):** průvodce po založení zobrazí hlášku „Zapněte novou společnost v přepínači firem“
(přepínač si pamatuje prohlížeč, server ho trvale nezapne).

**9. Testy:** bod 1 (viz výše), zrušené pole, doména fondu, viditelnost a povinnost nadřazené knihy, LEI a sektor na knize
z profilu, popisek DIČ (pokud jde otestovat). `tools/run_tests.sh` pro dotčené moduly a nakonec `all`.

**10. Nasazení:** povýšení dotčených modulů v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071.

**11. Manuál:** `docs/manual/01-spolecnost-a-kniha.md` (průvodce jen z tlačítka, bez zakladatele, formulář knihy, LEI,
hláška o přepínači), `02-fond.md` (doména knihy); štítek „v prohlížeči neověřeno“ ponechat.

**Rozsah souborů:** `investra_entity`, `investra_chart_fund`, `investra_counterparty`, `investra_fund` (jen doména v pohledu),
jejich testy, verze, README; `docs/manual/01-*.md`, `02-*.md`; tento soubor (Výsledek), předávka.

**Mimo rozsah:** zdroj kurzů „Neimplementováno“ pro jiné měny (MN-07), zámky a nápovědy tříd (MN-06), logika kurzů pro ČNB
(etapa CN), změna modelu profilu protistrany, osnova a účtování.

**Kritéria přijetí:** test chyby z bodu 1 bez opravy selže a s opravou projde; testy dotčených modulů i `all` bez selhání na
`investra_ci_*`; v `investra` průvodce založí knihu (ověřit nanečisto v `odoo shell` s kontextem prohlížeče a rollbackem,
v `investra` nic nezakládat); Výsledek uvádí, co zůstalo neověřené v prohlížeči.

## Výsledek

Provedeno 16. 11. 2026 (Claude Code, Sonnet 5.5).

- **Změněné soubory:** `investra_entity` (`models/entity.py`: `create_book` přes `with_company`, zrušené `founder_id`, doména a nápověda
  nadřazené knihy, nápovědy druhu, rámce a zdroje kurzů; `views/entity_views.xml`: nový formulář, vyhledávání bez zakladatele; verze 0.10.0),
  `investra_chart_fund` (průvodce bez zakladatele, nadřazená kniha jen u podfondu s doménou SICAV, hláška po založení; zrušená položka nabídky;
  README, verze 0.12.0, testy), `investra_counterparty` (na knize LEI a sektor ESA z profilu kontaktu společnosti, tlačítko Údaje protistrany,
  volitelný sloupec LEI; verze 0.3.0, test), `investra_fund` (doména pole Účetní kniha ve formuláři, verze 0.8.3, test),
  manuál `01-spolecnost-a-kniha.md`, `02-fond.md`, tento soubor, předávka.
- **Ověřeno:** test „prohlížeč s kontextem `allowed_company_ids` bez nové společnosti, uživatel s více firmami“ **bez opravy selže**
  (`AccessError`: Administrator nemá přístup pro vytvořit k Účetní kniha, „Průvodce prohlížeč“) a s opravou projde. Testy dotčených modulů
  62 OK; `tools/run_tests.sh all` 755 testů, 0 selhání, 0 chyb; dočasné `investra_ci_*` smazány (0 zbývá). Seed volá `create_book` stejně
  (jen se změnil kontext prostředí); jeho testy (`investra_entity`, `investra_nav`, `investra_posting` a další) prošly. Záloha
  `zalohy/investra-2026-11-16-pred-MN05.dump` (čitelný `pg_restore -l`), povýšeny `investra_entity`, `investra_chart_fund`,
  `investra_counterparty`, `investra_fund` v `investra` (verze v DB potvrzeny, formulář a seznam existují, nabídka `menu_new_book`
  a pole `founder_id` v `ir.model.fields` už ne), 8071 restartováno (HTTP 200). `founder_id` v `investra`: 0 vyplněných; sloupec
  `investra_entity.founder_id` v databázi zůstává (Odoo sloupec při upgradu nemaže), je prázdný a nepoužitý.
- **Bod 4 (DIČ):** popisek TIN nepochází z našeho modulu ani z překladu pole `vat`. Odoo bere popisek z `vat_label` země **aktivní firmy**
  (`res.partner`: `self.env.company.country_id.vat_label`). Výchozí firma Odoo „My Company“ (id 1) má zemi USA (`vat_label` TIN);
  všechny naše společnosti mají Česko (cs_CZ „DIČ“, en_US „VAT“). Kód jsem neměnil. Řešení je datové: nastavit u „My Company“ zemi Česko
  (rozhodne Martin; nedělal jsem to). V anglickém rozhraní bude u české firmy popisek VAT. Popisek IČO (`company_registry`) jsem neřešil
  zvlášť: nenašel jsem pro něj úpravu v kódu ani důvod k ní. Test popisku nejde smysluplně napsat bez změny dat.
- **Neověřeno:** vzhled a chování v prohlížeči (formulář knihy, skrytí nadřazené knihy, hláška po založení, tlačítko Údaje protistrany,
  nabídka pryč). Nanečisto v `odoo shell` v `investra` jsem nezakládal: `create_book` může potvrdit transakci, a rollback by tedy nebyl
  zaručen; průvodce v kontextu prohlížeče pokrývá test na dočasné databázi. Popisek IČO.
- **Odchylky od zadání:** hláška po založení je `display_notification` s následnou akcí na formulář (průvodce proto vrací jinou strukturu,
  testy upraveny). Sektor ESA je ve formuláři uveden vedle LEI (zadání: „aktuální LEI a sektor“). Doména fondu je jen v pohledu, jak ukládá zadání.
- **Otevřené otázky a návrhy mimo rozsah:** (1) Nastavit zemi Česko u „My Company“ (id 1)? (2) Prázdný sloupec `founder_id` lze po
  schválení odstranit migrací (změna schématu, nedělal jsem). (3) Po MN-05 ve formuláři knihy zbývá nechat Martina projít v prohlížeči
  zakládání SICAV a podfondu.
