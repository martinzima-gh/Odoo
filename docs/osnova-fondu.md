# Jednotná osnova fondů (pracovní návrh)

Stav 2026-11-07. Rámec: vyhláška č. 501/2002 Sb., případně IFRS podle knihy. Čísla účtů jsou **pracovní** a nemají oporu v předpisu;
prototyp je používá, aby šlo testovat. Pravidla pracují s rolemi, takže změna čísla nemění výpočty.
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
| 256000 | Účasti | 411000 | participation | 41 Dlouhodobé finanční investice | dělení rolí: krok 2 plánu | |
| – | (nový) Účasti oceňované RH do výsledku | 384000 | participation_fv (nová) | 38 | podle deníku 2026-11-11 | |
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

Poznámka ke skupině 59: příloha ji nazývá „Hospodářský výsledek ve schvalovacím řízení“. V Odoo je to účet nerozděleného
výsledku (`equity_unaffected`): nikdo na něj neúčtuje, rozvaha na něm ukazuje výsledek minulých let, který ještě nikdo nerozdělil, a výsledek běžného roku
dopočítá. Výsledek běžného roku se v Odoo nezavírá přes závěrkové účty (58), proto je 59 věcně nejbližší. Rozhodnutí z deníku platí.

Mimo rozsah tohoto kroku (k doplnění): podrozvaha (91–99, hlavně 98 hodnoty v úschově), opravné položky a rezervy (54, 65, 75),
časové rozlišení aktivní (35), neinvestiční část SICAV, dluhopisy v naběhlé hodnotě (41), opce (39).

### Rozhodnutí k otázkám (uživatel 2026-11-11)

1. Peníze na cestě ve 32, vnitřní zúčtování tříd ve 34.
2. Reverzní repo se dělí podle protistrany: banka nebo centrální banka (sektor ESA S.121, S.122) → 134000, ostatní → 212000.
3. Závazky z úpisu, odkupu a rozdílů vůči investorům ve 37.

## Plán přečíslování a migrace knih (návrh, červená zóna – čeká na schválení)

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
