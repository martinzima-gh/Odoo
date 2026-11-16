# MN-13 Manuál kap. 4: kalendář ocenění a schvalovací matice

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen dokumentace v `docs/manual/`) |
| Výchozí větev | `ukol/MN-manual` (po MN-12) |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-02 (kap. 1–3, formát a konvence), osnova v `docs/manual/README.md` |

**Cíl:** kapitola 4 manuálu. Podle ní Martin v `investra` (8071) u fondu založeného podle kap. 1–3 nastaví kalendář
ocenění a schvalovací matici tak, aby šlo spočítat a schválit první ocenění. Co nebude fungovat nebo bude matoucí,
se opraví samostatnými úkoly.

**Výstup:** `docs/manual/04-kalendar-a-matice.md` a řádek kap. 4 v `README.md` (stav „koncept“). Obsah:

1. **Kalendář ocenění** (`investra.valuation.calendar`, `investra_fund/models/fund.py`; použití v `investra_nav`
   `valuation.py`): vztah k poli Frekvence ocenění a Datum vzniku fondu (kap. 2), jak se zadávají dny ocenění
   a mimořádné ocenění, co hlídá kontrola (texty chyb), co nejde po prvním ocenění změnit.
2. **Schvalovací matice** (`investra.approval.matrix` a `.step`, `investra_fund/models/approval_matrix.py`, views a nabídka
   „Schvalovací matice“): činnosti (`ACTIVITIES`), role Příprava a Schvalování ocenění, druhá osoba, kroky, platnost od,
   kdo smí matici měnit (rozhodnutí: zpřísnění mění jen schvalovatel ocenění, ne správce). Výchozí řádky po založení
   fondu (pokud vznikají – zjistit z kódu a seedu).
3. **Žádosti ke schválení a Úkony bez druhé osoby** (nabídky stejného jména): k čemu jsou, kdo je vidí, jak se žádost
   vyřídí. Jen přehled, podrobný postup ocenění patří do pozdější kapitoly.
4. **Minimální nastavení pro první ocenění**: krátký kontrolní seznam (co musí být vyplněno ve fondu, kalendáři
   a matici a jaké skupiny uživatelů jsou potřeba – skupiny jen jmenovat, uživatelé a role jsou kap. 5).

**Formát kroku:** stejně jako kap. 1–3 (README, Konvence): cesta v nabídce, pole s významem a výchozí hodnotou, povinná
pole, kontroly s textem chyby z kódu, co nejde později změnit. Štítek „Ověřeno v kódu, v prohlížeči neověřeno“. Bez obrázků.

**Zdroje (číst cíleně, grep):** `investra_fund` (models `fund.py` jen část kalendáře, `approval_matrix.py`, views, `security/`),
`investra_nav/models/valuation.py` (jen místa, kde se čte kalendář, frekvence a matice), `tools/demo_data/seed.py` (jak
seed nastavuje kalendář a matici), `docs/rozhodnuti.md` (jen hesla interval ocenění, schvalování, matice, druhá osoba,
kalendář). Názvy polí a nabídek přebírat přesně z XML a `string=`, nevymýšlet.

**Pravidla:** česky, stručně, bez vysvětlování účetních základů. Smyšlená jména (Alfa Investiční společnost, a.s.; Fond Alfa
Růst). Bez textu z důvěrných dokumentů, bez obchodního názvu IS. Nesrovnalosti v aplikaci neopravovat, jen zapsat
do Výsledku jako číslovaný seznam pro pročištění.

**Rozsah souborů:** `docs/manual/04-kalendar-a-matice.md`, `docs/manual/README.md`, tento soubor (Výsledek), předávka.
Kód ani databázi neměnit; testy se nespouštějí.

**Kritéria přijetí:** každé pole formulářů kalendáře a matice (včetně kroků) je popsané, nebo výslovně vynechané s důvodem;
kontrolní seznam pro první ocenění; seznam nálezů ve Výsledku.

## Výsledek

Hotovo (Sonnet, 16. 11. 2026): `docs/manual/04-kalendar-a-matice.md` (koncept, „Ověřeno v kódu, v prohlížeči neověřeno“),
řádek kap. 4 v `README.md` přepnut na koncept. Kód, databáze ani testy se nedotkly. Zdroje: `investra_fund` (`fund.py`,
`approval_matrix.py`, views, `data/approval_matrix.xml`, `security/ir.access.csv`), `investra_nav` `valuation.py`
(`_period_start`, kontroly matice), `investra_dashboard` `dashboard.py` (jediné místo, kde se čte kalendář), seed.

Pokrytí polí: kalendář (Datum ocenění, Plánované zveřejnění), řádek matice (všechna pole vč. vynechaných `builtin`
a `company_id`, které se nezadávají), kroky (Pořadí, Krok, Nejnižší role, Jen tito uživatelé), žádost a její potvrzení,
log úkonů. Seed nastavuje matici na jednoho uživatele pro obhospodařovatele (rozhodnutí 2026-11-15); kalendář seed nezakládá.

Nálezy pro pročištění (nic neopraveno):

1. Kalendář se nekontroluje proti Frekvenci ocenění, Datu vzniku, statutu ani zákonné lhůtě (deník 2026-11-04
   „Interval ocenění“ to předpokládá); řádky se negenerují podle frekvence.
2. Ocenění jde založit k datu mimo kalendář; kalendář čte jen Přehled fondů (další ocenění, „Ocenění po termínu“).
3. Mimořádné ocenění nemá vlastní druh ani pole, je to jen další řádek kalendáře.
4. Řádek kalendáře jde měnit a mazat kdykoli, i po prvním oceněním (žádný zámek), na rozdíl od Data vzniku.
5. Výchozí řádky matice (od 1. 1. 2000, `noupdate`) běžný uživatel nezmění; mění se jen novým řádkem obhospodařovatele.
6. Řádky z modulu jde od vlastních rozlišit jen poznámkou, `builtin` není v seznamu ani formuláři.
7. Záložka fondu „Zpřísnění matice“ je needitovatelný seznam; zadání řádku z ní v prohlížeči neověřeno.
8. Čtyři oči u ocenění, ceny a výjimky z uzamčení se potvrzují na záznamu, u ostatních činností v Žádostech ke schválení;
   neobvyklé rozdělení, v manuálu zatím jen zmíněno (podrobně kap. 8 a pozdější).
9. Příklad „fond zpřísní storno obchodu“ i číselné příklady v kapitole jsou z kódu, ne z prohlížeče; ověřit v UI.

