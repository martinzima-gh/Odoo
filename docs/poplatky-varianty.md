# Úplaty a výkonnostní odměny: podporované varianty

Stav 2026-11-07. Katalog vznikl z veřejných statutů českých fondů a z obecných modelů trhu. Slouží k návrhu systému,
není to výklad ani doporučení výše úplat. Konkrétní fond se vždy nastavuje podle svého platného statutu.

Stav: **Hotovo** = v modulu a otestováno v Odoo. **Jádro** = umí výpočetní jádro a test, chybí pole nebo obrazovka.
**Mimo** = zatím se počítá mimo Odoo a částka se doloží. **Později** = vyžaduje další modul nebo data.

## Princip

Pravidlo se skládá z bloků, nepíše se vzorec na fond: **období a sazba v čase → základ → částka → kdo platí → kdo přijímá**.
Každý výpočet ukládá rozpis. Nová varianta je malé rozšíření s testem. Volné vzorce v nastavení záměrně nejsou kvůli auditu.

## Sazba v čase

| Varianta | Stav |
|---|---|
| Změna sazby během období, výpočet se rozdělí podle dnů | Hotovo |
| Sazbu určuje statutární orgán v mezích statutu, eviduje se rozhodnutí | Hotovo |
| Použitou verzi nejde přepsat, změna je nová verze s datem | Hotovo |
| Období bez platné sazby je chyba, nedomýšlí se | Hotovo |
| Konvence dnů: ACT/365, ACT/360, ACT/ACT (ISDA), 30E/360, 30/360 US, měsíce/12 | Hotovo |

## Zaokrouhlení kurzu

Výchozí počet desetinných míst a způsob (dolů, matematicky, nahoru) má fond, třída je může přepsat. V statutech se běžně objevují 4 místa dolů, u tříd v cizí měně i jiný počet. Hotovo.

## Úrokové konvence

Šest nejběžnějších konvencí trhu. Rozhoduje vždy statut, smlouva nebo emisní podmínky konkrétního nástroje; typické použití je orientační.

| Konvence | Typické použití | Stav |
|---|---|---|
| ACT/360 | Peněžní trh, depozita, repo, pohyblivé úroky; ověřeno u emise státního dluhopisu s pohyblivou sazbou | Hotovo |
| ACT/365 Fixed | Depozita a úvěry, úplaty fondů | Hotovo |
| ACT/ACT ISDA | Swapy, úroky přes přestupný rok | Hotovo |
| ACT/ACT ICMA | Dluhopisy, počítá se v rámci kupónového období | Jádro, potřebuje kupónový kalendář nástroje |
| 30E/360 | Eurobondy | Hotovo |
| 30/360 US | Americké dluhopisy | Hotovo |

## Úplata za obhospodařování, administraci a depozitáři

| Varianta | Příklad z praxe | Stav |
|---|---|---|
| Procento p. a. z FK | 0,1 až 2 % | Hotovo |
| Z hrubého FK před úplatou, nebo z FK po úplatě (kruhový výpočet) | „před odměnou za správu“ | Hotovo |
| Z kapitálu třídy, z aktiv | | Hotovo |
| Pevná částka měsíčně, poměrně nebo za každý započatý měsíc | 110 000 Kč měsíčně | Hotovo |
| Pevná částka plus procento z části nad práh | 58 000 Kč + 0,08 % nad 280 mil. | Hotovo |
| Klouzavá pásma, sazba jen na svou část základu | 0,30 % na 300–500 mil., 0,25 % na 500 mil.–1 mld. | Hotovo |
| Stupňová cena za započaté pásmo | 45 000 Kč + 10 000 Kč za každých dalších 500 mil. | Hotovo |
| Roční minimum a maximum | 0,1 %, min. 200 tis., max. 1,25 mil. | Hotovo |
| Příplatek za třídy nad určitý počet | + 10 000 Kč za pátou a další třídu | Hotovo |
| Průměrný FK od začátku roku, dohad v každém ocenění, doúčtování proti naúčtovanému | průměrná roční hodnota FK | Hotovo |
| Průměr z ocenění fondu: denní u denních fondů, měsíční u měsíčních | prostý průměr denních hodnot, průměr ke konci měsíců | Hotovo; jiná frekvence než ocenění chybí |
| Zálohová měsíční výplata a roční vyúčtování | | Platby později, dohad Hotovo |
| Úplata z hodnoty transakce | až 1 % z hodnoty transakce | Mimo |
| Skutečné náklady do ročního stropu | vnitřní audit do 350 tis. | Mimo, faktura a dohad |
| Úplata hrazena jen jednou při investici do vlastního fondu | | Mimo |
| Úvodní sleva na určité období | 25 000 Kč po dobu 6 měsíců | Hotovo novou verzí sazby |
| Úplata se nemusí účtovat, odpuštění | „může rozhodnout, že nebude účtována“ | Hotovo nulovou verzí |
| Rozdělení nákladu mezi podfondy podle počtu aktivních podfondů | | Mimo, později v SICAV |
| Záloha 90 % a doúčtování po známých parametrech | | Dohad, doúčtování fakturou |
| Základ z upsaného nebo investovaného kapitálu | fondy private equity | Mimo |
| DPH k úplatě | „+ DPH“ | Později, po rozhodnutí o režimu |

## Výkonnostní odměna

| Varianta | Příklad z praxe | Stav |
|---|---|---|
| High-water mark na kapitálu třídy, nebo na hodnotě kusu | 20 % z nové vyšší úrovně | Hotovo |
| Tvrdá překážka: odměna jen z části nad práh | 100 % nad 6,75 % p. a. | Hotovo |
| Vstupy a výstupy upravují srovnávací hodnotu, včetně práhu za dobu od toku | | Hotovo |
| Sazba 12 až 100 % | | Hotovo |
| Benchmark nebo index, marže nad index | 6M PRIBOR + 2,5 % | Hotovo |
| Odměna i při záporném výnosu, když fond překoná benchmark; nebo jen při kladném | | Hotovo |
| Měkká překážka s doháněním | běžné u private equity | Hotovo |
| Složený benchmark z více indexů | vážený index | Mimo, vstupem je výsledný index |
| Etalon odlišný po třídách a měnách | inflace ČSÚ a Eurostat plus marže | Hotovo, pravidlo na třídu; inflace jako řada hodnot |
| Etalon známý až po skončení období | roční inflace | Ověřit dohad v průběhu roku |
| Etalon třídy o rozdíl fixních úplat | 10 % p. a. + rozdíl sazeb | Hotovo ručně novou verzí |
| Záporný etalon se počítá jako nula | 30 % z kladné výkonnosti | Hotovo |
| HWM omezí odměnu, je-li blíž než etalon | | Hotovo |
| Krystalizace měsíčně, čtvrtletně, ročně, nikdy | | Hotovo |
| Dohad v každém ocenění, doplatek i záporný | | Hotovo |
| Krystalizace při odkupu | podíl dohadu na odkoupené kusy | Jádro |
| Odměna z průměrného NAV | 20 % z přebytku krát průměrný NAV | Jádro |
| Dohad vážený pravděpodobností | | Hotovo |
| Strop odměny | | Hotovo |
| Vzdání se části odměny do čistého výnosu | část se neuplatní pod 9 % p. a. | Jádro |
| High-on-high s klouzavým pětiletým obdobím (ESMA) | 5 % z přírůstku, reference zanikne po 5 letech bez odměny | Mimo, potřebuje historii kurzů; doplnit |
| Reset HWM po určité době | | Mimo |
| Vyrovnávací mechanismus po investorech | rovnost starých a nových investorů | Později, potřebuje data z IS, jinak Mimo |
| Série po datu vstupu | běžné v zahraničí | Později |
| Vodopád private equity, zpětné vrácení odměny | | Mimo |

## Přesuny mezi třídami

Výkonnostní odměna nemusí jít obhospodařovateli, ale jiné třídě. Přesun jde přes účet vnitřního zúčtování: FK fondu se nemění,
mění se jen podíly tříd a zápis zůstává dohledatelný.

| Varianta | Příklad z praxe | Stav |
|---|---|---|
| Odměna třídy je výnosem jiných tříd | 100 % přebytku třídy C tříd A a B | Hotovo |
| Část obhospodařovateli, část třídám | 50 % úplaty třídám, 50 % obhospodařovateli | Hotovo |
| Krytí nedosaženého výnosu z podřízené třídy do výše jejího kapitálu | třída nese rozdíl do 5,25 % | Hotovo |
| Pořadí vypořádání tříd | nejdřív jedna, pak druhá | Hotovo pořadím pravidel |
| Vydání nových akcií obhospodařovateli za odměnu | | Později, přes IS |

## Rozdělení mezi třídy

| Varianta | Příklad z praxe | Stav |
|---|---|---|
| Alokační poměr a specifické položky | běžné | Hotovo |
| Pořadí nároků: prioritní třída dostane cílový výnos, zbytek ostatní | 6 % p. a. prioritní, zbytek výkonnostní | Hotovo |
| Nedostatek na cíle: dělení poměrem cílů | | Hotovo |
| Zbytek částečně podle kapitálů, částečně v pevném poměru | 50 % a 74 : 26 | Hotovo |
| Ztrátu nese přednostně podřízená třída do vyčerpání | | Hotovo |
| Ztráta poměrem kapitálů | | Hotovo |
| Měnová oprava třídy, aby kurz neovlivnil výnos | | Mimo, řeší se v prototypu fondu |

## Výpočet mimo Odoo

Co nestojí za naprogramování, zůstává mimo Odoo, ale v postupu ocenění: pravidlo typu **Výpočet mimo Odoo s doložením**.
Účetní zadá částku, příloha s výpočtem a důvod jsou povinné, bez nich ocenění nejde spočítat. Částka prochází stejným schválením
a účtováním. Doporučení: nové pravidlo naprogramovat, až se opakuje u více fondů nebo tvoří podstatnou část nákladů.

## Největší fondy na trhu

Pokrytí je výběrové, ne úplné. U velkých retailových a nemovitostních fondů převažuje jednoduchý model: procento z průměrného FK nebo z aktiv, konkrétní sazba v mezích statutu a výkonnostní poplatek žádný nebo jen v určité třídě. Složité modely jsou hlavně u menších fondů kvalifikovaných investorů.

| Správce | Co bylo čteno | Závěr |
|---|---|---|
| ČSOB | Nemovitostní (speciální a FKI) | Nejvýše 2 % z průměru FK ke koncům měsíců, výkonnostní poplatek není |
| Česká spořitelna, Erste | Top Stocks, Fond řízených výnosů, Universum | Průměr denních hodnot, měsíční výplata, úplata jen jednou u vlastních fondů |
| REICO | Výroční zprávy, statut nenalezen | 1,75 % z průměrného kapitálu, data do roku 2018 až 2020 |
| Generali | Vyvážený, Konzervativní, Fond realit, přehled sazeb 2026 | Třídy se sazbou v čase, třída P s high-on-high 5 % a pětiletým obdobím |
| J&T, Amista | Naše Česko, J&T SICAV, IMOS, Thein, Rockaway, Alethes | Od žádné odměny po přesuny mezi třídami |
| Amundi | KB Portfolio | Benchmark po třídách, krystalizace při odkupu |
| Investika | Realitní fond, OK Smart Stability+ | Procento z aktiv, sazba podle třídy; PRIBOR a HWM čtvrtletně |
| Conseq | Active Invest, soukromé financování | Vzorec s toky, vážený dohad, hurdle PRIBOR plus marže |
| Partners | 13 statutů | Průměr FK, měsíční nebo roční etalon, inflace plus marže |
| Accolade | Jen klíčové informace | Výkonnostní poplatek se neuplatňuje |

## Otevřené

- Zjišťovat u přebíraných fondů, co používají, a podle toho doplnit stavy Mimo a Jádro.
- U dvou zadaných správců se veřejné statuty nepodařilo najít; REICO a Accolade jen ze zpráv a klíčových informací; statut ČSOB Akciový se nepodařilo přečíst.
- Odhad výkonnostní odměny v příkladu jednoho statutu nesouhlasí s uvedeným průměrným NAV: u podobných vzorců číst i příklady, ne jen text.

## Zdroje

Veřejné statuty a dokumenty, čteno 2026-11-07:
[AMBEAT II](https://www.codyainvest.cz/file/sdff-get?id=7377),
[REALIA Retail Parks](https://www.avantfunds.cz/wp-content/uploads/2020/06/statut_realia-podfond-retail-parks_kpia-final_dpia-final_signed.pdf),
[Thein Industry](https://www.amista.cz/files/thesic-theind/2022-05-10-thein-private-equity-podfond-industry-statut-amista-statut-p-.pdf),
[IMOS development](https://www.amista.cz/files/imos/2026-03-13-statut-imospf-p-.pdf),
[Alethes](https://www.amista.cz/files/investovani/statut-fondu-a-podfondu-alethes.pdf),
[OK Smart Stability+](https://www.investika.cz/files/statut-okss-20260515-clear.pdf),
[Double Speed, Partners](https://www.partnersis.cz/data/files/catalogueg-products-files/39/statut-double-speed-final-630-1239.pdf),
[Conseq Active Invest](https://www.conseq.cz/getmedia/0fdc2b06-c80e-4b2e-9ef3-6766d5a4db88/Statut_CFISSICAV_Dodatek_CSQActiveInvestDynamicky.aspx?ext=.pdf),
[KB Portfolio, Amundi](https://www.amundi-kb.cz/storage/app/media/A_Statuty/Statut_CZ0008473162.pdf),
[Trigea](https://www.trigea.cz/userfiles/statut-trigea-20240229-final.pdf),
[Czech Power Stability Fund](https://www.cpsfund.cz/wp-content/uploads/2024/11/Czech-Power-Stability-Fund-podfond-_Statut.pdf),
[Residento](https://www.cyrrusis.cz/assets/0b505fe8-703f-45d3-acc2-0b2533723930),
[Top Stocks, Erste](https://data.erste-am.com/gem/erste-am/getDocumentContent/7668c768-b8b0-404e-a6ed-6c3d35dca12e),
[Findigo](https://findigofki.cz/),
[Ascavia](https://ascavia.cz/pro-investory/),
[Fondefi](https://www.fondefi.cz/informace-pro-investory/),
[fondy Partners investiční společnosti](https://www.partnersis.cz/nase-fondy), 13 statutů včetně Universe, 7 Stars, Bond Opportunity, Simplea a Aspire,
[Generali Fond vyvážený](https://www.generali-investments.cz/media/generali/docs/STAT_CZ0008474806_FV_20250203.pdf),
[přehled sazeb Generali 2026](https://www.generali-investments.cz/media/generali/docs/informace-aktualni-vysi-vyse-uplaty-za-obhospodarovani-a-vyse-sazby-vykonnostniho-poplatku-pro-fondy-spravovane-generali-investments-cee-01-2026-69551dc9b9f18.pdf),
[ČSOB Nemovitostní](https://is.patria.cz/strapi/uploads/CSOB_Nemovitostni_Statut_specialni_fond_final_draft_signed_482c3f371c.pdf),
[Fond řízených výnosů, Erste](https://data.erste-am.com/gem/erste-am/getDocumentContent/dce1ddcc-d7c8-4309-aeb8-9517ba5c149e),
[INVESTIKA realitní fond](https://www.investika.cz/files/statut-irf.pdf),
[ČS nemovitostní fond, výroční zpráva](https://www.reico.cz/content/dam/cz/csas/www_reico_cz/dokumenty/vyrocni-zpravy/CSNF/CSNF%20VZ%202018%20FINAL_LR.pdf).
Úrokové konvence: [emisní podmínky státních dluhopisů, MF](https://mfcr.cz/assets/attachments/2025-05-29_Emisni-podminky-pro-Statni-dluhopis-Ceske-republiky-2025-2038.pdf),
[Day count convention](https://en.wikipedia.org/wiki/Day_count_convention), [ACT Wiki](https://wiki.treasurers.org/wiki/ACT/360).
Obecné modely: [ESMA Guidelines on performance fees](https://www.esma.europa.eu/sites/default/files/library/esma34-39-992%5Fguidelines%5Fon%5Fperformance%5Ffees%5Fen.pdf),
[SS&C: Series vs Equalization](https://www.ssctech.com/blog/understanding-performance-fees-in-hedge-funds-series-vs-equalization),
[Alter Domus: Private equity waterfalls](https://alterdomus.com/insight/private-equity-waterfall/).
Pořadí největších správců podle [AKAT, přes Investiční web](https://www.investicniweb.cz/podilove-fondy/327728-investice-v-cesku-prekonaly-v-pololeti-ctyri-biliony-korun-lakaji-hlavne-akcie) je z neověřeného období.
