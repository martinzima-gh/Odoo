# Syntetické účty pro rámec 501 (vnitřní standard)

Seznam dodal uživatel 2026-11-12 jako závazná čísla syntetických účtů pro knihy v rámci vyhlášky 501/2002 Sb.
(investiční společnost, fondy, podfondy, SICAV). Nadpis zdroje je „Účtová osnova pro banky“; názvy skupin odpovídají
příloze č. 4 vyhlášky 501. Zda jsou syntetické účty součástí předpisu, není ověřeno – v projektu je bereme jako vnitřní
standard. Skupina 25 (agendy z pověření, jen ČSOB) je vynechána na pokyn uživatele.

Kód účtu v Odoo: syntetický účet (3 číslice) + analytika (3 číslice). Knihy v rámci 500 (Investra Services) mají
vlastní osnovu a tento seznam se jich netýká. Převod šablony fondů: `docs/osnova-fondu.md`.

## Třída 1 – Pokladní a mezibankovní účty

| Účet | Název |
|---|---|
| **11** | **Pokladní hodnoty** |
| 111 | Pokladna |
| 113 | Zlato |
| 119 | Jiné pokladní hodnoty |
| **12** | **Vklady a úvěry u emisních bank, šekové poštovní účty** |
| 121 | Běžné účty u emisních bank |
| 122 | Účty peněžních rezerv u emisních bank |
| 123 | Poskytnuté úvěry emisním bankám |
| 124 | Šekové poštovní účty |
| 125 | Přijaté úvěry od emisních bank |
| 126 | Termínové vklady u emisních bank |
| 127 | Termínové vklady emisních bank |
| **13** | **Vklady, úvěry a ostatní pohledávky za jinými bankami** |
| 131 | Běžné účty u jiných bank |
| 132 | Termínové vklady u jiných bank |
| 133 | Poskytnuté úvěry jiným bankám |
| 134 | Běžné účty jiných bank |
| 135 | Ostatní pohledávky za jinými bankami |
| 136 | Termínové vklady jiných bank |
| 137 | Přijaté úvěry od jiných bank |
| 138 | Klasifikované úvěry, vklady a ostatní pohledávky za jinými bankami |
| 139 | Opravná položka ke klasifikovaným úvěrům, vkladům a ostatním pohledávkám za jinými bankami |
| **16** | **Závazky z jiných hodnot** |
| 163 | Závazky ve zlatě |
| 164 | Závazky z jiných hodnot |
| **17** | **Závazky z cenných papírů** |
| 171 | Závazky ze státních bezkuponových dluhopisů |
| 172 | Závazky z bezkuponových dluhopisů emisních bank |
| 173 | Závazky z bezkuponových dluhopisů |
| 174 | Závazky z akcií |
| 175 | Závazky z podílových listů |
| 176 | Závazky z ostatních bezkuponových dluhopisů |
| 177 | Závazky ze směnek |
| 178 | Závazky z cenných papírů zajištěných aktivy |

## Třída 2 – Účty klientů

| Účet | Název |
|---|---|
| **21** | **Standardní úvěry a ostatní pohledávky za klienty** |
| 212 | Ostatní pohledávky za klienty |
| 213 | Spotřební úvěry nekategorizované |
| 214 | Krátkodobé úvěry |
| 216 | Střednědobé úvěry |
| 218 | Dlouhodobé úvěry |
| 219 | Opravná položka ke spotřebním úvěrům nekategorizovaným |
| **22** | **Vklady klientů** |
| 221 | Běžné účty klientů |
| 223 | Vkladové certifikáty |
| 224 | Termínové vklady klientů s výpovědní lhůtou |
| 225 | Termínové vklady klientů se splatností |
| 226 | Úsporné vklady klientů na požádání |
| 227 | Úsporné vklady klientů se splatností |
| 228 | Úsporné vklady klientů s výpovědní lhůtou |
| 229 | Ostatní krátkodobé závazky vůči klientům |
| **23** | **Přijaté úvěry od klientů, orgánů státu a obdobných orgánů** |
| 231 | Přijaté úvěry od klientů |
| 232 | Přijaté úvěry od orgánů státu |
| 233 | Přijaté úvěry od územních samosprávných celků |
| 234 | Přijaté úvěry od veřejných fondů |
| 235 | Přijaté úvěry od státních fondů |
| **24** | **Klasifikované úvěry a ostatní pohledávky za klienty** |
| 241 | Sledované úvěry a ostatní pohledávky |
| 242 | Nestandardní úvěry a ostatní pohledávky |
| 243 | Pochybné úvěry a ostatní pohledávky |
| 244 | Ztrátové úvěry a ostatní pohledávky |
| 249 | Opravná položka ke klasifikovaným úvěrům a ostatním pohledávkám za klienty |
| **26** | **Emitované krátkodobé cenné papíry** |
| 262 | Dluhopisy |
| 263 | Vkladní listy |
| 264 | Směnky |
| **27** | **Účelové pohledávky a závazky vůči klientům** |
| 271 | Účelově vázané vklady |
| 272 | Ostatní účelové pohledávky a závazky |
| **28** | **Vklady, úvěry a ostatní pohledávky za orgány státu a obdobnými orgány** |
| 281 | Poskytnuté úvěry a ostatní pohledávky za orgány státu |
| 282 | Poskytnuté úvěry a ostatní pohledávky za územními samosprávnými celky |
| 283 | Poskytnuté úvěry a ostatní pohledávky za veřejnými fondy |
| 284 | Vklady veřejných fondů |
| 285 | Vklady mimorozpočtových prostředků orgánů státu |
| 287 | Vklady mimorozpočtových prostředků územních samosprávných celků |
| 288 | Vklady rozpočtových prostředků orgánů územních samosprávných celků |
| 289 | Opravná položka k úvěrům a ostatním pohledávkám |
| **29** | **Zúčtování s orgány státu a obdobnými orgány** |
| 291 | Rozpočtové příjmy rozpočtu územních samosprávných celků |
| 292 | Rozpočtové výdaje rozpočtu územních samosprávných celků |
| 297 | Státní fondy a jiná zúčtování s rozpočtem České republiky |

## Třída 3 – Cenné papíry, deriváty, ostatní pohledávky a závazky a přechodné účty

| Účet | Název |
|---|---|
| **30** | **Pevné termínové operace a opce s úvěrovými nástroji** |
| 301 | Pevné termínové operace s úvěrovými nástroji |
| 303 | Nakoupené opce na úvěrové nástroje |
| 304 | Prodané opce na úvěrové nástroje |
| **31** | **Pevné termínové operace** |
| 311 | Pevné termínové operace s úrokovými nástroji |
| 313 | Pevné termínové operace s měnovými nástroji |
| 315 | Pevné termínové operace s akciovými nástroji |
| 317 | Pevné termínové operace s komoditními nástroji |
| 319 | Zúčtování marží burzovních derivátů |
| **32** | **Pohledávky a závazky z inkasa a ze zúčtování** |
| 321 | Hodnoty k inkasu přijaté od korespondentů |
| 322 | Hodnoty k inkasu přijaté od klientů |
| 323 | Uspořádací účet pro zúčtování platebního styku |
| 325 | Účty korespondentů s připsáním platby po jejím inkasu |
| 326 | Účty klientů s připsáním platby po jejím inkasu |
| **33** | **Pobočky a jednatelství** |
| 331 | Tuzemské pobočky a jednatelství |
| 332 | Zahraniční pobočky a jednatelství – provozní prostředky |
| **34** | **Různé pohledávky a závazky** |
| 341 | Různí dlužníci |
| 342 | Různí věřitelé |
| 343 | Zúčtování se zaměstnanci |
| 344 | Poskytnuté provozní zálohy |
| 345 | Přijaté provozní zálohy |
| 346 | Zúčtování s orgány sociálního zabezpečení a zdravotními pojišťovnami |
| 347 | Zúčtování se státním rozpočtem |
| 348 | Odložená daňová pohledávka a závazek |
| 349 | Opravná položka k pohledávkám |
| **35** | **Časové rozlišení, dohadné položky, uspořádací účet** |
| 351 | Náklady příštích období |
| 352 | Příjmy příštích období |
| 353 | Dohadné účty aktivní |
| 354 | Dohadné účty pasivní |
| 355 | Výdaje příštích období |
| 356 | Výnosy příštích období |
| 358 | Uspořádací účet kurzových rozdílů |
| **36** | **Cenné papíry k prodeji** |
| 361 | Státní bezkuponové dluhopisy |
| 362 | Bezkuponové dluhopisy emisních bank |
| 363 | Kuponové dluhopisy |
| 364 | Akcie |
| 365 | Podílové listy |
| 366 | Ostatní bezkuponové dluhopisy |
| 367 | Směnky |
| 368 | Cenné papíry zajištěné aktivy |
| 369 | Opravná položka k cenným papírům k prodeji |
| **37** | **Pohledávky a závazky z obchodování s cennými papíry a z emise vlastních cenných papírů** |
| 371 | Zúčtování s trhem cenných papírů |
| 372 | Upsané cenné papíry určené k umístění na veřejnosti |
| 373 | Zúčtování s příkazci |
| 374 | Závazky z cenných papírů klientů svěřených do dispozice banky |
| 375 | Pohledávky za akcionáři |
| 376 | Závazky vůči akcionářům |
| 378 | Závazky z emitovaných dluhopisů |
| **38** | **Cenné papíry k obchodování** |
| 381 | Státní bezkuponové dluhopisy |
| 382 | Bezkuponové dluhopisy emisních bank |
| 383 | Kuponové dluhopisy |
| 384 | Akcie |
| 385 | Podílové listy |
| 386 | Ostatní bezkuponové dluhopisy |
| 387 | Směnky |
| 388 | Cenné papíry zajištěné aktivy |
| 389 | Opravná položka k cenným papírům k obchodování |
| **39** | **Opce** |
| 391 | Nakoupené opce na úrokové nástroje |
| 392 | Prodané opce na úrokové nástroje |
| 393 | Nakoupené opce na měnové nástroje |
| 394 | Prodané opce na měnové nástroje |
| 395 | Nakoupené opce na akciové nástroje |
| 396 | Prodané opce na akciové nástroje |
| 397 | Nakoupené opce na komoditní nástroje |
| 398 | Prodané opce na komoditní nástroje |

## Třída 4 – Nehmotný, hmotný majetek, účasti, cenné papíry držené do splatnosti, zahraniční pobočky a jednatelství

| Účet | Název |
|---|---|
| **41** | **Účasti, cenné papíry držené do splatnosti** |
| 411 | Směnky |
| 412 | Účasti s podstatným vlivem |
| 413 | Účasti s rozhodujícím vlivem |
| 414 | Cenné papíry zajištěné aktivy |
| 415 | Kuponové dluhopisy |
| 416 | Státní bezkuponové dluhopisy |
| 417 | Bezkuponové dluhopisy emisních bank |
| 418 | Ostatní bezkuponové dluhopisy |
| 419 | Opravná položka k účastem a cenným papírům drženým do splatnosti |
| **42** | **Zahraniční pobočky a jednatelství** |
| 421 | Prostředky dlouhodobě poskytnuté pobočkám a jednatelstvím v zahraničí |
| 424 | Poskytnuté dlouhodobé úvěry zvláštního charakteru pobočkám a jednatelstvím v zahraničí |
| 429 | Opravná položka k poskytnutým dlouhodobým úvěrům zvláštního charakteru |
| **43** | **Hmotný majetek** |
| 431 | Provozní hmotný majetek |
| 432 | Neprovozní hmotný majetek |
| 438 | Oprávky k hmotnému majetku |
| 439 | Opravná položka k hmotnému majetku |
| **44** | **Pořízení majetku** |
| 441 | Pořízení provozního hmotného majetku |
| 442 | Pořízení neprovozního hmotného majetku |
| 445 | Pořízení nehmotného majetku |
| 446 | Poskytnuté zálohy na pořízení majetku |
| 449 | Opravná položka k poskytnutým zálohám |
| **45** | **Hmotný majetek v leasingu** |
| 451 | Hmotný majetek v leasingu |
| 453 | Hmotný majetek po rozvázání leasingové smlouvy |
| 458 | Oprávky k hmotnému majetku v leasingu |
| **47** | **Nehmotný majetek** |
| 473 | Goodwill |
| 474 | Software |
| 475 | Zřizovací výdaje |
| 476 | Ostatní nehmotný majetek |
| 478 | Oprávky k nehmotnému majetku |
| 479 | Opravná položka k nehmotnému majetku |
| **48** | **Zásoby** |
| 480 | Zásoby |

## Třída 5 – Kapitálové účty, dlouhodobé závazky a závěrkové účty

| Účet | Název |
|---|---|
| **50** | **Dotace a obdobné prostředky** |
| 501 | Dotace |
| 507 | Prostředky obdobné dotacím |
| **52** | **Emitované dlouhodobé cenné papíry** |
| 521 | Kuponové dluhopisy |
| 522 | Hypoteční zástavní listy |
| 524 | Směnky |
| 525 | Bezkuponové dluhopisy |
| **53** | **Podřízené finanční závazky** |
| 531 | Podřízené přijaté úvěry a vklady od bank |
| 532 | Podřízené přijaté úvěry a vklady od klientů |
| 533 | Podřízené emitované dluhopisy |
| **54** | **Rezervy** |
| 542 | Rezervy daňově uznané |
| 543 | Rezervy daňově neuznané |
| **55** | **Fondy ze zisku** |
| 552 | Zákonné rezervní fondy |
| 557 | Ostatní fondy ze zisku |
| **56** | **Základní kapitál a kapitálové fondy** |
| 561 | Základní kapitál |
| 562 | Dlouhodobý závazek zahraniční pobočky vůči centrále |
| 563 | Ažiový fond |
| 564 | Ostatní kapitálové fondy |
| 566 | Vlastní akcie |
| 567 | Rozdíly z přepočtu účastí |
| 569 | Rozdíly z přepočtů zajišťovacích derivátů |
| **57** | **Převedený hospodářský výsledek** |
| 571 | Nerozdělený zisk z předchozích období |
| 572 | Neuhrazená ztráta z předchozích období |
| **58** | **Závěrkové účty** |
| 581 | Počáteční účet rozvažný |
| 582 | Konečný účet rozvažný |
| 583 | Účet zisků a ztrát |
| **59** | **Hospodářský výsledek ve schvalovacím řízení** |
| 590 | Hospodářský výsledek ve schvalovacím řízení |

## Třída 6 – Náklady

| Účet | Název |
|---|---|
| **61** | **Náklady na finanční činnosti** |
| 611 | Náklady na pokladní a mezibankovní operace |
| 612 | Náklady na operace s klienty |
| 613 | Náklady na leasing |
| 614 | Náklady na emitované cenné papíry |
| 615 | Náklady na operace s cennými papíry |
| 616 | Náklady na devizové operace |
| 617 | Náklady na ostatní operace |
| 619 | Náklady na derivátové operace |
| **63** | **Všeobecné provozní náklady** |
| 631 | Náklady na zaměstnance |
| 632 | Sociální náklady |
| 635 | Daně a poplatky |
| 636 | Nakupované výkony |
| 637 | Odpisy hmotného majetku |
| 638 | Odpisy nehmotného majetku |
| **65** | **Tvorba rezerv a opravných položek** |
| 651 | Tvorba opravných položek daňově neuznaných |
| 652 | Tvorba rezerv daňově uznaných |
| 653 | Tvorba rezerv daňově neuznaných |
| 654 | Tvorba opravných položek daňově uznaných |
| **66** | **Ostatní provozní náklady** |
| 661 | Odepsané pohledávky za bankami |
| 662 | Odepsané pohledávky za klienty a ostatními dlužníky |
| 663 | Náklady z postoupených pohledávek za bankami |
| 664 | Náklady z postoupených pohledávek za klienty |
| 665 | Náklady z převodu účastí |
| 666 | Náklady z převodu ostatního majetku |
| 667 | Jiné provozní náklady |
| **67** | **Mimořádné náklady** |
| 671 | Mimořádné náklady |
| **68** | **Daň z příjmů** |
| 681 | Daň z příjmů z běžné činnosti – splatná |
| 682 | Daň z příjmů z běžné činnosti – odložená |
| 683 | Daň z příjmů z mimořádné činnosti – splatná |
| 684 | Daň z příjmů z mimořádné činnosti – odložená |
| 685 | Dodatečné odvody daně z příjmu |
| **69** | **Vnitrobankovní náklady** |
| 690 | Vnitrobankovní náklady |

## Třída 7 – Výnosy

| Účet | Název |
|---|---|
| **71** | **Výnosy z finančních činností** |
| 711 | Výnosy z pokladních a mezibankovních operací |
| 712 | Výnosy z operací s klienty |
| 713 | Výnosy z leasingu |
| 714 | Výnosy z držených cenných papírů |
| 715 | Výnosy z operací s cennými papíry |
| 716 | Výnosy z devizových operací |
| 717 | Výnosy z ostatních operací |
| 719 | Výnosy z derivátových operací |
| **75** | **Použití rezerv a opravných položek** |
| 751 | Použití opravných položek daňově neuznaných |
| 752 | Použití rezerv daňově uznaných |
| 753 | Použití rezerv daňově neuznaných |
| 754 | Použití opravných položek daňově uznaných |
| **76** | **Ostatní provozní výnosy** |
| 761 | Výnosy z odepsaných pohledávek za bankami |
| 762 | Výnosy z odepsaných pohledávek za klienty a ostatními dlužníky |
| 763 | Výnosy z postoupených pohledávek za bankami |
| 764 | Výnosy z postoupených pohledávek za klienty |
| 765 | Výnosy z převodu účastí |
| 766 | Výnosy z převodu ostatního majetku |
| 767 | Jiné provozní výnosy |
| **77** | **Mimořádné výnosy** |
| 771 | Mimořádné výnosy |
| **79** | **Vnitrobankovní výnosy** |
| 790 | Vnitrobankovní výnosy |

## Třída 8 – Vnitrobankovní účetnictví

Bez syntetických účtů.

## Třída 9 – Podrozvahové účty

| Účet | Název |
|---|---|
| **91** | **Pohledávky a závazky z příslibů úvěrů a půjček** |
| 911 | Poskytnuté přísliby úvěrů a půjček |
| 912 | Přijaté přísliby úvěrů a půjček |
| **92** | **Pohledávky a závazky ze záruk** |
| 921 | Poskytnuté záruky a ručení |
| 922 | Přijaté záruky a ručení |
| 923 | Poskytnutá přijetí směnek |
| 924 | Přijatá přijetí směnek |
| 925 | Poskytnuté záruky z převedených směnek |
| 926 | Přijaté záruky z převedených směnek |
| 927 | Poskytnutá směnečná rukojemství |
| 928 | Přijatá směnečná rukojemství |
| **93** | **Pohledávky a závazky z akreditivů** |
| 931 | Poskytnuté záruky z otevření akreditivů |
| 932 | Přijaté záruky z otevření akreditivů |
| 933 | Poskytnuté záruky z potvrzení akreditivů |
| 934 | Přijaté záruky z potvrzení akreditivů |
| **94** | **Pohledávky a závazky ze spotových operací** |
| 941 | Pohledávky ze spotových operací s úrokovými nástroji |
| 942 | Závazky ze spotových operací s úrokovými nástroji |
| 943 | Pohledávky ze spotových operací s měnovými nástroji |
| 944 | Závazky ze spotových operací s měnovými nástroji |
| 945 | Pohledávky ze spotových operací s akciovými nástroji |
| 946 | Závazky ze spotových operací s akciovými nástroji |
| 947 | Pohledávky ze spotových operací s komoditními nástroji |
| 948 | Závazky ze spotových operací s komoditními nástroji |
| **95** | **Pohledávky a závazky z pevných termínových operací** |
| 951 | Pohledávky z pevných termínových operací s úvěrovými a úrokovými nástroji |
| 952 | Závazky z pevných termínových operací s úvěrovými a úrokovými nástroji |
| 953 | Pohledávky z pevných termínových operací s měnovými nástroji |
| 954 | Závazky z pevných termínových operací s měnovými nástroji |
| 955 | Pohledávky z pevných termínových operací s akciovými nástroji |
| 956 | Závazky z pevných termínových operací s akciovými nástroji |
| 957 | Pohledávky z pevných termínových operací s komoditními nástroji |
| 958 | Závazky z pevných termínových operací s komoditními nástroji |
| **96** | **Pohledávky a závazky z opčních operací** |
| 961 | Pohledávky z opcí na úvěrové a úrokové nástroje |
| 962 | Závazky z opcí na úvěrové a úrokové nástroje |
| 963 | Pohledávky z opcí na měnové nástroje |
| 964 | Závazky z opcí na měnové nástroje |
| 965 | Pohledávky z opcí na akciové nástroje |
| 966 | Závazky z opcí na akciové nástroje |
| 967 | Pohledávky z opcí na komoditní nástroje |
| 968 | Závazky z opcí na komoditní nástroje |
| **97** | **Pohledávky a závazky ze zástav a závazky z kolaterálu** |
| 971 | Poskytnuté nemovité zástavy |
| 972 | Přijaté nemovité zástavy |
| 973 | Poskytnuté peněžní zástavy |
| 974 | Přijaté peněžní zástavy |
| 975 | Poskytnuté zástavy – cenné papíry |
| 976 | Přijaté zástavy – cenné papíry |
| 977 | Poskytnuté ostatní zástavy |
| 978 | Přijaté ostatní zástavy |
| 979 | Přijaté kolaterály – cenné papíry |
| **98** | **Pohledávky a závazky z hodnot v úschově, správě a uložení** |
| 983 | Hodnoty banky předané do úschovy |
| 984 | Hodnoty převzaté do úschovy |
| 985 | Hodnoty banky předané do správy |
| 986 | Hodnoty převzaté do správy |
| 987 | Hodnoty banky předané k uložení |
| 988 | Hodnoty převzaté k uložení |
| **99** | **Uspořádací a evidenční účty** |
| 991 | Uspořádací účet operací s úrokovými nástroji |
| 992 | Uspořádací účet operací s měnovými nástroji |
| 993 | Uspořádací účet operací s akciovými nástroji |
| 994 | Uspořádací účet operací s komoditními nástroji |
| 995 | Uspořádací účet operací s úvěrovými nástroji |
| 996 | Odepsané pohledávky |
| 997 | Zásoba hodnot v evidenci |
| 998 | Jiné hodnoty v evidenci |
| 999 | Pomocné souvztažné účty |
