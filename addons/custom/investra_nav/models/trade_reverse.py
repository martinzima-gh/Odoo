"""Storno vypořádání, storno a oprava obchodu (rozhodnutí 2026-11-12 „Storno a oprava obchodu“).

- Storno vypořádání: událost vypořádání se stornuje k jejímu datu a obchod se vrátí do stavu Sjednáno, nevypořádáno;
  datum a kurz vypořádání pak jdou opravit a obchod znovu vypořádat. U rozvahy ke dni vypořádání je vypořádání zároveň
  zaúčtováním obchodu, proto se vyprázdní i událost obchodu.
- Storno: všechny události obchodu se stornují k jejich datům, obchod dostane stav Stornováno a nepočítá se do pozic.
- Oprava: storno a nový obchod v návrhu s odkazem na opravovaný.

Zámek ocenění: ocenění Ke schválení až Potvrzeno storno odmítne (nejdřív ho vraťte); po zveřejnění projde storno jen
s výjimkou z uzamčení (zámek Odoo hlídá zaúčtování stornodokladu). Úkon jde přes schvalovací matici, činnost
„Storno a oprava obchodu“ (`trade_reverse`).
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class InvestraTradeReverse(models.Model):
    _inherit = "investra.trade"

    # --- kontroly --------------------------------------------------------------------------------------------

    def _check_reason(self, reason):
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod."))

    def _check_valuation_lock(self, day, what):
        """Vrstva 1 zámku ocenění jako u splátek: ocenění Ke schválení až Potvrzeno s datem ≥ day storno zastaví."""
        self.ensure_one()
        Valuation = self.env["investra.valuation"]
        locking = Valuation._locking(self.company_id, day)
        if locking:
            Valuation._raise_locked(locking, day, what)

    def _check_position_without_self(self):
        """Storno nákupu nesmí nechat pozdější prodej bez kusů ani zaúčtovanou splátku bez pozice.

        Doplněno při provedení (nebylo v návrhu): bez kontroly by pozice po stornu šla do záporu.
        """
        self.ensure_one()
        if self.quantity <= 0:
            return
        trades = self.sudo().search([
            ("fund_id", "=", self.fund_id.id), ("portfolio_id", "=", self.portfolio_id.id),
            ("instrument_id", "=", self.instrument_id.id), ("state", "!=", "reversed"), ("id", "!=", self.id),
        ], order="trade_date, id")
        held = 0.0
        for trade in trades:
            held += trade.quantity
            if held < -1e-9:
                raise UserError(self.env._(
                    "Po stornu by prodej %(name)s k %(day)s neměl dost kusů. Nejdřív stornujte nebo opravte prodej.",
                    name=self.instrument_id.name, day=trade.trade_date,
                ))
        repayment = self.env["investra.instrument.repayment"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("portfolio_id", "=", self.portfolio_id.id),
            ("instrument_id", "=", self.instrument_id.id), ("state", "=", "posted"), ("date", ">=", self.trade_date),
        ], limit=1)
        if repayment:
            raise UserError(self.env._(
                "Pozice %(name)s má od data obchodu zaúčtovanou splátku z %(day)s. Nejdřív stornujte splátku.",
                name=self.instrument_id.name, day=repayment.date,
            ))

    def _check_reversible(self, reason, what):
        self.ensure_one()
        self._require_preparer()
        if self.state not in ("unsettled", "settled"):
            raise UserError(self.env._("%s lze jen zaúčtovaný obchod.", what))
        self._check_reason(reason)

    def _check_settlement_reversible(self, reason):
        self.ensure_one()
        self._require_preparer()
        if self.state != "settled" or not self.settlement_event_id:
            raise UserError(self.env._(
                "Stornovat vypořádání lze jen u vypořádaného obchodu s odloženým vypořádáním. "
                "Obchod vypořádaný v den sjednání opravte opravou obchodu."
            ))
        self._check_reason(reason)

    # --- úkony -----------------------------------------------------------------------------------------------

    def action_reverse_settlement(self, reason):
        """Storno vypořádání; obchod zpět do stavu Sjednáno, nevypořádáno."""
        self._check_settlement_reversible(reason)
        request = self.env["investra.approval.matrix"]._gate(
            "trade_reverse", self, "action_reverse_settlement", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno vypořádání obchodu: %s", reason),
        )
        if request:
            return request
        self._do_reverse_settlement(reason)
        return self

    def action_reverse(self, reason):
        """Storno obchodu k datům jeho dokladů; obchod se přestane počítat do pozic."""
        self._check_reversible(reason, self.env._("Stornovat"))
        request = self.env["investra.approval.matrix"]._gate(
            "trade_reverse", self, "action_reverse", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno obchodu: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self

    def action_correct(self, reason):
        """Oprava = storno a nový obchod v návrhu s odkazem na opravovaný."""
        self._check_reversible(reason, self.env._("Opravit"))
        request = self.env["investra.approval.matrix"]._gate(
            "trade_reverse", self, "action_correct", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Oprava obchodu: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        default = {"replaced_id": self.id}
        if not self.foreign_currency:
            default.update(fx_rate=1, settlement_fx_rate=0)  # Měna fondu: chybný kurz se do opravy nepřenese.
        return self.copy(default)

    # --- provedení -------------------------------------------------------------------------------------------

    @api.model
    def _retire_event_key(self, event):
        """Stornovaná událost uvolní klíč, aby nové vypořádání mohlo vzniknout (jako zrušený návrh)."""
        event._service().write({"key": f"{event.key}#reversed{event.id}"})

    def _do_reverse_settlement(self, reason):
        trade = self.sudo()
        event = trade.settlement_event_id
        trade._check_valuation_lock(event.date, self.env._("Storno vypořádání obchodu"))
        event._reverse_events()
        self._retire_event_key(event)
        vals = {"settlement_event_id": False, "state": "unsettled", "settlement_reversal_reason": reason}
        if trade.event_id == event:
            vals["event_id"] = False  # Rozvaha ke dni vypořádání: vypořádání bylo zároveň zaúčtováním obchodu.
        trade.write(vals)

    def _do_reverse(self, reason):
        trade = self.sudo()
        trade._check_valuation_lock(trade.trade_date, self.env._("Storno obchodu"))
        trade._check_position_without_self()
        events = (trade.event_id | trade.settlement_event_id).filtered(lambda e: e.state == "posted")
        events._reverse_events()
        trade.write({"state": "reversed", "reversal_reason": reason})


class InvestraTradeReverseWizard(models.TransientModel):
    """Okno pro důvod storna vypořádání, storna nebo opravy obchodu; volá obchod, samo nic neúčtuje."""

    _name = "investra.trade.reverse.wizard"
    _description = "Storno nebo oprava obchodu"

    trade_id = fields.Many2one("investra.trade", required=True, ondelete="cascade", string="Obchod")
    mode = fields.Selection([
        ("settlement", "Stornovat vypořádání"),
        ("reverse", "Stornovat obchod"),
        ("correct", "Opravit (storno a nový obchod)"),
    ], required=True, default="correct", string="Krok")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    reason = fields.Text(required=True, string="Důvod")

    @api.depends("mode", "trade_id")
    def _compute_effect(self):
        for wizard in self:
            if wizard.mode == "settlement":
                wizard.effect = self.env._(
                    "Doklad vypořádání se stornuje k datu vypořádání a obchod se vrátí do stavu Sjednáno, nevypořádáno. "
                    "Opravte datum nebo kurz vypořádání a obchod znovu vypořádejte. U rozvahy ke dni vypořádání "
                    "se tím stornuje i zaúčtování obchodu."
                )
                continue
            wizard.effect = self.env._(
                "Doklady obchodu a vypořádání se stornují k jejich datům a obchod dostane stav Stornováno; "
                "do pozic se už nepočítá. Rozdíl v ocenění dopočítá další ocenění."
            ) + ("" if wizard.mode == "reverse" else self.env._(
                " Vznikne nový obchod v návrhu s odkazem na opravovaný; po úpravě ho zaúčtujte."
            ))

    def action_confirm(self):
        self.ensure_one()
        method = {
            "settlement": self.trade_id.action_reverse_settlement,
            "reverse": self.trade_id.action_reverse,
            "correct": self.trade_id.action_correct,
        }[self.mode]
        result = method(self.reason)
        if result._name == "investra.approval.request":
            return result._action_open()
        return {"type": "ir.actions.act_window", "res_model": result._name, "res_id": result.id,
                "view_mode": "form", "target": "current"}
