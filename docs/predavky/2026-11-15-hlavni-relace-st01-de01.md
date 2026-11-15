# Předávka 2026-11-15 – hlavní relace: ověření IM-13, zadání ST-01 a DE-01

**Cíl:** hlavní relace jen ověřuje, píše zadání do `docs/ukoly/` a prompty s modelem; programují jiné relace.

**Stav:** větev `feature/instrument-master`, commit „Zadání ST-01 a DE-01“ (+ tato předávka), pracovní strom čistý.
Běží `investra-web` (8071, databáze `investra`) a výuková instance 8069; 8070 a 8072 zastavené.

**Hotovo (ověřeno jen čtením):**
- IM-13 a oprava `create_book`: sekce Výsledek vyplněná; v `investra` 7 knih, fondy A–E s oceněními 14/12/6/4/1,
  MD = D ve všech knihách, Investra Services rámec 500/2002 Sb., osnova `cz`, 289 aktivních a 41 archivovaných účtů,
  `investra_env_banner` nenainstalovaný, přihlašovací stránka 8071 vrací 200.
- Zadání `docs/ukoly/ST-01-slouceni-do-main.md` a `docs/ukoly/DE-01-navrh-fx-derivaty.md`; prompty v plánu aktualizované.

**Neověřeno:** obrazovky v prohlížeči (lišta, Přehled, Ocenění, Portfolio, Výkazy); testy 677/0/0 hlavní relace nespouštěla.

**Zbývá (první krok nahoře):**
1. Martin: změnit výchozí heslo správce v `investra`, projít nabídky v prohlížeči.
2. ST-01 (Sonnet) – sloučení do `main`; pak DE-01 (Opus) – návrh FX derivátů. Postupně, ne souběžně (jeden pracovní strom).
3. Po DE-01: Martin rozhodne varianty, hlavní relace zkontroluje zadání DE-02 až DE-06.
4. ST-02 (GitHub Actions), ST-03 (chyba Přehledu – čeká na text chyby), ST-04 (pravidla Copilota a Antigravity, 8072 z kopie `investra`).

**Rozhodnutí:** žádné nové.

**Otevřené otázky:** skupina `account.group_account_basic` u správce v `investra`; smazání starých databází a větví jen
na Martinův pokyn; má výuková instance 8069 zůstat spuštěná?

**Číst:** `docs/plan-dalsiho-vyvoje.md`, `docs/ukoly/ST-01-slouceni-do-main.md`, `docs/ukoly/DE-01-navrh-fx-derivaty.md`,
`docs/predavky/2026-11-15-im13-hotovo.md`.
