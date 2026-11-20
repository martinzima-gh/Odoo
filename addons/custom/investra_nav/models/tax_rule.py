"""Daňová pravidla a výjimky fondu (ZJ-07, dávka ZJ-07 až ZJ-19, oddíl 9.3 C2, rozhodnutí D1–D14).

Pravidla jsou sdílená pro všechny fondy (Nastavení › Daně › Daňová pravidla); každé má sazby s platností od data, kód účtu daně
(výsledovka, u odložené daně z přecenění do kapitálu vlastní kapitál), kód rozvahového účtu (347… splatná, 348… odložená) a u splatné
daně volitelně účet zahraniční daně k zápočtu. Přiřazení účtů k pravidlům je na úrovni fondu: výchozí pravidlo fondu pro všechny
výsledkové účty a tabulka výjimek (účet → pravidlo). V tomto běhu jen modely, kontroly a data; výpočet daně přijde s enginem.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

TAX_KINDS = [("general", "Obecný základ"), ("separate", "Samostatný základ"), ("exempt", "Mimo základ daně")]
TAX_METHODS = [("current", "Splatná – výsledek od začátku účetního období"), ("deferred", "Odložená – zůstatek k datu")]


class InvestraTaxRule(models.Model):
    _name = "investra.tax.rule"
    _inherit = ["mail.thread"]
    _description = "Daňové pravidlo"
    _order = "kind, name"

    name = fields.Char(required=True, tracking=True, string="Název")
    active = fields.Boolean(default=True, tracking=True, string="Aktivní")
    kind = fields.Selection(TAX_KINDS, required=True, default="general", tracking=True, string="Druh")
    method = fields.Selection(TAX_METHODS, default="current", tracking=True, string="Způsob")
    tax_account_code = fields.Char(
        tracking=True, string="Účet daně",
        help="Kód účtu v knize fondu: náklad na daň (681…, 682…), u odložené daně z přecenění do kapitálu účet vlastního kapitálu.")
    balance_account_code = fields.Char(tracking=True, string="Rozvahový účet", help="Kód účtu závazku: 347… splatná, 348… odložená.")
    credit_account_code = fields.Char(
        tracking=True, string="Započíst daň z účtu",
        help="Zahraniční daň k zápočtu (681400): zůstatek od začátku účetního období snižuje daň pravidla nejvýš na nulu.")
    recognise_asset = fields.Boolean(
        tracking=True, string="Vykázat i pohledávku", help="Odložená daň: i záporný stav (pohledávka). Výchozí ne – opatrnost.")
    note = fields.Text(tracking=True, string="Poznámka")
    version_ids = fields.One2many("investra.tax.rule.version", "rule_id", string="Sazby")
    rate_now = fields.Float(compute="_compute_rate_now", digits=(10, 6), string="Aktuální sazba")

    @api.depends("version_ids.valid_from", "version_ids.rate")
    def _compute_rate_now(self):
        today = fields.Date.context_today(self)
        for rule in self:
            valid = rule.version_ids.filtered(lambda v: v.valid_from and v.valid_from <= today).sorted("valid_from")
            rule.rate_now = valid[-1].rate if valid else 0.0

    @api.constrains("kind", "method", "tax_account_code", "balance_account_code", "credit_account_code", "recognise_asset")
    def _check_setup(self):
        for rule in self:
            if rule.kind == "exempt":
                if rule.tax_account_code or rule.balance_account_code or rule.credit_account_code or rule.version_ids:
                    raise ValidationError(self.env._("%s: Mimo základ daně nemá sazbu ani účty.", rule.name))
                continue
            if not (rule.method and rule.tax_account_code and rule.balance_account_code):
                raise ValidationError(self.env._("%s: vyplňte způsob, účet daně a rozvahový účet.", rule.name))
            if rule.method == "deferred" and rule.credit_account_code:
                raise ValidationError(self.env._("%s: zápočet je jen u splatné daně.", rule.name))
            if rule.method == "current" and rule.recognise_asset:
                raise ValidationError(self.env._("%s: pohledávku lze vykázat jen u odložené daně.", rule.name))

    @api.constrains("kind", "version_ids")
    def _check_versions(self):
        for rule in self:
            if rule.kind != "exempt" and not rule.version_ids:
                raise ValidationError(self.env._("Pravidlo %s nemá žádnou sazbu.", rule.name))

    def _version_at(self, day):
        """Verze sazby platná k datu (jako `investra.fee.rule._version_at`)."""
        self.ensure_one()
        valid = self.version_ids.filtered(lambda v: v.valid_from <= day).sorted("valid_from")
        if not valid:
            raise UserError(self.env._("Pravidlo %(rule)s nemá sazbu k %(day)s.", rule=self.name, day=day))
        return valid[-1]

    def _book_accounts(self, company):
        """Účty pravidla v knize podle kódu; chybějící účet nebo účet bez role je chyba (stop výpočtu)."""
        self.ensure_one()
        Account = self.env["account.account"].sudo().with_company(company)
        Role = self.env["investra.account.role"]
        tax_role = Role.accounts_for(company, "expense_tax")
        payable_role = Role.accounts_for(company, "tax_payable")
        result = {}
        for key, field in (("tax", "tax_account_code"), ("balance", "balance_account_code"), ("credit", "credit_account_code")):
            code = self[field]
            if not code:
                continue
            account = Account.search([("code", "=", code), ("company_ids", "in", company.ids)], limit=1)
            if not account:
                raise UserError(self.env._(
                    "Kniha %(book)s nemá účet %(code)s daňového pravidla %(rule)s. Založte ho v osnově a přidejte k roli "
                    "v Nastavení › Účtování › Účty rolí.", book=company.name, code=code, rule=self.name))
            expected = payable_role if key == "balance" else tax_role
            if account not in expected and not (key == "tax" and account.account_type.startswith("equity")):
                raise UserError(self.env._(
                    "Účet %(code)s pravidla %(rule)s nemá v knize %(book)s roli %(role)s (přidejte ho jako další účet).",
                    code=code, rule=self.name, book=company.name,
                    role=self.env._("Odložená a splatná daň") if key == "balance" else self.env._("Daň z příjmů")))
            result[key] = account
        return result

    def _account_codes(self):
        self.ensure_one()
        return {code for code in (self.tax_account_code, self.balance_account_code, self.credit_account_code) if code}


class InvestraTaxRuleVersion(models.Model):
    _name = "investra.tax.rule.version"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Sazba daňového pravidla"
    _order = "rule_id, valid_from"
    _line_tracking_parent = "rule_id"

    rule_id = fields.Many2one("investra.tax.rule", required=True, ondelete="cascade", index=True, string="Pravidlo")
    valid_from = fields.Date(required=True, tracking=True, string="Platí od")
    rate = fields.Float(digits=(10, 6), required=True, tracking=True, string="Sazba", help="0,05 = 5 %.")
    decision_ref = fields.Char(tracking=True, string="Předpis")

    _rule_from_uniq = models.Constraint("unique(rule_id, valid_from)", "Pravidlo už má sazbu platnou od tohoto data.")

    @api.constrains("rate")
    def _check_rate(self):
        for version in self:
            if not 0 <= version.rate <= 1:
                raise ValidationError(self.env._("Sazba je zlomek od 0 do 1 (0,21 = 21 %)."))

    def _line_tracking_desc(self):
        return self.env._("Sazba platná od %s", self.valid_from or "–")

    def _check_unused(self):
        """Verze použitá v ocenění mimo návrh zůstává beze změny; změna sazby je nová verze.

        Rozpad daně ocenění uvádí id pravidla (`"tax_rule": <id>` v detailu řádku úplaty; zapisuje ho výpočet daně)."""
        Fee = self.env["investra.valuation.fee"].sudo()
        for version in self:
            if not version.rule_id.id:
                continue
            fees = Fee.search([
                ("rule_id.kind", "=", "tax"), ("detail", "like", f'"tax_rule": {version.rule_id.id}'),
                ("valuation_id.state", "not in", ("draft", "computed", "returned")),
            ])
            if fees and version.valid_from <= max(fees.valuation_id.mapped("date")):
                raise UserError(self.env._("Použitou sazbu nejde měnit, založte novou s platností od data."))

    def write(self, vals):
        self._check_unused()
        return super().write(vals)

    def unlink(self):
        self._check_unused()
        return super().unlink()


class InvestraFundTaxException(models.Model):
    _name = "investra.fund.tax.exception"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Daňová výjimka fondu"
    _order = "fund_id, account_id"
    _check_company_auto = True
    _line_tracking_parent = "fund_id"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="cascade", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="fund_id.company_id.currency_id")
    account_id = fields.Many2one("account.account", required=True, ondelete="restrict", check_company=True, tracking=True, string="Účet")
    tax_rule_id = fields.Many2one("investra.tax.rule", required=True, ondelete="restrict", tracking=True, string="Daňové pravidlo")
    share = fields.Float(digits=(6, 4), default=1.0, tracking=True, string="Podíl",
                         help="Část účtu pro toto pravidlo; zbytek zůstává ve výchozím.")
    nondeductible_pct = fields.Float(digits=(6, 2), default=0.0, tracking=True, string="Neuznatelné náklady (% z výnosu)",
                                     help="Jen u výnosového účtu: část výnosu, ke které se připočtou neuznatelné náklady.")
    movement_ytd = fields.Monetary(compute="_compute_movement_ytd", currency_field="currency_id", string="Pohyb od začátku období",
                                   help="Pohyb účtu od začátku účetního období fondu se znaménkem výnosu (kredit = +).")
    note = fields.Char(tracking=True, string="Poznámka")

    _fund_account_uniq = models.Constraint("unique(fund_id, account_id)", "Účet už má ve fondu výjimku.")

    def _line_tracking_desc(self):
        return f"{self.account_id.display_name or '–'} → {self.tax_rule_id.name or '–'}"

    @api.depends("fund_id", "account_id")
    def _compute_movement_ytd(self):
        today = fields.Date.context_today(self)
        Line = self.env["account.move.line"].sudo()
        for exception in self:
            if not (exception.fund_id and exception.account_id and exception.fund_id.company_id):
                exception.movement_ytd = 0.0
                continue
            start = exception.fund_id._fiscal_year_start(today)
            balance = Line._read_group([
                ("company_id", "=", exception.fund_id.company_id.id), ("parent_state", "=", "posted"),
                ("account_id", "=", exception.account_id.id), ("date", ">=", start), ("date", "<=", today),
            ], aggregates=["balance:sum"])[0][0]
            exception.movement_ytd = -(balance or 0.0)

    @api.constrains("account_id", "tax_rule_id", "share", "nondeductible_pct", "fund_id")
    def _check_exception(self):
        for exception in self:
            account, rule = exception.account_id, exception.tax_rule_id
            if not 0 < exception.share <= 1:
                raise ValidationError(self.env._("Podíl výjimky musí být větší než 0 a nejvýš 1."))
            if not 0 <= exception.nondeductible_pct <= 100:
                raise ValidationError(self.env._("Neuznatelné náklady jsou v procentech od 0 do 100."))
            if exception.nondeductible_pct and not account.account_type.startswith("income"):
                raise ValidationError(self.env._("Neuznatelné náklady z výnosu jde zadat jen u výnosového účtu."))
            company = exception.fund_id.company_id
            if company and account.company_ids and company not in account.company_ids:
                raise ValidationError(self.env._("Účet %s nepatří knize fondu.", account.display_name))
            is_pnl = account.account_type.startswith(("income", "expense"))
            if not is_pnl and rule.kind == "exempt":
                raise ValidationError(self.env._("Rozvahový účet %s nemá smysl mít v pravidle Mimo základ daně.", account.display_name))
            # D10: rozvahový účet smí mít i splatné pravidlo (přispívá svým pohybem od začátku období); výsledkový účet
            # s odloženým pravidlem ne (odložená daň se počítá ze zůstatku rozvahového účtu).
            if is_pnl and rule.method == "deferred":
                raise ValidationError(self.env._("Odložené pravidlo %(rule)s jde přiřadit rozvahovému účtu, ne výsledkovému (%(account)s).",
                                                 rule=rule.name, account=account.display_name))
            if company and account in self.env["investra.account.role"].sudo().accounts_for(company, "expense_tax"):
                raise ValidationError(self.env._("Účty daně (%s) se do daňového základu nikdy nepočítají.", account.display_name))
            exception.fund_id._check_tax_accounts_distinct()
