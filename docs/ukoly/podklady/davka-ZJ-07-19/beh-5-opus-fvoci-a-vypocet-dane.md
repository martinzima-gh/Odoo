# Běh 5 – Opus 5.5 (úsilí high): FVOCI a výpočet daně

```
Přečti CLAUDE.md, předávku běhu 4 a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen „Přednosti“, oddíl 1, oddíl 8 a oddíl 9
(9.1 řešení C a referenční příklady, 9.2 C0, C2–C5, 9.3 C3–C5 a C7).
Větev ukol/ZJ-07-dane-a-tridy. Schváleno; návrhy nespuštěné – převezmi, uprav, otestuj, odchylky do Výsledku ZJ-18 a ZJ-07.
Před G: SELECT pozic FVOCI v databázi investra – když nějaké jsou, zastav se a napiš kolik a jaké.
ROZSAH: G2 ocenění FVOCI (cílová rezerva, dluh/akcie, kurz, nevypořádaný obchod), sloupec OCI na řádku listu portfolio (pole),
G4 testy; C výpočet: engine._tax po pravidlech (plochý spec beze změny), _tax_item, _apply_base_correction, _book_tax po pravidlech,
G3 (odložená z OCI, realizace akcií FVOCI přes rozvahový účet se splatným pravidlem), rozpad daně jako počítané HTML pole ocenění,
kontroly ocenění (bez výchozího pravidla, chybějící účet, propadlý zápočet), migrace investra_nav 20.0.0.39.0 (C5) se zkouškou
na kopii, testy C7 + všechny referenční příklady z 9.1 a oddílu 1 (každé číslo), tools/nav_reference.
MIMO ROZSAH: XLS list Daň a závěrečné nasazení (běh 7), formuláře a manuál (Copilot, běh 6).
Po G a po C testy investra_nav+, investra_cnb+, investra_chart_fund+ a snímek 35/39 = beze změny (bez nového nastavení).
Commit po částech, push, předávka …-davka-beh-5.md se seznamem polí pro Copilota. Na konci mi napiš krátce: commity, odchylky,
tabulku referenčních čísel (očekávané | spočtené), testy, snímek.
```
