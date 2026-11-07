# Prototyp NAV: stav a spuštění

Stav 2026-11-07, větev `feature/nav-prototyp`, databáze `investra_test`, smyšlená data. Vývojový návrh, není schválený k ostrému použití.
Technická zjištění jsou v `analyza-odoo20-nav.md`, varianty úplat v `poplatky-varianty.md`.

## Moduly

| Modul | Hotovo | Testů |
|---|---|--:|
| `investra_entity` | Kniha, založení s povinným nastavením, role účtů, skupiny | 6 |
| `investra_chart_fund` | Pracovní osnova fondu a mapování rolí | 4 |
| `investra_rates` | Kurzy ČNB a ECB, neměnný záznam se zdrojem, promítnutí do Odoo | 15 |
| `investra_fund` | Fondy, třídy, kalendář, zaokrouhlení kurzu | 10 |
| `investra_posting` | Události, ochrana dokladů, třída na řádku, hash, storno | 22 |
| `investra_instruments` | Nástroje, ceny se schválením, obchody, pozice | 9 |
| `investra_allocation` | Verzovaná schémata, poměr a pořadí nároků | 3 |
| `investra_nav` | Úplaty, ocenění, schvalování, depozitář, zveřejnění, balíček | 66 |

Výpočetní jádro a referenční výpočet mají dalších 53 testů mimo Odoo (`tools/nav_reference`).

## Co je ověřené

- Pět scénářů: Odoo z účetních řádků dojde ke stejnému FK, kapitálu tříd, kusům a kurzům jako referenční výpočet.
- Akceptace prototypu z `harmonogram.md`: opakovaný výpočet nic nezdvojí, součet tříd rovná se FK, pozice se rovnají hlavní knize, zadavatel si neschválí vlastní ocenění, vrácení před zaúčtováním je bez storen, vrácení depozitářem stornuje a vzniká nová verze.
- Referenční výpočet není nezávislá kontrola: má stejného autora. Scénáře musí ověřit člověk.

## Odchylky od architektury

- `investra_posting` závisí na `investra_fund`, protože třída je pole na řádku.
- Role účtů jsou v `investra_entity`, šablona osnovy v `investra_chart_fund`.
- Pravidlo podle účetního rámce zatím není: řádky dokladu určuje kód ocenění. Doplnit, až bude víc rámců.
- Rozdělení mezi třídy podle pořadí nároků se zaúčtuje jako přesun přes vnitřní zúčtování. Do architektury doplnit jako nový způsob alokace.

## Co chybí

Sjednáno, nevypořádáno; poplatky obchodů; dohadné položky; kupóny a dividendy; termínované vklady a deriváty v portfoliu; platnost kurzu;
hranice kontrol; UI ověřené člověkem; bezpečnostní revize; test na reálném objemu.

## Spuštění testů

```
python3 -m unittest discover -s tools/nav_reference -p 'test_*.py'
python3 tools/nav_reference/nav_reference.py
docker compose -f docker-compose.investra.yml run --rm --no-deps -T odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d investra_test -u investra_nav --test-enable --test-tags /investra_nav \
  --stop-after-init --no-http --max-cron-threads=0
```

Pozor: `-i` u už nainstalovaného modulu testy nespustí, zpráva „0 tests“ není úspěch.
Kurzy jsou v databázi společné a neměnné: testy s kurzy nesmí používat stejné období jako ukázková data.

## Ukázka

Data vytvoří `tools/nav_demo/demo.py` (všechno smyšlené). Web nad testovací databází se spustí na portu 8071, vývojové instance se to nedotkne:

```
docker compose -f docker-compose.investra.yml run -d --rm --no-deps --name investra-test-web -p 127.0.0.1:8071:8069 odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d investra_test --db-filter='^investra_test$' --max-cron-threads=0
docker stop investra-test-web
```

Testovací databáze má výchozí přihlášení správce. Slouží jen na tomto počítači a nesmí obsahovat reálná data.
