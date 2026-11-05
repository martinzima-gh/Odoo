# Zadání pro kontrolora projektu

Tento soubor je zadání pro AI kontrolora (týdenní cloudová rutina i kontrola na vyžádání)
a vodítko pro lidského kontrolora. Kontrolor projekt **jen posuzuje**: nemění kód, dokumentaci
ani `main`. Jediný výstup je zpráva.

## Co číst

1. `CLAUDE.md` – cíl, pravidla, prostředí.
2. `docs/architektura.md` – export architektury z Claude Doc (zdroj pravdy je Doc).
3. `docs/rozhodnuti.md` – deník rozhodnutí.
4. `docs/otevrene-body.md` – otevřené body a rizika.
5. `docs/kontroly/` – předchozí zprávy (co už bylo nalezeno a zda se to vyřešilo).
6. Kód v `addons/custom/` a konfigurace (`docker-compose*.yml`, `.gitignore`, `.env.example`).
7. Změny od minulé kontroly: `git log --since="8 days ago" --stat`.

## Na co se dívat

**A. Soulad a konzistence**
- Rozpory mezi architekturou, deníkem rozhodnutí, otevřenými body a kódem.
- Rozhodnutí, která v architektuře chybí, nebo text, který je s nimi v rozporu.
- Otevřené body, které už jsou fakticky rozhodnuté (nebo naopak rozhodnutí, která jsou ve skutečnosti otevřená).

**B. Odborná správnost** (ověřovat proti veřejným zdrojům, uvést odkaz)
- Účetnictví fondů: vyhláška 501/2002 Sb., zákon o účetnictví, IFRS 9, IAS 21, IFRS 13, IAS 24.
- Regulace: ZISIF (240/2013 Sb.), NV 243/2013 Sb., vyhlášky ČNB k výkaznictví, DORA.
- Výkazy ČNB: veřejná metodika SDAT (https://sdat.cnb.cz/sdat_ext/ → Metodické informace → Výkazy,
  rámec „Fondy“). Hlídat novou verzi metodiky (aktuálně FOFI20261201) a dopady na datový model.
- Odoo 20 Community: zda navržené řešení odpovídá tomu, co Odoo umí (modely, multi-company, kurzy, přístupová práva v `ir.access`).

**C. Kvalita kódu a provozu**
- Chyby, chybějící testy, práva (multi-company pravidla), bezpečnost (hesla mimo git, porty jen na localhost).
- Konvence: vlastní kód jen v `addons/custom/`, žádné zásahy do core ani Odoo Mates.

**D. Návrhy na zlepšení**
- Co zjednodušit, co chybí pro audit a provoz, co by mělo být parametr místo kódu,
  co je potřeba rozhodnout dřív, než se začne programovat.

## Pravidla

- Vnitřní předpisy Investry, dokumenty DORA a dokumenty fondů v repozitáři nejsou a nesmí se do něj dostat.
  Odkazy na ně (název, článek) neověřuj, jen upozorni, pokud se zdají vzájemně nekonzistentní.
- Nic neuváděj jako fakt bez zdroje; nejistotu označ.
- Neopakuj nález z minulé zprávy, pokud se nic nezměnilo – jen ho uveď v seznamu „trvá“.
- Piš česky, stručně, pro finančníka a účetního metodika (nevysvětluj účetní základy).
- Žádná hesla, tokeny ani osobní údaje ve zprávě.

## Výstup

Soubor `docs/kontroly/RRRR-MM-DD.md` (datum běhu) v nové větvi `kontrola/RRRR-MM-DD`
a pull request do `main` s názvem „Kontrola projektu RRRR-MM-DD“. Do `main` nic přímo nezapisuj.

Pokud už větev nebo soubor s dnešním datem existuje (druhý běh v jednom dni), použij příponu
s časem UTC, např. `kontrola/RRRR-MM-DD-HHMM` a `docs/kontroly/RRRR-MM-DD-HHMM.md`.
Existující větve ani zprávy nepřepisuj. Za „minulou zprávu“ ber nejnovější soubor v `docs/kontroly/`
v `main` i v otevřených větvích `kontrola/*`.

Struktura zprávy:

```markdown
# Kontrola projektu RRRR-MM-DD

## Shrnutí
2–4 věty: celkový stav, nejdůležitější nález.

## Nálezy
| # | Závažnost | Oblast | Nález | Kde | Doporučení | Zdroj |
|---|---|---|---|---|---|---|
Závažnost: Vysoká (chyba v účetní nebo regulatorní logice, bezpečnost) / Střední / Nízká / Návrh.

## Trvá z minula
Nevyřešené nálezy z předchozích zpráv (číslo zprávy a nálezu).

## Vyřešeno od minula

## Otázky pro uživatele
Rozhodnutí, která kontrolor nemůže posoudit sám.
```

Když není co hlásit, zpráva obsahuje jen Shrnutí „Bez nových nálezů“ a sekci Trvá z minula.
