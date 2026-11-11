from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


IFRS9_CATEGORY = [("fvtpl", "Reálná hodnota do výsledku"), ("fvoci", "Reálná hodnota do OCI"), ("amortised", "Naběhlá hodnota")]
VALUATION_METHOD = [
    ("price", "Cena × kusy"), ("amortised", "Naběhlá hodnota"), ("model", "Model nebo znalec"), ("contract", "Reálná hodnota podle smlouvy"),
    ("position", "Zadaná hodnota pozice"),
]
DAY_COUNT = [
    ("act365", "ACT/365"), ("act360", "ACT/360"), ("act_act", "ACT/ACT ISDA"), ("thirty360_eu", "30E/360"), ("thirty360_us", "30/360 US"),
]
# Po prvním obchodu neměnná pole, na kterých stojí zaúčtované hodnoty.
LOCKED_AFTER_TRADE = {"type_id", "role_id", "ifrs9_category", "valuation_method"}
SYSTEM_TRADE_FIELDS = {"state", "event_id", "settlement_event_id"}
BOOKED_TRADE_FIELDS = {"fund_id", "instrument_id", "trade_date", "quantity", "price", "fx_rate"}
SYSTEM_PRICE_FIELDS = {"state", "approved_by", "entered_by"}
# Kdo změní některé z těchto polí návrhu, stává se zadavatelem ceny.
PRICE_INPUT_FIELDS = {"instrument_id", "fund_id", "date", "price", "currency_id", "source", "deviation_reason"}


class InvestraInstrumentType(models.Model):
    """Typ nástroje: nabízí výchozí hodnoty. Rozhoduje hodnota na nástroji, kterou může účetní změnit."""

    _name = "investra.instrument.type"
    _description = "Typ nástroje"
    _order = "group, name"

    code = fields.Char(required=True, string="Kód")
    name = fields.Char(required=True, string="Název")
    active = fields.Boolean(default=True, string="Aktivní")
    group = fields.Selection(
        [("listed", "Kótované"), ("debt", "Dluhové"), ("money_market", "Peněžní trh"), ("loan", "Úvěry a účasti"), ("derivative", "Deriváty"),
         ("other_holding", "Ostatní podíly")],
        required=True,
        string="Skupina",
    )
    kind = fields.Selection(
        [("equity", "Akcie"), ("bond", "Dluhopis"), ("fund", "Fond"), ("participation", "Účast"), ("loan", "Úvěr"),
         ("derivative", "Derivát"), ("deposit", "Termínovaný vklad"), ("repo", "Repo"), ("other_holding", "Ostatní podíl")],
        required=True,
        string="Druh v portfoliu",
    )
    ifrs9_category = fields.Selection(IFRS9_CATEGORY, required=True, string="Navržená kategorie IFRS 9")
    valuation_method = fields.Selection(VALUATION_METHOD, required=True, string="Navržený způsob ocenění")
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Navržená role účtu")
    cnb_sheet = fields.Char(string="Navržený list ČNB")
    max_price_age = fields.Integer(
        string="Navržené maximální stáří ceny (dny)",
        help="Návrh pro nové nástroje tohoto typu. 0 = ocenění upozorní na každou cenu starší než datum ocenění.",
    )

    _code_uniq = models.Constraint("unique(code)", "Kód typu nástroje musí být jedinečný.")


class InvestraInstrument(models.Model):
    _name = "investra.instrument"
    _inherit = ["mail.thread"]
    _description = "Nástroj"
    _order = "name"

    name = fields.Char(required=True, string="Název")
    isin = fields.Char(string="ISIN")
    currency_id = fields.Many2one("res.currency", required=True, string="Měna")
    type_id = fields.Many2one("investra.instrument.type", required=True, ondelete="restrict", string="Typ", tracking=True)
    type_group = fields.Selection(related="type_id.group", string="Skupina")
    ifrs9_category = fields.Selection(IFRS9_CATEGORY, required=True, string="Kategorie IFRS 9", tracking=True)
    valuation_method = fields.Selection(VALUATION_METHOD, required=True, string="Způsob ocenění", tracking=True)
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Role účtu", tracking=True)
    cnb_sheet = fields.Char(string="List ČNB", tracking=True)
    max_price_age = fields.Integer(
        string="Maximální stáří ceny (dny)", tracking=True,
        help="Ocenění vezme poslední známou schválenou cenu; je-li starší o víc dní, ocenění upozorní (nezastaví). "
             "0 = upozornit na každou cenu starší než datum ocenění.",
    )
    deviates_from_type = fields.Boolean(compute="_compute_deviates", string="Odchylka od návrhu typu")
    fair_value_level = fields.Selection([("1", "Úroveň 1"), ("2", "Úroveň 2"), ("3", "Úroveň 3")], string="Úroveň RH")
    market = fields.Char(string="Trh")
    counterparty_id = fields.Many2one("res.partner", string="Protistrana", ondelete="restrict")
    collateral = fields.Char(string="Kolaterál")
    maturity_date = fields.Date(string="Splatnost")
    coupon_rate = fields.Float(digits=(16, 6), string="Sazba %")
    day_count = fields.Selection(DAY_COUNT, default="act365", string="Konvence dnů")
    commitment_amount = fields.Float(digits=(20, 2), string="Upisovací závazek", help="Celková částka v měně nástroje, 0 = bez závazku.")
    holding_kind = fields.Selection([("securities", "Cenné papíry"), ("shares", "Podíly")], string="Typ investice", tracking=True)
    fund_id = fields.Many2one("investra.fund", ondelete="restrict", string="Fond", help="Vyplněno: nástroj patří jen tomuto fondu.")
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict", string="Třída", domain="[('fund_id', '=', fund_id)]")
    order_ref = fields.Char(string="Zakázka")
    accrual_method = fields.Selection(
        [("fund", "Podle fondu"), ("eir", "Efektivní úroková míra"), ("linear", "Lineárně")],
        required=True,
        default="fund",
        string="Úročení",
        tracking=True,
    )
    accrual_note = fields.Char(string="Zdůvodnění lineárního úročení")
    cashflow_ids = fields.One2many("investra.instrument.cashflow", "instrument_id", string="Smluvní peněžní toky")

    def _type_proposal(self, kind):
        return {
            "ifrs9_category": kind.ifrs9_category, "valuation_method": kind.valuation_method,
            "role_id": kind.role_id.id, "cnb_sheet": kind.cnb_sheet, "max_price_age": kind.max_price_age,
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            kind = self.env["investra.instrument.type"].browse(vals.get("type_id"))
            for field, value in self._type_proposal(kind).items():
                vals.setdefault(field, value)
        return super().create(vals_list)

    @api.onchange("type_id")
    def _onchange_type_id(self):
        if self.type_id:
            self.update(self._type_proposal(self.type_id))

    @api.depends("type_id", "ifrs9_category", "valuation_method", "role_id", "cnb_sheet")
    def _compute_deviates(self):
        for instrument in self:
            kind = instrument.type_id
            instrument.deviates_from_type = bool(kind) and (
                (instrument.ifrs9_category, instrument.valuation_method, instrument.role_id, instrument.cnb_sheet or False)
                != (kind.ifrs9_category, kind.valuation_method, kind.role_id, kind.cnb_sheet or False)
            )

    @api.constrains("ifrs9_category", "valuation_method")
    def _check_valuation_method(self):
        for instrument in self:
            if (instrument.ifrs9_category == "amortised") != (instrument.valuation_method == "amortised"):
                raise ValidationError(self.env._("Naběhlou hodnotou se oceňuje právě kategorie Naběhlá hodnota: %s.", instrument.name))

    @api.constrains("type_id", "fund_id", "class_id", "holding_kind", "commitment_amount")
    def _check_other_holding(self):
        for instrument in self:
            if instrument.commitment_amount < 0:
                raise ValidationError(self.env._("Upisovací závazek nemůže být záporný: %s.", instrument.name))
            if instrument.class_id and instrument.class_id.fund_id != instrument.fund_id:
                raise ValidationError(self.env._("Třída nepatří do fondu nástroje: %s.", instrument.name))
            if instrument.type_group == "other_holding" and not (instrument.fund_id and instrument.holding_kind):
                raise ValidationError(self.env._("Ostatní podíl musí mít fond a typ investice: %s.", instrument.name))

    @api.constrains("accrual_method", "accrual_note")
    def _check_accrual_note(self):
        for instrument in self:
            if instrument.accrual_method == "linear" and not instrument.accrual_note:
                raise ValidationError(self.env._("Lineární úročení musí mít zdůvodnění: %s.", instrument.name))

    def write(self, vals):
        if not self.env.su and LOCKED_AFTER_TRADE & set(vals):
            if self.env["investra.trade"].sudo().search_count([("instrument_id", "in", self.ids)], limit=1):
                raise UserError(self.env._("Po prvním obchodu nejde měnit typ, klasifikaci, způsob ocenění ani roli účtu."))
        return super().write(vals)

    def _effective_accrual(self, fund):
        """Metoda úročení pro fond; volba na nástroji má přednost před fondem."""
        self.ensure_one()
        return fund.accrual_method if self.accrual_method == "fund" else self.accrual_method


class InvestraInstrumentCashflow(models.Model):
    """Smluvní tok na jednotku nástroje, bez pořízení; to se bere z obchodu."""

    _name = "investra.instrument.cashflow"
    _description = "Smluvní peněžní tok nástroje"
    _order = "date, id"

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="cascade", index=True, string="Nástroj")
    date = fields.Date(required=True, string="Datum")
    amount = fields.Float(required=True, digits=(20, 8), string="Částka na jednotku")
    flow_type = fields.Selection([("interest", "Úrok"), ("principal", "Jistina")], required=True, default="principal", string="Druh")


class InvestraInstrumentPrice(models.Model):
    """Cena k datu v jednotkách měny nástroje za kus. Do ocenění vstupuje jen schválená.

    Cena bez fondu je sdílená tržní cena (vede ji kniha investiční společnosti, platí pro všechny fondy);
    cena s fondem je cena fondu (posudek, odchylka). Opravená schválená cena se vrací ke schválení.
    """

    _name = "investra.instrument.price"
    _inherit = ["investra.record.guard", "mail.thread"]
    _description = "Cena nástroje"
    _order = "date desc"
    _book_fields = ("fund_id", "company_id")
    _system_fields = SYSTEM_PRICE_FIELDS

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", index=True, string="Nástroj")
    fund_id = fields.Many2one(
        "investra.fund", ondelete="restrict", index=True, string="Fond",
        help="Prázdné = sdílená tržní cena pro všechny fondy. Vyplněné = cena jen pro tento fond (posudek, odchylka).",
    )
    scope = fields.Selection(
        [("shared", "Sdílená"), ("fund", "Fond")], compute="_compute_scope", store=True, precompute=True, string="Rozsah",
    )
    # Kniha ceny: u ceny fondu společnost fondu, u sdílené ceny kniha investiční společnosti; nastaví se při založení.
    company_id = fields.Many2one("res.company", required=True, readonly=True, index=True, string="Kniha")
    date = fields.Date(required=True, string="Datum", tracking=True)
    price = fields.Float(required=True, digits=(20, 8), string="Cena", tracking=True, help="V jednotkách měny ceny za kus.")
    currency_id = fields.Many2one(
        "res.currency", compute="_compute_currency_id", store=True, precompute=True, readonly=False, required=True, string="Měna",
        tracking=True, help="Musí se rovnat měně nástroje.",
    )
    source = fields.Char(required=True, string="Zdroj", tracking=True)
    deviation_reason = fields.Char(
        string="Důvod odchylky", tracking=True,
        help="Povinné u ceny fondu, když ke stejnému dni existuje sdílená tržní cena.",
    )
    state = fields.Selection(
        [("draft", "Návrh"), ("approved", "Schváleno")], default="draft", required=True, readonly=True, string="Stav",
        tracking=True,
    )
    entered_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True, string="Zadal")
    approved_by = fields.Many2one("res.users", readonly=True, string="Schválil")

    _uniq = models.Constraint("unique(fund_id, instrument_id, date)", "Cena nástroje k datu už existuje.")
    # NULL se v PostgreSQL nerovná NULL, proto sdílené ceny potřebují vlastní index.
    _shared_uniq = models.UniqueIndex(
        "(instrument_id, date) WHERE fund_id IS NULL", "Sdílená cena nástroje k datu už existuje.",
    )

    @api.depends("fund_id")
    def _compute_scope(self):
        for price in self:
            price.scope = "fund" if price.fund_id else "shared"

    @api.depends("instrument_id")
    def _compute_currency_id(self):
        for price in self:
            price.currency_id = price.instrument_id.currency_id

    @api.model
    def _shared_price_company(self):
        """Sdílené ceny vede kniha investiční společnosti (rozhodnutí 2026-11-11)."""
        books = self.env["investra.entity"].sudo().search([("entity_type", "=", "manager")])
        if len(books) != 1:
            raise UserError(self.env._(
                "Sdílené tržní ceny vede kniha investiční společnosti, která zatím není založená (nebo jich je víc). "
                "Zadejte cenu fondu."
            ))
        return books.company_id

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_PRICE_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Cenu schvaluje jen schvalovací krok."))
        for vals in vals_list:
            fund = self.env["investra.fund"].browse(vals.get("fund_id", self.env.context.get("default_fund_id")))
            vals["company_id"] = fund.company_id.id if fund else self._shared_price_company().id
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and SYSTEM_PRICE_FIELDS & set(vals):
            raise UserError(self.env._("Cenu schvaluje jen schvalovací krok."))
        approved = self.filtered(lambda p: p.state == "approved")
        if approved and set(vals) - {"state", "approved_by"}:
            if {"instrument_id", "fund_id", "date", "company_id"} & set(vals):
                raise UserError(self.env._("U schválené ceny nejde změnit nástroj, fond ani datum. Založte novou cenu."))
            # Oprava schválené ceny: zpět do návrhu, schválí ji znovu druhá osoba. Hotová ocenění drží svou cenu.
            if "state" not in vals:
                approved.sudo().write({"state": "draft", "approved_by": False})
        if not self.env.su and PRICE_INPUT_FIELDS & set(vals):
            vals = {**vals, "entered_by": self.env.user.id}
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda p: p.state == "approved"):
            raise UserError(self.env._("Schválenou cenu nejde smazat."))
        return super().unlink()

    @api.constrains("instrument_id", "fund_id", "currency_id", "date", "deviation_reason")
    def _check_price(self):
        for price in self:
            instrument = price.instrument_id
            if price.currency_id != instrument.currency_id:
                raise ValidationError(self.env._(
                    "Měna ceny %(price)s se musí rovnat měně nástroje %(instrument)s (%(name)s).",
                    price=price.currency_id.name, instrument=instrument.currency_id.name, name=instrument.name,
                ))
            if instrument.fund_id and price.fund_id != instrument.fund_id:
                raise ValidationError(self.env._(
                    "Nástroj %(name)s patří jen fondu %(fund)s; cenu lze zadat jen tomuto fondu.",
                    name=instrument.name, fund=instrument.fund_id.display_name,
                ))
            if price.fund_id and not price.deviation_reason and self.sudo().search_count([
                ("instrument_id", "=", instrument.id), ("date", "=", price.date), ("fund_id", "=", False),
            ], limit=1):
                raise ValidationError(self.env._(
                    "Ke dni %(day)s existuje sdílená cena %(name)s; cena fondu musí mít důvod odchylky.",
                    day=price.date, name=instrument.name,
                ))

    def action_approve(self):
        if not self.env.user.has_group("investra_entity.group_valuation_approver"):
            raise UserError(self.env._("Ceny schvaluje jen uživatel se skupinou schvalování ocenění."))
        if self.sudo().company_id - self.env.companies:
            raise AccessError(self.env._("Cena patří jiné společnosti."))
        if self.filtered(lambda p: p.state != "draft"):
            raise UserError(self.env._("Schválit jde jen cenu v návrhu."))
        for price in self:
            if self.env.user in price.entered_by | price.create_uid:
                raise UserError(self.env._("Zadavatel nemůže schválit vlastní cenu."))
        self.sudo().write({"state": "approved", "approved_by": self.env.user.id})


class InvestraTrade(models.Model):
    """Portfoliová transakce; účetní doklad vzniká přes událost a nese nástroj na řádku."""

    _name = "investra.trade"
    _inherit = ["investra.record.guard"]
    _description = "Obchod s nástrojem"
    _order = "trade_date, id"
    _book_fields = ("fund_id",)
    _system_fields = SYSTEM_TRADE_FIELDS

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", string="Nástroj")
    trade_date = fields.Date(required=True, string="Datum sjednání")
    settlement_date = fields.Date(string="Datum vypořádání")
    quantity = fields.Float(required=True, digits=(20, 6), help="Kladně nákup, záporně prodej.", string="Množství")
    price = fields.Float(required=True, digits=(20, 8), string="Cena")
    fx_rate = fields.Float(default=1, digits=(16, 6), required=True, help="Funkční měna za jednotku měny nástroje.", string="Kurz")
    settlement_fx_rate = fields.Float(digits=(16, 6), help="Kurz platby; bez zadání platí kurz obchodu.", string="Kurz vypořádání")
    state = fields.Selection(
        [("draft", "Návrh"), ("unsettled", "Sjednáno, nevypořádáno"), ("settled", "Vypořádáno")],
        required=True, default="draft", readonly=True, string="Stav",
    )
    event_id = fields.Many2one("investra.accounting.event", readonly=True, string="Účetní událost")
    settlement_event_id = fields.Many2one("investra.accounting.event", readonly=True, string="Událost vypořádání")

    @api.constrains("quantity")
    def _check_quantity(self):
        for trade in self:
            if not trade.quantity:
                raise ValidationError(self.env._("Obchod musí mít množství."))

    @api.constrains("trade_date", "settlement_date")
    def _check_settlement_date(self):
        for trade in self:
            if trade.settlement_date and trade.settlement_date < trade.trade_date:
                raise ValidationError(self.env._("Vypořádání nemůže být před sjednáním."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_TRADE_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav obchodu mění jen zaúčtování."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            if SYSTEM_TRADE_FIELDS & set(vals):
                raise UserError(self.env._("Stav obchodu mění jen zaúčtování."))
            if self.filtered(lambda t: t.state == "settled") or (self.filtered("event_id") and BOOKED_TRADE_FIELDS & set(vals)):
                raise UserError(self.env._("Zaúčtovaný obchod nejde změnit."))
        return super().write(vals)

    def action_book(self):
        self._require_preparer()
        self.sudo()._book()
        return True

    def action_settle(self):
        self._require_preparer()
        self.sudo()._settle()
        return True

    def _require_preparer(self):
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        self.check_access("write")

    def _is_deferred(self):
        """Vypořádání je až po sjednání; stejný den nebo bez data jde obchod rovnou proti bance."""
        self.ensure_one()
        return bool(self.settlement_date) and self.settlement_date > self.trade_date

    def _recognition_date(self):
        """Den, od kterého je nástroj v pozici fondu."""
        self.ensure_one()
        if self.fund_id.trade_recognition == "settlement_date" and self._is_deferred():
            return self.settlement_date
        return self.trade_date

    def _booked_fx(self):
        """Kurz, kterým je nástroj zaúčtovaný."""
        self.ensure_one()
        if self.fund_id.trade_recognition == "settlement_date" and self._is_deferred():
            return self.settlement_fx_rate or self.fx_rate
        return self.fx_rate

    def _event_lines(self, role, counter_role, fx):
        """Dvojice řádků obchodu: role proti protiúčtu, v měně nástroje a ve funkční měně."""
        amount = self.quantity * self.price * fx
        foreign = self.quantity * self.price
        extra = {"investra_instrument_id": self.instrument_id.id}
        currency_id = self.instrument_id.currency_id.id
        foreign_currency = self.instrument_id.currency_id != self.company_id.currency_id
        debit = {"currency_id": currency_id, "amount_currency": foreign} if foreign_currency else {}
        credit = {"currency_id": currency_id, "amount_currency": -foreign} if foreign_currency else {}
        return [
            {"role": role, "amount": amount, "movement_type": "transaction", "extra": extra, **debit},
            {"role": counter_role, "amount": -amount, "movement_type": "transaction", **credit},
        ]

    def _post_trade_event(self, key, name, day, lines):
        event = self.env["investra.accounting.event"]._create_event(self.company_id, key, name, day, "trade", lines)
        event._lock_events()
        event._post_events()
        return event

    def _book(self):
        """Zaúčtuje obchod podle nastavení fondu; v prototypu bez poplatků."""
        for trade in self.filtered(lambda t: t.state == "draft"):
            instrument = trade.instrument_id
            if instrument.type_group == "other_holding":
                raise UserError(self.env._("Operace s ostatními podíly zatím nejsou napojené na účtování: %s.", instrument.name))
            deferred = trade._is_deferred()
            if deferred and trade.fund_id.trade_recognition == "settlement_date":
                trade.sudo().state = "unsettled"
                continue
            counter = trade._unsettled_role() if deferred else "bank"
            lines = trade._event_lines(instrument.role_id.code, counter, trade.fx_rate)
            event = trade._post_trade_event(f"trade:{trade.id}", f"Obchod {instrument.name}", trade.trade_date, lines)
            trade.sudo().write({"event_id": event.id, "state": "unsettled" if deferred else "settled"})

    def _unsettled_role(self):
        self.ensure_one()
        return "unsettled_payable" if self.quantity > 0 else "unsettled_receivable"

    def _settle(self):
        """Zaúčtuje vypořádání. Rozdíl kurzu proti závazku doúčtuje nejbližší ocenění."""
        for trade in self:
            if trade.state != "unsettled":
                raise UserError(self.env._("Vypořádat jde jen sjednaný nevypořádaný obchod."))
            instrument = trade.instrument_id
            fx = trade.settlement_fx_rate or trade.fx_rate
            name = f"Vypořádání {instrument.name}"
            if trade.fund_id.trade_recognition == "settlement_date":
                lines = trade._event_lines(instrument.role_id.code, "bank", fx)
                event = trade._post_trade_event(f"trade:{trade.id}", name, trade.settlement_date, lines)
                trade.sudo().write({"event_id": event.id, "settlement_event_id": event.id, "state": "settled"})
            else:
                lines = trade._event_lines(trade._unsettled_role(), "bank", fx)
                event = trade._post_trade_event(f"trade-settle:{trade.id}", name, trade.settlement_date, lines)
                trade.sudo().write({"settlement_event_id": event.id, "state": "settled"})

    @api.model
    def _recognised(self, fund, day, instrument=None):
        """Obchody, které jsou k datu v pozici fondu podle jeho nastavení."""
        domain = [("fund_id", "=", fund.id), ("trade_date", "<=", day)]
        if instrument:
            domain.append(("instrument_id", "=", instrument.id))
        return self.search(domain).filtered(lambda t: t._recognition_date() <= day)

    @api.model
    def _positions(self, fund, day):
        """Kusy a účetní hodnota po nástrojích k datu, z obchodů a z hlavní knihy."""
        quantities = {}
        for trade in self._recognised(fund, day):
            quantities[trade.instrument_id] = quantities.get(trade.instrument_id, 0.0) + trade.quantity
        return {instrument: qty for instrument, qty in quantities.items() if qty}


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    def write(self, vals):
        if "trade_recognition" in vals and self.env["investra.trade"].sudo().search_count([("fund_id", "in", self.ids)], limit=1):
            raise UserError(self.env._("Po prvním obchodu fondu nejde způsob zaúčtování změnit."))
        return super().write(vals)


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
