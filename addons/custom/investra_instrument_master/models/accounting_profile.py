from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Účetní profil (plán docs/navrh-evidence-nastroju.md, oddíl 3.7): jen se vybírá a porovnává s rolí zařazení.
# Nic se neúčtuje a role zařazení se nepřepisuje.
PROFILE_STATE = [("ok", "V pořádku"), ("missing", "Není nastaven"), ("deviates", "Role se liší")]


class InvestraAccountingProfile(models.Model):
    _name = "investra.accounting.profile"
    _inherit = ["investra.codelist.mixin"]
    _description = "Účetní profil"

    # Profil odkazuje na roli účtu, ne na účet; role se do účtu knihy překládá až při účtování.
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", tracking=True, string="Role účtu")


class InvestraAccountingProfileAssignment(models.Model):
    _name = "investra.accounting.profile.assignment"
    _inherit = ["mail.thread"]
    _description = "Přiřazení účetního profilu"
    _order = "company_id, priority, id"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company", compute="_compute_company", store=True, readonly=False, required=True, precompute=True,
        index=True, tracking=True, string="Společnost",
    )
    portfolio_id = fields.Many2one(
        "investra.fund.portfolio", ondelete="restrict", index=True, tracking=True, string="Portfolio",
        help="Prázdné = pravidlo platí pro všechna portfolia společnosti.",
    )
    ba0088_id = fields.Many2one(
        "investra.ba0088.code", ondelete="restrict", tracking=True, string="Druh ČNB (BA0088)",
        domain="[('selectable', '=', True)]",
    )
    ba0088_group_id = fields.Many2one("investra.ba0088.group", ondelete="restrict", tracking=True, string="Skupina BA0088")
    accounting_profile_id = fields.Many2one(
        "investra.accounting.profile", required=True, ondelete="restrict", tracking=True, string="Účetní profil",
    )
    role_id = fields.Many2one(related="accounting_profile_id.role_id", string="Role účtu")
    priority = fields.Integer(default=10, tracking=True, string="Priorita", help="Nižší číslo má přednost.")
    valid_from = fields.Date(required=True, default=fields.Date.context_today, tracking=True, string="Platí od")
    valid_to = fields.Date(tracking=True, string="Platí do")
    note = fields.Text(string="Poznámka")

    @api.depends("portfolio_id")
    def _compute_company(self):
        for rec in self:
            rec.company_id = rec.portfolio_id.company_id or rec.company_id or self.env.company

    @api.depends("company_id", "portfolio_id", "ba0088_id", "ba0088_group_id", "accounting_profile_id")
    def _compute_display_name(self):
        for rec in self:
            scope = rec.ba0088_id.display_name or rec.ba0088_group_id.display_name or self.env._("všechny druhy")
            rec.display_name = f"{rec.portfolio_id.display_name or self.env._('všechna portfolia')} / {scope}"

    @api.constrains("ba0088_id", "ba0088_group_id")
    def _check_code_or_group(self):
        if any(rec.ba0088_id and rec.ba0088_group_id for rec in self):
            raise ValidationError(self.env._("Pravidlo má buď druh BA0088, nebo skupinu BA0088, ne obojí."))

    @api.constrains("valid_from", "valid_to")
    def _check_validity(self):
        for rec in self:
            if rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(self.env._("Platnost do nesmí být před platností od."))

    @api.constrains("company_id", "portfolio_id")
    def _check_portfolio_company(self):
        for rec in self.filtered("portfolio_id"):
            if rec.portfolio_id.company_id != rec.company_id:
                raise ValidationError(self.env._(
                    "Portfolio %(p)s patří jiné společnosti než pravidlo (%(c)s).",
                    p=rec.portfolio_id.display_name, c=rec.company_id.name,
                ))

    @api.constrains("company_id", "portfolio_id", "ba0088_id", "ba0088_group_id", "priority", "valid_from", "valid_to")
    def _check_overlap(self):
        for rec in self:
            domain = [
                ("id", "!=", rec.id), ("company_id", "=", rec.company_id.id), ("portfolio_id", "=", rec.portfolio_id.id),
                ("ba0088_id", "=", rec.ba0088_id.id), ("ba0088_group_id", "=", rec.ba0088_group_id.id),
                ("priority", "=", rec.priority),
            ]
            if rec.valid_to:
                domain.append(("valid_from", "<=", rec.valid_to))
            domain += ["|", ("valid_to", "=", False), ("valid_to", ">=", rec.valid_from)]
            other = self.sudo().search(domain, limit=1)
            if other:
                raise ValidationError(self.env._("Pro tuto kombinaci a prioritu už platí pravidlo %s.", other.display_name))

    @api.model
    def _select(self, company, portfolio, ba0088, day):
        """Pravidlo pro společnost, portfolio a druh CP k datu; prázdná množina = není nastaveno.

        Pořadí: priorita vzestupně, pak kód před skupinou před obecným, pak konkrétní portfolio před obecným.
        """
        day = fields.Date.to_date(day)
        group = ba0088.group_id
        rules = self.sudo().search([
            ("company_id", "=", company.id), ("valid_from", "<=", day),
            "|", ("valid_to", "=", False), ("valid_to", ">=", day),
            "|", ("portfolio_id", "=", False), ("portfolio_id", "=", portfolio.id),
        ]).filtered(lambda r: (
            (r.ba0088_id and r.ba0088_id == ba0088)
            or (r.ba0088_group_id and r.ba0088_group_id == group)
            or not (r.ba0088_id or r.ba0088_group_id)
        ))
        rules = rules.sorted(lambda r: (
            r.priority, 0 if r.ba0088_id else 1 if r.ba0088_group_id else 2, 0 if r.portfolio_id else 1, r.id,
        ))
        return rules[:1].with_env(self.env)


class InvestraFundPortfolioProfile(models.Model):
    _inherit = "investra.fund.portfolio"

    profile_assignment_ids = fields.One2many(
        "investra.accounting.profile.assignment", "portfolio_id", string="Přiřazení účetních profilů",
    )


class InvestraPortfolioClassificationProfile(models.Model):
    _inherit = "investra.portfolio.classification"

    accounting_profile_id = fields.Many2one(
        "investra.accounting.profile", compute="_compute_accounting_profile", string="Účetní profil",
        help="Vybraný podle společnosti, portfolia a druhu BA0088 nástroje. Jen se zobrazuje; neúčtuje se podle něj.",
    )
    profile_state = fields.Selection(PROFILE_STATE, compute="_compute_accounting_profile", string="Stav profilu")

    @api.depends(
        "portfolio_id", "company_id", "instrument_id.ba0088_id", "valid_from", "role_id",
        "portfolio_id.profile_assignment_ids.accounting_profile_id", "portfolio_id.profile_assignment_ids.priority",
        "portfolio_id.profile_assignment_ids.valid_from", "portfolio_id.profile_assignment_ids.valid_to",
    )
    def _compute_accounting_profile(self):
        for record in self:
            rule = record._profile_rule()
            profile = rule.accounting_profile_id
            record.accounting_profile_id = profile
            # Role zařazení se nepřepisuje, jen porovnává (plán oddíl 1 bod 10).
            record.profile_state = "missing" if not profile else "ok" if profile.role_id == record.role_id else "deviates"

    def _profile_rule(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        day = max(today, self.valid_from) if self.valid_from else today
        return self.env["investra.accounting.profile.assignment"]._select(
            self.company_id, self.portfolio_id, self.instrument_id.ba0088_id, day,
        )

    def _require_profile(self):
        """Účetní profil zařazení pro budoucí účtování; bez pravidla chyba."""
        self.ensure_one()
        profile = self._profile_rule().accounting_profile_id
        if not profile:
            raise UserError(self.env._(
                "Pro portfolio %(p)s a druh %(k)s není nastaven účetní profil.",
                p=self.portfolio_id.display_name, k=self.instrument_id.ba0088_id.display_name or self.env._("bez druhu"),
            ))
        return profile
