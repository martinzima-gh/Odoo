# MN-17 Matice: odlišit řádky z modulu a záložka Zpřísnění matice

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen `addons/custom/investra_fund/views/*.xml`) |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | bez větve; zápis do `~/odoo-review`, bez commitu |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | nálezy MN-13 č. 6 a 7 |

**Cíl:** (6) v seznamu a formuláři řádků schvalovací matice je poznat, který řádek je výchozí z modulu a který vlastní; (7) záložka fondu „Zpřísnění matice“ je z pohledu uživatele srozumitelná (popisek, co ukazuje a kde se zpřísnění zadává).

**Smí:** jen pohledy XML v `investra_fund/views/`; pole `builtin` už existuje (nové pole se nezakládá, Python se nemění). Např. sloupec/štítek „Výchozí (modul)“ v seznamu, `readonly` ve formuláři, nápověda. Když to bez nového pole nejde, zastavit a napsat návrh.

**Mimo rozsah:** práva (`security/`) a změna toho, kdo řádky smí měnit (to je MN-18); logika matice.

**Kritéria přijetí:** `tools/view_check` projde; popis změn s názvy polí; v prohlížeči (8072) ověřeno, co šlo, zbytek označen „neověřeno“.

## Výsledek

- **Hotovo:** v seznamu a formuláři řádku matice je vidět pole `builtin` jako „Výchozí (modul)“ / „Výchozí řádek (z modulu)“; pole je ve formuláři jen pro čtení a je doplněno vysvětlení rozdílu mezi řádkem z modulu a vlastním řádkem.
- Na záložce fondu „Zpřísnění matice“ je popis, že obsahuje fondové řádky (nikoli výchozí či obhospodařovatele), kde řádek založit a že fondové pravidlo může základní pravidlo pouze zpřísnit. Oprávnění a způsob editace řádků se neměnily.
- **Změněné soubory:** `addons/custom/investra_fund/views/approval_matrix_views.xml`, `addons/custom/investra_fund/views/fund_views.xml`.
- **Ověřeno:** `python3 tools/view_check/check_views.py addons/custom/investra_fund/views/approval_matrix_views.xml addons/custom/investra_fund/views/fund_views.xml` — 2 soubory, 0 chyb; `git diff --check` — bez chyb.
- **Neověřeno:** prohlížeč na portu 8072 nebyl dostupný, proto nebyl ověřen vzhled ani skutečné texty po načtení Odoo. Služba nebyla spuštěna ani restartována; modul ani databáze nebyly měněny.

## Převzetí

Claude 17. 11. 2026: zóna zelená (jen views XML, `builtin` existuje v modelu, Python beze změny); `check_views.py` 0 chyb. Nasazeno 17. 11. 2026 se souhlasem Martina: záloha `zalohy/investra-2026-11-17-pred-MN17.dump`, `-u investra_fund` bez chyby, 8071 restartována (HTTP 200, bez ERROR), pohled v databázi ověřen SELECTem. Vzhled v prohlížeči neověřen.
