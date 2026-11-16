from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Spot je stejná výměna měn jako forward, jen s krátkým vypořádáním; druh se volí při zadání (pokyn Martina 2026-11-15).
# Účtuje se na jiné účty než forward (role určí DE-03).
KIND = [("spot", "FX spot"), ("forward", "FX forward"), ("swap", "FX swap")]
ONE_LEG_KINDS = ("spot", "forward")
STATE = [("draft", "Návrh"), ("agreed", "Sjednáno"), ("settled", "Vypořádáno"), ("reversed", "Stornováno")]
LEG_STATE = [("open", "Otevřená"), ("settled", "Vypořádaná")]
# Stav a nástroj nastavuje jen systém (založení, sjednání, vypořádání, storno).
SYSTEM_DERIVATIVE_FIELDS = frozenset({
    "state", "instrument_id", "event_id", "reversal_reason", "settlement_reversal_reason",
})
SYSTEM_LEG_FIELDS = frozenset({"state", "b0", "buy_rate0", "sell_rate0", "settlement_event_id", "offbalance_event_id"})
# Obchodní údaje smlouvy a nohy; od stavu Sjednáno jsou jen ke čtení.
TERMS_FIELDS = {"fund_id", "portfolio_id", "partner_id", "kind", "trade_date", "contract_ref", "leg_ids"}
LEG_TERMS_FIELDS = {
    "derivative_id", "sequence", "settlement_date", "buy_currency_id", "buy_amount", "sell_currency_id", "sell_amount",
}


class InvestraDerivative(models.Model):
    """Smlouva o měnovém spotu, forwardu nebo swapu (docs/navrh-fx-derivaty.md, oddíl Evidence).

    Ke smlouvě vzniká 1 : 1 nástroj typu „Mimoburzovní derivát“, aby fungovalo portfolio, zařazení a výkazy.
    """

    _name = "investra.derivative"
    _inherit = ["investra.record.guard", "mail.thread"]
    _description = "FX derivát"
    _order = "trade_date desc, id desc"
    _book_fields = ("fund_id",)
    _system_fields = SYSTEM_DERIVATIVE_FIELDS

    name = fields.Char(compute="_compute_name", store=True, string="Název")
    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    functional_currency_id = fields.Many2one(related="fund_id.company_id.currency_id", string="Funkční měna")
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", index=True, string="Obchodní model",
        domain="[('fund_id', '=', fund_id)]",
    )
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", string="Protistrana", tracking=True)
    kind = fields.Selection(KIND, required=True, default="forward", string="Druh", tracking=True)
    trade_date = fields.Date(required=True, default=fields.Date.context_today, string="Datum sjednání", tracking=True)
    contract_ref = fields.Char(required=True, copy=False, string="Číslo smlouvy", tracking=True,
                               help="Číslo konfirmace nebo smlouvy; je i identifikátorem nástroje ve fondu.")
    state = fields.Selection(STATE, required=True, default="draft", readonly=True, copy=False, index=True, string="Stav",
                             tracking=True)
    instrument_id = fields.Many2one("investra.instrument", readonly=True, copy=False, ondelete="restrict", string="Nástroj")
    leg_ids = fields.One2many("investra.derivative.leg", "derivative_id", copy=True, string="Nohy")
    value_ids = fields.One2many("investra.derivative.value", "derivative_id", string="Ruční hodnoty")

    _instrument_uniq = models.UniqueIndex("(instrument_id) WHERE instrument_id IS NOT NULL", "Nástroj už patří jiné smlouvě.")

    # --- název -------------------------------------------------------------------------------------------------------

    def _pair_label(self):
        """Měnový pár „cizí/funkční“ a poslední datum vypořádání pro název smlouvy a nástroje."""
        self.ensure_one()
        legs = self.leg_ids.sorted(lambda leg: (leg.settlement_date or fields.Date.today(), leg.sequence))
        if not legs:
            return ""
        functional = self.fund_id.company_id.currency_id
        leg = legs[-1]
        foreign = leg.buy_currency_id if leg.sell_currency_id == functional else leg.sell_currency_id
        day = leg.settlement_date.strftime("%d.%m.%Y") if leg.settlement_date else ""
        return f"{foreign.name or '?'}/{functional.name or '?'} {day}".strip()

    @api.depends("kind", "fund_id", "leg_ids.settlement_date", "leg_ids.buy_currency_id", "leg_ids.sell_currency_id")
    def _compute_name(self):
        labels = dict(KIND)
        for derivative in self:
            derivative.name = f"{labels.get(derivative.kind, 'FX derivát')} {derivative._pair_label()}".strip()

    # --- kontroly ----------------------------------------------------------------------------------------------------

    @api.onchange("fund_id")
    def _onchange_fund_id(self):
        if self.fund_id and self.portfolio_id.fund_id != self.fund_id:
            self.portfolio_id = self.fund_id._default_portfolio()

    @api.constrains("fund_id", "portfolio_id")
    def _check_portfolio(self):
        for derivative in self:
            if derivative.portfolio_id.fund_id != derivative.fund_id:
                raise ValidationError(self.env._("Obchodní model nepatří fondu smlouvy."))

    @api.constrains("kind", "leg_ids", "trade_date", "fund_id")
    def _check_legs(self):
        for derivative in self:
            derivative._check_structure()

    @api.constrains("fund_id", "contract_ref")
    def _check_contract_ref(self):
        """Číslo smlouvy je identifikátor nástroje ve fondu; duplicitu ohlásit dřív než jedinečný index nástroje."""
        for derivative in self:
            domain = [("fund_id", "=", derivative.fund_id.id), ("contract_ref", "=", derivative.contract_ref),
                      ("id", "!=", derivative.id)]
            taken = self.env["investra.instrument"].sudo().search_count([
                ("fund_id", "=", derivative.fund_id.id), ("identifier_kind", "=", "contract"),
                ("identifier", "=", derivative.contract_ref), ("id", "!=", derivative.instrument_id.id)], limit=1)
            if taken or self.sudo().search_count(domain, limit=1):
                raise ValidationError(self.env._(
                    "Fond už má smlouvu nebo nástroj s číslem smlouvy %s.", derivative.contract_ref))

    def _check_structure(self):
        """Forward má jednu nohu, swap dvě opačné s rostoucím datem; jedna měna každé nohy je funkční měna fondu."""
        self.ensure_one()
        legs = self.leg_ids.sorted(lambda leg: (leg.settlement_date, leg.sequence, leg.id))
        if self.kind in ONE_LEG_KINDS and len(legs) != 1:
            raise ValidationError(self.env._("FX spot a FX forward musí mít právě jednu nohu (má %s).", len(legs)))
        if self.kind == "swap" and len(legs) != 2:
            raise ValidationError(self.env._("FX swap musí mít právě dvě nohy, blízkou a vzdálenou (má %s).", len(legs)))
        functional = self.fund_id.company_id.currency_id
        for leg in legs:
            if leg.settlement_date < self.trade_date:
                raise ValidationError(self.env._("Vypořádání nohy nemůže být před sjednáním smlouvy."))
            if functional not in (leg.buy_currency_id | leg.sell_currency_id):
                raise ValidationError(self.env._(
                    "Jedna z měn nohy musí být funkční měna fondu (%s); jiné měnové páry první verze nepodporuje.",
                    functional.name))
        if self.kind == "swap":
            near, far = legs
            if near.settlement_date >= far.settlement_date:
                raise ValidationError(self.env._("Vzdálená noha swapu musí mít pozdější datum vypořádání než blízká."))
            if near.buy_currency_id != far.sell_currency_id or near.sell_currency_id != far.buy_currency_id:
                raise ValidationError(self.env._(
                    "Nohy swapu musí mít opačný směr: měnu koupenou v blízké noze vzdálená noha prodává a naopak."))

    # --- založení, změny, mazání -----------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_DERIVATIVE_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav a nástroj smlouvy nastavuje jen systém."))
        for vals in vals_list:
            # Fond s jediným portfoliem: smlouva ho dostane sama, stejně jako obchod.
            if not vals.get("portfolio_id") and vals.get("fund_id"):
                vals["portfolio_id"] = self.env["investra.fund"].browse(vals["fund_id"])._default_portfolio().id
                if not vals["portfolio_id"]:
                    raise UserError(self.env._("Fond má víc obchodních modelů; vyberte, do kterého smlouva patří."))
        derivatives = super().create(vals_list)
        derivatives._check_contract_ref()
        for derivative in derivatives:
            derivative._create_instrument()
        return derivatives

    def _instrument_vals(self):
        """Nástroj fondu bez ISIN: identifikuje ho číslo smlouvy. Měna = funkční měna fondu, v níž se vede reálná hodnota."""
        self.ensure_one()
        return {
            "name": self.name,
            "type_id": self.env.ref("investra_instruments.type_derivative_otc").id,
            "fund_id": self.fund_id.id,
            "currency_id": self.fund_id.company_id.currency_id.id,
            "identifier_kind": "contract",
            "identifier": self.contract_ref,
            "counterparty_id": self.partner_id.id,
            "maturity_date": max(self.leg_ids.mapped("settlement_date"), default=False),
        }

    def _create_instrument(self):
        self.ensure_one()
        instrument = self.env["investra.instrument"].create(self._instrument_vals())
        self.sudo().instrument_id = instrument.id

    def _sync_instrument(self):
        """Návrh smlouvy: název, číslo smlouvy, protistrana a splatnost nástroje sledují smlouvu."""
        for derivative in self.filtered(lambda d: d.state == "draft" and d.instrument_id):
            vals = derivative._instrument_vals()
            derivative.instrument_id.write(
                {name: vals[name] for name in ("name", "identifier", "counterparty_id", "maturity_date")})

    def write(self, vals):
        if not self.env.su:
            if SYSTEM_DERIVATIVE_FIELDS & set(vals):
                raise UserError(self.env._("Stav a nástroj smlouvy nastavuje jen systém."))
            if TERMS_FIELDS & set(vals) and self.filtered(lambda d: d.state != "draft"):
                raise UserError(self.env._("Sjednanou, vypořádanou ani stornovanou smlouvu nejde změnit; opravte ji stornem."))
        result = super().write(vals)
        if TERMS_FIELDS & set(vals):
            # Kontrola čísla smlouvy před zápisem do nástroje (jinak by ji předběhl jedinečný index nástroje).
            self._check_contract_ref()
            self._sync_instrument()
        return result

    def unlink(self):
        if self.filtered(lambda d: d.state != "draft"):
            raise UserError(self.env._("Smazat jde jen smlouvu ve stavu Návrh; sjednanou opravte stornem."))
        instruments = self.instrument_id
        result = super().unlink()
        instruments.sudo().unlink()
        return result

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for vals, derivative in zip(vals_list, self):
            vals.setdefault("contract_ref", self.env._("%s (kopie)", derivative.contract_ref))
        return vals_list


class InvestraDerivativeLeg(models.Model):
    """Noha smlouvy: výměna dvou měn k datu vypořádání. Forward má jednu, swap blízkou a vzdálenou."""

    _name = "investra.derivative.leg"
    _inherit = ["investra.record.guard"]
    _description = "Noha FX derivátu"
    _order = "settlement_date, sequence, id"
    _book_fields = ("derivative_id",)
    _system_fields = SYSTEM_LEG_FIELDS

    derivative_id = fields.Many2one("investra.derivative", required=True, ondelete="cascade", index=True, string="Smlouva")
    company_id = fields.Many2one(related="derivative_id.company_id", store=True, index=True)
    sequence = fields.Integer(default=10, string="Pořadí")
    settlement_date = fields.Date(required=True, string="Datum vypořádání")
    buy_currency_id = fields.Many2one("res.currency", required=True, ondelete="restrict", string="Kupovaná měna")
    buy_amount = fields.Monetary(required=True, currency_field="buy_currency_id", string="Kupovaná částka")
    sell_currency_id = fields.Many2one("res.currency", required=True, ondelete="restrict", string="Prodávaná měna")
    sell_amount = fields.Monetary(required=True, currency_field="sell_currency_id", string="Prodávaná částka")
    rate = fields.Float(compute="_compute_rate", store=True, digits=(16, 6), string="Sjednaný kurz",
                        help="Funkční měna fondu za jednotku cizí měny, dopočtený z částek.")
    state = fields.Selection(LEG_STATE, required=True, default="open", readonly=True, copy=False, string="Stav nohy")

    @api.depends("buy_amount", "sell_amount", "buy_currency_id", "sell_currency_id", "derivative_id.fund_id")
    def _compute_rate(self):
        for leg in self:
            functional = leg.derivative_id.fund_id.company_id.currency_id
            if leg.buy_currency_id == functional and leg.sell_amount:
                leg.rate = leg.buy_amount / leg.sell_amount
            elif leg.sell_currency_id == functional and leg.buy_amount:
                leg.rate = leg.sell_amount / leg.buy_amount
            else:
                leg.rate = 0.0

    @api.constrains("buy_currency_id", "sell_currency_id", "buy_amount", "sell_amount")
    def _check_amounts(self):
        for leg in self:
            if leg.buy_currency_id == leg.sell_currency_id:
                raise ValidationError(self.env._("Kupovaná a prodávaná měna nohy se musí lišit."))
            if leg.buy_amount <= 0 or leg.sell_amount <= 0:
                raise ValidationError(self.env._("Částky nohy musí být kladné; směr určuje, která měna se kupuje a která prodává."))

    @api.constrains("derivative_id", "settlement_date", "buy_currency_id", "sell_currency_id")
    def _check_contract(self):
        for derivative in self.derivative_id:
            derivative._check_structure()

    def _check_editable(self, vals=None):
        if self.env.su:
            return
        if vals is not None and SYSTEM_LEG_FIELDS & set(vals):
            raise UserError(self.env._("Stav nohy a údaje ze sjednání nastavuje jen systém."))
        if (vals is None or LEG_TERMS_FIELDS & set(vals)) and self.derivative_id.filtered(lambda d: d.state != "draft"):
            raise UserError(self.env._("Nohy sjednané, vypořádané ani stornované smlouvy nejde změnit; opravte ji stornem."))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_LEG_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav nohy a údaje ze sjednání nastavuje jen systém."))
        legs = super().create(vals_list)
        legs._check_editable()
        legs.derivative_id._sync_instrument()
        return legs

    def write(self, vals):
        self._check_editable(vals)
        result = super().write(vals)
        if LEG_TERMS_FIELDS & set(vals):
            self.derivative_id._sync_instrument()
        return result

    def unlink(self):
        self._check_editable()
        return super().unlink()


class InvestraDerivativeValue(models.Model):
    """Ručně zadaná reálná hodnota smlouvy k datu ocenění (např. z potvrzení banky)."""

    _name = "investra.derivative.value"
    _inherit = ["investra.record.guard"]
    _description = "Ruční hodnota FX derivátu"
    _order = "date desc, id desc"
    _book_fields = ("derivative_id",)

    derivative_id = fields.Many2one("investra.derivative", required=True, ondelete="cascade", index=True, string="Smlouva")
    company_id = fields.Many2one(related="derivative_id.company_id", store=True, index=True)
    date = fields.Date(required=True, string="Datum ocenění")
    amount = fields.Monetary(required=True, currency_field="currency_id", string="Hodnota",
                             help="Reálná hodnota z pohledu fondu: kladná = pohledávka, záporná = závazek.")
    currency_id = fields.Many2one(
        "res.currency", required=True, ondelete="restrict", string="Měna",
        default=lambda self: self.env.company.currency_id,
    )
    source = fields.Char(required=True, string="Zdroj", help="Např. potvrzení banky, výpočet depozitáře.")
    reason = fields.Text(string="Důvod")
    document = fields.Binary(attachment=True, string="Příloha")
    document_name = fields.Char(string="Název přílohy")

    _derivative_date_uniq = models.Constraint("unique(derivative_id, date)", "Smlouva už má ruční hodnotu k tomuto datu.")

    @api.constrains("date", "derivative_id")
    def _check_date(self):
        for value in self:
            if value.date < value.derivative_id.trade_date:
                raise ValidationError(self.env._("Ruční hodnota nemůže být před datem sjednání smlouvy."))
