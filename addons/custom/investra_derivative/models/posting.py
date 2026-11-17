"""Účtování FX spotu, forwardu a swapu: sjednání, vypořádání nohy, storna a náhled (DE-03).

Podrozvaha (vyhláška č. 501/2002 Sb. § 35 a § 41; ČÚS pro finanční instituce č. 110 bod 7 a 8, spot třída 9 bod 7):
při sjednání pohledávka v kupované a závazek v prodávané měně v nominálech kurzem dne sjednání, rozdíl na vyrovnávací
účet podrozvahy. Reálná hodnota je v rozvaze (ČÚS 110 bod 9; kladná § 14 odst. 1, záporná § 20 odst. 1 vyhlášky),
její změny ve výsledku (ČÚS 110 bod 11; spot ČÚS 105 bod 3). Při vypořádání nohy se reálná hodnota dopočte na
V ke dni vypořádání, zaúčtují se oba peněžní toky, reálná hodnota nohy se zruší a podrozvaha nohy odúčtuje.

Doklady vznikají jen přes účetní události; náhled je ze stejných funkcí, které účtují (`investra.posting.preview`).
"""
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from ..calc import d, days_left, leg_fair_value, leg_value, money

# Role účtů podle druhu smlouvy; čísla účtů schválil Martin 2026-11-16 (docs/rozhodnuti.md).
ROLES = {
    "forward": {
        "asset": "derivative", "liability": "derivative_liability", "gain": "gain_derivative", "loss": "loss_derivative",
        "receivable": "offbalance_forward_receivable", "payable": "offbalance_forward_payable",
    },
    "swap": {
        "asset": "derivative_swap", "liability": "derivative_swap_liability", "gain": "gain_derivative_swap",
        "loss": "loss_derivative_swap", "receivable": "offbalance_swap_receivable", "payable": "offbalance_swap_payable",
    },
    "spot": {
        "asset": "fx_spot_asset", "liability": "fx_spot_liability", "gain": "gain_fx_spot", "loss": "loss_fx_spot",
        "receivable": "offbalance_spot_receivable", "payable": "offbalance_spot_payable",
    },
}
CLEARING = "offbalance_clearing"
PREPARER = "investra_entity.group_valuation_preparer"


class InvestraDerivative(models.Model):
    _name = "investra.derivative"
    _inherit = ["investra.derivative", "investra.posting.preview", "investra.approval.pending.mixin"]

    event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Událost sjednání")
    reversal_reason = fields.Text(readonly=True, copy=False, string="Důvod storna")
    settlement_reversal_reason = fields.Text(
        readonly=True, copy=False, string="Důvod storna vypořádání",
        help="Poslední storno vypořádání nohy; noha se po něm vrátila do stavu Otevřená.",
    )
    posting_preview = fields.Html(
        compute="_compute_posting_preview", sanitize=False, string="Zaúčtování",
        help="Zaúčtované doklady smlouvy včetně storen; u návrhu náhled podrozvahy při sjednání, u sjednané smlouvy "
             "náhled vypořádání nejbližší otevřené nohy.",
    )

    # --- pomocné --------------------------------------------------------------------------------------------------

    def _roles(self):
        self.ensure_one()
        return ROLES[self.kind]

    def _require_preparer(self):
        if not self.env.user.has_group(PREPARER):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        self.check_access("write")

    def _line_extra(self):
        self.ensure_one()
        return {"investra_instrument_id": self.instrument_id.id}

    def _ledger(self, role, day, currency=None, valuation=None):
        """Zůstatek role na řádcích této smlouvy k datu; s oceněním včetně jeho návrhů dokladů."""
        self.ensure_one()
        accounts = self.env["investra.account.role"].accounts_for(self.company_id, role)
        extra = [("account_id", "in", accounts.ids), ("investra_instrument_id", "=", self.instrument_id.id)]
        if currency:
            extra.append(("currency_id", "=", currency.id))
        if valuation:
            domain = valuation._line_domain(*extra)  # k datu ocenění, včetně návrhů dokladů tohoto ocenění
        else:
            domain = [("company_id", "=", self.company_id.id), ("date", "<=", day), ("parent_state", "=", "posted"), *extra]
        total = self.env["account.move.line"].sudo()._read_group(domain, aggregates=["balance:sum"])[0][0]
        return money(total)

    def _booked_fair_value(self, day, valuation=None):
        """Zaúčtovaná reálná hodnota smlouvy: (aktivní účet, pasivní účet); pasivní zůstatek je záporný."""
        roles = self._roles()
        return self._ledger(roles["asset"], day, valuation=valuation), self._ledger(roles["liability"], day, valuation=valuation)

    def _open_legs(self, day):
        """Nohy otevřené k datu: nevypořádané, nebo vypořádané až po tomto dni."""
        self.ensure_one()
        return self.leg_ids.filtered(lambda leg: leg.state == "open" or leg.settlement_date > day)

    def _ensure_classification(self):
        """Zařazení nástroje v obchodním modelu ke dni sjednání (kategorie, způsob ocenění a role podle návrhu typu)."""
        self.ensure_one()
        Classification = self.env["investra.portfolio.classification"]
        if not Classification._valid(self.portfolio_id, self.instrument_id, self.trade_date):
            Classification.create({
                "portfolio_id": self.portfolio_id.id, "instrument_id": self.instrument_id.id, "valid_from": self.trade_date,
            })

    def _currency_values(self, currency, amount):
        """Měna řádku: cizí měna s částkou; funkční měna bez (Odoo doplní měnu knihy)."""
        self.ensure_one()
        if currency == self.company_id.currency_id:
            return {}
        return {"currency_id": currency.id, "amount_currency": str(amount)}

    # --- řádky dokladů (zaúčtování i náhled) ------------------------------------------------------------------------

    def _agree_lines(self):
        """Podrozvaha při sjednání: za každou nohu MD pohledávka, D závazek, rozdíl vyrovnávací účet."""
        self.ensure_one()
        roles, extra, lines = self._roles(), self._line_extra(), []
        for leg in self.leg_ids.sorted(lambda l: (l.settlement_date, l.sequence, l.id)):
            buy_rate, sell_rate = leg._rates(self.trade_date)
            receivable, payable = money(d(leg.buy_amount) * buy_rate), money(d(leg.sell_amount) * sell_rate)
            label = {"name": self.env._("%(name)s – noha %(day)s", name=self.name, day=fields.Date.to_string(leg.settlement_date))}
            lines.append({"role": roles["receivable"], "amount": str(receivable), "extra": extra, **label,
                          **self._currency_values(leg.buy_currency_id, d(leg.buy_amount))})
            lines.append({"role": roles["payable"], "amount": str(-payable), "extra": extra, **label,
                          **self._currency_values(leg.sell_currency_id, -d(leg.sell_amount))})
            if receivable != payable:
                lines.append({"role": CLEARING, "amount": str(payable - receivable), "extra": extra, **label})
        return lines

    def _settle_lines(self, leg, buy_account=None, sell_account=None):
        """Vypořádání nohy ke dni vypořádání: (rozvahové řádky, podrozvahové řádky).

        Rozvaha: dopočet RH smlouvy, oba peněžní toky, zrušení RH nohy. Podrozvaha: odúčtování nohy. Jsou to dva
        doklady, protože Odoo nedovolí v jednom dokladu kombinovat podrozvahové a ostatní účty.
        Reálná hodnota smlouvy se bere z hlavní knihy (zaúčtované doklady do dne vypořádání), takže vypořádání
        navazuje na poslední zaúčtované ocenění, ať bylo kdykoli.
        """
        self.ensure_one()
        roles, extra, day = self._roles(), self._line_extra(), leg.settlement_date
        buy_rate, sell_rate = leg._rates(day)
        cash_in, cash_out = money(d(leg.buy_amount) * buy_rate), money(d(leg.sell_amount) * sell_rate)
        leg_value_now = cash_in - cash_out
        others = sum((money(other._fair_value(day)) for other in self._open_legs(day) - leg), Decimal(0))
        total = others + leg_value_now
        asset, liability = self._booked_fair_value(day)
        delta = total - (asset + liability)
        movement = "fx_revaluation" if self.kind == "spot" else "price_revaluation"
        name = {"name": self.env._("Dopočet reálné hodnoty %s", self.name)}
        lines = [
            # 1. dopočet reálné hodnoty smlouvy na hodnotu ke dni vypořádání
            {"role": roles["asset"], "amount": str(max(total, Decimal(0)) - asset), "movement_type": movement, "extra": extra, **name},
            {"role": roles["liability"], "amount": str(min(total, Decimal(0)) - liability), "movement_type": movement,
             "extra": extra, **name},
            {"role": roles["gain"] if delta > 0 else roles["loss"], "amount": str(-delta), "movement_type": movement,
             "extra": extra, **name},
            # 2. peněžní toky a zrušení reálné hodnoty vypořádané nohy
            {"role": "bank", "amount": str(cash_in), "movement_type": "transaction",
             "extra": {"account_id": (buy_account or leg._default_bank_account(leg.buy_currency_id)).id},
             **self._currency_values(leg.buy_currency_id, d(leg.buy_amount))},
            {"role": "bank", "amount": str(-cash_out), "movement_type": "transaction",
             "extra": {"account_id": (sell_account or leg._default_bank_account(leg.sell_currency_id)).id},
             **self._currency_values(leg.sell_currency_id, -d(leg.sell_amount))},
            {"role": roles["asset"], "amount": str(max(others, Decimal(0)) - max(total, Decimal(0))),
             "movement_type": "transaction", "extra": extra},
            {"role": roles["liability"], "amount": str(min(others, Decimal(0)) - min(total, Decimal(0))),
             "movement_type": "transaction", "extra": extra},
        ]
        # 3. odúčtování podrozvahy nohy v zůstatcích, v jakých je vedena (po posledním přepočtu)
        receivable = self._ledger(roles["receivable"], day, currency=leg.buy_currency_id)
        payable = self._ledger(roles["payable"], day, currency=leg.sell_currency_id)
        label = {"name": self.env._("Odúčtování podrozvahy %s", self.name)}
        off_balance = [
            {"role": roles["receivable"], "amount": str(-receivable), "extra": extra, **label,
             **self._currency_values(leg.buy_currency_id, -d(leg.buy_amount))},
            {"role": roles["payable"], "amount": str(-payable), "extra": extra, **label,
             **self._currency_values(leg.sell_currency_id, d(leg.sell_amount))},
            {"role": CLEARING, "amount": str(receivable + payable), "extra": extra, **label},
        ]
        nonzero = lambda rows: [line for line in rows if Decimal(line["amount"])]
        return nonzero(lines), nonzero(off_balance)

    def _post_event(self, key, name, day, lines, event_type):
        event = self.env["investra.accounting.event"]._create_event(
            self.company_id, key, name, day, event_type, lines, source=self,
        )
        event._lock_events()
        event._post_events()
        return event

    # --- sjednání -------------------------------------------------------------------------------------------------

    def action_agree(self):
        self._require_preparer()
        self.sudo()._agree()
        return True

    def _agree(self):
        """Návrh → Sjednáno: uloží na nohy kurzy dne sjednání a B0, zapíše podrozvahu. Rozvaha se nemění."""
        for derivative in self:
            if derivative.state != "draft":
                raise UserError(self.env._("Sjednat jde jen smlouvu ve stavu Návrh."))
            derivative._check_structure()
            derivative._ensure_classification()
            for leg in derivative.leg_ids:
                buy_rate, sell_rate = leg._rates(derivative.trade_date)
                leg.write({
                    "buy_rate0": float(buy_rate), "sell_rate0": float(sell_rate),
                    "b0": float(leg_value(leg.buy_amount, buy_rate, leg.sell_amount, sell_rate)),
                })
            event = derivative._post_event(
                f"derivative:{derivative.id}", self.env._("Sjednání %s", derivative.name), derivative.trade_date,
                derivative._agree_lines(), "trade",
            )
            derivative.write({"event_id": event.id, "state": "agreed"})

    # --- vypořádání nohy -------------------------------------------------------------------------------------------

    def _next_leg(self):
        self.ensure_one()
        return self.leg_ids.filtered(lambda leg: leg.state == "open").sorted(lambda l: (l.settlement_date, l.sequence, l.id))[:1]

    def action_open_settle(self):
        self.ensure_one()
        leg = self._next_leg()
        if not leg:
            raise UserError(self.env._("Smlouva nemá otevřenou nohu."))
        return leg.action_open_settle()

    def _check_valuation_lock(self, day, what):
        """Zámek ocenění jako u obchodu: ocenění Ke schválení až Potvrzeno s datem ≥ day úkon zastaví."""
        self.ensure_one()
        Valuation = self.env["investra.valuation"]
        locking = Valuation._locking(self.company_id, day)
        if locking:
            Valuation._raise_locked(locking, day, what)

    def _settle_leg(self, leg, buy_account=None, sell_account=None):
        self.ensure_one()
        if self.state != "agreed" or leg.state != "open":
            raise UserError(self.env._("Vypořádat jde jen otevřenou nohu sjednané smlouvy."))
        if leg != self._next_leg():
            raise UserError(self.env._("Nejdřív vypořádejte nohu s dřívějším datem vypořádání."))
        if leg.settlement_date > fields.Date.context_today(self):
            raise UserError(self.env._(
                "Nohu jde vypořádat nejdřív v den vypořádání %s.", fields.Date.to_string(leg.settlement_date)))
        for account in (buy_account, sell_account):
            if account and account not in leg._bank_accounts():
                raise UserError(self.env._("Účet %s není bankovním účtem fondu (role Bankovní účet).", account.display_name))
        self._check_valuation_lock(leg.settlement_date, self.env._("Vypořádání nohy derivátu"))
        lines, off_balance = self._settle_lines(leg, buy_account, sell_account)
        event = self._post_event(
            f"derivative-settle:{leg.id}", self.env._("Vypořádání %s", self.name), leg.settlement_date,
            lines, "trade_settlement",
        )
        vals = {"state": "settled", "settlement_event_id": event.id}
        if off_balance:
            vals["offbalance_event_id"] = self._post_event(
                f"derivative-settle-ob:{leg.id}", self.env._("Odúčtování podrozvahy %s", self.name), leg.settlement_date,
                off_balance, "trade_settlement",
            ).id
        leg.write(vals)
        if not self._next_leg():
            self.write({"state": "settled"})

    # --- storna ---------------------------------------------------------------------------------------------------

    def _check_reason(self, reason):
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod."))

    def _last_settled_leg(self):
        self.ensure_one()
        return self.leg_ids.filtered(lambda leg: leg.state == "settled").sorted(
            lambda l: (l.settlement_date, l.sequence, l.id))[-1:]

    def action_reverse_settlement(self, reason):
        """Storno vypořádání naposledy vypořádané nohy; noha je znovu otevřená a smlouva Sjednáno."""
        self.ensure_one()
        self._require_preparer()
        if not self._last_settled_leg() or self.state not in ("agreed", "settled"):
            raise UserError(self.env._("Smlouva nemá vypořádanou nohu."))
        self._check_reason(reason)
        request = self.env["investra.approval.matrix"]._gate(
            "trade_reverse", self, "action_reverse_settlement", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno vypořádání nohy derivátu: %s", reason),
        )
        if request:
            return request
        self._do_reverse_settlement(reason)
        return self

    def action_reverse(self, reason):
        """Storno smlouvy: stornují se doklady sjednání i vypořádání k jejich datům."""
        self.ensure_one()
        self._require_preparer()
        if self.state not in ("agreed", "settled"):
            raise UserError(self.env._("Stornovat lze jen sjednanou nebo vypořádanou smlouvu."))
        self._check_reason(reason)
        request = self.env["investra.approval.matrix"]._gate(
            "trade_reverse", self, "action_reverse", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno derivátu: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self

    @api.model
    def _retire_event_key(self, event):
        """Stornovaná událost uvolní klíč, aby nové vypořádání mohlo vzniknout (stejně jako u obchodu)."""
        event._service().write({"key": f"{event.key}#reversed{event.id}"})

    def _do_reverse_settlement(self, reason):
        derivative = self.sudo()
        leg = derivative._last_settled_leg()
        events = leg.settlement_event_id | leg.offbalance_event_id
        derivative._check_valuation_lock(leg.settlement_date, self.env._("Storno vypořádání nohy derivátu"))
        events._reverse_events()
        for event in events:
            self._retire_event_key(event)
        leg.write({"state": "open", "settlement_event_id": False, "offbalance_event_id": False})
        derivative.write({"state": "agreed", "settlement_reversal_reason": reason})

    def _do_reverse(self, reason):
        derivative = self.sudo()
        derivative._check_valuation_lock(derivative.trade_date, self.env._("Storno derivátu"))
        legs = derivative.leg_ids
        events = (legs.settlement_event_id | legs.offbalance_event_id | derivative.event_id).filtered(
            lambda e: e.state == "posted")
        events._reverse_events()
        for event in events:
            self._retire_event_key(event)
        derivative.write({"state": "reversed", "reversal_reason": reason})

    # --- náhled zaúčtování -----------------------------------------------------------------------------------------

    @api.depends("state", "kind", "fund_id", "trade_date", "event_id", "event_id.state", "reversal_reason",
                 "leg_ids.state", "leg_ids.settlement_date", "leg_ids.buy_amount", "leg_ids.sell_amount",
                 "leg_ids.buy_currency_id", "leg_ids.sell_currency_id", "leg_ids.settlement_event_id")
    def _compute_posting_preview(self):
        for derivative in self:
            derivative.posting_preview = derivative._posting_preview_html()

    def _ready_for_preview(self):
        ready = self.fund_id and self.trade_date and self.leg_ids and all(
            leg.settlement_date and leg.buy_currency_id and leg.sell_currency_id and leg.buy_amount and leg.sell_amount
            for leg in self.leg_ids)
        return bool(ready) and (self.state == "draft" or (self.state == "agreed" and bool(self._next_leg())))

    def _preview_rows(self, lines):
        """Jako společný náhled, jen bankovní řádek ukáže zvolený účet (řádek ho nese v `extra`)."""
        Role, Account, rows = self.env["investra.account.role"], self.env["account.account"].sudo(), []
        for line in lines:
            account_id = line.get("extra", {}).get("account_id")
            account = Account.browse(account_id) if account_id else Role.account_for(self.company_id, line["role"])
            amount, label = d(line["amount"]), line.get("name") or ""
            rows.append((account.display_name + (f" ({label})" if label else ""),
                         amount if amount > 0 else Decimal(0), -amount if amount < 0 else Decimal(0),
                         line.get("amount_currency")))
        return rows

    def _preview_documents(self):
        self.ensure_one()
        if self.state == "draft":
            return [(self.env._("Při sjednání (podrozvaha)"), self.trade_date, self._preview_rows(self._agree_lines()))]
        leg = self._next_leg()
        if leg.settlement_date > fields.Date.context_today(self):
            raise UserError(self.env._(
                "Náhled vypořádání nohy bude k dispozici od dne vypořádání %s (dřív není kurz).",
                fields.Date.to_string(leg.settlement_date)))
        return self._settle_documents(leg)

    def _settle_documents(self, leg, buy_account=None, sell_account=None):
        lines, off_balance = self._settle_lines(leg, buy_account, sell_account)
        documents = [(self.env._("Při vypořádání nohy"), leg.settlement_date, self._preview_rows(lines))]
        if off_balance:
            documents.append((self.env._("Při vypořádání nohy (podrozvaha)"), leg.settlement_date,
                              self._preview_rows(off_balance)))
        return documents

    def _preview_currency(self):
        functional = self.company_id.currency_id
        foreign = (self.leg_ids.buy_currency_id | self.leg_ids.sell_currency_id) - functional
        return foreign[:1]

    def _preview_intro(self):
        if self.state == "draft":
            return self.env._("Jen náhled: nic se neúčtuje. Podrozvahový doklad vznikne tlačítkem Sjednat; rozvaha se nemění.")
        return self.env._("Náhled: doklad vznikne tlačítkem Vypořádat nohu (s výchozími bankovními účty; jiné zvolíte v okně vypořádání).")

    def _booked_intro(self):
        return self.env._("Zaúčtované doklady smlouvy.")

    def _booked_caption(self, event):
        captions = {"trade": self.env._("Sjednání"), "trade_settlement": self.env._("Vypořádání nohy")}
        return captions.get(event.event_type, event.name)


class InvestraDerivativeLeg(models.Model):
    _inherit = "investra.derivative.leg"

    buy_rate0 = fields.Float(digits=(16, 8), readonly=True, copy=False, string="Kurz kupované měny při sjednání")
    sell_rate0 = fields.Float(digits=(16, 8), readonly=True, copy=False, string="Kurz prodávané měny při sjednání")
    b0 = fields.Float(
        digits=(20, 6), readonly=True, copy=False, string="Forwardové body (B0)",
        help="Hodnota nohy ve funkční měně kurzy dne sjednání: kupovaná částka × kurz − prodávaná částka × kurz. "
             "Rozpouští se rovnoměrně do dne vypořádání.",
    )
    settlement_event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Událost vypořádání")
    offbalance_event_id = fields.Many2one(
        "investra.accounting.event", readonly=True, copy=False, string="Událost odúčtování podrozvahy")

    def _rates(self, day):
        """(kurz kupované měny, kurz prodávané měny) = funkční měna fondu za jednotku, ze zdroje kurzů fondu."""
        self.ensure_one()
        fund = self.derivative_id.fund_id
        return fund._fx_at(self.buy_currency_id, day), fund._fx_at(self.sell_currency_id, day)

    def _value(self, day):
        """V(t) nezaokrouhleně."""
        buy_rate, sell_rate = self._rates(day)
        return leg_value(self.buy_amount, buy_rate, self.sell_amount, sell_rate)

    def _days(self, day):
        """(zbývající dny, dny celkem) od sjednání do vypořádání."""
        self.ensure_one()
        total = (self.settlement_date - self.derivative_id.trade_date).days
        return days_left(day, self.settlement_date), total

    def _fair_value(self, day):
        """RH(t) nohy nezaokrouhleně, varianta B."""
        left, total = self._days(day)
        return leg_fair_value(self._value(day), self.b0, left, total)

    def _bank_accounts(self):
        self.ensure_one()
        return self.env["investra.account.role"].accounts_for(self.company_id, "bank")

    def _default_bank_account(self, currency):
        """Bankovní účet fondu v měně toku; jinak hlavní účet role Bankovní účet."""
        self.ensure_one()
        accounts = self._bank_accounts()
        functional = self.company_id.currency_id
        if currency == functional:
            match = accounts.filtered(lambda a: not a.currency_id or a.currency_id == functional)
        else:
            match = accounts.filtered(lambda a: a.currency_id == currency)
        return match[:1] or self.env["investra.account.role"].account_for(self.company_id, "bank")

    def action_open_settle(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "name": self.env._("Vypořádat nohu"),
            "res_model": "investra.derivative.settle.wizard", "view_mode": "form", "target": "new",
            "context": {"default_leg_id": self.id},
        }

    def action_settle(self, buy_account=None, sell_account=None):
        self.ensure_one()
        self.derivative_id._require_preparer()
        accounts = self.env["account.account"].sudo()
        self.derivative_id.sudo()._settle_leg(
            self.sudo(), accounts.browse(buy_account.id) if buy_account else None,
            accounts.browse(sell_account.id) if sell_account else None)
        return True
