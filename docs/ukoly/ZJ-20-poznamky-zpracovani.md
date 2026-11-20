# ZJ-20 Poznámky z průchodu (20. 11. 2026): zpracování a rozdělení úkolů

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | rozcestník; vlastní práce podle úkolů níže, nejpřísnější zóna platí u každého zvlášť |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (po sloučení do `main` nová větev z `main`) |
| Větev úkolu | `ukol/ZJ-20-poznamky` (jen dokumentace); kód v samostatných větvích úkolů |
| Zadal, dne | Martin, 2026-11-20 (poznámky po kontrole dávky ZJ-07 až ZJ-19) |
| Navazuje na | `docs/predavky/2026-11-20-davka-beh-7.md`, `docs/ukoly/CP-2026-11-20-ZJ-07-19-formulare.md` |

**Cíl:** Zpracovat sebrané poznámky najednou, sloučit příbuzné a rozdělit je podle agentů.

## Rozdělení poznámek

| # | Poznámka | Úkol | Kdo | Zóna |
|---|---|---|---|---|
| 1 | Jak smazat návrh obchodu (fond Alfa) | tento soubor, bod A | Claude | oranžová (`security`) |
| 2 | Pořadí polí: fond, třída, ostatní | AG-023 | Antigravity (revize Copilot) | zelená |
| 3 | ISIN v přehledech, filtrech, hledání | AG-024 (+ otevřená otázka na doplnění názvu) | Antigravity | zelená + oranžová |
| 4 + 6 | Daňové výjimky: šablona, univerzální %, nápověda Podíl | ZJ-23 | Claude (plán schvaluje Martin); texty Copilot | červená |
| 5 | Chyba záložky Daň | AG-025 | Antigravity | zelená |
| 6 (text) | Vysvětlení Podílu v UI a manuálu | CP-2026-11-20-dan-napoveda-podil | Copilot | zelená |
| 7 | Konec účetního období | tento soubor, bod B | Claude | oranžová/červená |
| 8 | Kurz poplatku z kurzového lístku | tento soubor, bod C | Claude | červená |
| 9 | Výsledek prodeje při prodeji | ZJ-21 | Claude (plán schvaluje Martin) | červená |
| 10 | Dividenda na cenný papír | ZJ-22 | Claude (plán schvaluje Martin) | červená |
| 11 | Ověření v prohlížeči: ex-kupón, FVOCI a OCI | otevřený bod (Martin) | Martin | – |
| 12 | Balíček pro depozitáře předělat | otevřený bod, plán později | Claude | červená |

**Sloučení:** poznámky 4 a 6 (jedno nastavení daňových výjimek), 3 a 10 (dividenda se zadává na cenný papír podle ISINu), 11 (dvě
ověření v prohlížeči).

**Pořadí práce:** AG-025, AG-023, AG-024 a CP (zelená, nezávislé) → body A až C tohoto souboru → ZJ-23 → ZJ-21 → ZJ-22.
ZJ-21 a ZJ-22 mění účtování a ocenění, proto až po stabilizaci formulářů a výjimek.

**Testy (Martin, 2026-11-20: nejdřív celé udělat, celkové testy až potom):** během práce se spouští jen nejnutnější kontrola
(instalace modulu a cílená třída testů změněného místa); `tools/run_tests.sh all` a snímek 35/39 jednou po dokončení všech
úkolů. U červených úkolů (ZJ-21, ZJ-22, ZJ-23) cílený test a snímek 35/39 i po každém, protože mění výpočet.

**Výjimka (Martin, 2026-11-20):** Copilot smí úkoly CP- spouštět i nad `~/odoo-dev` (stejně jako CP-2026-11-20-ZJ-07-19-formulare):
v zelené zóně, bez commitu a pushe, výsledek zapíše do `docs/ukoly/CP-*.md`; commit při převzetí dělá Claude.
Platí pro jednotlivé úkoly CP, ne trvale pro `CLAUDE.md`.

## A. Smazání návrhu obchodu (poznámka 1)

**Zjištění:** model smazání povoluje (`investra.trade.unlink` jen ve stavu Návrh bez události, `instrument.py` ř. ~1070), ale
`investra_instruments/security/ir.access.csv` dává uživatelům s rolí zpracovatele jen `cru` (bez `d`). Smazat tak jde jen jako
administrátor. Zjištěno z přístupových práv; v prohlížeči neověřeno.

**Návrh:** přidat právo `d` (smazat) pro `investra.trade` skupině zpracovatele; model dál smaže jen návrh (zaúčtovaný nebo
stornovaný obchod UI odmítne a odkáže na storno). Stejné ověřit u návrhu úpisu a odkupu, splátky, derivátu, dividendy.
**Ověření:** test, že zpracovatel smaže návrh a nesmaže zaúčtovaný obchod; ověření v prohlížeči u fondu Alfa.
**Rozhodnuto (Martin, 2026-11-20):** schvalovací matice (Nastavení › Schvalovací matice: Ne / čtyři oči / Kroky) existuje, ale mazání návrhu
v ní není činností a návrh nemá účetní dopad. Návrh smí smazat **kdokoli, kdo smí obchod vytvářet** (role zpracovatele), bez
schvalování. Mazání zaúčtovaného nebo stornovaného obchodu zůstává zakázané (storno a oprava dál podle matice `trade_reverse`).
**Zóna:** oranžová (`security/`).

## B. Konec účetního období (poznámka 7)

1. Pole **Konec účetního období** na formuláři fondu udělat editovatelné (den a měsíc) do prvního zaúčtovaného ocenění fondu;
   potom jen pro čtení. Hodnota se zapisuje do `res.company.fiscalyear_last_day/month` knihy fondu.
2. Opravit nápovědu pole a kapitolu „Účetní období“ v `docs/manual/02-fond.md`: Odoo 20 Community nemá viditelnou položku
   v nastavení účetnictví (jen úvodní průvodce); změna se dělá zde.
3. Ověření v UI; test změny před a po prvním ocenění.
**Zóna:** oranžová (`investra_fund`), kontrola zámku podle ocenění je v `investra_nav` (červená).

## C. Kurz poplatku z kurzového lístku (poznámka 8)

Předvyplnit `fee_fx_rate` stejně jako kurz obchodu (`trade_preview.py`, výchozí kurz podle data sjednání a měny poplatku), aby
uživatel zadával jen částku a měnu poplatku. U měny nástroje a funkční měny nic nepředvyplňovat (platí kurz obchodu, resp. 1).
Ověřit, v jakém případě systém kurz vyžadoval (Martin: u prodeje); doplnit test. **Zóna:** červená (`investra_nav/models`).

## Převzetí

Body A, B, C provedl Claude přímo ve větvi `ukol/ZJ-20-poznamky` (2026-11-20).

- **A:** právo `d` pro zpracovatele na `investra.trade`, `investra.instrument.repayment`, `investra.dividend`, `investra.derivative`
  (úpisy a odkupy ho měly). Model dál maže jen návrh. Test `investra_nav/tests/test_draft_delete.py`. Tlačítko Smazat v prohlížeči u fondu Alfa neověřeno.
- **B:** pole `fiscal_year_last_day` a `fiscal_year_last_month` (related na knihu, zápis přes `write` fondu se sudo, zpráva do chatteru);
  zámek `fiscal_year_locked` po prvním zaúčtovaném ocenění (stavy posted, sent, confirmed, published, reversed; návrh nezamyká) v `investra_nav/models/valuation.py`.
  Dosavadní pole `fiscal_year_end` zrušeno. Manuál `02-fond.md` opraven. Test `test_fund_fiscal_year_end.py`.
  Zjištění: účetní období bere výpočet z knihy při každém čtení, uložená ocenění se nepřepočítají (proto zámek).
- **C:** `trade_preview.py` `_onchange_fee_fx_rate`; třetí měna dostane kurz k datu sjednání, měna nástroje a funkční měna kurz 0.
  Ve kódu (`_check_fee`, `_fee_amounts`) žádný rozdíl mezi nákupem a prodejem není: kurz je povinný jen u měny jiné než nástroje a funkční.
  Test v `test_trade_fee.py`; manuál `06-portfolia-a-nastroje.md`.
- **Testy:** cílené (`TestTradeFee`, `TestFundFiscalYearEnd`, `TestDraftDelete`, `TestLaunchDate`) bez chyby; `all` po bodech A až C: 1197 testů, 0 selhání (2026-11-20; po dokončení dalších úkolů se `all` opakuje).
  Snímek 35/39 se nedělal (neměnily se výpočty; po dokončení všech úkolů).
- **Neověřeno v prohlížeči:** předvyplnění kurzu poplatku, úprava konce období a mazání návrhu. Pracovní `investra` zatím neupgradována
  (změna přístupových práv a pohledů se projeví až po povýšení modulů).
