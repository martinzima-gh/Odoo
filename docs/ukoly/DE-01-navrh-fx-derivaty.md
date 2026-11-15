# DE-01 Návrh: FX forward a FX swap

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | návrh (kód se nemění); výstup je podklad pro oranžovou a červenou zónu |
| Výchozí větev | `main` po ST-01 |
| Větev úkolu | `etapa/derivaty` |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/plan-dalsiho-vyvoje.md` (Etapa 1), `docs/navrh-oceneni-derivatu.md`, otevřené body „Oceňování derivátů“, „Podrozvaha v Odoo“, „TISIFI10 u nových smluv“ |

**Cíl:** návrh, podle kterého půjde měnový forward a měnový swap (dvě nohy, mimoburzovní, bez zajišťovacího účetnictví)
evidovat, ocenit, zaúčtovat a přiřadit třídě. Martin z něj rozhodne varianty; implementace běží až po schválení.

**Účetní jednotka a rámec:** fond (kniha `fund`, vyhláška č. 501/2002 Sb., osnova `investra_fund`). Rámec Services
(500/2002 Sb.) se nemíchá. Vychází se jen z platných a účinných předpisů.

**Výstupy:**

1. `docs/navrh-fx-derivaty.md`, nejvýš 100 řádků: varianty s doporučením, číselný příklad, seznam testů, otázky k rozhodnutí.
2. Zadání `docs/ukoly/DE-02` až `DE-06` podle `_sablona.md` (rozsah souborů, kritéria přijetí, zóna, model podle plánu).
3. Doplnění otevřených bodů (`docs/otevrene-body.md`), pokud návrh některý zpřesní; nic neuzavírat bez Martina.

**Co musí návrh zodpovědět:**

- **Evidence smlouvy:** nominály obou měn, sjednaný kurz, data obou noh, protistrana, portfolio, účel (zajištění třídy /
  fondu / bez zajištění); vazba na evidenci nástrojů (`investra_instrument_master`, číselník BA0088) a na protistranu.
  Swap jako jedna smlouva se dvěma nohami, nebo dva forwardy – varianty a dopad na ocenění a výkazy.
- **Zdroj hodnoty:** ocenění od protistrany × vlastní výpočet (spot a forwardové body, nebo úrokové sazby obou měn);
  pořadí zdrojů podle `docs/navrh-oceneni-derivatu.md`, kontrola stáří vstupů, kde se vstupy evidují (`investra_rates`).
- **Účtování:** sjednání (podrozvaha), kladná a záporná reálná hodnota, přecenění při ocenění, vypořádání blízké
  a vzdálené nohy, storna. Ověřit na instalaci, jak podrozvahu vést v Odoo 20 Community (otevřený bod), a navrhnout
  účty rolí. Každá operace přes `investra.posting.preview` (náhled a záložka dokladů).
- **Zajištění třídy:** výsledek derivátu jen do zajišťované třídy (`investra_allocation`), co s nezajišťovacím derivátem,
  dopad na NAV a kurz třídy; měna ocenění = měna kurzu třídy, NAV ve funkční měně (deník rozhodnutí).
- **Výkazy ČNB:** které výkazy a položky FOFI20261201 derivát plní (`docs/cnb/`, hledat cíleně), včetně bodu TISIFI10.
- **Kontroly ocenění:** nová upozornění (derivát bez hodnoty, starý vstup, splatná noha nevypořádaná).

**Číselný příklad (povinný):** jeden FX swap fondu s třídou v EUR přes dvě po sobě jdoucí ocenění a vypořádání vzdálené
nohy: vstupy, reálná hodnota v obou dnech, všechny účetní zápisy (MD/D, částky), dopad do NAV fondu a do kurzu obou tříd.
Čísla smyšlená, spočtená a zkontrolovaná (součet změn RH = výsledek při vypořádání).

**Předpisy – ověřit v primárních zdrojích, uvádět přesně, neověřené označit:**

- vyhláška č. 501/2002 Sb. (deriváty, reálná hodnota, podrozvaha) a České účetní standardy pro finanční instituce
  k derivátům; IFRS 9 a IFRS 13 v rozsahu, v jakém na ně rámec odkazuje,
- ZISIF a nařízení vlády č. 243/2013 Sb. (deriváty v majetku fondu, limity a protistrany) – jen dopad na evidenci a kontroly,
- nařízení (EU) č. 648/2012 (EMIR): zda a komu vzniká oznamovací povinnost u měnových forwardů a swapů; jen pojmenovat
  dopad na data, která je třeba evidovat. Hlavní relace tyto body neověřovala.
- Vnitřní Pravidla oceňování (důvěrné): odkazovat jen názvem a článkem; `duverne/poznatky-derivaty.md` jen číst.
- Nejistý výklad pojmenovat a navrhnout ověření u auditora nebo ČNB.

**Rozsah souborů:** `docs/navrh-fx-derivaty.md`, `docs/ukoly/DE-0[2-6]-*.md`, `docs/otevrene-body.md`, tento soubor
(Výsledek), předávka v `docs/predavky/`. Kód číst jen cíleně (modely obchodu, ocenění, alokace, náhled zaúčtování).

**Mimo rozsah:** jakákoli změna kódu a databáze, ostatní deriváty, zajišťovací účetnictví, odeslání do SDAT,
rozhodování za Martina (varianty jen navrhnout).

**Kritéria přijetí:** návrh do 100 řádků s příkladem, který početně sedí; každá citace předpisu s paragrafem nebo
označením „neověřeno“; pět zadání DE-02 až DE-06; seznam otázek k rozhodnutí ve zprávě Martinovi; commit a push
`origin etapa/derivaty:etapa/derivaty`; pak se zastavit.

## Výsledek

Hotovo 15. 11. 2026, hlavní relace (Fable) místo relace Opus; rozsah zúžil Martin na zjednodušené řešení.

- **Vytvořené soubory:** `docs/navrh-fx-derivaty.md`, zadání `DE-02` až `DE-05` (původní DE-05 Zajištění třídy odpadlo,
  ukázka je nově DE-05), úprava plánu, deník rozhodnutí, otevřený bod „Zjednodušené ocenění FX derivátů“.
- **Ověřeno:** číselný příklad přepočítán (součet změn RH = −300 000,00); v kódu existují typ `derivative_otc`,
  role `derivative`, účet Deriváty v osnově fondu, typ účtu `off_balance` v Odoo 20, události a náhled zaúčtování.
- **Neověřeno:** předpisy (501/2002 Sb., ČÚS, IFRS 13, EMIR, ZISIF) – ověření je první bod DE-03; čísla účtů.
- **Rozhodnuto Martinem:** varianta B; bez zajišťovacích derivátů; ruční hodnota s přílohou nebo důvodem; vypořádání tlačítkem.
