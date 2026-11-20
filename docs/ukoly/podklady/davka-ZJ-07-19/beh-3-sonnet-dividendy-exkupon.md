# Běh 3 – Sonnet 5.5 (úsilí high): dividendy a ex-kupón (logika)

```
Přečti CLAUDE.md, předávku běhu 2 a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen „Přednosti“ a oddíl 7.
Větev ukol/ZJ-07-dane-a-tridy. Schváleno; návrhy nespuštěné – převezmi, uprav, otestuj, odchylky do Výsledku ZJ-19.
ROZSAH: H1 model investra.dividend (pole, výpočty, kontroly, oprávnění ir.model.access + pravidla společnosti jako u obchodu,
zaúčtování k ex-datu, výplata, storno, náhled zaúčtování jako HTML pole), nové analytiky pohledávek v šabloně + migrace chart_fund
+ profil kurzového přecenění; H2 ex_coupon_days, ex_date na toku, předvyplnění záporného naběhlého úroku, kontrola znaménka,
nárok na kupón u splátky k ex_date − 1; testy H1 (česká 10 000 / 15 %, rakouská 7 000 / 27,5 % / 10 %, USD s kurzovým rozdílem,
portfolio třídy B, storno) a test_ex_coupon.py.
Pro dividendu použij účty 714100/714200/714300, 681100, 681400 – pokud je šablona ještě nemá (přijdou v běhu 4), založ je TEĎ
přesně podle oddílu 9.3 C1 (čísla, názvy, další účty rolí) a běh 4 je jen převezme.
MIMO ROZSAH (Copilot v běhu 6): formuláře, seznam a nabídka Dividendy, tlačítko z nástroje, pole lhůty na formuláři nástroje, manuál.
Testy investra_instruments+, investra_nav+, investra_chart_fund+ a snímek 35/39 = beze změny. Dvakrát neprošlý test → commitni hotové,
popiš, skonči. Commit, push, předávka …-davka-beh-3.md se seznamem polí, akcí a modelů pro Copilota. V relaci 2 pokračuj rovnou během 4; zprávu napiš až na konci relace.
```
