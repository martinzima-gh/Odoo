# MN-03 Datum vzniku ve formuláři fondu a výchozí hodnoty nové třídy

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | oranžová (formuláře a výchozí hodnoty; datum vzniku určuje první oceňovací období, výpočet ocenění se nemění) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-02, Výsledek – nálezy 1 a 2 (ověřeno čtením kódu hlavní relací) |

**Nález 1:** `investra.fund.launch_date` („Datum vzniku“, `investra_nav/models/valuation.py:36`) není v žádném pohledu.
Bez něj první ocenění skončí chybou „Fond nemá datum vzniku.“ (`_period_start`). Fond založený v UI nejde ocenit.

**Nález 2:** seznam tříd ve formuláři fondu (`investra_fund/views/fund_views.xml`, pole `class_ids`) předává v kontextu
výchozí kusy a poplatky, ale ne `price_digits` a `price_rounding`. `price_digits` je povinné celé číslo bez výchozí
hodnoty: klient pošle 0 a `create` ho (`setdefault`) nepřepíše, takže třída tiše vznikne s 0 desetinnými místy kurzu.
`price_rounding` je skrytý povinný sloupec bez výchozí hodnoty.

**Plán (od Clauda):**

1. Datum vzniku do formuláře fondu: zděděný pohled v `investra_nav` (vzor `view_fund_form_history` v `nav_views.xml`),
   v hlavní skupině u Frekvence ocenění. Povinné není (stávající fondy), ale ve formuláři ho zvýraznit nápovědou.
2. Zámek: po prvním ocenění fondu, které není ve stavu Stornováno, nejde datum vzniku změnit, ve formuláři je jen
   pro čtení a `write` to odmítne srozumitelnou chybou (změna by posunula první oceňovací období). Výpočet nic dalšího.
3. Kontext `class_ids`: doplnit `default_price_digits` a `default_price_rounding` z fondu. Navíc v `create` třídy
   nespoléhat jen na klienta: pokud v kontextu výchozí hodnota není a hodnota chybí, doplnit z fondu (stávající chování).
4. Testy: formulář fondu (`odoo.tests.Form`) – nová třída přidaná řádkem dostane desetinná místa a zaokrouhlení kurzu
   z fondu; datum vzniku jde zadat, po ocenění (ne stornovaném) změna selže, po storno ocenění projde.
5. Povýšení `investra_fund` a `investra_nav` v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071.
6. Manuál: v `docs/manual/02-fond.md` a `03-tridy.md` upravit odstavce, které popisují nález 1 a 2 jako chybu.

**Rozsah souborů:** `investra_nav/views/`, `investra_nav/models/` (jen zámek data vzniku), `investra_fund/views/fund_views.xml`,
`investra_fund/models/fund.py` (jen `create` třídy), testy obou modulů, verze v manifestech, `docs/manual/02-fond.md`,
`03-tridy.md`, tento soubor (Výsledek), předávka.

**Mimo rozsah:** ostatní nálezy MN-02 (3–10), výpočet ocenění, migrace dat (stávající třídy nechat, jen ve Výsledku
vypsat SELECTem třídy s `price_digits = 0`, pokud v `investra` nějaké jsou).

**Kritéria přijetí:** testy obou modulů projdou na `investra_ci_*`; v `investra` je pole vidět; Výsledek uvádí,
co zůstalo neověřené v prohlížeči.

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:** `investra_nav/models/valuation.py` (pole `launch_locked`, `write` fondu se zámkem), `investra_nav/views/nav_views.xml`
  (pohled `view_fund_form_launch_date`), `investra_fund/views/fund_views.xml` (kontext `class_ids`), testy
  (`investra_fund/tests/test_fund.py`, nový `investra_nav/tests/test_launch_date.py`, `__init__.py`), manifesty
  (`investra_fund` 20.0.0.8.2, `investra_nav` 20.0.0.30.0), `docs/manual/02-fond.md`, `03-tridy.md`, tento soubor, předávka.
- **Ověřeno (příkaz a výsledek):** `tools/run_tests.sh investra_fund,investra_nav` → 0 failed, 0 error z 357 testů (první běh
  selhal na mém testu kvůli cache nestored compute, test opraven; kód beze změny); dočasná DB smazána. Záloha
  `zalohy/investra-2026-11-16-pred-MN03.dump`; upgrade `-u investra_fund,investra_nav` v `investra` bez ERROR; instance 8071
  restartována (HTTP 200); verze modulů 8.2 / 30.0; pohled `investra.fund.form.launch.date` v DB existuje; SELECT tříd s
  `price_digits = 0` v `investra` vrátil 0 řádků.
- **Neověřeno:** vzhled a chování v prohlížeči (pole u Frekvence ocenění, jen pro čtení po ocenění, předvyplnění nového řádku
  třídy); `create` třídy ponechán beze změny (`setdefault` už z fondu doplňuje, jen klientem poslaná 0 se nepřepíše – řeší
  kontext); test formuláře dokládá výchozí hodnoty přes `Form`.
- **Otevřené otázky a návrhy mimo rozsah:** zámek hlídá i ocenění v návrhu (každé nestornované); pokud má platit až od
  výpočtu, změnit domain. Nález MN-02 3–10 beze změny.
