from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import formatLang


class InvestraDerivativeSettleWizard(models.TransientModel):
    """Okno vypořádání nohy: volba bankovních účtů a náhled dokladu; účtuje smlouva, okno samo nic."""

    _name = "investra.derivative.settle.wizard"
    _description = "Vypořádání nohy FX derivátu"

    leg_id = fields.Many2one("investra.derivative.leg", required=True, ondelete="cascade", string="Noha")
    derivative_id = fields.Many2one(related="leg_id.derivative_id", string="Smlouva")
    settlement_date = fields.Date(related="leg_id.settlement_date")
    bank_account_ids = fields.Many2many("account.account", compute="_compute_bank_account_ids", string="Bankovní účty fondu")
    buy_currency_id = fields.Many2one(related="leg_id.buy_currency_id")
    sell_currency_id = fields.Many2one(related="leg_id.sell_currency_id")
    buy_amount = fields.Monetary(related="leg_id.buy_amount", currency_field="buy_currency_id")
    sell_amount = fields.Monetary(related="leg_id.sell_amount", currency_field="sell_currency_id")
    buy_account_id = fields.Many2one(
        "account.account", required=True, compute="_compute_accounts", store=True, readonly=False, precompute=True,
        domain="[('id', 'in', bank_account_ids)]", string="Účet pro přijatou měnu")
    sell_account_id = fields.Many2one(
        "account.account", required=True, compute="_compute_accounts", store=True, readonly=False, precompute=True,
        domain="[('id', 'in', bank_account_ids)]", string="Účet pro odeslanou měnu")
    preview = fields.Html(compute="_compute_preview", sanitize=False, string="Náhled zaúčtování")

    @api.depends("leg_id")
    def _compute_bank_account_ids(self):
        for wizard in self:
            wizard.bank_account_ids = wizard.leg_id.sudo()._bank_accounts() if wizard.leg_id else False

    @api.depends("leg_id")
    def _compute_accounts(self):
        for wizard in self:
            leg = wizard.leg_id.sudo()
            wizard.buy_account_id = leg._default_bank_account(leg.buy_currency_id) if leg else False
            wizard.sell_account_id = leg._default_bank_account(leg.sell_currency_id) if leg else False

    @api.depends("leg_id", "buy_account_id", "sell_account_id")
    def _compute_preview(self):
        money = lambda value: formatLang(self.env, float(value), digits=2) if value else ""
        for wizard in self:
            leg = wizard.leg_id.sudo()
            derivative = leg.derivative_id
            if not (leg and wizard.buy_account_id and wizard.sell_account_id):
                wizard.preview = False
                continue
            try:
                documents = derivative._settle_documents(leg, wizard.buy_account_id.sudo(), wizard.sell_account_id.sudo())
            except UserError as error:
                wizard.preview = Markup('<div class="alert alert-warning" role="alert">%s</div>') % error.args[0]
                continue
            wizard.preview = derivative._documents_html(documents, money)

    def action_confirm(self):
        self.ensure_one()
        self.leg_id.action_settle(self.buy_account_id, self.sell_account_id)
        return {"type": "ir.actions.act_window_close"}


class InvestraDerivativeReverseWizard(models.TransientModel):
    """Okno pro důvod storna vypořádání nohy nebo storna smlouvy; volá smlouvu, samo nic neúčtuje."""

    _name = "investra.derivative.reverse.wizard"
    _description = "Storno FX derivátu"

    derivative_id = fields.Many2one("investra.derivative", required=True, ondelete="cascade", string="Smlouva")
    mode = fields.Selection(
        [("settlement", "Stornovat vypořádání poslední nohy"), ("reverse", "Stornovat smlouvu")],
        required=True, default="reverse", string="Krok")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    reason = fields.Text(required=True, string="Důvod")

    @api.depends("mode")
    def _compute_effect(self):
        for wizard in self:
            if wizard.mode == "settlement":
                wizard.effect = self.env._(
                    "Doklad vypořádání naposledy vypořádané nohy se stornuje k datu vypořádání: vrátí se peněžní toky, "
                    "reálná hodnota i podrozvaha nohy. Noha bude znovu otevřená a smlouva ve stavu Sjednáno.")
            else:
                wizard.effect = self.env._(
                    "Doklady sjednání a vypořádání se stornují k jejich datům a smlouva dostane stav Stornováno. "
                    "Reálnou hodnotu a přepočet podrozvahy zaúčtované oceněním vrátí nejbližší další ocenění.")

    def action_confirm(self):
        self.ensure_one()
        method = self.derivative_id.action_reverse_settlement if self.mode == "settlement" else self.derivative_id.action_reverse
        result = method(self.reason)
        if result._name == "investra.approval.request":
            return result._action_open()
        return {"type": "ir.actions.act_window_close"}
