# DE-03 FX derivát: účty a role, sjednání, vypořádání, storno

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (účtování, osnova, role) – plán schvaluje Martin v promptu |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Opus |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Podrozvaha, Účtování, Příklad, Neověřeno a otevřené), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** sjednání zapíše podrozvahu, vypořádání nohy zaúčtuje peněžní toky a zruší reálnou hodnotu, storno vše vrátí;
vždy s náhledem zaúčtování a záložkou dokladů.

**Schválený plán** (návrh Clauda; schválení Martina a datum doplní relace podle promptu):

1. **Ověření předpisů před kódem:** v primárním zdroji (Sbírka zákonů, MF) ověřit požadavky vyhlášky č. 501/2002 Sb.
   a ČÚS pro finanční instituce na podrozvahu u pevných termínových operací a na vykazování kladné a záporné RH
   derivátů; uvést paragraf nebo bod. Co ověřit nejde, označit. Při rozporu s návrhem se zastavit.
2. **Role** (`investra_entity`): `derivative_liability` (závazek), `gain_derivative`, `loss_derivative`,
   `offbalance_forward_receivable`, `offbalance_forward_payable`, `offbalance_clearing`.
3. **Účty:** navrhnout čísla a názvy v osnově `investra_fund` podle směrné účtové osnovy (podrozvaha typu
   `off_balance`), **předložit Martinovi ke schválení a počkat**; teprve pak doplnit šablonu osnovy a funkci, která
   účty a přiřazení rolí založí ve stávajících knihách přes ORM (žádné SQL). Výchozí přiřazení rolí pro nové knihy.
4. **Sjednat** (stav Návrh → Sjednáno): uloží na nohu `B0` a kurzy dne sjednání, zapíše podrozvahu každé nohy.
   Přes schvalovací matici stejně jako obchod.
5. **Vypořádat nohu** (v den vypořádání nebo později, ne před): dopočet RH na `V` kurzem dne vypořádání, oba
   peněžní toky na bankovních účtech fondu v příslušných měnách (uživatel vybere účty), zrušení RH, odúčtování
   podrozvahy nohy. Po poslední noze stav Vypořádáno. Blízká noha swapu stejným postupem.
6. **Storno** smlouvy nebo vypořádání s důvodem přes `_reverse_events`; zámek ocenění platí jako u obchodu.
7. Náhled a záložka dokladů zděděním `investra.posting.preview` (vzor `investra_nav/models/trade_preview.py`).
8. Testy podle návrhu (sjednání, storno, vypořádání podle příkladu na haléř, FK se podrozvahou nemění, fond v EUR).

**Rozsah souborů:** `investra_derivative/`, `investra_entity/data` (role), `investra_chart_fund` (účty, verze,
případná migrace), `docs/rozhodnuti.md`, `docs/navrh-fx-derivaty.md` (jen doplnění ověřených citací), tento soubor.

**Mimo rozsah:** výpočet RH při ocenění (DE-04), výkazy ČNB, ukázková data, nasazení do `investra`.

**Kritéria přijetí:** citace předpisů ověřené nebo označené; čísla účtů schválená Martinem (zapsat datum); testy
`all` na dočasné databázi bez selhání; MD = D u každého dokladu; po stornu nulové zůstatky podrozvahy i RH.

## Výsledek

Doplní provádějící relace.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí
