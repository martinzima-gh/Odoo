# Předávka 2026-11-16: MN-12 zaokrouhlení a místa třídy po prvním pohybu

- **Cíl:** po zaúčtovaném úpisu nebo odkupu jdou měnit zaokrouhlení a desetinná místa kurzu a kusů třídy; kód a měna
  zůstávají zamčené; nic se nepřepočítává zpětně.
- **Stav:** větev `ukol/MN-manual`, commit MN-12 nad MN-11 (`254e09b`). Nenasazeno do `investra`.
- **Hotové:** `investra_nav` 20.0.0.31.2 (`fund_class.py` `LOCKED_FIELDS`, pohled třídy, 3 nové testy v `test_class_lock.py`),
  manuál kap. 2 a 3, Výsledek v zadání s nálezy k bodům 2 a 3.
- **Zbývá:** nasazení hlavní relací najednou s MN-10 a MN-11 – záloha `investra`, povýšení `investra_nav` (a modulů MN-10/11),
  restart 8071, ověření ve formuláři fondu (sloupce míst a zaokrouhlení třídy s pohybem jdou upravit, kód a měna ne).
- **Rozhodnutí:** žádné nové; plán MN-12 schválil Martin.
- **Otevřené (rozhoduje Martin):**
  1. snížení míst kusů pod přesnost zaúčtovaných pohybů odmítnout? (doporučeno ano; riziko neodkoupitelného zbytku),
  2. souhrn ocenění (`valuation_summary.js`) formátuje kurz starého ocenění podle dnešních míst třídy – brát místa
     z uloženého textu kurzu? (doporučeno ano, drobná oprava JS).
- **Číst:** `docs/ukoly/MN-12-zaokrouhleni-trid-po-pohybu.md` (Výsledek), `docs/predavky/2026-11-16-mn10-12-poznamky-z-pruchodu.md`.
