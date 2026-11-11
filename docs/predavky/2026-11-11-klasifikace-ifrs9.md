# Předávka 2026-11-11: klasifikace IFRS 9 podle obchodního modelu fondu (bod 9 podkladu UX)

**Cíl:** prototyp NAV na Odoo 20 (`addons/custom/`); bod 9 hotový, další na řadě test knihy se zdrojem ECB a body 15, 8, 14, 16, 5.3, 3.

**Stav:** větev `feature/nav-prototyp` (pushnuto), poslední commit je ten s touto předávkou; `main` je pozadu (sloučení jen na pokyn).
Testy: 351 testů modulů Investry v `investra_test`, 0 chyb. `investra_test` je na `investra_instruments` 20.0.0.5.0
(zálohy `zalohy/investra_test-2026-11-11-pred-klasifikaci.dump` a `…-pred-dodatkem-ifrs9.dump`). `investra_dev` beze změny.
Web `investra-test-web` (port 8071) běží s novým kódem. Souběžně jiná relace pracuje na kurzech (necommitnuté soubory nechat).

**Hotovo 11. 11.:**
- Plán `docs/navrh-klasifikace-ifrs9.md` (varianta B) schválen a proveden; sekce Provedení a 6 odchylek v plánu.
- Nové modely `investra.fund.portfolio` (obchodní model) a `investra.portfolio.classification` (zařazení s platností od,
  SPPI, určení 4.1.5 / 5.7.5); obchod a splátka nesou portfolio; klasifikace z nástroje odstraněna, list ČNB na nástroji zůstal.
- Ocenění po pozicích nástroj + portfolio; ČNB bere kategorii ze zařazení; zařazení není v integritním hashi (odchylka 1).
- Deník, otevřené body, Claude Doc (revize 287), export `docs/architektura.md`, `docs/sql/11-klasifikace.sql`.
- Dodatek (plán, sekce Dodatek a Provedení dodatku): zařazení po krocích (a) povaha, (b) SPPI se zněním (EU) 2025/1047,
  (c) obchodní model (Řízení na RH, Obchodování), (d) povinná, (e) určení/volba, (f) výsledek se zdůvodněním;
  ruční přepsání kategorie se zdůvodněním a upozorněním v ocenění; jen kombinace přípustné podle IFRS 9.

**Zbývá – první krok:** prohlédnout s uživatelem formulář zařazení v prohlížeči (port 8071) a ověřit, že nabízí jen
přípustné volby (mezera 5 neprověřena v UI). Pak: potvrzení SPPI u migrovaného vkladu, primární ověření (EU) 2025/1047,
plány bodů 15, 8, 14, 16, 5.3, 3 (kurzy řeší jiná relace).

**Rozhodnutí:** „Obchodní model fondu a zařazení nástroje“, „Klasifikace podle fondu – provedení“ a
„Klasifikace IFRS 9 po krocích (a)–(f)“ (deník 2026-11-11).

**Otevřené otázky:** účtování FVOCI a chování ocenění s pozicí FVOCI do té doby; sloupec EFO0244 v DOFOS31;
reklasifikace (IFRS 9 4.4.1) jako samostatný krok; výchozí maximální stáří ceny u typů; Community vs Enterprise; sloučení do `main`.

**Postupy:** testy `-u <moduly> --test-enable --test-tags /<moduly>` nad `investra_test` (`docs/prototyp-nav.md`, Spuštění testů);
v testech zařazení přes `NavCase.classify()`; fond s více portfolii musí mít u obchodu portfolio.

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-klasifikace-ifrs9.md` (sekce Dodatek a Provedení dodatku)
4. `addons/custom/investra_instruments/models/portfolio.py`
5. `docs/otevrene-body.md` (řádky Primární ověření novely IFRS 9 a Potvrzení SPPI)
