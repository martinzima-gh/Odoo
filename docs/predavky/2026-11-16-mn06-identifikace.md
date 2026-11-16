# Předávka: MN-06 identifikace společnosti (IČO, DIČ, LEI, ESA)

- **Cíl:** průvodce Nová účetní kniha a formulář knihy s IČO, DIČ, LEI, kódem ESA a existujícím kontaktem; sektor z kódu.
- **Stav:** větev `ukol/MN-manual`; testy `all` 779/779; v `investra` povýšeny `investra_entity` 20.0.0.11.0,
  `investra_counterparty` 20.0.0.5.0, `investra_chart_fund` 20.0.0.12.3, `investra_instrument_master` 20.0.0.8.0
  (záloha `zalohy/investra-2026-11-16-pred-MN06.dump`), 8071 restartována, nic nezaloženo.
- **Hotové:** sektor ESA 2010 z kódu (jen pro čtení), číselníky s kódem a hledáním podle kódu i názvu, názvy záznamu
  profilu, IČO (kontrola mod 11, uloženo v `additional_identifiers['CZ_EN']`) a DIČ ve formuláři knihy, průvodce
  s identifikací, existujícím kontaktem a upozorněním na stejné jméno, parametr `partner` v `create_book`, manuál kap. 1.
- **Zbývá:** Martin ověří v prohlížeči. První krok: Účetní knihy → Nová účetní kniha, vybrat Fond, zadat IČO 45274649
  (DIČ se předvyplní), zkusit kód ESA a existující kontakt; nic netvořit v `investra`, jen otevřít formulář a Zrušit.
- **Rozhodnutí:** bez nových; odchylky (IČO v CZ_EN, nabídka kontaktů přes `parent_id`) jsou ve Výsledku MN-06.
- **Otevřené:** který ze tří rezidentských kódů předvyplnit pro fond a investiční společnost (dnes prázdné); následné MN-07
  (fond a třídy) a MN-08 (kurzy).
- **Číst:** docs/ukoly/MN-06-identifikace-spolecnosti.md, addons/custom/investra_instrument_master/wizard/new_book.py.

Prompt: „Přečti CLAUDE.md a docs/predavky/2026-11-16-mn06-identifikace.md; pokračuj ověřením výsledku od Martina, poté MN-07.“
