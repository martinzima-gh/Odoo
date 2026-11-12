from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    @api.model
    def accounts_for(self, company, code):
        """Všechny účty role v knize (hlavní a další) pro zůstatky, výkazy a kontroly; účtuje se jen na hlavní."""
        mapping = self.env["investra.role.account"].sudo().search(
            [("company_id", "=", company.id), ("role_id.code", "=", code)], limit=1
        )
        return mapping.account_id | mapping.extra_account_ids

    @api.model
    def add_extra_account(self, company, code, account):
        """Přidá účet k roli jako další účet (např. nový bankovní deník). Bez mapování role nebo když účet už
        nějakou roli v knize má, nedělá nic (rozhodnutí 2026-11-12 „Role s více účty“)."""
        Mapping = self.env["investra.role.account"].sudo()
        mappings = Mapping.search([("company_id", "=", company.id)])
        mapping = mappings.filtered(lambda m: m.role_id.code == code)
        if not mapping or account in (mappings.account_id | mappings.extra_account_ids):
            return False
        mapping.extra_account_ids = [(4, account.id)]
        return True


class InvestraRoleAccount(models.Model):
    _name = "investra.role.account"
    _description = "Účet role v knize"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, string="Kniha")
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Role")
    account_id = fields.Many2one("account.account", required=True, ondelete="restrict", check_company=True, string="Účet",
                                 help="Hlavní účet role: na něj účtují pravidla účtování.")
    # Rozhodnutí 2026-11-12 „Role s více účty“: více bankovních účtů, platby na cestě. Zůstatky, výkazy ČNB a kontroly
    # sčítají hlavní i další účty; účtování jde jen na hlavní účet.
    extra_account_ids = fields.Many2many(
        "account.account", "investra_role_account_extra_rel", "mapping_id", "account_id",
        check_company=True, string="Další účty",
        help="Účty se stejným významem (např. další bankovní účty). Patří do zůstatku role ve výkazech a kontrolách.",
    )

    _company_role_uniq = models.Constraint(
        "unique(company_id, role_id)", "Role může mít v knize jen jedno mapování."
    )

    @api.constrains("account_id", "extra_account_ids", "company_id")
    def _check_account_single_role(self):
        """Účet smí v knize patřit jen jedné roli, jinak by se jeho zůstatek ve výkazech započetl dvakrát."""
        for company in self.company_id:
            mappings = self.search([("company_id", "=", company.id)])
            seen = {}
            for mapping in mappings:
                for account in mapping.account_id | mapping.extra_account_ids:
                    if account in seen and seen[account] != mapping:
                        raise ValidationError(self.env._(
                            "Účet %(account)s má v knize %(book)s dvě role: %(a)s a %(b)s.",
                            account=account.display_name, book=company.name,
                            a=seen[account].role_id.name, b=mapping.role_id.name,
                        ))
                    seen[account] = mapping
