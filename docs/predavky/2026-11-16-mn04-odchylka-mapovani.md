# Předávka 2026-11-16: MN-04 – odchylka mapování rolí

**Cíl:** v Účtech rolí je vidět a jde filtrovat odchylka fondu od standardu (rozhodnutí 2026-11-16, varianta A).

**Stav:** větev `ukol/MN-manual`, commit „MN-04“ (viz `git log`), push na origin. `investra_chart_fund` 20.0.0.11.0 povýšen
v `investra` (záloha `zalohy/investra-2026-11-16-pred-mn04.dump`), 8071 restartováno.

**Hotové:** pole Standard a Standardní účet, filtry, zvýraznění; `_apply_standard_role(code, old_xmlid)` pro budoucí
migrace; 5 testů (26 OK v modulu); manuál kap. 1 doplněna; v `investra` 345 řádků podle standardu, 0 odchylek.

**Zbývá – první krok:** Martin v prohlížeči ověří Investra › Nastavení › Účtování › Účty rolí (sloupce, filtr, zvýraznění);
pak nálezy MN-02 č. 3–10 a kap. 4–8 manuálu.

**Rozhodnutí:** žádné nové; odchylky od plánu (bez seskupení, parametr old_xmlid) jsou ve Výsledku úkolu.

**Otevřené otázky:** žádné.

**Číst:** `CLAUDE.md`, `docs/ukoly/MN-04-odchylka-mapovani-roli.md` (Výsledek), `docs/ukoly/MN-02-manual-zalozeni-fondu.md`.
