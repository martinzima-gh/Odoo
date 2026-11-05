# Projektové instrukce pro GitHub Copilot

## Projekt a zdroje pravdy

- Jde o vývojové prostředí Odoo pro Investra. Lokální workspace na Macu je primární pracovní prostředí; GitHub slouží k verzování a záloze projektu.
- Nová vývojová instance používá Odoo 20 Community. Podrobný cíl, architekturu, rozhodnutí a otevřené body popisují `README.md`, `CLAUDE.md` a dokumenty v `docs/`.
- Při rozporu ověř skutečný kód a konfiguraci. Nepovažuj starší popis v dokumentaci automaticky za aktuální; upozorni na rozpor a aktualizuj dokumentaci jen pokud o to uživatel požádá nebo je to součást zadání.
- Komunikuj s uživatelem česky, stručně a srozumitelně. Uživatel je finančník a účetní metodik, který se učí Odoo a vývoj; vysvětluj důležité technické kroky, ale nevysvětluj zbytečně účetní základy.

## Prostředí Odoo a Docker

- Projekt běží lokálně na Macu přes Docker Compose a PostgreSQL.
- `docker-compose.investra.yml` je nová vývojová instance Odoo 20 Community:
  - Compose project `odoo-investra`, databáze `investra_dev`, web `http://127.0.0.1:8070`.
  - Obraz Odoo je připnutý na `odoo:20.0-20261102`; aktualizace prováděj pouze řízeně.
  - Načítá pouze core a `addons/custom`; nepřipojuje Odoo Mates.
  - Má vlastní databázový a Odoo volume oddělené od výukové instance.
- `docker-compose.yml` je samostatná výuková instance Odoo 19 na `http://localhost:8069`, databáze `odoo_cz`, s Odoo Mates addony. Zachovej ji a její data.
- Odoo 19 a Odoo 20 jsou oddělené instance s různými Compose projekty, databázemi, host porty a volumes. Nikdy automaticky neslučuj jejich databáze, volumes, addony ani verze.
- Před spuštěním, restartem nebo změnou Compose nejprve ověř aktuální kontejnery a porty, Compose projekt, image/verzi Odoo, databázi, environment variable names (nikoli hodnoty), připojené addon adresáře a volumes. Použij validaci `docker compose -f <soubor> config --quiet`; neukládej ani nevypisuj vyrenderovanou konfiguraci obsahující secrets.
- Pokud existuje kolize portů, nečekaný kontejner/volume/databáze, chybí povinná proměnná nebo by příkaz mohl ovlivnit jinou instanci, zastav se a vysvětli situaci. Před restartem či zastavením služeb, změnou Compose nebo jiným krokem s provozním dopadem si vyžádej souhlas podle `CLAUDE.md`.
- Nikdy automaticky nemigruj databázi mezi hlavními verzemi Odoo.

## Bezpečnost a data

- Před každou změnou nejprve analyzuj skutečný aktuální stav workspace, Git změn, konfigurace a dotčených dat. Nepracuj na základě předpokladů ani zastaralých shrnutí.
- Nikdy nemaž databázi, PostgreSQL volume, Docker volume, container, addon ani jiné uživatelské soubory bez výslovného souhlasu uživatele.
- Bez výslovného souhlasu nikdy nepoužívej `docker compose down -v`, `docker volume rm`, `docker rm`, `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, `DELETE`, `UPDATE`, `INSERT`, `rm -rf` ani obdobnou destruktivní operaci.
- Nad databází používej bez zvláštního souhlasu jen read-only diagnostiku a SQL `SELECT`. Účetní data měň standardním Odoo UI/ORM, nikdy přímými zápisy do PostgreSQL.
- Před migrací nebo obnovou databáze, změnou schématu, instalací/upgrade/odinstalací modulu a jakoukoli změnou ovlivňující účetní či historická data si vyžádej výslovný souhlas. Neprováděj tyto kroky automaticky.
- Zachovej případné existující změny uživatele. Nepřepisuj ani nevracej nesouvisející soubory; před commitem ověř diff a commit/push proveď pouze na výslovný pokyn.
- Vnitřní předpisy, dokumenty DORA a dokumenty fondů na OneDrive/SharePoint jsou důvěrné: neupravuj je, nekopíruj jejich text do repozitáře ani do sdílených dokumentů a neobcházej přístupová omezení. Řiď se `CLAUDE.md`.

## Odoo addony

- Vlastní moduly patří výhradně do `addons/custom/`; moduly třetích stran patří do `addons/third_party/`. Tyto oblasti nikdy nemíchej.
- V projektu již existuje vlastní modul `addons/custom/investra_fx_revaluation`. Před změnou prostuduj jeho manifest, modely, přístupová práva a testy; nepopisuj složku custom jako prázdnou.
- Soubory v `addons/third_party/odoomates/` nejsou součástí nové vývojové architektury Odoo 20. Odoo Mates je používáno ve výukové Odoo 19; nepřenášej je ani jejich závislosti do Odoo 20 automaticky.
- Cizí/community addon před převzetím nebo instalací prověř: upstream zdroj a udržovatele, licenci, cílovou větev a kompatibilitu s přesnou verzí Odoo, závislosti, přístupová práva, bezpečnostně citlivé operace a způsob aktualizací. Instalaci/upgrade nejprve schval s uživatelem.
- Preferuj standardní Odoo funkcionalitu nebo malé, auditovatelné vlastní addony před zbytečnou third-party závislostí.
- Neupravuj Odoo core ani zdrojový kód third-party modulů. Funkčnost rozšiřuj vlastním modulem v `addons/custom/`.
- Respektuj projektové konvence Odoo 20 v `CLAUDE.md` a existujícím addonu; ověř je proti skutečnému kódu a testům, neaplikuj bez kontroly staré vzory z Odoo 19.

## Účetnictví a finance

- Projekt může zahrnovat české účetnictví, FX přecenění a později portfolio, ocenění investičních fondů, NAV a výkaznictví ČNB.
- Rozsah zahrnuje účetní jednotky používající české účetní rámce nebo IFRS; použitelný rámec se určuje pro konkrétní jednotku. Nepředpokládej účetní zacházení, klasifikaci instrumentu, metodu ocenění ani kurz bez explicitního zadání a ověřené účetní politiky.
- Každou změnu ovlivňující účetní zápisy, měny, FX, hlavní knihu, ocenění, alokace nebo NAV navrhuj konzervativně. Před implementací objasni účetní pravidlo, vstupy, datum účinnosti, zaokrouhlení, účetní dopad, storno/opravný postup a požadovanou auditní stopu.
- Odděluj standardní Odoo funkcionalitu od vlastních účetních rozšíření. Fondové/portfolio/NAV funkce nevytvářej automaticky bez schválených požadavků a účetní metodiky.
- Upřednostňuj auditovatelnost, reprodukovatelné výpočty, dohledatelnost vstupních dat a jasnou historii změn.
- U účetních UI akcí vždy popiš, zda jde o návrh, zaúčtování nebo párování a jaký bude finanční dopad. Databáze `odoo_cz` je výuková; Odoo 20 `investra_dev` je vývojová. Přesto nepředpokládej, že konkrétní akci lze bez následků vrátit.

## Secrets a Git

- `.env`, hesla, API klíče, tokeny a jiné secrets nesmí být commitovány. Nikdy nevypisuj celé hodnoty secrets do chatu, dokumentace, příkazového výstupu ani logů, pokud to není nezbytné.
- `.env.example` smí obsahovat pouze bezpečné placeholdery; skutečné hodnoty čti jen pokud je to nutné a nikdy je nevypisuj.
- `.gitignore` aktuálně ignoruje `.env` a `.env.*` s výjimkou `.env.example`; zároveň ignoruje zálohy databáze a `addons/third_party/odoomates/`. Před změnou `.gitignore` ověř `git check-ignore` a zda skutečný `.env` není sledován (`git ls-files --error-unmatch .env`).
- Third-party zdroj je evidován v `addons/third_party/README.md`; před změnou jeho verzování nebo obnovou ověř skutečný stav a vyžádej si souhlas, pokud jde o stažení/aktualizaci kódu.
- GitHub je verzovací a záložní systém projektu, ale automaticky neprováděj commit ani push.

## Změny, validace a testy

- Pokud uživatel žádá „zkontroluj“, nejprve pouze analyzuj; soubory neměň, pokud změna nebyla požadována.
- Před významnější změnou stručně sděl, co se změní a proč. Prováděj malé, vratné a snadno kontrolovatelné úpravy; neměň současně nesouvisející části.
- Po změně Docker Compose validuj příslušný soubor pomocí `docker compose -f <soubor> config --quiet` ještě před spuštěním služeb.
- Po změně Odoo addonu spusť dostupné relevantní testy. Testy a upgrade mohou měnit databázové schéma nebo data; před jejich spuštěním ověř cílovou databázi a použij izolované/testovací prostředí. Neprováděj testy proti produkčním datům.
- Při chybě validace nebo testu ji výslovně uveď; neskrývej ji a nepokračuj slepě dalšími změnami.
- Po dokončení shrň změněné soubory, účetní/provozní dopad a provedené kontroly.

## Komunikace a rozhodování

- Důležité technické kroky vysvětluj jednoduše česky a uveď, co má uživatel udělat dál.
- Pokud existuje bezpečnější a rizikovější postup, vysvětli rozdíl a preferuj bezpečnější variantu.
- Nepožaduj po uživateli ruční zadávání příkazů, které můžeš bezpečně provést sám; příkazy však nespouštěj, pokud by porušily pravidla souhlasu nebo mohly ohrozit data či běžící instance.
