# Předávka: MN-05a otevření formuláře po založení knihy

- **Cíl:** opravit pád klienta `action.views.map` po „Založit knihu“.
- **Stav:** větev `ukol/MN-manual`; oprava hotová, testy `investra_chart_fund` prošly (29/29), modul 20.0.0.12.1 povýšen v `investra`, 8071 restartována.
- **Hotové:** `views` v akci `form` průvodce, test struktury akce, záloha `zalohy/investra-2026-11-16-pred-MN05a.dump`.
- **Zbývá:** Martin v prohlížeči založí knihu a ověří, že se formulář otevře. První krok: Nastavení → Nová účetní kniha → Založit.
- **Rozhodnutí:** bez nových; ostatní `next` akce jsou klientské (`soft_reload`), chybu nemají.
- **Otevřené:** obecná kontrola `views` v `tools/view_check` jen navržena.
- **Číst:** docs/ukoly/MN-05a-pruvodce-otevreni-formulare.md, addons/custom/investra_chart_fund/wizard/new_book.py.

Prompt: „Přečti CLAUDE.md a docs/predavky/2026-11-16-mn05a-otevreni-formulare.md; pokračuj ověřením výsledku od Martina, poté MN-06.“
