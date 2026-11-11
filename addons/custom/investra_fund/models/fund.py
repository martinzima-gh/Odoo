from odoo import api, fields, models
from odoo.exceptions import ValidationError


PRICE_ROUNDING = [("down", "Dolů"), ("half_up", "Matematicky"), ("up", "Nahoru")]
# Úpisy a odkupy (rozhodnutí „Úpisy a odkupy (bod 8 UX)“, 2026-11-11): parametry fondu, třída je při založení převezme
# a smí je přepsat – stejně jako desetinná místa kurzu.
ROUNDING_OWNER = [("fund", "Zůstává ve fondu"), ("investor", "Vrací se investorovi")]
FEE_RECIPIENT = [("manager", "Obhospodařovatel"), ("distributor", "Distributor")]
MOVEMENT_PARAMS = ("unit_digits", "unit_rounding", "rounding_owner", "entry_fee_rate", "exit_fee_rate", "fee_recipient")


class InvestraFund(models.Model):
    _name = "investra.fund"
    _description = "Fond"
    _order = "name"
    _check_company_auto = True

    name = fields.Char(related="entity_id.name", store=True)
    entity_id = fields.Many2one("investra.entity", required=True, ondelete="restrict", string="Účetní kniha")
    company_id = fields.Many2one(related="entity_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="entity_id.currency_id")
    class_ids = fields.One2many("investra.fund.class", "fund_id", string="Třídy")
    valuation_frequency = fields.Selection(
        [("daily", "Denně"), ("weekly", "Týdně"), ("monthly", "Měsíčně"), ("quarterly", "Čtvrtletně"), ("yearly", "Ročně")],
        required=True,
        default="monthly",
        string="Frekvence ocenění",
    )
    # Druhou osobu určuje schvalovací matice (rozhodnutí 2026-11-11); dřívější pole second_person_required
    # převedla migrace investra_nav 20.0.0.6.0, sloupec v databázi zůstává jen pro historii.
    manager_id = fields.Many2one(
        "investra.entity", ondelete="restrict", domain=[("entity_type", "=", "manager")], string="Obhospodařovatel",
        help="Investiční společnost; její schvalovací matice platí pro fond. Prázdné = výchozí matice.",
    )
    approval_matrix_ids = fields.One2many("investra.approval.matrix", "fund_id", string="Zpřísnění matice")
    price_digits = fields.Integer(default=4, required=True, string="Výchozí desetinná místa kurzu")
    price_rounding = fields.Selection(PRICE_ROUNDING, required=True, default="down", string="Výchozí zaokrouhlení kurzu")
    unit_digits = fields.Integer(default=6, required=True, string="Výchozí desetinná místa kusů")
    unit_rounding = fields.Selection(PRICE_ROUNDING, required=True, default="down", string="Výchozí zaokrouhlení kusů")
    rounding_owner = fields.Selection(
        ROUNDING_OWNER, required=True, default="fund", string="Výchozí: rozdíl ze zaokrouhlení kusů",
        help="Zůstává ve fondu = kapitál třídy; vrací se investorovi = závazek, výplatu zadává IS.",
    )
    entry_fee_rate = fields.Float(digits=(7, 4), default=0.0, string="Výchozí vstupní poplatek (%)", help="Sazba z hrubé platby úpisu.")
    exit_fee_rate = fields.Float(digits=(7, 4), default=0.0, string="Výchozí výstupní poplatek (%)", help="Sazba z hrubé částky odkupu (kusy × cena).")
    fee_recipient = fields.Selection(FEE_RECIPIENT, required=True, default="manager", string="Výchozí příjemce poplatku")
    trade_recognition = fields.Selection(
        [("trade_date", "Trade date accounting"), ("settlement_date", "Settlement date accounting")],
        required=True,
        default="trade_date",
        string="Zaúčtování obchodu",
        help="IFRS 9 odst. 3.1.2. Po prvním obchodu fondu nejde změnit.",
    )
    accrual_method = fields.Selection(
        [("eir", "Efektivní úroková míra"), ("linear", "Lineárně")],
        required=True,
        default="eir",
        string="Úročení nástrojů v naběhlé hodnotě",
    )
    accrual_note = fields.Char(string="Zdůvodnění lineárního úročení")
    calendar_ids = fields.One2many("investra.valuation.calendar", "fund_id", string="Kalendář ocenění")

    _entity_uniq = models.Constraint("unique(entity_id)", "Kniha může mít jen jeden fond.")

    @api.constrains("accrual_method", "accrual_note")
    def _check_accrual_note(self):
        for fund in self:
            if fund.accrual_method == "linear" and not fund.accrual_note:
                raise ValidationError(self.env._("Lineární úročení fondu musí mít zdůvodnění."))

    @api.constrains("manager_id")
    def _check_manager(self):
        for fund in self:
            if fund.manager_id and fund.manager_id.entity_type != "manager":
                raise ValidationError(self.env._("Obhospodařovatel musí být kniha druhu Investiční společnost."))

    @api.constrains("entity_id")
    def _check_entity_type(self):
        for fund in self:
            if fund.entity_id.entity_type not in ("fund", "subfund", "sicav"):
                raise ValidationError(self.env._("Fond musí stát na knize fondu, podfondu nebo SICAV."))


class InvestraFundClass(models.Model):
    _name = "investra.fund.class"
    _description = "Třída fondu"
    _order = "fund_id, sequence, code"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    code = fields.Char(required=True, string="Kód")
    name = fields.Char(required=True, string="Název")
    sequence = fields.Integer(default=10, string="Pořadí")
    active = fields.Boolean(default=True, string="Aktivní")
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Měna zveřejnění kurzu", help="V této měně se zveřejňuje kurz a probíhají úpisy a odkupy. NAV fondu a kapitál třídy zůstávají ve funkční měně."
    )
    isin = fields.Char(string="ISIN")
    price_digits = fields.Integer(required=True, string="Desetinná místa kurzu", help="Bez zadání platí hodnota fondu.")
    price_rounding = fields.Selection(PRICE_ROUNDING, required=True, string="Zaokrouhlení kurzu", help="Bez zadání platí hodnota fondu.")
    distribution = fields.Selection([("growth", "Růstová"), ("dividend", "Dividendová")], default="growth", required=True, string="Rozdělování výnosu")
    unit_digits = fields.Integer(required=True, string="Desetinná místa kusů", help="Bez zadání platí hodnota fondu.")
    unit_rounding = fields.Selection(PRICE_ROUNDING, required=True, string="Zaokrouhlení kusů", help="Bez zadání platí hodnota fondu.")
    rounding_owner = fields.Selection(ROUNDING_OWNER, required=True, string="Rozdíl ze zaokrouhlení kusů", help="Bez zadání platí hodnota fondu.")
    entry_fee_rate = fields.Float(digits=(7, 4), string="Vstupní poplatek (%)", help="Bez zadání platí hodnota fondu.")
    exit_fee_rate = fields.Float(digits=(7, 4), string="Výstupní poplatek (%)", help="Bez zadání platí hodnota fondu.")
    fee_recipient = fields.Selection(FEE_RECIPIENT, required=True, string="Příjemce poplatku", help="Bez zadání platí hodnota fondu.")

    _fund_code_uniq = models.Constraint("unique(fund_id, code)", "Kód třídy musí být ve fondu jedinečný.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            fund = self.env["investra.fund"].browse(vals.get("fund_id"))
            vals.setdefault("price_digits", fund.price_digits)
            vals.setdefault("price_rounding", fund.price_rounding)
            for name in MOVEMENT_PARAMS:
                vals.setdefault(name, fund[name])
        return super().create(vals_list)

    @api.depends("code", "fund_id.name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.fund_id.name} / {record.code}"

    @api.constrains("price_digits")
    def _check_digits(self):
        for record in self:
            if not 0 <= record.price_digits <= 18:
                raise ValidationError(self.env._("Počet desetinných míst kurzu musí být 0 až 18."))

    @api.constrains("unit_digits", "entry_fee_rate", "exit_fee_rate")
    def _check_movement_params(self):
        for record in self:
            # Kusy se ukládají na 6 desetinných míst (pohyb i výsledek ocenění).
            if not 0 <= record.unit_digits <= 6:
                raise ValidationError(self.env._("Počet desetinných míst kusů musí být 0 až 6."))
            if not (0 <= record.entry_fee_rate <= 100 and 0 <= record.exit_fee_rate <= 100):
                raise ValidationError(self.env._("Sazba poplatku musí být 0 až 100 %."))


class InvestraValuationCalendar(models.Model):
    _name = "investra.valuation.calendar"
    _description = "Plánované ocenění"
    _order = "date"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="cascade", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    date = fields.Date(required=True, string="Datum ocenění")
    published_on = fields.Date(string="Plánované zveřejnění")

    _fund_date_uniq = models.Constraint("unique(fund_id, date)", "Datum ocenění je v kalendáři už uvedené.")
