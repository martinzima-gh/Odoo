from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraAllocationScheme(models.Model):
    """Způsob rozdělení změny hodnoty mezi třídy, s platností od data.

    proportional: alokační poměr z předběžného kapitálu tříd.
    waterfall: pořadí nároků; rozdíl proti poměru se zaúčtuje jako přesun mezi třídami.
    """

    _name = "investra.allocation.scheme"
    _description = "Alokační schéma"
    _order = "fund_id, valid_from desc"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    valid_from = fields.Date(required=True)
    method = fields.Selection([("proportional", "Alokační poměr"), ("waterfall", "Pořadí nároků")], required=True, default="proportional")
    statute_ref = fields.Char(string="Článek statutu")
    line_ids = fields.One2many("investra.allocation.line", "scheme_id", string="Třídy")
    residual_pro_rata = fields.Float(digits=(6, 4), string="Část zbytku podle kapitálů")

    _uniq = models.Constraint("unique(fund_id, valid_from)", "Schéma s tímto datem už existuje.")

    @api.model
    def _for_date(self, fund, day):
        return self.search([("fund_id", "=", fund.id), ("valid_from", "<=", day)], order="valid_from desc", limit=1)


class InvestraAllocationLine(models.Model):
    _name = "investra.allocation.line"
    _description = "Nárok třídy"
    _order = "rank, id"

    scheme_id = fields.Many2one("investra.allocation.scheme", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="scheme_id.company_id", store=True, index=True)
    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict")
    rank = fields.Integer(default=1, string="Pořadí nároku", help="Třídy se stejným pořadím se dělí poměrem cílů.")
    target_rate = fields.Float(digits=(8, 6), string="Cílový výnos p. a.")
    residual_share = fields.Float(digits=(6, 4), string="Podíl na zbytku")
    loss_rank = fields.Integer(default=0, string="Pořadí ve ztrátě", help="0 znamená poměrem kapitálů; 1 nese ztrátu první.")

    @api.constrains("class_id", "scheme_id")
    def _check_class(self):
        for line in self:
            if line.class_id.fund_id != line.scheme_id.fund_id:
                raise ValidationError(self.env._("Třída musí patřit do fondu schématu."))
