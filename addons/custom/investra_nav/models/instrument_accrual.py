import logging
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import engine

COUPON_MONTHS = {"maturity": 0, "annual": 12, "semiannual": 6, "quarterly": 3, "monthly": 1}
# Částka toku je na jednotku (u jistiny na jednotku 1 i zlomky haléře), proto 8 desetinných míst jako pole toku.
UNIT_AMOUNT = Decimal("0.00000001")

_logger = logging.getLogger(__name__)


class InvestraInstrument(models.Model):
    _inherit = "investra.instrument"

    principal = fields.Float(
        digits=(20, 2), string="Jistina na jednotku",
        help="Pro kalendář vkladu a pro splátky bez kalendáře. Doporučeno 1: kusy obchodu = jistina, cena na jednotku jistiny.",
    )
    start_date = fields.Date(string="Začátek úročení")
    coupon_frequency = fields.Selection(
        [("maturity", "Ve splatnosti"), ("annual", "Ročně"), ("semiannual", "Pololetně"), ("quarterly", "Čtvrtletně"),
         ("monthly", "Měsíčně")], default="maturity", string="Výplata úroku",
        help="Pro generátor kalendáře: kupónová data se odpočítají od splatnosti, kratší první období je na začátku.",
    )

    @api.constrains("start_date", "maturity_date")
    def _check_cashflow_dates(self):
        """Tok kalendáře musí být po začátku úročení a nejpozději v den splatnosti (2026-11-12, zkouška v UI)."""
        for instrument in self:
            for flow in instrument.cashflow_ids:
                if instrument.start_date and flow.date <= instrument.start_date:
                    raise ValidationError(self.env._(
                        "Tok kalendáře %(day)s není po začátku úročení %(start)s: %(name)s.",
                        day=flow.date, start=instrument.start_date, name=instrument.name,
                    ))
                if instrument.maturity_date and flow.date > instrument.maturity_date:
                    raise ValidationError(self.env._(
                        "Tok kalendáře %(day)s je po splatnosti %(end)s: %(name)s.",
                        day=flow.date, end=instrument.maturity_date, name=instrument.name,
                    ))

    def action_generate_schedule(self):
        """Kalendář z jistiny na jednotku, sazby, výplaty úroku, konvence dnů, začátku úročení a splatnosti.

        Kupónová data se odpočítávají od splatnosti (kratší první období je na začátku); kupón = jistina × sazba × část
        roku podle konvence dnů; ve splatnosti poslední kupón a jistina (rozhodnutí 2026-11-12 „Generátor kupónového
        kalendáře“). Výplata Ve splatnosti dává vklad s jednou splátkou jako dosud.
        """
        for instrument in self:
            if not (instrument.principal and instrument.start_date and instrument.maturity_date):
                raise UserError(self.env._("Vyplňte jistinu, začátek a splatnost: %s.", instrument.name))
            if instrument.maturity_date <= instrument.start_date:
                raise UserError(self.env._("Splatnost musí být po začátku úročení: %s.", instrument.name))
            # Stornovaná splátka kalendář neblokuje (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
            if self.env["investra.instrument.repayment"].sudo().search_count(
                [("instrument_id", "=", instrument.id), ("state", "!=", "reversed")], limit=1
            ):
                raise UserError(self.env._("Kalendář po splacení nejde měnit: %s.", instrument.name))
            principal = engine.dec(instrument.principal)
            rate = engine.dec(instrument.coupon_rate) / 100
            basis = instrument.day_count or "act365"
            months = COUPON_MONTHS[instrument.coupon_frequency or "maturity"]
            days = [instrument.maturity_date]
            if months:
                step = 1
                while (day := instrument.maturity_date - relativedelta(months=months * step)) > instrument.start_date:
                    days.append(day)
                    step += 1
            days.sort()
            commands, start = [(5,)], instrument.start_date
            for day in days:
                interest = (principal * rate * engine.year_fraction(start, day, basis)).quantize(UNIT_AMOUNT, rounding=ROUND_HALF_UP)
                if interest:
                    commands.append((0, 0, {"date": day, "amount": float(interest), "flow_type": "interest"}))
                start = day
            commands.append((0, 0, {"date": instrument.maturity_date, "amount": float(principal), "flow_type": "principal"}))
            instrument.cashflow_ids = commands
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
        domain = [("fund_id", "=", fund.id), ("instrument_id", "=", self.id), ("trade_date", "<=", day), ("state", "!=", "reversed")]
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
            # Dluhopis koupený s naběhlým kupónem: zaplacený úrok je součástí pořizovací částky (rozhodnutí 2026-11-12
            # „Úrok v RH a realizovaný výsledek“).
            cost = quantity * engine.dec(trade.price) + engine.dec(trade._signed_accrued_interest()) * factor
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


    # --- úrok u nástrojů v reálné hodnotě (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“) -----------

    def _coupon_periods(self):
        """Kupónová období [(začátek, konec, úrok na jednotku)] z toků Úrok kalendáře.

        První období začíná Začátkem úročení, bez něj prvním obchodem s nástrojem (pak se úrok za dny před ním
        nepočítá ani do naběhlého úroku obchodu).
        """
        self.ensure_one()
        amounts = {}
        for flow in self.cashflow_ids.filtered(lambda f: f.flow_type == "interest"):
            amounts[flow.date] = amounts.get(flow.date, engine.ZERO) + engine.dec(flow.amount)
        if not amounts:
            return []
        start = self.start_date or self.env["investra.trade"].sudo().search(
            [("instrument_id", "=", self.id), ("state", "!=", "reversed")], order="trade_date", limit=1).trade_date or min(amounts)
        periods = []
        for end in sorted(amounts):
            if end > start:
                periods.append((start, end, amounts[end]))
                start = end
        return periods

    def _earned_coupon_unit(self, periods, day, factor_at=None):
        """Úrok na jednotku vydělaný do data lineárně podle konvence dnů (kupón splatný v den toku je celý vydělaný).
        factor_at(datum) sníží období koeficientem mimořádných splátek k jeho konci, nejpozději k datu."""
        basis = self.day_count or "act365"
        total = engine.ZERO
        for start, end, amount in periods:
            if day <= start:
                break
            share = engine.dec(1) if day >= end else engine.year_fraction(start, day, basis) / engine.year_fraction(start, end, basis)
            total += amount * share * (factor_at(min(day, end)) if factor_at else 1)
        return total

    def _accrued_coupon_unit(self, day):
        """Naběhlý kupón na jednotku k datu podle smlouvy (běžné období); předvyplnění u obchodu s dluhopisem."""
        self.ensure_one()
        periods = self._coupon_periods()
        current = [(s, e, a) for s, e, a in periods if s < day < e]
        if not current:
            return engine.ZERO
        start = current[0][0]
        return self._earned_coupon_unit(current, day) if start < day else engine.ZERO

    def _fair_value_interest(self, fund, portfolio, day):
        """Úrok pozice v RH k datu v měně nástroje: (vydělaný úrok od pořízení, naběhlý úrok v hodnotě pozice).

        Kupónové nástroje lineárně podle smlouvy, bezkupónové (jen toky Jistina) diskont efektivní úrokovou mírou.
        Naběhlý úrok = vydělaný úrok + úrok zaplacený u nákupů − přijatý u prodejů − úrok ze splátek.
        Nástroj bez kalendáře vrátí None (akcie, podíly). Jen výpočet: nic se neúčtuje.
        """
        self.ensure_one()
        trades = self.env["investra.trade"].sudo()._recognised(fund, day, self, portfolio)
        if not trades or not self.cashflow_ids:
            return None
        periods = self._coupon_periods()
        earned = engine.ZERO
        if periods:
            Repayment = self.env["investra.instrument.repayment"].sudo()
            factors = {}

            def factor_at(when):
                if when not in factors:
                    factors[when] = Repayment._prorata_factor(fund, self, portfolio, when)
                return factors[when]

            at_day = self._earned_coupon_unit(periods, day, factor_at)
            for trade in trades:
                earned += engine.dec(trade.quantity) * (at_day - self._earned_coupon_unit(periods, trade.trade_date, factor_at))
        else:
            if any(trade.quantity < 0 for trade in trades):
                raise UserError(self.env._("Prodej bezkupónového nástroje v reálné hodnotě zatím není podporovaný: %s.", self.name))
            basis = self.day_count or "act365"
            for trade in trades:
                quantity = engine.dec(trade.quantity)
                cost = quantity * engine.dec(trade.price)
                flows = [(f.date, engine.dec(f.amount) * quantity) for f in self.cashflow_ids.filtered(lambda f: f.date > trade.trade_date)]
                if not flows:
                    continue
                paid = sum((a for d, a in flows if d <= day), engine.ZERO)
                earned += engine.amortised_cost([(trade.trade_date, -cost), *flows], day, basis=basis) + paid - cost
        bought = sum((engine.dec(t._signed_accrued_interest()) for t in trades), engine.ZERO)
        received = sum((engine.dec(r.interest_amount) for r in self.env["investra.instrument.repayment"].sudo().search([
            ("fund_id", "=", fund.id), ("instrument_id", "=", self.id), ("portfolio_id", "=", portfolio.id),
            ("state", "=", "posted"), ("date", "<=", day),
        ])), engine.ZERO)
        earned = engine.money(earned)
        return earned, engine.money(earned + bought - received)


class InvestraInstrumentCashflow(models.Model):
    _inherit = "investra.instrument.cashflow"

    @api.constrains("date", "instrument_id")
    def _check_date(self):
        self.instrument_id._check_cashflow_dates()


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
        [("scheduled", "Podle kalendáře"), ("extraordinary", "Mimořádná")],
        required=True, default="scheduled", string="Druh",
        help="Mimořádná splátka úměrně sníží zbylé toky kalendáře, nebo s volbou Uzavírá pozici ukončí celou pozici "
             "(rozhodnutí 2026-11-12 „Mimořádná splátka nástroje“).",
    )
    closes_position = fields.Boolean(
        string="Uzavírá pozici",
        help="Zaškrtne se samo, když jistina pokryje zbývající jistinu. Ručně jen když protistrana zaplatí méně a pozice "
             "přesto končí (diskont, vyrovnání): zbytek pak ocenění odúčtuje do výsledku.",
    )
    write_off_amount = fields.Float(
        compute="_compute_remaining", digits=(20, 2), string="Neuhrazená jistina",
        help="Zbývající jistina, kterou splátka s volbou Uzavírá pozici nepokryje; ocenění ji odúčtuje do výsledku.",
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
            if repayment.kind == "extraordinary" and not repayment.closes_position:
                before = repayment._position_principal() - repaid
                if before > 0:
                    factor *= (before - principal) / before
            repaid += principal
        return factor

    # --- návrhy splátek podle kalendáře (rozhodnutí 2026-11-12 „Návrhy kalendářních splátek“) -------------

    @api.model
    def _missing_scheduled(self, fund, day, posted_only=False):
        """Toky kalendáře splatné do data bez splátky: [(nástroj, model, datum toku, jistina, úrok)].

        Tok je pokrytý, když má pozice nestornovanou splátku (s posted_only jen zaúčtovanou) k datu toku nebo pozdější.
        Jistina a úrok jsou snížené koeficientem mimořádných splátek; pozice bez kusů se přeskočí.
        """
        states = ("posted",) if posted_only else ("draft", "posted")
        missing = []
        for instrument, portfolio in self.env["investra.trade"].sudo()._holdings(fund, day):
            flow_days = sorted(set(instrument.cashflow_ids.filtered(lambda f: f.date <= day).mapped("date")))
            if not flow_days:
                continue
            latest = self.sudo().search([
                ("fund_id", "=", fund.id), ("instrument_id", "=", instrument.id), ("portfolio_id", "=", portfolio.id),
                ("state", "in", states),
            ], order="date desc", limit=1).date
            for flow_day in flow_days:
                if latest and latest >= flow_day:
                    continue
                probe = self.new({"fund_id": fund.id, "instrument_id": instrument.id, "portfolio_id": portfolio.id,
                                  "date": flow_day, "kind": "scheduled"})
                schedule = probe._schedule()
                if flow_day not in schedule:
                    continue
                factor = self._prorata_factor(fund, instrument, portfolio, flow_day)
                position = probe._position_principal()
                due = sum((p for d, (p, _i) in schedule.items() if d <= flow_day), engine.ZERO)
                principal = position - probe._other_repaid() - engine.money((position - due) * factor)
                interest = engine.money(schedule[flow_day][1] * factor)
                if principal > 0 or interest > 0:
                    missing.append((instrument, portfolio, flow_day, max(principal, engine.ZERO), interest))
        return missing

    @api.model
    def _create_scheduled_drafts(self, funds, day):
        """Založí návrhy splátek pro splatné toky kalendáře; tok v zamčeném ocenění se přeskočí a zapíše do logu."""
        created = self.browse()
        for fund in funds:
            for instrument, portfolio, flow_day, principal, interest in self._missing_scheduled(fund, day):
                try:
                    with self.env.cr.savepoint():
                        created |= self.with_company(fund.company_id).create({
                            "fund_id": fund.id, "instrument_id": instrument.id, "portfolio_id": portfolio.id,
                            "date": flow_day, "kind": "scheduled",
                            "principal_amount": float(principal), "interest_amount": float(interest),
                        })
                except (UserError, ValidationError) as error:
                    _logger.warning("Návrh splátky %s k %s ve fondu %s nevznikl: %s", instrument.name, flow_day, fund.name, error)
        return created

    @api.model
    def _cron_create_scheduled_drafts(self):
        """Denní úloha: návrhy splátek podle kalendáře do dnešního data ve všech fondech; nic se neúčtuje."""
        funds = self.env["investra.fund"].sudo().search([])
        self.sudo()._create_scheduled_drafts(funds, fields.Date.context_today(self))

    def action_create_scheduled_drafts(self):
        """Tlačítko v seznamu: otevře okno s datem „Návrhy do“ (rozhodnutí 2026-11-12 „Návrhy splátek předem“)."""
        self._check_drafts_access()
        return {
            "type": "ir.actions.act_window", "name": self.env._("Návrhy podle kalendáře"),
            "res_model": "investra.instrument.repayment.drafts.wizard", "view_mode": "form", "target": "new",
        }

    @api.model
    def _check_drafts_access(self):
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))

    @api.model
    def _create_drafts_until(self, day):
        """Návrhy do zvoleného data pro fondy vybraných společností; totéž co denní úloha, jen ručně a případně předem."""
        self._check_drafts_access()
        funds = self.env["investra.fund"].search([("company_id", "in", self.env.companies.ids)])
        created = self._create_scheduled_drafts(funds, day)
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {
                "type": "success" if created else "info", "sticky": False,
                "message": self.env._("Vytvořeno návrhů splátek: %s", len(created)),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

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

    @api.depends("fund_id", "date", "instrument_id", "portfolio_id", "principal_amount", "kind", "closes_position")
    def _compute_remaining(self):
        for repayment in self:
            repayment.write_off_amount = 0.0
            if not repayment._ready():
                repayment.remaining_before = repayment.remaining_after = 0.0
                continue
            before = repayment._position_principal() - repayment._other_repaid()
            repayment.remaining_before = float(before)
            after = before - engine.money(engine.dec(repayment.principal_amount))
            if repayment.closes_position:
                repayment.remaining_after = 0.0
                repayment.write_off_amount = float(max(after, engine.ZERO))
            else:
                repayment.remaining_after = float(after)

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
        if self.kind == "extraordinary" or not schedule:
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
        """Mimořádná splátka předvyplní celou zbývající jistinu (pozice se uzavře); nižší jistina = poměrné snížení."""
        if self.state != "draft":
            return
        if self.kind == "scheduled":
            self.closes_position = False
        elif self._ready():
            self.principal_amount = float(max(self._position_principal() - self._other_repaid(), engine.ZERO))
            self._onchange_principal()

    @api.onchange("principal_amount")
    def _onchange_principal(self):
        """Uzavírá pozici: zaškrtne se, když jistina pokryje zbývající jistinu; při nižší jistině se zruší
        (ručně ho lze zaškrtnout znovu)."""
        if self.state == "draft" and self.kind == "extraordinary" and self._ready():
            remaining = self._position_principal() - self._other_repaid()
            self.closes_position = engine.money(engine.dec(self.principal_amount)) >= remaining

    # --- kontroly --------------------------------------------------------------------------------

    @api.constrains("principal_amount", "interest_amount", "fee_amount", "kind", "closes_position", "instrument_id",
                    "portfolio_id", "fund_id", "date")
    def _check_repayment(self):
        for repayment in self:
            repayment._validate()

    def _validate(self):
        self.ensure_one()
        principal, interest = engine.money(engine.dec(self.principal_amount)), engine.money(engine.dec(self.interest_amount))
        fee = engine.money(engine.dec(self.fee_amount))
        if principal < 0 or interest < 0 or fee < 0 or not principal + interest:
            raise ValidationError(self.env._("Jistina, úrok a poplatek nesmí být záporné a splátka musí mít jistinu nebo úrok."))
        if self.closes_position and self.kind != "extraordinary":
            raise ValidationError(self.env._("Uzavřít pozici lze jen mimořádnou splátkou."))
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


class InvestraInstrumentRepaymentDraftsWizard(models.TransientModel):
    """Okno tlačítka Návrhy podle kalendáře: návrhy do zvoleného data, i předem; nic se neúčtuje.

    Denní úloha dál zakládá jen toky splatné do dneška (rozhodnutí 2026-11-12 „Návrhy splátek předem“).
    """

    _name = "investra.instrument.repayment.drafts.wizard"
    _description = "Návrhy splátek podle kalendáře"

    date_to = fields.Date(
        required=True, default=fields.Date.context_today, string="Návrhy do",
        help="Založí návrhy pro toky kalendáře splatné do tohoto data včetně. Částky jsou podle stavu pozice dnes; "
             "když do data toku přijde mimořádná splátka, návrh před zaúčtováním upravte.",
    )

    def action_confirm(self):
        self.ensure_one()
        return self.env["investra.instrument.repayment"]._create_drafts_until(self.date_to)


class InvestraTrade(models.Model):
    _inherit = "investra.trade"

    def _calendar_accrued_interest(self):
        """Naběhlý kupón dluhopisu k datu sjednání podle kalendáře: kusy × úrok na jednotku (nákup i prodej)."""
        self.ensure_one()
        unit = self.instrument_id._origin._accrued_coupon_unit(self.trade_date)
        return float(engine.money(abs(engine.dec(self.units or self.quantity)) * unit))

    @api.onchange("instrument_id", "trade_date", "quantity", "units", "side")
    def _onchange_accrued_interest(self):
        """Dluhopis: naběhlý kupón se předvyplní z kalendáře; jde přepsat."""
        for trade in self:
            if trade.event_id or trade.instrument_id.type_id.kind != "bond" or not trade.trade_date:
                continue
            trade.accrued_interest = trade._calendar_accrued_interest()

    @api.model_create_multi
    def create(self, vals_list):
        """Obchod s dluhopisem bez zadaného naběhlého úroku (import, API) dostane úrok z kalendáře."""
        trades = super().create(vals_list)
        for trade, vals in zip(trades, vals_list):
            if "accrued_interest" not in vals and trade.instrument_id.type_id.kind == "bond" and not trade.event_id:
                interest = trade._calendar_accrued_interest()
                if interest:
                    trade.accrued_interest = interest
        return trades

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
            if repayment.closes_position:
                closed.add(key)
        result = dict(quantities)
        for key, principal in repaid.items():
            if key not in result:
                continue
            if key in closed:
                # Mimořádná splátka s volbou Uzavírá pozici ukončí pozici bez ohledu na jistinu (diskont, vyrovnání).
                del result[key]
                continue
            ppu = engine.dec(key[0]._principal_per_unit())
            remaining = engine.money(engine.dec(result[key]) * ppu - principal)
            if remaining > 0:
                result[key] = float(remaining / ppu)
            else:
                del result[key]
        return result
