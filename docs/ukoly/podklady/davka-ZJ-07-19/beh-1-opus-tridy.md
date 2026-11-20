# Běh 1 – Opus 5.5 (úsilí high): třída portfolia a třída bez podílu (logika)

```
Přečti CLAUDE.md, předávku běhu 0 a v docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md jen „Přednosti“, oddíl 2 a oddíl 3 (vč. D6).
Větev ukol/ZJ-07-dane-a-tridy. Vše je schválené; návrhy kódu jsou nespuštěné – převezmi, uprav podle kódu, otestuj, odchylky do Výsledku ZJ-09/ZJ-08.
ROZSAH (Python, data, testy): A1 pole a zámek, A2 `_portfolio_class_lines` v `_create_event`, 2.3 deriváty / nevypořádané / kurzové
přecenění po třídách, A5 zrušení investra.instrument.class_id (SELECT napřed; při nenulovém výsledku zastav; ODEBER pole i z pohledu
instrument_views.xml, jinak modul nepůjde povýšit), A6, testy A7; D1 pole shares_common + zámek, D2 výpočet (`_class_context`,
`_shared_neutral`, `_class_value`, `_finish`, přemostění, `_apply_scheme`), kontrola na alokačním schématu, D5 testy, D6 upozornění
(computed pole + kontrola ocenění, BEZ úpravy formuláře). Čísla příkladů z oddílu 10 („Alokační schéma“ a „Třída bez podílu“) ověř testem
(test_allocation_examples.py); když vyjdou jinak, oprav text oddílu 10 v podkladech, ne výpočet, a napiš mi to.
MIMO ROZSAH (dělá Copilot v běhu 6): formulář portfolia (Třída), text třídy u obchodu, sloupec Třída v náhledu zaúčtování, přepínač na
formuláři třídy, zobrazení upozornění D6 ve formuláři pravidla, manuál.
Po A a po D: testy investra_instruments+, investra_nav+, investra_derivative+, investra_fx_revaluation+, investra_allocation+ a snímek
ocenění 35/39 porovnej se souborem z běhu 0 – musí být stejný. Commit po bodech, push. Předávka docs/predavky/…-davka-beh-1.md se
seznamem nových polí (model, název, popisek) pro Copilota. Zastav se jen podle podmínek z oddílu 0.
Na konci mi napiš krátce: commity, odchylky, testy, snímek, seznam polí pro Copilota.
```
