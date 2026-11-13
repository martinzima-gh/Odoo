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
# Po prvním obchodu neměnná pole nástroje. Klasifikace, způsob ocenění a role jsou v zařazení (rozhodnutí 2026-11-11).
# Měna od rozhodnutí 2026-11-13 „Sdílené nástroje a pravidlo knihy“: její změna by přepočetla pozice všech fondů.
LOCKED_AFTER_TRADE = {"type_id", "currency_id"}
# Nástroj bez ISIN se identifikuje druhem a hodnotou identifikátoru v rámci fondu (rozhodnutí 2026-11-13).
IDENTIFIER_KINDS = [
    ("contract", "Číslo smlouvy"), ("company", "IČO nebo LEI společnosti"), ("trade_ref", "Reference obchodu"), ("other", "Jiný"),
]
# Údaje nástroje, které mění NAV fondů; jejich změny se zapíší do historie nástroje a ukáže je kontrola ocenění
# instrument_changes. Vlastní zápis (podtyp mt_instrument_change) vedle standardního sledování polí: kontrola tak čte
# jen změny ovlivňující NAV a změny toků, ne např. přejmenování nebo list ČNB.
NAV_INSTRUMENT_FIELDS = {
    "currency_id", "maturity_date", "coupon_rate", "day_count", "accrual_method", "price_excludes_accrued", "max_price_age",
}
# Stav, události a důvody storna zapisuje jen zaúčtování a storno (rozhodnutí 2026-11-12 „Storno a oprava obchodu“).
SYSTEM_TRADE_FIELDS = {"state", "event_id", "settlement_event_id", "reversal_reason", "settlement_reversal_reason"}
# Odchylka kurzu vypořádání od kurzu obchodu, od které formulář upozorní (rozhodnutí 2026-11-12).
SETTLEMENT_FX_WARNING = 0.10
BOOKED_TRADE_FIELDS = {"fund_id", "portfolio_id", "instrument_id", "trade_date", "quantity", "side", "price", "fx_rate", "accrued_interest"}


def book_problem(env, books, record_label, in_form=False):
    """Text hlášky, když kniha záznamu není zaškrtnutá v přepínači firem nebo ji uživatel nemá povolenou; jinak False.

    `in_form`: varianta pro pruh ve formuláři (rozhodnutí 2026-11-13 „Upozornění na nezaškrtnutou knihu ve formuláři“) –
    přepnutí firmy znovu načte stránku a neuložený formulář zahodí, proto se má kniha zaškrtnout před vyplněním.
    """
    if env.su:
        return False
    book = (books - env.companies)[:1].sudo()
    if not book:
        return False
    if book in env.user.sudo().company_ids:
        if in_form:
            return env._("%(what)s vede kniha %(book)s, která není zaškrtnutá v přepínači firem vpravo nahoře. Zaškrtněte ji "
                         "dřív, než začnete vyplňovat nebo upravovat: bez ní se změny neuloží a přepnutí firem neuložený "
                         "formulář zahodí.", what=record_label, book=book.name)
        return env._("%(what)s vede kniha %(book)s. Zaškrtněte ji v přepínači firem vpravo nahoře a akci opakujte.",
                     what=record_label, book=book.name)
    if in_form:
        return env._("%(what)s vede kniha %(book)s, kterou nemáte mezi povolenými společnostmi: změny nepůjde uložit. "
                     "Pokud je potřebujete, požádejte správce (Nastavení → Uživatelé → Povolené společnosti).",
                     what=record_label, book=book.name)
    return env._("%(what)s vede kniha %(book)s, kterou nemáte mezi povolenými společnostmi. "
                 "Požádejte správce o přidání (Nastavení → Uživatelé → Povolené společnosti).",
                 what=record_label, book=book.name)


def check_book_active(env, books, record_label):
    """Srozumitelná hláška místo obecné chyby více společností (rozhodnutí 2026-11-13 „Sdílené nástroje a pravidlo knihy“).

    Pravidlo záznamů pustí založení a změnu jen v knize zaškrtnuté v přepínači firem. Tady se to ověří předem
    a hláška řekne, kterou knihu zaškrtnout, nebo že ji uživatel nemá mezi povolenými společnostmi.
    Pravidlo záznamů zůstává beze změny, tohle je jen dřívější a čitelnější kontrola.
    """
    message = book_problem(env, books, record_label)
    if message:
        raise AccessError(message)
SYSTEM_PRICE_FIELDS = {"state", "approved_by", "entered_by"}
# Kdo změní některé z těchto polí návrhu, stává se zadavatelem ceny.
PRICE_INPUT_FIELDS = {"instrument_id", "fund_id", "date", "price", "currency_id", "source", "deviation_reason"}


class InvestraInstrumentType(models.Model):
    """Typ nástroje: nabízí výchozí hodnoty. Klasifikaci, způsob ocenění a roli navrhuje pro zařazení ve fondu,
    list ČNB a stáří ceny pro nástroj; rozhoduje účetní."""

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

    isin_required = fields.Boolean(
        string="Vyžaduje ISIN", help="Nástroj tohoto typu musí mít ISIN. Nástroj s ISIN je sdílený pro všechny fondy.",
    )
    code_prefix = fields.Char(default="NAS", required=True, string="Prefix kódu nástroje", help="Např. AKC → AKC-000123.")

    _code_uniq = models.Constraint("unique(code)", "Kód typu nástroje musí být jedinečný.")


class InvestraInstrument(models.Model):
    """Nástroj. S ISIN je sdílený pro všechny fondy a vede ho kniha investiční společnosti; bez ISIN patří jednomu
    fondu a vede ho kniha fondu (rozhodnutí 2026-11-13 „Sdílené nástroje a pravidlo knihy“)."""

    _name = "investra.instrument"
    _inherit = ["investra.record.guard", "mail.thread"]
    _description = "Nástroj"
    _order = "name"
    _book_fields = ("fund_id", "company_id")
    _system_fields = frozenset({"code", "company_id"})

    name = fields.Char(required=True, string="Název")
    code = fields.Char(readonly=True, copy=False, index=True, string="Kód", help="Přidělí systém při založení, nemění se.")
    # Kniha nástroje: u nástroje fondu kniha fondu, u sdíleného kniha investiční společnosti. Do založení knihy
    # investiční společnosti je u sdíleného prázdná (založit ho smí jen superuživatel, ostatním je jen ke čtení).
    company_id = fields.Many2one("res.company", readonly=True, index=True, string="Kniha")
    book_warning = fields.Char(compute="_compute_book_warning", string="Upozornění na knihu")
    isin = fields.Char(string="ISIN")
    identifier_kind = fields.Selection(IDENTIFIER_KINDS, string="Druh identifikátoru")
    identifier = fields.Char(string="Identifikátor", help="Nástroj bez ISIN: např. číslo smlouvy, IČO nebo LEI.")
    isin_required = fields.Boolean(related="type_id.isin_required")
    currency_id = fields.Many2one("res.currency", required=True, string="Měna")
    type_id = fields.Many2one("investra.instrument.type", required=True, ondelete="restrict", string="Typ", tracking=True)
    type_group = fields.Selection(related="type_id.group", string="Skupina")
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
    # Odchylka od návrhu etapy 2 (pole u typu): návrh se bere z druhu typu (dluhopis), aby se nemusela měnit data typů;
    # u nástroje jde přepsat (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).
    price_excludes_accrued = fields.Boolean(
        compute="_compute_price_excludes_accrued", store=True, readonly=False, string="Cena bez naběhlého úroku",
        help="Zaškrtnuto (dluhopisy): reálná hodnota = kusy × cena + naběhlý úrok. Nezaškrtnuto (vklady, úvěry): úrok je "
             "v ceně; naběhlý úrok jen rozdělí výsledek ocenění na úrok a přecenění.",
    )
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
    calendar_missing = fields.Boolean(compute="_compute_calendar_missing", string="Chybí kalendář toků")
    classification_ids = fields.One2many(
        "investra.portfolio.classification", "instrument_id", string="Zařazení ve fondech",
        help="Kategorie IFRS 9, způsob ocenění a role účtu podle obchodního modelu fondu (rozhodnutí 2026-11-11).",
    )

    _isin_currency_uniq = models.UniqueIndex(
        "(isin, currency_id) WHERE isin IS NOT NULL", "Nástroj s tímto ISIN a měnou už existuje; použijte ho.",
    )
    _identifier_uniq = models.UniqueIndex(
        "(fund_id, identifier_kind, identifier) WHERE isin IS NULL AND identifier IS NOT NULL",
        "Fond už má nástroj s tímto identifikátorem.",
    )
    _instrument_code_uniq = models.UniqueIndex("(code) WHERE code IS NOT NULL", "Kód nástroje musí být jedinečný.")

    def _type_proposal(self, kind):
        return {"cnb_sheet": kind.cnb_sheet, "max_price_age": kind.max_price_age}

    @api.model
    def _normalize_identifiers(self, vals):
        """ISIN velkými písmeny bez mezer; prázdný identifikátor = nevyplněný."""
        if "isin" in vals:
            vals["isin"] = "".join((vals["isin"] or "").split()).upper() or False
        if "identifier" in vals:
            vals["identifier"] = (vals["identifier"] or "").strip() or False

    @api.model
    def _shared_company(self):
        """Sdílené nástroje vede kniha investiční společnosti, stejně jako sdílené ceny (rozhodnutí 2026-11-13)."""
        books = self.env["investra.entity"].sudo().search([("entity_type", "=", "manager")])
        if len(books) == 1:
            return books.company_id
        if self.env.su:
            # Skripty a testy před založením knihy investiční společnosti; její založení nástroj převezme.
            return self.env["res.company"]
        raise UserError(self.env._(
            "Nástroj s ISIN je sdílený a vede ho kniha investiční společnosti, která zatím není založená (nebo jich je víc). "
            "Nástroj bez ISIN založte jako nástroj fondu."
        ))

    @api.depends("fund_id", "company_id")
    @api.depends_context("uid", "allowed_company_ids")
    def _compute_book_warning(self):
        """Pruh ve formuláři ještě před vyplněním: kniha se určí stejně jako při založení (fond, jinak investiční společnost).

        Rozhodnutí 2026-11-13 „Upozornění na nezaškrtnutou knihu ve formuláři“. Bez knihy investiční společnosti se nic
        neukazuje; to řekne chyba při uložení (`_shared_company`).
        """
        managers = self.env["investra.entity"].sudo().search([("entity_type", "=", "manager")])
        shared_book = managers.company_id if len(managers) == 1 else self.env["res.company"]
        for instrument in self:
            fund = instrument.sudo().fund_id
            book = instrument.sudo().company_id or (fund.company_id if fund else shared_book)
            label = self.env._("Nástroj fondu") if fund else self.env._("Sdílený nástroj (s ISIN)")
            instrument.book_warning = book_problem(self.env, book, label, in_form=True)

    @api.model_create_multi
    def create(self, vals_list):
        Sequence = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            kind = self.env["investra.instrument.type"].browse(vals.get("type_id"))
            for field, value in self._type_proposal(kind).items():
                vals.setdefault(field, value)
            self._normalize_identifiers(vals)
            fund = self.env["investra.fund"].browse(vals.get("fund_id")).sudo()
            vals["company_id"] = fund.company_id.id if fund else self._shared_company().id
            check_book_active(self.env, self.env["res.company"].browse(vals["company_id"]),
                              self.env._("Nástroj fondu") if fund else self.env._("Sdílený nástroj (s ISIN)"))
            vals["code"] = f"{kind.code_prefix or 'NAS'}-{Sequence.next_by_code('investra.instrument')}"
        return super().create(vals_list)

    @api.constrains("isin", "type_id", "fund_id", "identifier_kind", "identifier")
    def _check_identifier(self):
        for instrument in self:
            if instrument.type_id.isin_required and not instrument.isin:
                raise ValidationError(self.env._("Nástroj typu %(type)s musí mít ISIN: %(name)s.",
                                                 type=instrument.type_id.name, name=instrument.name))
            if instrument.isin and instrument.fund_id:
                raise ValidationError(self.env._(
                    "Nástroj s ISIN je sdílený pro všechny fondy, pole Fond nechte prázdné: %s.", instrument.name))
            if not instrument.isin and not instrument.fund_id:
                raise ValidationError(self.env._("Nástroj bez ISIN patří jednomu fondu, vyplňte Fond: %s.", instrument.name))
            if not instrument.isin and not (instrument.identifier_kind and instrument.identifier):
                raise ValidationError(self.env._(
                    "Nástroj bez ISIN musí mít druh a hodnotu identifikátoru (např. číslo smlouvy): %s.", instrument.name))

    @api.onchange("type_id")
    def _onchange_type_id(self):
        if self.type_id:
            self.update(self._type_proposal(self.type_id))

    @api.depends("type_id")
    def _compute_price_excludes_accrued(self):
        for instrument in self:
            instrument.price_excludes_accrued = instrument.type_id.kind == "bond"

    @api.depends("type_id.kind", "cashflow_ids")
    def _compute_calendar_missing(self):
        for instrument in self:
            instrument.calendar_missing = instrument.type_id.kind == "bond" and not instrument.cashflow_ids

    @api.depends("type_id", "cnb_sheet")
    def _compute_deviates(self):
        for instrument in self:
            kind = instrument.type_id
            instrument.deviates_from_type = bool(kind) and (instrument.cnb_sheet or False) != (kind.cnb_sheet or False)

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
        if not self.env.su and "code" in vals:
            raise UserError(self.env._("Kód nástroje přiděluje systém a nemění se."))
        for instrument in self.sudo():
            check_book_active(self.env, instrument.company_id,
                              self.env._("Nástroj %s", instrument.display_name))
        self._normalize_identifiers(vals)
        if not self.env.su and LOCKED_AFTER_TRADE & set(vals):
            changed = self.filtered(lambda i: any(
                (i[name].id if name.endswith("_id") else i[name]) != vals[name] for name in LOCKED_AFTER_TRADE & set(vals)
            ))
            if changed and self.env["investra.trade"].sudo().search_count([("instrument_id", "in", changed.ids)], limit=1):
                raise UserError(self.env._("Po prvním obchodu nejde měnit typ ani měnu nástroje."))
        watched = NAV_INSTRUMENT_FIELDS & set(vals)
        before = {instrument: {name: instrument._change_text(name) for name in watched} for instrument in self} if watched else {}
        result = super().write(vals)
        for instrument, old in before.items():
            changes = [
                f"{instrument._fields[name].get_description(self.env)['string']}: {old[name]} → {instrument._change_text(name)}"
                for name in sorted(watched) if instrument._change_text(name) != old[name]
            ]
            if changes:
                instrument._log_cashflow_change(self.env._("Změna údajů: %s", "; ".join(changes)))
        return result

    def _change_text(self, name):
        value = self[name]
        if isinstance(value, models.BaseModel):
            return value.display_name or "–"
        if self._fields[name].type == "boolean":
            return self.env._("ano") if value else self.env._("ne")
        if self._fields[name].type == "selection":
            return dict(self._fields[name]._description_selection(self.env)).get(value, "–")
        return "–" if value is False or value is None else str(value)

    def _log_cashflow_change(self, body):
        """Změny údajů a smluvních toků do historie nástroje; kontrola ocenění instrument_changes je ukáže."""
        subtype = self.env.ref("investra_instruments.mt_instrument_change")
        for instrument in self:
            instrument.sudo().message_post(body=body, subtype_id=subtype.id, author_id=self.env.user.partner_id.id)

    def _effective_accrual(self, fund):
        """Metoda úročení pro fond; volba na nástroji má přednost před fondem."""
        self.ensure_one()
        return fund.accrual_method if self.accrual_method == "fund" else self.accrual_method


class InvestraInstrumentCashflow(models.Model):
    """Smluvní tok na jednotku nástroje, bez pořízení; to se bere z obchodu.

    Každé založení, změna a smazání se zapíše do historie nástroje (rozhodnutí 2026-11-13).
    """

    _name = "investra.instrument.cashflow"
    _description = "Smluvní peněžní tok nástroje"
    _order = "date, id"

    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="cascade", index=True, string="Nástroj")
    company_id = fields.Many2one(related="instrument_id.company_id", store=True, index=True)
    date = fields.Date(required=True, string="Datum")
    amount = fields.Float(required=True, digits=(20, 8), string="Částka na jednotku")
    flow_type = fields.Selection([("interest", "Úrok"), ("principal", "Jistina")], required=True, default="principal", string="Druh")

    def _describe(self):
        kinds = dict(self._fields["flow_type"]._description_selection(self.env))
        return f"{self.date} {kinds.get(self.flow_type, '')} {self.amount:g}"

    @api.model_create_multi
    def create(self, vals_list):
        flows = super().create(vals_list)
        for flow in flows:
            flow.instrument_id._log_cashflow_change(self.env._("Tok přidán: %s", flow._describe()))
        return flows

    def write(self, vals):
        before = {flow: flow._describe() for flow in self}
        if "instrument_id" in vals and not self.env.su and self.filtered(lambda f: f.instrument_id.id != vals["instrument_id"]):
            raise UserError(self.env._("Tok nejde přesunout k jinému nástroji. Smažte ho a založte znovu."))
        result = super().write(vals)
        for flow, old in before.items():
            if flow._describe() != old:
                flow.instrument_id._log_cashflow_change(self.env._("Tok změněn: %(old)s → %(new)s", old=old, new=flow._describe()))
        return result

    def unlink(self):
        removed = [(flow.instrument_id, flow._describe()) for flow in self]
        result = super().unlink()
        for instrument, text in removed:
            if instrument.exists():
                instrument._log_cashflow_change(self.env._("Tok smazán: %s", text))
        return result


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
    book_warning = fields.Char(compute="_compute_book_warning", string="Upozornění na knihu")
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

    @api.depends("fund_id", "company_id")
    @api.depends_context("uid", "allowed_company_ids")
    def _compute_book_warning(self):
        """Pruh ve formuláři ještě před vyplněním (rozhodnutí 2026-11-13 „Upozornění na nezaškrtnutou knihu ve formuláři“)."""
        managers = self.env["investra.entity"].sudo().search([("entity_type", "=", "manager")])
        shared_book = managers.company_id if len(managers) == 1 else self.env["res.company"]
        for price in self:
            fund = price.sudo().fund_id
            book = price.sudo().company_id or (fund.company_id if fund else shared_book)
            label = self.env._("Cenu fondu") if fund else self.env._("Sdílenou tržní cenu")
            price.book_warning = book_problem(self.env, book, label, in_form=True)

    @api.model
    def _shared_price_company(self):
        """Sdílené ceny vede kniha investiční společnosti (rozhodnutí 2026-11-11); stejně sdílené nástroje (2026-11-13)."""
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
            check_book_active(self.env, self.env["res.company"].browse(vals["company_id"]),
                              self.env._("Cenu fondu") if fund else self.env._("Sdílenou tržní cenu"))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and SYSTEM_PRICE_FIELDS & set(vals):
            raise UserError(self.env._("Cenu schvaluje jen schvalovací krok."))
        for price in self.sudo():
            check_book_active(self.env, price.company_id,
                              self.env._("Sdílenou tržní cenu") if not price.fund_id else self.env._("Cenu fondu"))
        approved = self.filtered(lambda p: p.state == "approved")
        if approved and set(vals) - {"state", "approved_by"}:
            if {"instrument_id", "fund_id", "date", "company_id"} & set(vals):
                raise UserError(self.env._("U schválené ceny nejde změnit nástroj, fond ani datum. Založte novou cenu."))
            # Oprava schválené ceny: zpět do návrhu, schválí ji znovu druhá osoba. Hotová ocenění drží svou cenu.
            if "state" not in vals:
                approved.sudo().write({"state": "draft", "approved_by": False})
        if set(vals) - {"state", "approved_by"}:
            # Změněná cena se schvaluje znovu od prvního kroku.
            self.env["investra.approval.done"].sudo().search([
                ("res_model", "=", self._name), ("res_id", "in", self.ids),
            ]).unlink()
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
        """Schválení ceny podle schvalovací matice (rozhodnutí 2026-11-11).

        Čtyři oči (výchozí): schvaluje role schvalování ocenění, nikdy zadavatel. Jeden člověk: smí i zadavatel
        a úkon se zapíše. Sdílená cena se týká všech fondů, platí nejpřísnější pravidlo z nich.
        """
        if self.sudo().company_id - self.env.companies:
            raise AccessError(self.env._("Cena patří jiné společnosti."))
        if self.filtered(lambda p: p.state != "draft"):
            raise UserError(self.env._("Schválit jde jen cenu v návrhu."))
        Matrix = self.env["investra.approval.matrix"]
        for price in self:
            funds = price.sudo().fund_id or self.env["investra.fund"].sudo().search([])
            if Matrix._approve_step("price_approve", price, funds, price.sudo().entered_by | price.sudo().create_uid):
                price.sudo().write({"state": "approved", "approved_by": self.env.user.id})


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
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", index=True, string="Obchodní model",
        domain="[('fund_id', '=', fund_id)]", help="Portfolio fondu s obchodním modelem; určuje klasifikaci IFRS 9 obchodu.",
    )
    classification_id = fields.Many2one(
        "investra.portfolio.classification", compute="_compute_classification_id", string="Zařazení",
    )
    ifrs9_category = fields.Selection(IFRS9_CATEGORY, compute="_compute_classification_id", string="Kategorie IFRS 9")
    trade_date = fields.Date(required=True, string="Datum sjednání")
    settlement_date = fields.Date(string="Datum vypořádání")
    quantity = fields.Float(required=True, digits=(20, 6), help="Kladně nákup, záporně prodej.", string="Množství")
    # Nákup a prodej zvlášť, kusy kladně; množství se znaménkem zůstává pro výpočty a importy (2026-11-12, zkouška v UI).
    side = fields.Selection([("buy", "Nákup"), ("sell", "Prodej")], compute="_compute_side", store=True, readonly=False,
                            string="Směr")
    units = fields.Float(compute="_compute_units", inverse="_inverse_units", digits=(20, 6), string="Kusy",
                         help="Kladně; u prodeje nejvýš kusy, které fond k datu sjednání v obchodním modelu drží.")
    held_instrument_ids = fields.Many2many("investra.instrument", compute="_compute_held", string="Držené nástroje")
    held_quantity = fields.Float(compute="_compute_held", digits=(20, 6), string="Drženo k datu",
                                 help="Kusy nástroje v obchodním modelu k datu sjednání, bez tohoto obchodu.")
    price = fields.Float(required=True, digits=(20, 8), string="Cena")
    instrument_kind = fields.Selection(related="instrument_id.type_id.kind", string="Druh nástroje")
    accrued_interest = fields.Float(
        digits=(20, 2), string="Naběhlý úrok",
        help="Jen u dluhopisů: naběhlý kupón zaplacený při nákupu nebo přijatý při prodeji, v měně nástroje, kladně. "
             "Platba obchodu = kusy × cena + naběhlý úrok (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).",
    )
    fx_rate = fields.Float(default=1, digits=(16, 6), required=True, help="Funkční měna za jednotku měny nástroje.", string="Kurz")
    settlement_fx_rate = fields.Float(digits=(16, 6), help="Kurz platby; bez zadání platí kurz obchodu.", string="Kurz vypořádání")
    state = fields.Selection(
        [("draft", "Návrh"), ("unsettled", "Sjednáno, nevypořádáno"), ("settled", "Vypořádáno"), ("reversed", "Stornováno")],
        required=True, default="draft", readonly=True, index=True, string="Stav",
    )
    event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Účetní událost")
    settlement_event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Událost vypořádání")
    reversal_reason = fields.Text(readonly=True, copy=False, string="Důvod storna")
    settlement_reversal_reason = fields.Text(
        readonly=True, copy=False, string="Důvod storna vypořádání",
        help="Poslední storno vypořádání; obchod se po něm vrátil do stavu Sjednáno, nevypořádáno.",
    )
    replaced_id = fields.Many2one("investra.trade", readonly=True, copy=False, ondelete="restrict", string="Opravuje obchod")
    foreign_currency = fields.Boolean(compute="_compute_foreign_currency", string="Nástroj v cizí měně")
    settlement_fx_note = fields.Char(compute="_compute_settlement_fx_note", string="Upozornění ke kurzu vypořádání")

    @api.depends("instrument_id", "fund_id")
    def _compute_foreign_currency(self):
        for trade in self:
            company_currency = trade.fund_id.company_id.currency_id
            trade.foreign_currency = bool(trade.instrument_id and company_currency and trade.instrument_id.currency_id != company_currency)

    @api.depends("foreign_currency", "fx_rate", "settlement_fx_rate")
    def _compute_settlement_fx_note(self):
        """Cizí měna: kurz vypořádání daleko od kurzu obchodu je spíš překlep (podnět: obchod se zadanou cenou místo kurzu)."""
        for trade in self:
            note = False
            if trade.foreign_currency and trade.fx_rate and trade.settlement_fx_rate:
                deviation = abs(trade.settlement_fx_rate / trade.fx_rate - 1)
                if deviation > SETTLEMENT_FX_WARNING:
                    note = self.env._(
                        "Kurz vypořádání %(settle)s se liší od kurzu obchodu %(trade)s o %(pct)s %%. Zkontrolujte ho.",
                        settle=trade.settlement_fx_rate, trade=trade.fx_rate, pct=round(deviation * 100, 1),
                    )
            trade.settlement_fx_note = note

    @api.onchange("instrument_id", "fund_id")
    def _onchange_home_currency_rate(self):
        """Nástroj v měně fondu: kurzy jsou skryté a musí být 1."""
        for trade in self:
            if trade.instrument_id and trade.fund_id and not trade.foreign_currency:
                trade.fx_rate = 1
                trade.settlement_fx_rate = 0

    @api.constrains("instrument_id", "fund_id", "fx_rate", "settlement_fx_rate")
    def _check_home_currency_rate(self):
        for trade in self:
            if trade.foreign_currency:
                continue
            if trade.fx_rate != 1 or trade.settlement_fx_rate not in (0, 1):
                raise ValidationError(self.env._(
                    "Nástroj %s je v měně fondu: kurz obchodu i kurz vypořádání musí být 1.", trade.instrument_id.name))

    @api.depends("quantity")
    def _compute_side(self):
        for trade in self:
            if trade.quantity < 0:
                trade.side = "sell"
            elif trade.quantity > 0 or not trade.side:
                trade.side = "buy"

    @api.depends("quantity")
    def _compute_units(self):
        for trade in self:
            trade.units = abs(trade.quantity)

    def _inverse_units(self):
        for trade in self:
            quantity = -trade.units if trade.side == "sell" else trade.units
            if trade.quantity != quantity:
                trade.quantity = quantity

    @api.onchange("side", "units")
    def _onchange_side_units(self):
        for trade in self:
            trade.quantity = -trade.units if trade.side == "sell" else trade.units

    def _holdings_without_self(self):
        """Pozice fondu k datu sjednání bez tohoto obchodu (ve formuláři i před uložením)."""
        self.ensure_one()
        fund = self.fund_id._origin
        if not fund:
            return {}
        day = self.trade_date or fields.Date.context_today(self)
        holdings = dict(self.sudo()._holdings(fund.sudo(), day))
        origin = self._origin
        if origin.id and origin.state != "reversed" and origin.event_id and origin._recognition_date() <= day:
            key = (origin.instrument_id, origin.portfolio_id)
            holdings[key] = holdings.get(key, 0.0) - origin.quantity
        return {key: qty for key, qty in holdings.items() if qty > 1e-9}

    @api.depends("fund_id", "trade_date", "instrument_id", "portfolio_id")
    def _compute_held(self):
        for trade in self:
            holdings = trade._holdings_without_self()
            trade.held_instrument_ids = [(6, 0, list({instrument.id for instrument, _p in holdings}))]
            trade.held_quantity = holdings.get((trade.instrument_id._origin, trade.portfolio_id._origin), 0.0)

    @api.onchange("instrument_id", "side")
    def _onchange_sale_portfolio(self):
        """Prodej: obchodní model z držené pozice; volí se jen u nástroje drženého ve dvou modelech."""
        for trade in self:
            if trade.side != "sell" or not trade.instrument_id:
                continue
            portfolios = [p for i, p in trade._holdings_without_self() if i == trade.instrument_id._origin]
            if len(portfolios) == 1:
                trade.portfolio_id = portfolios[0]

    @api.constrains("quantity", "side")
    def _check_side(self):
        for trade in self:
            if (trade.side == "sell") != (trade.quantity < 0):
                raise ValidationError(self.env._("Směr obchodu nesouhlasí se znaménkem množství: %s.", trade.instrument_id.name))

    @api.constrains("quantity", "trade_date", "instrument_id", "portfolio_id")
    def _check_sale_on_save(self):
        for trade in self:
            trade._check_sale()

    @api.constrains("quantity")
    def _check_quantity(self):
        for trade in self:
            if not trade.quantity:
                raise ValidationError(self.env._("Obchod musí mít množství."))

    @api.depends("portfolio_id", "instrument_id", "trade_date")
    def _compute_classification_id(self):
        Classification = self.env["investra.portfolio.classification"]
        for trade in self:
            ready = trade.portfolio_id and trade.instrument_id and trade.trade_date
            trade.classification_id = Classification._valid(trade.portfolio_id, trade.instrument_id, trade.trade_date) if ready else False
            trade.ifrs9_category = trade.classification_id.ifrs9_category

    @api.onchange("fund_id")
    def _onchange_fund_id(self):
        if self.fund_id and self.portfolio_id.fund_id != self.fund_id:
            self.portfolio_id = self.fund_id._default_portfolio()

    @api.constrains("fund_id", "portfolio_id")
    def _check_portfolio(self):
        for trade in self:
            if trade.portfolio_id.fund_id != trade.fund_id:
                raise ValidationError(self.env._("Obchodní model nepatří fondu obchodu."))

    def _classification(self):
        """Zařazení platné k datu sjednání; bez něj obchod nejde zaúčtovat."""
        self.ensure_one()
        classification = self.classification_id
        if not classification:
            raise UserError(self.env._(
                "Nástroj %(name)s nemá v obchodním modelu %(portfolio)s k %(day)s zařazení. Založte ho v obchodních modelech fondu.",
                name=self.instrument_id.name, portfolio=self.portfolio_id.name, day=self.trade_date,
            ))
        return classification

    def _check_sale(self):
        """Prodej nesmí vzít z portfolia víc kusů, než v něm k datu sjednání je."""
        self.ensure_one()
        if self.quantity >= 0:
            return
        held = sum(self.sudo().search([
            ("fund_id", "=", self.fund_id.id), ("portfolio_id", "=", self.portfolio_id.id),
            ("instrument_id", "=", self.instrument_id.id), ("trade_date", "<=", self.trade_date), ("id", "!=", self.id),
            # Jen zaúčtované obchody (rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“). Na rozdíl od pozice stačí
            # stisknuté Zaúčtovat: u fondu s pozicí od data vypořádání vzniká doklad nákupu až při vypořádání
            # a prodej sjednaný před ním by jinak nešel zaúčtovat (kontrola prodeje pracuje s datem sjednání).
            ("state", "not in", ("draft", "reversed")),
        ]).mapped("quantity"))
        if held + self.quantity < -1e-9:
            raise UserError(self.env._(
                "V obchodním modelu %(portfolio)s je k %(day)s jen %(held)s kusů %(name)s; prodej %(qty)s nejde zaúčtovat.",
                portfolio=self.portfolio_id.name, day=self.trade_date, held=held, name=self.instrument_id.name, qty=-self.quantity,
            ))

    @api.constrains("accrued_interest", "instrument_id")
    def _check_accrued_interest(self):
        for trade in self:
            if trade.accrued_interest < 0:
                raise ValidationError(self.env._("Naběhlý úrok obchodu se zadává kladně, i u prodeje."))
            if trade.accrued_interest and trade.instrument_id.type_id.kind != "bond":
                raise ValidationError(self.env._("Naběhlý úrok se u obchodu zadává jen u dluhopisů: %s.", trade.instrument_id.name))

    def _signed_accrued_interest(self):
        """Naběhlý úrok se znaménkem obchodu: nákup kladně, prodej záporně (v měně nástroje)."""
        self.ensure_one()
        return self.accrued_interest if self.quantity >= 0 else -self.accrued_interest

    @api.constrains("trade_date", "settlement_date")
    def _check_settlement_date(self):
        for trade in self:
            if trade.settlement_date and trade.settlement_date < trade.trade_date:
                raise ValidationError(self.env._("Vypořádání nemůže být před sjednáním."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_TRADE_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav obchodu mění jen zaúčtování."))
        for vals in vals_list:
            # Import se směrem a kladnými kusy: znaménko množství podle směru.
            if vals.get("side") and vals.get("quantity"):
                vals["quantity"] = -abs(vals["quantity"]) if vals["side"] == "sell" else abs(vals["quantity"])
            # Fond s jediným portfoliem: obchod ho dostane sám (rozhodnutí 2026-11-11, portfolio „Hlavní“).
            if not vals.get("portfolio_id") and vals.get("fund_id"):
                vals["portfolio_id"] = self.env["investra.fund"].browse(vals["fund_id"])._default_portfolio().id
                if not vals["portfolio_id"]:
                    raise UserError(self.env._("Fond má víc obchodních modelů; vyberte, do kterého obchod patří."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            if SYSTEM_TRADE_FIELDS & set(vals):
                raise UserError(self.env._("Stav obchodu mění jen zaúčtování."))
            if self.filtered(lambda t: t.state == "reversed"):
                raise UserError(self.env._("Stornovaný obchod nejde změnit."))
            if self.filtered(lambda t: t.state == "settled") or (self.filtered("event_id") and BOOKED_TRADE_FIELDS & set(vals)):
                raise UserError(self.env._("Zaúčtovaný obchod nejde změnit; opravte ho stornem vypořádání nebo opravou obchodu."))
        if vals.get("side") and vals.get("quantity"):
            vals = dict(vals, quantity=-abs(vals["quantity"]) if vals["side"] == "sell" else abs(vals["quantity"]))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda t: t.state != "draft" or t.event_id):
            raise UserError(self.env._("Zaúčtovaný nebo stornovaný obchod nejde smazat; opravte ho stornem."))
        return super().unlink()

    def copy_data(self, default=None):
        # Stav, události a důvody storna nastavuje jen zaúčtování a storno; kopie začíná v návrhu.
        vals_list = super().copy_data(default)
        for vals in vals_list:
            for name in SYSTEM_TRADE_FIELDS:
                vals.pop(name, None)
        return vals_list

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
        """Řádky obchodu: role proti protiúčtu, v měně nástroje a ve funkční měně.

        Naběhlý úrok dluhopisu je samostatný řádek role (stejný účet, popis „Naběhlý úrok“); protiúčet nese celou platbu.
        """
        round_ = self.company_id.currency_id.round
        foreign = self.quantity * self.price
        interest_foreign = self._signed_accrued_interest()
        amount = round_(foreign * fx)
        interest = round_((foreign + interest_foreign) * fx) - amount
        extra = {"investra_instrument_id": self.instrument_id.id, "investra_classification_id": self._classification().id}
        currency_id = self.instrument_id.currency_id.id
        foreign_currency = self.instrument_id.currency_id != self.company_id.currency_id

        def currency(value):
            return {"currency_id": currency_id, "amount_currency": value} if foreign_currency else {}

        lines = [{"role": role, "amount": amount, "movement_type": "transaction", "extra": extra, **currency(foreign)}]
        if interest or interest_foreign:
            lines.append({"role": role, "amount": interest, "movement_type": "transaction", "extra": extra,
                          "name": self.env._("Naběhlý úrok %s", self.instrument_id.name), **currency(interest_foreign)})
        lines.append({"role": counter_role, "amount": -(amount + interest), "movement_type": "transaction",
                      **currency(-(foreign + interest_foreign))})
        return lines

    def _post_trade_event(self, key, name, day, lines, event_type="trade"):
        event = self.env["investra.accounting.event"]._create_event(
            self.company_id, key, name, day, event_type, lines, source=self,
        )
        event._lock_events()
        event._post_events()
        return event

    def _planned_postings(self):
        """Doklady obchodu v pořadí, jak vzniknou: [(krok, klíč, název, datum, řádky, druh události)].

        Krok „book“ vzniká tlačítkem Zaúčtovat, „settle“ tlačítkem Vypořádat. Používá zaúčtování i náhled
        Očekávané zaúčtování (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“), aby se nemohly rozejít.
        """
        self.ensure_one()
        name = self.instrument_id.name
        role = self._classification().role_id.code
        # Nevypořádaný obchod má vypořádání i po pozdější úpravě data vypořádání (dříve _settle nezkoumal odklad).
        deferred = self._is_deferred() or self.state == "unsettled"
        settlement_fx = self.settlement_fx_rate or self.fx_rate
        if not deferred:
            return [("book", f"trade:{self.id}", f"Obchod {name}", self.trade_date,
                     self._event_lines(role, "bank", self.fx_rate), "trade")]
        if self.fund_id.trade_recognition == "settlement_date":
            return [("settle", f"trade:{self.id}", f"Vypořádání {name}", self.settlement_date,
                     self._event_lines(role, "bank", settlement_fx), "trade")]
        unsettled = self._unsettled_role()
        return [
            ("book", f"trade:{self.id}", f"Obchod {name}", self.trade_date,
             self._event_lines(role, unsettled, self.fx_rate), "trade"),
            ("settle", f"trade-settle:{self.id}", f"Vypořádání {name}", self.settlement_date,
             self._event_lines(unsettled, "bank", settlement_fx), "trade_settlement"),
        ]

    def _planned_step(self, step):
        self.ensure_one()
        return next((plan for plan in self._planned_postings() if plan[0] == step), None)

    def _book(self):
        """Zaúčtuje obchod podle nastavení fondu; v prototypu bez poplatků."""
        for trade in self.filtered(lambda t: t.state == "draft"):
            instrument = trade.instrument_id
            if instrument.type_group == "other_holding":
                raise UserError(self.env._("Operace s ostatními podíly zatím nejsou napojené na účtování: %s.", instrument.name))
            trade._classification()
            trade._check_sale()
            deferred = trade._is_deferred()
            plan = trade._planned_step("book")
            if not plan:
                # Rozvaha ke dni vypořádání: do vypořádání se nic neúčtuje.
                trade.sudo().state = "unsettled"
                continue
            _step, key, name, day, lines, event_type = plan
            event = trade._post_trade_event(key, name, day, lines, event_type)
            trade.sudo().write({"event_id": event.id, "state": "unsettled" if deferred else "settled"})

    def _unsettled_role(self):
        self.ensure_one()
        return "unsettled_payable" if self.quantity > 0 else "unsettled_receivable"

    def _settle(self):
        """Zaúčtuje vypořádání. Rozdíl kurzu proti závazku doúčtuje nejbližší ocenění."""
        for trade in self:
            if trade.state != "unsettled":
                raise UserError(self.env._("Vypořádat jde jen sjednaný nevypořádaný obchod."))
            _step, key, name, day, lines, event_type = trade._planned_step("settle")
            event = trade._post_trade_event(key, name, day, lines, event_type)
            if trade.fund_id.trade_recognition == "settlement_date":
                trade.sudo().write({"event_id": event.id, "settlement_event_id": event.id, "state": "settled"})
            else:
                trade.sudo().write({"settlement_event_id": event.id, "state": "settled"})

    @api.model
    def _recognised(self, fund, day, instrument=None, portfolio=None):
        """Obchody, které jsou k datu v pozici fondu podle jeho nastavení."""
        # Stornovaný obchod není v pozici (rozhodnutí 2026-11-12 „Storno a oprava obchodu“). V pozici je jen obchod
        # s dokladem (rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“): návrh ani obchod fondu s pozicí od data
        # vypořádání, který ještě není vypořádaný, pozici nemění; ocenění na ně upozorní kontrolou trades_booked.
        domain = [("fund_id", "=", fund.id), ("trade_date", "<=", day), ("state", "!=", "reversed"), ("event_id", "!=", False)]
        if instrument:
            domain.append(("instrument_id", "=", instrument.id))
        if portfolio:
            domain.append(("portfolio_id", "=", portfolio.id))
        return self.search(domain).filtered(lambda t: t._recognition_date() <= day)

    @api.model
    def _holdings(self, fund, day):
        """Kusy po pozicích (nástroj, obchodní model) k datu; tentýž nástroj může být ve dvou modelech fondu."""
        quantities = {}
        for trade in self._recognised(fund, day):
            key = (trade.instrument_id, trade.portfolio_id)
            quantities[key] = quantities.get(key, 0.0) + trade.quantity
        return {key: qty for key, qty in quantities.items() if qty}

    @api.model
    def _positions(self, fund, day):
        """Kusy po nástrojích k datu, součet přes obchodní modely fondu."""
        quantities = {}
        for (instrument, _portfolio), qty in self._holdings(fund, day).items():
            quantities[instrument] = quantities.get(instrument, 0.0) + qty
        return {instrument: qty for instrument, qty in quantities.items() if qty}


class InvestraEntity(models.Model):
    _inherit = "investra.entity"

    @api.model_create_multi
    def create(self, vals_list):
        entities = super().create(vals_list)
        if entities.filtered(lambda e: e.entity_type == "manager"):
            entities._adopt_shared_instruments()
        return entities

    def write(self, vals):
        result = super().write(vals)
        if vals.get("entity_type") == "manager":
            self._adopt_shared_instruments()
        return result

    def _adopt_shared_instruments(self):
        """Sdílené nástroje založené před knihou investiční společnosti převezme tato kniha (rozhodnutí 2026-11-13)."""
        books = self.sudo().search([("entity_type", "=", "manager")])
        if len(books) == 1:
            orphans = self.env["investra.instrument"].sudo().with_context(active_test=False).search(
                [("fund_id", "=", False), ("company_id", "=", False)]
            )
            orphans.write({"company_id": books.company_id.id})


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    def write(self, vals):
        if "trade_recognition" in vals and self.env["investra.trade"].sudo().search_count([("fund_id", "in", self.ids)], limit=1):
            raise UserError(self.env._("Po prvním obchodu fondu nejde způsob zaúčtování změnit."))
        return super().write(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    investra_instrument_id = fields.Many2one("investra.instrument", string="Nástroj", ondelete="restrict", index="btree_not_null")
    # Odchylka od plánu klasifikace: zařazení není v integritním hashi. Přidání pole by změnilo hash všech dříve
    # zaúčtovaných dokladů a kontrola integrity by u nich selhala; po zaúčtování ho chrání zákaz změny níže.
    investra_classification_id = fields.Many2one(
        "investra.portfolio.classification", string="Zařazení", ondelete="restrict", index="btree_not_null",
    )

    def _get_integrity_hash_fields(self):
        base = super()._get_integrity_hash_fields()
        return base + ["investra_instrument_id"] if "investra_class_id" in base else base

    def write(self, vals):
        if {"investra_instrument_id", "investra_classification_id"} & set(vals) and self.filtered(lambda l: l.parent_state == "posted"):
            raise UserError(self.env._("Nástroj ani zařazení nejde po zaúčtování změnit."))
        return super().write(vals)
