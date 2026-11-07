# Česká lokalizace Odoo: co sledovat

Stav 2026-11-07. Průzkum veřejných stránek poskytovatelů a otevřených repozitářů, jako zdroj informací, ne jako výběr dodavatele.
Údaje jsou z popisů na webu: kód, instalace ani testy ověřené nejsou. Aktuální požadavky na podání vždy ověřit u Finanční správy.

## Hlavní zjištění

- **Odoo 20 žádný zdroj nepotvrzuje.** Lokalizace jsou uvedené do verze 19. Pro nás to znamená převod na 20, nebo vlastní doplnění.
- **Standardní `l10n_cz` v naší instalaci** obsahuje osnovu, daně, finanční úřady, QR a přehled DPH. Export pro EPO, kontrolní a souhrnné hlášení ani české bankovní formáty v něm nevidíme (ověřit).
- **Fondovou doménu žádný zdroj neřeší.**
- **Data Dance** zveřejňuje největší otevřenou sadu pro Odoo 19 pod AGPL-3 a závisí na modulech OCA. Dobrý zdroj rozsahu; licenci a slučitelnost s Enterprise ověřit právně, než se kód použije.

## Stav v Odoo 20 Community (kontrola 2026-11-07)

Ověřeno v kódu a databázi naší instance `investra_dev`, bez testování v UI. Závisí na volbě edice.

| Oblast A | Stav | Co doplnit |
|---|---|---|
| DPH přiznání | Řádky výkazu jsou v datech, Community ale nemá zobrazení ani export EPO | Sestava a XML, nebo Enterprise a ověření |
| Souhrnné hlášení | Nenalezeno | Sestava a XML |
| Režim DPH | Daně a 4 fiskální pozice jsou; režim registrované osoby není | Nastavení a ověření postupu |
| DUZP a přenesená daň | DUZP je; daně EU jsou; oprava základu neověřena | Ověřit na dokladech |
| VS, KS, SS, QR | QR platba je; samostatné VS, KS, SS nejsou | Pole a párování |
| Interní doklady, zápočet | Deník ostatních operací je; zápočet neověřen | Ověřit postup |
| Banka a výpisy | Import výpisů, české formáty a párování v menu nejsou | Import, párování se schválením účetní |
| Platební příkazy | Nejsou | Export podle banky |
| Registry | Automatické doplnění partnerů přes placenou službu Odoo; ARES, nespolehlivý plátce nejsou; VIES neověřen | ARES a kontrola plátce |
| Kurzy | Bez automatického stahování a bez kurzů v databázi | Stahování kurzů ČNB |
| Výkazy | Rozvaha, výsledovka, hlavní kniha, saldokonto nejsou; je analýza faktur a cash flow | Vlastní sestavy, nebo Enterprise |
| Uzávěrka | Zámky a zabezpečení zápisů jsou; časové rozlišení a dohady neověřeny | Ověřit a doplnit |
| Přijaté faktury | E-mailový deník je; vytěžení a schvalování nejsou | Oběh dokladů |
| Mzdy | Není | Import účetního zápisu |

## Kontrolní seznam funkcí

Priorita: **A** = potřeba pro Investra Services od začátku, **B** = brzy, **C** = později nebo podle potřeby.

| Oblast | Co má systém umět | Priorita | Kde se objevuje |
|---|---|---|---|
| DPH | Přiznání DPHDP3 pro EPO, řádné, opravné a dodatečné | A | Systee, Data Dance, Pokutsoft, 26HOUSE |
| DPH | Režim neplátce, identifikovaná osoba, plátce a změna režimu | A | Data Dance |
| DPH | Kontrolní hlášení DPHKH1, kontrola proti přiznání | B | Systee, Data Dance, Pokutsoft |
| DPH | Souhrnné hlášení DPHSHV, VIES | A | Systee, Data Dance, Origamis |
| Daně | Daň z příjmů právnických osob, podklady DPPDP9 | B | Data Dance |
| Doklady | DUZP, DPPD, přenesená daňová povinnost, oprava základu daně | A | Systee, Synwase |
| Doklady | VS, KS, SS, QR platba | A | Systee, Data Dance, Synwase |
| Doklady | Zálohy daňové i nedaňové, vydané i přijaté, cizí měna | B | Systee, Origamis, Data Dance |
| Doklady | Interní doklady, vzájemný zápočet | A | Data Dance, Systee |
| Doklady | ISDOC import a export | B | Systee, Data Dance, Origamis |
| Banka | Automatické načtení výpisů, návrh párování, schválení účetní | A | Systee, Data Dance, 26HOUSE |
| Banka | Formáty výpisů ABO/GPC, MultiCash, MT940, CAMT podle banky | A | Systee, Data Dance |
| Banka | Platební příkazy ABO, MultiCash, SEPA XML, podle banky | A | Systee, Origamis, Data Dance |
| Registry | ARES, VIES, nespolehlivý plátce, zveřejněné účty | A | Data Dance, Synwase, Ash technology |
| Registry | Insolvenční rejstřík | C | Origamis |
| Kurzy | Denní kurzy ČNB, historie, kurz na dokladu, přecenění 563/663 | A | Systee, Data Dance |
| Výkazy | Rozvaha a výsledovka podle vyhlášky 500, plný i zkrácený rozsah, deník, hlavní kniha, saldokonto | A | Systee, Data Dance, CyberMindNet |
| Uzávěrka | Období, zámky, časové rozlišení, dohady, rozdělení výsledku | A | Data Dance, CyberMindNet |
| Majetek | Účetní a daňové odpisy, odpisové skupiny, technické zhodnocení, vyřazení | B | Systee, Data Dance, Origamis |
| Pokladna | Pokladní doklady a pokladní deník | C | Systee, Data Dance |
| Mzdy | Mzdy vede externí dodavatel; do Odoo se importuje jen účetní zápis | A | Vlastní import, formát domluvit |
| Cesty | Cestovní příkazy a stravné | C | Origamis |
| Přijaté faktury | Vytěžení, schvalování, oběh dokladů | A | Synwase, standard Enterprise |
| Podání | Datová schránka, automatické odeslání | C | Synwase; CyberMindNet plánuje |
| Hlášení | Intrastat, EET a dopravci | Nepotřebujeme | Systee, Data Dance, Origamis |

## Na co se ptát

- Má funkce podporu Odoo 20 a kdy?
- Běží na Community, nebo potřebuje Enterprise či moduly OCA?
- Podporuje opravná podání a aktuální XSD EPO?
- Kdo aktualizuje funkci po změně legislativy a jak rychle?

## Zdroje

- [Data Dance: repozitář](https://github.com/votrelec/cssk-public) a [průvodce](https://data-dance.github.io/cssk-public/)
- [Ash technology: l10n_cz_extra](https://github.com/ash-technology/l10n_cz_extra)
- [Systee: česká legislativa](https://www.systee.cz/cz-legislativa-odoo)
- [Synwase: průvodce českou lokalizací](https://www.synwase.cz/cs/blog/kompletni-pruvodce-ceskou-lokalizaci-odoo/)
- [Origamis: moduly](https://www.origamis.cz/ceska-odoo-lokalizace)
- [26HOUSE: profil](https://www.odoo.com/partners/26house-s-r-o-2896590)
- [Pokutsoft: kontrolní hlášení](https://pokutsoft.com/apps/l10n_cz_kontrolni_hlaseni/)
- [CyberMindNet: moduly pro Odoo 18](https://cybermindnet.eu/en/blog/cybernews-1/czech-accounting-and-payroll-in-odoo-18-community-the-modules-we-had-to-build-ourselves-6)
