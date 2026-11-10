# AG-007 Přecenění cizích měn: výběr účtů

V profilu přecenění jde dnes z výběru přeceňovaných účtů otevřít a měnit nastavení samotného účtu (poznámka 2
z 10. 11. 2026). Výběr účtů má sloužit jen k výběru.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | zelená (jen formulář v XML pohledů) |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-007-preceneni-vyber-uctu` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | návrh nabídky a pořadí úkolů schválený 2026-11-10 |

**Cíl:** Přeceňované účty se zobrazí jako štítky („kód název“). Kliknutí na štítek účet neotevře a z výběru nejde
založit nový účet. U účtů zisku a ztráty z přecenění nepůjde z rozbalovacího seznamu založit nový účet.

**Rozsah souborů:** `addons/custom/investra_fx_revaluation/views/fx_views.xml` (jen záznam `view_fx_profile_form`)
a sekce Výsledek v tomto souboru. Modul `investra_fx_revaluation` je jinak v červené zóně: modely, data ani Python
neotvírej k úpravě.

**Změna** v záznamu `view_fx_profile_form`.

Bylo:
```xml
                        <field name="gain_account_id"/><field name="loss_account_id"/><field name="rate_source"/><field name="max_rate_age_days"/><field name="active"/>
                    </group>
                    <notebook><page string="Přeceňované účty"><field name="account_ids"/></page></notebook>
```
Bude:
```xml
                        <field name="gain_account_id" options="{'no_create': True}"/><field name="loss_account_id" options="{'no_create': True}"/><field name="rate_source"/><field name="max_rate_age_days"/><field name="active"/>
                    </group>
                    <notebook><page string="Přeceňované účty"><field name="account_ids" widget="many2many_tags" options="{'no_create': True}"/></page></notebook>
```

Když se blok „Bylo“ v souboru nenajde přesně, zastav se a napiš to do výsledku. Nic jiného neměň.

**Mimo rozsah:**
- Kód účtu v rozbalovacím seznamu (poznámka 1). Odoo ho standardně zobrazuje jako „kód název“. Chybí-li, je
  pravděpodobnou příčinou chybějící kód účtu ve společnosti profilu (kód je v Odoo 20 závislý na společnosti).
  Ověří Claude na běžící instanci, pohled to neřeší.
- Seznam profilů, přecenění (`investra.fx.run`), nabídky, modely, Python, testy.

**Ověření (z kořene repozitáře):**

```bash
python3 tools/view_check/check_views.py
```
Skončí „chyb: 0“ (formuláře skript nekontroluje, jde o kontrolu, že se nerozbil zbytek souboru).

```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('addons/custom/investra_fx_revaluation/views/fx_views.xml'); print('XML OK')"
```
Vypíše `XML OK`.

```bash
grep -c "no_create" addons/custom/investra_fx_revaluation/views/fx_views.xml
```
Vypíše `3`.

```bash
git diff --check && git diff --stat HEAD
```
Bez chyb; mění se jen `fx_views.xml` a tento soubor.

**Kritéria přijetí:**
- Příkazy výše projdou.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje `investra_fx_revaluation` v `investra_test`, spustí
  jeho testy a ve formuláři profilu ověří: štítky účtů s kódem, kliknutí na štítek nic neotevře, ve výběru
  chybí „Vytvořit“.

## Výsledek

Úkol provedl Copilot.

- **Změněné soubory:** `addons/custom/investra_fx_revaluation/views/fx_views.xml` (jen záznam `view_fx_profile_form`) a tento soubor (jen sekce Výsledek).
- **Ověřeno (příkaz a výsledek):** `python3 tools/view_check/check_views.py` — Zkontrolováno souborů: 11, chyb: 0; příkaz pro parsování XML — `XML OK`; `grep -c "no_create" addons/custom/investra_fx_revaluation/views/fx_views.xml` — 2 řádky obsahující `no_create`; `grep -o "no_create" addons/custom/investra_fx_revaluation/views/fx_views.xml` — 3 výskyty; `git diff --check` — bez výstupu; `git diff --stat HEAD` — změny pouze v XML pohledu a tomto souboru zadání.
- **Neověřeno:** chování formuláře v běžícím Odoo (štítky, kliknutí a nabídka „Vytvořit“); Odoo testy. Docker ani databáze nebyly spuštěny.
- **Otevřené otázky:** Zadání očekává 3 u `grep -c`, avšak tento přepínač počítá řádky s výskytem a vrací 2; v souboru jsou tři výskyty na dvou řádcích, potvrzené `grep -o`. Jiné otevřené otázky nejsou.

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
