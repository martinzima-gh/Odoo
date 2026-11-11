from odoo import api, models


class InvestraInstrumentPrice(models.Model):
    """Kde byla cena použita: upozornění při opravě schválené ceny (rozhodnutí 2026-11-11)."""

    _inherit = "investra.instrument.price"

    def _used_in_valuations(self):
        """Ocenění, jejichž portfolio cenu použilo; u starších řádků bez odkazu podle fondu, nástroje a data."""
        self.ensure_one()
        Line = self.env["investra.valuation.portfolio"].sudo()
        lines = Line.search([("price_id", "=", self.id)])
        if self.fund_id:
            lines |= Line.search([
                ("price_id", "=", False), ("instrument_id", "=", self.instrument_id.id),
                ("valuation_id.fund_id", "=", self.fund_id.id), ("valuation_id.date", "=", self.date),
            ])
        return lines.valuation_id

    @api.onchange("price", "currency_id", "source", "deviation_reason")
    def _onchange_approved_price(self):
        origin = self._origin
        if not origin or origin.state != "approved":
            return None
        message = self.env._("Oprava vrátí cenu do návrhu; znovu ji musí schválit jiný uživatel.")
        valuations = origin._used_in_valuations()
        if valuations:
            message += " " + self.env._(
                "Cena byla použita v oceněních: %s. Hotová ocenění si drží svou cenu; "
                "přepočítat je jde jen vrácením nebo stornem ocenění.",
                ", ".join(valuations.sorted("date").mapped("display_name")),
            )
        return {"warning": {"title": self.env._("Oprava schválené ceny"), "message": message}}
