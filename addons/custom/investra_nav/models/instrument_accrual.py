from odoo import models
from odoo.exceptions import UserError

from .. import engine


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    def _accrued_value(self, fund, day):
        """Naběhlá hodnota pozice v měně nástroje; každý nákup má vlastní efektivní úrokovou míru.

        Jen výpočet: nic se neúčtuje. Prodej a lineární úročení s více toky zatím nejsou podporované.
        """
        self.ensure_one()
        trades = self.env["investra.trade"].sudo().search([
            ("fund_id", "=", fund.id), ("instrument_id", "=", self.id), ("trade_date", "<=", day),
        ])
        if any(trade.quantity < 0 for trade in trades):
            raise UserError(self.env._("Naběhlá hodnota po prodeji zatím není podporovaná: %s.", self.name))
        method = self._effective_accrual(fund)
        basis = self.day_count or "act365"
        total = engine.ZERO
        for trade in trades:
            quantity = engine.dec(trade.quantity)
            cost = quantity * engine.dec(trade.price)
            flows = [(flow.date, engine.dec(flow.amount) * quantity) for flow in self.cashflow_ids if flow.date > trade.trade_date]
            if not flows:
                raise UserError(self.env._("Nástroj nemá smluvní peněžní toky po pořízení: %s.", self.name))
            if method == "eir":
                total += engine.amortised_cost([(trade.trade_date, -cost), *flows], day, basis=basis)
            elif len(flows) > 1:
                raise UserError(self.env._("Lineární úročení zatím umí jen jednu splátku: %s.", self.name))
            elif day < flows[0][0]:
                total += engine.linear_accrual(cost, flows[0][1], trade.trade_date, flows[0][0], day, basis)
        return engine.money(total)
