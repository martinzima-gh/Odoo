# Předávka 2026-11-11: zastavení ocenění nezaúčtovaným pohybem, osnova fondů podle 501

**Cíl:** zpřísnit kontrolu nezaúčtovaných úpisů a odkupů; navrhnout přečíslování osnovy fondů podle vyhlášky 501.

**Stav:** větev `feature/nav-prototyp`, commity „Nezaúčtovaný úpis nebo odkup zastaví ocenění“ (75f36d7)
a „Osnova fondů podle 501: zásady přečíslování“ (725f554), pushnuto.

**Hotovo:**
- `investra_nav/models/valuation.py`: kontrola `movements_posted` má výsledek Stop, ocenění nejde předložit.
  Testy upraveny (nový test zastavení, test zámku zaúčtuje pohyb před předložením).
- `investra_test`: 0 failed ze 428 testů všech 13 modulů; web 8071 restartován; čítač společností 6075.
- Deník (2 záznamy), Claude Doc rev 300, export `docs/architektura.md`.
- Zásady osnovy (rozhodl uživatel): úplaty skupina 63, běžný výsledek 59, účasti 41 (reálná hodnota do výsledku 38),
  přečíslovat hned; interní identifikátory účtů `ifa_*` zůstávají, mění se jen `code`.

**Zbývá – první krok:** ověřit doslovný text přílohy č. 4 vyhlášky 501/2002 Sb. (zakonyprolidi.cz ho při načtení
zkrátil; uživatel ověří ve Sbírce) a podle něj sestavit převodovou tabulku v `docs/osnova-fondu.md`.
Dál: rozdělit roli účasti (41 / 38 podle IFRS 9), nové účty (podrozvaha 9x, zakladatelské akcie 561),
přečíslování šablony a migrace knih přes ORM, mapování ČNB, porovnání předvahy před a po na kopii `investra_test`.

**Rozhodnutí:** deník 2026-11-11 „Nezaúčtovaný úpis nebo odkup zastaví ocenění“ a „Osnova fondů podle vyhlášky 501 –
zásady přečíslování“.

**Otevřené otázky:** závaznost tříd a skupin směrné osnovy (§ 66 neověřen doslovně); otisk ocenění
(`valuation.py`, `_fingerprint`) obsahuje číslo účtu – migraci nepouštět při ocenění mezi předložením
a zaúčtováním, nebo otisk převést na roli (červená zóna, plán ke schválení).

**Přečíst (nejvýš 5):**
1. `CLAUDE.md`
2. tato předávka
3. `docs/osnova-fondu.md`
4. `addons/custom/investra_chart_fund/models/template_investra_fund.py`
5. `addons/custom/investra_chart_fund/data/template/account.account-investra_fund.csv`
