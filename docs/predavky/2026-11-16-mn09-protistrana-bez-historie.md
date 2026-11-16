# Předávka: MN-09 údaje protistrany bez historie

- **Cíl:** jeden záznam údajů protistrany na kontakt, bez „Platí od“; změny v historii záznamu (rozhodnutí 2026-11-16).
- **Stav:** větev `ukol/MN-manual`; testy `all` 757/757, `investra_counterparty` 20.0.0.4.0 a `investra_instrument_master`
  20.0.0.7.0 povýšeny v `investra` (záloha `zalohy/investra-2026-11-16-pred-MN09.dump`), 8071 restartována.
- **Hotové:** omezení `unique(partner_id)`, zrušené `valid_from` a `is_latest` (sloupce odstraněny), `_counterparty_profile(day)`
  a `_issuer_profile(day)` datum ignorují; změna potvrzených údajů vyžaduje důvod a vrací stav na Ke kontrole; tlačítko
  v knize otevře jediný záznam; migrace slučující duplicity (zkoušená na kopii); seed, SQL příklady, manuál kap. 1.
- **Zbývá:** Martin ověří v prohlížeči. První krok: Nastavení → knihy → kniha → tlačítko Údaje protistrany; změnit
  sektor potvrzeného záznamu bez důvodu (chyba) a s důvodem (stav Ke kontrole, změna v historii).
- **Rozhodnutí:** bez nových; doporučení ponechat samostatný model 1:1 (provedeno) je ve Výsledku MN-09.
- **Otevřené:** návrh role repo bere aktuální sektor i u starších zařazení; `docs/navrh-evidence-nastroju.md` a plán
  ještě zmiňují verze profilu; archiv výkazů ČNB v etapě CN.
- **Číst:** docs/ukoly/MN-09-udaje-protistrany-bez-historie.md, addons/custom/investra_instrument_master/models/issuer.py.

Prompt: „Přečti CLAUDE.md a docs/predavky/2026-11-16-mn09-protistrana-bez-historie.md; pokračuj ověřením výsledku od Martina, poté MN-06.“
