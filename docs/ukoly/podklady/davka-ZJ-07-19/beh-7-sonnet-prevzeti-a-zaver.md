# Běh 7 – Sonnet 5.5 (úsilí high): převzetí Copilota, XLS, nasazení, závěr

```
Přečti CLAUDE.md, předávky běhů 1–5, docs/ukoly/CP-2026-11-xx-ZJ-07-19-formulare.md a v docs/ukoly/podklady/
zadani-davka-ZJ-07-az-19.md jen oddíl 0 (ZÁVĚR), 9.2 C4 (XLS) a oddíl 11.
1. Převzetí Copilota: diff cp/ZJ-07-19-formulare proti ukol/ZJ-07-dane-a-tridy – jen XML, manifesty, docs; žádný Python ani pole navíc
   (jinak vrať). Zkontroluj body 1–8 jeho zadání proti polím z předávek, české popisky, invisible podmínky; drobnosti oprav sám,
   chybějící pole doplň jen když jde o čistě zobrazovací computed pole, jinak zapiš do otevřených bodů. Merge do ukol větve.
2. XLS pro depozitáře: list „Daň“ ze snímku detailu daně (package.py, vzor ostatních listů); sloupec OCI na listu portfolio.
3. ZÁVĚR podle oddílu 0: tools/run_tests.sh all, migrace zkouškou na kopii investra, povýšení investra se zálohou (moduly podle oddílu 11),
   restart investra-web, snímek 35/39 před a po (porovnej se souborem z běhu 0 – stejný), Výsledek do ZJ-07, 08, 09, 15, 16, 17, 18, 19
   (z předávek běhů), otevřené body, předávka …-davka-beh-7.md, push.
Neopravuj výpočty (daň, FVOCI, třídy) – když test nebo snímek nesedí, zastav se a napiš mi, který test a čísla.
Na konci mi napiš krátce: co šlo ven, odchylky ze všech běhů, výsledky testů, snímek a seznam ke kontrole v prohlížeči z oddílu 0.
```
