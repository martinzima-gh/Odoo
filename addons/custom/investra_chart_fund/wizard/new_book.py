from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.investra_entity.models.entity import RATE_SOURCE_BY_CURRENCY

FUND_TYPES = ("sicav", "fund", "subfund")
# Rámec se odvozuje od druhu jednotky a rámce se nemíchají (servisní společnost 500/2002, ostatní 501/2002).
FRAMEWORK_BY_TYPE = {"service": "cas500", "manager": "cas501", "sicav": "cas501", "fund": "cas501", "subfund": "cas501"}


def template_for(entity_type):
    """Šablona osnovy podle druhu jednotky; uživatel ji nevolí."""
    return "investra_fund" if entity_type in FUND_TYPES else "cz"


class InvestraNewBookWizard(models.TransientModel):
    """Průvodce „Nová účetní kniha“: společnost a kniha jediným voláním create_book (stejně jako seed)."""

    _name = "investra.new.book.wizard"
    _description = "Nová účetní kniha"

    name = fields.Char(required=True, string="Název společnosti")
    entity_type = fields.Selection(
        lambda self: self.env["investra.entity"]._fields["entity_type"].selection,
        required=True, default="fund", string="Druh jednotky",
    )
    framework = fields.Selection(
        lambda self: self.env["investra.entity"]._fields["framework"].selection,
        required=True, default="cas501", string="Účetní rámec",
    )
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Funkční měna", default=lambda self: self.env.ref("base.CZK"),
    )
    country_id = fields.Many2one("res.country", required=True, string="Země", default=lambda self: self.env.ref("base.cz"))
    parent_id = fields.Many2one("investra.entity", string="Nadřazená kniha", domain="[('entity_type', '=', 'sicav')]")
    template = fields.Char(compute="_compute_template", string="Šablona osnovy")
    rate_source = fields.Char(compute="_compute_template", string="Zdroj kurzů")

    @api.depends("entity_type", "currency_id")
    def _compute_template(self):
        labels = dict(self.env["investra.entity"]._fields["rate_source"].selection)
        for wizard in self:
            wizard.template = template_for(wizard.entity_type) if wizard.entity_type else False
            wizard.rate_source = labels[RATE_SOURCE_BY_CURRENCY.get(wizard.currency_id.name, "cnb")]

    @api.onchange("entity_type")
    def _onchange_entity_type(self):
        if self.entity_type:
            self.framework = FRAMEWORK_BY_TYPE[self.entity_type]

    def _check_before_create(self):
        """Kontroly před založením: nic se nezaloží, dokud vše neprojde.

        Načtení šablony doinstaluje chybějící modul osnovy a potvrdí tím transakci (account.chart.template._load,
        button_immediate_install); při pozdější chybě by zůstala polovičatá společnost. Proto se chybějící moduly
        jen ohlásí a průvodce se zastaví.
        """
        self.ensure_one()
        if not self.env.is_system():
            raise UserError(self.env._("Účetní knihu může založit jen správce."))
        if self.framework != FRAMEWORK_BY_TYPE[self.entity_type]:
            labels = dict(self._fields["framework"]._description_selection(self.env))
            raise UserError(self.env._(
                "Druh jednotky a účetní rámec nejdou dohromady: pro tento druh platí %s.",
                labels[FRAMEWORK_BY_TYPE[self.entity_type]],
            ))
        if self.entity_type == "subfund" and self.parent_id.entity_type != "sicav":
            raise UserError(self.env._("Podfond musí mít nadřazený SICAV."))
        if self.env["res.company"].sudo().search_count([("name", "=", self.name)], limit=1):
            raise UserError(self.env._("Společnost %s už existuje.", self.name))
        template = template_for(self.entity_type)
        module = self.env["account.chart.template"]._get_chart_template_mapping(get_all=True).get(template, {}).get("module")
        missing = self.env["ir.module.module"].sudo().search([("name", "=", module), ("state", "!=", "installed")])
        missing |= self.env["res.company"].new({"country_id": self.country_id.id}).uninstalled_l10n_module_ids
        if missing:
            raise UserError(self.env._(
                "Nejdřív nainstalujte moduly: %s. Nic se nezaložilo.", ", ".join(missing.mapped("name")),
            ))

    def action_create(self):
        self._check_before_create()
        entity = self.env["investra.entity"].create_book(
            self.name, self.entity_type, self.framework, self.currency_id, template_for(self.entity_type),
            country=self.country_id, parent_id=self.parent_id.id,
        )
        company = entity.company_id
        # res.company.create uživatele obvykle připojí sám; tady výslovně, ať na tom průvodce nezávisí.
        self.env.user.sudo().write({"company_ids": [Command.link(company.id)]})
        form = {
            "type": "ir.actions.act_window",
            "res_model": "investra.entity",
            "res_id": entity.id,
            "view_mode": "form",
            "target": "current",
            # Kontext akce přebije kontext klienta: formulář nové knihy projde pravidlem „Knihy podle společnosti“
            # i bez ručního přepnutí firmy.
            "context": {"allowed_company_ids": self.env.companies.ids + company.ids},
        }
        # Přepínač firem si pamatuje prohlížeč, server nově založenou společnost trvale nezapne (MN-05, nález MN-02 9).
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "warning",
                "sticky": True,
                "title": self.env._("Kniha založena"),
                "message": self.env._("Zapněte novou společnost v přepínači firem."),
                "next": form,
            },
        }
