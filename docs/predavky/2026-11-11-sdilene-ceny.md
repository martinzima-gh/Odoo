# Předávka 2026-11-11: sdílené tržní ceny (bod 10 podkladu UX)

**Cíl:** prototyp NAV na Odoo 20 (`addons/custom/`); další na řadě plán bodu 9 podkladu UX (klasifikace IFRS 9 na obchodu).

**Stav:** větev `feature/nav-prototyp` (pushnuto), poslední commit je ten s touto předávkou; `main` je pozadu (sloučení jen na pokyn).
Testy: 328 testů modulů Investry v `investra_test`, 0 chyb. `investra_dev` modul nástrojů nemá, nic se tam neměnilo.
Web `investra-test-web` (port 8071) běží se starým kódem Pythonu: před prohlídkou v prohlížeči restart se souhlasem uživatele.

**Hotovo 11. 11.:**
- Plán `docs/navrh-sdilene-ceny.md` (varianta B) schválen a proveden, sekce Provedení a odchylky v plánu.
- Cena bez fondu = sdílená tržní cena v knize investiční společnosti (dokud kniha neexistuje, sdílenou cenu zadat nejde);
  cena fondu s důvodem odchylky; měna ceny = měna nástroje; 8 desetinných míst beze změny.
- Ocenění: poslední známá schválená cena, kontroly `price_age` a `price_fund_deviation` (Upozornění), `price_id` na řádku portfolia.
- Oprava schválené ceny vrací návrh ke schválení, formulář upozorní na ocenění, kde byla cena použita.
- Deník rozhodnutí, Claude Doc (řádek Sdílené tržní ceny, revize 284), export `docs/architektura.md`, `docs/sql/10-ceny.sql`.

**Zbývá – první krok:** napsat plán bodu 9 (klasifikace IFRS 9, způsob ocenění a role účtu z nástroje na obchod / obchodní model
fondu s platností od; rozhodnutí 2026-11-09) do `docs/navrh-klasifikace-ifrs9.md` s variantami; ke schválení uživatelem.
Pak: test knihy se zdrojem ECB a měny mimo ECB, body 15, 8, 14, 16, 5.3, 3.

**Rozhodnutí:** „Sdílené tržní ceny“ (deník 2026-11-11).

**Otevřené otázky:** výchozí maximální stáří ceny u typů nástrojů (uživatel); datum ceny v balíčku pro depozitáře;
rozpad ostatních položek třídy; Community vs Enterprise; sloučení do `main`.

**Postupy:** testy `-u <moduly> --test-enable --test-tags /<moduly>` nad `investra_test` (`docs/prototyp-nav.md`, Spuštění testů);
kurzy v testech jen ve vlastním roce (sdílené ceny používají 2032).

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (řádek Klasifikace podle fondu)
4. `docs/rozhodnuti.md` (záznam 2026-11-09 Klasifikace IFRS 9 podle fondu a obchodního modelu)
5. `addons/custom/investra_instruments/models/instrument.py` (třídy `InvestraInstrument`, `InvestraTrade`)
