# Předávka 2026-11-15: vylepšení Přehledu fondů

**Cíl:** vylepšit stránku Přehled (modul `investra_dashboard`) podle seznamu návrhů A–D z 15. 11. 2026.

**Stav:** větev `etapa/derivaty`, poslední commit této práce „Přehled fondů: úpisy − odkupy, uzávěrka a souhrnný pás“
(+ commit s touto předávkou), pushnuto na origin. Modul 0.5.0 je povýšený v pracovní databázi `investra` (8071),
záloha před povýšením `zalohy/investra-2026-11-15-pred-prehled-05.dump`.

**Hotovo:**

- A (AG-018, Copilot, převzato): prokliky na fond, kontroly a termíny ČNB, seznam kontrol, čtyři filtry, sloupec Můj krok.
- A3: sbalení bloku Ke zpracování („+N dalších“), řazení můj krok → varování → postup.
- 12: „můj krok“ podle schvalovací matice (schválení a zveřejnění ocenění, ceny, žádosti).
- 13: počty ocenění a zůstatky souhrnným dotazem (5 fondů: 238 dotazů, 43 ms; srovnání s dřívějškem neměřeno).
- 8, 9: nástroje bez aktuální ceny k ocenění; informativní výhled na 7 dnů.
- 6, 7, 10: souhrnný pás nad kartami, úpisy − odkupy za období, uzávěrka a platné výjimky ze zámku.
- Testy `tools/run_tests.sh investra_dashboard`: 29 testů, 0 chyb. Rozhodnutí v deníku (4 řádky) a v Claude Doc (1 řádek).

**Zbývá:** nic. Martin Přehled v prohlížeči viděl (souhrnný pás funguje); nález „jde kliknout na kartu s nulou“
opraven (karta s počtem 0 je vypnutá). Graf FK, řazení tabulky, karta Investra Services, likvidita a limity jsou
odložené jako poznámky v `docs/otevrene-body.md` („Přehled fondů – možná vylepšení“); otevřít jen na Martinův pokyn.
`docs/architektura.md` nebyl po doplnění řádku v Claude Doc znovu exportován. Sloučení do `main` jen na Martinovu výzvu.

**Doplněno 16. 11. 2026:** karta zhuštěna, odkaz „Otevřít ocenění“ odstraněn, kontroly jen u nezveřejněného ocenění
(modul 0.5.1, povýšeno v `investra`, 30 testů bez chyb; vzhled Martin potvrdil 16. 11. 2026). Do plánu
(`docs/plan-dalsiho-vyvoje.md`, Nezařazené úkoly) přibyly PO-01 (kusy v podrozvaze), DA-01 (daně) a OZ-01 až OZ-03
(oprava zveřejněného ocenění, návrh `docs/navrh-oprava-zverejneneho-oceneni.md` čeká na rozhodnutí).
První krok příště: Martin řekne, zda sloučit `etapa/derivaty` do `main`.

**Soubory ke čtení:** `addons/custom/investra_dashboard/models/dashboard.py`, `views/dashboard_views.xml`,
`static/src/fund_summary.js`, `docs/ukoly/AG-018-prehled-ovladani-karty.md`.
