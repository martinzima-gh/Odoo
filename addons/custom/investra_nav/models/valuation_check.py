"""ZJ-25: katalog, strukturovaný výsledek a položky kontrol ocenění (podklad-katalog-kontrol.md, oddíl 5 a 6)."""
from odoo import api, fields, models

from .check_catalog import CHECK_AREAS, CHECK_CATALOG

STATUS_ORDER = {"stop": 0, "warning": 1, "ok": 2}


class InvestraValuationCheck(models.Model):
    _inherit = "investra.valuation.check"
    _order = "valuation_id, status_order, area, id"

    area = fields.Selection(CHECK_AREAS, compute="_compute_catalog", store=True, string="Oblast",
                            help="Oblast kontroly podle katalogu kontrol (check_catalog.py).")
    what = fields.Char(compute="_compute_catalog", string="Co se kontroluje",
                       help="Srozumitelný popis kontroly z katalogu; mění se s katalogem i u starších ocenění.")
    how = fields.Char(compute="_compute_catalog", string="Jak opravit",
                      help="Kde v aplikaci chybu opravit (nabídka, formulář, pole).")
    status_order = fields.Integer(compute="_compute_status_order", store=True, string="Pořadí výsledku")
    expected = fields.Char(readonly=True, string="Očekáváno", help="Hodnota, která by měla vyjít (formátovaný text).")
    actual = fields.Char(readonly=True, string="Skutečnost", help="Hodnota, která vyšla (formátovaný text).")
    difference = fields.Char(readonly=True, string="Rozdíl", help="Skutečnost − očekáváno (formátovaný text).")
    item_ids = fields.One2many("investra.valuation.check.item", "check_id", readonly=True, string="Co nesedí",
                               help="Položky, které kontrolu nesplnily; řádek otevře záznam.")
    item_count = fields.Integer(compute="_compute_item_count", string="Počet položek")

    @api.depends("code")
    def _compute_catalog(self):
        for check in self:
            area, what, how = CHECK_CATALOG.get(check.code, (False, check.name, ""))
            check.area, check.what, check.how = area, what, how

    @api.depends("status")
    def _compute_status_order(self):
        for check in self:
            check.status_order = STATUS_ORDER.get(check.status, 3)

    @api.depends("item_ids")
    def _compute_item_count(self):
        for check in self:
            check.item_count = len(check.item_ids)


class InvestraValuationCheckItem(models.Model):
    _name = "investra.valuation.check.item"
    _description = "Položka kontroly ocenění"
    _order = "check_id, sequence, id"

    check_id = fields.Many2one("investra.valuation.check", required=True, ondelete="cascade", index=True, string="Kontrola")
    company_id = fields.Many2one(related="check_id.company_id", store=True, index=True)
    sequence = fields.Integer(string="Pořadí")
    name = fields.Char(required=True, string="Položka", help="Název záznamu, který nesedí (nástroj, obchod, třída, doklad …).")
    values = fields.Char(string="Hodnoty", help="Co u položky nesedí, např. „očekáváno 100,00, skutečnost 99,50, rozdíl −0,50“.")
    res_model = fields.Char(string="Model záznamu", help="Technický model záznamu, který položka otevře.")
    res_id = fields.Many2oneReference(model_field="res_model", string="Id záznamu")

    def action_open(self):
        self.ensure_one()
        if not (self.res_model and self.res_id):
            return False
        record = self.env[self.res_model].browse(self.res_id)
        record.check_access("read")
        return {"type": "ir.actions.act_window", "res_model": self.res_model, "res_id": self.res_id,
                "views": [(False, "form")], "target": "current"}


class InvestraValuation(models.Model):
    _inherit = "investra.valuation"

    check_stop_count = fields.Integer(compute="_compute_check_counts", string="Kontroly se stopem")
    check_warning_count = fields.Integer(compute="_compute_check_counts", string="Kontroly s upozorněním")
    check_ok_count = fields.Integer(compute="_compute_check_counts", string="Kontroly v pořádku")
    check_summary = fields.Char(compute="_compute_check_counts", string="Kontroly")

    @api.depends("check_ids.status")
    def _compute_check_counts(self):
        for valuation in self:
            statuses = valuation.check_ids.mapped("status")
            stop, warning = statuses.count("stop"), statuses.count("warning")
            valuation.check_stop_count = stop
            valuation.check_warning_count = warning
            valuation.check_ok_count = statuses.count("ok")
            valuation.check_summary = (
                self.env._("Kontroly: %(stop)s stop, %(warning)s upozornění", stop=stop, warning=warning) if stop or warning else False)

    def action_show_checks(self):
        """Seznam kontrol tohoto ocenění (stop → upozornění → v pořádku, po oblastech)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Kontroly – %s", self.display_name),
            "res_model": "investra.valuation.check",
            "views": [(False, "list")],
            "domain": [("valuation_id", "=", self.id)],
            "context": {"group_by": "area", "create": False},
        }
