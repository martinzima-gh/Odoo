# MN-16 Manuál kap. 6 a 7: portfolia a nástroje, kurzy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `docs/manual/`) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | bez větve; zápis do `~/odoo-review`, bez commitu |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-15 (stejný formát), osnova `docs/manual/README.md` (kap. 6 a 7) |

**Cíl:** `docs/manual/06-portfolia-a-nastroje.md` (portfolio fondu, instrumenty, vazba na kmenová data) a `docs/manual/07-kurzy.md` (zdroje kurzů, ruční kurz, chování „Neimplementováno“ podle rozhodnutí MN-08 v deníku).

**Zdroje (číst cíleně):** `investra_instruments`, `investra_instrument_master`, `investra_rates` (models, views, security), `docs/rozhodnuti.md` (hesla kurzy, zdroj kurzů, MN-08), seed `tools/demo_data/seed.py`.

**Formát a pravidla:** stejné jako MN-15. Kap. 7 nesmí slibovat zdroje, které nejsou implementované.

**Rozsah souborů:** dva soubory kapitol, dva řádky v `docs/manual/README.md`, sekce Výsledek. Kód neměnit.

**Kritéria přijetí:** každé pole formulářů instrumentu a kurzu popsané nebo vynechané s důvodem; nálezy ve Výsledku.

## Výsledek

- **Hotovo:** vytvořeny kapitoly [06-portfolia-a-nastroje.md](../manual/06-portfolia-a-nastroje.md) a [07-kurzy.md](../manual/07-kurzy.md); řádky 6 a 7 v osnově [README.md](../manual/README.md) mají stav „koncept“.
- Kapitola 6 popisuje formuláře portfolia, zařazení nástroje, nástroj a jeho rozšířená kmenová data, včetně podmíněných, odvozených a systémových polí, peněžních toků a proměnné sazby.
- Kapitola 7 popisuje evidenci kurzů, ruční kurz/přepis a platnost; pro funkční měny mimo CZK a EUR výslovně uvádí „Neimplementováno“.
- **Nálezy / neověřeno:** názvy a chování polí byly ověřeny v kódu. Zobrazení a cesty nabídek nebylo možné ověřit v prohlížeči; obě kapitoly nesou příslušný štítek. Účetní politiku ani vhodnost konkrétní klasifikace manuál nepředpokládá.
- **Testy:** Odoo testy ani databázové operace nebyly provedeny; šlo o dokumentační změnu.

## Převzetí

Claude 17. 11. 2026: zóna zelená. Namátkou ověřeno: cesty nabídek (Obchodní modely, Nástroje, Kurzy měn, Platnost kurzů) existují v XML; kap. 7 odpovídá rozhodnutí MN-08. Kap. 6 jen vzorkem, ne celá pole po poli.
