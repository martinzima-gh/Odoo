# Jednotná osnova fondů (pracovní návrh)

Stav 2026-11-11. Rámec: vyhláška č. 501/2002 Sb., případně IFRS podle knihy. Čísla účtů jsou od 2026-11-11 podle skupin
směrné účtové osnovy (příloha č. 4), viz převodová tabulka níže. Pravidla pracují s rolemi, takže změna čísla nemění výpočty.
Vazbu na položky účetní závěrky a na výkazy ČNB je potřeba ověřit proti aktuálnímu znění vyhlášky, před zápisem do šablony.

## Zásady

- Jedna šablona `investra_fund`, šestimístné kódy, role účtu je povinná.
- Měna ani třída nejsou v čísle účtu: třída, část fondu, nástroj a typ pohybu jsou pole na řádku.
- Převzatý fond se převede převodovou tabulkou; původní číslo zůstává jako odkaz.

## Účty a role

Zdroj pravdy je `addons/custom/investra_chart_fund/data/template/account.account-investra_fund.csv` a mapování rolí v `template_investra_fund.py`.

| Skupina | Role |
|---|---|
| Peníze | bankovní účet, peníze na cestě |
| Investice | investiční nástroje |
| Pohledávky | obchodní, ostatní, vnitřní zúčtování tříd |
| Závazky | obchodní, úpis, odkup, úplaty, výkonnostní odměna, poplatky za úpis a odkup, vůči investorům z rozdílů, dohady, daň |
| Kapitál | kapitál tříd, výsledek minulých let, běžný výsledek |
| Výnosy | přecenění, kurzové, úroky, dividendy, ostatní, rozdíly ze zaokrouhlení úpisů a odkupů |
| Náklady | přecenění, kurzové, obhospodařování, administrace, depozitář, výkonnostní odměna, ostatní, rozdíly ze zaokrouhlení úpisů a odkupů, daň |

## Převodová tabulka podle přílohy č. 4 vyhlášky 501/2002 Sb. (návrh 2026-11-11)

Podklad: text přílohy č. 4 (Směrná účtová osnova) ověřil uživatel ve Sbírce 11. 11. 2026. Zásady: deník 2026-11-11
„Osnova fondů podle vyhlášky 501 – zásady přečíslování“. Kód = skupina (2 číslice) + syntetika + analytika.
Interní identifikátor (`ifa_*`), role, typ účtu i výpočty zůstávají; mění se jen `code`.
Pozor na posun tříd: dosud 5 = náklady a 6 = výnosy, nově **6 = náklady, 7 = výnosy, 5 = kapitál**.
Žádný nový kód se nekryje se starým kódem jiného účtu, takže přečíslování proběhne v jednom kroku.

| Původní účet | Původní název | Nový účet | Role | Skupina 501 | Poznámka | Schválil |
|---|---|---|---|---|---|---|
| 221100 | Bankovní účty | 131100 | bank | 13 Vklady… za jinými bankami | prefix bankovních účtů 2211 → 1311; účet u ČNB by byl ve 12 | |
| (prefix 2111) | Pokladna | prefix 1111 | – | 11 Pokladní hodnoty | v šabloně jen prefix | |
| 261000 | Peníze na cestě | 322000 | cash_in_transit | 32 Pohl. a záv. z inkasa a ze zúčtování | i účet nevyjasněných plateb Odoo; prefix převodů 2611 → 3221 | uživatel 2026-11-11 |
| 251000 | Investiční nástroje | 381000 | instrument | 38 CP oceňované RH proti N/V | FVTPL | |
| 252000 | Dluhové cenné papíry | 382000 | instrument_debt | 38 | FVTPL; dluhopisy v naběhlé hodnotě patří do 41, nová role později | |
| 253000 | Termínované vklady | 133000 | deposit | 13 | | |
| 254000 | Reverzní repo | 134000 | repo | 13 | protistrana banka nebo centrální banka (sektor ESA S.121, S.122) | uživatel 2026-11-11 |
| – | (nový) Reverzní repo s nebankovní protistranou | 212000 | repo_client (nová) | 21 a 24 | ostatní sektory ESA | uživatel 2026-11-11 |
| 255000 | Poskytnuté úvěry | 211000 | loan_given | 21 a 24 Poskytnuté úvěry a jiné pohl. | | |
| 256000 | Účasti → Účasti oceňované reálnou hodnotou do výsledku | 384000 | participation_fv (nová) | 38 | účet ifa_256000 i se zůstatkem zůstává účastem v RH (všechny účasti jsou dnes FVTPL), takže se nic nepřeúčtovává | uživatel 2026-11-11 |
| – | (nový) Účasti | 411000 | participation | 41 Dlouhodobé finanční investice | nový účet ifa_411000 | uživatel 2026-11-11 |
| 257000 | Deriváty | 312000 | derivative | 31 Pevné termínové operace | opce do 39, nová role až s deriváty (odloženo) | |
| 258000 | Ostatní podíly | 385000 | other_holding | 38 | | |
| 378100 | Pohledávky z nevypořádaných obchodů | 371000 | unsettled_receivable | 37 Pohl. a záv. z obchodování s CP | | |
| 379100 | Závazky z nevypořádaných obchodů | 372000 | unsettled_payable | 37 | | |
| 378200 | Změna RH nevypořádaných obchodů | 373000 | unsettled_fair_value | 37 | | |
| 311000 | Pohledávky z obchodního styku | 341100 | (výchozí pohledávky Odoo) | 34 Ostatní pohl. a závazky | párovatelný | |
| 315000 | Ostatní pohledávky | 341200 | receivable_other | 34 | | |
| 395000 | Vnitřní zúčtování tříd | 349000 | internal_clearing | 34 | technický, saldo fondu 0 | uživatel 2026-11-11 |
| 321000 | Závazky z obchodního styku | 345100 | (výchozí závazky Odoo) | 34 | párovatelný | |
| 325300 | Závazek z úplat | 345300 | fee_payable | 34 | | |
| 325400 | Závazek z výkonnostní odměny | 345400 | performance_payable | 34 | | |
| 325500 | Závazek z poplatků za úpis a odkup | 345500 | subscription_fee_payable | 34 | příjemce obhospodařovatel nebo distributor | |
| 341000 | Daň z příjmů (závazek) | 346000 | tax_payable | 34 | | |
| 325100 | Závazek z úpisu | 374100 | subscription_payable | 37 …z emise vlastních CP | podílové listy a investiční akcie jsou vlastní CP fondu | uživatel 2026-11-11 |
| 325200 | Závazek z odkupu | 374200 | redemption_payable | 37 | | uživatel 2026-11-11 |
| 325600 | Závazek vůči investorům z rozdílů | 374300 | investor_rounding_payable | 37 | | uživatel 2026-11-11 |
| 389000 | Dohadné položky pasivní | 352000 | accrual | 35 Časové rozlišení, dohadné účty | | |
| – | (rezervováno) Zakladatelské akcie | 561000 | – | 56 Základní kapitál a kapitálové fondy | jen SICAV, až s ní | |
| 413000 | Kapitál tříd | 562000 | class_capital | 56 | | |
| 428000 | Výsledek minulých let | 571000 | retained_result | 57 Převedený HV | | |
| 431000 | Výsledek běžného období | 590000 | (nerozdělený výsledek Odoo) | 59 HV ve schvalovacím řízení | podle deníku; viz poznámka níže | |
| 662000 | Úrokové výnosy | 711000 | income_interest | 71 Výnosy z finančních činností | | |
| 665000 | Dividendové výnosy | 712000 | income_dividend | 71 | | |
| 611000 | Zisk z přecenění na RH | 713000 | gain_fair_value | 71 | | |
| 663000 | Kurzové zisky | 714000 | gain_fx | 71 | i kurzový výnos společnosti | |
| 668000 | Ostatní výnosy | 761000 | income_other | 76 Ostatní provozní výnosy | i výchozí výnosový účet | |
| 668100 | Rozdíly ze zaokrouhlení – výnos | 761100 | rounding_gain | 76 | | |
| 511000 | Ztráta z přecenění na RH | 613000 | loss_fair_value | 61 Náklady na finanční činnosti | | |
| 563000 | Kurzové ztráty | 614000 | loss_fx | 61 | i kurzový náklad společnosti | |
| 518100 | Úplata za obhospodařování | 631100 | expense_management | 63 Správní náklady | | |
| 518200 | Úplata za administraci | 631200 | expense_administration | 63 | | |
| 518300 | Úplata depozitáři | 631300 | expense_depositary | 63 | | |
| 518400 | Výkonnostní odměna | 631400 | expense_performance | 63 | | |
| 548000 | Ostatní náklady | 661000 | expense_other | 66 Ostatní provozní náklady | i výchozí nákladový účet | |
| 548100 | Rozdíly ze zaokrouhlení – náklad | 661100 | rounding_loss | 66 | | |
| 591000 | Daň z příjmů (náklad) | 681000 | expense_tax | 68 Daň z příjmů | | |

Účty, které zakládá Odoo mimo šablonu (přečísluje je migrace; nové knihy je dostanou ze šablony):

| Původní účet | Původní název | Nový účet | Skupina 501 | Poznámka |
|---|---|---|---|---|
| 2211xx | Bank, Outstanding Receipts, Outstanding Payments | 1311xx | 13 | prefix bankovních účtů |
| 2611xx | Funds in Transit | 3221xx | 32 | prefix převodů |
| 999001 / 999002 | Cash Difference Gain / Loss | 761901 / 661901 | 76 / 66 | třída 9 je podle přílohy č. 4 podrozvaha |
| 999997 / 999998 | Cash Discount Gain / Loss | 761902 / 661902 | 76 / 66 | totéž |

Poznámka ke skupině 59: příloha ji nazývá „Hospodářský výsledek ve schvalovacím řízení“. V Odoo je to účet nerozděleného
výsledku (`equity_unaffected`): nikdo na něj neúčtuje, rozvaha na něm ukazuje výsledek minulých let, který ještě nikdo nerozdělil, a výsledek běžného roku
dopočítá. Výsledek běžného roku se v Odoo nezavírá přes závěrkové účty (58), proto je 59 věcně nejbližší. Rozhodnutí z deníku platí.

Mimo rozsah tohoto kroku (k doplnění): podrozvaha (91–99, hlavně 98 hodnoty v úschově), opravné položky a rezervy (54, 65, 75),
časové rozlišení aktivní (35), neinvestiční část SICAV, dluhopisy v naběhlé hodnotě (41), opce (39).

### Rozhodnutí k otázkám (uživatel 2026-11-11)

1. Peníze na cestě ve 32, vnitřní zúčtování tříd ve 34.
2. Reverzní repo se dělí podle protistrany: banka nebo centrální banka (sektor ESA S.121, S.122) → 134000, ostatní → 212000.
3. Závazky z úpisu, odkupu a rozdílů vůči investorům ve 37.

## Plán přečíslování a migrace knih (schválen a proveden 2026-11-11)

Účetní dopad: žádný doklad se nemění ani neúčtuje. Řádky dokladů odkazují na účet přes id, takže se změní jen
číslo, pod kterým se zobrazují. Výkazy ČNB jsou mapované přes role (`investra.cnb.map`), přečíslování je nezasáhne.

1. **Šablona** (`investra_chart_fund` 20.0.0.3.0): nové kódy v CSV, prefixy 1311 / 1111 / 3221 v `template_investra_fund.py`.
   `ROLE_ACCOUNTS` se nemění, protože odkazuje na `ifa_*`.
2. **Dělení repa:** nová role `repo_client` (212000). Roli navrhne zařazení nástroje podle sektoru ESA protistrany repa
   (S.121, S.122 → `repo`, jinak `repo_client`); nesoulad role a sektoru ukáže kontrola ocenění jako upozornění.
   Stávající zařazení repa převede migrace stejným pravidlem.
3. **Dělení účastí:** nová role `participation_fv` (384000). Zařazení nástroje (IFRS 9) vybere roli podle kategorie:
   FVTPL → 384000, ostatní → 411000. Mapování ČNB pro novou roli navrhne Claude a potvrdí metodik.
4. **Migrace** (post-migration 20.0.0.3.0, přes ORM `with_company`):
   - pojistka: pokud je v knize ocenění ve stavu Ke schválení nebo Schváleno, migrace skončí chybou. Otisk
     (`valuation.py`, `_fingerprint`) obsahuje číslo účtu a porovnává se při zaúčtování; zaúčtovaná ocenění se znovu nekontrolují;
   - účet podle xmlid `account.<id společnosti>_ifa_*` dostane nový kód. Musí to proběhnout **před** `_ensure_fund_accounts`, protože
     ta hledá účet nejdřív podle kódu a jinak by založila duplikát;
   - bankovní, pokladní a převodové účty založené mimo šablonu (kódy 2211xx, 2111xx, 2611xx) dostanou nový prefix; na společnosti se
     přepíšou prefixy;
   - původní kód se zapíše do chatteru účtu jako odkaz („Původní číslo 251000, přečíslováno podle osnovy 501“).
5. **Testy:** všech 13 modulů v `investra_test`; testy pracují s rolemi, natvrdo zapsaná čísla fondových účtů v kódu nejsou.
6. **Ověření na kopii `investra_test`:** předvaha před migrací a po ní podle id účtu (počet účtů, obraty MD/D, zůstatky – musí sedět
   na haléř); kontrola, že žádný účet fondové knihy nemá starý kód; výkazy ČNB před a po beze změny; vybrané ocenění přepočítat
   a porovnat NAV.
7. Teprve potom aktualizace modulu v `investra_test` (se souhlasem), restart `investra-test-web`; `investra_dev` zvlášť se zálohou
   (`investra_nav` tam není nainstalovaný, fondové knihy ověřit dotazem).

Volitelně (samostatný plán): otisk ocenění převést z čísla účtu na roli. Pojistka pak nebude potřeba.

### Provedení 2026-11-11

- Moduly: `investra_entity` 20.0.0.3.0 (role `repo_client`, `participation_fv`), `investra_chart_fund` 20.0.0.3.0 (šablona,
  migrace), `investra_instruments` 20.0.0.8.0 (návrh role podle kategorie), `investra_counterparty` 20.0.0.2.0 (repo podle
  sektoru), `investra_cnb` 20.0.0.3.0, `investra_nav` (kontrola „Zařazení pozic odpovídá návrhu“, upozornění).
- Odchylky od plánu: (1) účasti obráceně, než uváděla první verze tabulky: stávající účet `ifa_256000` nese účasti v RH (384000)
  a pro roli účastí ve 41 je nový účet, aby se zůstatky nepřesouvaly; (2) navíc přečíslovány pomocné účty Odoo 999xxx
  (třída 9 je podrozvaha) a šablona je nastaví sama; (3) kontrola ocenění ukazuje každou odchylku zařazení od návrhu
  (role i způsob ocenění), ne jen repo; (4) mapování ČNB nových rolí je stejné jako u původních rolí (repo řádek 11 / RIS30 9,
  účasti řádek 14 / RIS30 10). Zda účasti v RH nepatří na ROFO10_11 řádek 6 nebo 7, potvrdí metodik.
- Ověření na kopii `investra_test`: předvaha podle id účtu shodná (37 řádků, MD, D, zůstatek, částka v měně); 51 účtů v každé
  z 5 knih přečíslováno, přibyly 212000 a 411000; všechny role mapované na účet i do ČNB; NAV pěti přepočtených ocenění
  shodné se základem bez migrace (porovnáno se starým kódem); testy 432 / 0 chyb ve 13 modulech; referenční scénáře 55 OK.
- `investra_test`: 5 ocenění Ke schválení vráceno s důvodem „Přečíslování osnovy podle vyhlášky 501“ (rozhodl uživatel),
  záloha `zalohy/investra_test-2026-11-11-pred-osnovou-501.dump`, aktualizace modulů, předvaha shodná, web 8071 restartován.
- Zjištěno mimo migraci: ukázkový dluhopis má v zařazení roli `instrument` místo `instrument_debt` z typu (nová kontrola
  ho ukazuje); ocenění fondu Beta k 2026-10-31 nejde přepočítat pro chybějící schválenou cenu dluhopisu (stav ukázkových dat);
  fond Ukázkový k 2027-02-28 dává po přepočtu cenu CZK 1,0021 místo dřívějších 1,0020 i se starým kódem (posun dat od 8. 11.).
- Oprava ukázkových dat `investra_test` (souhlas uživatele 2026-11-11, záloha
  `zalohy/investra_test-2026-11-11-pred-opravou-ukazkovych-dat.dump`): role dluhopisu změněna na `instrument_debt` ve třech
  zařazeních (fondy Ukázkový, Alfa, Beta; jako superuser, po obchodu je role zamčená, poznámka v historii zařazení) a zůstatek
  přeúčtován událostí „Ostatní“ z 381000 na 382000 (Ukázkový a Alfa 30 240 000 k 2027-02-01 kvůli uzávěrce k 2027-01-31,
  Beta 10 000 k 2026-10-04). Zveřejněná ocenění k 2027-01-31 zůstávají s účtem 381000. Fondu Beta doplněna cena dluhopisu
  k 2026-10-31 (10 000, zadal `beta_priprava`, schválil `beta_schvaleni`). Ověření: součet 381+382 v každé knize beze změny,
  FK konceptů 2027-02-28 shodné s výpočtem před opravou (Ukázkový 100 222 767,69, Alfa 31 111 205,69), Beta k 2026-10-31
  10 042 000 (= vrácená verze), kontrola zařazení bez upozornění; SELECT 8 v `docs/sql/11-klasifikace.sql`.
