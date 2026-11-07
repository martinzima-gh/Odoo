import hashlib
import json
from datetime import date as date_type, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .. import engine

BALANCE_SHEET = ("asset", "liability")
PREPARER = "investra_entity.group_valuation_preparer"
APPROVER = "investra_entity.group_valuation_approver"
STOPPING = ("stop",)
# Pole, která smí nastavit jen postup ocenění; přes API je uživatel nezapíše.
SYSTEM_FIELDS = {
    "state", "previous_id", "preparer_id", "fund_capital", "neutral_capital", "class_line_ids", "fee_line_ids",
    "portfolio_line_ids", "check_ids", "approval_ids", "event_ids", "snapshot", "snapshot_hash", "return_reason",
    "published_at", "package_id",
}


def d(value):
    return Decimal(str(value or 0))


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    launch_date = fields.Date(string="Datum vzniku", help="Začátek prvního oceňovacího období.")
    max_rate_age_days = fields.Integer(default=5, required=True, string="Nejvyšší stáří kurzu")
    approval_step_ids = fields.One2many("investra.fund.approval.step", "fund_id", string="Schvalovatelé před zaúčtováním")


class InvestraFundApprovalStep(models.Model):
    _name = "investra.fund.approval.step"
    _description = "Krok schválení"
    _order = "fund_id, sequence"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)


class InvestraValuation(models.Model):
    """Jedno ocenění fondu k datu ve verzi. Stavy vedou přes schválení k zaúčtování a zveřejnění."""

    _name = "investra.valuation"
    _description = "Ocenění"
    _order = "fund_id, date desc, version desc"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="fund_id.currency_id")
    date = fields.Date(required=True)
    version = fields.Integer(default=1, required=True, readonly=True)
    state = fields.Selection(
        [
            ("draft", "Návrh"),
            ("computed", "Spočteno"),
            ("submitted", "Ke schválení"),
            ("approved", "Schváleno"),
            ("posted", "Zaúčtováno"),
            ("sent", "U depozitáře"),
            ("confirmed", "Potvrzeno depozitářem"),
            ("published", "Zveřejněno a uzamčeno"),
            ("returned", "Vráceno"),
            ("reversed", "Stornováno"),
        ],
        default="draft",
        required=True,
        readonly=True,
    )
    previous_id = fields.Many2one("investra.valuation", readonly=True, string="Předchozí ocenění")
    preparer_id = fields.Many2one("res.users", readonly=True)
    fund_capital = fields.Monetary(readonly=True, string="FK")
    neutral_capital = fields.Monetary(readonly=True, string="NFK")
    class_line_ids = fields.One2many("investra.valuation.class", "valuation_id", readonly=True)
    fee_line_ids = fields.One2many("investra.valuation.fee", "valuation_id", readonly=True)
    portfolio_line_ids = fields.One2many("investra.valuation.portfolio", "valuation_id", readonly=True)
    check_ids = fields.One2many("investra.valuation.check", "valuation_id", readonly=True)
    approval_ids = fields.One2many("investra.valuation.approval", "valuation_id", readonly=True)
    external_fee_ids = fields.One2many("investra.valuation.external", "valuation_id")
    event_ids = fields.Many2many("investra.accounting.event", readonly=True, string="Doklady")
    snapshot = fields.Text(readonly=True, string="Snímek")
    snapshot_hash = fields.Char(readonly=True)
    return_reason = fields.Text(readonly=True)
    published_at = fields.Datetime(readonly=True)

    _uniq = models.Constraint("unique(fund_id, date, version)", "Verze ocenění k datu už existuje.")

    # --- práva ---------------------------------------------------------------------------------

    def _require(self, group):
        if not self.env.su and not self.env.user.has_group(group):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))

    def _require_state(self, *states):
        for record in self:
            if record.state not in states:
                raise UserError(self.env._("Krok není ve stavu %s možný.", record.state))

    # --- hlavní kniha --------------------------------------------------------------------------

    def _line_domain(self, *extra):
        self.ensure_one()
        drafts = self.event_ids.filtered(lambda e: e.state in ("draft", "locked")).move_id.ids
        return [
            ("company_id", "=", self.company_id.id),
            ("date", "<=", self.date),
            "|", ("parent_state", "=", "posted"), ("move_id", "in", drafts),
            *extra,
        ]

    def _sum(self, *extra):
        Line = self.env["account.move.line"].sudo()
        total = Line._read_group(self._line_domain(*extra), aggregates=["balance:sum"])[0][0]
        return d(total).quantize(engine.CENT, rounding=ROUND_HALF_UP)

    def _net_assets(self):
        """FK z rozvahy: aktiva a závazky včetně návrhů tohoto ocenění."""
        return self._sum(("account_id.account_type", "=like", "asset%")) + self._sum(
            ("account_id.account_type", "=like", "liability%")
        )

    def _assets(self):
        return self._sum(("account_id.account_type", "=like", "asset%"))

    def _period_start(self):
        self.ensure_one()
        if self.previous_id:
            return self.previous_id.date
        if not self.fund_id.launch_date:
            raise UserError(self.env._("Fond nemá datum vzniku."))
        return self.fund_id.launch_date

    def _delta(self, fund_class):
        """Změna rozvahových položek označených třídou za období."""
        start = self._period_start()
        return self._sum(
            ("investra_class_id", "=", fund_class.id),
            ("date", ">", start),
            ("account_id.account_type", "not like", "equity"),
            ("account_id.account_type", "not like", "income"),
            ("account_id.account_type", "not like", "expense"),
        )

    def _role_balance(self, role, *extra):
        account = self.env["investra.account.role"].account_for(self.company_id, role)
        return self._sum(("account_id", "=", account.id), *extra)

    # --- výpočet -------------------------------------------------------------------------------

    def action_compute(self):
        """Přepočte návrh ocenění. Opakovaný výpočet nahradí návrhy, nic nezdvojí."""
        self._require(PREPARER)
        self._require_state("draft", "computed")
        for record in self.sudo():
            record._compute_all()
        return True

    def _find_previous(self):
        return self.search([
            ("fund_id", "=", self.fund_id.id),
            ("date", "<", self.date),
            ("state", "in", ("posted", "sent", "confirmed", "published")),
        ], order="date desc, version desc", limit=1)

    def _clear(self):
        self.event_ids.filtered(lambda e: e.state == "draft")._discard_events()
        self.write({"event_ids": [(5,)]})
        self.class_line_ids.unlink()
        self.fee_line_ids.unlink()
        self.portfolio_line_ids.unlink()
        self.check_ids.unlink()

    def _class_context(self):
        """Předběžný kapitál, kusy a poměr tříd."""
        start = self._period_start()
        result = {}
        previous = {line.class_id: line for line in self.previous_id.class_line_ids}
        for fund_class in self.fund_id.class_ids:
            movements = self.env["investra.class.movement"].sudo().search([
                ("class_id", "=", fund_class.id), ("date", ">", start), ("date", "<=", self.date),
            ])
            prior = previous.get(fund_class)
            capital = d(prior.capital if prior else 0)
            units = d(prior.units if prior else 0)
            result[fund_class] = {
                "pre_capital": capital + sum((d(m.signed_amount) for m in movements), Decimal(0)),
                "units": units + sum((d(m.signed_units) for m in movements), Decimal(0)),
                "movements": movements,
                "previous": prior,
            }
        total = sum(row["pre_capital"] for row in result.values())
        if not total:
            raise UserError(self.env._("Předběžný kapitál fondu je nulový."))
        for row in result.values():
            row["ratio"] = row["pre_capital"] / total
        return result

    def _add_event(self, kind, name, lines, event_type="valuation"):
        lines = [line for line in lines if line["amount"]]
        if not lines:
            return self.env["investra.accounting.event"]
        for line in lines:
            line["amount"] = str(line["amount"])
        event = self.env["investra.accounting.event"]._create_event(
            self.company_id, f"valuation:{self.id}:{self.env.context.get('compute_run', 0)}:{kind}",
            f"{name} ({self.date})", self.date, event_type, lines,
        )
        self.event_ids = [(4, event.id)]
        return event

    def _compute_all(self):
        self._clear()
        self.previous_id = self._find_previous()
        self.preparer_id = self.env.user
        self = self.with_company(self.company_id)
        context = self._class_context()
        self._compute_portfolio()
        self._compute_bank_fx()
        for rule in self.env["investra.fee.rule"].search([("fund_id", "=", self.fund_id.id)]):
            if rule.kind == "periodic":
                self._apply_periodic(rule, context)
            elif rule.kind == "performance":
                self._apply_performance(rule, context)
            elif rule.kind == "tax":
                self._apply_tax(rule)
            else:
                self._apply_external(rule)
        self._apply_scheme(context)
        self._finish(context)
        self.state = "computed"

    def _rate_source(self):
        return self.fund_id.entity_id.rate_source

    def _fx(self, currency):
        """Měna fondu za jednotku měny, jen z vyhlášeného kurzu k datu."""
        Rate = self.env["investra.rate"]
        fund_currency = self.fund_id.currency_id
        if currency == fund_currency:
            return Decimal(1)
        source = self._rate_source()
        age = self.fund_id.max_rate_age_days
        return Rate.get_rate(source, currency, self.date, age) / Rate.get_rate(source, fund_currency, self.date, age)

    def _approved_price(self, instrument):
        price = self.env["investra.instrument.price"].search([
            ("fund_id", "=", self.fund_id.id), ("instrument_id", "=", instrument.id),
            ("date", "=", self.date), ("state", "=", "approved"),
        ], limit=1)
        if not price:
            raise UserError(self.env._("Chybí schválená cena %(name)s k %(day)s.", name=instrument.name, day=self.date))
        return price

    def _compute_portfolio(self):
        """Přecení nástroje a založí řádky listu portfolio; změna ceny a kurzu jde zvlášť."""
        Trade = self.env["investra.trade"].sudo()
        instrument_account = self.env["investra.account.role"].account_for(self.company_id, "instrument")
        rows, lines = [], []
        for instrument, quantity in Trade._positions(self.fund_id, self.date).items():
            price = self._approved_price(instrument)
            fx = self._fx(instrument.currency_id)
            value_ccy = d(quantity) * d(price.price)
            value = engine.money(value_ccy * fx)
            # Jen účet nástrojů: protiúčty přecenění nesou nástroj také, ale nejsou jeho účetní hodnotou.
            domain = [("investra_instrument_id", "=", instrument.id), ("account_id", "=", instrument_account.id)]
            carrying = self._sum(*domain)
            line_model = self.env["account.move.line"].sudo()
            foreign_raw = line_model._read_group(self._line_domain(*domain), aggregates=["amount_currency:sum"])[0][0]
            foreign = d(foreign_raw)
            foreign_currency = instrument.currency_id != self.fund_id.currency_id
            if foreign_currency:
                price_effect = engine.money((value_ccy - foreign) * fx)
                fx_effect = value - carrying - price_effect
            else:
                price_effect, fx_effect = value - carrying, Decimal(0)
            extra = {"investra_instrument_id": instrument.id}
            currency_values = {"currency_id": instrument.currency_id.id} if foreign_currency else {}
            if price_effect:
                lines.append({
                    "role": "instrument", "amount": price_effect, "movement_type": "price_revaluation", "extra": extra,
                    **({**currency_values, "amount_currency": str(value_ccy - foreign)} if foreign_currency else {}),
                })
                lines.append({
                    "role": "gain_fair_value" if price_effect > 0 else "loss_fair_value",
                    "amount": -price_effect, "movement_type": "price_revaluation", "extra": extra,
                })
            if fx_effect:
                lines.append({
                    "role": "instrument", "amount": fx_effect, "movement_type": "fx_revaluation", "extra": extra,
                    **({**currency_values, "amount_currency": "0"} if foreign_currency else {}),
                })
                lines.append({
                    "role": "gain_fx" if fx_effect > 0 else "loss_fx",
                    "amount": -fx_effect, "movement_type": "fx_revaluation", "extra": extra,
                })
            trades = Trade.search([("fund_id", "=", self.fund_id.id), ("instrument_id", "=", instrument.id), ("trade_date", "<=", self.date)])
            rows.append({
                "valuation_id": self.id,
                "kind": instrument.instrument_type,
                "instrument_id": instrument.id,
                "name": instrument.name,
                "isin": instrument.isin,
                "currency_id": instrument.currency_id.id,
                "quantity": quantity,
                "price": price.price,
                "price_source": price.source,
                "cost_currency": sum(t.quantity * t.price for t in trades),
                "cost": sum(t.quantity * t.price * t.fx_rate for t in trades),
                "fair_value_currency": float(value_ccy),
                "fx_rate": float(fx),
                "fx_source": self._rate_source() if foreign_currency else False,
                "fair_value": float(value),
            })
        self._add_event("portfolio", "Přecenění portfolia", lines)
        self.env["investra.valuation.portfolio"].sudo().create(rows)

    def _compute_bank_fx(self):
        """FX přecenění bank v cizí měně a řádky bank v listu portfolio."""
        account = self.env["investra.account.role"].account_for(self.company_id, "bank")
        Line = self.env["account.move.line"].sudo()
        groups = Line._read_group(
            self._line_domain(("account_id", "=", account.id)),
            groupby=["currency_id"],
            aggregates=["amount_currency:sum", "balance:sum"],
        )
        lines, rows = [], []
        for currency, amount, balance in groups:
            fx = self._fx(currency)
            value = engine.money(d(amount) * fx)
            difference = value - engine.money(balance)
            if currency != self.fund_id.currency_id and difference:
                lines.append({"role": "bank", "amount": difference, "movement_type": "fx_revaluation",
                              "currency_id": currency.id, "amount_currency": "0"})
                lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                              "movement_type": "fx_revaluation"})
            rows.append({
                "valuation_id": self.id,
                "kind": "bank",
                "name": f"Bankovní účty {currency.name}",
                "currency_id": currency.id,
                "fair_value_currency": float(d(amount)),
                "cost_currency": float(d(amount)),
                "cost": float(engine.money(balance)),
                "fx_rate": float(fx),
                "fx_source": self._rate_source() if currency != self.fund_id.currency_id else False,
                "fair_value": float(value),
            })
        self._add_event("bank_fx", "FX přecenění bank", lines)
        self.env["investra.valuation.portfolio"].sudo().create(rows)

    def _fee_record(self, rule, amount, fund_class=None, detail=None):
        self.env["investra.valuation.fee"].sudo().create({
            "valuation_id": self.id,
            "rule_id": rule.id,
            "class_id": fund_class.id if fund_class else False,
            "amount": float(amount),
            "detail": json.dumps(detail or {}, ensure_ascii=False, default=str),
        })

    def _class_value(self, fund_class, context):
        """Kapitál třídy podle aktuálního stavu knihy, před dalším krokem."""
        deltas = {c: self._delta(c) for c in context}
        neutral = self._net_assets() - sum(deltas.values())
        return context[fund_class]["ratio"] * neutral + deltas[fund_class]

    def _fee_base(self, rule, context, fund_class=None):
        if rule.base_source == "none":
            return Decimal(0)
        if rule.base_source == "assets":
            return self._assets()
        if rule.base_source == "class_fk" and fund_class:
            return self._class_value(fund_class, context)
        return self._net_assets()

    def _book_fee(self, rule, amount, fund_class, movement="fee", payable="fee_payable", kind_suffix=""):
        """Zaúčtuje úplatu: část příjemcům z tříd přes vnitřní zúčtování, zbytek jako náklad a závazek."""
        class_id = fund_class.id if fund_class else False
        share = d(rule.recipient_share) if rule.recipient_class_ids else Decimal(0)
        to_classes = engine.money(amount * share)
        external = amount - to_classes
        lines = []
        if external:
            lines += [
                {"role": rule.expense_role, "amount": external, "class_id": class_id, "movement_type": movement},
                {"role": payable, "amount": -external, "class_id": class_id, "movement_type": movement},
            ]
        if to_classes:
            lines += self._transfer_lines(fund_class, self._recipient_parts(rule, to_classes))
        self._add_event(f"fee:{rule.id}:{class_id}{kind_suffix}", rule.name, lines)

    def _recipient_parts(self, rule, amount):
        context = self._class_context()
        weights = {c: self._class_value(c, context) for c in rule.recipient_class_ids}
        weights = {c.code: max(v, Decimal(0)) for c, v in weights.items()}
        parts = engine.split_amount(amount, weights)
        return {c: parts[c.code] for c in rule.recipient_class_ids}

    def _transfer_lines(self, payer, parts):
        """Přesun hodnoty mezi třídami: účet vnitřního zúčtování má v součtu nulu, FK se nemění."""
        total = sum(parts.values())
        lines = [{"role": "internal_clearing", "amount": -total, "class_id": payer.id, "movement_type": "class_transfer"}]
        for fund_class, amount in parts.items():
            lines.append({"role": "internal_clearing", "amount": amount, "class_id": fund_class.id, "movement_type": "class_transfer"})
        return lines

    def _apply_periodic(self, rule, context):
        start, end = self._period_start(), self.date
        payers = rule.class_ids or [None]
        for fund_class in payers:
            base = self._fee_base(rule, context, fund_class)
            result = engine.periodic_fee(
                rule._engine_rule(start, end), start, end, base, classes_count=len(self.fund_id.class_ids)
            )
            self._fee_record(rule, result["amount"], fund_class, {"base": base, **result})
            self._book_fee(rule, result["amount"], fund_class)

    def _performance_state(self, rule, fund_class, row, version):
        """Srovnávací hodnoty, naběhlá odměna a období od poslední krystalizace."""
        previous = row["previous"]
        if previous and previous.perf_base_date:
            return d(previous.perf_reference), d(previous.perf_hwm), d(previous.perf_accrued), previous.perf_base_date
        initial = d(version.initial_reference)
        return initial, initial, Decimal(0), self.fund_id.launch_date

    def _is_crystallisation(self, rule):
        day = self.date
        month_end = (day + timedelta(days=1)).day == 1
        if rule.crystallisation == "month":
            return month_end
        if rule.crystallisation == "quarter":
            return month_end and day.month in (3, 6, 9, 12)
        if rule.crystallisation == "year":
            return month_end and day.month == 12
        return False

    def _apply_performance(self, rule, context):
        version = rule._version_at(self.date)
        for fund_class in rule.class_ids:
            row = context[fund_class]
            reference, hwm, accrued, base_date = self._performance_state(rule, fund_class, row, version)
            gross = self._class_value(fund_class, context) + accrued
            flows = []
            if version.perf_measure == "capital":
                movements = self.env["investra.class.movement"].sudo().search([
                    ("class_id", "=", fund_class.id), ("date", ">", base_date), ("date", "<=", self.date),
                ])
                flows = [(m.date, m.signed_amount) for m in movements]
            spec = {
                "measure": version.perf_measure,
                "rate": version.rate,
                "reference": reference,
                "hwm": hwm if version.perf_use_hwm else None,
                "hurdle_kind": version.hurdle_kind,
                "hurdle_rate": version.hurdle_rate,
                "hurdle_margin": version.hurdle_margin,
                "hurdle_type": version.hurdle_type,
                "catch_up": version.catch_up,
                "basis": rule.basis,
                "require_positive_return": version.require_positive_return,
                "probability": version.probability,
                "cap_rate": version.cap_rate or None,
            }
            if version.hurdle_kind == "index":
                spec["index_start"] = version.benchmark_id._value_at(base_date)
                spec["index_end"] = version.benchmark_id._value_at(self.date)
            result = engine.performance_fee(spec, base_date, self.date, gross, units=row["units"], flows=flows, accrued=accrued)
            self._fee_record(rule, result["move"], fund_class, {"gross": gross, "base_date": base_date, **result})
            self._book_fee(rule, result["move"], fund_class, payable="performance_payable")
            row["perf"] = {
                "reference": reference, "hwm": hwm, "accrued": result["required"], "base_date": base_date,
                "crystallise": self._is_crystallisation(rule) and result["required"] > 0,
                "measure": version.perf_measure,
            }
            if rule.cover_class_id and result["shortfall"] > 0:
                available = max(self._class_value(rule.cover_class_id, context), Decimal(0))
                covered = min(result["shortfall"], engine.money(available))
                lines = self._transfer_lines(rule.cover_class_id, {fund_class: covered})
                self._add_event(f"cover:{rule.id}:{fund_class.id}", f"Krytí {rule.name}", lines)
                self._fee_record(rule, -covered, fund_class, {"covered_by": rule.cover_class_id.code})

    def _apply_tax(self, rule):
        """Očekávaná daň jako doplatek do požadovaného zůstatku; základ je výsledek od začátku roku."""
        version = rule._version_at(self.date)
        year_start = date_type(self.date.year, 1, 1)
        tax_account = self.env["investra.account.role"].account_for(self.company_id, "expense_tax")
        result = -(
            self._sum(("date", ">=", year_start), ("account_id.account_type", "=like", "income%"))
            + self._sum(("date", ">=", year_start), ("account_id.account_type", "=like", "expense%"), ("account_id", "!=", tax_account.id))
        )
        required = engine.money(max(result, Decimal(0)) * d(version.rate))
        booked = self._sum(("date", ">=", year_start), ("account_id", "=", tax_account.id))
        move = required - booked
        self._fee_record(rule, move, None, {"base": result, "required": required, "booked": booked})
        self._add_event(f"tax:{rule.id}", rule.name, [
            {"role": "expense_tax", "amount": move, "movement_type": "fee"},
            {"role": "tax_payable", "amount": -move, "movement_type": "fee"},
        ])

    def _apply_external(self, rule):
        """Částka spočtená mimo Odoo: bez přílohy a důvodu ji ocenění nepřijme."""
        entries = self.external_fee_ids.filtered(lambda e: e.rule_id == rule)
        if not entries:
            raise UserError(self.env._("Pravidlo %s čeká na zadání částky spočtené mimo Odoo.", rule.name))
        for entry in entries:
            if not entry.attachment_id or not entry.reason:
                raise UserError(self.env._("U částky %s chybí příloha s výpočtem nebo důvod.", rule.name))
            amount = d(entry.amount)
            self._fee_record(rule, amount, entry.class_id, {"external": True, "reason": entry.reason})
            self._book_fee(rule, amount, entry.class_id, kind_suffix=f":{entry.id}")

    def _apply_scheme(self, context):
        """U pořadí nároků zaúčtuje rozdíl proti alokačnímu poměru jako přesun mezi třídami."""
        scheme = self.env["investra.allocation.scheme"].sudo()._for_date(self.fund_id, self.date)
        if not scheme or scheme.method != "waterfall":
            return
        start = self._period_start()
        deltas = {c: self._delta(c) for c in context}
        neutral = self._net_assets() - sum(deltas.values())
        pre_total = sum(row["pre_capital"] for row in context.values())
        change = neutral - pre_total
        fraction = engine.year_fraction(start, self.date, "act365")
        lines = scheme.line_ids
        tiers = []
        for rank in sorted(set(lines.filtered("target_rate").mapped("rank"))):
            tiers.append({
                line.class_id.code: context[line.class_id]["pre_capital"] * d(line.target_rate) * fraction
                for line in lines.filtered(lambda l: l.rank == rank and l.target_rate)
            })
        residual = {l.class_id.code: l.residual_share for l in lines if l.residual_share}
        capitals = {c.code: row["pre_capital"] for c, row in context.items()}
        loss_order = [l.class_id.code for l in lines.filtered("loss_rank").sorted("loss_rank")]
        targets = engine.waterfall(change, capitals, tiers, residual, d(scheme.residual_pro_rata), loss_order)
        transfers = {
            c: engine.money(targets[c.code]) - engine.money(row["ratio"] * change)
            for c, row in context.items()
        }
        rounding = -sum(transfers.values())
        if rounding:
            largest = max(transfers, key=lambda c: abs(transfers[c]))
            transfers[largest] += rounding
        event_lines = [
            {"role": "internal_clearing", "amount": amount, "class_id": c.id, "movement_type": "class_transfer"}
            for c, amount in transfers.items()
        ]
        self._add_event("waterfall", "Rozdělení mezi třídy", event_lines)

    def _finish(self, context):
        """Finální kapitál tříd, kurzy a kontroly."""
        fund_capital = self._net_assets()
        deltas = {c: self._delta(c) for c in context}
        neutral = fund_capital - sum(deltas.values())
        raw = {c: row["ratio"] * neutral + deltas[c] for c, row in context.items()}
        rounded = {c: engine.money(value) for c, value in raw.items()}
        remainder = fund_capital - sum(rounded.values())
        if remainder:
            rounded[max(sorted(rounded, key=lambda c: c.code), key=lambda c: rounded[c])] += remainder
        rows = []
        for fund_class, row in context.items():
            value = rounded[fund_class]
            value_class = value
            if fund_class.currency_id != self.fund_id.currency_id:
                value_class = value / self._fx(fund_class.currency_id)
            digits = Decimal(1).scaleb(-fund_class.price_digits)
            method = ROUND_DOWN if fund_class.price_rounding == "down" else ROUND_HALF_UP
            price = (value_class / row["units"]).quantize(digits, rounding=method) if row["units"] else Decimal(0)
            perf = row.get("perf") or {}
            previous = row["previous"]
            reference = d(previous.perf_reference) if previous else Decimal(0)
            hwm = d(previous.perf_hwm) if previous else Decimal(0)
            accrued = d(previous.perf_accrued) if previous else Decimal(0)
            base_date = previous.perf_base_date if previous else False
            if perf:
                reference, hwm, accrued, base_date = perf["reference"], perf["hwm"], perf["accrued"], perf["base_date"]
                if perf["crystallise"]:
                    current = value if perf["measure"] == "capital" else value / row["units"]
                    reference, hwm, accrued, base_date = current, max(hwm, current), Decimal(0), self.date
            rows.append({
                "valuation_id": self.id,
                "class_id": fund_class.id,
                "pre_capital": float(row["pre_capital"]),
                "ratio": float(row["ratio"]),
                "delta": float(deltas[fund_class]),
                "capital": float(value),
                "units": float(row["units"]),
                "price": str(price),
                "perf_reference": float(reference),
                "perf_hwm": float(hwm),
                "perf_accrued": float(accrued),
                "perf_base_date": base_date,
            })
        self.env["investra.valuation.class"].sudo().create(rows)
        self.write({"fund_capital": float(fund_capital), "neutral_capital": float(neutral)})
        self._run_checks(fund_capital, rounded)

    def _check(self, code, name, ok, detail="", severity="stop"):
        self.env["investra.valuation.check"].sudo().create({
            "valuation_id": self.id,
            "code": code,
            "name": name,
            "status": "ok" if ok else severity,
            "detail": str(detail),
        })

    def _run_checks(self, fund_capital, rounded):
        self._check("classes_sum", "Součet tříd se rovná FK", sum(rounded.values()) == fund_capital, sum(rounded.values()))
        clearing = self._role_balance("internal_clearing")
        self._check("clearing_zero", "Vnitřní zúčtování je za fond nulové", clearing == 0, clearing)
        instrument_ledger = self._role_balance("instrument")
        positions = sum(
            (d(line.fair_value) for line in self.portfolio_line_ids if line.kind != "bank"), Decimal(0)
        )
        self._check("positions_ledger", "Pozice se rovnají hlavní knize", instrument_ledger == engine.money(positions),
                    f"{instrument_ledger} / {positions}")
        transit = self._role_balance("cash_in_transit")
        self._check("transit_zero", "Peníze na cestě jsou nulové", transit == 0, transit, severity="warning")
        pending = self.env["account.move"].sudo().search_count([
            ("company_id", "=", self.company_id.id), ("state", "=", "draft"), ("date", "<=", self.date),
            ("id", "not in", self.event_ids.move_id.ids),
        ])
        self._check("no_foreign_drafts", "K datu nejsou jiné nezaúčtované doklady", not pending, pending, severity="warning")

    # --- postup --------------------------------------------------------------------------------

    def _fingerprint(self):
        """Otisk výsledků a řádků návrhů: zaúčtovat lze jen to, co bylo schváleno."""
        self.ensure_one()
        lines = sorted(
            (l.account_id.code or "", str(l.balance), l.investra_class_id.code or "", l.investra_movement_type or "")
            for l in self.event_ids.filtered(lambda e: e.state in ("draft", "locked", "posted")).move_id.sudo().line_ids
        )
        classes = sorted((c.class_id.code, c.capital, c.units, c.price) for c in self.class_line_ids)
        payload = json.dumps({"date": str(self.date), "version": self.version, "fk": self.fund_capital,
                              "classes": classes, "lines": lines}, ensure_ascii=False)
        return payload, hashlib.sha256(payload.encode()).hexdigest()

    def action_submit(self):
        """Zamkne návrhy a uloží snímek."""
        self._require(PREPARER)
        self._require_state("computed")
        for record in self.sudo():
            stops = record.check_ids.filtered(lambda c: c.status in STOPPING)
            if stops:
                raise UserError(self.env._("Ocenění má nesplněné kontroly: %s", ", ".join(stops.mapped("name"))))
            record.event_ids._lock_events()
            payload, digest = record._fingerprint()
            record.write({"snapshot": payload, "snapshot_hash": digest, "state": "submitted"})
            steps = record.fund_id.approval_step_ids
            names = steps.mapped("name") or (["Kontrola druhou osobou"] if record.fund_id.second_person_required else [])
            if not names:
                raise UserError(self.env._("Fond nemá určené schválení."))
            record.env["investra.valuation.approval"].create([
                {"valuation_id": record.id, "sequence": index, "name": name} for index, name in enumerate(names)
            ])
        return True

    def action_approve(self):
        """Schválí další krok. Stejná osoba nesmí zadávat ani schvalovat dvakrát."""
        self._require(APPROVER)
        self._require_state("submitted")
        user = self.env.user
        for record in self.sudo():
            if record.preparer_id == user:
                raise UserError(self.env._("Zadavatel nemůže schválit vlastní ocenění."))
            if user in record.approval_ids.user_id:
                raise UserError(self.env._("Jeden člověk nemůže schválit dva kroky."))
            step = record.approval_ids.filtered(lambda a: not a.user_id).sorted("sequence")[:1]
            step.write({"user_id": user.id, "approved_at": fields.Datetime.now()})
            if not record.approval_ids.filtered(lambda a: not a.user_id):
                record.state = "approved"
        return True

    def action_return(self, reason):
        """Vrácení před zaúčtováním: návrhy zaniknou bez storen a vznikne nová verze."""
        self._require(APPROVER)
        self._require_state("submitted", "approved")
        if not reason:
            raise UserError(self.env._("Uveďte důvod vrácení."))
        record = self.sudo()
        record.event_ids.filtered(lambda e: e.state in ("draft", "locked"))._discard_events()
        record.write({"state": "returned", "return_reason": reason})
        return record._new_version()

    def _new_version(self):
        self.ensure_one()
        return self.create({"fund_id": self.fund_id.id, "date": self.date, "version": self.version + 1})

    def action_post(self):
        """Zaúčtuje návrhy jedním krokem, jen pokud sedí se schváleným snímkem."""
        self._require(PREPARER)
        self._require_state("approved")
        for record in self.sudo():
            if record._fingerprint()[1] != record.snapshot_hash:
                raise UserError(self.env._("Stav se od schválení změnil, ocenění se musí přepočítat."))
            record.event_ids.filtered(lambda e: e.state == "locked").sorted("id")._post_events()
            record.state = "posted"
        return True

    def action_send_depositary(self):
        self._require(PREPARER)
        self._require_state("posted")
        self.sudo().state = "sent"
        return True

    def action_depositary_confirm(self):
        self._require(APPROVER)
        self._require_state("sent")
        self.sudo().state = "confirmed"
        return True

    def action_depositary_return(self, reason):
        """Vrácení depozitářem: storno všech dokladů ocenění a nová verze."""
        self._require(APPROVER)
        self._require_state("sent")
        if not reason:
            raise UserError(self.env._("Uveďte důvod vrácení."))
        record = self.sudo()
        record.event_ids.filtered(lambda e: e.state == "posted").sorted("id", reverse=True)._reverse_events()
        record.write({"state": "reversed", "return_reason": reason})
        return record._new_version()

    def action_publish(self):
        """Zveřejnění uzamkne ocenění i období; hard lock je nevratný, proto až po depozitáři."""
        self._require(APPROVER)
        self._require_state("confirmed")
        for record in self.sudo():
            record.company_id.hard_lock_date = record.date
            record.write({"state": "published", "published_at": fields.Datetime.now()})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav a výsledky ocenění nastavuje jen postup ocenění."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and SYSTEM_FIELDS & set(vals):
            raise UserError(self.env._("Stav a výsledky ocenění nastavuje jen postup ocenění."))
        guarded = {"fund_id", "date", "version"}
        if guarded & set(vals) and self.filtered(lambda v: v.state != "draft"):
            raise UserError(self.env._("Datum ani fond ocenění po výpočtu nejde změnit."))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda v: v.state not in ("draft", "computed")):
            raise UserError(self.env._("Ocenění po odeslání ke schválení nejde smazat."))
        return super().unlink()


class InvestraValuationClass(models.Model):
    _name = "investra.valuation.class"
    _description = "Výsledek třídy"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict")
    pre_capital = fields.Float(digits=(20, 2), string="Předběžný kapitál")
    ratio = fields.Float(digits=(16, 12), string="Alokační poměr")
    delta = fields.Float(digits=(20, 2), string="Specifická změna")
    capital = fields.Float(digits=(20, 2), string="Kapitál třídy")
    units = fields.Float(digits=(20, 6), string="Kusy")
    price = fields.Char(string="Kurz")
    perf_reference = fields.Float(digits=(20, 8))
    perf_hwm = fields.Float(digits=(20, 8))
    perf_accrued = fields.Float(digits=(20, 2))
    perf_base_date = fields.Date()


class InvestraValuationFee(models.Model):
    _name = "investra.valuation.fee"
    _description = "Rozpis úplaty"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    rule_id = fields.Many2one("investra.fee.rule", required=True, ondelete="restrict")
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict")
    amount = fields.Float(digits=(20, 2))
    detail = fields.Text()


class InvestraValuationExternal(models.Model):
    """Částka spočtená mimo Odoo: příloha s výpočtem a důvod jsou povinné, schvaluje se s oceněním."""

    _name = "investra.valuation.external"
    _description = "Částka spočtená mimo Odoo"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    rule_id = fields.Many2one("investra.fee.rule", required=True, ondelete="restrict", domain=[("kind", "=", "external")])
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict")
    amount = fields.Float(digits=(20, 2), required=True)
    reason = fields.Char(string="Důvod a postup")
    attachment_id = fields.Many2one("ir.attachment", string="Výpočet", ondelete="restrict")


class InvestraValuationPortfolio(models.Model):
    """Řádek listu portfolio: finanční aktivum k datu ocenění."""

    _name = "investra.valuation.portfolio"
    _description = "Řádek portfolia"
    _order = "kind, name"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    kind = fields.Selection(
        [("bank", "Bankovní účet"), ("deposit", "Termínovaný vklad"), ("equity", "Akcie"), ("bond", "Dluhopis"),
         ("fund", "Fond"), ("participation", "Účast"), ("loan", "Úvěr"), ("derivative", "Derivát")],
        required=True,
    )
    instrument_id = fields.Many2one("investra.instrument", ondelete="restrict")
    name = fields.Char(required=True)
    isin = fields.Char(string="ISIN")
    currency_id = fields.Many2one("res.currency", required=True)
    quantity = fields.Float(digits=(20, 6), string="Kusy")
    price = fields.Float(digits=(20, 8), string="Cena")
    price_source = fields.Char(string="Zdroj ceny")
    cost_currency = fields.Float(digits=(20, 2), string="Pořizovací hodnota v měně")
    cost = fields.Float(digits=(20, 2), string="Pořizovací hodnota v měně fondu")
    fair_value_currency = fields.Float(digits=(20, 2), string="Reálná hodnota v měně")
    fx_rate = fields.Float(digits=(16, 8), string="Kurz")
    fx_source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], string="Zdroj kurzu")
    fair_value = fields.Float(digits=(20, 2), string="Reálná hodnota v měně fondu")


class InvestraValuationCheck(models.Model):
    _name = "investra.valuation.check"
    _description = "Kontrola ocenění"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    status = fields.Selection([("ok", "V pořádku"), ("warning", "Upozornění"), ("stop", "Stop")], required=True)
    detail = fields.Char()


class InvestraValuationApproval(models.Model):
    _name = "investra.valuation.approval"
    _description = "Schválení ocenění"
    _order = "valuation_id, sequence"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    sequence = fields.Integer(required=True)
    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", readonly=True)
    approved_at = fields.Datetime(readonly=True)
