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

## Příkazy a bezpečnostní hook

Každé volání nástroje kontroluje hook `.agents/hooks.json` (guard `.agents/scripts/tool_guard.py`). Guard ani hook
neměň, neobcházej a nevypínej; jsou v zakázané zóně.

**Bez potvrzení** (guard je schválí):
- čtení: `git status`, `git diff`, `git log`, `git show`, `git branch` (výpis), `git config --get …`, `git remote -v`,
  `ls`, `cat`, `head`, `tail`, `wc`, `grep`, `find` (bez `-exec` a `-delete`) uvnitř `~/odoo-review`
- `python3 -m py_compile <soubor>`
- referenční výpočet NAV: `python3 -m unittest discover -s tools/nav_reference -p "test_*.py"` (z kořene workspace)
- kontrola XML: `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" <soubor>`
- `git add <soubory>` jen pro soubory z „Rozsahu souborů“ aktuálního úkolu a `git commit -m "…"`, obojí jen na větvi `ag/*`

**S potvrzením uživatele:** `git switch`, `git checkout`, vytvoření větve `ag/*`, `git pull`, `git merge` do `ag/*`,
`git fetch`, `git add` mimo rozsah úkolu, mazání a přesuny souborů, zápis do červené zóny, web, neznámé příkazy.

**Zakázané** (guard je zablokuje):
- `git push`, změny `git remote` a `git config`, `git rebase`, `git reset --hard`, `git clean`, tagy, větve mimo `ag/*`,
  commit a add mimo `ag/*`
- `docker`, `odoo`, `psql`, `pg_dump` a jakýkoli přístup k databázi; `pip`, `npm`, `brew`; `sudo`; `curl`, `ssh`
- čtení nebo zápis mimo `~/odoo-review`, tajemství (`.env`), zápis do zakázaných souborů
- `sh -c`, `bash -c`, `eval`, `env`, `xargs`, `python -c` s jiným kódem, `base64` a podobné
- řetězení a přesměrování (`;`, `&&`, `|`, `>`), substituce (`$(…)`, `` ` ``, `$PROMĚNNÁ`), nezakótované `*`, `?`, `~`

Jeden příkaz = jeden program. Místo `git log | head` použij `git log -n 5`; vzory pro `find` dej do uvozovek.

Testy Odoo nespouštíš (potřebují Docker a databázi). Spustí je Claude při převzetí.

## Výsledek

Na konci doplň do souboru úkolu sekci **Výsledek** a commitni ji:
- co jsi změnil (soubory),
- co jsi ověřil a jak (příkazy a výsledek),
- co jsi neověřil (např. vzhled v Odoo, testy Odoo),
- otevřené otázky a návrhy změn mimo rozsah.

Pak napiš uživateli název větve. Nemergeuj, nepushuj.
