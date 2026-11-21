# ZJ-24 bod 15 – technický rozpis pro Sonnet (připravil poradce 2026-11-20 podle plánu v ZJ-24, který Martin schválil: a ano, b A, c ne)

**K6 (hláška nulového kapitálu) schválil Martin 2026-11-20.**

Stav kódu: větev `ukol/ZJ-24-hlasky-a-sazby` dc1a404. Modul `investra_nav`. Rozhodnutí: pravidlo úplaty se před svou první verzí sazby
neúčtuje (0) a ocenění ukáže upozornění; pravidlo **bez jakékoli verze** zůstává chybou. Výkonnostní odměna a daň beze změny (chyba z bodu 14).
Období plně pokrytá verzemi musí dát **přesně stejný výsledek jako dnes** (snímek 35/39 beze změny).

## K1 `addons/custom/investra_nav/engine.py` – `split_by_versions` (ř. ~73)
Nahraď tělo cyklu takto (docstring: „Období před první verzí vrací úsek s verzí None (úplata 0, ZJ-24 bod 15). Bez verzí chyba.“):
```python
    ordered = sorted(versions, key=lambda v: v["valid_from"])
    if not ordered:
        raise ValueError("Pravidlo nemá žádnou verzi sazby.")
    segments = []
    cursor = start
    while cursor < end:
        first_day = cursor + timedelta(days=1)
        valid = [v for v in ordered if v["valid_from"] <= first_day]
        following = [v for v in ordered if v["valid_from"] > first_day]
        seg_end = min(end, following[0]["valid_from"] - timedelta(days=1)) if following else end
        segments.append((cursor, seg_end, valid[-1] if valid else None))
        cursor = seg_end
    return segments
```
(Bez `valid` vždy existuje `following`, protože `ordered` není prázdné.)

## K2 `engine._segment_amount` (ř. ~123) – první řádek funkce:
```python
    if version is None:
        return ZERO, {"from": seg_start.isoformat(), "to": seg_end.isoformat(), "uncovered": True,
                      "fraction": "0", "variable": "0", "fixed": "0", "amount": "0"}
```
Minimum a maximum se tím uplatní jen na úseky s verzí (jsou až níže ve funkci).

## K3 `engine.periodic_fee` (ř. ~150)
```python
    segments = split_by_versions(start, end, rule["versions"])
    first_covered = next((i for i, (_s, _e, v) in enumerate(segments) if v is not None), None)
    uncovered_days = sum(((e - s).days for s, e, v in segments if v is None), 0)
```
V `compute` změň `first_segment=(index == 0)` na `first_segment=(index == first_covered)`.
Do vráceného slovníku přidej `"uncovered_days": uncovered_days` (ostatní klíče beze změny).

## K4 `models/fee_rule.py` – `_engine_rule` (ř. ~484)
Smaž blok s komentářem „ZJ-24 bod 14: engine by na mezeru…“ (podmínka `min(...) > start + timedelta(days=1)` a `raise self._no_rate_error(...)`).
Zůstane kontrola „nemá žádnou sazbu“. `_no_rate_error` a `_version_at` neměň. Když už `timedelta` v souboru nikdo nepoužívá, odstraň import.

## K5 `models/valuation.py` – `_apply_fees` (ř. ~1738)
Na začátek funkce (před `for rule in rules.filtered(lambda r: r.kind == "periodic")`):
```python
        start = self._period_start()
        late = []
        for rule in rules.filtered(lambda r: r.kind == "periodic" and r.version_ids):
            first = min(rule.version_ids.mapped("valid_from"))
            if first > start + timedelta(days=1):
                until = min(self.date, first - timedelta(days=1))
                late.append(self.env._(
                    "%(rule)s (fond %(fund)s): neúčtuje se %(since)s – %(until)s, první verze sazby platí od %(first)s",
                    rule=rule.name, fund=self.fund_id.display_name,
                    since=format_date(self.env, start + timedelta(days=1)), until=format_date(self.env, until),
                    first=format_date(self.env, first)))
        if late:
            self._check("fee_not_in_force", self.env._("Pravidla úplat začínají až po začátku období"), False,
                        "; ".join(late), severity="warning")
```
Import `from odoo.tools import format_date` a `timedelta`, pokud v souboru nejsou. Kontrolu zakládej **jen když něco najde** (jako `tax_no_rule`),
aby se u běžných ocenění nezměnil počet kontrol ani snímek. Úplata 0 → `_add_event` řádky s nulou vynechá, doklad nevznikne (nic dalšího neměň).

## K6 `models/valuation.py` – `_zero_capital_error` (ř. ~399), hláška u jiné třídy (schválený bod 5 plátna)
Dnes věta o úpisu před vznikem fondu padne i tehdy, když dřívější pohyb patří třídě **bez podílu** na společných položkách, a obecná hláška
neřekne, o které třídy jde. Uprav:
```python
    def _zero_capital_error(self, start, whole_fund):
        common = self.fund_id.class_ids.filtered("shares_common")
        domain = [("fund_id", "=", self.fund_id.id), ("date", "<=", start), ("state", "!=", "reversed")]
        if not whole_fund:
            domain.append(("class_id", "in", common.ids))
        early = self.env["investra.class.movement"].sudo().search(domain, order="date, id")
        if early and not self.previous_id:
            ...  # dosavadní hláška beze změny
        if whole_fund:
            return UserError(self.env._("Předběžný kapitál fondu je nulový."))
        return UserError(self.env._(
            "Předběžný kapitál tříd %(classes)s, které se podílejí na společných položkách, je nulový.",
            classes=", ".join(common.mapped("code"))))
```

## K7 Testy – nový `investra_nav/tests/test_zj24_bod15.py` (+ import v `tests/__init__.py`)
Engine (čisté funkce, bez DB; verze jako slovníky jako v `test_fee_started_month.py`):
1. období 31. 12. – 31. 1., jediná verze od 1. 3. → `amount == 0`, `uncovered_days == 31`, jeden úsek `uncovered`.
2. období 31. 12. – 31. 1., verze od 10. 1., sazba 1 % ročně, základ 1 000 000, act365 → částka = 1 000 000 × 0,01 × 22/365 (10.–31. 1.), `uncovered_days == 9`.
3. režim „Za každý započatý měsíc“, fixed_monthly 10 000, verze od 10. 1., období 31. 12. – 31. 1. → 10 000 (ne 0).
4. min_annual 120 000 s verzí od 10. 1. → minimum jen na 22 dní: max(var, 120 000 × 22/365).
5. `versions=[]` → `ValueError`.
6. dvě verze pokrývající celé období → výsledek shodný s výpočtem před změnou (porovnej s pevnou hodnotou z dnešního kódu – spočti ji před úpravou K1).
Ocenění (vzor fixtures z `test_zj24_messages.py`):
7. pravidlo s verzí od 10. 1., ocenění 31. 1. → úplata za 10.–31. 1., kontrola `fee_not_in_force` warning, ocenění se spočte.
8. pravidlo s verzí od 1. 3., ocenění 31. 1. → úplata 0, žádný doklad úplaty, kontrola `fee_not_in_force`.
9. Test hlášky z bodu 14 v `test_zj24_messages.py`, který dnes čeká chybu z `_engine_rule`: přepiš na výkonnostní odměnu
   (`_version_at` dál hlásí `_no_rate_error`).
10. K6: fond se dvěma třídami, třída B bez podílu má úpis před vznikem, třída A nic → hláška obsahuje „tříd A“ a neobsahuje větu o datu vzniku.

## K8 Ověření
`TestZj24Bod15`, `TestZj24Messages`, `TestFees`, `TestFeeStartedMonth`, `TestFeeCharacterization`, `TestFeeReferenceModel`, `TestFeeSolver`,
`TestFeeAverageClass`, `TestScenarios` → `tools/run_tests.sh investra_nav+` → `all`. Snímek 35/39 (`tools/snimek_na_kopii.sh`) shodný.
Verze `investra_nav` +1 v posledním čísle. Migrace není potřeba. Do ZJ-24 oddíl „Provedeno: bod 15 (datum)“ max 10 řádků.
