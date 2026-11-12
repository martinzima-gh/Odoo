from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import engine


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    principal = fields.Float(
        digits=(20, 2), string="Jistina na jednotku",
        help="Pro kalendář vkladu a pro splátky bez kalendáře. Doporučeno 1: kusy obchodu = jistina, cena na jednotku jistiny.",
    )
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

    def _principal_per_unit(self):
        """Jistina na jednotku: součet jistiny v kalendáři, bez kalendáře pole Jistina na jednotku, jinak 1
        (kusy = jistina; rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“)."""
        self.ensure_one()
        flows = self.cashflow_ids.filtered(lambda f: f.flow_type == "principal")
        return sum(flows.mapped("amount")) or self.principal or 1.0

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
        Repayment = self.env["investra.instrument.repayment"].sudo()
        factors = {}
        for trade in trades:
            if trade.portfolio_id not in factors:
                factors[trade.portfolio_id] = Repayment._prorata_factor(fund, self, trade.portfolio_id, day)
            factor = factors[trade.portfolio_id]
            quantity = engine.dec(trade.quantity) * factor
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
    """Splátka nástroje (jistina a úrok) v naběhlé i reálné hodnotě.

    Splátka účtuje MD inkasa na cestě / D nástroj; výpis pak inkaso vynuluje. Jistina snižuje kusy pozice, rozdíl proti
    požadované hodnotě doúčtuje ocenění (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“). Zaúčtovaná splátka je
    zamčená; chybu opraví storno nebo oprava (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
    """

    _name = "investra.instrument.repayment"
    _inherit = ["investra.record.guard"]
    _description = "Splátka nástroje"
    _order = "date desc, id desc"
    _book_fields = ("fund_id",)
    _system_fields = frozenset({"event_id", "state", "reversal_reason"})

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, string="Datum")
    instrument_id = fields.Many2one(
        "investra.instrument", required=True, ondelete="restrict", string="Nástroj",
        domain="[('id', 'in', allowed_instrument_ids)]",
    )
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", string="Obchodní model",
        domain="[('id', 'in', allowed_portfolio_ids)]", help="Doplní se z nákupu; volí se jen u nástroje drženého ve dvou modelech.",
    )
    allowed_instrument_ids = fields.Many2many("investra.instrument", compute="_compute_allowed", string="Držené nástroje")
    allowed_portfolio_ids = fields.Many2many("investra.fund.portfolio", compute="_compute_allowed", string="Modely nástroje")
    portfolio_choice = fields.Boolean(compute="_compute_allowed")
    kind = fields.Selection(
        [("scheduled", "Podle kalendáře"), ("prorata", "Mimořádná – poměrné snížení"), ("early_termination", "Předčasné ukončení")],
        required=True, default="scheduled", string="Druh",
        help="Mimořádná splátka úměrně sníží zbylé toky kalendáře; předčasné ukončení uzavře celou pozici "
             "(rozhodnutí 2026-11-12 „Mimořádná splátka nástroje“).",
    )
    principal_amount = fields.Float(digits=(20, 2), string="Jistina")
    interest_amount = fields.Float(digits=(20, 2), string="Úrok")
    fee_amount = fields.Float(
        digits=(20, 2), string="Poplatek", help="Poplatek, který fondu strhne protistrana (např. banka za předčasné ukončení); "
        "náklad fondu na bankovní poplatky, o který je výplata nižší.",
    )
    amount = fields.Float(compute="_compute_amount", store=True, digits=(20, 2), string="Výplata v měně nástroje")
    remaining_before = fields.Float(compute="_compute_remaining", digits=(20, 2), string="Zbývající jistina před splátkou")
    remaining_after = fields.Float(compute="_compute_remaining", digits=(20, 2), string="Zbývající jistina po splátce")
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
        return self.env["investra.portfolio.classification"]._valid(self.portfolio_id._origin, self.instrument_id._origin, self.date)

    # --- pozice, zbývající jistina a kalendář ------------------------------------------------------

    def _held_positions(self):
        """Pozice fondu (nástroj, obchodní model) k datu splátky, po zaúčtovaných splátkách."""
        self.ensure_one()
        if not self.fund_id:
            return {}
        # Ve formuláři (onchange) jsou vazby nové záznamy; hledá se podle původních (_origin).
        return self.env["investra.trade"].sudo()._holdings(self.fund_id._origin.sudo(), self.date or fields.Date.context_today(self))

    def _trades(self):
        self.ensure_one()
        return self.env["investra.trade"].sudo()._recognised(
            self.fund_id._origin.sudo(), self.date, self.instrument_id._origin, self.portfolio_id._origin
        )

    def _other_repaid(self):
        """Jistina ostatních zaúčtovaných splátek téže pozice do data splátky."""
        self.ensure_one()
        others = self.sudo().search([
            ("fund_id", "=", self.fund_id._origin.id), ("instrument_id", "=", self.instrument_id._origin.id),
            ("portfolio_id", "=", self.portfolio_id._origin.id), ("state", "=", "posted"), ("date", "<=", self.date),
            ("id", "!=", self._origin.id or 0),
        ])
        return engine.money(sum(engine.dec(r.principal_amount) for r in others))

    def _position_principal(self):
        """Jistina pozice z obchodů k datu (kusy × jistina na jednotku), bez splátek."""
        ppu = engine.dec(self.instrument_id._principal_per_unit())
        return engine.money(sum(engine.dec(t.quantity) for t in self._trades()) * ppu)

    def _schedule(self):
        """Toky kalendáře pozice po datech: {datum: (jistina, úrok)} v měně nástroje, podle kusů obchodů."""
        schedule = {}
        for trade in self._trades():
            quantity = engine.dec(trade.quantity)
            for flow in self.instrument_id.cashflow_ids.filtered(lambda f: f.date > trade.trade_date):
                principal, interest = schedule.get(flow.date, (engine.ZERO, engine.ZERO))
                amount = engine.dec(flow.amount) * quantity
                if flow.flow_type == "principal":
                    principal += amount
                else:
                    interest += amount
                schedule[flow.date] = (principal, interest)
        return dict(sorted(schedule.items()))

    @api.model
    def _prorata_factor(self, fund, instrument, portfolio, day):
        """Koeficient zbylých toků po mimořádných splátkách s poměrným snížením do data (rozhodnutí 2026-11-12
        „Mimořádná splátka nástroje“): každá sníží zbylé toky v poměru (zbývající jistina − splátka) / zbývající jistina,
        původní EIR se nemění."""
        repayments = self.sudo().search([
            ("fund_id", "=", fund.id), ("instrument_id", "=", instrument.id), ("portfolio_id", "=", portfolio.id),
            ("state", "=", "posted"), ("date", "<=", day),
        ], order="date, id")
        factor, repaid = engine.dec(1), engine.ZERO
        for repayment in repayments:
            principal = engine.dec(repayment.principal_amount)
            if repayment.kind == "prorata":
                before = repayment._position_principal() - repaid
                if before > 0:
                    factor *= (before - principal) / before
            repaid += principal
        return factor

    def _ready(self):
        return bool(self.fund_id and self.instrument_id and self.portfolio_id and self.date)

    @api.depends("fund_id", "date", "instrument_id")
    def _compute_allowed(self):
        for repayment in self:
            keys = list(repayment._held_positions())
            repayment.allowed_instrument_ids = [(6, 0, list({i.id for i, _p in keys}))]
            portfolios = [p.id for i, p in keys if i == repayment.instrument_id._origin]
            repayment.allowed_portfolio_ids = [(6, 0, portfolios)]
            repayment.portfolio_choice = len(portfolios) > 1

    @api.depends("principal_amount", "interest_amount", "fee_amount")
    def _compute_amount(self):
        for repayment in self:
            repayment.amount = float(engine.money(
                engine.dec(repayment.principal_amount) + engine.dec(repayment.interest_amount) - engine.dec(repayment.fee_amount)
            ))

    @api.depends("fund_id", "date", "instrument_id", "portfolio_id", "principal_amount", "kind")
    def _compute_remaining(self):
        for repayment in self:
            if not repayment._ready():
                repayment.remaining_before = repayment.remaining_after = 0.0
                continue
            before = repayment._position_principal() - repayment._other_repaid()
            repayment.remaining_before = float(before)
            after = before - engine.money(engine.dec(repayment.principal_amount))
            repayment.remaining_after = 0.0 if repayment.kind == "early_termination" else float(after)

    @api.onchange("instrument_id")
    def _onchange_instrument(self):
        """Nový nástroj: model z nákupu a vždy nové předvyplnění (částky předchozího nástroje k němu nepatří)."""
        self._onchange_position(force=True)

    @api.onchange("fund_id", "date")
    def _onchange_position(self, force=False):
        """Model z nákupu a předvyplnění jistiny a úroku podle kalendáře (bez kalendáře celá zbývající jistina).
        Při změně fondu nebo data se ručně zadané částky nepřepisují; předvyplní se jen prázdná splátka."""
        if self.state != "draft":
            return
        if self.instrument_id and self.instrument_id._origin not in self.allowed_instrument_ids._origin:
            self.instrument_id = False
        allowed = self.allowed_portfolio_ids._origin
        if self.portfolio_id._origin not in allowed:
            self.portfolio_id = allowed if len(allowed) == 1 else False
        if not self._ready() or (not force and (self.principal_amount or self.interest_amount)):
            return
        principal, interest = self._expected()
        self.principal_amount, self.interest_amount = float(principal), float(interest)

    def _expected(self):
        """Očekávaná splátka: nejbližší tok kalendáře, jehož jistina ještě není splacená; po mimořádné splátce
        s poměrným snížením toky sníží koeficient. Předčasné ukončení: celá zbývající jistina."""
        remaining = self._position_principal() - self._other_repaid()
        schedule = self._schedule()
        if self.kind == "early_termination" or not schedule:
            return max(remaining, engine.ZERO), engine.ZERO
        factor = self._prorata_factor(self.fund_id._origin, self.instrument_id._origin, self.portfolio_id._origin, self.date)
        position, due = self._position_principal(), engine.ZERO
        for day, (principal, interest) in schedule.items():
            due += principal
            payable = remaining - engine.money((position - due) * factor)
            if payable > 0:
                return engine.money(payable), engine.money(interest * factor)
        return max(remaining, engine.ZERO), engine.ZERO

    @api.onchange("kind")
    def _onchange_kind(self):
        """Předčasné ukončení předvyplní celou zbývající jistinu; úrok a poplatek zadá uživatel podle výplaty."""
        if self.state == "draft" and self._ready() and self.kind == "early_termination":
            self.principal_amount = float(max(self._position_principal() - self._other_repaid(), engine.ZERO))

    # --- kontroly --------------------------------------------------------------------------------

    @api.constrains("principal_amount", "interest_amount", "fee_amount", "kind", "instrument_id", "portfolio_id", "fund_id", "date")
    def _check_repayment(self):
        for repayment in self:
            repayment._validate()

    def _validate(self):
        self.ensure_one()
        principal, interest = engine.money(engine.dec(self.principal_amount)), engine.money(engine.dec(self.interest_amount))
        fee = engine.money(engine.dec(self.fee_amount))
        if principal < 0 or interest < 0 or fee < 0 or not principal + interest:
            raise ValidationError(self.env._("Jistina, úrok a poplatek nesmí být záporné a splátka musí mít jistinu nebo úrok."))
        if fee > principal + interest:
            raise ValidationError(self.env._("Poplatek nesmí být vyšší než jistina a úrok."))
        if self.portfolio_id.fund_id != self.fund_id:
            raise ValidationError(self.env._("Obchodní model nepatří fondu splátky."))
        if not self._classification():
            raise ValidationError(self.env._(
                "Nástroj %(name)s nemá v modelu %(portfolio)s k %(day)s zařazení.",
                name=self.instrument_id.name, portfolio=self.portfolio_id.name, day=self.date,
            ))
        if self.state == "reversed":
            return
        remaining = self._position_principal() - self._other_repaid()
        if remaining <= 0:
            raise ValidationError(self.env._(
                "Fond k %(day)s nedrží nástroj %(name)s v modelu %(portfolio)s.",
                day=self.date, name=self.instrument_id.name, portfolio=self.portfolio_id.name,
            ))
        if principal > remaining:
            raise ValidationError(self.env._(
                "Jistina %(principal)s je vyšší než zbývající jistina %(remaining)s.", principal=principal, remaining=remaining,
            ))
        if self.kind == "scheduled" and self._classification().valuation_method == "amortised":
            # Po splátce musí zůstat aspoň kalendářem ještě nesplatná jistina, snížená mimořádnými splátkami (koeficient).
            due = sum((p for day, (p, _i) in self._schedule().items() if day <= self.date), engine.ZERO)
            factor = self._prorata_factor(self.fund_id._origin, self.instrument_id._origin, self.portfolio_id._origin, self.date)
            not_due = engine.money((self._position_principal() - due) * factor)
            if remaining - principal < not_due:
                due = remaining - not_due
                raise ValidationError(self.env._(
                    "Podle kalendáře je do %(day)s splatná jistina %(due)s. Vyšší splátku zadejte jako mimořádnou "
                    "(poměrné snížení) nebo předčasné ukončení.", day=self.date, due=engine.money(due),
                ))

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
            # Mezitím mohla být zaúčtována jiná splátka téže pozice; kontrola znovu.
            repayment._validate()
            instrument = repayment.instrument_id
            company = repayment.company_id
            classification = repayment._classification()
            foreign = instrument.currency_id != company.currency_id
            round_ = company.currency_id.round
            principal = round_(repayment.principal_amount * repayment.fx_rate)
            interest = round_((repayment.principal_amount + repayment.interest_amount) * repayment.fx_rate) - principal
            fee = round_(repayment.fee_amount * repayment.fx_rate)
            extra = {"investra_instrument_id": instrument.id, "investra_classification_id": classification.id}

            def currency(amount_ccy):
                return {"currency_id": instrument.currency_id.id, "amount_currency": amount_ccy} if foreign else {}

            lines = [{"role": "cash_in_transit_receipt", "amount": principal + interest - fee, "movement_type": "transaction",
                      **currency(repayment.amount)}]
            if fee:
                # Poplatek strhnutý protistranou je náklad na bankovní poplatky (rozhodnutí 2026-11-12).
                lines.append({"role": "expense_bank_fee", "amount": fee, "movement_type": "fee",
                              "name": self.env._("Poplatek %s", instrument.name), **currency(repayment.fee_amount)})
            for amount, amount_ccy, label in (
                (principal, repayment.principal_amount, self.env._("Jistina")),
                (interest, repayment.interest_amount, self.env._("Úrok")),
            ):
                if amount or amount_ccy:
                    lines.append({"role": classification.role_id.code, "amount": -amount, "movement_type": "transaction",
                                  "name": f"{label} {instrument.name}", "extra": extra, **currency(-amount_ccy)})
            event = self.env["investra.accounting.event"]._create_event(
                company, f"repayment:{repayment.id}", f"Splátka {instrument.name}", repayment.date, "repayment",
                lines, source=repayment,
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


class InvestraTrade(models.Model):
    _inherit = "investra.trade"

    @api.model
    def _holdings(self, fund, day):
        """Kusy pozic po zaúčtovaných splátkách jistiny: splátka sníží kusy o jistinu / jistinu na jednotku
        (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“)."""
        quantities = super()._holdings(fund, day)
        repayments = self.env["investra.instrument.repayment"].sudo().search([
            ("fund_id", "=", fund.id), ("state", "=", "posted"), ("date", "<=", day),
        ])
        if not repayments:
            return quantities
        repaid, closed = {}, set()
        for repayment in repayments:
            key = (repayment.instrument_id, repayment.portfolio_id)
            repaid[key] = repaid.get(key, engine.ZERO) + engine.dec(repayment.principal_amount)
            if repayment.kind == "early_termination":
                closed.add(key)
        result = dict(quantities)
        for key, principal in repaid.items():
            if key not in result:
                continue
            if key in closed:
                # Předčasné ukončení uzavře pozici bez ohledu na zadanou jistinu (diskont, krácený úrok).
                del result[key]
                continue
            ppu = engine.dec(key[0]._principal_per_unit())
            remaining = engine.money(engine.dec(result[key]) * ppu - principal)
            if remaining > 0:
                result[key] = float(remaining / ppu)
            else:
                del result[key]
        return result
