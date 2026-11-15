# DE-02 Evidence FX derivátu: smlouva, nohy, ruční hodnota

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (nový model a formuláře, bez účtování) |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Sonnet |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Rozsah, Evidence), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** uživatel založí měnový forward nebo swap, vidí ho v seznamu a ve formuláři; nic se neúčtuje.

**Plán (od Clauda):**

1. Nový modul `addons/custom/investra_derivative` (závislosti `investra_nav`, `investra_counterparty`,
   `investra_instrument_master`), verze 20.0.0.1.0, práva v `security/ir.access.csv` podle vzoru obchodu (`investra.trade`).
2. Modely podle oddílu Evidence: `investra.derivative` (dědí `investra.record.guard` a chatter jako obchod),
   `investra.derivative.leg`, `investra.derivative.value`. Peněžní pole s měnou, společnost z fondu.
3. Při založení smlouvy vzniká 1 : 1 nástroj typu `derivative_otc` (kód z řady OTC, název „FX forward/swap EUR/CZK
   <datum vypořádání>“); pokud povinná pole evidence nástrojů (emitent, číselníky) založení brání, zastavit se
   a popsat ve Výsledku, co chybí – nic neobcházet.
4. Kontroly: forward právě 1 noha, swap právě 2 s opačným směrem a rostoucím datem; měny nohy různé; částky kladné;
   datum vypořádání ≥ datum sjednání; jedna z měn nohy je funkční měna fondu (jiné páry první verze nepodporuje);
   sjednaný kurz dopočtený z částek, jen ke čtení; po stavu Sjednáno jsou smlouva a nohy jen ke čtení.
5. Stavy smlouvy Návrh / Sjednáno / Vypořádáno / Stornováno a nohy Otevřená / Vypořádaná jako pole; přechody
   (tlačítka Sjednat, Vypořádat, Storno) v tomto kroku **nedělat** – přidá je DE-03.
6. Pohledy: seznam, formulář (hlavička, nohy, záložka Ruční hodnoty), hledání (fond, protistrana, stav), nabídka
   Portfolio → Deriváty. České popisky, vzhled jako obchod.
7. Testy kontrol a založení nástroje; `tools/run_tests.sh investra_derivative`, pak `all`.

**Rozsah souborů:** jen `addons/custom/investra_derivative/`, tento soubor, předávka.

**Mimo rozsah:** účtování, podrozvaha, ocenění, výpočet RH, role účtů, osnova, ukázková data, databáze `investra`.

**Kritéria přijetí:** modul se nainstaluje na čisté databázi; testy bez selhání (číslo z výstupu); formulář swapu jde
uložit a chybné kombinace hlásí srozumitelnou českou chybu.

## Výsledek

Provedl Claude Code (hlavní relace) 15. 11. 2026, větev `etapa/derivaty`.

- **Změněné soubory:** nový modul `addons/custom/investra_derivative/` (`__manifest__.py`, `models/derivative.py`,
  `security/ir.access.csv`, `views/derivative_views.xml`, `tests/common.py`, `tests/test_derivative.py`), tento soubor.
- **Ověřeno (příkaz a výsledek):** `tools/run_tests.sh investra_derivative` → 0 failed, 0 error(s) of 15 tests;
  `tools/run_tests.sh all` → 0 failed, 0 error(s) of 703 tests (dočasné `investra_ci_*`, smazány). Testy pokrývají
  založení nástroje 1 : 1 (typ Mimoburzovní derivát, kód OTC-…, identifikátor = číslo smlouvy), uložení swapu
  formulářem jako zpracovatel, všechny kontroly z bodu 4 s českou hláškou, ochranu stavu a zámek po Sjednáno.
- **Odchylky od zadání:**
  - Přidán třetí druh **FX spot** (pokyn Martina 15. 11. 2026 v relaci): jedna noha jako forward, volí se při zadání.
  - Měna nástroje = funkční měna fondu (v ní se vede reálná hodnota); měnový pár je v názvu a na nohách.
  - Smlouva má práva jako obchod (`cru`, bez mazání); nohy a ruční hodnoty `crud`. Návrh smlouvy tedy zpracovatel
    nesmaže, stejně jako obchod.
  - Zařazení nástroje do obchodního modelu se při založení nevytváří (datum sjednání se v návrhu může měnit);
    založí ho Sjednat v DE-03.
- **Neověřeno:** vzhled formuláře v prohlížeči (ověřeno jen uložení přes testovací `Form`); modul není nainstalovaný
  v `investra` (DE-05).
- **Otevřené otázky a návrhy mimo rozsah:** FX spot dostává nástroj typu Mimoburzovní derivát (list ČNB DOFO31_22)
  stejně jako forward – zda má spot ve výkazech ČNB a v portfoliu vystupovat jako derivát, rozhodne Martin (DE-05, etapa CN).

## Převzetí
