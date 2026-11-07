from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class InvestraInstrument(models.Model):
    _name = "investra.instrument"
    _description = "Nástroj"
    _order = "name"

    name = fields.Char(required=True)
    isin = fields.Char(string="ISIN")
    currency_id = fields.Many2one("res.currency", required=True)
    instrument_type = fields.Selection(
        [("equity", "Akcie"), ("bond", "Dluhopis"), ("fund", "Fond"), ("participation", "Účast"), ("loan", "Úvěr"), ("derivative", "Derivát")],
        required=True,
    )
    ifrs9_category = fields.Selection(
        [("fvtpl", "Reálná hodnota do výsledku"), ("fvoci", "Reálná hodnota do OCI"), ("amortised", "Naběhlá hodnota")],
        required=True,
        default="fvtpl",
        string="Kategorie IFRS 9",
    )
    fair_value_level = fields.Selection([("1", "Úroveň 1"), ("2", "Úroveň 2"), ("3", "Úroveň 3")], string="Úroveň RH")


class InvestraInstrumentPrice(models.Model):
    """Cena k datu. Do ocenění vstupuje jen schválená; schválenou nelze měnit."""

    _name = "investra.instrument.price"
    _description = "Cena nástroje"
    _order = "date desc"

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", index=True)
    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    date = fields.Date(required=True)
    price = fields.Float(required=True, digits=(20, 8))
    source = fields.Char(required=True, string="Zdroj")
    state = fields.Selection([("draft", "Návrh"), ("approved", "Schváleno")], default="draft", required=True, readonly=True)
    entered_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    approved_by = fields.Many2one("res.users", readonly=True)

    _uniq = models.Constraint("unique(fund_id, instrument_id, date)", "Cena nástroje k datu už existuje.")

    def write(self, vals):
        if self.filtered(lambda p: p.state == "approved") and set(vals) - {"state", "approved_by"}:
            raise UserError(self.env._("Schválenou cenu nejde měnit."))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda p: p.state == "approved"):
            raise UserError(self.env._("Schválenou cenu nejde smazat."))
        return super().unlink()

    def action_approve(self):
        if not self.env.user.has_group("investra_entity.group_valuation_approver"):
            raise UserError(self.env._("Ceny schvaluje jen uživatel se skupinou schvalování ocenění."))
        for price in self:
            if price.entered_by == self.env.user:
                raise UserError(self.env._("Zadavatel nemůže schválit vlastní cenu."))
        self.sudo().write({"state": "approved", "approved_by": self.env.user.id})


class InvestraTrade(models.Model):
    """Portfoliová transakce; účetní doklad vzniká přes událost a nese nástroj na řádku."""

    _name = "investra.trade"
    _description = "Obchod s nástrojem"
    _order = "trade_date, id"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict")
    trade_date = fields.Date(required=True)
    settlement_date = fields.Date()
    quantity = fields.Float(required=True, digits=(20, 6), help="Kladně nákup, záporně prodej.")
    price = fields.Float(required=True, digits=(20, 8))
    fx_rate = fields.Float(default=1, digits=(16, 6), required=True, help="Funkční měna za jednotku měny nástroje.")
    event_id = fields.Many2one("investra.accounting.event", readonly=True)

    @api.constrains("quantity")
    def _check_quantity(self):
        for trade in self:
            if not trade.quantity:
                raise ValidationError(self.env._("Obchod musí mít množství."))

    def _book(self):
        """Zaúčtuje nákup proti bance; v prototypu bez poplatků a bez sjednaného nevypořádaného stavu."""
        for trade in self:
            amount = trade.quantity * trade.price * trade.fx_rate
            foreign = trade.quantity * trade.price
            company = trade.company_id
            extra = {"investra_instrument_id": trade.instrument_id.id}
            currency = {}
            if trade.instrument_id.currency_id != company.currency_id:
                currency = {"currency_id": trade.instrument_id.currency_id.id, "amount_currency": foreign}
            event = self.env["investra.accounting.event"]._create_event(
                company, f"trade:{trade.id}", f"Obchod {trade.instrument_id.name}", trade.trade_date, "trade",
                [
                    {"role": "instrument", "amount": amount, "movement_type": "transaction", "extra": extra, **currency},
                    {"role": "bank", "amount": -amount, "movement_type": "transaction",
                     **({"currency_id": currency["currency_id"], "amount_currency": -foreign} if currency else {})},
                ],
            )
            event._lock_events()
            event._post_events()
            trade.sudo().event_id = event

    @api.model
    def _positions(self, fund, day):
        """Kusy a účetní hodnota po nástrojích k datu, z obchodů a z hlavní knihy."""
        trades = self.search([("fund_id", "=", fund.id), ("trade_date", "<=", day)])
        quantities = {}
        for trade in trades:
            quantities[trade.instrument_id] = quantities.get(trade.instrument_id, 0.0) + trade.quantity
        return {instrument: qty for instrument, qty in quantities.items() if qty}


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    investra_instrument_id = fields.Many2one("investra.instrument", string="Nástroj", ondelete="restrict", index="btree_not_null")

    def _get_integrity_hash_fields(self):
        base = super()._get_integrity_hash_fields()
        return base + ["investra_instrument_id"] if "investra_class_id" in base else base

    def write(self, vals):
        if "investra_instrument_id" in vals and self.filtered(lambda l: l.parent_state == "posted"):
            raise UserError(self.env._("Nástroj nejde po zaúčtování změnit."))
        return super().write(vals)
