from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InvestraAllocationScheme(models.Model):
    """Způsob rozdělení změny hodnoty mezi třídy, s platností od data.

    proportional: alokační poměr z předběžného kapitálu tříd.
    waterfall: pořadí nároků; rozdíl proti poměru se zaúčtuje jako přesun mezi třídami.
    """

    _name = "investra.allocation.scheme"
    _inherit = ["mail.thread"]
    _description = "Alokační schéma"
    _order = "fund_id, valid_from desc"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, tracking=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    valid_from = fields.Date(required=True, tracking=True, string="Platí od")
    method = fields.Selection([("proportional", "Alokační poměr"), ("waterfall", "Pořadí nároků")], required=True, default="proportional", tracking=True, string="Metoda rozdělení")
    statute_ref = fields.Char(tracking=True, string="Článek statutu")
    line_ids = fields.One2many("investra.allocation.line", "scheme_id", string="Třídy")
    residual_pro_rata = fields.Float(digits=(6, 4), tracking=True, string="Část zbytku podle kapitálů")

    _uniq = models.Constraint("unique(fund_id, valid_from)", "Schéma s tímto datem už existuje.")

    @api.model
    def _for_date(self, fund, day):
        return self.search([("fund_id", "=", fund.id), ("valid_from", "<=", day)], order="valid_from desc", limit=1)


class InvestraAllocationLine(models.Model):
    _name = "investra.allocation.line"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Nárok třídy"
    _order = "rank, id"

    _line_tracking_parent = "scheme_id"

    scheme_id = fields.Many2one("investra.allocation.scheme", required=True, ondelete="cascade", string="Schéma")
    company_id = fields.Many2one(related="scheme_id.company_id", store=True, index=True)
    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict", tracking=True, string="Třída")
    rank = fields.Integer(default=1, tracking=True, string="Pořadí nároku", help="Třídy se stejným pořadím se dělí poměrem cílů.")
    target_rate = fields.Float(digits=(8, 6), tracking=True, string="Cílový výnos p. a.")
    residual_share = fields.Float(digits=(6, 4), tracking=True, string="Podíl na zbytku")
    loss_rank = fields.Integer(default=0, tracking=True, string="Pořadí ve ztrátě", help="0 znamená poměrem kapitálů; 1 nese ztrátu první.")

    def _line_tracking_desc(self):
        return self.env._("Nárok třídy %s", self.class_id.display_name or "–")

    @api.constrains("class_id", "scheme_id")
    def _check_class(self):
        for line in self:
            if line.class_id.fund_id != line.scheme_id.fund_id:
                raise ValidationError(self.env._("Třída musí patřit do fondu schématu."))
            if not line.class_id.shares_common:
                # ZJ-08 D1: třída bez podílu na společných položkách se na rozdělení výsledku nepodílí.
                raise ValidationError(self.env._(
                    "Třída %s se nepodílí na společných položkách, nemůže být v alokačním schématu.", line.class_id.display_name))


class InvestraFundClass(models.Model):
    _inherit = "investra.fund.class"

    @api.constrains("shares_common")
    def _check_shares_common_scheme(self):
        """ZJ-08 D1: třída na řádku alokačního schématu se musí podílet na společných položkách."""
        lines = self.env["investra.allocation.line"].sudo().search([("class_id", "in", self.filtered(lambda c: not c.shares_common).ids)], limit=1)
        if lines:
            raise ValidationError(self.env._(
                "Třída %s je v alokačním schématu; nejdřív ji ze schématu odeberte.", lines.class_id.display_name))
