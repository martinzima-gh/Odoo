# IM test report – evidence nástrojů

Převzato ze sekcí Výsledek v `docs/ukoly/IM-01` až `IM-07` (stav 15. 11. 2026). Testy běžely na dočasných databázích
`investra_ci_*` (smazány); na `investra_test` a `investra_vzhled` se modul nenainstaloval. Čísla jsem znovu nespouštěla.

| Úkol | Rozsah testů | Počet testů | Selhání / chyby | Poznámka |
|---|---|---|---|---|
| IM-01 číselníky | `investra_instrument_master` | 15 | 0 / 0 | |
| IM-02 import číselníků | `investra_instrument_master` | 79 (8 nových) | 0 / 0 | ERROR `null value … reason` v logu je očekávaný z IM-04 |
| IM-03 emitent | master + counterparty | 39 (14 nových) | 0 / 0 | |
| IM-04 nástroj | master + instruments + nav | 441 (16 nových) | 0 / 0 | ERROR „null value in column reason“ je očekávaný z testu |
| IM-05 SPPI na nástroji | všech 16 modulů `investra_*` | 625 | 0 / 0 | migrace ověřena na kopii `investra_test`: SPPI beze změny, 4 nástroje přeneseno |
| IM-06 portfolio | master, instruments, counterparty, nav, cnb | 482 → 483 po doplňku (podílový list vždy FVTPL) | 0 / 0 | `bad query` v logu je známá očekávaná chyba z IM-04 |
| IM-07 účetní profil | `investra_instrument_master` | 71 (12 nových) | 0 / 0 | |

Poslední stav modulu `investra_instrument_master`: 79 testů v modulu (IM-02, po IM-07), 483 v pětici modulů (IM-06 po doplňku);
po IM-07 a IM-02 širší sadu nikdo nespouštěl.

## Neověřeno

- Import skutečné nové verze metodiky a vzhled průvodce importu.
- Vzhled všech nových formulářů a seznamů v prohlížeči (jen načtení pohledů při instalaci).
- Instalace a upgrade v `investra_test` a `investra_vzhled`.
- Plná sada všech modulů po IM-07.
- IM-08: SELECTy z `docs/sql/23-evidence-nastroju.sql` proběhly bez chyby, ale na dočasné DB bez dat (jen seed číselníků),
  takže nevracejí řádky; správnost výsledků na datech není ověřena.
