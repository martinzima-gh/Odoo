# ZJ-04 Nasazení zjednodušení do `investra` a manuál

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (nové založení `investra` se souhlasem), zelená (manuál) |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-03) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Sonnet (nasazení), manuál Haiku nebo Sonnet |

**Změna 17. 11. 2026 (Martin): místo upgradu se `investra` založí znovu čistá z ukázkového skriptu (varianta B).**
V `investra` jsou jen ukázková data ze 16. 11. a ruční zkoušky Martina ze 17. 11., které si zadá znovu. Migrace ZJ-01 až
ZJ-03 jsou ověřené na kopii (ZJ-03, Výsledek). Smazání `investra` je nevratné: **jen se souhlasem Martina v promptu**
a jen po ověřené záloze.

**Postup:**
1. **Zkouška nanečisto:** `tools/demo_data/run_seed.sh investra_ci_zj04` (založí dočasnou databázi se všemi moduly).
   Log bez ERROR (řádky `ERROR/3` z popisů modulů nejsou chyba). SELECTem ověřit: 6 fondů, ocenění, obchody, pohyby,
   role Admin, Účetní, Schvalovatel, Náhled, uživatelé `admin`, `ucetni`, `schvalovatel`, `view` se skupinami podle
   Výsledku ZJ-02, řádky matice „jeden člověk“. Pak dočasnou databázi smazat (`odoo db drop`, i s filestore).
   Selže-li cokoli, zastavit a hlásit; `investra` se nemění.
2. `.env` existuje, **nečíst ho**; jen `grep -c '^INVESTRA_DEMO_USER_PASSWORD=' .env` (bez ní seed uživatelů skončí chybou).
3. **Záloha:** `pg_dump -Fc investra` do `zalohy/investra-2026-11-17-pred-ZJ.dump`; ověřit `pg_restore -l` (počet položek)
   a velikost. Bez ověřené zálohy dál nepokračovat.
4. `docker stop investra-web && docker rm investra-web`; smazat `investra` přes `odoo db drop` (i filestore; postup jako
   úklid v `tools/run_tests.sh`, heslo jen z proměnných kontejneru). Docker volumes nemazat.
5. `tools/demo_data/run_seed.sh investra`; log bez ERROR; stejné SELECTy jako v kroku 1.
6. Spustit `investra-web` příkazem z README (8071) a ověřit odpověď `/web/login`.
7. Uživatel `admin` má po založení výchozí heslo Odoo: říct Martinovi, ať si ho hned změní. Heslo agent nenastavuje
   ani nevypisuje. Hesla ukázkových uživatelů jsou z `.env`.
8. SELECT do `docs/sql/`: role, jejich činnosti a uživatelé; řádky matice; ručně doložené úplaty ocenění.
9. Manuál: kap. 4 (matice bez fondů a jmenovitých uživatelů), kap. 5 (role a činnosti, ukázkoví uživatelé bez hesla),
   kap. 2 (záložka Úplaty, bez zpřísnění matice a fondových vstupních poplatků), kap. 3 (vstupní a výstupní poplatek
   třídy, článek statutu, poznámka, historie změn), nová krátká část o ručně doložených úplatách v ocenění.
10. Otevřený bod „Poznámky k poplatkům v XLS pro depozitáře“ potvrdit v `docs/otevrene-body.md`; předávka.

Krok 2a původního zadání (řádek matice ruční úpis „jeden člověk“) odpadá: ukázkový skript zakládá pro všechny činnosti
řádek „jeden člověk“ platný ode dne založení (pokyn 15. 11. 2026). Čtyři oči si Martin případně nastaví v UI.

**Kritéria přijetí:** Martin v UI ověří čtyři uživatele a jednu ruční úplatu v návrhu ocenění; sekce Výsledek.

## Výsledek

Provedl Claude (Sonnet) 17. 11. 2026 ve větvi `ukol/ZJ-zjednoduseni`; nasazení se souhlasem Martina v promptu (záloha, smazání, nové založení).

**Postup a ověření**

1. Zkouška `run_seed.sh investra_ci_zj04`: log 0 ERROR, 0 Traceback. SELECTem: 5 fondů (A–E; zadání uvádělo 6, seed zakládá 5 + obhospodařovatel + Services,
   tedy 7 knih), 37 ocenění, 21 obchodů, 17 pohybů tříd, 20 řádků matice (10 výchozích + 10 „jeden člověk“ od 17. 11.), 4 role (Admin 10 činností,
   Schvalovatel 10, Účetní 10 bez schvalování, Náhled 0), uživatelé `admin`, `ucetni`, `schvalovatel`, `view` se skupinami Investry podle ZJ-02. Databáze smazána (`odoo db drop`).
2. `.env` nečten; `grep -c` proměnné `INVESTRA_DEMO_USER_PASSWORD` = 1.
3. Záloha `zalohy/investra-2026-11-17-pred-ZJ.dump` (mimo git): 9,3 MB, `pg_restore -l` 10 913 položek. Záloha je jen databáze; filestore `investra` nezálohován (ukázková data bez příloh).
4. `investra-web` zastaven a odstraněn, `investra` smazána (`odoo db drop`, volumes nedotčeny), `run_seed.sh investra` znovu (log 0 ERROR).
   Stav shodný se zkouškou: 5 fondů + 1 obhospodařovatel + 1 Services, 37 ocenění, 21 obchodů, 17 pohybů, 20 řádků matice.
5. `investra-web` spuštěn příkazem z README; `/web/login` HTTP 200.
6. Nové `docs/sql/26-role-matice-uplaty.sql` (role, činnosti, uživatelé, matice, ruční úplaty), ověřeno na `investra`; ruční úplaty: 0 řádků (nové databáze).
7. Manuál: kap. 2 (záložka Úplaty, bez zpřísnění matice a fondových poplatků), kap. 3 (poplatky třídy, článek statutu, poznámka, historie), kap. 4 (matice bez
   fondů a jmenovitých uživatelů, nová část o ručně doložených úplatách), kap. 5 (role a činnosti, ukázkoví uživatelé bez hesel). Ověřeno v kódu a SELECTem, v prohlížeči ne.
8. Otevřený bod „Poznámky k poplatkům v XLS pro depozitáře“ potvrzen v `docs/otevrene-body.md`.

**Upozornění**

- `admin` má výchozí heslo Odoo: Martin si ho změní sám. Hesla ukázkových uživatelů jsou z `.env` (nikam se nevypisují); přihlášení ověří Martin.
- Účet `dbeaver_ro` nemá v nové `investra` práva na tabulky (`has_table_privilege` = false); obnoví je `tools/db/dbeaver_ro_grants.sql` až po souhlasu Martina.
- Zbytková nápověda pole **Obhospodařovatel** ve fondu („její schvalovací matice platí pro fond“) je po ZJ-01 zastaralá (kód matice pole nečte); opravit v dalším úkolu.
- Mimo zadání: nezkoušeno v prohlížeči (formuláře rolí, třídy, ruční úplata); přepočet ocenění Fondu A k 31. 10. není potřeba (databáze nová).

## Převzetí
