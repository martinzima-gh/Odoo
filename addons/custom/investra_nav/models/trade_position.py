"""Průměrná pořizovací cena pozice a cena vyskladnění na prodeji (ZJ-15, dávka ZJ-07 až ZJ-19, oddíl 6).

Společná průměrka: `_position_events` (dříve v ocenění) a `_average_cost` – ocenění, náhled obchodu i kontroly prodeje
čtou tu samou funkci. Prodej nese cenu vyskladnění za kus (výchozí průměrná cena pozice nástroj + portfolio); ruční
změna mění jen rozdělení výsledku na realizovaný a přecenění, ne celkový výsledek (výpočet je v `valuation._cost_walk`
a `_realised_ccy`).
"""
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Odchylka ceny vyskladnění od průměrné, která se ještě bere jako „beze změny“ (osm desetinných míst pole).
DERECOGNITION_TOLERANCE = Decimal("0.00000001")


def d(value):
    return Decimal(str(value or 0))


class InvestraTradePosition(models.Model):
    _inherit = "investra.trade"

    average_cost_price = fields.Float(
        digits=(20, 8), compute="_compute_average_cost", string="Průměrná cena k datu sjednání",
        help="Průměrná pořizovací cena za kus pozice (nástroj a portfolio) k datu sjednání v měně nástroje; jen u prodeje.",
    )
    # Odchylka od plánu (ZJ-15 B2): `tracking=True` vynecháno – obchod nemá chatter (není mail.thread) a po zaúčtování se
    # nemění; cena i důvod zůstávají na záznamu a v dokladu ocenění.
    derecognition_price = fields.Float(
        digits=(20, 8), string="Cena vyskladnění za kus",
        help="Pořizovací cena prodaných kusů za kus; výchozí je průměrná cena pozice (nástroj a portfolio). Mění jen "
             "rozdělení výsledku na realizovaný a přecenění, ne celkový výsledek. Prázdné nebo nula = průměrná cena.",
    )
    derecognition_manual = fields.Boolean(
        compute="_compute_derecognition_manual", store=True, string="Upraveno ručně",
        help="Cena vyskladnění se liší od průměrné ceny. Uloženo, aby ocenění nepočítalo průměrku znovu při čtení.",
    )
    derecognition_reason = fields.Text(string="Důvod úpravy ceny vyskladnění")

    # --- společná průměrka -----------------------------------------------------------------------------------------

    @api.model
    def _position_events(self, fund, instrument, portfolio, start, end):
        """Obchody a zaúčtované splátky jistiny pozice v období (start, end] po datech:
        [(datum, kusy se znaménkem, částka bez úroku v měně nástroje, kurz zaúčtování, uzavírá pozici, cena prodaných
        kusů zadaná ručně v měně nástroje nebo None)].

        Přesun 1:1 z `valuation._position_events` (ZJ-15 B1); nový je 6. prvek `cost` u prodeje s ruční cenou
        vyskladnění."""
        Trade = self.env["investra.trade"].sudo()
        trades = Trade._recognised(fund, end, instrument, portfolio)
        if start:
            trades -= Trade._recognised(fund, start, instrument, portfolio)
        # Náhled obchodu (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“): uložená verze obchodu se nahradí
        # hodnotami z formuláře, nebo se vynechá; běžné ocenění kontext nemá.
        preview = self.env.context.get("investra_trade_preview")
        if preview:
            trades = trades.filtered(lambda t: t.id != preview["exclude_id"])

        def event(trade):
            # ZJ-16 E4: poplatek nákupu v naběhlé hodnotě a FVOCI je součástí pořizovací ceny (v měně nástroje).
            manual = (-d(trade.quantity) * d(trade.derecognition_price)) if trade.quantity < 0 and trade.derecognition_manual else None
            return (trade._recognition_date(), d(trade.quantity),
                    d(trade.quantity) * d(trade.price) + d(trade._capitalised_fee_ccy()), d(trade._booked_fx()), False, manual)

        events = [event(t) for t in trades]
        added = preview and preview.get("trade")
        if added and (not start or added._recognition_date() > start) and added._recognition_date() <= end:
            events.append(event(added))
        domain = [("fund_id", "=", fund.id), ("instrument_id", "=", instrument.id), ("portfolio_id", "=", portfolio.id),
                  ("state", "=", "posted"), ("date", "<=", end)]
        if start:
            domain.append(("date", ">", start))
        ppu = d(instrument._principal_per_unit())
        for repayment in self.env["investra.instrument.repayment"].sudo().search(domain):
            principal = d(repayment.principal_amount)
            events.append((repayment.date, -principal / ppu, -principal, d(repayment.fx_rate), repayment.closes_position, None))
        # Nákupy téhož dne před prodeji a splátkami.
        return sorted(events, key=lambda e: (e[0], e[1] < 0))

    @api.model
    def _average_cost(self, fund, instrument, portfolio, day, exclude=None):
        """Kusy a pořizovací cena pozice průměrem po nástroji a portfoliu k datu (v měně nástroje), bez obchodu `exclude`.

        Stejná smyčka jako `valuation._cost_walk` (prodej s ruční cenou odebere zadanou pořizovací cenu); vrací
        (kusy, pořizovací cena)."""
        context = {"investra_trade_preview": {"exclude_id": exclude.id, "trade": None}} if exclude and exclude.id else {}
        units = cost = Decimal(0)
        for _day, quantity, amount, _fx, closes, manual in self.with_context(**context)._position_events(
                fund, instrument, portfolio, None, day):
            if quantity > 0:
                units, cost = units + quantity, cost + amount
            elif units > 0:
                share_units = Decimal(1) if closes else min(-quantity / units, Decimal(1))
                share_cost = min(manual / cost, Decimal(1)) if manual is not None and cost else share_units
                units, cost = units * (1 - share_units), cost * (1 - share_cost)
        return units, cost

    # --- pole prodeje ----------------------------------------------------------------------------------------------

    def _average_cost_key(self):
        """(fond, nástroj, portfolio, datum) prodeje nebo None, když ještě není vše vyplněno (i ve formuláři)."""
        self.ensure_one()
        if self.side != "sell" or not (self.fund_id and self.instrument_id and self.portfolio_id and self.trade_date):
            return None
        return self.fund_id._origin, self.instrument_id._origin, self.portfolio_id._origin, self.trade_date

    @api.depends("fund_id", "instrument_id", "portfolio_id", "trade_date", "side")
    def _compute_average_cost(self):
        for trade in self:
            key = trade._average_cost_key()
            if not key:
                trade.average_cost_price = 0.0
                continue
            units, cost = self._average_cost(*key, exclude=trade._origin)
            trade.average_cost_price = float(cost / units) if units else 0.0

    @api.depends("derecognition_price", "average_cost_price", "side")
    def _compute_derecognition_manual(self):
        for trade in self:
            trade.derecognition_manual = bool(
                trade.side == "sell" and trade.derecognition_price
                and abs(d(trade.derecognition_price) - d(trade.average_cost_price)) > DERECOGNITION_TOLERANCE)

    @api.onchange("side", "instrument_id", "portfolio_id", "trade_date")
    def _onchange_derecognition_price(self):
        """Prodej v návrhu: cena vyskladnění se předvyplní průměrnou cenou (jen návrh, jde přepsat)."""
        for trade in self:
            if trade.side == "sell" and not trade.event_id:
                trade.derecognition_price = trade.average_cost_price
            elif trade.side != "sell":
                trade.derecognition_price = 0.0
                trade.derecognition_reason = False

    # --- kontroly a zaúčtování -------------------------------------------------------------------------------------

    @api.constrains("derecognition_price", "derecognition_reason", "side")
    def _check_derecognition_fields(self):
        for trade in self:
            if trade.derecognition_price < 0:
                raise ValidationError(self.env._("Cena vyskladnění nesmí být záporná."))
            if trade.derecognition_manual and not (trade.derecognition_reason or "").strip():
                raise ValidationError(self.env._(
                    "Cena vyskladnění %(price)s se liší od průměrné ceny %(average)s: doplňte důvod úpravy.",
                    price=trade.derecognition_price, average=round(trade.average_cost_price, 8)))

    def _prepare_derecognition(self):
        """Před zaúčtováním prodeje: znovu spočte průměrku k datu sjednání, uloží cenu a příznak ruční úpravy a hlídá
        pozici. Cena bez ruční úpravy = dnešní chování (ocenění bere průměrný podíl)."""
        self.ensure_one()
        units, cost = self._average_cost(self.fund_id, self.instrument_id, self.portfolio_id, self.trade_date, exclude=self)
        average = float(cost / units) if units else 0.0
        price = self.derecognition_price or average
        manual = bool(self.derecognition_price) and abs(d(price) - d(average)) > DERECOGNITION_TOLERANCE
        if manual:
            if not (self.derecognition_reason or "").strip():
                raise UserError(self.env._(
                    "Cena vyskladnění %(price)s se liší od průměrné ceny %(average)s: doplňte důvod úpravy.",
                    price=price, average=round(average, 8)))
            sold_cost = -d(self.quantity) * d(price)
            if sold_cost > cost + Decimal("0.005"):
                raise UserError(self.env._(
                    "Cena vyskladnění %(price)s × %(units)s kusů = %(sold)s je víc než pořizovací cena celé pozice %(cost)s "
                    "(%(name)s, %(portfolio)s).", price=price, units=-self.quantity, sold=round(sold_cost, 2),
                    cost=round(cost, 2), name=self.instrument_id.name, portfolio=self.portfolio_id.name))
            if -d(self.quantity) >= units - Decimal("0.000001"):
                raise UserError(self.env._(
                    "Prodej celé pozice (%s) nejde s upravenou cenou vyskladnění: celá pořizovací cena pozice odchází. "
                    "Použijte průměrnou cenu.", self.instrument_id.name))
        self.sudo().write({"derecognition_price": price, "derecognition_manual": manual})

    def _book(self):
        for trade in self.filtered(lambda t: t.state == "draft" and t.quantity < 0):
            trade._check_sale()
            trade._prepare_derecognition()
        return super()._book()

    def write(self, vals):
        if not self.env.su and {"derecognition_price", "derecognition_reason"} & set(vals) and self.filtered("event_id"):
            raise UserError(self.env._("Zaúčtovaný obchod nejde změnit; opravte ho stornem vypořádání nebo opravou obchodu."))
        return super().write(vals)
