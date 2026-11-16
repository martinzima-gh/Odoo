# Předávka 2026-11-16: MN-07 fond, třídy, úklid

- **Cíl:** zámek tříd po prvním pohybu, ISIN, řazení/archivace, nápovědy, kód ESA podle druhu, IČO/DIČ a země v seedu, migrace `founder_id`.
- **Stav:** větev `ukol/MN-manual`, commit „MN-07“ (poslední v historii větve); pushnuto do `origin ukol/MN-manual`.
- **Hotové:** vše z plánu 1–9; testy `all` OK (kromě opraveného testu ISIN, po opravě `investra_fund` OK); seed ověřen na dočasné DB;
  moduly povýšeny v `investra` (záloha `zalohy/investra-2026-11-16-pred-MN07.dump`), 8071 restartována.
- **Zbývá:** Martin v prohlížeči ověří formulář fondu (úchyt, zamčená pole po pohybu, Aktivní, nápovědy). První krok: otevřít
  fond s úpisem a zkusit změnit kód třídy.
- **Rozhodnutí:** zapsáno v deníku (zámek tříd, ISIN, DIČ řady 99 bez kontroly formátu).
- **Otevřené:** vrácení archivované třídy z UI; ověření účinku frekvence ocenění a kalendáře pro nápovědy.
- **Číst:** `docs/ukoly/MN-07-fond-tridy-a-uklid.md`, `addons/custom/investra_nav/models/fund_class.py`,
  `docs/manual/03-tridy.md`.
