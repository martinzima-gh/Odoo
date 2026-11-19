# ZJ-13 Kurzy USD a zapnutí stahování kurzů v pracovní databázi

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (data a nastavení, žádná změna kódu); zápis do databáze `investra` jen přes UI nebo ORM |
| Výchozí větev | `ukol/ZJ-13-14` (z `main` 9f0f3d2) |
| Zadal, dne | Martin, 19. 11. 2026 (varianta 2 z odpovědi na hlášení „Chybí kurz USD k 31. 10. 2026“) |
| Řešitel | Claude (zápis do databáze); jiný agent do `investra` nezapisuje |
| Navazuje na | rozhodnutí 2026-11-10 „Ochrana kurzů“, 2026-11-11 „Platnost kurzů“ |
| Stav | **hotovo 19. 11. 2026 (data v `investra`, žádná změna kódu)** |

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

## Výsledek (19. 11. 2026)

**1. Co fondy používají:** 8 účetních jednotek se zdrojem ČNB (funkční měna CZK), 1 se zdrojem ECB (EUR); jiný zdroj není. Měny tříd, nástrojů,
cen, účetních událostí, derivátů i uložených ručních úplat jsou jen CZK a EUR; USD není v žádném uloženém záznamu (ruční úplata v USD
se kvůli chybě neuložila). Aktivní měny v Odoo: CZK, EUR, USD. Rozsah tedy: USD, 1. 8. 2025 – 19. 11. 2026.

**2. Stažení** přes ORM (`fetch_cnb` po dnech + `_publish`, `fetch_ecb`), bez SQL zápisu; ČNB a ECB z kontejneru dostupné (zkouška 30. 10. 2026:
USD 21,814). 475 dní ČNB bez chyby, 0 rozdílů proti Odoo. USD ČNB: 325 vyhlášených dnů (14 dnů bez USD jsou české státní svátky,
kdy ČNB nevyhlašuje; kurz platí z předchozího dne). USD ECB: jen vyhlášení z 18. 11. 2026 (`fetch_ecb` bere jen aktuální soubor; historii ECB
kód nestahuje, mimo rozsah).

**3. Vedlejší účinek (nahlásit):** `_store` ukládá všechny měny, které v `res.currency` existují (i neaktivní), nejen USD. Vzniklo 9 572
záznamů v `investra.rate` (do 9 910) pro ~29 měn (AUD, GBP, JPY, CHF, PLN …; ČNB i BGN do 12/2025) a odpovídající neaktivní kurzy
v `res.currency.rate` (10 249). Záznamy kurzů se nesmějí mazat ani měnit (ochrana kurzů), takže zůstávají; nemají vliv na výpočty
(měny jsou neaktivní a nic je nepoužívá) a stejně by je cron přinášel denně. Chování je v kódu `_store`, neměnil jsem ho.

**4. Ověření:** kurz USD z evidence i z Odoo (1/rate) = kurzovní lístek ČNB (stažený znovu přes curl) pro 4. 8. 2025 (21,254),
31. 12. 2025 (20,632), 31. 3. 2026 (21,333), 30. 6. 2026 (21,287), 30. 10. 2026 (21,814). Ocenění fondu B (č. 35, k 31. 10. 2026, zdroj ČNB):
ruční úplata 1 000 USD se spočítala (21 814,00 CZK, kurz 21,814); zkouška běžela v transakci s rollbackem, v `investra` nezůstala.

**5. Cron „Investra: stažení kurzů“ zapnut** (`active=True`, denně, přes ORM; záznam je `noupdate`, upgrade modulu ho nevrátí). **Pozor:** instance
`investra-web` běží s `--max-cron-threads=0`, takže cron sám nepoběží, dokud se tato volba neodstraní (změna příkazu v README, restart
kontejneru; čeká na Martinův pokyn). Do té doby kurzy stahovat ručně.

**Otevřené:** (a) omezit `_store` jen na měny používané knihami (změna kódu, červená zóna – rozhodnutí Martina); (b) historie ECB pro EUR jednotku.
