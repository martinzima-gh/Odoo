# AG-019 Úpisy a odkupy: formulář s dopočty při ručním zadání

Zadání pro Antigravity (druhý vývojář). Pravidla jsou v `.agents/rules/`, role v `CLAUDE.md` (Role agentů).
Původní označení plánu: UO-01.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (podle schváleného plánu níže); kontroly a zaúčtování pohybu jsou červená zóna a **nemění se** |
| Výchozí větev | `main` |
| Větev úkolu | `ag/AG-019-upisy-formular` |
| Zadal, dne | Martin, 19. 11. 2026 (plán schválil Martin 19. 11. 2026) |
| Navazuje na | rozhodnutí 2026-11-19 „Úpisy a odkupy – dopočty při ručním zadání“, `docs/manual/08-prvni-upis-a-prevzeti-fondu.md` |

**Cíl:** Při ručním zadání úpisu a odkupu formulář sám navrhne dopočitatelné hodnoty podle pravidel třídy a pohyby mají
přehledný formulář a seznam. Zdroj „IS“ se dál nedopočítává.

**Rozsah souborů:** `addons/custom/investra_nav/models/movement.py` (jen onchange, výchozí hodnoty a zobrazovací pole),
pohledy `view_movement_form` / `view_movement_list` / `view_movement_search` v `addons/custom/investra_nav/views/nav_views.xml`,
testy pohybů v `addons/custom/investra_nav/tests/` (nový soubor), `docs/manual/08-prvni-upis-a-prevzeti-fondu.md`.

**Mimo rozsah:** kontroly a zaúčtování (`_check_booking`, `_booking_valuation`, `_book_lines`, `_lines_functional`,
`_capital_functional`) se NEMĚNÍ; nové uložené pole ani příznak „upraveno ručně“; zdroj IS. Když by cokoli vyžadovalo změnu
zaúčtování nebo kontrol, zastavit a zeptat se (červená zóna). Testy Odoo, commit, push a povýšení modulu dělá Claude při převzetí.

**Kritéria přijetí:** body A–E níže; předvyplněný pohyb projde `action_book` beze změny kontrol; stávající testy pohybů
beze změny; kontrola pohledů `python3 tools/view_check/check_views.py` bez chyb.

**Schválený plán** (schválil Martin 19. 11. 2026):

**Rozhodnutí Martina:** u ZDROJE „Ruční zadání“ formulář navrhne dopočitatelné hodnoty podle pravidel třídy (kusy, poplatek,
rozdíl ze zaokrouhlení, cena ze zveřejněného kurzu); uživatel je smí přepsat. U zdroje „IS“ se nic nedopočítává (zásada „Odoo
jen kontroluje“ platí dál). Návrh jen předvyplní hodnoty, které stejné kontroly projdou.

### A) Dopočty při ručním zadání

Onchange; jen když source = manual a stav Nezaúčtováno. Jednoduché pravidlo: změna VSTUPU (třída, typ, datum, přijatá platba,
kusy nebo požadovaná částka u odkupu, cena) vždy znovu přepočte závislá pole (poplatek, kusy u úpisu, rozdíl, hrubá částka
u odkupu). Ruční úprava závislého pole platí, dokud uživatel nezmění vstup. Žádný příznak „upraveno ručně“, žádné nové uložené pole.

1. **Cena za kus:** po výběru třídy a data předvyplnit kurz třídy z posledního zveřejněného ocenění k datu
   (`_published_valuation`); vedle ceny zobrazit „zveřejněný kurz k DD. MM. RRRR“. Když zveřejněné ocenění není (první úpis
   třídy), cenu nepředvyplnit, ukázat nápovědu „První úpis: zadejte počáteční cenu za kus“ a důvod odlišné ceny předvyplnit
   textem „První úpis třídy“.
2. **Úpis** – uživatel zadá PŘIJATOU PLATBU (`amount_class`): poplatek = platba × vstupní sazba třídy (na haléře, jako dnes
   `_onchange_fee`); kusy = (platba − poplatek) / cena, zaokrouhlené na `unit_digits` podle `unit_rounding` třídy (stejně jako
   expected v `_booking_valuation`); rozdíl ze zaokrouhlení = platba − poplatek − money(kusy × cena); zbytek pak vyjde 0.
3. **Odkup** – uživatel zadá KUSY (výchozí) NEBO POŽADOVANOU ČÁSTKU (zobrazovací volba „Odkup podle: kusů / částky“, neukládá se):
   podle kusů: hrubá částka = money(kusy × cena), poplatek = hrubá částka × výstupní sazba, rozdíl 0, výplata = hrubá − poplatek;
   podle částky: kusy = částka / cena zaokrouhlené podle třídy, hrubá částka = money(kusy × cena), rozdíl = částka − hrubá
   (zobraz, komu patří), poplatek ze sazby; výplata jako dnes.
4. **Kurz (`fx_rate`) a hrubá částka ve funkční měně:** předvyplnit z vyhlášeného kurzu k datu (už dnes v create/write);
   u třídy v měně fondu obě pole SKRÝT.
5. **Příjemce poplatku a komu patří rozdíl:** předvyplnit z třídy (už dnes); partnera příjemce ukázat jen u příjemce
   Obhospodařovatel nebo Distributor.
6. **Výchozí hodnoty:** datum = dnes; typ z tlačítka (viz C); třída předvyplněná, má-li fond jedinou třídu (u fondu vybraného
   ve filtru).
7. **Třída bez sazby poplatku (0 %):** poplatek se předvyplní 0,00 a jde zadat ručně (jako dnes). Jakmile je poplatek > 0, pole
   Příjemce je ve formuláři povinné (required), předvyplněné z třídy, a pokud ho třída nemá, musí ho vybrat uživatel; partner
   podle A5. Upozornění „poplatek se liší od sazby třídy“ je jen informativní (nezastavuje), u sazby 0 % zní „třída nemá
   sazbu poplatku; poplatek zadán ručně“. Test: třída bez sazby, ruční poplatek s příjemcem → projde `action_book`.

### B) Rozložení formuláře (pořadí podle práce)

- Hlavička: Zaúčtovat / Opravit / Stornovat, stav.
- Nadpis: „Úpis“ / „Odkup“ + třída (Fond – třída) + měna kurzu; vpravo Datum.
- Řádek zdroje: Zdroj; u ručního zadání Důvod; u IS Identifikátor.
- 1 **Zadání:** úpis – Přijatá platba; odkup – Odkup podle (kusů / částky) a Kusy nebo Požadovaná částka; Cena za kus
  s „zveřejněný kurz k …“ (zelená fajfka, když se shoduje); Důvod odlišné ceny JEN když se cena liší nebo zveřejněný kurz chybí;
  Kurz měny jen u třídy v cizí měně.
- 2 **Poplatek:** Sazba (% z třídy, jen pro čtení) → Poplatek; upozornění, když se poplatek liší od sazby; Příjemce; Partner (A5).
- 3 **Výsledek** (jen pro čtení): Kusy (u úpisu dopočtené, s textem „zaokrouhleno dolů na 6 míst“ podle třídy), Kusy × cena,
  Rozdíl ze zaokrouhlení + Komu patří, Zbytek (zelená 0,00, jinak červeně s textem „zaúčtování zastaví, je-li víc než 0,01“),
  Výplata investorovi (odkup), Změna kapitálu třídy (v měně kurzu a ve funkční měně), Hrubá částka ve funkční měně (cizí měna).
- Pak Účetní událost / Opravuje pohyb / Ocenění s cenou (jen když jsou), Důvod storna (jen stornované), záložka Zaúčtování.
- Pole bez hodnoty a bez významu pro daný typ a zdroj skrýt (např. výplata u úpisu, partner u interního příjemce).
- **Vzorový úpis** pro test i manuál: platba 1 000 000,00 CZK, sazba 1 %, cena 1 036,6444, 6 míst dolů →
  poplatek 10 000,00, kusy 955,004437, kusy × cena 990 000,00, rozdíl 0,00, zbytek 0,00 (přepočítat a ověřit v testu).

### C) Seznam a nabídka

- V seznamu tlačítka „Nový úpis“ a „Nový odkup“ (`default_movement_type`) místo obecného Nový.
- Sloupce v pořadí: Datum, Fond, Třída, Typ, Stav, Kusy, Cena za kus, Hrubá částka (měna kurzu), Poplatek, Změna kapitálu ±,
  Měna kurzu; Kurz, Hrubá ve funkční měně, Zdroj, Identifikátor IS, Účetní událost jako volitelné skryté.
- Výchozí filtr žádný; ponechat řazení od nejnovějšího. Seskupení podle fondu a třídy zachovat.
- Prázdný stav seznamu: krátký návod (úpis = zadejte přijatou platbu, odkup = kusy nebo částku; zbytek dopočte formulář).

### D) Testy (`odoo.tests.Form`)

Úpis z platby (vzor výše), odkup podle kusů, odkup podle částky s rozdílem, první úpis bez zveřejněného ocenění, třída v cizí
měně (kurz předvyplněn), zdroj IS – nic se nedopočítává, ruční úprava poplatku zůstane, dokud se nezmění vstup, předvyplněný
pohyb projde `action_book` bez chyby (stejné kontroly), třída bez sazby s ručním poplatkem a příjemcem. Stávající testy pohybů
beze změny.

### E) Manuál

V kapitole 8 nahradit „Zásada: Odoo nic nedopočítává“ dvěma odstavci (IS: jen kontrola; ruční zadání: formulář navrhne hodnoty,
uživatel je může upravit) a doplnit vzorový úpis a odkup.

### Po dokončení (Claude při převzetí)

Testy `investra_nav` → `investra_nav+`, commit, push. Přidá-li se jen pohled a žádné pole, stačí povýšit modul se zálohou
a restartovat `investra-web` (Martin souhlasí); kontrola ocenění 35 a 39 jako dosud. Martinovi napsat, co šlo ven, a poslat
snímek nebo popis formuláře úpisu a odkupu.

## Výsledek

Doplní Antigravity.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
