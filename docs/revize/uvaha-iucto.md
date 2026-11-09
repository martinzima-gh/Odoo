# Úvaha: iÚčto pro všechny subjekty a vlastní aplikace pro ocenění

Vedlejší úvaha k revizi projektu Investra (`revize-krok2.md`), zpracovaná 8. 11. 2026. **Hlavní směr je Odoo (P).**
Tento dokument jen shrnuje, co by znamenala druhá varianta, kdyby se k ní projekt vrátil. Dokument je důvěrný.

**Značky:**
- **(P)** fakt z podkladu nebo od vlastníka projektu,
- **(Z)** odborná znalost,
- **(D)** domněnka nebo odhad.

Odhady pracnosti jsou v člověkodnech (MD) a jsou vždy (D).

---

## 1. Zadání (P)

Ve hře jsou jen dvě varianty, smíšenou (Services v iÚčtu, fondy v Odoo) vlastník vyloučil:
- **A: Odoo pro vše** – účetnictví Services, investiční společnosti i fondů a ocenění v modulech `investra_*`.
  Je to hlavní směr.
- **B: iÚčto pro vše** – iÚčto jako účetní software pro všechny subjekty (účtovali byste sami) a ocenění fondů ve vlastní
  aplikaci mimo Odoo.

Hlavním důvodem pro zvážení varianty B je cena licencí a vývoje. Services pracuje na Macu a iOS.

## 2. Vylučovací kritéria pro iÚčto

Podle dosavadního průzkumu v podkladu je iÚčto pro fondy nevhodné (P). Ověření je levné, zkušební účet a dotaz
na dodavatele zaberou 1–2 dny. Pokud iÚčto nesplní některé z kritérií K1–K5, varianta B pro fondy nejde (D).

| # | Kritérium | Proč | Jak ověřit |
|---|---|---|---|
| K1 | Účetnictví podle vyhlášky 501 (osnova a výkazy pro finanční instituce) | fondy a investiční společnost účtují podle 501 (P) | zkušební účet, dotaz na dodavatele |
| K2 | Účetnictví v EUR jako funkční měně s kurzy ECB | funkční měna je parametr fondu (P) | zkušební účet |
| K3 | Import účetních zápisů z aplikace (API nebo soubor) s odkazem na zdrojovou událost a ochranou proti ruční změně | každé číslo musí jít dohledat k ceně, kurzu a schvalovateli (P) | dokumentace API |
| K4 | Export předvahy a obratů po účtech přes API | ocenění, kontrola „pozice = hlavní kniha“ a výkazy ČNB potřebují data z účetnictví | dokumentace API |
| K5 | Desítky účetních jednotek, oprávnění po jednotkách, MFA, cena za jednotku | start s jedním fondem, později desítky (P) | ceník, zkušební účet |
| K6 | Import výpisů fondu bez jmen a účtů investorů | pravidlo o osobních údajích investorů (P; v revizi rozhodnutí R17) | zkušební účet |
| K7 | Uzamčení období, neměnnost zaúčtovaného, storno místo přepisu | auditovatelnost (P) | zkušební účet |
| K8 | Smluvní náležitosti DORA (lokalita dat, audit, incidenty, exit plán) | iÚčto by bylo dodavatelem ICT služeb pro kritickou funkci obhospodařovatele (D, ověří právník) | smlouva, dotaz na dodavatele |
| K9 | Export všech dat a dokladů pro archiv a odchod k jinému systému | archivace čitelná bez systému (P) | dokumentace |
| K10 | DPH identifikované osoby (přiznání bez odpočtu) | Services (P) | zkušební účet |

## 3. Co by musela umět vlastní aplikace

- **Totéž co dnešní moduly `investra_*` kromě hlavní knihy:**
  - fondy a třídy, nástroje a ceny se schválením, obchody a pozice, peněžní toky,
  - úplaty a performance fee, alokace, ocenění s kroky a kontrolami, schvalování a zastupování,
  - balíček pro depozitáře, zveřejnění kurzu, rozhraní IS, převzetí, výkazy ČNB a přehledy napříč fondy.
- **Navíc vše, co Odoo dává hotové:** přihlášení a MFA, uživatele a role po fondech, auditní stopu, přílohy, exporty,
  plánovač úloh, upozornění a správu číselníků.
- **Integraci s iÚčtem:** export zápisů s ID události, import předvahy a průběžné odsouhlasení pozic s hlavní knihou
  ve dvou systémech.

## 4. Srovnání (D, odhady)

| Hledisko | A: Odoo pro vše | B: iÚčto pro vše + vlastní aplikace |
|---|---|---|
| Účetnictví Services | s Enterprise hotové (licence), v Community 35–75 MD | hotové v iÚčtu, nastavení 1–3 MD |
| Účetnictví fondů a investiční společnosti | standard Odoo + vlastní výkazy podle vyhlášky 501 | jen pokud iÚčto splní K1–K5 |
| Ocenění a NAV | dokončit `investra_*`: jádro 100–170 MD (revize, kapitola 2.7) | stejné mezery jádra + základ aplikace 40–80 MD + převod logiky 20–40 MD + integrace s iÚčtem 15–30 MD |
| Licence | Enterprise se platí za uživatele: 5–8 uživatelů ≈ 1 400–2 700 € ročně, s počtem fondů neroste (ceník podle podkladu, ověřit) | iÚčto pravděpodobně za účetní jednotku, roste s počtem fondů (ověřit ceník) |
| Provoz a DORA | jeden systém, jeden hosting | dva systémy (SaaS a vlastní aplikace), dvě zálohy, dvě správy přístupů, integrace |
| Hotová práce | 13 modulů, 274 testů (P) | využije se logika v Pythonu a testy, obrazovky a vazby na Odoo ne |
| Čas k prvnímu fondu | napjatý (revize, kapitola 2.7) | o 2–4 měsíce později |
| Závislost | Odoo, na trhu jsou partneři | malý dodavatel SaaS a vlastní kód |

## 5. Cena licencí proti ceně vývoje (D)

- Roční licence Enterprise pro 5–8 uživatelů (1 400–2 700 €) stojí tolik jako 10 člověkodnů při sazbě 140–270 € za den.
  Při vyšší sazbě je licence levnější než vývoj, který nahrazuje.
- Varianta B ušetří licence a vývoj účetních funkcí pro Services, ale přidá zhruba 75–150 MD na aplikaci a integraci
  s iÚčtem.
- Rozhodující náklad je tedy vývoj, ne licence.

## 6. Závěr úvahy

- Hlavní směr Odoo (P) odpovídá i odhadu nákladů. Varianta B vychází podle odhadu dráž a první fond by posunula
  o 2–4 měsíce (D).
- Kdyby se projekt k variantě B vrátil, nejdřív ověřit kritéria K1–K10. Bez splnění K1–K5 nemá smysl pokračovat.
- Pokud chcete nechat cestu k vlastní aplikaci otevřenou, dá se výpočetní jádro NAV psát jako knihovna v Pythonu
  nezávislá na Odoo, kterou moduly Odoo jen volají. Pomáhá to i při upgradech Odoo. V akčním plánu revize to zatím není.

## 7. V čem stavět vlastní aplikaci a co to znamená pro Mac a iOS

- **Doporučená technologie:**
  - webová aplikace na serveru v Pythonu (3.12 nebo novější) s frameworkem Django 5.2 LTS (podpora do dubna 2028, ověřit),
  - databáze PostgreSQL,
  - uživatelské rozhraní ze serverových šablon s knihovnou HTMX,
  - výpočty v typu Decimal, testy v pytest, běh v Dockeru.
- **Proč Python a Django:**
  - stejný jazyk jako Odoo i referenční výpočet NAV, takže jde převzít logiku i testy,
  - vyspělé knihovny pro přihlášení, MFA, oprávnění a historii změn (např. django-otp, django-simple-history),
  - hotové administrační rozhraní pro číselníky,
  - s Claude Code se v něm pracuje stejně jako dnes.
- **Mac a iOS:**
  - vývoj na Macu v Dockeru jako dnes; licenční podmínky Docker Desktop pro firmy ověřit,
  - uživatelé pracují v Safari na Macu; schvalovatel může schvalovat i z iPhonu nebo iPadu přes responzivní stránku,
  - druhý faktor přes ověřovací kódy v aplikaci Hesla na Macu a iPhonu (TOTP), případně passkeys (podporu v knihovně ověřit).
- **Nativní aplikaci pro macOS a iOS (Swift) nedoporučuji.** Data, výpočty, čtyři oči, auditní stopa a zálohy musí být
  na serveru. Nativní klient by tak byl práce navíc jen pro zařízení Apple a auditor, depozitář nebo externí účetní by
  stejně potřebovali webový přístup.
- **Jiné možnosti:**
  - TypeScript (např. Next.js) má modernější rozhraní, ale pro přesná desetinná čísla potřebuje zvláštní knihovnu
    a nevyužije dnešní kód v Pythonu,
  - .NET je pro finance silné, ale je mimo dosavadní znalosti týmu,
  - nástroje typu low-code mají slabou auditní stopu a nejistou lokalitu dat (DORA).
- **Pro hlavní směr Odoo se nic nemění:** Odoo je také v Pythonu, vývoj probíhá na Macu v Dockeru a uživatelé pracují
  v Safari na Macu i iPadu.

## 8. Otevřené otázky k této úvaze

| # | Otázka | Kdo odpoví |
|---|---|---|
| 1 | Jaký je ceník iÚčta pro desítky účetních jednotek? | VED |
| 2 | Přijme dodavatel iÚčta smluvní náležitosti DORA (audit, incidenty, exit plán, lokalita dat)? | VED, právník |
| 3 | Splní iÚčto kritéria K1–K5 (vyhláška 501, EUR, import a export přes API, desítky jednotek)? | VED (zkušební účet) |
