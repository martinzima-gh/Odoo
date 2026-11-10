# AG-012 České názvy polí

Pole bez vlastního názvu Odoo popisuje anglicky podle technického jména (např. „Version“, „Fund“, „Entered By“).
Úkol doplní český název (`string=`) u 153 polí ve 13 modulech. Mění se jen popisky; data, výpočty ani databázová
struktura ne.

## Zadání

| Položka | Hodnota |
|---|---|
| Zóna | červená a oranžová podle cest (`models/`), ale **jen** doplnění argumentu `string=` podle tabulky níže |
| Výchozí větev | `feature/nav-prototyp` |
| Větev úkolu | `ag/AG-012-ceske-nazvy-poli` (připraví Claude z výchozí větve) |
| Zadal, dne | Claude na pokyn uživatele, 2026-11-10 |
| Navazuje na | podklad UX 2026-11-10 (anglické popisky na obrazovkách) |

**Cíl:** Formuláře, seznamy, filtry a exporty ukazují české názvy polí.

**Rozsah souborů:** soubory `addons/custom/investra_*/models/*.py` uvedené v tabulce a sekce Výsledek v tomto souboru.

**Pravidla:**
- U každého pole z tabulky přidej do volání `fields.…(…)` pojmenovaný argument `string="…"` přesně podle tabulky,
  jako **poslední** argument. Nic jiného na řádku neměň (pořadí, mezery, ostatní argumenty, komentáře).
- U víceřádkových definic (např. `fields.Selection([...], required=True, default="monthly",)`) přidej
  `string="…"` před uzavírací závorku, se stejným odsazením jako ostatní argumenty.
- Když pole v souboru nenajdeš nebo už `string=` má, nic nedomýšlej a napiš to do výsledku.
- Neměň hodnoty výběrů, `help`, `default`, `required`, metody ani testy.

**Schválený plán:** tabulka níže; schválil uživatel ____ (doplní Claude po schválení).

| Modul | Model | Pole | Název |
|---|---|---|---|
| investra_allocation | investra.allocation.scheme | fund_id | Fond |
| investra_allocation | investra.allocation.scheme | valid_from | Platí od |
| investra_allocation | investra.allocation.scheme | method | Metoda rozdělení |
| investra_allocation | investra.allocation.line | scheme_id | Schéma |
| investra_allocation | investra.allocation.line | class_id | Třída |
| investra_counterparty | investra.esa.sector | code | Kód |
| investra_counterparty | investra.esa.sector | name | Název |
| investra_entity | investra.account.role | code | Kód |
| investra_entity | investra.account.role | name | Název |
| investra_entity | investra.account.role | category | Druh |
| investra_entity | investra.account.role | active | Aktivní |
| investra_entity | investra.role.account | company_id | Kniha |
| investra_entity | investra.role.account | role_id | Role |
| investra_entity | investra.role.account | account_id | Účet |
| investra_entity | investra.entity | company_id | Společnost |
| investra_entity | investra.entity | entity_type | Druh jednotky |
| investra_entity | investra.entity | rate_source | Zdroj kurzů |
| investra_fund | investra.fund | entity_id | Účetní kniha |
| investra_fund | investra.fund | valuation_frequency | Frekvence ocenění |
| investra_fund | investra.fund.class | fund_id | Fond |
| investra_fund | investra.fund.class | code | Kód |
| investra_fund | investra.fund.class | name | Název |
| investra_fund | investra.fund.class | sequence | Pořadí |
| investra_fund | investra.fund.class | active | Aktivní |
| investra_fund | investra.fund.class | distribution | Rozdělování výnosu |
| investra_fund | investra.valuation.calendar | fund_id | Fond |
| investra_fund | investra.valuation.calendar | date | Datum ocenění |
| investra_fx_revaluation | investra.fx.profile | name | Název |
| investra_fx_revaluation | investra.fx.profile | active | Aktivní |
| investra_fx_revaluation | investra.fx.profile | company_id | Společnost |
| investra_fx_revaluation | investra.fx.run | company_id | Společnost |
| investra_fx_revaluation | investra.fx.run.line | run_id | Přecenění |
| investra_instruments | investra.instrument.type | code | Kód |
| investra_instruments | investra.instrument.type | name | Název |
| investra_instruments | investra.instrument.type | active | Aktivní |
| investra_instruments | investra.instrument | name | Název |
| investra_instruments | investra.instrument | currency_id | Měna |
| investra_instruments | investra.instrument.cashflow | instrument_id | Nástroj |
| investra_instruments | investra.instrument.price | instrument_id | Nástroj |
| investra_instruments | investra.instrument.price | fund_id | Fond |
| investra_instruments | investra.instrument.price | date | Datum |
| investra_instruments | investra.instrument.price | price | Cena |
| investra_instruments | investra.instrument.price | state | Stav |
| investra_instruments | investra.instrument.price | entered_by | Zadal |
| investra_instruments | investra.instrument.price | approved_by | Schválil |
| investra_instruments | investra.trade | fund_id | Fond |
| investra_instruments | investra.trade | instrument_id | Nástroj |
| investra_instruments | investra.trade | trade_date | Datum sjednání |
| investra_instruments | investra.trade | settlement_date | Datum vypořádání |
| investra_instruments | investra.trade | quantity | Množství |
| investra_instruments | investra.trade | price | Cena |
| investra_instruments | investra.trade | fx_rate | Kurz |
| investra_instruments | investra.trade | settlement_fx_rate | Kurz vypořádání |
| investra_instruments | investra.trade | event_id | Účetní událost |
| investra_instruments | investra.trade | settlement_event_id | Událost vypořádání |
| investra_nav | investra.fee.rule | fund_id | Fond |
| investra_nav | investra.fee.rule | name | Název |
| investra_nav | investra.fee.rule | sequence | Pořadí |
| investra_nav | investra.fee.rule | active | Aktivní |
| investra_nav | investra.fee.rule | kind | Druh |
| investra_nav | investra.fee.rule | base_source | Základ |
| investra_nav | investra.fee.rule | base_mode | Základ před/po úplatě |
| investra_nav | investra.fee.rule | expense_role | Nákladová role |
| investra_nav | investra.fee.rule | crystallisation | Krystalizace |
| investra_nav | investra.fee.version | rule_id | Pravidlo |
| investra_nav | investra.fee.version | valid_from | Platí od |
| investra_nav | investra.fee.version | fixed_mode | Výpočet za období |
| investra_nav | investra.fee.version | perf_measure | Měřítko výkonnosti |
| investra_nav | investra.fee.version | hurdle_kind | Překážka (hurdle) |
| investra_nav | investra.fee.version | hurdle_rate | Sazba překážky |
| investra_nav | investra.fee.version | hurdle_type | Typ překážky |
| investra_nav | investra.fee.version | catch_up | Dohánění (catch-up) |
| investra_nav | investra.fee.version | benchmark_id | Benchmark |
| investra_nav | investra.fee.tier | version_id | Verze pravidla |
| investra_nav | investra.fee.tier | amount_from | Od částky |
| investra_nav | investra.fee.tier | rate | Sazba |
| investra_nav | investra.benchmark | name | Název |
| investra_nav | investra.benchmark | value_ids | Hodnoty |
| investra_nav | investra.benchmark.value | benchmark_id | Benchmark |
| investra_nav | investra.benchmark.value | date | Datum |
| investra_nav | investra.benchmark.value | value | Hodnota |
| investra_nav | investra.benchmark.value | source | Zdroj |
| investra_nav | investra.instrument.repayment | event_id | Účetní událost |
| investra_nav | investra.class.movement | class_id | Třída |
| investra_nav | investra.class.movement | date | Datum |
| investra_nav | investra.class.movement | movement_type | Typ |
| investra_nav | investra.class.movement | units | Kusy |
| investra_nav | investra.class.movement | event_id | Účetní událost |
| investra_nav | investra.valuation.return.wizard | valuation_id | Ocenění |
| investra_nav | investra.fund.approval.step | fund_id | Fond |
| investra_nav | investra.fund.approval.step | sequence | Pořadí |
| investra_nav | investra.fund.approval.step | name | Název kroku |
| investra_nav | investra.valuation | fund_id | Fond |
| investra_nav | investra.valuation | date | Datum ocenění |
| investra_nav | investra.valuation | version | Verze |
| investra_nav | investra.valuation | state | Stav |
| investra_nav | investra.valuation | preparer_id | Zadal |
| investra_nav | investra.valuation | class_line_ids | Třídy |
| investra_nav | investra.valuation | fee_line_ids | Úplaty |
| investra_nav | investra.valuation | portfolio_line_ids | Portfolio |
| investra_nav | investra.valuation | check_ids | Kontroly |
| investra_nav | investra.valuation | approval_ids | Schválení |
| investra_nav | investra.valuation | external_fee_ids | Ručně doložené úplaty |
| investra_nav | investra.valuation | snapshot_hash | Otisk snímku |
| investra_nav | investra.valuation | return_reason | Důvod vrácení |
| investra_nav | investra.valuation | published_at | Zveřejněno |
| investra_nav | investra.valuation.class | valuation_id | Ocenění |
| investra_nav | investra.valuation.class | class_id | Třída |
| investra_nav | investra.valuation.class | perf_reference | Srovnávací hodnota odměny |
| investra_nav | investra.valuation.class | perf_hwm | High-water mark |
| investra_nav | investra.valuation.class | perf_accrued | Naběhlá odměna |
| investra_nav | investra.valuation.class | perf_base_date | Začátek období odměny |
| investra_nav | investra.valuation.fee | valuation_id | Ocenění |
| investra_nav | investra.valuation.fee | rule_id | Pravidlo |
| investra_nav | investra.valuation.fee | class_id | Třída |
| investra_nav | investra.valuation.fee | amount | Částka |
| investra_nav | investra.valuation.fee | detail | Výpočet |
| investra_nav | investra.valuation.external | valuation_id | Ocenění |
| investra_nav | investra.valuation.external | rule_id | Pravidlo |
| investra_nav | investra.valuation.external | class_id | Třída |
| investra_nav | investra.valuation.external | amount | Částka |
| investra_nav | investra.valuation.portfolio | valuation_id | Ocenění |
| investra_nav | investra.valuation.portfolio | kind | Druh |
| investra_nav | investra.valuation.portfolio | instrument_id | Nástroj |
| investra_nav | investra.valuation.portfolio | name | Název |
| investra_nav | investra.valuation.portfolio | currency_id | Měna |
| investra_nav | investra.valuation.check | valuation_id | Ocenění |
| investra_nav | investra.valuation.check | code | Kód |
| investra_nav | investra.valuation.check | name | Kontrola |
| investra_nav | investra.valuation.check | status | Výsledek |
| investra_nav | investra.valuation.check | detail | Podrobnosti |
| investra_nav | investra.valuation.approval | valuation_id | Ocenění |
| investra_nav | investra.valuation.approval | sequence | Pořadí |
| investra_nav | investra.valuation.approval | name | Krok |
| investra_nav | investra.valuation.approval | user_id | Schválil |
| investra_nav | investra.valuation.approval | approved_at | Schváleno dne |
| investra_posting | account.move | investra_event_id | Účetní událost Investra |
| investra_posting | investra.accounting.event | name | Název |
| investra_posting | investra.accounting.event | company_id | Společnost |
| investra_posting | investra.accounting.event | date | Datum |
| investra_posting | investra.accounting.event | event_type | Druh události |
| investra_posting | investra.accounting.event | key | Klíč |
| investra_posting | investra.accounting.event | fingerprint | Otisk |
| investra_posting | investra.accounting.event | move_id | Doklad |
| investra_posting | investra.accounting.event | reversal_move_id | Storno doklad |
| investra_posting | investra.accounting.event | state | Stav |
| investra_rates | investra.rate | source | Zdroj |
| investra_rates | investra.rate | date | Datum |
| investra_rates | investra.rate | currency_id | Měna |
| investra_rates | investra.rate | quantity | Množství |
| investra_rates | investra.rate | rate | Kurz |
| investra_rates | investra.rate | fetched_at | Staženo |
| investra_rates | investra.rate | document_hash | Otisk souboru |

**Mimo rozsah:** pole, která už `string=` mají, pole s `related=`, popisky v XML pohledů, hodnoty výběrů,
nápovědy (`help`), testy, `i18n/`, jazyk uživatelů.

**Ověření (z kořene repozitáře):**

```bash
python3 -m compileall -q addons/custom && echo OK
```
Vypíše `OK`.

Kontrola tabulky proti kódu (skript se nikam neukládá):
```bash
python3 - <<'EOF'
import ast, glob, re
rows = re.findall(r"^\| (investra_\w+) \| ([\w.]+) \| (\w+) \| (.+?) \|$",
                  open("docs/ukoly/AG-012-ceske-nazvy-poli.md").read(), re.M)
found = {}
for path in glob.glob("addons/custom/investra_*/models/*.py"):
    module = path.split("/")[2]
    tree = ast.parse(open(path).read())
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        model = next((s.value.value for s in cls.body if isinstance(s, ast.Assign)
                      and getattr(s.targets[0], "id", "") in ("_name", "_inherit")
                      and isinstance(s.value, ast.Constant)), None)
        for s in cls.body:
            if isinstance(s, ast.Assign) and isinstance(s.value, ast.Call) and getattr(s.value.func, "attr", None):
                kw = {k.arg: k.value for k in s.value.keywords}
                if "string" in kw and isinstance(kw["string"], ast.Constant):
                    found[(module, model, s.targets[0].id)] = kw["string"].value
bad = [(m, mo, f, want, found.get((m, mo, f))) for m, mo, f, want in rows if found.get((m, mo, f)) != want]
print("polí v tabulce:", len(rows), "nesouhlasí:", len(bad))
for b in bad: print(b)
EOF
```
Vypíše `polí v tabulce: 153 nesouhlasí: 0`.

```bash
git diff --check && git diff --stat HEAD
```
Bez chyb; mění se jen soubory `models/*.py` a tento soubor. Řádků přidaných = odebraných (každá změna jen doplní
argument na existujícím řádku), kromě víceřádkových definic.

**Kritéria přijetí:**
- Příkazy výše projdou.
- Při převzetí Claude (se souhlasem uživatele) aktualizuje dotčené moduly v `investra_test` a spustí testy.

## Výsledek

Doplní Antigravity nebo Copilot.

- **Změněné soubory:**
- **Ověřeno (příkaz a výsledek):**
- **Neověřeno:**
- **Otevřené otázky a návrhy mimo rozsah:**

## Převzetí

Doplní Claude: datum, commit sloučení, výsledek testů Odoo, nálezy z revize.
