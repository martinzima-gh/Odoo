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

**Zbývá:**

1. Martin ověří Přehled v prohlížeči (Cmd+Shift+R): souhrnný pás a přepínání filtru kliknutím, nový pás karty,
   „+N dalších“, prokliky. Nic z toho nebylo v prohlížeči ověřeno; pás je nová komponenta OWL podle vzoru z jádra.
2. Bod 11 (malý graf FK) – rozhodnout až po zhlédnutí karty.
3. Bod 14 (řazení tabulky podle počítaných sloupců) – neověřeno, zda klik na záhlaví řadí.
4. Body 15 (karta Investra Services) a 16 (likvidita, limity) – neotevřeno.
5. `docs/architektura.md` nebyl po doplnění řádku v Claude Doc znovu exportován.

**Otevřené otázky:** výjimky ze zámku čekající na potvrzení nejsou v bloku Ke zpracování (jen počet platných na kartě).

**Soubory ke čtení:** `addons/custom/investra_dashboard/models/dashboard.py`, `views/dashboard_views.xml`,
`static/src/fund_summary.js`, `docs/ukoly/AG-018-prehled-ovladani-karty.md`.
