"""Dividenda jako záznam s ex-datem, srážkou a zápočtem (ZJ-19, dávka ZJ-07 až ZJ-19, oddíl 7, H1 a D14).

Výnos patří tomu, kdo drží k večeru dne před ex-datem (`Trade._holdings(fund, ex_date − 1 den)`). Dividenda se zaúčtuje
k ex-datu: výnos na 714100 (česká), 714200 (zahraniční), 714300 (z dceřiné společnosti), sražená daň u české na 681100
a u zahraniční započitatelná část na 681400, přeplatek nad smluvní sazbou na pohledávku k vrácení nebo do nákladů,
čistá pohledávka z dividendy. Výplata (datum výplaty) přesune pohledávku do banky a vyúčtuje kurzový rozdíl.
Výpočet daně tak dostane účty správně bez ručních dokladů (ruční doklady dál fungují).
"""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import engine

KINDS = [("domestic", "Česká"), ("foreign", "Zahraniční"), ("subsidiary", "Z dceřiné společnosti")]
# Účty výnosu podle druhu a účty daně a pohledávek (analytické účty šablony investra_chart_fund, další účty rolí).
INCOME_ACCOUNT = {"domestic": "714100", "foreign": "714200", "subsidiary": "714300"}
WITHHOLDING_DOMESTIC, WITHHOLDING_CREDITABLE = "681100", "681400"
RECEIVABLE_DIVIDEND, RECEIVABLE_TAX_REFUND = "341210", "341220"
DEFAULT_DOMESTIC_WITHHOLDING = 15.0  # § 36/2 ZDP, srážka 15 % u tuzemských dividend (konečná)
DEFAULT_TREATY_RATE = 15.0


def d(value):
    return Decimal(str(value or 0))


class InvestraDividend(models.Model):
    _name = "investra.dividend"
    _inherit = ["investra.record.guard", "investra.posting.preview", "mail.thread"]
    _description = "Dividenda"
    _order = "ex_date desc, id desc"
    _book_fields = ("fund_id",)
    _system_fields = frozenset({"event_id", "pay_event_id", "state", "reversal_reason"})

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond", tracking=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one(
        "investra.instrument", required=True, ondelete="restrict", string="Nástroj", tracking=True,
        domain="[('type_id.kind', 'in', ('equity', 'fund', 'participation'))]",
        help="Akcie, podílový list nebo účast; dividendu vyplácí nástroj bez splátkového kalendáře.",
    )
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", required=True, ondelete="restrict", string="Portfolio", tracking=True,
        domain="[('id', 'in', allowed_portfolio_ids)]",
        help="Nabízí se portfolia, která držela nástroj k večeru dne před ex-datem.",
    )
    allowed_portfolio_ids = fields.Many2many("investra.fund.portfolio", compute="_compute_allowed", string="Portfolia s nárokem")
    portfolio_class_id = fields.Many2one(related="portfolio_id.class_id", string="Třída portfolia")
    ex_date = fields.Date(required=True, string="Ex-datum", tracking=True,
                          help="Od tohoto dne se obchoduje bez dividendy; nárok má držitel k večeru dne před ex-datem.")
    pay_date = fields.Date(string="Datum výplaty", tracking=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency", store=True, readonly=False, precompute=True, string="Měna dividendy",
                                  tracking=True, help="Výchozí měna nástroje.")
    units = fields.Float(compute="_compute_units", store=True, readonly=False, precompute=True, digits=(20, 6), string="Kusy s nárokem",
                         help="Kusy držené k večeru dne před ex-datem v portfoliu; jde snížit, ne zvýšit.")
    per_share = fields.Float(digits=(20, 8), string="Hrubá dividenda na kus", tracking=True)
    gross_amount = fields.Float(compute="_compute_gross", store=True, precompute=True, digits=(20, 2), string="Hrubá dividenda")
    kind = fields.Selection(KINDS, compute="_compute_kind", store=True, readonly=False, precompute=True, string="Druh dividendy",
                            tracking=True, help="Podle země emitenta: česká nebo zahraniční; z dceřiné společnosti jen ručně.")
    withholding_rate = fields.Float(compute="_compute_withholding_rate", store=True, readonly=False, precompute=True, digits=(16, 4),
                                    string="Sražená sazba %", tracking=True)
    withheld_amount = fields.Float(compute="_compute_withheld", store=True, readonly=False, precompute=True, digits=(20, 2), string="Sražená daň")
    treaty_rate = fields.Float(default=DEFAULT_TREATY_RATE, digits=(16, 4), string="Smluvní sazba %", tracking=True,
                               help="Jen zahraniční dividenda: sazba podle smlouvy o zamezení dvojího zdanění; "
                                    "daň do této výše je započitatelná.")
    creditable_amount = fields.Float(compute="_compute_creditable", store=True, readonly=False, precompute=True, digits=(20, 2),
                                     string="Započitatelná daň", help="Část sražené daně do smluvní sazby; u české dividendy celá srážka.")
    excess_amount = fields.Float(compute="_compute_excess", digits=(20, 2), string="Přeplatek nad smluvní sazbou")
    excess_treatment = fields.Selection(
        [("receivable", "Pohledávka k vrácení"), ("expense", "Náklad")], default="receivable", required=True,
        string="Přeplatek daně", help="Co se sraženou daní nad započitatelnou částku: pohledávka za zahraničním správcem daně, nebo náklad.")
    net_amount = fields.Float(compute="_compute_excess", digits=(20, 2), string="Čistá dividenda")
    foreign_currency = fields.Boolean(compute="_compute_foreign_currency", string="Dividenda v cizí měně")
    fx_rate = fields.Float(default=1, digits=(16, 6), required=True, string="Kurz k ex-datu",
                           help="Funkční měna za jednotku měny dividendy.")
    pay_fx_rate = fields.Float(digits=(16, 6), string="Kurz k výplatě", help="Prázdné = kurz k ex-datu (bez kurzového rozdílu).")
    state = fields.Selection(
        [("draft", "Návrh"), ("booked", "Zaúčtováno k ex-datu"), ("paid", "Vyplaceno"), ("reversed", "Stornováno")],
        required=True, default="draft", readonly=True, index=True, copy=False, string="Stav", tracking=True,
    )
    event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Účetní událost")
    pay_event_id = fields.Many2one("investra.accounting.event", readonly=True, copy=False, string="Událost výplaty")
    reversal_reason = fields.Text(readonly=True, copy=False, string="Důvod storna")
    note = fields.Char(string="Poznámka")

    # --- předvyplnění a výpočty --------------------------------------------------------------------------------

    @api.depends("fund_id", "instrument_id", "ex_date")
    def _compute_allowed(self):
        for dividend in self:
            portfolios = [p.id for (i, p) in dividend._holdings() if i == dividend.instrument_id._origin]
            dividend.allowed_portfolio_ids = [(6, 0, portfolios)]

    def _entitlement_day(self):
        return self.ex_date - timedelta(days=1) if self.ex_date else False

    def _holdings(self):
        """Pozice fondu (nástroj, portfolio) k večeru dne před ex-datem."""
        self.ensure_one()
        day = self._entitlement_day()
        if not (self.fund_id and day):
            return {}
        return self.env["investra.trade"].sudo()._holdings(self.fund_id._origin.sudo(), day)

    @api.depends("instrument_id")
    def _compute_currency(self):
        for dividend in self:
            dividend.currency_id = dividend.instrument_id.currency_id

    @api.depends("currency_id", "fund_id")
    def _compute_foreign_currency(self):
        for dividend in self:
            dividend.foreign_currency = bool(dividend.currency_id and dividend.fund_id
                                             and dividend.currency_id != dividend.fund_id.currency_id)

    @api.depends("fund_id", "instrument_id", "portfolio_id", "ex_date")
    def _compute_units(self):
        for dividend in self:
            key = (dividend.instrument_id._origin, dividend.portfolio_id._origin)
            dividend.units = float(dividend._holdings().get(key, 0.0)) if dividend.portfolio_id else 0.0

    @api.depends("units", "per_share")
    def _compute_gross(self):
        for dividend in self:
            dividend.gross_amount = float((d(dividend.units) * d(dividend.per_share)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def _origin_kind(self):
        """Druh podle země emitenta: CZ → česká, jinak zahraniční. Emitent z modulu Instrument master, bez něj země z ISIN."""
        self.ensure_one()
        instrument = self.instrument_id
        country = ""
        if "issuer_id" in instrument._fields and instrument.issuer_id.country_id:
            country = instrument.issuer_id.country_id.code or ""
        elif instrument.isin:
            country = instrument.isin[:2]
        return "foreign" if country and country != "CZ" else "domestic"

    @api.depends("instrument_id")
    def _compute_kind(self):
        for dividend in self:
            if dividend.instrument_id and dividend.kind != "subsidiary":
                dividend.kind = dividend._origin_kind()
            elif not dividend.kind:
                dividend.kind = "domestic"

    @api.depends("kind", "instrument_id")
    def _compute_withholding_rate(self):
        for dividend in self:
            dividend.withholding_rate = DEFAULT_DOMESTIC_WITHHOLDING if dividend._tax_is_domestic() else 0.0

    def _tax_is_domestic(self):
        """Sražená daň se účtuje jako česká srážková: česká dividenda, nebo dividenda z tuzemské dceřiné společnosti."""
        self.ensure_one()
        return self.kind == "domestic" or (self.kind == "subsidiary" and self._origin_kind() == "domestic")

    @api.depends("gross_amount", "withholding_rate")
    def _compute_withheld(self):
        for dividend in self:
            dividend.withheld_amount = float((d(dividend.gross_amount) * d(dividend.withholding_rate) / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP))

    @api.depends("withheld_amount", "gross_amount", "treaty_rate", "kind", "instrument_id")
    def _compute_creditable(self):
        for dividend in self:
            if dividend._tax_is_domestic():
                dividend.creditable_amount = dividend.withheld_amount
            else:
                limit = (d(dividend.gross_amount) * d(dividend.treaty_rate) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                dividend.creditable_amount = float(min(d(dividend.withheld_amount), limit))

    @api.depends("gross_amount", "withheld_amount", "creditable_amount")
    def _compute_excess(self):
        for dividend in self:
            dividend.excess_amount = float(d(dividend.withheld_amount) - d(dividend.creditable_amount))
            dividend.net_amount = float(d(dividend.gross_amount) - d(dividend.withheld_amount))

    @api.onchange("fund_id", "instrument_id", "ex_date", "pay_date")
    def _onchange_defaults(self):
        for dividend in self:
            if not (dividend.fund_id and dividend.instrument_id):
                continue
            allowed = dividend.allowed_portfolio_ids._origin
            if dividend.portfolio_id._origin not in allowed:
                dividend.portfolio_id = allowed if len(allowed) == 1 else False
            if not dividend.foreign_currency:
                dividend.fx_rate, dividend.pay_fx_rate = 1, 0
                continue
            for name, day in (("fx_rate", dividend.ex_date), ("pay_fx_rate", dividend.pay_date)):
                if not day:
                    continue
                try:
                    dividend[name] = float(dividend.fund_id._fx_at(dividend.currency_id, day))
                except UserError:
                    dividend[name] = 0.0  # chybějící kurz formulář nezastaví, zaúčtování ho vyžaduje

    # --- kontroly ---------------------------------------------------------------------------------------------

    @api.constrains("per_share", "units", "withholding_rate", "treaty_rate", "withheld_amount", "creditable_amount",
                    "gross_amount", "ex_date", "pay_date", "fx_rate", "pay_fx_rate")
    def _check_amounts(self):
        for dividend in self:
            if dividend.per_share < 0 or dividend.units < 0:
                raise ValidationError(self.env._("Dividenda na kus a kusy nesmí být záporné."))
            if not 0 <= dividend.withholding_rate <= 100 or not 0 <= dividend.treaty_rate <= 100:
                raise ValidationError(self.env._("Sazby jsou v procentech od 0 do 100."))
            if dividend.withheld_amount < 0 or dividend.creditable_amount < 0:
                raise ValidationError(self.env._("Sražená a započitatelná daň nesmí být záporná."))
            if dividend.pay_date and dividend.ex_date and dividend.pay_date < dividend.ex_date:
                raise ValidationError(self.env._("Datum výplaty nemůže být před ex-datem."))
            if dividend.fx_rate < 0 or dividend.pay_fx_rate < 0:
                raise ValidationError(self.env._("Kurz nesmí být záporný."))

    def _validate(self):
        """Kontroly před zaúčtováním: nárok z pozice k ex-datu − 1, zařazení, kurz."""
        self.ensure_one()
        if not self.gross_amount:
            raise UserError(self.env._("Dividenda nemá hrubou částku: doplňte dividendu na kus a kusy s nárokem."))
        if d(self.withheld_amount) > d(self.gross_amount):
            raise UserError(self.env._("Sražená daň je vyšší než hrubá dividenda."))
        if d(self.creditable_amount) > d(self.withheld_amount):
            raise UserError(self.env._("Započitatelná daň je vyšší než sražená."))
        if self.portfolio_id.fund_id != self.fund_id:
            raise UserError(self.env._("Portfolio nepatří fondu dividendy."))
        held = self._holdings().get((self.instrument_id, self.portfolio_id), 0.0)
        if held <= 0:
            raise UserError(self.env._(
                "Fond k večeru dne před ex-datem (%(day)s) nedržel nástroj %(name)s v portfoliu %(portfolio)s; dividenda mu nepatří.",
                day=self._entitlement_day(), name=self.instrument_id.name, portfolio=self.portfolio_id.name))
        if self.units > held + 1e-9:
            raise UserError(self.env._(
                "Kusy s nárokem %(units)s jsou víc, než fond k %(day)s držel (%(held)s).",
                units=self.units, day=self._entitlement_day(), held=held))
        if not self._classification():
            raise UserError(self.env._(
                "Nástroj %(name)s nemá v portfoliu %(portfolio)s k %(day)s zařazení.",
                name=self.instrument_id.name, portfolio=self.portfolio_id.name, day=self.ex_date))
        if self.foreign_currency and not self.fx_rate:
            raise UserError(self.env._("Chybí kurz k ex-datu."))

    def _classification(self):
        self.ensure_one()
        return self.env["investra.portfolio.classification"]._valid(self.portfolio_id._origin, self.instrument_id._origin, self.ex_date)

    def _check_valuation_lock(self, what, day=None):
        """Zámek ocenění jako u splátky: datum v ocenění Ke schválení až Potvrzeno."""
        self.ensure_one()
        day = day or self.ex_date
        Valuation = self.env["investra.valuation"]
        locking = Valuation._locking(self.company_id, day)
        if locking:
            Valuation._raise_locked(locking, day, what)

    # --- životní cyklus záznamu -------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(set(vals) & self._system_fields for vals in vals_list):
            raise UserError(self.env._("Stav, účetní události a důvod storna nastavuje jen zaúčtování a storno."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and (set(vals) & self._system_fields or self.filtered(lambda r: r.state != "draft")):
            raise UserError(self.env._("Zaúčtovanou dividendu nejde změnit; opravte ji stornem."))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda r: r.state != "draft" or r.event_id):
            raise UserError(self.env._("Zaúčtovanou dividendu nejde smazat; opravte ji stornem."))
        return super().unlink()

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for vals in vals_list:
            for name in self._system_fields:
                vals.pop(name, None)
        return vals_list

    def _require_preparer(self):
        if not self.env.user.has_group("investra_entity.group_valuation_preparer"):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        self.check_access("write")

    # --- účtování ---------------------------------------------------------------------------------------------

    def _account(self, code, role):
        """Analytický účet role v knize fondu podle kódu; chybějící účet je chyba s návodem."""
        self.ensure_one()
        account = self.env["investra.account.role"].sudo().accounts_for(self.company_id, role).filtered(lambda a: a.code == code)[:1]
        if not account:
            raise UserError(self.env._(
                "Kniha %(book)s nemá účet %(code)s. Přidejte ho k roli (Účty rolí) nebo povyšte modul Investra Chart Fund.",
                book=self.company_id.name, code=code))
        return account

    def _line(self, role, amount, account=None, amount_ccy=None, **values):
        """Řádek dokladu; částka v měně dividendy jen u cizí měny a rozvahových řádků."""
        self.ensure_one()
        extra = {"investra_instrument_id": self.instrument_id.id, "investra_classification_id": self._classification().id}
        if account:
            extra["account_id"] = account.id
        line = {"role": role, "amount": amount, "movement_type": values.pop("movement_type", "transaction"), "extra": extra,
                "name": values.pop("name", self.env._("Dividenda %s", self.instrument_id.name)), **values}
        if amount_ccy is not None and self.foreign_currency:
            line.update(currency_id=self.currency_id.id, amount_currency=amount_ccy)
        return line

    def _book_lines(self):
        """Řádky dokladu k ex-datu (volá je zaúčtování i náhled): výnos, daň, přeplatek a čistá pohledávka."""
        self.ensure_one()
        round_ = self.company_id.currency_id.round
        fx = self.fx_rate or 1.0
        gross, withheld, creditable = self.gross_amount, self.withheld_amount, self.creditable_amount
        excess = float(d(withheld) - d(creditable))
        gross_c = round_(gross * fx)
        creditable_c = round_(creditable * fx)
        excess_c = round_(excess * fx)
        # Čistá pohledávka dopočtem, aby doklad vyšel na haléř.
        net_c = round_(gross_c - creditable_c - excess_c)
        net = float(d(gross) - d(withheld))
        kind = self.kind
        lines = [self._line("income_dividend", -gross_c, account=self._account(INCOME_ACCOUNT[kind], "income_dividend"),
                            name=self.env._("Dividenda %s", self.instrument_id.name), movement_type="dividend")]
        if creditable_c or creditable:
            tax_code = WITHHOLDING_DOMESTIC if self._tax_is_domestic() else WITHHOLDING_CREDITABLE
            lines.append(self._line("expense_tax", creditable_c, account=self._account(tax_code, "expense_tax"),
                                    name=self.env._("Srážková daň z dividendy %s", self.instrument_id.name), movement_type="dividend"))
        if excess_c or excess:
            if self.excess_treatment == "receivable":
                lines.append(self._line("receivable_other", excess_c, account=self._account(RECEIVABLE_TAX_REFUND, "receivable_other"),
                                        amount_ccy=excess, name=self.env._("Daň k vrácení z dividendy %s", self.instrument_id.name),
                                        movement_type="dividend"))
            else:
                lines.append(self._line("expense_other", excess_c, name=self.env._("Nezapočitatelná daň z dividendy %s", self.instrument_id.name),
                                        movement_type="dividend"))
        lines.append(self._line("receivable_other", net_c, account=self._account(RECEIVABLE_DIVIDEND, "receivable_other"),
                                amount_ccy=net, name=self.env._("Pohledávka z dividendy %s", self.instrument_id.name),
                                movement_type="dividend"))
        return lines

    def _pay_lines(self):
        """Řádky výplaty: banka proti pohledávce z dividendy, kurzový rozdíl na zisk nebo ztrátu z kurzu."""
        self.ensure_one()
        round_ = self.company_id.currency_id.round
        fx = self.fx_rate or 1.0
        pay_fx = self.pay_fx_rate or fx
        net = float(d(self.gross_amount) - d(self.withheld_amount))
        gross_c = round_(self.gross_amount * fx)
        booked_c = round_(gross_c - round_(self.creditable_amount * fx) - round_((self.withheld_amount - self.creditable_amount) * fx))
        received_c = round_(net * pay_fx)
        lines = [
            {"role": "bank", "amount": received_c, "movement_type": "transaction", "name": self.env._("Výplata dividendy %s", self.instrument_id.name),
             **({"currency_id": self.currency_id.id, "amount_currency": net} if self.foreign_currency else {})},
            self._line("receivable_other", -booked_c, account=self._account(RECEIVABLE_DIVIDEND, "receivable_other"),
                       amount_ccy=-net, name=self.env._("Výplata dividendy %s", self.instrument_id.name), movement_type="dividend"),
        ]
        difference = round_(received_c - booked_c)
        if difference:
            lines.append(self._line("gain_fx" if difference > 0 else "loss_fx", -difference, movement_type="fx_realised",
                                    name=self.env._("Kurzový rozdíl z výplaty dividendy %s", self.instrument_id.name)))
        return lines

    def _post_event(self, key, name, day, lines, event_type):
        event = self.env["investra.accounting.event"]._create_event(self.company_id, key, name, day, event_type, lines, source=self)
        event._lock_events()
        event._post_events()
        return event

    def action_book(self):
        """Zaúčtuje dividendu k ex-datu."""
        self._require_preparer()
        for dividend in self.sudo().filtered(lambda r: r.state == "draft"):
            dividend._validate()
            dividend._check_valuation_lock(self.env._("Zaúčtování dividendy"))
            event = dividend._post_event(f"dividend:{dividend.id}", self.env._("Dividenda %s", dividend.instrument_id.name),
                                         dividend.ex_date, dividend._book_lines(), "dividend")
            dividend.write({"event_id": event.id, "state": "booked"})
        return True

    def action_pay(self):
        """Zaplaceno: banka proti pohledávce z dividendy k datu výplaty."""
        self._require_preparer()
        for dividend in self.sudo():
            if dividend.state != "booked":
                raise UserError(self.env._("Zaplatit jde jen dividendu zaúčtovanou k ex-datu."))
            if not dividend.pay_date:
                raise UserError(self.env._("Doplňte datum výplaty."))
            if dividend.foreign_currency and not (dividend.pay_fx_rate or dividend.fx_rate):
                raise UserError(self.env._("Chybí kurz k výplatě."))
            dividend._check_valuation_lock(self.env._("Výplata dividendy"), dividend.pay_date)
            event = dividend._post_event(f"dividend-pay:{dividend.id}", self.env._("Výplata dividendy %s", dividend.instrument_id.name),
                                         dividend.pay_date, dividend._pay_lines(), "dividend_payment")
            dividend.write({"pay_event_id": event.id, "state": "paid"})
        return True

    def action_reverse(self, reason):
        """Storno dividendy: nejdřív doklad výplaty, potom doklad k ex-datu. Stav Stornováno.

        Odchylka od plánu: bez schvalovací matice (nová činnost matice by zasáhla ZJ-01/02); vyžaduje roli přípravy a důvod."""
        self._require_preparer()
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod."))
        for dividend in self.sudo():
            if dividend.state not in ("booked", "paid"):
                raise UserError(self.env._("Stornovat jde jen zaúčtovanou dividendu."))
            dividend._check_valuation_lock(self.env._("Storno dividendy"))
            if dividend.pay_event_id:
                dividend._check_valuation_lock(self.env._("Storno výplaty dividendy"), dividend.pay_date)
                dividend.pay_event_id._reverse_events()
            dividend.event_id._reverse_events()
            dividend.write({"state": "reversed", "reversal_reason": reason})
        return self

    # --- náhled zaúčtování ------------------------------------------------------------------------------------

    @api.depends("state", "fund_id", "instrument_id", "portfolio_id", "ex_date", "pay_date", "units", "per_share", "kind",
                 "withholding_rate", "withheld_amount", "creditable_amount", "excess_treatment", "fx_rate", "pay_fx_rate",
                 "event_id", "event_id.state", "pay_event_id", "pay_event_id.state")
    def _compute_posting_preview(self):
        for dividend in self:
            dividend.posting_preview = dividend._posting_preview_html()

    def _ready_for_preview(self):
        return bool(self.state in ("draft", "booked") and self.fund_id and self.instrument_id and self.portfolio_id and self.ex_date
                    and self.gross_amount)

    def _preview_documents(self):
        """Doklady, které vzniknou tlačítky Zaúčtovat a Zaplaceno; stejné kontroly a řádky jako účtování."""
        self.ensure_one()
        documents = []
        if self.state == "draft":
            self._validate()
            documents.append((self.env._("Při zaúčtování k ex-datu"), self.ex_date, self._preview_rows(self._book_lines())))
        if self.pay_date:
            documents.append((self.env._("Při výplatě"), self.pay_date, self._preview_rows(self._pay_lines())))
        return documents

    def _preview_currency(self):
        return self.currency_id if self.foreign_currency else self.env["res.currency"]

    def _booked_intro(self):
        return self.env._("Zaúčtované doklady dividendy.")

    def _booked_caption(self, event):
        return {"dividend": self.env._("Dividenda k ex-datu"), "dividend_payment": self.env._("Výplata")}.get(event.event_type, event.name)

    def _preview_intro(self):
        return self.env._("Jen náhled: nic se neúčtuje. Doklad k ex-datu vznikne tlačítkem Zaúčtovat, výplata tlačítkem Zaplaceno.")
