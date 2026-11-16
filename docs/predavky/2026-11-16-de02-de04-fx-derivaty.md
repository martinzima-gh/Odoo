# Předávka 2026-11-16: DE-02 až DE-04 – FX spot, forward a swap

**Cíl:** etapa 1 plánu (`docs/plan-dalsiho-vyvoje.md`): evidence, účtování a ocenění měnových derivátů ve fondu.

**Stav:** větev `etapa/derivaty`, poslední commit „DE-04“ (viz `git log`); pushnuto do `origin/etapa/derivaty`.
`tools/run_tests.sh all`: 733 testů, 0 selhání, 0 chyb. Modul `investra_derivative` není v databázi `investra` (to je DE-05).

**Hotové**
- DE-02: modul `investra_derivative` – smlouva, nohy, ruční hodnota, nástroj 1 : 1; přidán druh **FX spot**.
- DE-03: 18 rolí a účtů (čísla určil Martin 16. 11.), druh role Podrozvaha, sjednání (podrozvaha), vypořádání nohy
  (dva doklady), storno smlouvy a vypořádání, náhled zaúčtování; ověřené citace 501/2002 Sb. a ČÚS 110, 105.
- DE-04: ocenění variantou B, ruční hodnota, přepočet podrozvahy, kontroly; bez změny v `investra_nav`.

**Zbývá:** DE-05 (Sonnet) – první krok: záloha `investra` do `zalohy/`, zkouška migrace `investra_chart_fund`
20.0.0.9.0 a `investra_entity` 20.0.0.9.0 na dočasné kopii ze zálohy, pak instalace `investra_derivative`.

**Rozhodnutí:** deník 2026-11-16 „Účty FX spotu, forwardu a swapu (DE-03)“ a „FX deriváty v ocenění (DE-04)“.

**Otevřené otázky pro Martina**
- Tolerance ruční hodnoty 0,10 % nominálu (návrh) – potvrdit nebo změnit.
- FX spot má nástroj typu Mimoburzovní derivát (list ČNB pro deriváty), ač podle ČÚS 110 bod 1 c) derivátem není.
- Mapování nových rolí na výkazy ČNB (v testu `investra_cnb` je dočasná výjimka).
- Výjimka z ČÚS 110 (bod 37) a § 4a vyhlášky 501 ve vztahu k fondu, novely vyhlášky po 1. 1. 2024 – neověřeno.
- Historie gitu: commit `0852614` jiné relace („Návrh: oprava zveřejněného ocenění“) obsahuje soubory DE-03, commit
  `a395d54` „DE-03“ jen Výsledek. Obsah je správný; přepis historie jen na Martinův pokyn. Ve stejném adresáři
  pracovaly souběžně dvě relace – příště commitovat jen jmenovité soubory.

**Číst:** `CLAUDE.md`, `docs/navrh-fx-derivaty.md`, `docs/ukoly/DE-03-*.md`, `docs/ukoly/DE-04-*.md`, `docs/ukoly/DE-05-*.md`.
