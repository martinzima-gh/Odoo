# Předávka 2026-11-16: MN-12 zaokrouhlení a místa třídy po prvním pohybu

- **Cíl:** po zaúčtovaném úpisu nebo odkupu jdou měnit zaokrouhlení a desetinná místa kurzu a kusů třídy; kód a měna
  zůstávají zamčené; nic se nepřepočítává zpětně.
- **Stav:** větev `ukol/MN-manual`, commit MN-12 nad MN-11 (`254e09b`). Nenasazeno do `investra`.
- **Hotové:** `investra_nav` 20.0.0.31.3 (`fund_class.py` `LOCKED_FIELDS`, kontrola snížení míst kusů, pohled třídy, souhrn ocenění JS, 5 nových testů v `test_class_lock.py`),
  manuál kap. 2 a 3, Výsledek v zadání s nálezy k bodům 2 a 3.
- **Zbývá:** nasazení hlavní relací najednou s MN-10 a MN-11 – záloha `investra`, povýšení `investra_nav` (a modulů MN-10/11),
  restart 8071, ověření ve formuláři fondu (sloupce míst a zaokrouhlení třídy s pohybem jdou upravit, kód a měna ne).
- **Rozhodnutí:** Martin schválil obě doporučení (deník 2026-11-16 „Snížení míst kusů a zobrazení kurzu (MN-12)“),
  provedeno v `investra_nav` 20.0.0.31.3; zapsáno i do Claude Doc.
- **Při nasazení ověřit:** snížení míst kusů u třídy s pohybem s více místy skončí chybou; souhrn ocenění ukazuje kurz
  s místy uloženého kurzu (JS ověřen jen `node --check`).
- **Otevřené:** nic z MN-12.
- **Číst:** `docs/ukoly/MN-12-zaokrouhleni-trid-po-pohybu.md` (Výsledek), `docs/predavky/2026-11-16-mn10-12-poznamky-z-pruchodu.md`.
