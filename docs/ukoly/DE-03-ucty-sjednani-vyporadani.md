# DE-03 FX derivát: účty a role, sjednání, vypořádání, storno

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, osnova, role) – plán schvaluje Martin v promptu |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Opus |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Podrozvaha, Účtování, Příklad, Neověřeno a otevřené), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** sjednání zapíše podrozvahu, vypořádání nohy zaúčtuje peněžní toky a zruší reálnou hodnotu, storno vše vrátí;
vždy s náhledem zaúčtování a záložkou dokladů.

**Schválený plán** (návrh Clauda; plán schválil Martin v promptu relace 15. 11. 2026, čísla účtů 16. 11. 2026):

1. **Ověření předpisů před kódem:** v primárním zdroji (Sbírka zákonů, MF) ověřit požadavky vyhlášky č. 501/2002 Sb.
   a ČÚS pro finanční instituce na podrozvahu u pevných termínových operací a na vykazování kladné a záporné RH
   derivátů; uvést paragraf nebo bod. Co ověřit nejde, označit. Při rozporu s návrhem se zastavit.
2. **Role** (`investra_entity`): `derivative_liability` (závazek), `gain_derivative`, `loss_derivative`,
   `offbalance_forward_receivable`, `offbalance_forward_payable`, `offbalance_clearing`.
3. **Účty:** navrhnout čísla a názvy v osnově `investra_fund` podle směrné účtové osnovy (podrozvaha typu
   `off_balance`), **předložit Martinovi ke schválení a počkat**; teprve pak doplnit šablonu osnovy a funkci, která
   účty a přiřazení rolí založí ve stávajících knihách přes ORM (žádné SQL). Výchozí přiřazení rolí pro nové knihy.
4. **Sjednat** (stav Návrh → Sjednáno): uloží na nohu `B0` a kurzy dne sjednání, zapíše podrozvahu každé nohy.
   Přes schvalovací matici stejně jako obchod.
5. **Vypořádat nohu** (v den vypořádání nebo později, ne před): dopočet RH na `V` kurzem dne vypořádání, oba
   peněžní toky na bankovních účtech fondu v příslušných měnách (uživatel vybere účty), zrušení RH, odúčtování
   podrozvahy nohy. Po poslední noze stav Vypořádáno. Blízká noha swapu stejným postupem.
6. **Storno** smlouvy nebo vypořádání s důvodem přes `_reverse_events`; zámek ocenění platí jako u obchodu.
7. Náhled a záložka dokladů zděděním `investra.posting.preview` (vzor `investra_nav/models/trade_preview.py`).
8. Testy podle návrhu (sjednání, storno, vypořádání podle příkladu na haléř, FK se podrozvahou nemění, fond v EUR).

**Rozsah souborů:** `investra_derivative/`, `investra_entity/data` (role), `investra_chart_fund` (účty, verze,
případná migrace), `docs/rozhodnuti.md`, `docs/navrh-fx-derivaty.md` (jen doplnění ověřených citací), tento soubor.

**Mimo rozsah:** výpočet RH při ocenění (DE-04), výkazy ČNB, ukázková data, nasazení do `investra`.

**Kritéria přijetí:** citace předpisů ověřené nebo označené; čísla účtů schválená Martinem (zapsat datum); testy
`all` na dočasné databázi bez selhání; MD = D u každého dokladu; po stornu nulové zůstatky podrozvahy i RH.

## Výsledek

Provedl Claude Code (hlavní relace) 16. 11. 2026, větev `etapa/derivaty`.

- **Ověření předpisů (bod 1):** vyhláška č. 501/2002 Sb. § 35 a § 41 (podrozvahové pohledávky a závazky ze spotových
  operací, pevných termínových operací a opcí, v hodnotách podkladových nástrojů; § 35 odst. 2 od sjednání nebo od
  vypořádání), § 14 odst. 1 a § 20 odst. 1 (kladná a záporná RH derivátů v ostatních aktivech a pasivech), § 47
  odst. 1 (zisk nebo ztráta z finančních operací); ČÚS pro finanční instituce č. 110 body 1 c), 4, 7–11, č. 105
  bod 3, společná ustanovení k osnově třída 3 bod 2 b), třída 9 body 3, 7, 8 a 12. Zdroje: zakonyprolidi.cz (znění
  účinné od 1. 1. 2024; e-Sbírka nešla strojově načíst), úplné znění standardů MF 2017 (mf.gov.cz). Rozpor s návrhem
  nenalezen; jediná odchylka je technická (dva doklady při vypořádání, viz níže).
- **Čísla účtů (bod 3):** syntetiku určil Martin 16. 11. 2026 v relaci (313, 619 / 719, 953 / 954; spot 358,
  616 / 716, 943 / 944; swap stejně na jiných účtech), analytiky a účty 313100, 313300, 358200, 992000 doplnil
  Claude; tabulka je v deníku rozhodnutí („Účty FX spotu, forwardu a swapu“).
- **Změněné soubory:** `investra_entity` (`data/account_role.xml` 18 rolí, `models/account_role.py` druh role
  Podrozvaha, verze 20.0.0.9.0); `investra_chart_fund` (šablona CSV 18 účtů a přejmenování 313000, `ROLE_ACCOUNTS`,
  migrace `20.0.0.9.0`, test osnovy, verze 20.0.0.9.0); `investra_derivative` (`calc.py`, `models/posting.py`,
  `models/wizard.py`, pohledy, práva, testy `test_calc.py`, `test_posting.py`, verze 20.0.0.2.0);
  `investra_cnb/tests/test_cnb_map.py`; `docs/rozhodnuti.md`, `docs/navrh-fx-derivaty.md`, tento soubor.
- **Ověřeno (příkaz a výsledek):** `tools/run_tests.sh investra_derivative,investra_chart_fund,investra_entity` →
  0 failed, 0 error(s) of 51 tests; `tools/run_tests.sh all` → 0 failed, 0 error(s) of 720 tests (dočasné `investra_ci_*`, smazány). Testy: sjednání zapíše jen podrozvahu
  podle příkladu (MD 953100 24 900 000, D 954100 25 000 000, MD 992000 100 000) a FK se nezmění; vypořádání podle
  příkladu na haléř; náhled = doklad; swap po nohách; spot na vlastních účtech; storno smlouvy a storno vypořádání
  s nulovými zůstatky podrozvahy i RH; zámek ocenění; fond v EUR; MD = D u všech dokladů i storen.
- **Odchylky od zadání:**
  - Vypořádání nohy tvoří **dva doklady** (rozvahový a podrozvahový), protože Odoo odmítne doklad kombinující
    podrozvahové a ostatní účty; stornují se společně.
  - Role účtů dostaly nový druh „Podrozvaha“ (změna modelu v `investra_entity`, nejen dat).
  - Vypořádání se účtuje vždy k datu vypořádání nohy kurzem toho dne; tlačítko jde stisknout nejdřív ten den.
  - Storno a storno vypořádání jdou přes stávající činnost matice „Storno a oprava obchodu“; Sjednat a Vypořádat
    smí zpracovatel bez matice, stejně jako Zaúčtovat a Vypořádat u obchodu.
  - Test `investra_cnb` „každá role osnovy je v převodové tabulce“ má výjimku pro nové role (mapování je DE-05 / CN).
- **Neověřeno:** migrace osnovy `20.0.0.9.0` na databázi s daty (čistá testovací databáze migrace nespouští; zkouška
  patří na kopii ze zálohy v DE-05); vzhled formuláře a oken v prohlížeči; zda se na fond vztahuje výjimka z ČÚS 110
  (bod 37) a vazba § 4a vyhlášky na IFRS; novely vyhlášky po 1. 1. 2024.
- **Otevřené otázky a návrhy mimo rozsah:** mapování nových rolí na řádky výkazů ČNB (DE-05, CN); FX spot má nástroj
  typu Mimoburzovní derivát, ačkoli spot podle ČÚS 110 bod 1 c) derivátem není (dopad na list ČNB); kontrola délky
  spotu (do 2 dnů podle třídy 9 bod 7) se nedělá.

## Převzetí
