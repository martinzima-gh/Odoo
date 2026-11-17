# ZJ-03 Poplatky a ručně doložené úplaty

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování ocenění, NAV, migrace) – plán níže schvaluje Martin |
| Výchozí větev | `ukol/ZJ-zjednoduseni` (po ZJ-02) |
| Větev úkolu | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace) podle zadání Martina, 17. 11. 2026 |
| Navazuje na | rozhodnutí 2026-11-17 „Poplatky fondu a tříd“ a „Ručně doložené úplaty zjednodušeny“ |
| Model | Opus |

**Postup – pravidla úplat (`investra_nav/models/fee_rule.py`, pohledy):**
1. Nové pole **Poznámka** (Text) vedle „Článek statutu“.
2. **Upozornění, ne zákaz:** pro jednu nákladovou roli (včetně Ostatních nákladů) má fond aktivní pravidlo bez tříd
   i pravidlo s třídami, nebo jedna třída má dvě aktivní pravidla téže role. Zobrazit ve formuláři pravidla (onchange /
   výpočetní pole s textem) a v kontrolách ocenění jako varování; uložení ani výpočet nezastaví.
3. Záložka **Úplaty** ve formuláři fondu (O2M pravidel); nabídka Pravidla úplat zůstává jako přehled.

**Postup – vstupní a výstupní poplatek (`investra_fund/models/fund.py`, pohledy):**
4. Z fondu odstranit `entry_fee_rate`, `exit_fee_rate`, `entry_fee_recipient`, `exit_fee_recipient` (pole, formulář,
   kopírování v `create` třídy přes `MOVEMENT_PARAMS`); na třídě zůstávají a třída je má povinné (sazba výchozí 0).
   Výpočet úpisu a odkupu se nemění (čte už jen třídu).
5. Na třídě nová pole **Článek statutu** a **Poznámka** pro vstupní a výstupní poplatek; sledování změn sazby a příjemce
   (historie na třídě).

**Postup – ručně doložené úplaty (`investra_nav/models/valuation.py`):**
6. `investra.valuation.external` bez `rule_id`: **třída** (prázdná = celý fond), **částka** (smí být záporná, ne nula),
   **měna** (výchozí měna fondu), **nákladový účet** (jen účty knihy fondu typu náklad), **poznámka** (povinná),
   příloha nepovinná. Kontrola, že třída patří fondu ocenění.
7. Zaúčtování k datu ocenění; v cizí měně kurzem k datu ocenění (stejný zdroj a platnost kurzu jako ostatní přepočty
   ocenění). **Protiúčet pevně závazek** – role závazku z úplat (ověřit existující roli; nevymýšlet novou bez dotazu).
   Pořadí: spolu s ostatními úplatami, před výkonnostní odměnou a daní. Náhled zaúčtování ze stejné funkce
   (`investra.posting.preview`) a doklady na záložce ocenění.
8. Zrušit druh pravidla `external` („Výpočet mimo Odoo s doložením“) a `_apply_external`. Migrace: řádky ručních úplat
   a pravidla druhu `external` **smazat přes ORM** (Martin 17. 11. 2026: v `investra` jen ukázková data); před smazáním
   vypsat počet. Upravit `seed.py`, pokud ruční úplatu zakládá.
9. XLS pro depozitáře **neměnit** (poznámky do XLS řeší samostatný bod v `docs/otevrene-body.md`).
10. Testy: ruční úplata fondu i třídy, záporná, v cizí měně (kurz k datu ocenění), náhled = doklad, pořadí před
    výkonnostní odměnou, upozornění souběhu, třída bez fondových výchozích hodnot vstupního poplatku.

**Mimo rozsah:** XLS, role a matice, manuál.

**Kritéria přijetí:** `tools/run_tests.sh all` zelené; číselný příklad (CZK fond, ruční úplata v EUR) v sekci Výsledek;
nic nezaúčtováno v `investra`.

**Schválený plán:** body 1–10; schválení Martin v promptu („Plán v úkolu ZJ-03 schvaluji (červená zóna, Martin).“).

## Výsledek

## Převzetí
