# Prompt – jedna relace Sonnet 5.5 (úsilí medium)

```
Přiložené soubory nejdřív ulož beze změny do docs/ukoly/podklady/davka-ZJ-24-27/ (všechny do této složky, jména ponech) – to je jejich
jediné místo; dál je čti odtud. Pak přečti CLAUDE.md a docs/ukoly/podklady/davka-ZJ-24-27/00-prehled.md (oddíly „Interakce Martina“ a
„Příprava“ přeskoč). Dál čti JEN soubory, které jmenuje aktuální část; nic neprocházej celé.
Pracuj sám bez dotazů, části 1–4 za sebou. Do main NESLUČUJ, dokud nenapíšu „slučuj“.
Obecně: commit po krocích plánu (zpráva „ZJ-xx Kn: …“), push po každé části. Po každém kroku cílené testy z plánu; na konci části
tools/run_tests.sh <modul>+ a snímek ocenění 35/39 (tools/snimek_na_kopii.sh) – musí být shodný s výchozím. Výchozí snímek ulož na začátku
části 1 do docs/predavky/snimek-35-39-pred-ZJ-25.txt. Po každé části předávka docs/predavky/2026-11-xx-cast-N.md (max 20 řádků) a pokračuj.
ÚSPORA: (1) testy spouštěj se zkráceným výstupem `… 2>&1 | grep -E "FAIL|ERROR|Error|Traceback|Ran |OK|FAILED" | tail -40`; celý log jen
u konkrétní chyby a jen její úsek; (2) soubory nad 300 řádků nikdy nečti celé – jen úseky (`sed -n 'A,Bp'`) podle čísel řádků z podkladů nebo
po `grep -n`; (3) kód ani diff necituj do zpráv, jen soubory a commity; (4) po opravě opakuj jen padající testy, `<modul>+` a `all` jen na konci
části; (5) co je v předávce předchozí části, už znovu nezjišťuj; (6) při opravě testu nejdřív přečti jen padající metodu a fixture, kterou volá.
STOP a napiš mi jen když: testy neprojdou ani po 2 pokusech o opravu, snímek se liší, kontrola class_split nesedí, nebo kód odporuje plánu
ve výpočtu či účtování (nevymýšlej jiné řešení).

ČÁST 1 – podklad plan-ZJ-24-bod-15.md. Větev ukol/ZJ-24-hlasky-a-sazby: záloha DB, povýšení investra_nav, restart investra-web,
run_tests.sh all, snímek (výchozí). Commitni složku docs/ukoly/podklady/davka-ZJ-24-27/ (podklady i zadání); založ podle docs/ukoly/_sablona.md
docs/ukoly/ZJ-25-oceneni-kontroly-rozpad.md, docs/ukoly/ZJ-27-zarazeni-z-obchodu.md a docs/ukoly/ZJ-26-vzhled.md (Technický plán = odkaz
na soubory podkladů). Pak z této větve založ ukol/ZJ-24-bod-15 a proveď K1–K8 přesně podle plánu.

ČÁST 2 – ověř, že hlavička plan-ZJ-25-technicky.md obsahuje „Schválil Martin“ s datem; jinak STOP. Podklady plan-ZJ-25-technicky.md
a podklad-katalog-kontrol.md, k tomu zadani oddíl 1 (jen texty v 1.4). Z ukol/ZJ-24-bod-15 založ ukol/ZJ-25-oceneni-kontroly-rozpad.
Commity v pořadí oddílu H plánu, testy oddílu G. Katalog kontrol převezmi doslova do models/check_catalog.py.

ČÁST 3 – před začátkem mi napiš „Část 2 hotová. Přepni úsilí relace na high a napiš pokračuj.“ a čekej (jediné plánované čekání).
Pak ověř, že hlavička plan-ZJ-27-technicky.md obsahuje „Schválil Martin“ s datem; jinak STOP. Podklady plan-ZJ-27-technicky.md
a podklad-zj27-fakta.md (jen oddíly, na které plán odkazuje). Z ukol/ZJ-25-oceneni-kontroly-rozpad založ ukol/ZJ-27-zarazeni-z-obchodu.
Kroky v pořadí plánu včetně migrace a doplnění dat; obrazovky v této části jen funkčně (pole, viditelnost), vzhled dělá část 4.

ČÁST 4 – podklad podklad-zj26-obrazovky.md (oddíl „Změny po ZJ-27“ má přednost před ostatními oddíly), k tomu zadani oddíl 2
a docs/vzhled/zasady-obrazovek.md. Z ukol/ZJ-27-zarazeni-z-obchodu založ ukol/ZJ-26-vzhled. Rozhodnutí Martina jsou v podkladu v oddílu
Nejasnosti (rámeček nahoře). Pořadí: zásady → SCSS → obrazovky (každá commit; před a po spočítej pole ve formuláři – počet musí sedět
s podkladem) → ostatní formuláře → dialogy → zkrácení popisků. Po každé obrazovce povýšení dotčeného modulu bez chyby; na konci all a snímek.

KONEC: napiš mi max 15 řádků: větve a poslední commity, odchylky od plánů, testy, snímek, co agent doplnil v datech (ZJ-27) a seznam
ke kontrole v prohlížeči (ZJ-24 body 13/14/16/15, ruční úplaty na výnos; ZJ-25 obrazovky; ZJ-27 obchod → zařazení, cena v %;
ZJ-26 obrazovky + dialogy). Pak čekej.
Na „slučuj“: v main postupně merge (bez squash) ukol/ZJ-20-poznamky, ukol/ZJ-24-hlasky-a-sazby, ukol/ZJ-24-bod-15,
ukol/ZJ-25-oceneni-kontroly-rozpad, ukol/ZJ-27-zarazeni-z-obchodu, ukol/ZJ-26-vzhled; povýšení modulů, run_tests.sh all, snímek, push.
Předávka docs/predavky/…-slouceni.md.
```
