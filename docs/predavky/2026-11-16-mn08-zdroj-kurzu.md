# Předávka 2026-11-16: MN-08 zdroj kurzů „Neimplementováno“

- **Cíl:** funkční měna mimo CZK a EUR povolená se zdrojem kurzů „Neimplementováno“; kde je kurz potřeba, chyba místo
  tichého kurzu ČNB.
- **Stav:** větev `ukol/MN-manual`, commit „MN-08“ (poslední v historii větve); pushnuto do `origin ukol/MN-manual`.
- **Hotové:** plán 1–6; testy `all` 795/0 chyb na dočasné DB (smazána); moduly entity, rates, fx_revaluation, chart_fund,
  nav povýšeny v `investra` (záloha `zalohy/investra-2026-11-16-pred-MN08.dump`), 8071 restartována; manuál kap. 1.
- **Zbývá:** nic; Martin ověřil průvodce a formulář knihy v prohlížeči 16. 11. 2026.
- **Rozhodnutí:** žádné nové (provedení bodu 5a z 2026-11-16).
- **Otevřené:** ruční kurz pro knihu bez zdroje; nativní přepočet Odoo v knize mimo CZK/EUR (oba v `docs/otevrene-body.md`).
- **Číst:** `docs/ukoly/MN-08-zdroj-kurzu-neimplementovano.md`, `addons/custom/investra_entity/models/entity.py`,
  `docs/manual/01-spolecnost-a-kniha.md`.
