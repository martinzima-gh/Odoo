---
trigger: always_on
---

# Postup práce na úkolu

## Zadání

- Pracuješ jen na úkolech ze složky `docs/ukoly/` (soubor `AG-<číslo>-<název>.md`, šablona `_sablona.md`).
  Bez zadání můžeš jen analyzovat, diagnostikovat a revidovat; výsledek napiš do chatu, soubory neměň.
- Před začátkem si přečti zadání, zónu a rozsah souborů. U oranžové a červené zóny musí zadání obsahovat schválený plán;
  když chybí, nezačínej a napiš to.
- Kopii aktualizuje uživatel příkazem `git pull`; sám nic nestahuj.

## Větev a commity

1. `git switch -c ag/AG-<číslo>-<název>` z větve uvedené v zadání.
2. Malé commity s českou zprávou v rozkazovacím způsobu, např. „Uspořádat formulář ocenění do sekcí“.
   Autor commitů je nastavený na „Antigravity“; neměň ho.
3. Neměň soubory mimo rozsah zadání. Když je změna nutná, zastav se a popiš ji ve výsledku.

## Povolené příkazy (každý stejně schvaluje uživatel)

- `git status`, `git diff`, `git log`, `git show`, `git switch -c ag/...`, `git add`, `git commit`
- `python3 -m py_compile <soubor>`
- referenční výpočet NAV: `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` (pytest není nainstalovaný)
- kontrola XML, např. `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" <soubor>`
- `grep`, `ls`, `cat`, `find` uvnitř `~/odoo-review`

## Zakázané příkazy

- `git push`, `git merge` do jiné než `ag/*` větve, `git rebase`, `git reset --hard`, `git config`, `git remote`
- `docker`, `docker compose`, `odoo`, `odoo-bin`, `psql`, `pg_dump`, jakýkoli přístup k databázi
- `pip install`, `npm install`, `brew`, stahování a spouštění skriptů z internetu
- `rm -rf`, čtení nebo zápis mimo `~/odoo-review`, `sudo`

Testy Odoo nespouštíš (potřebují Docker a databázi). Spustí je Claude při převzetí.

## Výsledek

Na konci doplň do souboru úkolu sekci **Výsledek** a commitni ji:
- co jsi změnil (soubory),
- co jsi ověřil a jak (příkazy a výsledek),
- co jsi neověřil (např. vzhled v Odoo, testy Odoo),
- otevřené otázky a návrhy změn mimo rozsah.

Pak napiš uživateli název větve. Nemergeuj, nepushuj.
