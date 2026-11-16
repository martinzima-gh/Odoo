from odoo import api, fields, models

from .template_investra_fund import ROLE_ACCOUNTS

STANDARD_STATES = [
    ("standard", "Podle standardu"),
    ("deviation", "Odchylka"),
    ("none", "Bez standardu"),
]


class InvestraRoleAccount(models.Model):
    """Značka odchylky mapování od standardu osnovy fondů (MN-04, rozhodnutí 2026-11-16 varianta A).

    Dohledání účtu při účtování (`account_for`) se nemění; pole jen zobrazují, zda hlavní účet role odpovídá šabloně.
    """

    _inherit = "investra.role.account"

    standard_state = fields.Selection(
        STANDARD_STATES, compute="_compute_standard", search="_search_standard_state", string="Standard",
        help="Podle standardu: hlavní účet je účet šablony. Odchylka: fond používá jiný účet. "
             "Bez standardu: kniha není ze šablony fondu nebo role ve standardu není. "
             "Porovnává se jen hlavní účet; Další účty odchylkou nejsou.",
    )
    standard_account_id = fields.Many2one(
        "account.account", compute="_compute_standard", string="Standardní účet",
        help="Účet šablony pro tuto roli v této knize.",
    )

    @api.depends("company_id.chart_template", "role_id.code", "account_id")
    def _compute_standard(self):
        chart = self.env["account.chart.template"].sudo()
        for mapping in self:
            xmlid = ROLE_ACCOUNTS.get(mapping.role_id.code)
            company = mapping.company_id
            standard = False
            if xmlid and company.chart_template == "investra_fund":
                standard = chart.with_company(company).ref(xmlid, raise_if_not_found=False) or False
            mapping.standard_account_id = standard
            if not standard:
                mapping.standard_state = "none"
            else:
                mapping.standard_state = "standard" if mapping.account_id == standard else "deviation"

    def _search_standard_state(self, operator, value):
        """Nestorované pole: vyhodnotí se nad všemi řádky; viditelnost řádků hlídá pravidlo záznamů při samotném hledání."""
        if operator not in ("=", "!=", "in", "not in"):
            raise NotImplementedError(self.env._("Operátor %s pro pole Standard není podporován.", operator))
        values = [value] if isinstance(value, str) else list(value)
        negate = operator in ("!=", "not in")
        ids = self.sudo().search([]).filtered(lambda m: (m.standard_state in values) != negate).ids
        return [("id", "in", ids)]

    @api.model
    def _apply_standard_role(self, code, old_xmlid=None):
        """Pomocná funkce pro migraci po změně `ROLE_ACCOUNTS[code]`: převede knihy fondů bez odchylky na nový standard.

        Odchylka od plánu MN-04: po změně slovníku už řádek, který odpovídal starému standardu, vypadá jako odchylka,
        proto migrace předá `old_xmlid` (původní xmlid účtu šablony). Řádek, jehož hlavní účet je starý standardní
        účet, nebo role v knize chybí, dostane nový standardní účet. Ostatní řádky (opravdová odchylka) se nemění
        a funkce je vrátí (investra.role.account) pro výpis do logu migrace. Opakovatelná; nic ji dnes nevolá.
        """
        xmlid = ROLE_ACCOUNTS[code]
        role = self.env["investra.account.role"].search([("code", "=", code)], limit=1)
        chart = self.env["account.chart.template"].sudo()
        Mapping = self.sudo()
        deviations = Mapping.browse()
        for company in self.env["res.company"].sudo().search([("chart_template", "=", "investra_fund")]):
            scoped = chart.with_company(company)
            new = scoped.ref(xmlid, raise_if_not_found=False)
            if not new:
                continue  # účet ještě v knize není (nejdřív `_ensure_fund_accounts`)
            old = scoped.ref(old_xmlid, raise_if_not_found=False) if old_xmlid else False
            mapping = Mapping.search([("company_id", "=", company.id), ("role_id", "=", role.id)], limit=1)
            if not mapping:
                Mapping.create({"company_id": company.id, "role_id": role.id, "account_id": new.id})
            elif mapping.account_id == new:
                continue
            elif old and mapping.account_id == old:
                mapping.account_id = new
            else:
                deviations |= mapping
        return deviations
