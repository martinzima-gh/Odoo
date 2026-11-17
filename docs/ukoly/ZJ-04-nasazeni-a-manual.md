# ZJ-04 Nasazení zjednodušení do `investra` a manuál

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (nasazení se souhlasem), zelená (manuál) |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-03) |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Sonnet (nasazení), manuál Haiku nebo Sonnet |

**Postup:**
1. Záloha `investra` (`zalohy/investra-<datum>-pred-ZJ.dump`), upgrade dotčených modulů – **jen po souhlasu Martina
   v promptu**. Log upgradu bez ERROR.
2. Kontrola, že `.env` má `INVESTRA_DEMO_USER_PASSWORD` (jen existence, hodnotu nečíst); spustit skript uživatelů a rolí.
   Ověřit přihlášení `ucetni`, `schvalovatel`, `view`, `admin` (heslo zadá Martin, ne agent).
2a. Po upgradu založit v UI (jako `admin`) řádek matice **Ruční zadání úpisu a odkupu – jeden člověk** s „Platí od“ dnes
   (rozhodnutí Martina 17. 11. 2026: po sloučení řádků ZJ-01 by jinak platily čtyři oči z globálního řádku 17. 11.).
   Matice je jedinečná podle (činnost, Platí od): při nasazení 17. 11. nový řádek nejde, místo toho se změní globální
   řádek ze 17. 11. (dnešní řádek jde ještě měnit) na „Ne – stačí jeden člověk“.
3. SELECT do `docs/sql/`: role, jejich činnosti a uživatelé; řádky matice.
4. Manuál: kap. 4 (matice bez fondů a jmenovitých uživatelů), kap. 5 (role a činnosti, ukázkoví uživatelé bez hesla),
   kap. 2 (záložka Úplaty, bez zpřísnění matice a fondových vstupních poplatků), kap. 3 (vstupní a výstupní poplatek
   třídy, článek statutu, poznámka); nová krátká část o ručně doložených úplatách v ocenění.
5. Otevřený bod „Poznámky k poplatkům v XLS pro depozitáře“ potvrdit v `docs/otevrene-body.md`; předávka.

**Kritéria přijetí:** Martin v UI ověří čtyři uživatele a jednu ruční úplatu v návrhu ocenění; sekce Výsledek.

## Výsledek

## Převzetí
