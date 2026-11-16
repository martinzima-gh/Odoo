# MN-05b Průvodce Nová účetní kniha: po založení znovu načíst stránku

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (návratová akce průvodce; založení knihy se nemění) |
| Výchozí větev | `ukol/MN-manual` |
| Větev úkolu | `ukol/MN-manual` |
| Zadal, dne | Claude (hlavní relace), 16. 11. 2026 |
| Navazuje na | MN-05a; poznámka Martina z průchodu zakládání 16. 11. 2026 (kniha 02) |

**Chyba (Martin v prohlížeči, po MN-05a):** `TypeError: undefined is not an object (evaluating
'allowedCompanies.find((c) => c.id === companyId).child_ids')` v `activateCompanies`. Kniha i společnost se založily správně
(ověřeno SELECTem: společnost 12, kniha 11, 69 rolí).

**Příčina (ověřeno čtením kódu klienta v kontejneru):** seznam povolených firem klient načte jen při načtení stránky
(`web/static/src/core/user.js`, aktivní firmy v cookie `cids`). Formulář nové knihy narazí na pravidlo „Knihy podle
společnosti“, `form_controller.js` (`onError`, AccessError se `suggested_company`) zavolá `user.activateCompanies` s novou
firmou, kterou v načteném seznamu nenajde, a spadne. Kontext akce `allowed_company_ids` to neobejde.

**Oprava:** `action_create` místo `display_notification` s `next` vrátí `ir.actions.act_url` s `target: "self"` na URL formuláře
nové knihy (akce `investra_entity.action_entity`, záznam `entity.id`). Celé načtení stránky dá klientovi nový seznam firem;
formulář pak narazí na pravidlo, Odoo samo zapne novou firmu v přepínači (stejná cesta `onError` → `activateCompanies`
→ reload) a otevře knihu. Tím odpadá i hláška „Zapněte novou společnost v přepínači“ (nález MN-02 9) a kontext
`allowed_company_ids` v akci.

- Tvar URL ověřit v kódu Odoo 20 v kontejneru (`odoo/addons/web/controllers/`, routa `/odoo/...`; např.
  `/odoo/action-investra_entity.action_entity/<id>`), nevymýšlet.
- Pokud se ukáže, že automatické zapnutí firmy po načtení nenastane (např. `suggested_company` v chybě chybí), zvolit
  bezpečnou variantu: URL na seznam Účetních knih a v manuálu krok „zapněte společnost v přepínači“; popsat ve Výsledku.

**Test:** v testech průvodce ověřit typ `ir.actions.act_url`, `target == "self"` a že URL obsahuje id nové knihy.

**Manuál:** `docs/manual/01-spolecnost-a-kniha.md` – po založení se stránka znovu načte a otevře kniha s novou firmou
zapnutou; odstavec o ručním zapnutí v přepínači upravit (ponechat jen jako náhradní postup).

**Nasazení:** povýšení `investra_chart_fund` v `investra` se zálohou do `zalohy/` (souhlas v promptu), restart 8071.
V `investra` nic nezakládat.

**Rozsah souborů:** `investra_chart_fund/wizard/new_book.py`, jeho testy, verze v manifestu, README modulu (pokud popisuje
hlášku), `docs/manual/01-spolecnost-a-kniha.md`, tento soubor (Výsledek), předávka.

**Kritéria přijetí:** testy `investra_chart_fund` projdou na `investra_ci_*`; Výsledek uvádí ověřený tvar URL a že
v prohlížeči neověřeno (ověří Martin dalším založením knihy).

## Výsledek

Doplní model, který úkol provedl.

- **Změněné soubory:** `investra_chart_fund/wizard/new_book.py` (`action_create` vrací `ir.actions.act_url`, `target: self`,
  URL `/odoo/action-investra_entity.action_entity/<id>`; zrušeno `display_notification` i `allowed_company_ids` v akci),
  `tests/test_new_book.py`, `__manifest__.py` (20.0.0.12.2), `README.md` modulu, `docs/manual/01-spolecnost-a-kniha.md`
  (krok 4 a odstavec Přepínač firem; ruční zapnutí jen jako náhradní postup), tento soubor, předávka.
- **Ověřeno (příkaz a výsledek):**
  - Tvar URL: `web/static/src/core/browser/router.js` v kontejneru (část `action-<číslo|xml_id>` následovaná id záznamu).
  - `tools/run_tests.sh investra_chart_fund`: 0 failed, 0 error z 29 testů; dočasná `investra_ci_20261116_134531` smazána.
  - Záloha `zalohy/investra-2026-11-16-pred-MN-05b.dump` (pg_dump -Fc, 9 MB), `-u investra_chart_fund` v `investra` bez chyby,
    `ir_module_module.latest_version` = 20.0.0.12.2, instance 8071 znovu běží (`/web/login` vrací 200).
  - V `investra` nic nezaloženo.
- **Neověřeno:** chování v prohlížeči (načtení stránky, automatické zapnutí nové firmy přes `onError` →
  `activateCompanies`); ověří Martin dalším založením knihy. Fallback ze zadání (URL na seznam knih a ruční zapnutí)
  nebyl potřeba, v manuálu zůstává jako náhradní postup.
