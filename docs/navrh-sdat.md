# Modul pro SDAT (návrh)

Stav 2026-11-07. Jen návrh, odložený do získání přístupu do testovacího SDAT. Nic není naprogramované ani nic nebylo do SDAT odesláno. Zdroj: technická specifikace SDAT na cnb.cz (TS 1 až 6, testování, WSDL a XSD ve verzi 1.99.6), vyhláška 267/2020 Sb., § 10.

## Co SDAT nabízí

| Účel | Služba | Pro nás |
|---|---|---|
| Plán výkazů a termínů | `ctiVykazovaciPovinnost` | Výskyty výkazů, `TerminPredlozeni`, výjimky; nahradí ruční termíny |
| Stav plnění | `ctiStavVykazovani` | Stav výskytu, upomínky, vydání, požadovaná oprava nebo potvrzení |
| Stav zpracování a protokoly | `ctiStavZpracovani` | Protokoly o zprávě a vydání, nalezené chyby |
| Metodika | `ctiSeznamMetodik`, `ctiSeznamVykazu`, `ctiVykaz`, `ctiZmenyVykazu` | Struktura, kontroly a změny; nahradí ruční obnovu `docs/cnb` |
| Údaje osoby | `ctiUdajeOsoby` | Ověření spojení, první test |
| Odeslání | `zaslaniVstupniZpravy` | Jediná služba pro všechny výkazy |

Technicky: SOAP 1.1, MTOM, TLS 1.2 nebo 1.3, UTF-8, autentizace certifikátem. Test `https://sdatt.cnb.cz/sdat_ws/`, produkce `https://sdat.cnb.cz/sdat_ws/`.
Formáty jsou XMLSDAT, XBRL, ISO 20022 a iXBRL. Formát a způsob podpisu určuje výkaz, proto se berou z metapopisu, ne z kódu.

## Pojmy SDAT v Odoo

| SDAT | Model | Obsah |
|---|---|---|
| Osoba | `investra.sdat.person` | Kód osoby, vazba na fond nebo společnost, LEI, role vykazující nebo zastupující |
| Výskyt výkazu | `investra.sdat.occurrence` | Výkaz, osoba, stav ke dni, rozsah, termín, stav, očekávaná akce |
| Vydání | `investra.sdat.issue` | Data, Storno, nebo Potvrzení; metodika, číslo vydání, snímek dat, vazba na ocenění |
| Vstupní zpráva | `investra.sdat.message` | Soubor, podpis, otisk, ID žádosti, `ReferencniId`, `VstupniZpravaId`, odpověď |
| Protokol | `investra.sdat.protocol` | Originál XML, výsledek, chyby navázané na kontroly |
| Metodika | `investra.sdat.methodology` | Verze metapopisu a její změny |

Výskyty plní evidenci `investra.regulatory.deadline` se zdrojem SDAT, Přehled fondů se nemění.

## Postup

1. **Plán:** čtení výskytů a termínů.
2. **Sestavení:** výkaz z mapování a schváleného ocenění, snímek dat se neměnně uloží.
3. **Kontrola:** validace proti XSD, formátové kontroly a vlastní JVK a MVK z metapopisu.
4. **Uvolnění:** připravil jeden člověk, uvolnil druhý.
5. **Podpis a odeslání:** provede pověřená osoba, viz varianty.
6. **Přijetí:** synchronní odpověď s `VstupniZpravaId`; zpracování je asynchronní.
7. **Sledování:** čtení stavu a protokolů, výsledek jde do Přehledu fondů.
8. **Reakce:** `Opravit` vede k novému vydání s daty, `Potvrdit` k potvrzujícímu vydání se zdůvodněním. Rozhoduje člověk.

Stavy výskytu jsou PLANOVANO, ZPRACOVANI, PREDBEZNE_SPLNENO, SPLNENO a NEDOKONCENO. Výkaz je hotový až při SPLNENO; PREDBEZNE_SPLNENO může ještě změnit mezivýkazová kontrola.
Po chybě sítě nebo vypršení času se zpráva opakuje se stejným UUID, jinak hrozí duplicita. Periodické čtení je bezpečné, odesílání nikdy nepoběží samo.

## Varianty podpisu a odeslání

| Varianta | Jak | Výhody | Nevýhody |
|---|---|---|---|
| A. Soubor a webová aplikace | Odoo vytvoří XML, člověk ho nahraje a podepíše v SDAT | Bez soukromého klíče pro podpis v Odoo, nejrychlejší start | Ruční krok u každého výkazu |
| B. Podpis mimo Odoo | Odoo připraví soubor, člověk ho podepíše svým nástrojem, Odoo odešle | Klíč zůstává u osoby, jde o službu | Potřeba podpisového nástroje podle XAdES |
| C. Elektronická pečeť | Klíč v HSM nebo trezoru, odeslání po kliknutí člověka | Nejméně ruční práce | Nejvyšší bezpečnostní nároky, nutné ověřit právně |

Utilita ČNB `sdat-xades-podpis.jar` podle ČNB nefunguje s novou Javou; ČNB doporučuje podpis v prohlížeči s komponentou I.CA, což podporuje variantu A. 

**Doporučení:** začít variantou A se čtením přes služby, později přejít na B. U C nejdřív vyřešit rozpor níže. Ve všech variantách odesílání spouští člověk; AI ani plánovač nic neodesílá.

## Doplnění z TS 4 a popisu kontrol

- **Prázdná oblast:** nepovinná datová oblast bez údajů se ve zprávě vůbec neuvádí, ani prázdným elementem.
- **Přílohy:** jsou součástí vydání a podepisují se s ním. Povolené formáty jsou v TS 4.
- **Kontroly:** pro strojové provádění je určen uživatelský tvar kontrol (list, řádek, sloupec). Ten je v `docs/cnb`, stačí vlastní vyhodnocovač; jazyk je popsaný v TS 8 a v souboru `sdat.bnf.txt`. Sémantický tvar je jen informativní.
- **Formáty rámce Fondy:** TS 4 popisuje XBRL a ISO 20022 pro rámce EBA, EIOPA a ESMA. Fondy podle dostupných podkladů míří na XMLSDAT, potvrdit z metapopisu.

Kopie dokumentace je v `zalohy/sdat-dokumentace/`, mimo git, staženo 2026-11-07.

## Bezpečnost

- Soukromé klíče nikdy v databázi ani v gitu; v trezoru nebo HSM, v Odoo jen otisk a platnost.
- Oddělené nastavení test a produkce, produkční přístup jen po výslovném schválení. V testu jen testovací data.
- Odchozí provoz povolený jen na SDAT, s kontrolou TLS.
- Originály zpráv a protokolů neměnně, s otisky a pravidly archivace. Pečeť ČNB na protokolu ověřit.
- Upozornění před koncem platnosti certifikátů.
- Záložní postup při výpadku jen po dohodě s ČNB. SDAT zahrnout do mapy DORA.

## Co je potřeba ověřit

- **Podpis:** § 10 odst. 3 vyhlášky 267/2020 Sb. mluví o uznávaném elektronickém podpisu kontaktní osoby, specifikace SDAT připouští i pečeť a způsob určuje výkaz. Pro výkazy Fondů ověřit v metapopisu a u ČNB.
- **Rozpory ve specifikaci:** otisk MD5 proti SHA-256 a komprese ZIP proti gzip. Ověřit v testovacím prostředí.
- **Výkazy Fondů:** formát a podpis každého výkazu.
- **Fond a Osoba:** zda má každý fond a podfond svůj kód a kdo vystupuje jako zastupující osoba.
- **Knihovny:** `zeep`, `lxml`, `cryptography` a `requests` v obrazu Odoo jsou; `xmlsec` a `signxml` chybí. Instalace je změna obrazu a vyžaduje souhlas.
- **Přístupy:** registrace v testovacím SDAT a certifikát; distribuce certifikátu může trvat do 24 hodin.

## Etapy

1. Spojení v testu, `ctiUdajeOsoby` (scénář ČNB TEST_0.1).
2. Čtení plánu a termínů, napojení na Přehled fondů.
3. Čtení metodiky a stavu vykazování, protokoly.
4. Sestavení a validace XML, varianta A, testovací scénáře ČNB TEST_1.
5. První výkaz v testu, oprava a potvrzení.
6. Podpis a odeslání službou, až po rozhodnutí o variantě.
7. Produkce po schválení, bezpečnostní revizi a mapě DORA.
