from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.investra_entity.models.entity import RATE_SOURCE_NONE, RATE_SOURCES, raise_no_rate_source, rate_source_for


class InvestraFxProfile(models.Model):
    """Které účty se přeceňují a kam jde rozdíl; účty určuje uživatel."""

    _name = "investra.fx.profile"
    _inherit = ["mail.thread"]
    _description = "Profil přecenění cizích měn"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True, string="Název")
    active = fields.Boolean(default=True, tracking=True, string="Aktivní")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, tracking=True, string="Společnost")
    account_ids = fields.Many2many("account.account", string="Přeceňované účty", check_company=True, tracking=True)
    gain_account_id = fields.Many2one("account.account", string="Účet zisku z přecenění", check_company=True, tracking=True, ondelete="restrict")
    loss_account_id = fields.Many2one("account.account", string="Účet ztráty z přecenění", check_company=True, tracking=True, ondelete="restrict")
    journal_id = fields.Many2one(
        "account.journal", string="Deník", check_company=True, tracking=True, ondelete="restrict", domain="[('type', '=', 'general')]"
    )
    # Výchozí podle funkční měny aktivní firmy, onchange a create podle zvolené společnosti (dřív pevně ČNB, MN-08).
    rate_source = fields.Selection(
        RATE_SOURCES, required=True, tracking=True, string="Zdroj kurzu", default=lambda self: rate_source_for(self.env.company.currency_id),
    )

    @api.onchange("company_id")
    def _onchange_company_rate_source(self):
        for record in self:
            record.rate_source = rate_source_for(record.company_id.currency_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("rate_source"):
                company = self.env["res.company"].browse(vals.get("company_id")) if vals.get("company_id") else self.env.company
                vals["rate_source"] = rate_source_for(company.currency_id)
        return super().create(vals_list)

    @api.constrains("rate_source", "company_id")
    def _check_rate_source(self):
        for profile in self:
            if profile.rate_source != rate_source_for(profile.company_id.currency_id):
                raise ValidationError(self.env._("Zdroj kurzu se řídí měnou účetnictví: %s.", profile.company_id.currency_id.name))

    @api.model
    def _foreign_balances(self, company, accounts, date, domain=None, by_partner=None):
        """Zůstatky přeceňovaných účtů v cizí měně k datu: (účet, měna, partner, částka v měně, účetní zůstatek).

        Společný výběr pro běh přecenění a pro ocenění fondu (rozhodnutí 2026-11-13, varianta A). Výchozí doména bere
        zaúčtované řádky; ocenění předá vlastní (i své nezaúčtované doklady). by_partner(účet) = False sloučí partnery
        účtu do jednoho řádku (partner None); bez funkce se dělí vždy podle partnera.
        """
        base = company.currency_id
        if domain is None:
            domain = [("company_id", "=", company.id), ("parent_state", "=", "posted"), ("date", "<=", date)]
        groups = self.env["account.move.line"]._read_group(
            [*domain, ("account_id", "in", accounts.ids), ("currency_id", "!=", base.id)],
            groupby=["account_id", "currency_id", "partner_id"],
            aggregates=["amount_currency:sum", "balance:sum"],
        )
        merged = {}
        for account, currency, partner, amount, balance in groups:
            key = (account, currency, partner if by_partner is None or by_partner(account) else None)
            total = merged.setdefault(key, [0.0, 0.0])
            total[0] += amount
            total[1] += balance
        return [(account, currency, partner or None, amount, balance) for (account, currency, partner), (amount, balance) in merged.items()]

    def _check_ready(self):
        self.ensure_one()
        if not (self.account_ids and self.gain_account_id and self.loss_account_id and self.journal_id):
            raise UserError(self.env._("Profil %s nemá účty, protiúčty a deník.", self.name))


class InvestraFxRun(models.Model):
    """Přecenění k datu: doúčtuje rozdíl do potřebného zůstatku, nic nezaúčtuje samo."""

    _name = "investra.fx.run"
    _description = "Přecenění cizích měn"
    _order = "date desc, id desc"
    _check_company_auto = True

    profile_id = fields.Many2one("investra.fx.profile", required=True, ondelete="restrict", string="Profil", check_company=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, string="Společnost")
    date = fields.Date(required=True, string="Datum přecenění")
    line_ids = fields.One2many("investra.fx.run.line", "run_id", string="Rozpis", readonly=True)
    move_id = fields.Many2one("account.move", readonly=True, string="Návrh dokladu", check_company=True, ondelete="set null")
    move_state = fields.Selection(related="move_id.state", string="Stav dokladu")
    difference = fields.Monetary(compute="_compute_difference", currency_field="currency_id", string="Rozdíl celkem")
    currency_id = fields.Many2one(related="company_id.currency_id")

    later_run_warning = fields.Char(compute="_compute_later_run_warning", string="Upozornění")

    def _compute_later_run_warning(self):
        for run in self:
            later = run._posted_later_runs()
            run.later_run_warning = self.env._(
                "Existuje zaúčtované přecenění k %s; po doplnění ho spusťte znovu i k tomuto datu.", later[0].date
            ) if later else False

    def _posted_later_runs(self):
        self.ensure_one()
        return self.search([
            ("profile_id", "=", self.profile_id.id), ("date", ">", self.date), ("move_id.state", "=", "posted"),
        ], order="date")

    def _compute_difference(self):
        for run in self:
            run.difference = sum(run.line_ids.mapped("difference"))

    def _ensure_open(self):
        """Zaúčtované přecenění se nemění; doplnění je nový běh. Dva návrhy profilu by rozdíl zdvojily."""
        self.ensure_one()
        if self.move_id.state == "posted":
            raise UserError(self.env._("Přecenění je zaúčtované; pro doplnění založte nové přecenění ke stejnému datu."))
        other = self.search_count([
            ("profile_id", "=", self.profile_id.id), ("id", "!=", self.id), ("move_id.state", "=", "draft"),
        ], limit=1)
        if other:
            raise UserError(self.env._("Profil má nezaúčtovaný návrh jiného přecenění, nejdřív ho dokončete nebo smažte."))

    def _ensure_period_open(self):
        """Odoo by datum v uzamčeném období tiše posunulo, rozdíl musí zůstat k datu přecenění."""
        self.ensure_one()
        if self.company_id._get_violated_lock_dates(self.date, False, self.profile_id.journal_id):
            raise UserError(self.env._("Období k %s je uzamčené, přecenění do něj nejde doplnit.", self.date))

    def _published_rate(self, currency):
        """Funkční měna za jednotku měny; chybějící, budoucí nebo starý kurz výpočet zastaví."""
        self.ensure_one()
        profile = self.profile_id
        Rate = self.env["investra.rate"].sudo()
        source, base = profile.rate_source, self.company_id.currency_id
        if source == RATE_SOURCE_NONE:
            raise_no_rate_source(self.env, self.company_id.name, base)
        return float(Rate.get_rate(source, currency, self.date) / Rate.get_rate(source, base, self.date))

    def action_compute(self):
        """Spočítá rozdíl po účtu, měně a partnerovi; opakovaný výpočet nahradí návrh."""
        for run in self:
            run.profile_id._check_ready()
            run._ensure_open()
            run.move_id.unlink()
            run.line_ids.unlink()
            company = run.company_id
            base = company.currency_id
            groups = self.env["investra.fx.profile"]._foreign_balances(company, run.profile_id.account_ids, run.date)
            values = []
            for account, currency, partner, amount, balance in groups:
                rate = run._published_rate(currency)
                target = base.round(amount * rate)
                difference = base.round(target - balance)
                if not base.is_zero(difference):
                    values.append({
                        "run_id": run.id, "account_id": account.id, "foreign_currency_id": currency.id, "partner_id": partner.id if partner else False,
                        "amount_currency": amount, "rate": rate, "balance": balance, "target": target, "difference": difference,
                    })
            self.env["investra.fx.run.line"].create(values)
        return True

    def action_create_move(self):
        """Vytvoří návrh dokladu. Zaúčtuje ho účetní po kontrole."""
        for run in self:
            run._ensure_open()
            run._ensure_period_open()
            if not run.line_ids:
                raise UserError(self.env._("Není co přecenit."))
            run.move_id.unlink()
            name = self.env._("Přecenění %(profile)s k %(day)s", profile=run.profile_id.name, day=run.date)
            base = run.company_id.currency_id
            commands = [(0, 0, {
                "name": name, "account_id": line.account_id.id, "partner_id": line.partner_id.id,
                "currency_id": line.foreign_currency_id.id, "amount_currency": 0.0, "balance": line.difference,
            }) for line in run.line_ids]
            gain = sum(line.difference for line in run.line_ids if line.difference > 0)
            loss = sum(line.difference for line in run.line_ids if line.difference < 0)
            for account, amount in ((run.profile_id.gain_account_id, -gain), (run.profile_id.loss_account_id, -loss)):
                if not base.is_zero(amount):
                    commands.append((0, 0, {"name": name, "account_id": account.id, "currency_id": base.id, "balance": amount}))
            run.move_id = self.env["account.move"].with_company(run.company_id).create({
                "move_type": "entry", "date": run.date, "journal_id": run.profile_id.journal_id.id, "ref": name, "line_ids": commands,
            })
        return True


class InvestraFxRunLine(models.Model):
    _name = "investra.fx.run.line"
    _description = "Rozpis přecenění"

    run_id = fields.Many2one("investra.fx.run", required=True, ondelete="cascade", index=True, string="Přecenění")
    company_currency_id = fields.Many2one(related="run_id.currency_id")
    account_id = fields.Many2one("account.account", required=True, ondelete="restrict", string="Účet")
    partner_id = fields.Many2one("res.partner", ondelete="restrict", string="Partner")
    foreign_currency_id = fields.Many2one("res.currency", required=True, ondelete="restrict", string="Měna")
    amount_currency = fields.Monetary(currency_field="foreign_currency_id", string="Zůstatek v měně")
    rate = fields.Float(digits=(16, 6), string="Kurz")
    balance = fields.Monetary(currency_field="company_currency_id", string="Účetní zůstatek")
    target = fields.Monetary(currency_field="company_currency_id", string="Potřebný zůstatek")
    difference = fields.Monetary(currency_field="company_currency_id", string="Rozdíl")
