# Předávka 2026-11-15 – hlavní relace: návrh FX derivátů a zadání DE-02 až DE-05

**Cíl:** hlavní relace jen navrhuje a píše zadání s prompty; programují Sonnet a Opus v samostatných relacích.

**Stav:** větev `etapa/derivaty` z `main` (commit „Návrh FX derivátů…“), pracovní strom čistý. `main` obsahuje vše
do ST-01 včetně ST-03 a OC-01. Běží 8071 (`investra`) a výuková 8069.

**Hotovo:**
- `docs/navrh-fx-derivaty.md`: zjednodušené řešení (podrozvaha v nominálech, RH variantou B, ruční hodnota,
  vypořádání tlačítkem), číselný příklad swapu přes dvě ocenění.
- Zadání `docs/ukoly/DE-02` až `DE-05`, prompty v `docs/plan-dalsiho-vyvoje.md` (Etapa 1), deník, otevřený bod.

**Zbývá (první krok nahoře):**
1. DE-02 (Sonnet) → DE-03 (Opus, Martin schvaluje čísla účtů) → DE-04 (Opus) → DE-05 (Sonnet), každý v nové relaci.
2. Po každém kroku hlavní relace jen čtením zkontroluje Výsledek, než pustí další.
3. Zapsat rozhodnutí z 15. 11. do Claude Doc (tabulka Přijatá rozhodnutí) a obnovit export `docs/architektura.md`.
4. ST-02 (GitHub Actions), ST-04 (pravidla Copilota a Antigravity); Martin: mazání starých větví, heslo správce.

**Rozhodnutí:** „FX deriváty zjednodušeně“ v `docs/rozhodnuti.md` (2026-11-15).

**Otevřené otázky:** předpisy k podrozvaze a derivátům neověřeny (první bod DE-03); soulad zjednodušené RH s IFRS 13
ověřit s auditorem; čísla podrozvahových účtů schválí Martin.

**Číst:** `docs/navrh-fx-derivaty.md`, `docs/plan-dalsiho-vyvoje.md` (Etapa 1), `docs/ukoly/DE-02-evidence-fx-derivatu.md`,
`docs/ukoly/DE-03-ucty-sjednani-vyporadani.md`.
