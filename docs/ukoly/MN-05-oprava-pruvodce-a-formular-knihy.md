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

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
