from collections import defaultdict
from datetime import date
from decimal import Decimal

from odoo import fields, models

from odoo.addons.investra_instruments.models.instrument import IFRS9_CATEGORY


class InvestraCnbMap(models.Model):
    """Převod role účtu na řádek listu ČNB. Pracovní nastavení, potvrzuje účetní metodik."""

    _name = "investra.cnb.map"
    _description = "Převod na výkaz ČNB"
    _order = "sheet, row, id"

    methodology = fields.Char(required=True, default="FOFI20261201", string="Metodika")
    sheet = fields.Char(required=True, index=True, string="List")
    row = fields.Integer(required=True, string="Řádek")
    column = fields.Integer(required=True, default=1, string="Sloupec")
    source = fields.Selection([("role", "Role účtu"), ("result", "Výsledek běžného období")], required=True, default="role", string="Zdroj")
    role_id = fields.Many2one("investra.account.role", ondelete="restrict", string="Role účtu")
    ifrs9_category = fields.Selection(IFRS9_CATEGORY, string="Jen kategorie IFRS 9")
    period = fields.Selection([("balance", "Zůstatek k datu"), ("ytd", "Od začátku roku")], required=True, default="balance", string="Období")
    sign = fields.Integer(required=True, default=1, string="Znaménko", help="1 zůstatek, -1 obrácený; určuje dopad do součtů.")
    report_sign = fields.Integer(required=True, default=1, string="Znaménko řádku", help="-1 u nákladů vykázaných kladně.")
    rollup_rows = fields.Char(string="Součtové řádky", help="Řádky oddělené čárkou, do kterých se hodnota přičte.")
    valid_from = fields.Date(required=True, default=date(2026, 12, 1), string="Platí od")
    valid_to = fields.Date(string="Platí do")

    def _active(self, sheet, day):
        return self.sudo().search([
            ("sheet", "=", sheet), ("valid_from", "<=", day), "|", ("valid_to", "=", False), ("valid_to", ">=", day),
        ])

    def _line_domain(self, company, day):
        return [("company_id", "=", company.id), ("parent_state", "=", "posted"), ("date", "<=", day)]

    def _sum(self, domain):
        total = self.env["account.move.line"].sudo()._read_group(domain, aggregates=["balance:sum"])[0][0]
        return Decimal(str(round(total or 0, 2)))

    def _amount(self, company, day):
        """Hodnota jednoho řádku převodu ve funkční měně."""
        self.ensure_one()
        domain = self._line_domain(company, day)
        start = date(day.year, 1, 1)
        if self.source == "result":
            return self._sum([
                *domain, ("date", ">=", start), ("account_id.account_type", "in", ("income", "income_other", "expense", "expense_depreciation", "expense_direct_cost")),
            ])
        # Hlavní i další účty role (rozhodnutí 2026-11-12 „Role s více účty“).
        accounts = self.env["investra.account.role"].accounts_for(company, self.role_id.code)
        if not accounts:
            return Decimal(0)
        domain.append(("account_id", "in", accounts.ids))
        if self.period == "ytd":
            domain.append(("date", ">=", start))
        if self.ifrs9_category:
            # Kategorie je v zařazení nástroje v obchodním modelu fondu, ne na nástroji (rozhodnutí 2026-11-11).
            domain.append(("investra_classification_id.ifrs9_category", "=", self.ifrs9_category))
        return self._sum(domain)

    def _sheet_values(self, company, sheet, day):
        """Hodnoty listu {(řádek, sloupec): částka} pro jednu knihu k datu."""
        values = defaultdict(Decimal)
        for entry in self._active(sheet, day):
            amount = entry._amount(company, day) * entry.sign
            values[(entry.row, entry.column)] += amount * entry.report_sign
            for row in filter(None, (entry.rollup_rows or "").split(",")):
                values[(int(row), entry.column)] += amount
        return dict(values)

    def _unmapped_roles(self, company, sheets, day):
        """Role s nenulovým zůstatkem, které žádný z listů nepokrývá; patří do kontrol."""
        covered = self.browse()
        for sheet in sheets:
            covered |= self._active(sheet, day)
        mappings = self.env["investra.role.account"].sudo().search([("company_id", "=", company.id)])
        missing = self.env["investra.account.role"]
        for mapping in mappings.filtered(lambda m: m.role_id not in covered.role_id):
            accounts = mapping.account_id | mapping.extra_account_ids
            if self._sum([*self._line_domain(company, day), ("account_id", "in", accounts.ids)]):
                missing |= mapping.role_id
        return missing

    def _accounts_without_role(self, company, day):
        """Účty s nenulovým zůstatkem, které nemají v knize roli; ve výkazu by chyběly. Výsledek běžného období
        (equity_unaffected) se do výkazu bere zvlášť (zdroj „result“)."""
        mappings = self.env["investra.role.account"].sudo().search([("company_id", "=", company.id)])
        covered = mappings.account_id | mappings.extra_account_ids
        groups = self.env["account.move.line"].sudo()._read_group(
            [*self._line_domain(company, day), ("account_id", "not in", covered.ids),
             ("account_id.account_type", "!=", "equity_unaffected")],
            groupby=["account_id"], aggregates=["balance:sum"],
        )
        return self.env["account.account"].union(*(account for account, balance in groups if round(balance or 0, 2)))
