# Zadání pro nezávislou revizi (prompt pro AI)

Vložit spolu se souborem `podklad-pro-revizi.md`. Doporučený postup je ve dvou krocích: nejdřív porozumění a otázky,
po odpovědích celá revize. Text níže se kopíruje celý.

---

## Krok 1: porozumění a otázky

Jsi zkušený architekt podnikových systémů se znalostí Odoo, účetnictví investičních fondů (NAV, třídy, IFRS 9)
a návrhu uživatelských rozhraní. Píšeš česky.

V příloze je podklad k projektu Investra na Odoo 20. Předpokládej, že o projektu nic nevíš kromě podkladu.
Nemáš přístup k repozitáři, kódu ani databázím. Když potřebuješ detail z dokumentu uvedeného v podkladu, zeptej se.

V tomto kroku nic nenavrhuj. Vrať:
1. Shrnutí projektu vlastními slovy na jednu stránku (cíl, subjekty, co je hotové, co se plánuje).
2. Seznam předpokladů, které z podkladu vyvozuješ, ale nejsou v něm výslovně.
3. Nejvýš 15 otázek, bez kterých by revize byla nepřesná, seřazených podle důležitosti. U každé uveď, co se bez odpovědi stane.

---

## Krok 2: revize a doporučení

Na základě podkladu a odpovědí na otázky zpracuj revizi. Cílem je doporučení až po závěr s jasnými kroky,
které pak provede vývojový AI agent (Claude Code) v repozitáři projektu a o kterých rozhodnou lidé.

### Co posoudit
1. **Architektura:** kniha = společnost Odoo, role účtů, jediný účtovací modul, rozdělení Odoo a IS. Silné stránky, rizika, alternativy.
2. **Využití Odoo:** co z Odoo použít, co koupit (Enterprise, moduly OCA), co vyvíjet. Odlišuj Community a Enterprise. Uveď, kde si nejsi jistý, že funkce v Odoo 20 existuje.
3. **Mezery k prvnímu fondu:** co chybí pro ostrý provoz prvního fondu ke konci Q1 2027 a pro účetnictví Investra Services; seřaď podle dopadu na termín.
4. **Uživatelsky přívětivé obrazovky:** navrhni obrazovky pro role z kapitoly 8 podkladu (účetní Services, účetní fondu, schvalovatel, vedoucí). Pro každou obrazovku:
   - účel a kdo ji používá,
   - textový náčrt rozložení (wireframe),
   - pole, akce a stavy,
   - kontroly a varování,
   - prázdný stav a chyby,
   - hromadné operace a klávesové zkratky,
   - jak ji postavit v Odoo 20: standardní formulář, seznam, kanban, průvodce (wizard), přehled; vlastní JavaScript (OWL) označ výslovně.

   Zaměř se hlavně na:
   - měsíční ocenění fondu od cen po zveřejnění kurzu,
   - přehled napříč desítkami fondů bez přepínání společností,
   - frontu ke schválení,
   - zadání přijaté faktury z PDF,
   - DPH identifikované osoby.
5. **Efektivita:**
   - počet kroků a kliknutí v hlavních procesech dnes a po návrhu,
   - co automatizovat (import cen, výpisy, výkazy, kontroly) a co ponechat ručně kvůli kontrole,
   - výkon a správa při desítkách společností,
   - údržba vlastních modulů při nových verzích Odoo.
6. **Rizika a soulad:** účetní, regulatorní, bezpečnostní a provozní rizika. Nedávej právní závěry; označ, co má ověřit auditor, daňový poradce, právník nebo ČNB.
7. **Harmonogram:** je realistický? Co přesunout, zjednodušit nebo udělat jinak.

### Pravidla
- Odlišuj fakta z podkladu, své odborné znalosti a domněnky. Domněnky označ.
- Kód nevidíš: u kroků akčního plánu popisuj chování a akceptaci, ne konkrétní implementaci; agent ji navrhne podle kódu.
- Nevymýšlej funkce Odoo ani paragrafy. Co neznáš jistě, označ „ověřit v Odoo 20“ nebo „ověřit v předpisu“.
- Respektuj pravidla z kapitoly 9 podkladu (auditovatelnost, čtyři oči, bez úprav jádra Odoo, osobní údaje investorů mimo Odoo, AI nerozhoduje).
- Nenavrhuj nic, co by vyžadovalo osobní údaje, hesla nebo důvěrné dokumenty.
- Kde je víc variant, dej doporučení a zdůvodni ho; rozhodnutí nech lidem.
- Buď konkrétní: místo „zlepšit UX“ napiš, co přesně změnit a jak to poznáme.

### Co vrátit (struktura výstupu)
1. **Shrnutí pro vedení** (nejvýš jedna stránka): hlavní závěry, 5 nejdůležitějších doporučení, co nedělat.
2. **Posouzení** podle bodů 1 až 7 výše.
3. **Návrhy obrazovek** podle bodu 4.
4. **Rozhodnutí pro lidi:** seznam rozhodnutí s variantami, doporučením a termínem, do kdy je potřeba rozhodnout.
5. **Akční plán pro vývojového agenta** jako blok YAML v přesně tomto formátu:

```yaml
- id: A01
  priorita: P0            # P0 blokuje první fond, P1 potřeba před ostrým provozem, P2 zlepšení, P3 později
  oblast: ocenění         # architektura | účetnictví Services | ocenění | výkazy ČNB | IS | UI | provoz | bezpečnost
  typ: kód                # kód | obrazovka | dokumentace | analýza | rozhodnutí
  nazev: Krátký název kroku
  popis: Co přesně udělat a proč
  dotcene_casti:          # moduly, modely, obrazovky nebo dokumenty z podkladu; nové označ „nový“
    - investra_nav
  akceptace:              # ověřitelná kritéria, nejlépe jako automatický test nebo kontrola v UI
    - Kritérium 1
  zavisi_na: [A00]
  odhad: S                # S do 1 dne, M do 1 týdne, L déle
  rozhoduje: člověk       # člověk | agent (agent může provést po schválení akčního plánu)
  riziko: Co se může pokazit a jak to poznat
```

   Seřaď kroky podle priority a závislostí. Krok typu „rozhodnutí“ nesmí mít `rozhoduje: agent`.
6. **Otevřené otázky** po revizi, pokud nějaké zůstaly.
