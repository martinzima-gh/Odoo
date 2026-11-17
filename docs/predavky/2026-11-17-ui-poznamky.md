# Předávka: poznámky Martina z průchodu UI (12 bodů), zpracovat až na jeho pokyn

**Cíl:** Martin prošel v UI založení fondu, úpisy a poplatky. Body se s ním nejdřív probírají (model Opus), opravy až po jeho pokynu.
**Stav:** větev `ukol/ZJ-zjednoduseni`, pracovní `investra` (8071) beze změn od nasazení ZJ-05. V této relaci se neměnil kód ani data.
**Ověřeno Martinem v UI:** oranžový pruh, blokování Odeslat ke schválení i obnova grafu po Spočítat fungují; ocenění Fondu A k 31. 10. 2026 je v pořádku.

**Body k posouzení** (zóna: Č = červená, O = oranžová, Z = zelená; zóny určit podle `.agents/rules/10-zony.md`)
1. Ve všech seznamech nabídnout sloupec ID položky, výchozí skrytý (Z/O).
2. Po odeslání ke schválení šlo smazat ruční úplatu (koš na záložce „Ručně doložené úplaty“). Varianty: skrýt koš; zrušit záložku
   (úplata je vidět i na záložce Úplaty). Zámek musí držet i v modelu (`unlink`); důvod, proč smazání prošlo, nezjištěn (Č).
3. Z Přehledu umožnit založit nové ocenění (klik na „Nezaloženo“ nebo jiné tlačítko); rozhodnout předvyplnění fondu a data (O).
4. Menu Nastavení → Fondy: první Účetní kniha, až za ní Fondy (Z).
5. Totéž menu: Schvalovací matice poslední, případně pod Auditní stopu s novým názvem; ověřit viditelnost podle skupin (Z/O).
6. Pravidla úplat: sloučit „Článek statutu“ (`statute_ref`) a „Poznámka“ (`note`) do jednoho pole; rozhodnout, co s existujícími hodnotami;
   zjednoduší odložený krok 4 ZJ-05 (XLS úplat) na jeden sloupec (Č).
7. Pole „Pořadí“ (`sequence`) u pravidla: ověřit smyčku `valuation.py:372`, jestli pravidla na sobě závisí. Pokud ne, skrýt/řadit podle druhu (Č).
8. Verze sazby mají jen „Platí od“, konec se odvozuje z další verze (`engine.split_by_versions`). Navrženo nepovinné „Platí do“ (Č).
9. Pole „Platí třídy“, „Přijímající třídy“, „Třída krytí“ nemají omezení na třídy téhož fondu; ani kontrola v modelu. Doplnit
   `domain` a constraint, nápovědy k polím (Č).
10. Krystalizace se týká jen výkonnostní úplaty; zobrazovat jen u ní a doplnit nápovědu (Z/O).
11. Řádek verze sazby ukazuje 8 sloupců; pásma, příplatky a většina výkonnostních polí v něm chybí. Zjistit, kde se zadávají, zobrazovat podle druhu úplaty,
    doplnit nápovědy (Č).

**Zbývá:** 1. Projednat body s Martinem (model Opus), s variantami a doporučením. 2. Po schválení plánu implementovat po zónách.
3. Krok 4 ZJ-05 (XLS úplat) jen na Martinovu výzvu, nejdřív rozhodnout bod 6. 4. Doplnit sekci Výsledek v zadání ZJ-05; do `main` jen na výzvu.

**Rozhodnutí:** žádné nové; nic se nezapisuje do deníku, dokud Martin body neschválí.
**Otevřené:** `dbeaver_ro` práva na `investra` (čeká na souhlas); formuláře ověřené jen v testech a v Martinově průchodu.
**Číst:** CLAUDE.md, tuto předávku, `docs/ukoly/ZJ-05-nasazeni-neaktualni-vypocet-a-xls.md`, `investra_nav/models/fee_rule.py`, `.agents/rules/10-zony.md`.

**Prompt pro novou relaci (model Opus):**
Přečti CLAUDE.md a docs/predavky/2026-11-17-ui-poznamky.md; probereš s Martinem 11 poznámek z UI bod po bodu, s variantami a doporučením.
Nic neprogramuj, dokud Martin neschválí plán; červená zóna jen s jeho plánem.
