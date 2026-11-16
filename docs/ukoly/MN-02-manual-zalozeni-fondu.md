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

Provedl Claude (Sonnet 5.5), 16. 11. 2026. Jen dokumentace; kód ani databáze beze změny.

- **Změněné soubory:** `docs/manual/README.md`, `01-spolecnost-a-kniha.md`, `02-fond.md`, `03-tridy.md` (nové); tento soubor;
  `docs/predavky/2026-11-16-mn02-manual-kap-1-3.md`.
- **Ověřeno:** pouze čtením kódu a XML: `investra_entity` (entity.py, entity_views.xml), `investra_fund` (fund.py, fund_views.xml, access),
  `investra_chart_fund` (průvodce, Výsledek MN-01), `investra_nav` (launch_date, pohyby), `investra_instruments` (zámek
  Zaúčtování obchodu). Názvy polí, výchozí hodnoty a texty chyb jsou převzaté z `string=`, `default=` a `raise`. Každé pole
  formulářů Fondy a Třídy je popsané; vynechané je jen to, co ve formuláři není (Pořadí, Aktivní jsou uvedené s poznámkou).
- **Neověřeno:** vše v prohlížeči (štítek v každé kapitole). Zejména: přesné popisky polí ve formuláři knihy (automatický
  formulář, popisek **Název** bere Odoo z modelu společnosti), chování nového řádku třídy (viz nález 2), viditelnost nabídek
  pro uživatele bez správce, zda se po založení fondu opravdu vytvoří portfolio Hlavní a profil FX (z kódu `create`).
- **Nálezy pro pročištění:**
  1. **Pole Datum vzniku (`launch_date`, modul `investra_nav`) není v žádném formuláři.** Bez něj první ocenění skončí chybou
     „Fond nemá datum vzniku.“ (`valuation.py`). Uživatel ho v UI nezadá; je to blokující pro scénář od nuly.
  2. **Nový řádek třídy:** kontext formuláře fondu předává třídě výchozí kusy a poplatky, ale ne `price_digits` ani
     `price_rounding`. Desetinná místa kurzu jsou povinné celé číslo bez výchozí hodnoty (v klientu zřejmě 0) a zaokrouhlení
     kurzu je povinný skrytý sloupec; uložení řádku může selhat nebo založit třídu s 0 místy. Ověřit v prohlížeči, doplnit do kontextu.
  3. **Změna polí třídy po prvním pohybu se nehlídá** (měna zveřejnění kurzu, desetinná místa, poplatky, kód). Zadání čeká „co nejde změnit“,
     v kódu je jen zámek Zaúčtování obchodu ve fondu a ochrana zaúčtovaných pohybů.
  4. **Pole `price_digits` fondu je „Výchozí desetinná místa kurzu“ (4), ale třída nemá `default`;** výchozí se doplňuje jen v `create`
     (odtud nález 2). Totéž pole `Pořadí` a `Aktivní` v seznamu tříd chybí (archivace třídy z formuláře fondu není vidět).
  5. **Pole `Účetní kniha` ve formuláři fondu nemá doménu:** nabízí i knihy druhu Servisní společnost či Investiční společnost
     a chyba přijde až při uložení („Fond musí stát na knize fondu, podfondu nebo SICAV.“). Doména by nabídku zúžila.
  6. **Kniha nemá vlastní formulář** (automatický): bez nápověd u polí, bez poznámky, že funkční měna a rámec jsou po zaúčtování zamčené.
  7. **Nápovědy chybí** u polí `Kód`, `Název`, `ISIN`, `Rozdělování výnosu`, `Frekvence ocenění`, `Úročení nástrojů v naběhlé hodnotě`
     a u `Kalendáře ocenění`; ISIN se nekontroluje (formát, délka).
  8. **Nadřazená kniha** u fondu a SICAV nemá omezení druhu (převzato z MN-01); vazba fond → investiční společnost je jen pole Obhospodařovatel.
  9. **Nová společnost se v přepínači firem trvale nezapne** (MN-01); manuál to dává do kroku „Po založení“, uživatel to může přehlédnout.
  10. **Obsah záložky Zpřísnění matice** smí měnit jen schvalovatel ocenění, ne správce; manuál to uvádí, rozhodnout, zda to tak má být (kap. 4).
