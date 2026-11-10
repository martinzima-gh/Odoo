import io

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import UserError

PORTFOLIO_COLUMNS = [
    ("Druh", "kind"), ("Název", "name"), ("ISIN", "isin"), ("Měna", "currency"), ("Kusy", "quantity"), ("Cena", "price"),
    ("Zdroj ceny", "price_source"), ("Pořizovací hodnota v měně", "cost_currency"),
    ("Pořizovací hodnota v měně fondu", "cost"), ("Reálná hodnota v měně", "fair_value_currency"),
    ("Kurz", "fx_rate"), ("Zdroj kurzu", "fx_source"), ("Reálná hodnota v měně fondu", "fair_value"),
    ("Změna proti pořízení", "change"), ("Podíl na FK", "weight"),
]


class InvestraValuation(models.Model):
    _inherit = "investra.valuation"

    package_id = fields.Many2one("ir.attachment", readonly=True, string="Příloha balíčku")
    # Otisk souboru při sestavení: ocenění pozná, kdyby příloha neodpovídala tomu, co systém vytvořil.
    package_checksum = fields.Char(readonly=True, string="Otisk balíčku")
    package_file = fields.Binary(related="package_id.raw", string="Balíček pro depozitáře")
    package_name = fields.Char(related="package_id.name", string="Soubor balíčku")
    package_ok = fields.Boolean(compute="_compute_package_ok", string="Balíček odpovídá otisku")

    @api.depends("package_id", "package_checksum")
    def _compute_package_ok(self):
        for record in self:
            stored = record.package_checksum
            record.package_ok = not stored or record.package_id.sudo().checksum == stored

    def _package_rows_portfolio(self):
        kinds = dict(self.env["investra.valuation.portfolio"]._fields["kind"].selection)
        total = self.fund_capital or 1
        rows = []
        for line in self.portfolio_line_ids:
            rows.append({
                "kind": kinds[line.kind],
                "name": line.name,
                "isin": line.isin or "",
                "currency": line.currency_id.name,
                "quantity": line.quantity,
                "price": line.price,
                "price_source": line.price_source or "",
                "cost_currency": line.cost_currency,
                "cost": line.cost,
                "fair_value_currency": line.fair_value_currency,
                "fx_rate": line.fx_rate,
                "fx_source": {"cnb": "ČNB", "ecb": "ECB"}.get(line.fx_source, ""),
                "fair_value": line.fair_value,
                "change": line.fair_value - line.cost,
                "weight": line.fair_value / total,
            })
        return rows

    def _trial_balance(self):
        """Předvaha k datu ze zaúčtovaných dokladů, účet a zůstatek."""
        Line = self.env["account.move.line"].sudo()
        groups = Line._read_group(
            [("company_id", "=", self.company_id.id), ("date", "<=", self.date), ("parent_state", "=", "posted")],
            groupby=["account_id"],
            aggregates=["debit:sum", "credit:sum", "balance:sum"],
        )
        rows = [(a.code, a.name, debit, credit, balance) for a, debit, credit, balance in groups]
        return sorted(rows, key=lambda row: row[0] or "")

    def _nav_rows(self):
        """Rozpad NAV po rolích účtů, aktuální a předchozí ocenění a rozdíl."""
        roles = self.env["investra.role.account"].sudo().search([("company_id", "=", self.company_id.id)])
        rows = []
        for category, label in (("asset", "Aktiva"), ("liability", "Závazky")):
            selected = roles.filtered(lambda r: r.role_id.category == category).sorted(lambda r: r.account_id.code)
            current_total = previous_total = 0
            for mapping in selected:
                current = float(self._role_balance(mapping.role_id.code))
                previous = float(self.previous_id._role_balance(mapping.role_id.code)) if self.previous_id else 0.0
                rows.append((mapping.role_id.name, current, previous, current - previous))
                current_total += current
                previous_total += previous
            rows.append((label + " celkem", current_total, previous_total, current_total - previous_total))
        return rows

    def action_build_package(self):
        """Sestaví XLSX z uloženého ocenění: portfolio, NAV, předvaha, rozpis úplat. Až po zaúčtování."""
        self._require("investra_entity.group_valuation_preparer")
        self._require_state("posted", "sent", "confirmed", "published")
        record = self.sudo()
        record.ensure_one()
        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        bold = book.add_format({"bold": True, "bottom": 1})
        amount = book.add_format({"num_format": "# ##0.00"})
        ratio = book.add_format({"num_format": "0.00%"})
        title = book.add_format({"bold": True, "font_size": 13})

        def header(sheet, name):
            sheet.write(0, 0, f"{record.fund_id.name}: {name} k {record.date}, verze {record.version}", title)

        sheet = book.add_worksheet("Portfolio")
        header(sheet, "Portfolio")
        for column, (label, _key) in enumerate(PORTFOLIO_COLUMNS):
            sheet.write(2, column, label, bold)
        rows = record._package_rows_portfolio()
        for row_index, row in enumerate(rows, start=3):
            for column, (_label, key) in enumerate(PORTFOLIO_COLUMNS):
                value = row[key]
                style = ratio if key == "weight" else amount if isinstance(value, float) else None
                sheet.write(row_index, column, value, style)

        sheet = book.add_worksheet("NAV")
        header(sheet, "NAV")
        for column, label in enumerate(("Položka", "Aktuální ocenění", "Předchozí ocenění", "Rozdíl")):
            sheet.write(2, column, label, bold)
        index = 3
        for label, current, previous, change in record._nav_rows():
            sheet.write(index, 0, label)
            for column, value in enumerate((current, previous, change), start=1):
                sheet.write(index, column, value, amount)
            index += 1
        sheet.write(index, 0, "NAV (FK)", bold)
        sheet.write(index, 1, record.fund_capital, amount)
        index += 2
        for column, label in enumerate(("Třída", "Měna", "Kapitál", "Kusy", "Kurz", "Alokační poměr", "Specifická změna")):
            sheet.write(index, column, label, bold)
        index += 1
        for line in record.class_line_ids:
            for column, value in enumerate((line.class_id.code, line.class_id.currency_id.name, line.capital, line.units, line.price, line.ratio, line.delta)):
                sheet.write(index, column, value)
            index += 1

        sheet = book.add_worksheet("Přemostění tříd")
        header(sheet, "Přemostění tříd")
        bridge_columns = (
            ("Třída", lambda l: l.class_id.code, None),
            ("Měna", lambda l: l.class_id.currency_id.name, None),
            ("Kusy", lambda l: l.units, None),
            ("FK (t−1)", lambda l: l.opening_capital, amount),
            ("Úpisy ks", lambda l: l.subscription_units, None),
            ("Úpisy", lambda l: l.subscription_amount, amount),
            ("Odkupy ks", lambda l: l.redemption_units, None),
            ("Odkupy", lambda l: l.redemption_amount, amount),
            ("Dividendy", lambda l: l.dividend_amount, amount),
            ("Upravený FK", lambda l: l.pre_capital, amount),
            ("Alokační poměr", lambda l: l.ratio, None),
            ("Změna společná", lambda l: l.shared_result, amount),
            ("Z toho zaokrouhlení", lambda l: l.rounding_amount, amount),
            ("Změna specifická", lambda l: l.delta, amount),
            ("Úplaty třídy", lambda l: l.fee_amount, amount),
            ("Výkonnostní odměna", lambda l: l.performance_amount, amount),
            ("Přesun podle pořadí nároků", lambda l: l.allocation_amount, amount),
            ("Ostatní specifické", lambda l: l.other_amount, amount),
            ("FK", lambda l: l.capital, amount),
            ("FK v měně třídy", lambda l: l.capital_class, amount),
            ("Kurz (t−1)", lambda l: l.opening_price or "", None),
            ("Kurz", lambda l: l.price, None),
            ("Změna kurzu %", lambda l: l.price_change_pct, None),
            ("Kurz přepočtu", lambda l: l.fx_rate, None),
        )
        for column, (label, _value, _format) in enumerate(bridge_columns):
            sheet.write(2, column, label, bold)
        for row_index, line in enumerate(record.class_line_ids, start=3):
            for column, (_label, value, cell_format) in enumerate(bridge_columns):
                sheet.write(row_index, column, value(line), cell_format)

        sheet = book.add_worksheet("Předvaha")
        header(sheet, "Předvaha")
        for column, label in enumerate(("Účet", "Název", "MD", "D", "Zůstatek")):
            sheet.write(2, column, label, bold)
        for row_index, row in enumerate(record._trial_balance(), start=3):
            sheet.write(row_index, 0, row[0])
            sheet.write(row_index, 1, row[1])
            for column, value in enumerate(row[2:], start=2):
                sheet.write(row_index, column, value, amount)

        sheet = book.add_worksheet("Úplaty")
        header(sheet, "Úplaty")
        for column, label in enumerate(("Pravidlo", "Třída", "Částka", "Článek statutu")):
            sheet.write(2, column, label, bold)
        for row_index, line in enumerate(record.fee_line_ids, start=3):
            sheet.write(row_index, 0, line.rule_id.name)
            sheet.write(row_index, 1, line.class_id.code or "")
            sheet.write(row_index, 2, line.amount, amount)
            sheet.write(row_index, 3, line.rule_id.statute_ref or "")
        book.close()
        attachment = self.env["ir.attachment"].sudo().create({
            "name": f"balicek-{record.fund_id.name}-{record.date}-v{record.version}.xlsx",
            "raw": output.getvalue(),
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "res_model": "investra.valuation",
            "res_id": record.id,
        })
        record.write({"package_id": attachment.id, "package_checksum": attachment.checksum})
        return attachment
