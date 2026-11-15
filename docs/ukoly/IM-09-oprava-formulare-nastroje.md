# IM-09 Oprava formuláře nástroje (emitent, odchylka od typu)

| Položka | Hodnota |
|---|---|
| Model | Haiku 5.5 (nebo Copilot/Antigravity v `~/odoo-review`) |
| Zóna | zelená (jen pohledy a popisky) |
| Číst | `addons/custom/investra_counterparty/views/counterparty_views.xml` (ř. 35–45), `addons/custom/investra_instruments/views/instrument_views.xml` (ř. 35–80), `addons/custom/investra_instrument_master/views/instrument_views.xml` |

**Nález (15. 11. 2026, snímek uživatele):** pohled `investra_counterparty` vkládá `issuer_id` přes
`//field[@name='isin']` `position="before"`. Po vzhledové úpravě 13. 11. je ISIN uvnitř `div.o_investra_metadata_item`
s vlastním `<label for="isin"/>`, takže Emitent skončil bez popisku pod nadpisem ISIN a ISIN se posunul o řádek níž.

**Cíl:**
1. Emitent má v hlavičce formuláře vlastní položku `o_investra_metadata_item` s popiskem (`<label for="issuer_id"/>`
   + `nolabel="1"`), umístěnou za položkou ISIN. Pořadí hlavičky: Typ, ISIN, Emitent, Měna (BA0088 a CFI z nového addonu
   zůstávají za Typem). XPath v `investra_instrument_master`, který cílí na `issuer_id`, musí dál fungovat.
2. Pole „Odchylka od návrhu typu“ (`deviates_from_type`): zaškrtávátko nahradit upozorněním, které je vidět jen při
   odchylce: pruh `alert alert-info` pod polem List ČNB s textem „List ČNB se liší od návrhu typu nástroje.“
   Pole samo zůstane v pohledu jako `invisible="1"`. Model se nemění.

**Rozsah souborů:** `investra_counterparty/views/counterparty_views.xml`, `investra_instruments/views/instrument_views.xml`.

**Mimo rozsah:** modely, styly (`investra_theme`), přesuny jiných polí, nové třídy CSS.

**Kritéria přijetí:**
- `python3 tools/view_check/check_views.py` → „chyb: 0“.
- Instalace a testy `investra_counterparty,investra_instruments,investra_instrument_master` na dočasné
  `investra_ci_master` podle oddílu 2 plánu: 0 selhání, 0 chyb; databázi po testech smazat. (Copilot/Antigravity testy
  nespouští; pustí je Claude při převzetí.)
- V sekci Výsledek výslovně napsat, že vzhled v prohlížeči nebyl ověřen, pokud nebyl.

**Commit:** `Formulář nástroje: emitent s popiskem, odchylka od typu jako upozornění`

## Výsledek

**Změněné soubory:** `addons/custom/investra_counterparty/views/counterparty_views.xml` (Emitent jako samostatná položka
`o_investra_metadata_item` s `<label for="issuer_id"/>` a `nolabel="1"`, vložená za položku ISIN přes `//field[@name='isin']/..`),
`addons/custom/investra_instruments/views/instrument_views.xml` (`deviates_from_type` je `invisible="1"`; pod skupinou s polem List ČNB
je pruh `alert alert-info` „List ČNB se liší od návrhu typu nástroje.“ viditelný jen při odchylce). Modely ani styly beze změny.
Pořadí hlavičky: Typ, BA0088, CFI, ISIN, Emitent, Měna. XPath v `investra_instrument_master` na `issuer_id` funguje (pohled se načetl).

**Kontrola pohledů:** `python3 tools/view_check/check_views.py` → 21 souborů, chyb: 0.

**Testy** (dočasná DB `investra_ci_master`, postup z oddílu 2 plánu; instalace `investra_counterparty,investra_instruments,investra_instrument_master`,
pak `l10n_cz`): `-u ... --test-tags /investra_counterparty,/investra_instruments,/investra_instrument_master` → 173 testů, 0 selhání, 0 chyb.
Dva řádky ERROR v logu jsou očekávané (docutils u popisu modulu; test povinného důvodu změny klasifikace). DB i filestore po testech smazány.

**Neověřeno:** vzhled v prohlížeči nebyl ověřen (jen načtení pohledů při instalaci a kontrola pohledů).

**Odchylky:** pruh je pod celou skupinou (dvousloupcovou), ne přímo pod polem List ČNB, protože pole je ve skupině; jinak by se rozbilo rozvržení.

## Převzetí

- 15. 11. 2026 (IM-12): v `investra_test` je kód načten (upgrade `investra_instruments`, `investra_nav` 20.0.0.28.9), registr bez chyb. `investra_vzhled` zatím ne, viz Výsledek IM-12.
