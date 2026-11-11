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
            if self.env["investra.instrument.repayment"].sudo().search_count([("instrument_id", "=", instrument.id)], limit=1):
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
    """Skutečná splátka nástroje v naběhlé hodnotě; rozdíl proti naběhlé hodnotě doúčtuje ocenění."""

    _name = "investra.instrument.repayment"
    _inherit = ["investra.record.guard"]
    _description = "Splátka nástroje"
    _order = "date desc, id desc"
    _book_fields = ("fund_id",)

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", string="Nástroj")
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", string="Obchodní model", domain="[('fund_id', '=', fund_id)]",
    )
    date = fields.Date(required=True, string="Datum")
    amount = fields.Float(required=True, digits=(20, 2), string="Částka v měně nástroje")
    fx_rate = fields.Float(required=True, default=1, digits=(16, 6), string="Kurz")
    event_id = fields.Many2one("investra.accounting.event", readonly=True, string="Účetní událost")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("portfolio_id") and vals.get("fund_id"):
                vals["portfolio_id"] = self.env["investra.fund"].browse(vals["fund_id"])._default_portfolio().id
        return super().create(vals_list)

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

    def action_book(self):
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        self.check_access("write")
        self.sudo()._book()
        return True

    def _book(self):
        for repayment in self.filtered(lambda r: not r.event_id):
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
            repayment.sudo().event_id = event
