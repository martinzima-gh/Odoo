# Předávka 2026-11-11: UX, přemostění, ochrana kurzů → další plány

**Cíl:** prototyp NAV na Odoo 20 (`addons/custom/`) uživatelsky přívětivý a auditovatelný; další na řadě plány bodů 10 a 9 podkladu UX.

**Stav:** větev `feature/nav-prototyp` (pushnuto na GitHub), poslední commit je ten s touto předávkou; `main` je pozadu (sloučení jen na pokyn uživatele).
Testy: 311 testů modulů Investry v `investra_test`, 0 failed. `investra_dev` aktualizovaný (entity, rates, fx), záloha `zalohy/investra_dev-pred-ochranou-kurzu-20261110-2242.dump`.

**Hotovo 10.–11. 11.:**
- AG-006 až AG-013 (Copilot) převzaty: nabídka podle práce, Nastavení → Účtování (účty rolí, role účtů, kurzy měn), seznamy, nápovědy, české názvy 153 polí.
- Přemostění kapitálu tříd (záložka Třídy podle příkladu uživatele, detail třídy, kontroly, list v balíčku).
- Vrácení a storno ocenění s důvodem (okno, ochrana proti navazujícímu ocenění).
- Zámek příloh ocenění + otisk balíčku (nález: přepsaný balíček zveřejněného ocenění).
- Ochrana kurzů: ruční kurz/přepis s důvodem (jen schvalovatel), zámek `res.currency.rate`, měsíční kurzy ČNB, upozornění v ocenění.
- `investra_test`: čeština pro uživatele, `admin` má přípravu i schvalování ocenění.

**Zbývá – první krok:** napsat plán bodu 10 (sdílené tržní ceny přes fondy, měna ceny) do `docs/navrh-sdilene-ceny.md` s variantami a doporučením; ke schválení uživatelem (červená zóna, model `investra.instrument.price` má povinné `fund_id`).
Pak: plán bodu 9 (klasifikace IFRS 9 na obchodu, rozhodnutí 9. 11.), test knihy se zdrojem ECB a měny mimo ECB, body 15, 8, 14, 16, 5.3, 3.

**Rozhodnutí (deník `docs/rozhodnuti.md`, 10.–11. 11.):** Struktura nabídky, Přepis kurzu, Ochrana kurzů, Přemostění kapitálu tříd,
Kurzy měn v nabídce, Stahování kurzů v investra_dev, Vrácení a storno ocenění, Zámek příloh ocenění, Předávka mezi relacemi.

**Otevřené otázky:** rozpad ostatních položek třídy (teď, nebo u prvního fondu); Community vs Enterprise a podklady pro start
Investra Services (strategicky důležitější než další obrazovky fondů); sloučení do `main`.

**Postupy:** převzetí práce Copilota/Antigravity viz `CLAUDE.md` (Role agentů); testy `-u <moduly> --test-enable --test-tags /<moduly>`
nad `investra_test`, kurzy v testech jen ve vlastním roce; po změně Pythonu restart `investra-test-web` (se souhlasem).

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md`
4. `docs/predavka-2026-11-10-ux.md` (body podkladu UX 3–16)
5. `addons/custom/investra_instruments/models/instrument.py` (třída `InvestraInstrumentPrice`)
