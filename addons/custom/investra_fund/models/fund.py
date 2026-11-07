from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraFund(models.Model):
    _name = "investra.fund"
    _description = "Fond"
    _order = "name"
    _check_company_auto = True

    name = fields.Char(related="entity_id.name", store=True)
    entity_id = fields.Many2one("investra.entity", required=True, ondelete="restrict")
    company_id = fields.Many2one(related="entity_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="entity_id.currency_id")
    class_ids = fields.One2many("investra.fund.class", "fund_id", string="Třídy")
    valuation_frequency = fields.Selection(
        [("daily", "Denně"), ("weekly", "Týdně"), ("monthly", "Měsíčně"), ("quarterly", "Čtvrtletně"), ("yearly", "Ročně")],
        required=True,
        default="monthly",
    )
    second_person_required = fields.Boolean(default=True, string="Kontrola druhou osobou")
    calendar_ids = fields.One2many("investra.valuation.calendar", "fund_id", string="Kalendář ocenění")

    _entity_uniq = models.Constraint("unique(entity_id)", "Kniha může mít jen jeden fond.")

    @api.constrains("entity_id")
    def _check_entity_type(self):
        for fund in self:
            if fund.entity_id.entity_type not in ("fund", "subfund", "sicav"):
                raise ValidationError(self.env._("Fond musí stát na knize fondu, podfondu nebo SICAV."))


class InvestraFundClass(models.Model):
    _name = "investra.fund.class"
    _description = "Třída fondu"
    _order = "fund_id, sequence, code"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one("res.currency", required=True, string="Měna třídy")
    isin = fields.Char(string="ISIN")
    price_digits = fields.Integer(default=4, required=True, string="Desetinná místa kurzu")
    price_rounding = fields.Selection(
        [("down", "Dolů"), ("half_up", "Matematicky")], required=True, default="down"
    )
    distribution = fields.Selection([("growth", "Růstová"), ("dividend", "Dividendová")], default="growth", required=True)

    _fund_code_uniq = models.Constraint("unique(fund_id, code)", "Kód třídy musí být ve fondu jedinečný.")

    @api.depends("code", "fund_id.name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.fund_id.name} / {record.code}"

    @api.constrains("price_digits")
    def _check_digits(self):
        for record in self:
            if not 0 <= record.price_digits <= 18:
                raise ValidationError(self.env._("Počet desetinných míst kurzu musí být 0 až 18."))


class InvestraValuationCalendar(models.Model):
    _name = "investra.valuation.calendar"
    _description = "Plánované ocenění"
    _order = "date"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    date = fields.Date(required=True)
    published_on = fields.Date(string="Plánované zveřejnění")

    _fund_date_uniq = models.Constraint("unique(fund_id, date)", "Datum ocenění je v kalendáři už uvedené.")
