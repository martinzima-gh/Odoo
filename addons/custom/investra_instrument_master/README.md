# Investra Instrument Master

Evidence nástrojů, emitentů a portfolií a číselníky ČNB a IFRS 9. Verze `20.0.0.5.0`, závisí na `investra_counterparty`
a `investra_instruments`. Plán a rozhodnutí: `docs/navrh-evidence-nastroju.md`, zadání úkolů `docs/ukoly/IM-*.md`.

## Co modul dělá

- **Číselníky** (Nastavení → Číselníky): druhy cenných papírů BA0088 (84 kódů, z toho 52 nabízených u nástroje) a jejich
  skupiny, sektory ESA (80 kódů) a typy emitenta, členství zemí v EU/EHP, oceňovací kategorie, důvody klasifikace.
  Záznamy nejdou mazat, jen deaktivovat; kód po založení nejde změnit; ruční úprava záznamu nastaví příznak „ručně změněno“.
- **Emitent** (rozšíření údajů protistrany): kód ESA, z něj typ emitenta, rezidentství, sektor ESA 2010 a region (CZ / EU / EHP /
  mimo EU podle členství k datu). Údaje mají verze „platí od“; potvrzenou verzi nejde měnit, změna = nová verze s důvodem.
- **Nástroj**: druh BA0088, CFI, páka, emise, nominál, kupón, podřízenost, podklad; upozornění na ISIN a CFI (neblokují);
  hlášení chybějících údajů klasifikace. Po potvrzení se druh, CFI, ISIN a emitent mění jen průvodcem s důvodem;
  změny jsou v Historii změn klasifikace. Test SPPI se posuzuje na nástroji (modul `investra_instruments`).
- **Portfolio**: kód, oceňovací kategorie, obchodní model (včetně „Nepoužije se“), důvod, strategie, schválení a uzavření,
  zámek po prvním obchodu, kontrola souladu zařazení nástrojů s kategorií portfolia.
- **Účetní profil**: role účtu a pravidla přiřazení (společnost, portfolio, druh nebo skupina BA0088, priorita, platnost);
  zařazení zobrazí profil a stav (v pořádku / chybí / odlišný). Nic se neúčtuje a role zařazení se nepřepisuje.

## Postup uživatele

1. **Emitent**: Emitenti a protistrany → založit údaje se zemí a kódem ESA → schvalovatel potvrdí.
2. **Nástroj**: vyplnit druh BA0088 (a CFI, emitenta, splatnost podle rodiny) → posoudit SPPI u dluhu → schvalovatel potvrdí klasifikaci.
3. **Portfolio**: vyplnit kód, kategorii, obchodní model, důvod a odborné zdůvodnění → schvalovatel schválí. Po prvním obchodu je zamčeno.
4. **Zařazení nástroje do portfolia**: musí odpovídat kategorii portfolia (jinak se neuloží).
5. **Účtování**: Nastavení → Účtování → Účetní profily a Přiřazení; zařazení bez profilu je ve stavu „chybí“.

## Práva

Skupina „Investra: správce číselníků“ upravuje číselníky, CFI mapu, členství zemí a účetní profily. Potvrzení emitenta
a nástroje a schválení portfolia smí jen skupina schvalování; kontrola je i v metodě, ne jen u tlačítka.
Čtení má čtenář účetnictví. Mazání nemá nikdo. Tabulka práv: `security/ir.access.csv`.

## Správa číselníků a nová metodika

Seed je v `data/*.xml` s `noupdate="1"`: upgrade modulu záznamy nepřepíše, ručně změněné se tedy neztratí.
Soubory `esa_code.xml`, `ba0088.xml` a `ba0088_group.xml` generuje `tools/codelist_seed.py` z katalogů v `docs/cnb/`
(ručně je neupravovat). Při nové metodice: obnovit katalog v `docs/cnb/`, spustit skript a nové kódy doplnit
(zatím ručně v číselníku; hromadný průvodce importem **není hotový**, viz níže). Zdroj a verze jsou v poli „Zdroj metodiky“
(např. `FOFI20261201 / D_S_RNBD_4`, `BA0088 v023.000`).

## Instalace a upgrade

- Instalace: `-i investra_instrument_master`; pro testy navíc `l10n_cz`. Verze v databázi ověřit v `ir_module_module`.
- Testy: dočasná databáze podle oddílu 2 plánu (`investra_ci_master`, po testech i s filestore smazat);
  `tools/run_tests.sh` je napevno na `investra_test`.
- Instalaci do `investra_test` a `investra_vzhled` uživatel povolil 15. 11. 2026, až po dokončení modulu a se zálohou předem;
  `investra_dev` se neinstaluje.
- Dotazy ke kontrole dat: `docs/sql/23-evidence-nastroju.sql` (jen čtení).

## Neimplementováno a otevřené (oddíl 8 plánu + výsledky úkolů)

- Průvodce importem číselníků (IM-02): sekce Výsledek úkolu je prázdná, v modulu průvodce není (jen `masterdata.change.wizard`).
- BA0088 je z testovacího portálu SDAT; před ostrým provozem porovnat s produkčním. Složení domény `D_S_CPMKT_1` není staženo.
- Členové EHP mimo EU a historie členství v EU před 1. 2. 2020; vazba kódů 1443000 a 2004430 na `Z_ESA2010`.
- Mezinárodní instituce: profil dál vyžaduje zemi (změna je červená zóna).
- `BANK_SECTORS` v `investra_counterparty` neobsahuje nerezidentní banky (2002100, 2002200): ověřit s metodikem.
- Návrh role účtu zařazení z účetního profilu a povinnost kategorie portfolia v databázi (červená zóna, později).
- `eu_status` se s plynutím času sám nepřepočítá; `classification_gap` zatím nehlásí chybějící SPPI (návrh na doplnění).
- Vzhled formulářů nebyl zkontrolován v prohlížeči.
