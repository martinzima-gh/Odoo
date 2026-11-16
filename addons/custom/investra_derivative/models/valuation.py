"""FX spot, forward a swap v ocenění fondu (DE-04): reálná hodnota variantou B, ruční hodnota, přepočet podrozvahy.

Napojení bez zásahu do `investra_nav`: ocenění se rozšiřuje děděním (`_compute_unsettled`, `_clear`,
`_position_balance`, `_run_checks`). Návrhy dokladů vznikají přes `_add_event`, takže je opakovaný výpočet nahradí,
vrácení a zrušení návrhu odstraní a storno ocenění stornuje stejně jako ostatní doklady ocenění.
Fond bez smluv: žádný řádek, doklad ani kontrola navíc.
"""
import json
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date

from ..calc import d, leg_fair_value, leg_value, money
from .posting import CLEARING, ROLES

# Výchozí tolerance rozdílu ruční a spočtené hodnoty: 0,10 % nominálu otevřených noh ve funkční měně (návrh Clauda
# v DE-04; lineární rozpouštění bodů se od ocenění banky liší řádově o setiny procenta nominálu).
DEFAULT_TOLERANCE_PCT = 0.10
# Stavy ocenění, ve kterých už ruční hodnotu použitou oceněním nejde změnit.
FROZEN_STATES = ("submitted", "approved", "posted", "sent", "confirmed", "published")


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    derivative_tolerance_pct = fields.Float(
        default=DEFAULT_TOLERANCE_PCT, digits=(6, 4), string="Tolerance ruční hodnoty derivátu (% nominálu)",
        help="Ocenění upozorní, když se ruční hodnota FX derivátu liší od spočtené o víc než toto procento nominálu "
             "otevřených noh ve funkční měně.",
    )


class InvestraValuation(models.Model):
    _inherit = "investra.valuation"

    derivative_line_ids = fields.One2many(
        "investra.valuation.derivative", "valuation_id", readonly=True, string="FX deriváty")

    def write(self, vals):
        if not self.env.su and "derivative_line_ids" in vals:
            raise UserError(self.env._("Stav a výsledky ocenění nastavuje jen postup ocenění."))
        return super().write(vals)

    def _clear(self):
        result = super()._clear()
        self.derivative_line_ids.unlink()
        return result

    def _compute_unsettled(self):
        result = super()._compute_unsettled()
        self._compute_derivatives()
        return result

    def _position_balance(self):
        """K účtům nástrojů přidá účty reálné hodnoty FX smluv (kladné i záporné), které role typů nástrojů nepokrývají."""
        balance = super()._position_balance()
        Mapping = self.env["investra.role.account"].sudo()
        roles = self.env["investra.instrument.type"].sudo().search([]).role_id
        roles |= self.env["investra.portfolio.classification"].sudo().search([("fund_id", "=", self.fund_id.id)]).role_id
        covered = Mapping.search([("company_id", "=", self.company_id.id), ("role_id", "in", roles.ids)])
        codes = [roles_[side] for roles_ in ROLES.values() for side in ("asset", "liability")]
        mine = Mapping.search([("company_id", "=", self.company_id.id), ("role_id.code", "in", codes)])
        extra = (mine.account_id | mine.extra_account_ids) - (covered.account_id | covered.extra_account_ids)
        return balance + self._sum(("account_id", "in", extra.ids)) if extra else balance

    # --- výpočet ---------------------------------------------------------------------------------------------------

    def _derivatives(self):
        """Smlouvy fondu sjednané do data ocenění, včetně vypořádaných a stornovaných (dorovnání zůstatků na nulu)."""
        return self.env["investra.derivative"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("trade_date", "<=", self.date), ("state", "!=", "draft"),
        ], order="trade_date, id")

    def _derivative_leg_inputs(self, leg):
        """Vstupy a výsledek nohy k datu ocenění; ukládají se k řádku ocenění, aby šel výpočet zopakovat."""
        buy_rate, sell_rate = self._fx(leg.buy_currency_id), self._fx(leg.sell_currency_id)
        value = leg_value(leg.buy_amount, buy_rate, leg.sell_amount, sell_rate)
        left, total = leg._days(self.date)
        fair = money(leg_fair_value(value, leg.b0, left, total))
        return {
            "settlement_date": fields.Date.to_string(leg.settlement_date),
            "buy": f"{leg.buy_amount} {leg.buy_currency_id.name}", "sell": f"{leg.sell_amount} {leg.sell_currency_id.name}",
            "buy_rate": str(buy_rate), "sell_rate": str(sell_rate), "value": str(money(value)), "b0": str(leg.b0),
            "days_left": left, "days_total": total, "fair_value": str(fair),
            "receivable": str(money(d(leg.buy_amount) * buy_rate)), "payable": str(money(d(leg.sell_amount) * sell_rate)),
        }

    def _compute_derivatives(self):
        Line = self.env["investra.valuation.derivative"].sudo()
        Classification = self.env["investra.portfolio.classification"].sudo()
        fair_lines, off_balance_lines, rows, portfolio_rows = [], [], [], []
        for derivative in self._derivatives():
            roles, extra = derivative._roles(), derivative._line_extra()
            open_legs = derivative._open_legs(self.date) if derivative.state != "reversed" else derivative.leg_ids.browse()
            asset, liability = derivative._booked_fair_value(self.date, valuation=self)
            booked = asset + liability
            try:
                inputs = [self._derivative_leg_inputs(leg) for leg in open_legs]
            except UserError as error:
                # Chybí kurz: smlouva se nepřecení a ocenění zastaví kontrola (docs/navrh-fx-derivaty.md, Kontroly ocenění).
                rows.append({"valuation_id": self.id, "derivative_id": derivative.id, "booked_before": float(booked),
                             "used_value": float(booked), "problem": error.args[0]})
                continue
            computed = sum((Decimal(row["fair_value"]) for row in inputs), Decimal(0))
            nominal = sum((max(Decimal(row["receivable"]), Decimal(row["payable"])) for row in inputs), Decimal(0))
            manual_record = derivative.value_ids.filtered(lambda v: v.date == self.date)[:1] if open_legs else None
            manual, problem = None, False
            if manual_record:
                try:
                    manual = money(d(manual_record.amount) * self._fx(manual_record.currency_id))
                except UserError as error:
                    problem = error.args[0]
            used = manual if manual is not None else computed
            # Reálná hodnota: změna proti zaúčtovanému stavu smlouvy; kladná na aktivní, záporná na pasivní účet.
            change = used - booked
            movement = "fx_revaluation" if derivative.kind == "spot" else "price_revaluation"
            label = {"name": self.env._("Přecenění %s", derivative.name)}
            fair_lines += [
                {"role": roles["asset"], "amount": max(used, Decimal(0)) - asset, "movement_type": movement, "extra": extra, **label},
                {"role": roles["liability"], "amount": min(used, Decimal(0)) - liability, "movement_type": movement,
                 "extra": extra, **label},
                {"role": roles["gain"] if change > 0 else roles["loss"], "amount": -change, "movement_type": movement,
                 "extra": extra, **label},
            ]
            # Podrozvaha: nominály otevřených noh kurzem ocenění, ostatní na nulu; rozdíl proti vyrovnávacímu účtu.
            targets = {leg: row for leg, row in zip(open_legs, inputs)}
            label = {"name": self.env._("Přepočet podrozvahy %s", derivative.name)}
            clearing = Decimal(0)
            for leg in derivative.leg_ids:
                row = targets.get(leg)
                for role, currency, target in (
                    (roles["receivable"], leg.buy_currency_id, Decimal(row["receivable"]) if row else Decimal(0)),
                    (roles["payable"], leg.sell_currency_id, -Decimal(row["payable"]) if row else Decimal(0)),
                ):
                    delta = target - derivative._ledger(role, self.date, currency=currency, valuation=self)
                    if delta:
                        clearing -= delta
                        off_balance_lines.append({"role": role, "amount": delta, "extra": extra, **label,
                                                  **derivative._currency_values(currency, 0)})
            if clearing:
                off_balance_lines.append({"role": CLEARING, "amount": clearing, "extra": extra, **label})
            if not open_legs and not booked and not change:
                continue  # Vypořádaná nebo stornovaná smlouva bez zůstatků: do ocenění nepatří.
            rows.append({
                "valuation_id": self.id, "derivative_id": derivative.id,
                "computed_value": float(computed), "has_manual": manual is not None,
                "manual_value": float(manual or 0), "manual_source": manual_record.source if manual_record else False,
                "manual_evidence": bool(manual_record and (manual_record.document or (manual_record.reason or "").strip())),
                "difference": float(manual - computed) if manual is not None else 0.0,
                "used_value": float(used), "booked_before": float(booked), "change": float(change),
                "nominal": float(nominal), "inputs": json.dumps(inputs, ensure_ascii=False), "problem": problem,
            })
            if open_legs or used:
                instrument = derivative.instrument_id
                classification = Classification._valid(derivative.portfolio_id, instrument, self.date)
                portfolio_rows.append({
                    "valuation_id": self.id, "kind": "derivative", "instrument_id": instrument.id,
                    "portfolio_id": derivative.portfolio_id.id, "classification_id": classification.id,
                    "name": derivative.name, "currency_id": self.fund_id.currency_id.id, "quantity": 1,
                    "price": float(used),
                    "price_source": (self.env._("Ruční hodnota: %s", manual_record.source) if manual is not None
                                     else self.env._("Výpočet ze spotového kurzu (varianta B)")),
                    "fair_value_currency": float(used), "fx_rate": 1.0, "fair_value": float(used),
                })
        self._add_event("derivatives", "Přecenění derivátů", fair_lines)
        self._add_event("derivatives_offbalance", "Přepočet podrozvahy", off_balance_lines)
        Line.create(rows)
        self.env["investra.valuation.portfolio"].sudo().create(portfolio_rows)

    # --- kontroly --------------------------------------------------------------------------------------------------

    def _run_checks(self, fund_capital, rounded):
        result = super()._run_checks(fund_capital, rounded)
        Derivative = self.env["investra.derivative"].sudo()
        if not Derivative.search_count([("fund_id", "=", self.fund_id.id)], limit=1):
            return result
        day = lambda value: format_date(self.env, value)
        overdue = self.env["investra.derivative.leg"].sudo().search([
            ("derivative_id.fund_id", "=", self.fund_id.id), ("derivative_id.state", "=", "agreed"),
            ("state", "=", "open"), ("settlement_date", "<=", self.date),
        ])
        self._check("derivative_settled", "Nohy derivátů po datu vypořádání jsou vypořádané", not overdue,
                    ", ".join(f"{leg.derivative_id.name} ({day(leg.settlement_date)})" for leg in overdue))
        lines = self.derivative_line_ids
        missing = lines.filtered("problem")
        self._check("derivative_rate", "Deriváty mají kurz měny k datu ocenění", not missing,
                    "; ".join(f"{line.derivative_id.name}: {line.problem}" for line in missing))
        undocumented = lines.filtered(lambda line: line.has_manual and not line.manual_evidence)
        self._check("derivative_manual_evidence", "Ruční hodnoty derivátů mají přílohu nebo důvod", not undocumented,
                    ", ".join(undocumented.derivative_id.mapped("name")))
        tolerance = d(self.fund_id.derivative_tolerance_pct) / 100
        deviating = lines.filtered(lambda line: line.has_manual and abs(d(line.difference)) > d(line.nominal) * tolerance)
        self._check(
            "derivative_manual_difference", "Ruční hodnoty derivátů odpovídají spočtené hodnotě v toleranci", not deviating,
            "; ".join(self.env._("%(name)s: ruční %(manual)s, spočtená %(computed)s, rozdíl %(diff)s",
                                 name=line.derivative_id.name, manual=line.manual_value, computed=line.computed_value,
                                 diff=line.difference) for line in deviating), severity="warning")
        drafts = Derivative.search([
            ("fund_id", "=", self.fund_id.id), ("state", "=", "draft"), ("trade_date", "<=", self.date)])
        self._check("derivative_draft", "Deriváty sjednané do data ocenění nejsou v návrhu", not drafts,
                    ", ".join(f"{derivative.name} ({day(derivative.trade_date)})" for derivative in drafts),
                    severity="warning")
        return result


class InvestraValuationDerivative(models.Model):
    """Řádek ocenění za smlouvu: spočtená a ruční reálná hodnota, rozdíl, zaúčtovaná změna a uložené vstupy výpočtu."""

    _name = "investra.valuation.derivative"
    _description = "FX derivát v ocenění"
    _order = "derivative_id"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="valuation_id.company_id.currency_id", string="Měna")
    derivative_id = fields.Many2one("investra.derivative", required=True, ondelete="restrict", index=True, string="Smlouva")
    kind = fields.Selection(related="derivative_id.kind", string="Druh")
    computed_value = fields.Monetary(currency_field="currency_id", string="Spočtená hodnota",
                                     help="Součet otevřených noh: V(t) − B0 × zbývající dny / dny celkem.")
    has_manual = fields.Boolean(string="Ruční hodnota zadána")
    manual_value = fields.Monetary(currency_field="currency_id", string="Ruční hodnota",
                                   help="Ruční hodnota k datu ocenění přepočtená kurzem ocenění do funkční měny.")
    manual_source = fields.Char(string="Zdroj ruční hodnoty")
    manual_evidence = fields.Boolean(string="Ruční hodnota doložena")
    difference = fields.Monetary(currency_field="currency_id", string="Rozdíl ruční − spočtená")
    used_value = fields.Monetary(currency_field="currency_id", string="Reálná hodnota v ocenění",
                                 help="Ruční hodnota, je-li k datu ocenění zadána; jinak spočtená.")
    booked_before = fields.Monetary(currency_field="currency_id", string="Zaúčtováno před oceněním")
    change = fields.Monetary(currency_field="currency_id", string="Změna do výsledku")
    nominal = fields.Monetary(currency_field="currency_id", string="Nominál otevřených noh")
    inputs = fields.Text(string="Vstupy výpočtu", help="Kurzy, B0 a dny otevřených noh k datu ocenění (JSON).")
    problem = fields.Char(string="Problém")


class InvestraDerivativeValue(models.Model):
    _inherit = "investra.derivative.value"

    def _check_not_used(self):
        """Ruční hodnotu, kterou použilo ocenění odeslané ke schválení nebo zaúčtované, nejde změnit ani smazat."""
        if self.env.su:
            return
        for value in self:
            used = self.env["investra.valuation.derivative"].sudo().search([
                ("derivative_id", "=", value.derivative_id.id), ("has_manual", "=", True),
                ("valuation_id.date", "=", value.date), ("valuation_id.state", "in", FROZEN_STATES),
            ], limit=1)
            if used:
                raise UserError(self.env._(
                    "Ruční hodnotu k %(day)s použilo ocenění %(valuation)s; nejdřív ocenění vraťte nebo stornujte.",
                    day=format_date(self.env, value.date), valuation=used.valuation_id.display_name))

    @api.model_create_multi
    def create(self, vals_list):
        values = super().create(vals_list)
        for value in values:
            self.env["investra.class.movement"]._check_valuation_lock(
                value.company_id, value.date, self.env._("Zadání ruční hodnoty derivátu"))
        return values

    def write(self, vals):
        self._check_not_used()
        return super().write(vals)

    def unlink(self):
        self._check_not_used()
        return super().unlink()
