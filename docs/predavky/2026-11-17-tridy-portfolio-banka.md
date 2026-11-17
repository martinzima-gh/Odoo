# Předávka: manažerská třída, třída portfolia a banky (ZJ-08, ZJ-09 zadané)

**Cíl:** fond s více třídami: třída bez účasti na výsledku portfolia, portfolio a bankovní účet společné, nebo pro jednu třídu.
**Stav:** větev `ukol/ZJ-zjednoduseni`, pushnuto, poslední commit `c8b3c6b`. Kód beze změny, jen deník, otevřené body, zadání a Claude Doc.

**Hotovo (17. 11. 2026):**
- ZJ-06 dokončeno a nasazeno (Sonnet body 1–6, 8–11; Opus 7, 7b, 12, 13, opravy z UI); viz `2026-11-17-zj06-ui-hotovo.md`.
- Rozhodnutí v deníku i Claude Doc: manažerská třída bez účasti na výsledku portfolia; ruční krystalizace; třída portfolia;
  bankovní účet třídy (buď všem třídám, nebo jedné); bankovní účet = vlastní účet hlavní knihy, výběr podle třídy a měny (IS účet neposílá).
- Zadání `docs/ukoly/ZJ-08-manazerska-trida-a-rucni-krystalizace.md` a `docs/ukoly/ZJ-09-trida-portfolia.md` (červená zóna, Opus).

**Zbývá:**
1. Plán ZJ-08 (bez kódu) ke schválení Martinem: kde je volba (třída, nebo alokační schéma), úprava `_finish` a `engine`,
   vztah k pořadí nároků, ruční krystalizace (pole v ocenění, historie kroků, matice). První krok: přečíst `valuation.py` `_compute_all`, `_finish`, `_is_crystallisation`.
2. Plán ZJ-09 po ZJ-08 (třída portfolia, banka třídy, pole Bankovní účet na dokladech, kurzové přecenění po třídách).
3. Dřívější: ocenění Fondu A v3 (id 39) spočítá Martin; ZJ-07 daň (návrh); archivace fondu čeká na pokyn; ZJ-06 do `main` na výzvu.

**Otevřené:** statut a zdanění manažerské třídy (právník, daňový poradce); `docs/architektura.md` nepřeexportováno (přibylo jen 5 řádků tabulky rozhodnutí).

**Číst:** CLAUDE.md, tuto předávku, `docs/ukoly/ZJ-08-manazerska-trida-a-rucni-krystalizace.md`, `docs/ukoly/ZJ-09-trida-portfolia.md`,
sekci „Vnitřní zúčtování tříd“ v `docs/architektura.md`.
