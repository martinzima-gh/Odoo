# Předávka 2026-11-16: MN-01 – průvodce Nová účetní kniha

**Cíl:** založit společnost a účetní knihu v aplikaci stejně jako seed (`create_book`), podklad pro manuál MN-02.

**Stav:** větev `ukol/MN-manual`; commit „MN-01“ (viz `git log`), push na `origin/ukol/MN-manual`.

**Hotové**
- Průvodce `investra.new.book.wizard` v `investra_chart_fund` (20.0.0.10.0): Investra › Nastavení › Fondy › Nová účetní
  kniha a tlačítko v seznamu knih, jen správce; kontroly předem (rámec podle druhu, podfond pod SICAV, název, moduly).
- 9 nových testů, modul 21/21, celá sada viz Výsledek MN-01.
- `investra`: záloha `zalohy/investra-2026-11-16-pred-MN01.dump`, povýšení modulu, 8071 běží.

**Zbývá – první krok:** Martin projde průvodce v prohlížeči (seznam „Neověřeno“ ve Výsledku MN-01). Pak MN-02
(manuál kap. 1–3, Sonnet) podle `docs/ukoly/MN-02-manual-zalozeni-fondu.md`; kroky UI průvodce jsou ve Výsledku MN-01.

**Rozhodnutí:** žádné nové (plán MN-01 schválil Martin; upřesnění ve Výsledku).

**Otevřené otázky:** trvalá aktivace nové firmy v přepínači; měny mimo CZK/EUR; omezení nadřazené knihy u fondu a SICAV.

**Číst:** `CLAUDE.md`, `docs/ukoly/MN-01-pruvodce-nova-kniha.md` (Výsledek), `docs/ukoly/MN-02-manual-zalozeni-fondu.md`.
