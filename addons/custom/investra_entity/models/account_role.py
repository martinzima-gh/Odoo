from odoo import api, fields, models
from odoo.exceptions import UserError


class InvestraAccountRole(models.Model):
    """Význam účtu nezávislý na jeho čísle; pravidla účtování pracují s rolemi."""

    _name = "investra.account.role"
    _description = "Role účtu"
    _order = "code"

    code = fields.Char(required=True, string="Kód")
    name = fields.Char(required=True, string="Název")
    category = fields.Selection(
        [
            ("asset", "Aktivum"),
            ("liability", "Závazek"),
            ("equity", "Vlastní kapitál"),
            ("income", "Výnos"),
            ("expense", "Náklad"),
        ],
        required=True,
        string="Druh",
    )
    active = fields.Boolean(default=True, string="Aktivní")

    _code_uniq = models.Constraint("unique(code)", "Kód role musí být jedinečný.")

    @api.model
    def account_for(self, company, code):
        """Účet role v knize; chybějící mapování je chyba, ne tichý výchozí účet."""
        mapping = self.env["investra.role.account"].sudo().search(
            [("company_id", "=", company.id), ("role_id.code", "=", code)], limit=1
        )
        if not mapping:
            raise UserError(self.env._("Kniha %(book)s nemá účet pro roli %(role)s.", book=company.name, role=code))
        return mapping.account_id


class InvestraRoleAccount(models.Model):
    _name = "investra.role.account"
    _description = "Účet role v knize"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, string="Kniha")
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Role")
    account_id = fields.Many2one("account.account", required=True, ondelete="restrict", check_company=True, string="Účet")

    _company_role_uniq = models.Constraint(
        "unique(company_id, role_id)", "Role může mít v knize jen jeden účet."
    )
