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

Provedl Claude (Opus, hlavní relace) 17. 11. 2026 ve větvi `ukol/ZJ-zjednoduseni`; plán schválil Martin. Do `investra` se
nenasazovalo a nic se v ní nezaúčtovalo (nasazení je ZJ-04).

**Co se změnilo**

| Bod | Soubor | Změna |
|---|---|---|
| 1, 3 | `investra_nav/models/fee_rule.py`, `nav_views.xml` | pole Poznámka; seznam pravidel; záložka **Úplaty** ve formuláři fondu (`fee_rule_ids`) |
| 2 | `fee_rule.py`, `valuation.py` | `overlap_warning` (upozornění ve formuláři i sloupec Souběh) a kontrola ocenění `fee_overlap` (varování): role na celém fondu i na třídách, nebo třída s více pravidly téže role; daň se neposuzuje |
| 4, 5 | `investra_fund/models/fund.py`, `fund_views.xml` (verze 0.12.0) | z fondu zrušeny sazby a příjemci poplatků; třída je má povinné (0 %, Obhospodařovatel), navíc Článek statutu a Poznámka; nový formulář třídy s historií (otevře se šipkou v seznamu tříd) |
| 6, 7 | `investra_nav/models/valuation.py` (verze 0.33.0) | `investra.valuation.external` bez pravidla: třída (prázdná = fond), částka ≠ 0 (i záporná), měna, nákladový účet knihy, povinná poznámka, nepovinná příloha. `_apply_manual_fees`: řádek nákladu na zvolený účet (vzor derivátů, `extra.account_id`), protiúčet role `fee_payable`; cizí měna `_fx` k datu ocenění, oba řádky nesou původní měnu, takže závazek přecení FX profil. Pořadí: před první výkonnostní odměnou nebo daní, jinak po úplatách |
| 8 | `fee_rule.py`, migrace `investra_nav 20.0.0.33.0` | druh `external` a `_apply_external` zrušeny; post-migrace vypíše počty, otevřená ocenění vrátí k přepočtu a smaže ruční úplaty a pravidla přes ORM; uzavřené ocenění migraci zastaví |
| 10 | `tests/test_manual_fees.py` (11 testů), úpravy 5 testových souborů | viz níže |

**Číselný příklad (test `test_foreign_currency_at_valuation_rate_and_preview_equals_posted`):** fond v CZK, třídy A a B po 1 000 CZK,
ruční úplata celého fondu 4 EUR, kurz ČNB 25,000 k 31. 1. 2027 (24,000 k 29. 1. se nepoužije) → MD ostatní náklady 100 CZK (4 EUR),
D závazek z úplat 100 CZK (−4 EUR); FK 2 000 → 1 900. Náhled (návrh dokladu z výpočtu) je po odeslání, schválení a zaúčtování
tentýž doklad se stejnými řádky k datu ocenění. Pořadí: ruční úplata třídy A 10 CZK sníží hrubou hodnotu A z 1 100 na 1 090,
výkonnostní odměna je proto 65,34 místo 75,34.

**Ověření**

- `tools/run_tests.sh all` na dočasné `investra_ci_20261117_122932` (smazána): 843 testů, 0 failed, 0 error.
- Migrace na dočasné kopii `investra` (`investra_ci_20261117_zj03mig`, i s filestore; po zkoušce smazána), upgrade `-u investra_entity`:
  bez chyby, proběhly i migrace ZJ-01. Smazána 1 ruční úplata a 1 pravidlo `external`, ocenění Fondu A k 31. 10. 2026
  vráceno do návrhu bez návrhů dokladů; sloupce poplatků fondu odstraněny, třídy bez prázdných sazeb. Přepočet toho ocenění
  na kopii proběhl (stav Spočteno, kontrola souběhu v pořádku) a byl vrácen zpět.

**Odchylky a upozornění**

- **Historie třídy:** původní poznámka, že `tracking=True` v Odoo 20 bez modulu `mail_tracking` neukládá změny polí, byla nepřesná
  (ověřeno 17. 11. 2026: vestavěné sledování Odoo 20 funguje v samostatné transakci i bez modulu `mail_tracking`). Změny poplatků
  zapisuje `write()` třídy do historie sama („staré → nové“), pole poplatků proto nemají `tracking=True`, aby se zprávy nezdvojovaly (ZJ-10).
- **XLS:** list Úplaty bere název z rozpisu (`line.name`), jinak by u ruční úplaty zapsal FALSE. Jiná změna XLS není.
- `investra_posting` se nemění; vlastní účet nese řádek v `extra` jako u derivátů.
- Povinnost účtu a poznámky ruční úplaty hlídá kontrola v Pythonu a formulář, ne NOT NULL ve sloupci (staré řádky smaže až post-migrace).
- Zpráva při založení třídy je anglicky („Třída fondu created“), text Odoo.

**Pro ZJ-04:** pracovní `investra` má moduly ještě před ZJ-01 (fond 0.9.0, NAV 0.31.3). Upgrade musí jít od `investra_entity`
(`-u investra_entity`); `-u investra_fund,investra_nav` selže na chybějící skupině Správa. Po nasazení přepočítat ocenění Fondu A k 31. 10. 2026.

## Převzetí
