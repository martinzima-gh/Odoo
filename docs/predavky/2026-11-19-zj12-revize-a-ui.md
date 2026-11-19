# Předávka 2026-11-19: ZJ-12 po revizi Copilota a úpravách rozhraní, čeká sloučení do `main`

**Cíl:** sloučit ZJ-11 a ZJ-12 do `main` na Martinův pokyn; pak ZJ-14 (průměrný FK po třídách).
**Stav:** větev `ukol/ZJ-zjednoduseni`, vše v `origin` (poslední commit „předávka ZJ-12 revize a UI“). Do `main` nic.
Pracovní `investra`: `investra_nav` 20.0.0.38.0 povýšený s kódem 06b13f4 (+ dashboard, derivative), `investra-web` běží (8071).

## Hotové (19. 11.)
- 6c přemostění (daňový efekt), dorovnání přesunů daně mezi oceněními (s4 únor −182,71 schválen), záporná oprava = upozornění.
- Revize Copilota `docs/ukoly/CP-2026-11-19-ZJ12-revize.md` (13 bodů): nálezy 1 a 2 opraveny (rozpad příjemců jako doklad, váhy příjemců).
- Rozhraní: Úplaty jeden řádek na pravidlo; přemostění třídy svisle v jedné mřížce (Martin vzhled potvrdil); předvolba do chatteru fondu;
  Přehled podle názvu; daň bez tříd/příjemců/role; upozornění na pole bez účinku; příjemci u průměrného FK; oprava pádu úplaty fondu s příjemci.
- Testy: `investra_nav` 510/510, `investra_nav+` 584/584; `all` naposledy 1001/1001 před revizí (znovu před `main`).
- Deník a Claude Doc rev 387 aktuální; `docs/architektura.md` exportovaná na rev 382 (před sloučením znovu exportovat).

## Zbývá
1. Na Martinův pokyn: `tools/run_tests.sh all`, export `docs/architektura.md`, sloučení do `main`.
2. ZJ-14 průměrný FK po třídách: technický plán podle zásad v zadání, ke schválení.
3. Necommitnutý `docs/ukoly/ZJ-13-kurzy-usd-a-stazeni.md` nevznikl v této relaci – nechat, zeptat se Martina.

## Otevřené otázky
- Řízený prohlížeč (Playwright) pro zkoušky UI?

## Číst
1. `CLAUDE.md`  2. tato předávka  3. `docs/ukoly/ZJ-14-prumerny-fk-po-tridach.md`  4. `docs/rozhodnuti.md` (řádky 2026-11-19)
