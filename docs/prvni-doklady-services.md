# První doklady Investra Services: postup

Podklad pro společnou práci. Účtuje se v `investra_dev`, které je zatím prázdné (0 dokladů). Vše je zkušební, dokud se společnost neoznačí za ostrou.
Ověřeno 2026-11-07: v `investra_dev` je jedna společnost „Investra Services s.r.o. (TEST)“, česká osnova s 328 účty, 0 dokladů. Kroky v UI ověřím na instalaci při společné práci.

## Před prvním dokladem (potřebuje rozhodnutí)

1. Posoudit `osnova-investra-services.md`, hlavně opravy typů účtů a výchozí účty deníků.
2. Určit účetní období a první den účtování.
3. Potvrdit režim DPH: zatím neplátce, registrace nepřišla.
4. Doplnit údaje společnosti (IČO, adresa) a rozhodnout, zda zůstane označení TEST.
5. Rozhodnout, zda účtovat rovnou reálné doklady, nebo smyšlené. Citlivé údaje do repozitáře nejdou, do databáze jen vědomě.

## Doklady na zkoušku

| Doklad | Co ukáže |
|---|---|
| Přijatá faktura za službu (`ukazkova_prijata_faktura.pdf`) | Návrh a zaúčtování, účet 518 |
| Vydaná faktura | Prodejní deník, účet 602 |
| Platba přijaté faktury | Ruční úhrada, bez bankovního párování |
| Interní doklad | Deník ostatních operací |
| Předvaha v SQL | Výsledek v DBeaveru |

## Co nejde

Community nemá import výpisů, párování, rozvahu ani výsledovku v menu. Proto předvaha přes SQL `docs/sql`.

## Pro status s Martinem

Ukázat: účtování Services v Odoo, oddělení společností, ocenění fondu v `investra_test` se zamčenými návrhy a schválením, balíček pro depozitáře, katalog poplatků.
Rozhodnout: edice a hosting po schůzce s Honzou.
