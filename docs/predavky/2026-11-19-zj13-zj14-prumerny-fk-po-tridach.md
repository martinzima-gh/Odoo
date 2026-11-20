# Předávka 2026-11-19 – ZJ-13 doplnění a ZJ-14 průměrný FK po třídách

**Cíl:** (A) evidence kurzů jen aktivních měn; (B) úplata z průměrného FK po třídách (ZJ-14).

**Stav:** větev `ukol/ZJ-13-14` (pushnutá), do `main` nic. Commity `58f9f57` (ZJ-13 část A) a commit ZJ-14 (viz `git log`).
`investra` bez povýšení (žádné nové pole); `investra-web` nerestartován – změny Pythonu a filtr Kurzy měn se v UI projeví až po
dohodnutém restartu a upgradu `investra_rates` a `investra_nav`.

**Hotové:**
- `_store` ukládá jen aktivní měny; filtr Aktivní měny; ruční stahování kurzů popsáno v ZJ-13 a manuálu 07; historie ECB v otevřených bodech.
- ZJ-14: `engine.average_fee`, `valuation._average_class_item` (začátek nároku, zařazení s přesností na ocenění, body, booked, přerušení),
  opravy základu a částky po třídách, příjemci, pojistka v obou směrech, kontrola `average_class_gap`, náhled Schématu, nápověda pravidla.
- Referenční příklad A, B, C sedí na haléř (Odoo test s krokem 2 a čistá funkce); tabulka v ZJ-14 Výsledek.
- Testy: `investra_rates` 42, `investra_rates+` 874, `investra_nav` 521, `investra_nav+` 595, `all` 1025, `tools/nav_reference` 60 – vše OK.
- Deník rozhodnutí + Claude Doc (rev 389): „Evidence kurzů jen aktivních měn“, „Průměrný FK po třídách – zařazení a pevné části“.

**Zbývá:** (1) Martin: projít odchylky v ZJ-14 (test s krokem 2; třída s úpisem 1. 1. má v lednu 30 dní; pojistka i směrem třídy → fond).
(2) Po pokynu restart `investra-web` a upgrade `investra_rates`, `investra_nav` v `investra` se zálohou. (3) Sloučení do `main` na výzvu.
(4) Export Claude Doc do `docs/architektura.md` při další větší změně Doc.

**Otevřené:** necommitnutá cizí změna `addons/custom/investra_nav/tests/test_valuation_sequence.py` (z dřívější relace; nechal jsem ji být).
Účet `dbeaver_ro` nemá práva na novější tabulky (`investra_fee_rule` aj.) – doplnit granty skriptem `tools/db/dbeaver_ro_grants.sql`.

**Číst:** `CLAUDE.md`, `docs/ukoly/ZJ-14-prumerny-fk-po-tridach.md`, `docs/ukoly/ZJ-13-kurzy-usd-a-stazeni.md`,
`addons/custom/investra_nav/tests/test_fee_average_class.py`.
