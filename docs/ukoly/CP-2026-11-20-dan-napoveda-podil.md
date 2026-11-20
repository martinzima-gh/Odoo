# CP-2026-11-20-dan-napoveda-podil – vysvětlení Podílu a Neuznatelných nákladů v UI a manuálu

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená |
| Výchozí větev | `ukol/ZJ-07-dane-a-tridy` (nebo `main` po sloučení) |
| Větev úkolu | `cp/dan-napoveda-podil` |
| Zadal, dne | Martin / Claude, 2026-11-20 |
| Navazuje na | `ZJ-23-danove-vyjimky-sablona-a-procento.md` bod 4; výjimka: Copilot smí běžet i nad `~/odoo-dev` (bez commitu a pushe) |

**Cíl:** Uživatel pochopí pole Podíl a Neuznatelné náklady bez dotazu.

**Rozsah souborů:** `addons/custom/investra_nav/views/nav_views.xml` (jen záložka Daň ve formuláři fondu: krátký vysvětlující text
pod tabulkou Výjimky), `docs/manual/11-dan.md`.

**Obsah:** (1) Co je **Podíl**: část pohybu účtu, kterou řídí pravidlo řádku; zbytek zůstává ve výchozím pravidlu. Příklad 1:
zahraniční dividenda 5 000, Samostatný základ 15 %, podíl 60 % → 3 000 do samostatného základu, 2 000 do obecného. Příklad 2:
úplata 40 000, Mimo základ, podíl 25 % → 10 000 mimo základ, 30 000 snižuje základ. Kdy se používá: dělení účtu mezi dvě pravidla,
krácení nákladů na osvobozené výnosy; běžně 100 %. (2) Rozdíl proti **Neuznatelným nákladům (% z výnosu)**: u pravidla Mimo základ
je výsledek stejný; u zdaňovaného pravidla se částka přičte navíc k základu výchozího pravidla. (3) Pravidlo „výjimka na účtu úplaty
má přednost před volbou Základ: po kroku“.

**Mimo rozsah:** Python (`help=` polí řeší Claude v ZJ-23), nová pole, výpočet.

**Kritéria přijetí:** text na záložce Daň, kapitola v manuálu, příklady přepočítané (každé číslo sedí s oddílem 9.1 zadání dávky); modul
se povýší bez chyby.

## Výsledek

- **Změněné soubory:** `addons/custom/investra_nav/views/nav_views.xml` – text pod tabulkou Výjimky a pole tabulky vytažené z podmíněně skrytého `<group>`; `docs/manual/11-dan.md` – vysvětlení Podílu a Neuznatelných nákladů se dvěma příklady.
- **Ověřeno:** ruční přepočet příkladů: 5 000 × 60 % = 3 000 (zbytek 2 000); 40 000 × 25 % = 10 000 (zbytek 30 000). Zkontrolováno, že text rozlišuje Podíl od navýšení základu neuznatelnými náklady a uvádí přednost účetní výjimky před volbou Základ: po kroku.
- **Neověřeno:** upgrade modulu a zobrazení textu na instanci Odoo.
- **Otevřené otázky a návrhy mimo rozsah:** žádné.

## Převzetí

Doplní Claude.
