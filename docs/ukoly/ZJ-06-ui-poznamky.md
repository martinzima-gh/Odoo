# ZJ-06 Poznámky z průchodu UI: seznamy, nabídky, ocenění z Přehledu, pravidla úplat

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (pohledy), oranžová (`investra_dashboard`), červená (`investra_nav/models`, `engine.py`, odstranění polí) – plán schválil Martin 17. 11. 2026 |
| Výchozí větev | `ukol/ZJ-zjednoduseni` |
| Zadal, dne | Claude (hlavní relace), 17. 11. 2026 |
| Model | Sonnet 5.5 pro zelenou a oranžovou část a body 6, 8, 9; bod 7 (výpočet základu úplat) Opus 5.5 |

**Kontext:** Martin prošel v UI založení fondu, úpisy a poplatky (předávka `docs/predavky/2026-11-17-ui-poznamky.md`); body probrány 17. 11. 2026,
rozhodnutí v deníku ze 17. 11. 2026 (ZJ-06). Daň je samostatný úkol `ZJ-07`.

**Postup po zónách** (každý balík: testy `tools/run_tests.sh`, commit do `ukol/ZJ-zjednoduseni`):

Zelená (pohledy)
1. Sloupec ID ve všech seznamech modulů `addons/custom/investra_*`: `<field name="id" optional="hide"/>`; standardní seznamy Odoo ne.
2. Ocenění, záložka Ručně doložené úplaty: `external_fee_ids` jen pro čtení, když `state not in ('draft', 'computed')` (zmizí koš i přidání).
   Zámek v modelu (`_check_open`) funguje a má test; v `investra` ocenění 38 (Odesláno) ruční úplatu dál má.
4. Nastavení → Fondy: Účetní knihy první, Fondy za nimi.
5. „Auditní stopa“ přejmenovat na „Schvalování a audit“, Schvalovací matici přesunout do ní jako první. Viditelnost položek podle skupin prověřit
   a návrh omezení předložit Martinovi (oranžová, bez schválení neměnit).
10. Pravidlo: Krystalizace a Třída krytí jen u druhu Výkonnostní odměna. U druhu Očekávaná daň skrýt Konvenci dnů, Základ a Základ před/po (daň je nepoužívá).
11. Verze sazby: v tabulce jen hlavní sloupce podle `parent.kind`; formulář verze se sekcemi Sazba a limity (sazba, práh, pevná částka a způsob,
    minimum, maximum, příplatek za pásmo a za třídu), Klouzavá pásma (vnořená tabulka `tier_ids`), Výkonnost (měřítko, HWM, počáteční hodnota,
    překážka, benchmark). Méně běžná pole (klouzavá pásma, příplatky za pásmo a za třídu, dohánění, váha pravděpodobnosti, strop, kladný výnos)
    ve sbalené sekci „Další parametry“. Co k druhu nepatří, skrýt.

Oranžová
3. Přehled: na kartě fondu tlačítko „Založit ocenění“, otevře nový návrh s předvyplněným fondem a očekávaným datem (`_dashboard_next`); datum lze přepsat.
   Kontroly pořadí ocenění beze změny.

Červená
6. Pravidlo úplaty: jedno pole „Statut a poznámka“ = `statute_ref` změněné na víceřádkový text; pole `note` odstranit (v `investra` prázdné u všech 13 pravidel;
   před odstraněním projít `tools/demo_data`, `tools/nav_demo`, testy, XLS v `package.py`).
7. Základ úplat a pořadí (nahrazuje rozhodnutí 2026-11-05 o parametru pořadí; minimální varianta schválená Martinem 17. 11. 2026):
   - pole `sequence` zrušit; pevné pořadí podle druhu: časově rozlišené úplaty → ručně doložené úplaty → výkonnostní odměna → daň;
   - časově rozlišená úplata, volba „Základ před/po“: **před** = stav před všemi úplatami v ocenění (snímek před první úplatou);
     **po** = stav po všech časově rozlišených a ručně doložených úplatách včetně počítané, dopočteno společně opakováním do ustálení
     (zobecnění dnešní smyčky v `engine.periodic_fee`); totéž pro základ Kapitál třídy (snímek za třídu); Průměrný FK beze změny;
   - výkonnostní odměna bez volby: vždy po ostatních úplatách, před sebou samou (jako dnes); daň bez volby, vždy nakonec z výsledku po všech úplatách;
   - mimo rozsah (možné rozšíření, až to bude vyžadovat statut): úplaty i výkonnostní odměna „po všech úplatách včetně výkonnostní odměny“;
   - testy: nahradit `test_rule_order_changes_base`; nové pro FK 1 000 000, obhospodařování 1 %, administrace 0,1 %, rok:
     obě před 10 000,00 / 1 000,00; obě po 9 891,20 / 989,12; obhospodařování před, administrace po 10 000,00 / 989,01 (ověřit výpočtem v testu);
   - očekávané hodnoty referenčních scénářů neměnit; když se změní, zastavit a říct Martinovi.
8. Verze sazby: dopočtené (neukládané) pole stavu verze; ukončená šedě, budoucí modře, sloupec „Platí do“ ne.
9. Třídy pravidla: v pohledu jen třídy fondu pravidla (po změně fondu vymazat); kontroly v modelu: třídy z fondu pravidla, třída nesmí být platící
   i přijímající, třída krytí nesmí být platící (smí být přijímající). Nápovědy polí.
10b. Krystalizace výkonnostní odměny: do výběru `crystallisation` přidat „Při každém ocenění“ (`valuation`; `_is_crystallisation` vrátí pravdu
    k datu každého ocenění); kalendářní volby měsíčně, čtvrtletně, ročně a „Nekrystalizuje“ beze změny. Test: dvě po sobě jdoucí ocenění, po prvním
    se posune srovnávací hodnota a HWM a naběhlá odměna se vynuluje. Krystalizace při odkupu mimo rozsah (rozhodnutí 2026-11-17).
11. Nápovědy polí verze sazby v modelu.

**Nasazení do `investra`:** až po výslovném souhlasu Martina, se zálohou (postup jako ZJ-05 krok 1); po upgradu znovu spočítat rozpracovaná ocenění.
Zveřejněná ocenění se nemění. U ukázkových fondů vyjde administrace mírně jinak (dnes počítá z FK po obhospodařování).

**Kritéria přijetí:** testy bez chyb; Martin v UI ověří body 2, 3, 4, 5, 10, 11 a výpočet úplat u Fondu A.

## Výsledek

Provedl Sonnet 5.5 (17. 11. 2026) na větvi `ukol/ZJ-zjednoduseni`; commity `792e9e8` (pohledy) a `b059bb9` (model). Do `investra` se nenasazovalo, nic se nepushovalo.
Testy `tools/run_tests.sh all` po obou balících: 848 a 856 testů, 0 chyb (dočasné databáze smazány).

| Bod | Stav | Poznámka |
|---|---|---|
| 1 | hotovo | `<field name="id" optional="hide"/>` v 42 samostatných seznamech modulů `investra_*` (vnořené tabulky ve formulářích a dědění seznamů ne). |
| 2 | hotovo | `external_fee_ids` je pro čtení mimo stavy Návrh a Spočteno (zmizí koš i přidání). Zámek v modelu beze změny. |
| 3 | hotovo | `investra.fund.action_create_next_valuation` a odkaz „Založit ocenění“ na kartě, když je stav dalšího ocenění „Nezaloženo“. Otevře nový formulář s fondem a očekávaným datem, nic nezaloží. Test `test_action_creates_next_valuation`. |
| 4 | hotovo | Účetní knihy (pořadí 5) před Fondy (10). |
| 5 | hotovo | „Auditní stopa“ → „Schvalování a audit“; Schvalovací matice je v ní první (pořadí 5). Aktualizován text hlášky ve `lock_exception.py` a manuál `04-oceneni-a-matice.md`. Omezení podle skupin viz Návrh níže. |
| 6 | hotovo | `statute_ref` je `Text` „Statut a poznámka“, `note` odstraněno z modelu i pohledů. Ostatní místa (`package.py` XLS, `tools/demo_data`, `tools/nav_demo`) `note` pravidla nepoužívají, `statute_ref` zůstává. |
| 8 | hotovo | Neukládané pole `validity_state` (Ukončená / Platná / Budoucí); v tabulce verzí řádek šedě a modře, štítek „Stav“, bez „Platí do“. |
| 9 | hotovo | Domény tříd ve formuláři pravidla, `onchange` na fond maže cizí třídy, `_check_classes` v modelu (třídy z fondu pravidla, platící ≠ přijímající, krytí ≠ platící). |
| 10 | hotovo | Krystalizace a Třída krytí jen u výkonnostní odměny; u daně skryty Konvence dnů, Základ a Základ před/po. |
| 10b | hotovo | Volba „Při každém ocenění“ (`valuation`), `_is_crystallisation` vrací pravdu; test `test_crystallisation_at_every_valuation` (+ kontrola, že měsíční volba uprostřed měsíce nekrystalizuje). |
| 11 | hotovo | Tabulka verzí: hlavní sloupce podle druhu; formulář verze (Sazba a limity, Výkonnost, záložka „Další parametry“ s pásmy, příplatky, dohánění, vahou, stropem, kladným výnosem). Nápovědy všech polí verze i pravidla. |
| 7 | **nedělal jsem** | Pole `sequence`, `base_mode` a `engine.py` jsou beze změny; zbývá Opus. Formulář i seznam pravidel pole Pořadí zatím mají. |

**Odchylky a upozornění**
- „Sbalená sekce“ je ve formuláři verze záložka „Další parametry“ (Odoo nemá pro formuláře sbalitelný blok); pásma jsou uvnitř ní.
- Verze sazby se v tabulce pravidla neupravuje přímo v řádku, ale ve formuláři verze (kliknutím na řádek).
- Sloupec `note` v tabulce `investra_fee_rule` Odoo při upgradu nemaže (zůstane osiřelý, v `investra` prázdný); případné odstranění sloupce je krok migrace a čeká na Martinův pokyn. Změna `statute_ref` z Char na Text proběhne při upgradu automaticky.
- Neověřeno v UI: formuláře (`parent.kind` v dialogu verze, domény tříd, odkaz „Založit ocenění“) jsou ověřené jen kontrolou pohledů a testy; je potřeba je projít v UI po nasazení.
- Existující pravidla v `investra`, která by porušila nové kontroly tříd, kontrola při upgradu neověřuje; ověřit SELECTem před nasazením.
- Konstrukce `tools/demo_data/seed.py` a `tools/nav_demo/demo.py` nebyla spuštěna; krystalizace „Při každém ocenění“ a nová pole je nevyžadují.

**Návrh k bodu 5 (neprovedeno, čeká na Martina):** všechny nabídky pod Nastavením jsou dnes bez `groups` a vidí je každý z `account.group_account_readonly` (kořen Investra). Přístupová práva ale už omezují obsah: Schvalovací matice zapisuje jen `group_investra_admin`,
Žádosti ke schválení a Úkony bez druhé osoby čtou všichni z readonly (podle společnosti). Návrh: (a) Schvalovací matici a Úkony bez druhé osoby nechat viditelné jen pro `group_investra_admin` a auditní role; (b) Žádosti ke schválení a Účetní události ponechat pro všechny;
(c) Výjimky z uzamčení pro `group_valuation_preparer`, `group_valuation_approver` a admina. Varianta 0: nic neměnit, protože právo čtení je záměrné (přehled rozhodnutí pro audit). Doporučení: varianta 0, dokud Martin nerozhodne, kdo má matici vidět.

## Převzetí
