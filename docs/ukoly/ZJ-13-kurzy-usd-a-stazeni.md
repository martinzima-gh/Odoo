# ZJ-13 Kurzy USD a zapnutí stahování kurzů v pracovní databázi

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (data a nastavení, žádná změna kódu); zápis do databáze `investra` jen přes UI nebo ORM |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (nebo aktuální pracovní větev) |
| Zadal, dne | Martin, 19. 11. 2026 (varianta 2 z odpovědi na hlášení „Chybí kurz USD k 31. 10. 2026“) |
| Řešitel | Claude (zápis do databáze); jiný agent do `investra` nezapisuje |
| Navazuje na | rozhodnutí 2026-11-10 „Ochrana kurzů“, 2026-11-11 „Platnost kurzů“ |
| Stav | **zadané, nezačato** |

**Příčina:** `Spočítat` u ocenění s ruční úplatou v USD končí chybou „Chybí kurz USD ke dni 2026-10-31“. V pracovní databázi je jen
ČNB/EUR a ECB/CZK (338 záznamů, 1. 8. 2025 – 17. 11. 2026); USD tam nikdy nebylo a cron „Investra: stažení kurzů“ je vypnutý
(`investra_rates/data/cron.xml`, `active=False`). Limit z Platnosti kurzů s tím nesouvisí (kurz nenalezen, ne příliš starý).

**Cíl:** pracovní databáze má skutečné kurzy USD (a dalších měn, které fondy používají) za potřebné období, aby šlo ocenění počítat.

**Kroky:**
1. Zjistit, které cizí měny a které zdroje kurzů (ČNB, ECB) fondy v databázi skutečně používají (účetní jednotka → zdroj, měny nástrojů a úplat). Výsledek ukázat Martinovi.
2. Rozhodnout s Martinem rozsah: od kdy zpět (nejméně od prvního ocenění, např. 1. 8. 2025), které měny.
3. Stáhnout kurzy přes `investra.rate` (`fetch_cnb`, `fetch_cnb_monthly`, `fetch_ecb`), ne přímým SQL; denní ČNB po dnech, měsíční ČNB pro ostatní měny.
4. Zvážit zapnutí cronu stahování (zásah do nastavení a restart nejsou nutné, ale dotaz na Martina před zapnutím).

**Mimo rozsah:** změna kódu evidence kurzů, ruční kurzy (jen nouzově, s důvodem), změna výchozích limitů stáří.

**Kritéria přijetí:** v **Kurzy měn** jsou USD záznamy za dohodnuté období; ocenění s úplatou v USD se spočítá; počty a vybrané kurzy porovnané s ČNB.

**Neověřeno / otevřené:** zda ukázkové fondy mají být se skutečnými kurzy, nebo smyšlenými (data jsou smyšlená, kurzy ČNB skutečné); dostupnost ČNB z kontejneru.
