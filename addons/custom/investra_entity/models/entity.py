from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Typy knih, jejichž deníky mají od založení neměnné zápisy (hash je nevratný).
HASHED_TYPES = ("sicav", "fund", "subfund")


class InvestraEntity(models.Model):
    """Účetní kniha: jedna hlavní společnost Odoo. Hierarchie je vlastní, ne pobočky."""

    _name = "investra.entity"
    _description = "Účetní kniha"
    _order = "name"

    name = fields.Char(related="company_id.name", store=True)
    company_id = fields.Many2one("res.company", required=True, ondelete="restrict")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Funkční měna")
    entity_type = fields.Selection(
        [
            ("service", "Servisní společnost"),
            ("manager", "Investiční společnost"),
            ("sicav", "SICAV"),
            ("fund", "Fond"),
            ("subfund", "Podfond"),
        ],
        required=True,
    )
    framework = fields.Selection(
        [
            ("cas500", "Vyhláška 500/2002"),
            ("cas501", "Vyhláška 501/2002"),
            ("ifrs", "IFRS přijaté EU"),
        ],
        required=True,
        string="Účetní rámec",
    )
    rate_source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], required=True, default="cnb")
    parent_id = fields.Many2one("investra.entity", string="Nadřazená kniha", ondelete="restrict")
    founder_id = fields.Many2one("res.partner", string="Zakladatel")

    _company_uniq = models.Constraint("unique(company_id)", "Společnost může mít jen jednu knihu.")

    @api.constrains("parent_id")
    def _check_parent(self):
        if self._has_cycle():
            raise ValidationError(self.env._("Hierarchie knih nesmí být kruhová."))
        for entity in self:
            if entity.entity_type == "subfund" and (not entity.parent_id or entity.parent_id.entity_type != "sicav"):
                raise ValidationError(self.env._("Podfond musí mít nadřazený SICAV."))

    def write(self, vals):
        if "framework" in vals or "company_id" in vals:
            booked = self.env["account.move"].sudo().search_count(
                [("company_id", "in", self.company_id.ids), ("posted_before", "=", True)], limit=1
            )
            if booked:
                raise UserError(self.env._("Rámec ani společnost nejde změnit v knize se zaúčtovanými doklady."))
        return super().write(vals)

    @api.model
    def create_book(self, name, entity_type, framework, currency, template, country=None, **values):
        """Založí společnost s osnovou a povinným nastavením.

        Načtení osnovy přepíše měnu společnosti měnou šablony, proto se měna nastaví znovu
        a výsledek se zkontroluje. První načtení šablony může potvrdit transakci.
        """
        company = self.env["res.company"].sudo().create({
            "name": name,
            "currency_id": currency.id,
            "country_id": (country or self.env.ref("base.cz")).id,
        })
        self.env["account.chart.template"].sudo().try_loading(template, company=company, install_demo=False)
        if company.currency_id != currency:
            company.currency_id = currency
        if company.currency_id != currency:
            raise UserError(self.env._("Funkční měna knihy %s nesouhlasí se zadáním.", name))
        company.write({"restrictive_audit_trail": True, "autopost_bills": False})
        if entity_type in HASHED_TYPES:
            journals = self.env["account.journal"].sudo().search([("company_id", "=", company.id)])
            journals.filtered(lambda j: j.type == "general").write({"restrict_mode_hash_table": True})
        return self.create({
            "company_id": company.id,
            "entity_type": entity_type,
            "framework": framework,
            **values,
        })
