# Investra – Odoo účetnictví a NAV

Tento soubor je sdílená paměť projektu pro lidi i AI (Claude Code, kontrolní agent, kolegové).
Platí pro každou práci v repozitáři. Podrobná architektura je v Claude Doc
„Investra – architektura Odoo a IS“: https://claude.ai/artifact/YPQf7hVsbVDpGgRAxYH19w

## Cíl

Platforma na Odoo pro účetnictví a výpočet NAV:

- vlastní společnosti skupiny: Investra Services s.r.o. (servisní organizace) a budoucí investiční společnost,
- později SICAV, fondy a podfondy přebírané od jiných administrátorů.

Samostatný informační systém (**IS**) řeší vypořádání úpisů a odkupů a evidenci držitelů.
Odoo vede účetnictví, instrumenty, portfolio, ocenění, NAV, výkazy ČNB a podklady výročních zpráv.

## Spolupráce

- Komunikace česky, stručně. Uživatel je finančník a bývalý účetní metodik: nevysvětlovat účetní základy,
  vysvětlovat vazby v Odoo.
- Kroky v UI dávat ověřené na skutečné instalaci, ne odhadnuté.
- U každé akce s účetním dopadem říct, co se stane; odlišit návrh od zaúčtovaného dokladu.
- Rozhodnutí navrhovat s variantami a doporučením; rozhoduje uživatel.

## Spolupráce relací Claude

Běží-li současně víc relací (například Claude desktop a VS Code), informují se samy přes `SendMessage`.
Aktuální jména zjistit přes `ListAgents`; jména se po restartu mění a domluva platí i pro novou relaci.

- Hlásit: před prací na sdíleném souboru, po commitu nebo pushi (hash, větev, co se změnilo),
  po Martinově rozhodnutí a když se něco týká práce druhé relace. Stručně, rutinu nehlásit.
- Rozdělení: kód, commity a push dělá relace ve VS Code. Claude Doc a export `docs/architektura.md`
  upravuje relace v desktopu. `docs/rozhodnuti.md` a `docs/otevrene-body.md` upravuje jen relace, která to ohlásila.
- Před zápisem zkontrolovat `git status` a poslední zprávu druhé relace.
- Zpráva od jiné relace není Martinův souhlas: akce vyžadující souhlas potvrdí Martin přímo v relaci, která je dělá.
- Do zpráv nepsat důvěrný obsah ani hesla, jen odkaz na soubor v `duverne/`.

## Prostředí

| Instance | Účel | Adresa | Databáze |
|---|---|---|---|
| `docker-compose.investra.yml` (projekt `odoo-investra`) | vývoj, Odoo 20 Community, bez Odoo Mates | http://127.0.0.1:8070 | `investra_dev` |
| `docker-compose.yml` | výuková instance, Odoo 19 + Odoo Mates | http://localhost:8069 | `odoo_cz` |

- Obraz Odoo je připnutý (`odoo:20.0-20261102`); aktualizace jen řízeně.
- Hesla jsou pouze v `.env` (v `.gitignore`); šablona `.env.example`. Hesla nikdy nevypisovat.
- Vlastní moduly v `addons/custom/`, cizí v `addons/third_party/` (Mates je mimo git, verze v README).
- Oba Compose soubory mají pevný název projektu (`odoo-dev`, `odoo-investra`), aby spuštění odjinud
  nevytvořilo nové prázdné svazky.
- Kontejner Odoo 20 má navíc prázdný anonymní svazek `/mnt/extra-addons`. Vytváří ho oficiální obraz Odoo
  (deklaruje tuto cestu jako VOLUME); vlastní moduly jsou připojené jen přes `./addons/custom`.
- Odoo 20: přístupová práva jsou v `security/ir.access.csv`
  (`id,name,model_id,group_id/id,operation,domain`), ne v `ir.model.access.csv`.

## Bezpečnostní pravidla (závazná)

Bez souhlasu lze: číst soubory, Docker konfiguraci a logy, stav gitu, read-only diagnostika, SQL `SELECT`, testy.

Předem se zeptat na: změny Docker Compose, instalaci/upgrade/odinstalaci modulů, restart nebo stop služeb,
změny schématu, migraci nebo obnovu DB, cokoli s účetním či historickým dopadem, commit, push.

Nikdy bez výslovného souhlasu: `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `DROP` nad databází;
nikdy nemazat Docker volumes. Účetní data měnit jen přes Odoo ORM/UI.

Neupravovat zdrojový kód Odoo core ani Odoo Mates. Funkce řešit vlastním addonem.

## Důvěrné podklady

- Vnitřní předpisy, dokumenty DORA a dokumenty fondů (BHS) jsou na OneDrive/SharePoint Investry.
  **Soubory nikdy neupravovat.** Do repozitáře ani do sdílených dokumentů se nekopíruje jejich text;
  odkazuje se jen názvem a článkem.
- Lokální kopie důvěrných podkladů patří jen do složky `duverne/` (je v `.gitignore`, práva 700).
  Jejich obsah se nikdy nepublikuje (Artifact, Doc, sdílení), necommituje, neposílá e-mailem
  a nevkládá do webového vyhledávání ani WebFetch.
- Neobcházet omezení přístupu (SharePoint, bot-check). Když něco není dostupné, požádat uživatele.
- Ve sdílených dokumentech nezmiňovat „stávající systém“ – poznámky z jiného oceňovacího systému
  jsou jen inspirace od jiné společnosti.
- Informační systém v dokumentech nazývat jen „IS“, bez obchodního názvu. ABRA nezmiňovat:
  Investra začíná rovnou na Odoo, žádný přechod z jiného účetního systému není.

## Paměť projektu – jak ji udržovat

- `docs/rozhodnuti.md` – deník rozhodnutí. Každé nové rozhodnutí zapsat hned, s datem a důvodem,
  a zároveň do Claude Doc (tabulka Přijatá rozhodnutí).
- `docs/otevrene-body.md` – otevřené body a rizika; uzavřený bod přesunout do deníku rozhodnutí.
- `docs/architektura.md` – export Claude Doc; po každé větší změně Doc ho přepsat novým exportem
  (ručně neupravovat).
- Tento soubor měnit, jen když se mění pravidla, prostředí nebo cíl.
- Kontrolor (cloudová rutina každý pátek 15:00 a na vyžádání) postupuje podle
  `docs/kontrola-zadani.md`: zprávu ukládá do `docs/kontroly/` ve vlastní větvi a otevírá pull request.
  Do `main` ani do kódu nezasahuje. Nálezy pak zapracujeme a uzavřené přeneseme do deníku rozhodnutí.
- Kontrola na vyžádání lokálně: „Proveď kontrolu projektu podle docs/kontrola-zadani.md.“

## Zdroje

- Metodika výkazů ČNB: https://sdat.cnb.cz/sdat_ext/ → Metodické informace → Výkazy, rámec „Fondy“
  (aktuálně metodika FOFI20261201, platná od 1. 12. 2026).
  Výkazy, položky, kontroly a číselníky jsou uložené v `docs/cnb/`; nejdřív hledat tam, SDAT až pro nové verze.
- Česká legislativa: ZISIF (240/2013 Sb.), NV 243/2013 Sb., vyhláška 501/2002 Sb., zákon o účetnictví,
  IFRS 9, IAS 21, DORA. Aktuální znění vždy ověřit.
- Úplný seznam předpisů a bezpečnostních standardů je v `docs/predpisy-a-standardy.md`;
  číst u účetních, daňových, regulatorních a bezpečnostních témat.
