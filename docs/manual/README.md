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
| 4 | [04-kalendar-a-matice.md](04-kalendar-a-matice.md) | kalendář ocenění a schvalovací matice | koncept |
| 5 | – | uživatelé a role | plán |
| 6 | – | portfolia a nástroje | plán |
| 7 | – | kurzy | plán |
| 8 | – | první úpis nebo převzetí fondu | plán |

Pořadí práce při založení od nuly: kap. 1 (společnost obhospodařovatele) → kap. 1 (kniha fondu) → kap. 2 (fond) → kap. 3 (třídy).
