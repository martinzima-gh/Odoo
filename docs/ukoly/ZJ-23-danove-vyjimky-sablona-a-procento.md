# ZJ-23 Daňové výjimky: šablona, jedno procento neuznatelnosti, nápověda

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (výpočet daně v `investra_nav`, migrace) – jen s plánem schváleným Martinem; texty a pohledy zelené |
| Výchozí větev | `main` (po sloučení dávky ZJ-07 až ZJ-19) |
| Větev úkolu | `ukol/ZJ-23-danove-vyjimky` |
| Zadal, dne | Martin, 2026-11-20 (poznámky 4 a 6) |
| Navazuje na | ZJ-07 (oddíl 9, D2, D10, D11), `docs/ukoly/ZJ-20-poznamky-zpracovani.md` |
| Model | Opus 5.5 (výpočet a migrace); texty a manuál Copilot |

**Cíl:** Zjednodušit nastavení daňových výjimek: jedno univerzální procento neuznatelnosti pro výnos i náklad, nastavitelná šablona
běžných výjimek místo hodnot napevno v kódu a srozumitelná nápověda k poli Podíl.

## Technický plán (návrh k schválení Martinem)

1. **Univerzální pole** `nondeductible_pct` na řádku výjimky (`investra.fund.tax.exception`): „Neuznatelné (% z částky)“. Výnosový účet:
   přičte se % z výnosu k základu výchozího pravidla (dnešní chování). Nákladový účet: přičte se % z nákladu zpět k základu
   (náklad základ sníží jen o zbytek). Dnešní omezení „jen u výnosového účtu“ se ruší. Výpočet: `valuation._tax_item` (jedna větev
   absolutní hodnoty pohybu), engine beze změny.
2. **Podíl** zůstává pro rozdělení účtu mezi dvě pravidla. Kontrola při uložení: řádek s pravidlem Mimo základ a podílem < 100 %
   spolu s procentem vyvolá upozornění (duplicitní zadání téhož).
3. **Šablona běžných výjimek:** nový sdílený model `investra.tax.exception.template` (kód účtu v šabloně `ifa_…`, pravidlo, podíl,
   % neuznatelnosti, poznámka, příznak „Při FVOCI“ pro D11). Nabídka Nastavení › Daně › Šablona výjimek. Tlačítko „Přidat běžné
   výjimky“ čte šablonu a kopíruje řádky do fondu (existující nepřepisuje, chybějící účet vypíše). Výchozí data = dnešní seznam
   z `action_add_common_tax_exceptions`. Rozhodnout: jen tlačítkem, nebo i automaticky při volbě výchozího pravidla u nového fondu.
4. **Nápověda a manuál (poznámka 6):** pole Podíl vysvětlit v `help`, v textu na záložce Daň a v kapitole Daň (`docs/manual/11-dan.md`):
   co je podíl (část účtu pro pravidlo řádku, zbytek zůstává ve výchozím), příklad zahraniční dividendy 60/40 a krácení nákladů
   (úplata 40 000 s podílem 25 % Mimo základ), kdy se používá a rozdíl proti Neuznatelným (%). Texty v zelené zóně připraví Copilot.
5. **Migrace:** stávající hodnoty se přenesou beze změny; hodnoty výjimek fondů zůstanou. Šablona se naplní z kódu.
6. **Otevřená otázka (poradce):** zda mají dividendy paušál 5 % z výnosu (původně praxe, § 25/1/zk ZDP je o podílu v dceřiné
   společnosti); do ověření nechat předvyplněné hodnoty v šabloně, ne v kódu.
7. **Testy:** referenční příklad ZJ-07 beze změny (4 200,00 / 4 237,50 / 750,00 / Rakousko 350,00); nákladový účet s 25 % → 10 000;
   šablona → tlačítko; migrace; snímek 35/39.

**Schválení:** plán schválil Martin zprávou „schvaluji“ dne 2026-11-20. Výchozí rozhodnutí: šablona se uplatní jen tlačítkem
„Přidat běžné výjimky“ (žádné automatické předvyplnění u nového fondu); paušál 5 % u dividend zůstane v šabloně jako výchozí
hodnota do vyjádření poradce.

## Výsledek

Doplní Claude po schválení plánu.

## Převzetí

Doplní Claude.
