# Předávka 2026-11-11: klasifikace IFRS 9 podle obchodního modelu fondu (bod 9 podkladu UX)

**Cíl:** prototyp NAV na Odoo 20 (`addons/custom/`); bod 9 hotový, další na řadě test knihy se zdrojem ECB a body 15, 8, 14, 16, 5.3, 3.

**Stav:** větev `feature/nav-prototyp` (pushnuto), poslední commit je ten s touto předávkou; `main` je pozadu (sloučení jen na pokyn).
Testy: 342 testů modulů Investry v `investra_test`, 0 chyb. `investra_test` je zmigrovaná (záloha před migrací
`zalohy/investra_test-2026-11-11-pred-klasifikaci.dump`). `investra_dev` se nic nedotklo.
Web `investra-test-web` (port 8071) běží se starým kódem: před prohlídkou restart se souhlasem uživatele.

**Hotovo 11. 11.:**
- Plán `docs/navrh-klasifikace-ifrs9.md` (varianta B) schválen a proveden; sekce Provedení a 6 odchylek v plánu.
- Nové modely `investra.fund.portfolio` (obchodní model) a `investra.portfolio.classification` (zařazení s platností od,
  SPPI, určení 4.1.5 / 5.7.5); obchod a splátka nesou portfolio; klasifikace z nástroje odstraněna, list ČNB na nástroji zůstal.
- Ocenění po pozicích nástroj + portfolio; ČNB bere kategorii ze zařazení; zařazení není v integritním hashi (odchylka 1).
- Deník, otevřené body, Claude Doc (revize 287), export `docs/architektura.md`, `docs/sql/11-klasifikace.sql`.

**Zbývá – první krok:** napsat test knihy se zdrojem ECB a měny mimo ECB (otevřený bod „Kniha se zdrojem ECB…“),
který potvrdí nebo vyvrátí míchání kurzů ČNB a ECB; řešení ke schválení zvlášť. Pak plány bodů 15, 8, 14, 16, 5.3, 3.

**Rozhodnutí:** „Obchodní model fondu a zařazení nástroje“ a „Klasifikace podle fondu – provedení“ (deník 2026-11-11).

**Otevřené otázky:** účtování FVOCI a chování ocenění s pozicí FVOCI do té doby; sloupec EFO0244 v DOFOS31;
reklasifikace (IFRS 9 4.4.1) jako samostatný krok; výchozí maximální stáří ceny u typů; Community vs Enterprise; sloučení do `main`.

**Postupy:** testy `-u <moduly> --test-enable --test-tags /<moduly>` nad `investra_test` (`docs/prototyp-nav.md`, Spuštění testů);
v testech zařazení přes `NavCase.classify()`; fond s více portfolii musí mít u obchodu portfolio.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/otevrene-body.md` (řádek Kniha se zdrojem ECB a měna mimo ECB)
4. `docs/navrh-ochrana-kurzu.md` (riziko 4)
5. `addons/custom/investra_rates/models/rate.py`
