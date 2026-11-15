# Předávka 2026-11-15 – evidence nástrojů (IM-01 až IM-12)

**Cíl:** dokončit etapu evidence nástrojů, emitentů a portfolií a ukázat ji uživateli v `investra_test` a `investra_vzhled`.

**Stav:** větev `feature/instrument-master`, poslední commit v době předávky `869bc44` (+ tato předávka).
Jiná relace (Opus) právě dokončuje IM-11 krok 2: neuložené změny v `investra_nav` (verze 20.0.0.29.0 s migrací),
`docs/rozhodnuti.md`, `docs/otevrene-body.md`; běží testy na `investra_ci_master`, existuje i `investra_ci_migrace`.
**Nová relace nesmí začít, dokud tato relace necommitne** (ověřit `git status` čistý a commit „Variabilní sazba…“).

**Hotovo:**
- IM-01 až IM-08: addon `investra_instrument_master` 20.0.0.6.0, SPPI na nástroji (`investra_instruments` 20.0.0.15.0).
- IM-09 (emitent s popiskem, odchylka od typu jako upozornění), IM-10 (výplata „Nepravidelně“).
- IM-11 krok 1: `docs/navrh-variabilni-sazba.md`; uživatel dostal doporučení (EIR varianta a) prospektivně, nahrazené
  toky archivovat, „platí od“ kterýkoli den) a krok 2 s nimi zadal.
- IM-12 částečně: `investra_test` povýšena a modul nainstalován (zálohy v `zalohy/*-2026-11-15-pred-IM.dump`,
  kategorie zařazení beze změny); nové obrazovky jsou na http://127.0.0.1:8071.

**Zbývá (první krok nahoře):**
1. Ověřit, že IM-11 krok 2 je commitnutý a testy prošly (sekce Výsledek v `docs/ukoly/IM-11-variabilni-sazba.md`);
   dočasné databáze `investra_ci_*` po něm smazat, pokud zůstaly.
2. `investra_vzhled` (8072): klon `~/odoo-review` má neuložené úpravy dvou pohledů (nahrazuje je commit `29ee710`).
   Rozhodnutí Martina: (a) zahodit a klon přepnout na aktuální větev, nebo (b) uložit stranou. Pak záloha, upgrade, restart.
3. Doinstalovat `investra_nav` 20.0.0.29.0 (migrace variabilní sazby) do `investra_test` i `investra_vzhled`, se zálohou.
4. Chyba nabídky Přehled na 8072: server vrací 200, padá v prohlížeči; čeká se na text chyby od uživatele.
5. Sekce Převzetí v IM-01 až IM-11, zápis do Claude Doc (tabulka Přijatá rozhodnutí), případně export
   `docs/architektura.md`; sloučení do `feature/nav-prototyp` jen na výzvu uživatele.

**Rozhodnutí z této relace:** vše v `docs/rozhodnuti.md` s datem 2026-11-15 (rozšíření místo paralelních modelů,
portfolio určuje kategorii, SPPI na nástroji, vzhled zachovat, BA0088, výplata Nepravidelně).

**Otevřené otázky:** odkazy IFRS 9 B5.4.5/B5.4.6 neověřené (auditor nebo znění přijaté EU); porovnání BA0088 s produkčním
SDAT; `BANK_SECTORS` bez nerezidentních bank; pracovní režim: uživatel chce, aby hlavní relace jen připravovala zadání
a prompty pro levnější modely, nic neprogramovala.

**Číst:** `docs/ukoly/IM-00-prehled.md`, `docs/ukoly/IM-12-prevzeti-a-instalace.md` (Výsledek),
`docs/ukoly/IM-11-variabilni-sazba.md` (Výsledek), `docs/navrh-variabilni-sazba.md`.
