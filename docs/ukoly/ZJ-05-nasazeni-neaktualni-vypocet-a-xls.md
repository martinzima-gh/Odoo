# ZJ-05 Nasazení upozornění na neaktuální výpočet, ověření v UI, XLS úplat

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (`investra_nav/models`, XLS v `package.py`) – jen s plánem schváleným Martinem; nasazení oranžová |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po commitu „neaktuální výpočet“) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Sonnet 5.5 (kroky 1–3 a 5); krok 4 návrh plánu také Sonnet, provedení až po schválení plánu Martinem |

**Kontext:** 17. 11. 2026 Martin zjistil, že po ručním zadání úplaty a Spočítat se neobnoví dlaždice s grafem kurzu (widget měl klíč bez času výpočtu)
a chtěl upozornění na neaktuální výpočet s blokováním odeslání (varianta A + blokovat). Hotovo ve větvi: `investra_nav` 0.34.0 (pole `computed_at`,
`inputs_stamp`, `stale_note`, kontrola v `action_submit`, pruh ve formuláři, obnova widgetu, 4 nové testy; `tools/run_tests.sh investra_nav`: 379 testů, 0 chyb).
Do běžící `investra` se ještě **nenasadilo** (kód se načte až po upgradu modulu).

**Postup:**
1. Po výslovném souhlasu Martina v promptu: záloha `pg_dump -Fc investra` do `zalohy/investra-2026-11-17-pred-nav34.dump` (ověřit `pg_restore -l`),
   `docker stop investra-web && docker rm investra-web`, upgrade `-u investra_nav --stop-after-init` na `investra` (stejně jako v README, bez `--max-cron-threads` změn),
   znovu spustit `investra-web`, ověřit `/web/login`. Log bez ERROR. Bez souhlasu nic nespouštět.
2. Říct Martinovi, co má ověřit v UI: ocenění Fondu A k 31. 10. 2026 (id 34, stav Spočteno, má ruční úplatu 1 000 CZK „test“): pruh se po změně vstupu objeví,
   tlačítko Odeslat ke schválení hlásí „Výpočet ocenění není aktuální“, po Spočítat pruh zmizí a graf kurzu třídy se načte znovu. Ocenění 34 po upgradu nemá otisk vstupů
   (`inputs_stamp` prázdný), takže hlídání začne až po jeho dalším Spočítat; to říct.
3. Oprava zbytkové nápovědy pole **Obhospodařovatel** ve fondu (`investra_fund/models/fund.py`, `help`: „její schvalovací matice platí pro fond“ je po ZJ-01 zastaralé; matice je společná).
   Nové znění navrhnout Martinovi, pak opravit a doplnit do testu/manuálu jen je-li třeba.
4. XLS pro depozitáře (otevřený bod „Poznámky k poplatkům v XLS“): navrhnout plán úpravy listu Úplaty v `investra_nav/models/package.py` – sloupce Článek statutu
   a Poznámka pravidla, u ruční úplaty poznámka a účet; u tříd vstupní a výstupní poplatek se článkem statutu a poznámkou. Plán s variantami předložit Martinovi,
   implementovat až po schválení; test, že text začínající `=` zůstane textem (rozhodnutí 2026-11-12).
5. Výsledek a předávka (`docs/predavky/`), commit a push do `ukol/ZJ-zjednoduseni`; do `main` jen na výzvu Martina.

**Kritéria přijetí:** Martin v UI ověří pruh, blokování odeslání a obnovu grafu po Spočítat; XLS plán schválen nebo odmítnut.

## Výsledek

## Převzetí
