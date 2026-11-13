# Předávka 2026-11-13: ruční úplaty a přecenění podle profilu

**Cíl:** zjednodušit ručně zadané úplaty (datum, popis, částka a měna, druh nákladu, třída, rozdělení, náhled
zaúčtování) a přeceňovat cizoměnové položky ocenění podle profilu `investra_fx_revaluation` (varianta A).

**Stav:** větev `feature/nav-prototyp`, poslední commit s touto předávkou.

**Hotové:**
- Detail ocenění: vrácen řádek „Přidat“ u ručně doložených úplat (CSS); pravidlo a třída ruční úplaty jen z fondu
  ocenění, nové pravidlo z výběru s fondem a druhem zamčeným, kontrola fondu na serveru.
- Plán `docs/navrh-rucni-uplaty.md` schválen; rozhodnutí v deníku a v Claude Doc (stav N, plán schválen).
- Etapa 1: ocenění přeceňuje podle profilu, `investra_test` povýšena (viz Provedení v plánu).

**Zbývá:**
- Etapa 2 (ruční úplaty) – **čekat na pokyn uživatele**. První krok: nová pole `investra.valuation.external` a migrace.
- Otázka: zakázat samostatný běh přecenění nad profilem fondu?
- Export `docs/architektura.md` z Claude Doc (rev 334) s další větší změnou.
- `investra_vzhled` (8072) dostane CSS opravu po sloučení do `cp/vzhled`, až Copilot uloží práci.

**Otevřené body:** zařazení nástroje vznikne prvním pořízením (uživatel chce celé zařazení zjednodušit).

**Číst:** `docs/navrh-rucni-uplaty.md`, `addons/custom/investra_nav/models/valuation.py` (`_fx_revaluation_lines`,
`_apply_external`), `addons/custom/investra_fx_revaluation/models/fx_profile.py`.
