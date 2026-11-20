# Manuál aplikace Investra

**Čtenář:** účetní a administrátor fondu. Zná účetnictví, Odoo nezná. Účetní základy se tu nevysvětlují, jen vazby v aplikaci.
**Příklady:** smyšlené (Alfa Investiční společnost, a.s.; Fond Alfa Růst). Žádná skutečná data.
**Prostředí:** pracovní databáze `investra` na http://127.0.0.1:8071.

## Konvence

- **Cesta v nabídce:** `Investra › Nastavení › Fondy › …`; názvy polí a tlačítek v tučném písmu přesně jako v aplikaci.
- **Výchozí** = hodnota, kterou pole má při založení. **Povinné** = bez něj nejde uložit.
- Text v uvozovkách u „Kontrola“ je znění chyby z aplikace.
- **Štítek ověření** je u každé kapitoly: dokud ho Martin neprojde v prohlížeči, stojí „Ověřeno v kódu, v prohlížeči neověřeno“.
- Obrázky zatím nejsou.
- Zjištěné nesrovnalosti aplikace jsou ve Výsledku úkolu MN-02 (`docs/ukoly/`), ne v kapitolách.

## Osnova a stav

| Kap. | Soubor | Téma | Stav |
|---|---|---|---|
| 1 | [01-spolecnost-a-kniha.md](01-spolecnost-a-kniha.md) | investiční společnost a účetní kniha (průvodce) | koncept |
| 2 | [02-fond.md](02-fond.md) | formulář Fondy | koncept |
| 3 | [03-tridy.md](03-tridy.md) | třídy fondu | koncept |
| 4 | [04-oceneni-a-matice.md](04-oceneni-a-matice.md) | frekvence ocenění a schvalovací matice | koncept |
| 5 | [05-uzivatele-a-role.md](05-uzivatele-a-role.md) | uživatelé a role | koncept |
| 6 | [06-portfolia-a-nastroje.md](06-portfolia-a-nastroje.md) | portfolia a nástroje | koncept |
| 7 | [07-kurzy.md](07-kurzy.md) | kurzy | koncept |
| 8 | [08-prvni-upis-a-prevzeti-fondu.md](08-prvni-upis-a-prevzeti-fondu.md) | první úpis a odkup; převzetí fondu zatím jen plán | koncept |
| 9 | [09-uplaty-a-opravy.md](09-uplaty-a-opravy.md) | úplaty, odměna a daň v ocenění: kroky a Základ, ruční opravy, zrušení úplaty, list Úplaty | koncept |
| 10 | [10-rozdeleni-mezi-tridy.md](10-rozdeleni-mezi-tridy.md) | sdílené a specifické položky, podíl tříd, alokační schéma | koncept |
| 11 | [11-dan.md](11-dan.md) | daňová pravidla, výjimky fondu, rozpad daně a FVOCI | koncept |

Pořadí práce při založení od nuly: kap. 1 (společnost obhospodařovatele) → kap. 1 (kniha fondu) → kap. 2 (fond) → kap. 3 (třídy).
