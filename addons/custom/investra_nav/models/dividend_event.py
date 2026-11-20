"""Dividenda jako událost cenného papíru (ZJ-22, dávka ZJ-07 až ZJ-19, navazuje na ZJ-19).

Uživatel zadá cenný papír (ISIN), ex-datum, datum výplaty a hrubou dividendu na kus; fond se nevybírá. Akce „Načíst držitele“
založí řádky (`investra.dividend`) pro každý fond a portfolio, které držely nástroj k večeru dne před ex-datem
(`Trade._holdings`). Účtování, výplata a storno zůstávají po řádcích, tj. v knize fondu a s oprávněním na úrovni fondu.
Jedna událost = jeden cenný papír a ex-datum; oprava dividendy je další událost (po stornu řádků předchozí).
"""
from datetime import timedelta
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import UserError

from .dividend import DEFAULT_DOMESTIC_WITHHOLDING, DEFAULT_TREATY_RATE, KINDS


class InvestraDividendEvent(models.Model):
    _name = "investra.dividend.event"
    _inherit = ["mail.thread"]
    _description = "Dividenda cenného papíru"
    _order = "ex_date desc, id desc"

    instrument_id = fields.Many2one(
        "investra.instrument", required=True, ondelete="restrict", index=True, string="Cenný papír", tracking=True,
        domain="[('type_id.kind', 'in', ('equity', 'fund', 'participation'))]",
        help="Akcie, podílový list nebo účast; dividendu vyplácí nástroj bez splátkového kalendáře.")
    isin = fields.Char(related="instrument_id.isin", string="ISIN")
    ex_date = fields.Date(required=True, tracking=True, string="Ex-datum",
                          help="Od tohoto dne se obchoduje bez dividendy; nárok má držitel k večeru dne před ex-datem.")
    pay_date = fields.Date(tracking=True, string="Datum výplaty")
    currency_id = fields.Many2one(related="instrument_id.currency_id", string="Měna dividendy")
    per_share = fields.Float(digits=(20, 8), tracking=True, string="Hrubá dividenda na kus")
    kind = fields.Selection(KINDS, compute="_compute_kind", store=True, readonly=False, precompute=True, tracking=True,
                            string="Druh dividendy", help="Podle země emitenta: česká nebo zahraniční; z dceřiné společnosti jen ručně.")
    withholding_rate = fields.Float(compute="_compute_rates", store=True, readonly=False, precompute=True, digits=(16, 4),
                                    tracking=True, string="Výchozí sražená sazba %", help="Předvyplní se do řádků držitelů.")
    treaty_rate = fields.Float(default=DEFAULT_TREATY_RATE, digits=(16, 4), tracking=True, string="Smluvní sazba %",
                               help="Jen zahraniční dividenda: předvyplní se do řádků držitelů.")
    line_ids = fields.One2many("investra.dividend", "dividend_event_id", string="Držitelé")
    state = fields.Selection(
        [("draft", "Návrh"), ("booked", "Zaúčtováno k ex-datu"), ("paid", "Vyplaceno"), ("reversed", "Stornováno")],
        compute="_compute_state", store=True, string="Stav")
    gross_total = fields.Float(compute="_compute_totals", digits=(20, 2), string="Hrubá dividenda celkem")
    withheld_total = fields.Float(compute="_compute_totals", digits=(20, 2), string="Srážka celkem")
    net_total = fields.Float(compute="_compute_totals", digits=(20, 2), string="Čistá dividenda celkem")

    @api.depends("instrument_id.name", "instrument_id.isin", "ex_date")
    def _compute_display_name(self):
        for event in self:
            instrument = event.instrument_id
            label = f"{instrument.name} ({instrument.isin})" if instrument.isin else (instrument.name or "")
            event.display_name = f"{label} – {event.ex_date}" if event.ex_date and label else label

    def _origin_kind(self):
        """Druh podle země emitenta (jako řádek dividendy): CZ → česká, jinak zahraniční."""
        self.ensure_one()
        instrument, country = self.instrument_id, ""
        if "issuer_id" in instrument._fields and instrument.issuer_id.country_id:
            country = instrument.issuer_id.country_id.code or ""
        elif instrument.isin:
            country = instrument.isin[:2]
        return "foreign" if country and country != "CZ" else "domestic"

    @api.depends("instrument_id")
    def _compute_kind(self):
        for event in self:
            if event.instrument_id and event.kind != "subsidiary":
                event.kind = event._origin_kind()
            elif not event.kind:
                event.kind = "domestic"

    @api.depends("kind", "instrument_id")
    def _compute_rates(self):
        for event in self:
            domestic = event.kind == "domestic" or (event.kind == "subsidiary" and event._origin_kind() == "domestic")
            event.withholding_rate = DEFAULT_DOMESTIC_WITHHOLDING if domestic else 0.0

    @api.depends("line_ids.state")
    def _compute_state(self):
        for event in self:
            states = set(event.line_ids.mapped("state"))
            live = states - {"reversed"}
            if not states or "draft" in states:
                event.state = "draft"
            elif not live:
                event.state = "reversed"
            elif live == {"paid"}:
                event.state = "paid"
            else:
                event.state = "booked"

    @api.depends("line_ids.gross_amount", "line_ids.withheld_amount", "line_ids.net_amount", "line_ids.state")
    def _compute_totals(self):
        for event in self:
            lines = event.line_ids.filtered(lambda l: l.state != "reversed")
            event.gross_total = sum(lines.mapped("gross_amount"))
            event.withheld_total = sum(lines.mapped("withheld_amount"))
            event.net_total = sum(lines.mapped("net_amount"))

    @api.constrains("instrument_id", "ex_date")
    def _check_unique(self):
        for event in self:
            duplicate = self.sudo().search([("id", "!=", event.id), ("instrument_id", "=", event.instrument_id.id),
                                            ("ex_date", "=", event.ex_date), ("state", "!=", "reversed")], limit=1)
            if duplicate:
                raise UserError(self.env._(
                    "Dividenda cenného papíru %(name)s s ex-datem %(day)s už existuje. Opravu zadejte až po stornu řádků předchozí.",
                    name=event.instrument_id.name, day=event.ex_date))

    # --- propagace do řádků -----------------------------------------------------------------------------------------

    def write(self, vals):
        locked = {"instrument_id", "ex_date"} & set(vals)
        if locked and self.line_ids.filtered(lambda l: l.state != "draft"):
            raise UserError(self.env._("Cenný papír a ex-datum nejdou změnit po zaúčtování řádku; opravte stornem."))
        result = super().write(vals)
        draft_fields = {name for name in ("instrument_id", "ex_date", "per_share", "kind", "withholding_rate", "treaty_rate")
                        if name in vals}
        for event in self:
            drafts = event.line_ids.filtered(lambda l: l.state == "draft")
            if draft_fields and drafts:
                drafts.write({name: event[name].id if name == "instrument_id" else event[name] for name in draft_fields})
            if "pay_date" in vals:
                event.line_ids.filtered(lambda l: l.state in ("draft", "booked")).sudo().write({"pay_date": event.pay_date})
        return result

    # --- akce -------------------------------------------------------------------------------------------------------

    def _require_preparer(self):
        self.env["investra.dividend"]._require_preparer()

    def action_load_holders(self):
        """Založí řádky pro každý fond a portfolio, které držely nástroj k večeru dne před ex-datem; existující nepřepíše."""
        self._require_preparer()
        Line = self.env["investra.dividend"]
        added = 0
        for event in self:
            if not (event.instrument_id and event.ex_date):
                raise UserError(self.env._("Nejdřív vyplňte cenný papír a ex-datum."))
            existing = {(l.fund_id.id, l.portfolio_id.id) for l in event.line_ids.sudo() if l.state != "reversed"}
            day = event.ex_date - timedelta(days=1)
            for fund in self.env["investra.fund"].search([]):
                holdings = self.env["investra.trade"].sudo()._holdings(fund.sudo(), day)
                for (instrument, portfolio), quantity in holdings.items():
                    if instrument != event.instrument_id or Decimal(str(quantity)) <= 0 or (fund.id, portfolio.id) in existing:
                        continue
                    line = Line.create({
                        "dividend_event_id": event.id, "fund_id": fund.id, "portfolio_id": portfolio.id,
                        "instrument_id": event.instrument_id.id, "ex_date": event.ex_date, "pay_date": event.pay_date,
                        "per_share": event.per_share, "kind": event.kind, "withholding_rate": event.withholding_rate,
                        "treaty_rate": event.treaty_rate,
                    })
                    line._onchange_defaults()  # kurzy k ex-datu a k výplatě jako ve formuláři
                    added += 1
        return self._notify(self.env._("Načteno držitelů: %s.", added), "success" if added else "warning")

    def _notify(self, message, kind="success", sticky=False):
        return {"type": "ir.actions.client", "tag": "display_notification",
                "params": {"type": kind, "message": message, "sticky": sticky,
                           "next": {"type": "ir.actions.client", "tag": "soft_reload"}}}

    def _run_per_line(self, state, method, label):
        """Provede krok po řádcích dostupných uživateli; chybný řádek nezastaví ostatní (každý má vlastní savepoint)."""
        self._require_preparer()
        done, errors = 0, []
        for event in self:
            for line in event.line_ids.filtered(lambda l: l.state == state):
                try:
                    with self.env.cr.savepoint():
                        getattr(line, method)()
                    done += 1
                except Exception as error:  # noqa: BLE001 – chyba řádku se vypíše, ostatní pokračují
                    errors.append(f"{line.fund_id.name}: {getattr(error, 'args', [error])[0]}")
        if not done and not errors:
            raise UserError(self.env._("Není co zpracovat: žádný řádek ve stavu %s.", dict(self._fields["state"].selection)[state]))
        message = self.env._("%(label)s: %(done)s řádků.", label=label, done=done)
        if errors:
            message += " " + self.env._("Nezpracováno: %s", "; ".join(errors))
        return self._notify(message, "warning" if errors else "success", sticky=bool(errors))

    def action_book_all(self):
        return self._run_per_line("draft", "action_book", self.env._("Zaúčtováno"))

    def action_pay_all(self):
        return self._run_per_line("booked", "action_pay", self.env._("Vyplaceno"))
