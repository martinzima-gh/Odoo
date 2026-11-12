from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import engine


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    principal = fields.Float(digits=(20, 2), string="Jistina na jednotku")
    start_date = fields.Date(string="Začátek úročení")

    def action_generate_schedule(self):
        """Vklad s jednou splátkou: jistina a úrok k splatnosti podle sazby a konvence dnů."""
        for instrument in self:
            if not (instrument.principal and instrument.start_date and instrument.maturity_date):
                raise UserError(self.env._("Vyplňte jistinu, začátek a splatnost: %s.", instrument.name))
            # Stornovaná splátka kalendář neblokuje (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
            if self.env["investra.instrument.repayment"].sudo().search_count(
                [("instrument_id", "=", instrument.id), ("state", "!=", "reversed")], limit=1
            ):
                raise UserError(self.env._("Kalendář po splacení nejde měnit: %s.", instrument.name))
            fraction = engine.year_fraction(instrument.start_date, instrument.maturity_date, instrument.day_count or "act365")
            principal = engine.dec(instrument.principal)
            interest = engine.money(principal * engine.dec(instrument.coupon_rate) / 100 * fraction)
            instrument.cashflow_ids = [(5,), (0, 0, {
                "date": instrument.maturity_date, "amount": float(principal), "flow_type": "principal",
            }), (0, 0, {"date": instrument.maturity_date, "amount": float(interest), "flow_type": "interest"})]
        return True

    def _accrued_value(self, fund, day, portfolio=None):
        """Naběhlá hodnota pozice v měně nástroje; každý nákup má vlastní efektivní úrokovou míru.

        Jen výpočet: nic se neúčtuje. Prodej a lineární úročení s více toky zatím nejsou podporované.
        Pozice je v jednom obchodním modelu fondu; bez něj se sečtou všechny modely.
        """
        self.ensure_one()
        domain = [("fund_id", "=", fund.id), ("instrument_id", "=", self.id), ("trade_date", "<=", day)]
        if portfolio:
            domain.append(("portfolio_id", "=", portfolio.id))
        trades = self.env["investra.trade"].sudo().search(domain)
        if any(trade.quantity < 0 for trade in trades):
            raise UserError(self.env._("Naběhlá hodnota po prodeji zatím není podporovaná: %s.", self.name))
        method = self._effective_accrual(fund)
        basis = self.day_count or "act365"
        total = engine.ZERO
        for trade in trades:
            quantity = engine.dec(trade.quantity)
            cost = quantity * engine.dec(trade.price)
            totals = {}
            for flow in self.cashflow_ids.filtered(lambda f: f.date > trade.trade_date):
                totals[flow.date] = totals.get(flow.date, engine.ZERO) + engine.dec(flow.amount) * quantity
            flows = sorted(totals.items())
            if not flows:
                raise UserError(self.env._("Nástroj nemá smluvní peněžní toky po pořízení: %s.", self.name))
            if method == "eir":
                total += engine.amortised_cost([(trade.trade_date, -cost), *flows], day, basis=basis)
            elif len(flows) > 1:
                raise UserError(self.env._("Lineární úročení zatím umí jen jednu splátku: %s.", self.name))
            elif day < flows[0][0]:
                total += engine.linear_accrual(cost, flows[0][1], trade.trade_date, flows[0][0], day, basis)
        return engine.money(total)


class InvestraInstrumentRepayment(models.Model):
    """Skutečná splátka nástroje v naběhlé hodnotě; rozdíl proti naběhlé hodnotě doúčtuje ocenění.

    Zaúčtovaná splátka je zamčená; chybu opraví storno nebo oprava (storno a nová splátka v návrhu), stejně jako
    u úpisu a odkupu (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
    """

    _name = "investra.instrument.repayment"
    _inherit = ["investra.record.guard"]
    _description = "Splátka nástroje"
    _order = "date desc, id desc"
    _book_fields = ("fund_id",)
    _system_fields = frozenset({"event_id", "state", "reversal_reason"})

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", string="Nástroj")
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", string="Obchodní model", domain="[('fund_id', '=', fund_id)]",
    )
    date = fields.Date(required=True, string="Datum")
    amount = fields.Float(required=True, digits=(20, 2), string="Částka v měně nástroje")
    fx_rate = fields.Float(required=True, default=1, digits=(16, 6), string="Kurz")
    state = fields.Selection(
        [("draft", "Návrh"), ("posted", "Zaúčtováno"), ("reversed", "Stornováno")],
        required=True, default="draft", readonly=True, index=True, string="Stav",
    )
    event_id = fields.Many2one("investra.accounting.event", readonly=True, string="Účetní událost")
    reversal_reason = fields.Text(readonly=True, string="Důvod storna")
    replaced_id = fields.Many2one("investra.instrument.repayment", readonly=True, ondelete="restrict", string="Opravuje splátku")

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(set(vals) & self._system_fields for vals in vals_list):
            raise UserError(self.env._("Stav, účetní událost a důvod storna nastavuje jen zaúčtování a storno."))
        for vals in vals_list:
            if not vals.get("portfolio_id") and vals.get("fund_id"):
                vals["portfolio_id"] = self.env["investra.fund"].browse(vals["fund_id"])._default_portfolio().id
        records = super().create(vals_list)
        for repayment in records:
            repayment._check_valuation_lock(self.env._("Zadání splátky"))
        return records

    def write(self, vals):
        if not self.env.su and (set(vals) & self._system_fields or self.filtered(lambda r: r.state != "draft")):
            raise UserError(self.env._("Zaúčtovanou splátku nejde změnit; opravte ji stornem nebo opravou."))
        # Stav a událost zapisuje zaúčtování a storno; to hlídá zámek dokladu a _do_reverse.
        if set(vals) - self._system_fields:
            for repayment in self:
                repayment._check_valuation_lock(self.env._("Změna splátky"))
        result = super().write(vals)
        if "date" in vals:
            for repayment in self:
                repayment._check_valuation_lock(self.env._("Změna splátky"))
        return result

    def unlink(self):
        if self.filtered(lambda r: r.state != "draft" or r.event_id):
            raise UserError(self.env._("Zaúčtovanou splátku nejde smazat; opravte ji stornem."))
        for repayment in self:
            repayment._check_valuation_lock(self.env._("Smazání splátky"))
        return super().unlink()

    def copy_data(self, default=None):
        # Stav, událost a důvod storna nastavuje jen zaúčtování a storno; kopie začíná v návrhu.
        vals_list = super().copy_data(default)
        for vals in vals_list:
            for name in self._system_fields:
                vals.pop(name, None)
        return vals_list

    def _check_valuation_lock(self, what):
        """Zámek ocenění jako u úpisu a odkupu: datum splátky v ocenění Ke schválení až Potvrzeno."""
        self.ensure_one()
        Valuation = self.env["investra.valuation"]
        locking = Valuation._locking(self.company_id, self.date)
        if locking:
            Valuation._raise_locked(locking, self.date, what)

    def _classification(self):
        self.ensure_one()
        return self.env["investra.portfolio.classification"]._valid(self.portfolio_id, self.instrument_id, self.date)

    @api.constrains("amount", "instrument_id", "portfolio_id", "fund_id")
    def _check_repayment(self):
        for repayment in self:
            if repayment.amount <= 0:
                raise ValidationError(self.env._("Splátka musí být kladná."))
            if repayment.portfolio_id.fund_id != repayment.fund_id:
                raise ValidationError(self.env._("Obchodní model nepatří fondu splátky."))
            if repayment._classification().valuation_method != "amortised":
                raise ValidationError(self.env._("Splátka je jen u nástroje v naběhlé hodnotě."))

    def _require_preparer(self):
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        self.check_access("write")

    def action_book(self):
        self._require_preparer()
        self.sudo()._book()
        return True

    def _book(self):
        for repayment in self.filtered(lambda r: r.state == "draft" and not r.event_id):
            instrument = repayment.instrument_id
            company = repayment.company_id
            amount = repayment.amount * repayment.fx_rate
            foreign = instrument.currency_id != company.currency_id
            debit = {"currency_id": instrument.currency_id.id, "amount_currency": repayment.amount} if foreign else {}
            credit = {"currency_id": instrument.currency_id.id, "amount_currency": -repayment.amount} if foreign else {}
            event = self.env["investra.accounting.event"]._create_event(
                company, f"repayment:{repayment.id}", f"Splátka {instrument.name}", repayment.date, "repayment",
                [
                    {"role": "bank", "amount": amount, "movement_type": "transaction", **debit},
                    {"role": repayment._classification().role_id.code, "amount": -amount, "movement_type": "transaction",
                     "extra": {"investra_instrument_id": instrument.id, "investra_classification_id": repayment._classification().id},
                     **credit},
                ],
                source=repayment,
            )
            event._lock_events()
            event._post_events()
            repayment.sudo().write({"event_id": event.id, "state": "posted"})

    # --- storno a oprava -----------------------------------------------------------------------

    def _check_reversible(self, reason, what):
        self.ensure_one()
        self._require_preparer()
        if self.state != "posted":
            raise UserError(self.env._("%s lze jen zaúčtovanou splátku.", what))
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod."))

    def action_reverse(self, reason):
        """Storno zaúčtované splátky k jejímu datu; pozice nástroje se tím znovu otevře."""
        self._check_reversible(reason, self.env._("Stornovat"))
        request = self.env["investra.approval.matrix"]._gate(
            "repayment_reverse", self, "action_reverse", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno splátky: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self

    def action_correct(self, reason):
        """Oprava = storno a nová splátka v návrhu s odkazem na opravovanou."""
        self._check_reversible(reason, self.env._("Opravit"))
        request = self.env["investra.approval.matrix"]._gate(
            "repayment_reverse", self, "action_correct", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Oprava splátky: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self.copy({"replaced_id": self.id})

    def _do_reverse(self, reason):
        repayment = self.sudo()
        repayment._check_valuation_lock(self.env._("Storno splátky"))
        repayment.event_id._reverse_events()
        repayment.write({"state": "reversed", "reversal_reason": reason})


class InvestraInstrumentRepaymentReverseWizard(models.TransientModel):
    """Okno pro důvod storna nebo opravy splátky; volá splátku, samo nic neúčtuje."""

    _name = "investra.instrument.repayment.reverse.wizard"
    _description = "Storno nebo oprava splátky"

    repayment_id = fields.Many2one("investra.instrument.repayment", required=True, ondelete="cascade", string="Splátka")
    mode = fields.Selection([("reverse", "Stornovat"), ("correct", "Opravit (storno a nová splátka)")], required=True, default="correct", string="Krok")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    reason = fields.Text(required=True, string="Důvod")

    @api.depends("mode")
    def _compute_effect(self):
        for wizard in self:
            wizard.effect = self.env._(
                "Doklad splátky se stornuje k datu splátky a splátka dostane stav Stornováno; "
                "pozice nástroje se znovu otevře a další ocenění dopočítá naběhlou hodnotu."
            ) + ("" if wizard.mode == "reverse" else self.env._(
                " Vznikne nová splátka v návrhu s odkazem na opravovanou; po úpravě ji zaúčtujte."
            ))

    def action_confirm(self):
        self.ensure_one()
        method = self.repayment_id.action_reverse if self.mode == "reverse" else self.repayment_id.action_correct
        result = method(self.reason)
        if result._name == "investra.approval.request":
            return result._action_open()
        return {"type": "ir.actions.act_window", "res_model": result._name, "res_id": result.id,
                "view_mode": "form", "target": "current"}
