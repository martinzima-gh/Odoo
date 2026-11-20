# Běh 0 – Sonnet 5.5 (úsilí medium): sloučení ZJ-13/14, REVOKE, zadání dávky

Soubory jsou v repozitáři v docs/ukoly/podklady/ (viz 00-prehled.md, Příprava).

```
Přečti CLAUDE.md a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen oddíl 0 (prompt), „Přednosti“, oddíl 1 a 12.
Dělej JEN krok 0 a krok 1 z oddílu 0, neprogramuj.
KROK 0: v ukol/ZJ-13-14 tools/run_tests.sh all; povýšení investra po AG-020–022, pokud ještě neproběhlo (záloha, upgrade
investra_instruments, investra_instrument_master, investra_nav, investra_derivative, restart investra-web, snímek ocenění 35 a 39 přes
docs/sql/28-snimek-oceneni.sql – ulož výstup do docs/predavky/snimek-35-39-pred-davkou.txt); merge do main „Sloučení ZJ-13, ZJ-14,
AG-019 až AG-022“, push. REVOKE CREATE ON SCHEMA public FROM PUBLIC do tools/db/dbeaver_ro_grants.sql, spusť, ověř (dbeaver_ro
nezaloží tabulku, Odoo funguje), řádek do deníku. Větev ukol/ZJ-07-dane-a-tridy z main.
KROK 1: commitni zadání a složku davka-ZJ-07-19 v docs/ukoly/podklady/. Založ/doplň zadání podle docs/ukoly/_sablona.md – Technický plán = odkaz na oddíl
souboru, NEkopíruj obsah: ZJ-09 (oddíl 2), ZJ-08 (3; bod 4 později), ZJ-17-ucetni-obdobi.md (4), ZJ-16-poplatek-obchodu.md (5),
ZJ-15-cena-vyskladneni.md (6), ZJ-19-dividendy-a-ex-kupon.md (7), ZJ-18-fvoci-do-oci.md (8), ZJ-07 (9). Deník docs/rozhodnuti.md:
D1–D14 z oddílu 1, odchylky C0.1–C0.8 (oddíl 9.2) a oddíl 12, každé jedním řádkem s odkazem na soubor. Otevřené body: z oddílu 0 ZÁVĚR.
Commit, push. Předávka docs/predavky/2026-11-xx-davka-beh-0.md. (V relaci 1 pokračuj rovnou během 1, zprávu napiš až na konci.)
Zastav se, když testy v ukol/ZJ-13-14 neprojdou nebo merge má konflikt.
```
