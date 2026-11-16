# Předávka 2026-11-16: MN-05 – oprava průvodce a formulář knihy

**Cíl:** průvodce Nová účetní kniha zakládá knihu i v prohlížeči (chyba přístupu), vlastní formulář knihy, LEI z profilu protistrany.

**Stav:** větev `ukol/MN-manual`, commit „MN-05“ (viz `git log`), push na origin. Povýšeny `investra_entity` 0.10.0, `investra_chart_fund` 0.12.0,
`investra_counterparty` 0.3.0, `investra_fund` 0.8.3 v `investra` (záloha `zalohy/investra-2026-11-16-pred-MN05.dump`), 8071 restartováno.

**Hotové:** body 1–3, 5–9 a 11 zadání; test chyby bez opravy selže; `all` 755 OK; manuál kap. 1 a 2. Bod 4 (DIČ): příčinou je země USA
u výchozí firmy „My Company“, kód beze změny.

**Zbývá – první krok:** Martin v prohlížeči projde založení SICAV a podfondu a formulář knihy; rozhodne o zemi u „My Company“.
Pak MN-06 (zámky a nápovědy tříd) a MN-07 (zdroj kurzů „Neimplementováno“).

**Rozhodnutí:** žádné nové.

**Otevřené otázky:** země u „My Company“ (id 1); případné odstranění prázdného sloupce `founder_id` migrací.

**Číst:** `CLAUDE.md`, `docs/ukoly/MN-05-oprava-pruvodce-a-formular-knihy.md` (Výsledek), `docs/manual/01-spolecnost-a-kniha.md`.
