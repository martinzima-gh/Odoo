"""Schéma výpočtu úplat na fondu (ZJ-12 krok 5, C.1): předvolby základu, náhled s čísly a informace o vzájemném dopočtu.

Náhled počítá STEJNÁ funkce jako ocenění (`engine.solve_fees`, `engine.periodic_fee`, `engine.performance_fee`); jen vstupy
jsou modelové (FK 1 000 000, sazby aktuálních verzí, rok, výnos +5 %), ne stav knihy. Do výpočtu ocenění tento soubor nezasahuje.
"""

from datetime import date
from decimal import Decimal

from markupsafe import Markup, escape

from odoo import api, fields, models

from .. import engine

PREVIEW_FK = Decimal(1000000)
PREVIEW_YIELD = Decimal("0.05")


def _fmt(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


class InvestraFundFeeScheme(models.Model):
    _inherit = "investra.fund"

    fee_scheme_preview = fields.Html(compute="_compute_fee_scheme", sanitize=False, string="Náhled schématu")
    fee_scheme_cycle_info = fields.Text(compute="_compute_fee_scheme", string="Vzájemný dopočet")

    @api.depends("fee_rule_ids.active", "fee_rule_ids.base_step", "fee_rule_ids.kind", "fee_rule_ids.class_ids",
                 "fee_rule_ids.version_ids.rate", "class_ids")
    def _compute_fee_scheme(self):
        for fund in self:
            rules = fund.fee_rule_ids.filtered("active")
            fund.fee_scheme_cycle_info = fund._fee_scheme_cycles(rules)
            fund.fee_scheme_preview = fund._fee_scheme_preview(rules) if rules else False

    # --- předvolby -----------------------------------------------------------------------------------------------

    def _apply_scheme_preset(self, periodic, performance, tax, name):
        """Nastaví základ aktivních pravidel; úplaty ze základu Aktiva nebo Bez základu volbu nemají (zůstávají 1).

        Změna se zapíše do historie každého pravidla (sledované pole) a souhrn do chatteru fondu (rozhodnutí 2026-11-19),
        aby bylo z fondu vidět, že šlo o předvolbu. Bez změny pravidla se nic nezapisuje.
        """
        self.ensure_one()
        changes = []
        for rule in self.fee_rule_ids.filtered("active"):
            step = {"periodic": periodic, "performance": performance, "tax": tax}[rule.kind]
            if step and rule.base_step != step and not (rule.kind == "periodic" and rule.base_source in ("assets", "none")):
                changes.append(f"{rule.name} {rule.base_step} → {step}")
                rule.base_step = step
        if changes:
            self.message_post(body=self.env._("Použita předvolba „%(name)s“ ve Schématu výpočtu (Základ: po kroku): %(changes)s.",
                                              name=name, changes=", ".join(changes)))

    def action_scheme_standard(self):
        """Standardní fond: úplaty po kroku 1, odměna po kroku 2, daň po kroku 3."""
        for fund in self:
            fund._apply_scheme_preset("1", "2", "3", self.env._("Standardní fond"))

    def action_scheme_net_fk(self):
        """Úplaty z výsledného FK: úplaty po kroku 4, daň po kroku 2 (odměna beze změny)."""
        for fund in self:
            fund._apply_scheme_preset("4", None, "2", self.env._("Úplaty z výsledného FK"))

    # --- vzájemný dopočet ------------------------------------------------------------------------------------------

    @api.model
    def _fee_scheme_cycles(self, rules):
        """Pravidla, která se počítají společně (cyklus závislostí mezi alespoň dvěma pravidly), jako text; jinak False.

        Pravidlo A závisí na B, když B patří do stavu po kroku, který je základem A (úplata 2, odměna 3, daň 4);
        odměna ani daň nezahrnují samy sebe. Zacyklení není chyba, společný dopočet ho umí.
        """
        stage = {"periodic": 2, "performance": 3, "tax": 4}
        rules = list(rules)
        depends = {r.id: {o.id for o in rules if o != r and stage[o.kind] <= int(r.base_step)} for r in rules}
        names = {r.id: r.name for r in rules}
        seen, groups = set(), []
        for rule in rules:
            if rule.id in seen:
                continue
            reach = self._reachable(rule.id, depends)
            group = sorted(o for o in reach if rule.id in self._reachable(o, depends) and o != rule.id) if reach else []
            if group:
                group = sorted(set(group) | {rule.id})
                seen.update(group)
                groups.append(group)
        if not groups:
            return False
        lines = []
        for group in groups:
            lines.append(", ".join(f"{names[i]} (po kroku {next(r.base_step for r in rules if r.id == i)})" for i in group))
        return self.env._(
            "Vzájemný dopočet: %s se počítají společně (každé je základem druhého); společný dopočet je ustálí. Není to chyba.",
            "; ".join(lines))

    @staticmethod
    def _reachable(start, depends):
        found, todo = set(), list(depends.get(start, ()))
        while todo:
            node = todo.pop()
            if node not in found:
                found.add(node)
                todo.extend(depends.get(node, ()))
        return found

    # --- náhled ------------------------------------------------------------------------------------------------------

    def _fee_scheme_items(self, rules):
        """Položky společného dopočtu s modelovým stavem; vrací (třídy, položky, poznámky)."""
        today = fields.Date.context_today(self)
        start, end = date(today.year, 1, 1), date(today.year + 1, 1, 1)
        fund_classes = self.class_ids
        count = len(fund_classes) or 1
        ids = fund_classes.ids or [0]
        each = PREVIEW_FK / count
        classes = {i: {"value": each, "ratio": Decimal(1) / count} for i in ids}
        notes, items = [], []
        names = {}

        def spec_for(rule):
            version = rule._version_at(today)
            return {"basis": rule.basis, "versions": [{**version._engine_values(), "valid_from": start}]}, version

        def recipients(rule):
            if not rule.recipient_class_ids:
                return {}
            return {"share": Decimal(str(rule.recipient_share)),
                    "recipients": {c.id: each for c in rule.recipient_class_ids}}

        for rule in rules.filtered(lambda r: r.kind == "periodic"):
            try:
                spec, _version = spec_for(rule)
            except Exception:  # pravidlo bez sazby: do náhledu nevstupuje
                notes.append(self.env._("%s: pravidlo nemá sazbu, v náhledu chybí.", rule.name))
                continue
            if rule.base_source == "assets":
                notes.append(self.env._("%s: základ Aktiva závisí na portfoliu, v náhledu chybí.", rule.name))
                continue

            def amount(value, spec=spec):
                return engine.periodic_fee(spec, start, end, value, classes_count=count)["exact"]

            step = int(rule.base_step)
            if rule.base_source == "none":
                targets, base, const = [None], None, amount(Decimal(0))
            elif rule.base_source == "average_fk":
                targets, base, const = [None], {"scope": "fund", "step": step}, None
            elif rule.base_source == "class_fk":
                targets, base, const = (rule.class_ids.ids or [None]), None, None
            else:
                targets, base, const = (rule.class_ids.ids or [None]), {"scope": "fund", "step": step}, None
            for target in targets:
                item_base = base
                if rule.base_source == "class_fk" and target:
                    item_base = {"scope": "class", "class": target, "step": step}
                elif rule.base_source == "class_fk":
                    item_base = {"scope": "fund", "step": step}
                key = ("fee", rule.id, target)
                items.append({"key": key, "stage": engine.STAGE_FEE, "payer": target, "kind": "periodic",
                              "rule": rule, "class": target, "base": item_base,
                              "amount": const if item_base is None else amount, **recipients(rule)})
                names[key] = rule.name
        for rule in rules.filtered(lambda r: r.kind == "performance"):
            try:
                _spec, version = spec_for(rule)
            except Exception:
                notes.append(self.env._("%s: pravidlo nemá sazbu, v náhledu chybí.", rule.name))
                continue
            hurdle = version.hurdle_kind
            if hurdle == "index":
                hurdle = "none"
                notes.append(self.env._("%s: překážka podle indexu je v náhledu vynechána.", rule.name))
            unit = version.perf_measure == "unit"
            for fund_class in rule.class_ids:
                if fund_class.id not in classes:
                    continue
                units = each / Decimal(1000) if unit else None
                reference = (Decimal(1000) if unit else each) / (1 + PREVIEW_YIELD)
                perf = {
                    "measure": version.perf_measure, "rate": version.rate, "reference": reference,
                    "hwm": reference if version.perf_use_hwm else None, "hurdle_kind": hurdle,
                    "hurdle_rate": version.hurdle_rate, "hurdle_margin": version.hurdle_margin,
                    "hurdle_type": version.hurdle_type, "catch_up": version.catch_up,
                    "hurdle_floor_zero": version.hurdle_floor_zero, "basis": rule.basis,
                    "require_positive_return": version.require_positive_return, "probability": version.probability,
                    "cap_rate": version.cap_rate or None,
                }

                def amount(value, perf=perf, units=units):
                    return engine.performance_fee(perf, start, end, value, units=units)["exact"]

                key = ("perf", rule.id, fund_class.id)
                items.append({"key": key, "stage": engine.STAGE_PERFORMANCE, "payer": fund_class.id,
                              "kind": "performance", "rule": rule, "class": fund_class.id,
                              "base": {"scope": "class", "class": fund_class.id, "step": int(rule.base_step)},
                              "amount": amount, **recipients(rule)})
        for rule in rules.filtered(lambda r: r.kind == "tax"):
            try:
                _spec, version = spec_for(rule)
            except Exception:
                notes.append(self.env._("%s: pravidlo nemá sazbu, v náhledu chybí.", rule.name))
                continue
            items.append({"key": ("tax", rule.id), "stage": engine.STAGE_TAX, "payer": None, "kind": "tax", "rule": rule,
                          "class": None, "tax": {"rate": version.rate, "step": int(rule.base_step),
                                                 "result": PREVIEW_FK * PREVIEW_YIELD, "booked": Decimal(0)}})
        return classes, items, notes

    def _fee_scheme_preview(self, rules):
        """Tabulka náhledu: částky z `engine.solve_fees` pro modelový FK 1 000 000 (stav po kroku 1)."""
        self.ensure_one()
        classes, items, notes = self._fee_scheme_items(rules)
        if not items:
            return Markup("<p class='text-muted'>%s</p>") % (escape(" ".join(notes)) or self.env._("Žádné pravidlo k náhledu."))
        try:
            solved = engine.solve_fees(classes, items)
        except ValueError as error:
            return Markup("<p class='text-danger'>%s</p>") % escape(str(error))
        codes = {c.id: c.code for c in self.class_ids}
        fk_final = PREVIEW_FK + sum(
            (engine.fee_effects(item, solved["amounts"][item["key"]], {k: v["ratio"] for k, v in classes.items()})[0]
             for item in items), Decimal(0))
        rows = []
        for item in items:
            amount = solved["amounts"][item["key"]]
            base = solved["bases"].get(item["key"])
            tax = solved["tax"] if item["kind"] == "tax" else None
            rows.append(Markup("<tr><td>%s</td><td>%s</td><td>%s</td><td class='text-end'>%s</td><td class='text-end'>%s</td></tr>") % (
                item["rule"].name, codes.get(item["class"], "") if item["class"] else "",
                self.env._("po kroku %s", item["rule"].base_step),
                _fmt(tax["base"] if tax else base) if (tax or base is not None) else "–", _fmt(engine.money(amount))))
        head = self.env._("Pravidlo"), self.env._("Třída"), self.env._("Základ"), self.env._("Částka základu"), self.env._("Částka za rok")
        table = Markup(
            "<table class='table table-sm'><thead><tr><th>%s</th><th>%s</th><th>%s</th><th class='text-end'>%s</th>"
            "<th class='text-end'>%s</th></tr></thead><tbody>%s</tbody></table>") % (*head, Markup("").join(rows))
        summary = Markup("<p><b>%s</b> %s</p>") % (self.env._("FK po úplatách, odměně a dani:"), _fmt(engine.money(fk_final)))
        info = Markup("<p class='text-muted small'>%s %s</p>") % (
            self.env._(
                "Náhled počítá stejná funkce jako ocenění (společný dopočet). Model: FK po kroku 1 %(fk)s, rok %(year)s, "
                "sazby aktuálních verzí, výnos za rok +5 %%, bez podílů příjemcům a bez oprav.",
                fk=_fmt(PREVIEW_FK), year=fields.Date.context_today(self).year),
            " ".join(notes))
        return table + summary + info
