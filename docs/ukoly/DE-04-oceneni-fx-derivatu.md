# DE-04 FX derivát v ocenění: reálná hodnota, přepočet podrozvahy, kontroly

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená (ocenění, NAV) – plán schvaluje Martin v promptu |
| Výchozí větev | `etapa/derivaty` (po předchozím kroku DE) |
| Větev úkolu | `etapa/derivaty` |
| Model | Opus |
| Zadal, dne | Claude (hlavní relace), 15. 11. 2026 |
| Navazuje na | `docs/navrh-fx-derivaty.md` (číst jen oddíly: Reálná hodnota, Účtování, Příklad, Kontroly ocenění, Testy), rozhodnutí 2026-11-15 „FX deriváty zjednodušeně“ |

**Cíl:** ocenění fondu spočte reálnou hodnotu otevřených smluv variantou B (nebo vezme ruční hodnotu), zaúčtuje
změnu a přepočte podrozvahu; výsledek je vidět v ocenění a ve FK.

**Schválený plán** (návrh Clauda; schválení Martina a datum doplní relace podle promptu):

1. **Výpočet** jako čistá funkce bez ORM (vzor výpočetního jádra ocenění), Decimal, zaokrouhlení na haléře až na
   konci: `RH(t) = V(t) − B0 × zbývající dny / dny celkem`. Vstupy (kurzy, B0, dny) se uloží k řádku ocenění.
   Kurzy ze zdroje kurzů ocenění (`_rate_source`, `investra.rate`).
2. **Ruční hodnota** k datu ocenění má přednost; přepočet do funkční měny kurzem ocenění; ocenění uloží spočtenou
   i ruční hodnotu a rozdíl. Tolerance rozdílu jako parametr fondu nebo společnosti (výchozí hodnotu navrhnout).
3. **Zapojení do ocenění** rozšířením `investra.valuation` v modulu `investra_derivative` (výpočet v `investra_nav`
   měnit jen o nezbytné místo napojení, popsat ve Výsledku): smlouvy fondu se stavem Sjednáno a otevřenou nohou
   k datu ocenění; řádek portfolia za smlouvu (hodnota může být záporná); návrh dokladu „Přecenění derivátů“
   se změnou proti zaúčtované RH smlouvy (kladná `derivative`, záporná `derivative_liability`, výsledek
   `gain_derivative` / `loss_derivative`); návrh dokladu „Přepočet podrozvahy“.
4. Opakovaný výpočet návrhy nahradí (`_clear`), vrácení a zrušení návrhu ocenění je odstraní, storno ocenění stornuje.
5. **Kontroly** podle návrhu (chyby a upozornění) do kontrol ocenění.
6. **Testy:** tabulka příkladu na haléř přes dvě ocenění a vypořádání; ostatní body oddílu Testy; stávající testy
   ocenění beze změny výsledků (fond bez derivátů se nesmí změnit ani o haléř).

**Rozsah souborů:** `investra_derivative/`, nezbytné místo napojení v `investra_nav/models/valuation.py` a pohled
ocenění, verze modulů, `docs/rozhodnuti.md`, tento soubor.

**Mimo rozsah:** přiřazení výsledku třídě, diskontování a sazby měn, výkazy ČNB, ukázková data, nasazení do `investra`.

**Kritéria přijetí:** testy `all` bez selhání; příklad sedí na haléř; FK = aktiva − závazky po každém kroku;
u fondu bez derivátů shodné výsledky ocenění jako před změnou (porovnání ve Výsledku).

## Výsledek

Doplní provádějící relace.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí
