# MN-02 Manuál: založení společnosti, fondu a tříd (kapitoly 1–3)

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen dokumentace v `docs/manual/`) |
| Výchozí větev | `ukol/MN-manual` (po MN-01) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-01 (průvodce Nová účetní kniha), rozhodnutí Martina 16. 11. 2026 (manuál v markdownu po kapitolách) |

**Cíl:** první kapitoly uživatelského manuálu aplikace. Podle nich Martin v `investra` (8071) založí od začátku novou
investiční společnost a fond s více třídami. Co při tom nebude fungovat nebo bude matoucí, se opraví samostatnými úkoly.

**Výstup:**

- `docs/manual/README.md`: účel, čtenář (účetní a administrátor fondu, zná účetnictví, nezná Odoo), konvence, osnova
  celého manuálu se stavem kapitol (hotovo / koncept / plán). Plánované kapitoly: 4 kalendář ocenění a schvalovací
  matice, 5 uživatelé a role, 6 portfolia a nástroje, 7 kurzy, 8 první úpis nebo převzetí fondu.
- `docs/manual/01-spolecnost-a-kniha.md`: investiční společnost (obhospodařovatel) a kniha fondu přes průvodce z MN-01;
  co nejde později změnit (funkční měna, rámec), kde je vidět osnova a role účtů.
- `docs/manual/02-fond.md`: formulář Fondy (`investra_fund/models/fund.py`, `views/`): obhospodařovatel, frekvence
  ocenění, datum zahájení, výchozí zaokrouhlení kurzu a kusů, rozdíl ze zaokrouhlení, poplatky a jejich příjemci.
- `docs/manual/03-tridy.md`: třídy fondu na smyšleném příkladu se třemi třídami (např. A retailová CZK, B EUR,
  I institucionální CZK s jinými poplatky); co třída dědí z fondu a co přepisuje; měna třídy = měna kurzu (deník
  rozhodnutí); co nejde po prvním pohybu změnit.

**Formát kroku:** cesta v nabídce (Investra › Nastavení › Fondy › …), pole s významem a výchozí hodnotou, povinná pole,
co hlídá kontrola (text chyby z kódu), co nejde po zaúčtování nebo prvním pohybu změnit. U každé kapitoly štítek
„Ověřeno v kódu, v prohlížeči neověřeno“; ověření doplní Martin při průchodu. Obrázky zatím ne.

**Zdroje (číst cíleně, grep):** `investra_entity` a `investra_fund` (models, views, nápovědy `help=`), `investra_chart_fund`
(Výsledek MN-01), `tools/demo_data/seed.py` (pořadí kroků), `docs/rozhodnuti.md` (jen hesla funkční měna, třída, poplatek,
zaokrouhlení). Názvy polí a nabídek přebírat přesně z XML a `string=`, nevymýšlet.

**Pravidla:** česky, stručně, bez vysvětlování účetních základů. Smyšlená jména. Bez textu z důvěrných dokumentů,
bez obchodního názvu IS. Zjištěné nesrovnalosti v aplikaci (chybějící nápověda, matoucí pole, chyba) neopravovat,
jen zapsat do Výsledku jako seznam pro pročištění.

**Rozsah souborů:** `docs/manual/`, tento soubor (Výsledek), předávka. Kód ani databázi neměnit.

**Kritéria přijetí:** tři kapitoly a README; každé pole z formulářů fondu a třídy je popsané nebo výslovně vynechané
s důvodem; seznam nálezů pro pročištění ve Výsledku.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:**
- **Ověřeno:**
- **Neověřeno:**
- **Nálezy pro pročištění:**
