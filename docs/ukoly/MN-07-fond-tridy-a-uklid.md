# MN-07 Fond a třídy: zámky, pořadí, nápovědy, ISIN; úklid po MN-05

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (zámky polí třídy, migrace odstraní prázdný sloupec; účtování beze změny) |
| Výchozí větev | `ukol/MN-manual` (po MN-06) |
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
7. **Testy:** zámek třídy (před a po prvním pohybu, poplatek jde změnit i po pohybu), kontrola ISIN (platný, neplatná
   číslice, špatný formát), seed na čisté databázi nastaví zemi My Company.
8. **Nasazení:** povýšení dotčených modulů v `investra` se zálohou do `zalohy/`, restart 8071.
9. **Manuál:** `02-fond.md`, `03-tridy.md` (co nejde po prvním pohybu změnit, ISIN, řazení a archivace tříd).

**Rozsah souborů:** `investra_fund`, `investra_nav` (jen zámek třídy, pokud tam patří zjištění pohybu), `investra_entity` (migrace),
`tools/demo_data/seed.py` (jen země My Company), testy, verze, `docs/manual/02-*.md`, `03-*.md`, tento soubor, předávka.

**Mimo rozsah:** změna poplatků v čase s platností od data; kontrola ISIN u nástrojů; identifikace (MN-06); kurzy (MN-08).

**Kritéria přijetí:** testy dotčených modulů a `all` bez selhání na `investra_ci_*`; v `investra` sloupec `founder_id` neexistuje
a My Company má Česko; Výsledek uvádí, co zůstalo neověřené v prohlížeči.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**
