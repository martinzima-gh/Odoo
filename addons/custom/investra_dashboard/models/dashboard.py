from datetime import timedelta

from odoo import fields, models

SOON_DAYS = 7


class InvestraRegulatoryDeadline(models.Model):
    """Termín podání; zdrojem bude SDAT. Dashboard ho jen vyhodnocuje a nic nepodává."""

    _name = "investra.regulatory.deadline"
    _inherit = ["investra.record.guard"]
    _description = "Termín podání ČNB"
    _order = "due_date, id"
    _book_fields = ("fund_id",)

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    report = fields.Char(required=True, string="Výkaz")
    period_end = fields.Date(required=True, string="Období do")
    due_date = fields.Date(required=True, string="Termín")
    state = fields.Selection([("open", "Otevřeno"), ("submitted", "Podáno")], required=True, default="open", string="Stav")
    source = fields.Selection(
        [("example", "Příklad"), ("manual", "Ručně"), ("sdat", "SDAT")], required=True, default="manual", string="Zdroj"
    )

    _uniq = models.Constraint("unique(fund_id, report, period_end)", "Termín výkazu za období už existuje.")


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    dashboard_valuation_id = fields.Many2one("investra.valuation", compute="_compute_dashboard", string="Poslední ocenění")
    dashboard_date = fields.Date(compute="_compute_dashboard", string="Datum ocenění")
    dashboard_state = fields.Char(compute="_compute_dashboard", string="Stav ocenění")
    dashboard_capital = fields.Monetary(compute="_compute_dashboard", string="FK", currency_field="currency_id")
    dashboard_published = fields.Date(compute="_compute_dashboard", string="Poslední zveřejnění")
    dashboard_prices = fields.Text(compute="_compute_dashboard", string="Kurzy tříd")
    dashboard_next_valuation = fields.Date(compute="_compute_dashboard", string="Další ocenění")
    dashboard_next_deadline = fields.Char(compute="_compute_dashboard", string="Další termín ČNB")
    dashboard_exceptions = fields.Text(compute="_compute_dashboard", string="Výjimky")
    dashboard_exception_count = fields.Integer(compute="_compute_dashboard", string="Počet výjimek")
    dashboard_status = fields.Selection(
        [("ok", "V pořádku"), ("warning", "Upozornění"), ("danger", "Vyžaduje zásah"), ("none", "Bez ocenění")],
        compute="_compute_dashboard",
        string="Stav",
    )

    def _compute_dashboard(self):
        today = fields.Date.context_today(self)
        for fund in self:
            fund.update(fund.sudo()._dashboard_values(today))

    def _dashboard_values(self, today):
        self.ensure_one()
        Valuation = self.env["investra.valuation"]
        latest = Valuation.search(
            [("fund_id", "=", self.id), ("state", "!=", "reversed")], order="date desc, version desc", limit=1
        )
        published = Valuation.search([("fund_id", "=", self.id), ("state", "=", "published")], order="date desc")
        missing = self.env["investra.valuation.calendar"].search(
            [("fund_id", "=", self.id), ("date", "not in", published.mapped("date"))], order="date"
        )
        deadlines = self.env["investra.regulatory.deadline"].search(
            [("fund_id", "=", self.id), ("state", "=", "open")], order="due_date"
        )
        danger, warning = self._dashboard_exceptions(latest, missing, deadlines, today)
        status = "danger" if danger else "warning" if warning else "ok" if latest else "none"
        states = dict(Valuation._fields["state"]._description_selection(self.env))
        first = deadlines[:1]
        return {
            "dashboard_valuation_id": latest.id,
            "dashboard_date": latest.date,
            "dashboard_state": states.get(latest.state, False),
            "dashboard_capital": latest.fund_capital,
            "dashboard_published": published[:1].date,
            "dashboard_prices": "\n".join(
                f"{line.class_id.code}: {line.price} {line.class_id.currency_id.name}"
                for line in latest.class_line_ids
            ),
            "dashboard_next_valuation": missing[:1].date,
            "dashboard_next_deadline": f"{first.report}: {first.due_date}" if first else False,
            "dashboard_exceptions": "\n".join(danger + warning),
            "dashboard_exception_count": len(danger) + len(warning),
            "dashboard_status": status,
        }

    def _dashboard_exceptions(self, latest, missing, deadlines, today):
        """Vrátí výjimky vyžadující zásah a upozornění jako texty."""
        _ = self.env._
        danger, warning = [], []
        late = missing.filtered(lambda c: (c.published_on or c.date) < today)
        if late:
            danger.append(_("Ocenění po termínu: %s", len(late)))
        if latest.state == "returned":
            danger.append(_("Ocenění je vrácené"))
        stops = latest.check_ids.filtered(lambda c: c.status == "stop")
        warnings = latest.check_ids.filtered(lambda c: c.status == "warning")
        if stops:
            danger.append(_("Kontroly se stopem: %s", len(stops)))
        if warnings:
            warning.append(_("Kontroly s upozorněním: %s", len(warnings)))
        overdue = deadlines.filtered(lambda d: d.due_date < today)
        soon = deadlines.filtered(lambda d: today <= d.due_date <= today + timedelta(days=SOON_DAYS))
        if overdue:
            danger.append(_("Termíny ČNB po lhůtě: %s", len(overdue)))
        if soon:
            warning.append(_("Termíny ČNB do %(days)s dnů: %(count)s", days=SOON_DAYS, count=len(soon)))
        unsettled = self.env["investra.trade"].search_count(
            [("fund_id", "=", self.id), ("state", "=", "unsettled"), ("settlement_date", "<", today)]
        )
        if unsettled:
            warning.append(_("Obchody po termínu vypořádání: %s", unsettled))
        # Ceny fondu v návrhu a sdílené ceny v návrhu pro nástroje, které fond drží.
        instruments = self.env["investra.trade"].sudo()._positions(self, today)
        prices = self.env["investra.instrument.price"].sudo().search_count([
            ("state", "=", "draft"), "|", ("fund_id", "=", self.id),
            "&", ("fund_id", "=", False), ("instrument_id", "in", [i.id for i in instruments]),
        ])
        if prices:
            warning.append(_("Ceny čekající na schválení: %s", prices))
        return danger, warning

    def action_open_valuation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.valuation",
            "res_id": self.dashboard_valuation_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }
