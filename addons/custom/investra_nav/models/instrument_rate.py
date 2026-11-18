"""Variabilní úroková sazba (úkol IM-11, rozhodnutí 2026-11-15 „Variabilní úroková sazba“).

Nástroj s variabilní sazbou má období sazeb (platí od, sazba). Toky Úrok se počítají po částech podle období; období
po poslední známé sazbě touto sazbou s příznakem Odhad. Nová sazba přepočte jen toky Úrok s datem po „platí od“;
nahrazené toky se archivují (neplatí od dne změny), nemažou. Naběhlá hodnota a vydělaný úrok se pak počítají po úsecích
mezi dny změn (efektivní míra se přepočte prospektivně ke dni změny, varianta a návrhu docs/navrh-variabilni-sazba.md).
Pevná sazba nemá období sazeb ani archivované toky a počítá stejně jako dosud.
"""

from decimal import ROUND_HALF_UP

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import engine
from .instrument_accrual import IRREGULAR, UNIT_AMOUNT


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    rate_type = fields.Selection(
        [("fixed", "Pevná"), ("variable", "Variabilní")], required=True, default="fixed", string="Druh sazby",
        help="Variabilní: sazba se mění tlačítkem Zadat novou sazbu; budoucí toky Úrok se odhadují poslední známou "
             "sazbou. Po prvním obchodu jde jen z pevné na variabilní.",
    )
    rate_period_ids = fields.One2many("investra.instrument.rate.period", "instrument_id", string="Období sazeb")
    superseded_cashflow_ids = fields.One2many(
        "investra.instrument.cashflow", "instrument_id", domain=[("active", "=", False)], context={"active_test": False},
        readonly=True, string="Nahrazené toky",
        help="Toky Úrok nahrazené novou sazbou. Zůstávají kvůli naběhlé hodnotě a úroku za dny před změnou.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        instruments = super().create(vals_list)
        instruments.filtered(lambda i: i.rate_type == "variable")._start_variable_rate()
        return instruments

    def write(self, vals):
        new_type = vals.get("rate_type")
        if not self.env.su:
            if "coupon_rate" in vals and (new_type or "variable") == "variable" and self.filtered(
                lambda i: i.rate_type == "variable" and i.coupon_rate != vals["coupon_rate"]
            ):
                raise UserError(self.env._("U variabilní sazby se sazba mění tlačítkem Zadat novou sazbu."))
            if new_type == "fixed":
                back = self.filtered(lambda i: i.rate_type == "variable")
                if back and self.env["investra.trade"].sudo().search_count([("instrument_id", "in", back.ids)], limit=1):
                    raise UserError(self.env._("Po prvním obchodu nejde variabilní sazbu změnit na pevnou."))
                if len(back.rate_period_ids) > len(back) or back.superseded_cashflow_ids:
                    raise UserError(self.env._(
                        "Nástroj už má změny sazby; na pevnou sazbu ho nejde vrátit. Nejdřív smažte novější období sazeb."))
        before = {i: i.rate_type for i in self} if new_type else {}
        result = super().write(vals)
        for instrument, old in before.items():
            if old == instrument.rate_type:
                continue
            if instrument.rate_type == "variable":
                instrument._start_variable_rate()
            else:
                instrument.rate_period_ids.sudo().unlink()
                instrument.cashflow_ids.filtered("estimated").write({"estimated": False})
            labels = dict(self._fields["rate_type"]._description_selection(self.env))
            instrument._log_cashflow_change(self.env._("Druh sazby: %(old)s → %(new)s", old=labels[old], new=labels[instrument.rate_type]))
        if "start_date" in vals:
            for instrument in self.filtered(lambda i: i.rate_type == "variable" and len(i.rate_period_ids) == 1 and i.start_date):
                instrument.rate_period_ids.sudo().write({"valid_from": instrument.start_date})
        return result

    def _start_variable_rate(self):
        """Přechod na variabilní sazbu: první období = Začátek úročení a dosavadní sazba; budoucí kupóny jsou odhad."""
        for instrument in self:
            if not instrument.start_date:
                raise UserError(self.env._("Variabilní sazba potřebuje Začátek úročení: %s.", instrument.name))
            if not instrument.rate_period_ids:
                self.env["investra.instrument.rate.period"].sudo().create({
                    "instrument_id": instrument.id, "valid_from": instrument.start_date, "rate": instrument.coupon_rate,
                })
            instrument._refresh_estimated()

    # --- období sazeb a výpočet úroku po částech -----------------------------------------------------------

    def _rate_periods(self, extra=None):
        """[(platí od, sazba % p.a.)] vzestupně; extra = (den, sazba) přidá zkoušenou novou sazbu (náhled průvodce)."""
        self.ensure_one()
        periods = [(p.valid_from, engine.dec(p.rate)) for p in self.rate_period_ids]
        if not periods and self.start_date:
            periods = [(self.start_date, engine.dec(self.coupon_rate))]
        if extra:
            periods.append((extra[0], engine.dec(extra[1])))
        return sorted(periods)

    @api.model
    def _rate_on(self, periods, when):
        """Sazba úroku nabíhajícího od dne `when` (období platí od svého dne včetně; před prvním platí první)."""
        valid = [rate for start, rate in periods if start <= when]
        return valid[-1] if valid else periods[0][1]

    def _period_interest(self, start, end, principal, periods):
        """Úrok na jednotku za kupónové období (start, end] po částech podle období sazeb: jistina × Σ sazba × část roku.

        Sazba platná od dne D se uplatní na úrok od D, tj. na část roku (D, konec]; kupón splatný v den D je celý
        podle dosavadní sazby (návrh IM-11, číselný příklad).
        """
        basis = self.day_count or "act365"
        bounds = [start, *sorted({d for d, _r in periods if start < d < end}), end]
        total = sum(
            (self._rate_on(periods, a) / 100 * engine.year_fraction(a, b, basis) for a, b in zip(bounds, bounds[1:])),
            engine.ZERO,
        )
        return (engine.dec(principal) * total).quantize(UNIT_AMOUNT, rounding=ROUND_HALF_UP)

    def _coupon_days(self):
        """Kupónová data: u nepravidelné výplaty data toků Úrok, jinak stejně jako generátor kalendáře."""
        self.ensure_one()
        if self.coupon_frequency == IRREGULAR or not (self.maturity_date and self.start_date):
            return sorted(set(self.cashflow_ids.filtered(lambda f: f.flow_type == "interest").mapped("date")))
        return self._schedule_days()

    def _outstanding_principal(self, after):
        """Jistina na jednotku úročená v období začínajícím dnem `after`: toky Jistina splatné po něm (bez nich Jistina)."""
        principal = self.cashflow_ids.filtered(lambda f: f.flow_type == "principal")
        if not principal:
            return engine.dec(self.principal)
        return sum((engine.dec(f.amount) for f in principal if f.date > after), engine.ZERO)

    def _planned_interest(self, extra=None):
        """{kupónové datum: (úrok na jednotku, odhad)} podle období sazeb; odhad = období začíná po poslední známé sazbě."""
        self.ensure_one()
        periods = self._rate_periods(extra)
        last = periods[-1][0]
        result, start = {}, self.start_date
        for day in self._coupon_days():
            if day <= start:
                continue
            result[day] = (self._period_interest(start, day, self._outstanding_principal(start), periods), start > last)
            start = day
        return result

    def _refresh_estimated(self):
        """Příznak Odhad u aktivních toků Úrok podle posledního období sazby (částky se nemění)."""
        for instrument in self:
            planned = instrument._planned_interest() if instrument.start_date else {}
            for flow in instrument.cashflow_ids.filtered(lambda f: f.flow_type == "interest"):
                estimated = planned.get(flow.date, (None, False))[1]
                if flow.estimated != estimated:
                    flow.write({"estimated": estimated})

    def _rate_changes(self, day, extra=None):
        """Toky Úrok, které nová sazba změní: [(datum, dosavadní tok, nová částka, odhad)], jen data po dni platnosti.
        extra = (den, sazba) u náhledu průvodce, kdy období ještě neexistuje."""
        self.ensure_one()
        changes = []
        for when, (amount, estimated) in sorted(self._planned_interest(extra).items()):
            if when <= day:
                continue
            old = self.cashflow_ids.filtered(lambda f: f.flow_type == "interest" and f.date == when)
            old_amount = sum((engine.dec(f.amount) for f in old), engine.ZERO).quantize(UNIT_AMOUNT)
            if old_amount != amount or any(f.estimated != estimated for f in old):
                changes.append((when, old, amount, estimated))
        return changes

    def _check_rate_change(self, day):
        """Kdy novou sazbu nejde zadat: neplatí po posledním období, je po splatnosti, zamčené ocenění nebo splátka."""
        self.ensure_one()
        if self.rate_type != "variable":
            raise UserError(self.env._("Období sazeb má jen nástroj s variabilní sazbou: %s.", self.name))
        last = max(self.rate_period_ids.mapped("valid_from"), default=None)
        if last and day <= last:
            raise UserError(self.env._(
                "Nová sazba musí platit po posledním období sazby (%(last)s): %(name)s.", last=last, name=self.name))
        if self.maturity_date and day >= self.maturity_date:
            raise UserError(self.env._("Sazba od splatnosti už žádný tok nemění: %s.", self.name))
        trades = self.env["investra.trade"].sudo().search([("instrument_id", "=", self.id), ("state", "!=", "reversed")])
        Valuation = self.env["investra.valuation"]
        for company in trades.fund_id.company_id:
            locking = Valuation._locking(company, day)
            if locking:
                Valuation._raise_locked(locking, day, self.env._("Nová sazba nástroje %s", self.name))
        repayment = self.env["investra.instrument.repayment"].sudo().search(
            [("instrument_id", "=", self.id), ("state", "!=", "reversed"), ("date", ">", day)], order="date", limit=1)
        if repayment:
            raise UserError(self.env._(
                "Nástroj %(name)s má splátku k %(date)s, tedy po dni platnosti nové sazby; nejdřív ji stornujte.",
                name=self.name, date=repayment.date,
            ))

    def _apply_rate_change(self, period):
        """Toky Úrok po dni platnosti: dosavadní se archivují (neplatí od dne změny), vzniknou nové; zápis do historie."""
        self.ensure_one()
        day = period.valid_from
        self.invalidate_recordset(["rate_period_ids"])
        changes = self._rate_changes(day)
        Flow = self.env["investra.instrument.cashflow"]
        texts = []
        for when, old, amount, estimated in changes:
            old_amount = sum((engine.dec(f.amount) for f in old), engine.ZERO).quantize(UNIT_AMOUNT)
            if old_amount == amount:
                old.write({"estimated": estimated})
                continue
            old.write({"active": False, "superseded_on": day})
            if amount:
                Flow.create({"instrument_id": self.id, "date": when, "amount": float(amount), "flow_type": "interest",
                             "estimated": estimated, "introduced_on": day})
            texts.append(f"{when} {float(old_amount):g} → {float(amount):g}")
        self.invalidate_recordset(["cashflow_ids", "superseded_cashflow_ids"])
        self._refresh_estimated()
        self.sudo().write({"coupon_rate": self._rate_periods()[-1][1]})
        self._log_cashflow_change(self.env._(
            "Nová sazba %(rate)s %% p.a. platí od %(day)s%(note)s. Toky Úrok: %(flows)s.",
            rate=f"{period.rate:g}", day=day, note=f" ({period.note})" if period.note else "",
            flows="; ".join(texts) or self.env._("beze změny"),
        ))

    def _revert_rate_change(self, period):
        """Smazání posledního období: nové toky toho dne se smažou, nahrazené se obnoví, sazba se vrátí."""
        self.ensure_one()
        day = period.valid_from
        Flow = self.env["investra.instrument.cashflow"].with_context(active_test=False)
        Flow.search([("instrument_id", "=", self.id), ("introduced_on", "=", day)]).unlink()
        Flow.search([("instrument_id", "=", self.id), ("superseded_on", "=", day)]).write(
            {"active": True, "superseded_on": False})
        return day

    def action_new_rate(self):
        """Tlačítko Zadat novou sazbu: okno s datem platnosti, sazbou a textem „Co se stane“."""
        self.ensure_one()
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        return {
            "type": "ir.actions.act_window", "name": self.env._("Zadat novou sazbu"),
            "res_model": "investra.instrument.rate.wizard", "view_mode": "form", "target": "new",
            "context": {"default_instrument_id": self.id, "default_rate": self.coupon_rate},
        }

    # --- verze kalendáře pro výpočty po úsecích -------------------------------------------------------------

    def _flow_versions(self):
        """(dny změn sazby, všechny toky včetně nahrazených); pevná sazba a nástroj bez změny vrátí ([], None)."""
        self.ensure_one()
        if self.rate_type != "variable":
            return [], None
        flows = self.env["investra.instrument.cashflow"].with_context(active_test=False).search([("instrument_id", "=", self.id)])
        days = set(flows.filtered("introduced_on").mapped("introduced_on")) | set(flows.filtered("superseded_on").mapped("superseded_on"))
        return sorted(days), flows

    @api.model
    def _flows_valid_on(self, flows, when):
        """Kalendář platný ode dne `when`: toky založené nejpozději tento den a do té doby nenahrazené."""
        return flows.filtered(lambda f: (not f.introduced_on or f.introduced_on <= when)
                              and (not f.superseded_on or f.superseded_on > when))


class InvestraInstrumentCashflow(models.Model):
    _inherit = "investra.instrument.cashflow"

    active = fields.Boolean(default=True, string="Platný")
    estimated = fields.Boolean(readonly=True, string="Odhad", help="Úrok období po poslední známé sazbě (variabilní sazba).")
    superseded_on = fields.Date(readonly=True, string="Nahrazen od", help="Den platnosti nové sazby, která tok nahradila.")
    # Odchylka od návrhu IM-11 (datový model): vedle „nahrazen od“ i „platí od“ nového toku, aby šel složit kalendář
    # platný v každém úseku i po více změnách sazby (tok vzniklý změnou c1 a nahrazený změnou c2 nepatří do úseku před c1).
    introduced_on = fields.Date(readonly=True, string="Platí od změny", help="Den platnosti sazby, která tok založila.")


class InvestraInstrumentRatePeriod(models.Model):
    """Období úrokové sazby nástroje s variabilní sazbou. První období založí přechod na variabilní sazbu, další
    průvodce Zadat novou sazbu; založení dalšího období přepočte budoucí toky Úrok."""

    _name = "investra.instrument.rate.period"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Období úrokové sazby nástroje"
    _order = "instrument_id, valid_from"

    # ZJ-10 fáze 2: mixin sleduje jen poznámku. Vznik a smazání sazby už popisují ruční zprávy nástroje
    # (_apply_rate_change, unlink), proto se create a unlink dělají s tracking_disable (bez duplicity).
    _line_tracking_parent = "instrument_id"
    _line_tracking_fields = ("note",)

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="cascade", index=True, string="Nástroj")
    company_id = fields.Many2one(related="instrument_id.company_id", store=True, index=True)
    valid_from = fields.Date(required=True, string="Platí od")
    rate = fields.Float(digits=(16, 6), string="Sazba % p.a.")
    note = fields.Char(tracking=True, string="Poznámka", help="Např. referenční sazba a marže; jen informativně, výpočet bere Sazbu.")

    _instrument_day_uniq = models.UniqueIndex("(instrument_id, valid_from)", "Nástroj už má období sazby s tímto dnem.")

    @api.model_create_multi
    def create(self, vals_list):
        periods = self.browse()
        for vals in vals_list:
            instrument = self.env["investra.instrument"].browse(vals.get("instrument_id"))
            first = not instrument.rate_period_ids
            if not first:
                instrument._check_rate_change(fields.Date.to_date(vals.get("valid_from")))
            elif not self.env.su:
                raise UserError(self.env._("První období sazby založí přechod nástroje na variabilní sazbu."))
            period = super(InvestraInstrumentRatePeriod, self.with_context(tracking_disable=True)).create([vals])
            if not first:
                instrument._apply_rate_change(period)
            periods |= period
        return periods

    def write(self, vals):
        if not self.env.su and set(vals) - {"note"}:
            raise UserError(self.env._("U období sazby jde měnit jen poznámka; chybnou sazbu smažte a zadejte znovu."))
        return super().write(vals)

    def unlink(self):
        quiet = self.with_context(tracking_disable=True)
        if self.env.su:
            return super(InvestraInstrumentRatePeriod, quiet).unlink()
        for period in self.sorted("valid_from", reverse=True):
            instrument = period.instrument_id
            if period != instrument.rate_period_ids[-1:] or len(instrument.rate_period_ids) == 1:
                raise UserError(self.env._(
                    "Smazat jde jen poslední období sazby a ne první (to patří k variabilní sazbě): %s.", instrument.name))
            day, rate = period.valid_from, period.rate
            period._check_revert()
            instrument._revert_rate_change(period)
            super(InvestraInstrumentRatePeriod, period.with_context(tracking_disable=True)).unlink()
            instrument.invalidate_recordset(["rate_period_ids", "cashflow_ids", "superseded_cashflow_ids"])
            instrument._refresh_estimated()
            instrument.sudo().write({"coupon_rate": instrument._rate_periods()[-1][1]})
            instrument._log_cashflow_change(self.env._(
                "Smazána sazba %(rate)s %% p.a. platná od %(day)s; toky Úrok vráceny na předchozí sazbu.",
                rate=f"{rate:g}", day=day,
            ))
        return True

    def _line_tracking_desc(self):
        return self.env._("Období sazby od %s", self.valid_from or "–")

    def _check_revert(self):
        """Smazání sazby mění toky po jejím dni platnosti: zamčené ocenění ani splátka po tomto dni ho nepovolí."""
        self.ensure_one()
        instrument, day = self.instrument_id, self.valid_from
        trades = self.env["investra.trade"].sudo().search([("instrument_id", "=", instrument.id), ("state", "!=", "reversed")])
        Valuation = self.env["investra.valuation"]
        for company in trades.fund_id.company_id:
            locking = Valuation._locking(company, day)
            if locking:
                Valuation._raise_locked(locking, day, self.env._("Smazání sazby nástroje %s", instrument.name))
        if self.env["investra.instrument.repayment"].sudo().search_count(
            [("instrument_id", "=", instrument.id), ("state", "!=", "reversed"), ("date", ">", day)], limit=1
        ):
            raise UserError(self.env._("Po dni platnosti sazby je splátka; nejdřív ji stornujte: %s.", instrument.name))


class InvestraInstrumentRateWizard(models.TransientModel):
    """Okno Zadat novou sazbu: založí období sazby; to přepočte budoucí toky Úrok. Nic se neúčtuje."""

    _name = "investra.instrument.rate.wizard"
    _description = "Nová úroková sazba nástroje"

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="cascade", string="Nástroj")
    valid_from = fields.Date(required=True, default=fields.Date.context_today, string="Platí od")
    rate = fields.Float(digits=(16, 6), string="Sazba % p.a.")
    note = fields.Char(string="Poznámka", help="Např. referenční sazba a marže; jen informativně.")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    period_warning = fields.Char(compute="_compute_effect", string="Upozornění")

    @api.depends("instrument_id", "valid_from", "rate")
    def _compute_effect(self):
        for wizard in self:
            instrument = wizard.instrument_id._origin
            wizard.period_warning = False
            if not (instrument and wizard.valid_from):
                wizard.effect = False
                continue
            day = wizard.valid_from
            lines = [self.env._(
                "Založí se období sazby %(rate)s %% p.a. od %(day)s. Toky Úrok s datem po %(day)s se přepočítají; dosavadní "
                "se archivují (záložka Nahrazené toky), toky do %(day)s a jistina se nemění. Efektivní úroková míra se ke dni "
                "%(day)s přepočte z naběhlé hodnoty k tomuto dni, bez výsledkového rozdílu; naběhlá hodnota a úrok za dny "
                "před %(day)s se nemění. Schválená ocenění a zaúčtované doklady se nemění, nová sazba se projeví od "
                "nejbližšího ocenění. Nic se neúčtuje.", rate=f"{wizard.rate:g}", day=day,
            )]
            if instrument.rate_type == "variable" and instrument.start_date:
                changes = [(when, old, amount) for when, old, amount, _e in instrument._rate_changes(day, (day, wizard.rate))
                           if sum(old.mapped("amount")) != float(amount)]
                lines += [f"{when}: {sum(old.mapped('amount')):g} → {float(amount):g}" for when, old, amount in changes] or [
                    self.env._("Žádný tok Úrok se nezmění.")]
                starts = [instrument.start_date, *instrument._coupon_days()]
                if day not in starts:
                    wizard.period_warning = self.env._(
                        "„Platí od“ %s není začátkem kupónového období: kupón běžného období se spočítá po částech "
                        "(dny do změny dosavadní sazbou, od změny novou).", day)
            wizard.effect = "\n".join(lines)

    def action_confirm(self):
        self.ensure_one()
        self.instrument_id.action_new_rate()  # kontrola oprávnění
        self.env["investra.instrument.rate.period"].create({
            "instrument_id": self.instrument_id.id, "valid_from": self.valid_from, "rate": self.rate, "note": self.note,
        })
        return {"type": "ir.actions.act_window_close"}
