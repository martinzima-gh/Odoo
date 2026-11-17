# MN-19 Manuál kap. 8: první úpis nebo převzetí fondu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (`docs/manual/`), věcně náročná |
| Výchozí větev | `ukol/MN-manual` (klon `~/odoo-review` synchronizuje Claude před zahájením) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | po MN-15 a MN-16; osnova `docs/manual/README.md` (kap. 8) |

**Cíl:** `docs/manual/08-prvni-upis-a-prevzeti-fondu.md`: od hotového fondu (kap. 1–7) k prvnímu úpisu a prvnímu ocenění; odděleně převzetí fondu od jiného administrátora (počáteční stavy). Zadání se upřesní po MN-15/16 podle toho, co kapitoly 5–7 už pokryjí.

**Provádí:** Sonnet, revize Claude (účetní dopad je v kódu a v deníku rozhodnutí; nic nevymýšlet, nejasnosti do Výsledku).

## Výsledek

Doplní provádějící agent.

## Převzetí

Posoudil Claude (Sonnet 5.5) 17. 11. 2026: **kap. 8 nepřevzata**, vrací se k přepracování (soubor zůstává jen v `~/odoo-review`, do `~/odoo-dev` nekopírován).
Zóna v pořádku (jen `docs/manual/`); ostatní změny v klonu (kap. 5–7, pohledy matice a fondu) jsou shodné s již převzatým stavem.
Nálezy proti kódu `investra_nav/models/movement.py`:
1. **Storno a oprava popsány chybně.** Kód (`action_reverse`, `action_correct`, `_do_reverse`): obě akce stornují doklad původního pohybu a ten
   dostane stav Stornováno; Opravit navíc založí nový pohyb v návrhu s odkazem na opravovaný. Kapitola tvrdí, že Stornovat vytváří reverzní
   pohyb opačného typu a že původní pohyb po Opravit zůstává zaúčtovaný; příklady 1 a 2 včetně „bilancí“ proto neplatí.
2. Storno i oprava jdou u ručního zadání přes matici (`subscription_manual`, výchozí příprava bez druhé osoby), ne přes jinou činnost „Storno a oprava pohybu“.
3. Uvedeno bez opory v kódu: tlačítko „Hromadný import“, „poplatek podle sazby“ s upozorněním, pole „Změna kapitálu ve funkční měně (zobrazení)“, „Počáteční ocenění“, postup převzetí „importem“.
4. Jazykové chyby a zbytky konceptu: „series“, „spot váží“, „písomných“, „Staný“, „vytvorena“, „kap. ?“, „zvedení úpisu“; příklad míchá EUR a CZK bez ověřených čísel.
5. Štítek „ověřeno v kódu“ proto neplatí; po přepracování ověřit každé pole a hlášení.
Další krok: přepracovat kap. 8 po opravách 1–5 (vlastní úkol MN-19b, ověřit proti kódu a testům `investra_nav`).
