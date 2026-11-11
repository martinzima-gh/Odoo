# Návrh: schvalovací matice obhospodařovatele

Stav: **návrh, čeká na odpovědi uživatele** (2026-11-11). Zóna: červená (schvalování ocenění, `record_guard`
a oprávnění). Podnět uživatele: na začátku bude málo lidí a ne všichni budou mít přístup; testy jsou jednodušší
bez druhé osoby.

## Jak to funguje dnes (ověřeno v kódu)

| Činnost | Kde | Pravidlo |
|---|---|---|
| Schválení ocenění | `investra_nav`, `action_approve` | fond: `second_person_required` (výchozí ano) nebo kroky `approval_step_ids`; zadavatel nesmí schválit, jeden člověk jen jeden krok |
| Schválení ceny | `investra_instruments`, cena `action_approve` | skupina schvalování ocenění; zadavatel nesmí schválit vlastní cenu – vždy, bez parametru |
| Potvrzení výjimky z uzamčení | `investra_nav`, žádost (vrstva 2 zámku) | jiný schvalovatel než žadatel – vždy |
| Ruční kurz a přepis kurzu | `investra_rates` | jen skupina, bez druhé osoby |
| Vrácení, storno a zveřejnění ocenění | `investra_nav` | jen skupina schvalování, bez druhé osoby |

Rozhodnutí 2026-11-04 „Schvalování ocenění“: **u fondů Investry povinná druhá osoba**. Matice, která druhou
osobu u ocenění vypne, toto rozhodnutí mění.

## Návrh

**Kde:** Nastavení → Fondy → Schvalovací matice, na úrovni obhospodařovatele (účetní kniha druhu
Investiční společnost). Fond dostane pole Obhospodařovatel (dnes vazba chybí); fond bez něj se řídí výchozí
maticí. Fond může jednotlivý řádek zpřísnit, nikdy zmírnit.

**Řádek matice** (činnost × pravidlo):

| Pole | Význam |
|---|---|
| Činnost | výběr z pevného seznamu níže; nové činnosti přidává jen kód |
| Kdo provádí | skupina Odoo (zadávání ocenění, schvalování ocenění), volitelně jmenovitě uživatelé |
| Druhá osoba | Ne / Ano / Kroky (pořadí schvalovatelů jako dnes `approval_step_ids`) |
| Kdo schvaluje | skupina, volitelně jmenovitě uživatelé |
| Platí od | datum; změna = nový řádek, historie zůstává (jako verze pravidel úplat) |

**Činnosti v první verzi:** schválení ocenění; vrácení a storno ocenění; zveřejnění ocenění; schválení ceny;
ruční kurz a přepis kurzu; potvrzení výjimky z uzamčení; ruční zadání úpisu a odkupu (bod 8); ruční přepsání
kategorie IFRS 9.

**Pojistky, aby vypnutí druhé osoby bylo vidět:**
- Úkon provedený bez druhé osoby se zapíše (kdo, kdy, podle kterého řádku matice) a ocenění ho ukáže jako
  upozornění v kontrolách – vidí ho schvalovatel, depozitář i auditor.
- Změnu matice smí jen skupina schvalování ocenění; změny se sledují (chatter) a první další ocenění ji ukáže
  v kontrolách.
- Zákaz „sám sobě“ platí i při vypnuté druhé osobě jen tam, kde je to nutné: výjimka z uzamčení zůstává vždy
  se dvěma lidmi (otázka 2).

**Testy:** automatické testy dál běží s druhou osobou a nově i bez ní (matice v testu). Ruční zkoušení v
`investra_test` půjde s maticí bez druhé osoby – to řeší podnět „pro testy bez 4 očí“.

**Dopad:** pole `second_person_required` a kroky schválení na fondu se převedou migrací do matice (výchozí =
dnešní chování, tedy druhá osoba ano). Doklady a ocenění se nemění.

## Otázky pro uživatele

1. **Ocenění bez druhé osoby:** smí matice druhou osobu u schválení ocenění vypnout? Mění to rozhodnutí
   2026-11-04 a musí to odpovídat vnitřním předpisům a statutům (řídicí a kontrolní systém obhospodařovatele,
   kontrola depozitářem). To neumím ověřit – doporučuji potvrdit s compliance. Varianta: vypnout jde jen
   jen v databázi s nainstalovaným modulem `investra_env_banner` (červený pruh TEST, instaluje se jen do testovací databáze), jinde ne.
2. **Výjimka z uzamčení** vždy dvě osoby bez ohledu na matici? Doporučuji ano.
3. **Úroveň:** matice u obhospodařovatele s možností zpřísnění u fondu – stačí, nebo chcete i zmírnění u fondu?
4. **„Kdo“** stačí skupinami Odoo (zadavatel ocenění, schvalovatel ocenění), nebo potřebujete jmenovité osoby
   a funkce (např. vedení fondu, compliance) jako samostatné role?

Doporučené pořadí: dokončit test vrstvy 2 zámku, pak matice, pak body A–E úpisů a odkupů (ruční úpis už
podle matice).
