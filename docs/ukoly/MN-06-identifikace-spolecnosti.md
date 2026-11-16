# MN-06 Identifikace společnosti: IČO, DIČ, LEI a ESA v průvodci a knize

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (průvodce, formuláře, odvození sektoru; `create_book` jen nový nepovinný parametr kontaktu; účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` |
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
3. **Historie profilu (pozn. 13):** model s platností zůstává (doporučení Clauda, viz Odpověď níže). Zjednodušit zadávání:
   Platí od výchozí dnes; drobečková navigace „Údaje protistrany – <kontakt> – od <datum>“, u nového záznamu „Nové údaje protistrany“.
4. **Průvodce Nová účetní kniha – skupina Identifikace (pozn. 10):** nepovinná pole IČO (`company_registry`, kontrola 8 číslic
   s kontrolní číslicí mod 11), DIČ (`vat`; u země Česko předvyplnit „CZ“ + IČO, lze přepsat), LEI, Kód sektoru ESA.
   Předvyplnění kódu podle druhu jednotky: fond, SICAV, podfond → rezidentský kód se sektorem „Fondy kolektivního investování
   (kromě FPT)“; investiční společnost → rezidentský kód se sektorem „Pomocné finanční instituce“; servisní → prázdné.
   Kódy vyhledat v číselníku, nevymýšlet; pokud jich odpovídá víc, nechat prázdné a uvést ve Výsledku. Je-li zadané LEI
   nebo kód, průvodce po založení vytvoří profil (platí od dne založení, země z průvodce). Pole profilu přidá do průvodce
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

**Odpověď na pozn. 13 (pro manuál a Martina):** údaje protistrany mají platnost od data, protože výkazy ČNB a ocenění se
vykazují k datu: když emitent nebo protistrana změní sektor, zemi nebo rezidentství, starší výkazy musí jít zopakovat se
starými údaji (deník 2026-11-15 „Evidence nástrojů – rozšíření místo paralelních modelů“, profil s potvrzením verze).
Vlastní fond je přitom také protistranou (např. když do něj investuje jiný náš fond), proto používá stejný profil.

**Rozsah souborů:** `investra_counterparty`, `investra_instrument_master` (profil, číselníky ESA, dědění průvodce), `investra_chart_fund`
(průvodce: kontakt, IČO, DIČ), `investra_entity` (jen parametr kontaktu v `create_book` a pole IČO/DIČ ve formuláři knihy),
jejich testy, verze, README; `docs/manual/01-spolecnost-a-kniha.md`; tento soubor (Výsledek), předávka.

**Mimo rozsah:** zrušení historie profilu; změna kontroly verzí profilu; fond a třídy (MN-07); kurzy (MN-08).

**Kritéria přijetí:** testy dotčených modulů a `all` bez selhání na `investra_ci_*`; Výsledek uvádí kódy ESA pro předvyplnění
a co zůstalo neověřené v prohlížeči.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
