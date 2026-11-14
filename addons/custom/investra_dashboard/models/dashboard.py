from datetime import timedelta

from odoo import fields, models

SOON_DAYS = 7
# Stavy, ve kterých je ocenění zaúčtované; stejnou množinu bere výpočet jako předchozí ocenění.
POSTED_STATES = ("posted", "sent", "confirmed", "published")
# Stavy rozpracovaného ocenění před zaúčtováním (vrácené a stornované verze se přeskakují).
NEXT_STATES = ("draft", "computed", "submitted", "approved")


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

    # Data a stavy karty Přehledu fondů (rozhodnutí 2026-11-14 „Přehled fondů – data a stavy karty“).
    # Poslední ocenění = nejnovější zaúčtované (stejná množina stavů jako předchozí ocenění ve výpočtu),
    # z něj FK a výsledek období ocenění. Vše ve funkční měně fondu, bez součtů napříč fondy.
    dashboard_valuation_id = fields.Many2one("investra.valuation", compute="_compute_dashboard", string="Poslední ocenění")
    dashboard_date = fields.Date(compute="_compute_dashboard", string="Datum ocenění")
    dashboard_state = fields.Char(compute="_compute_dashboard", string="Stav ocenění")
    dashboard_capital = fields.Monetary(compute="_compute_dashboard", string="FK", currency_field="currency_id")
    dashboard_result = fields.Monetary(
        compute="_compute_dashboard", string="Výsledek za období", currency_field="currency_id",
        help="Součet společné a specifické změny tříd posledního ocenění, tj. změna FK bez úpisů, odkupů a dividend. "
             "Není to výkonnost fondu ani účetní výsledek hospodaření.",
    )
    dashboard_has_result = fields.Boolean(compute="_compute_dashboard", string="Má výsledek za období")
    dashboard_result_period = fields.Char(compute="_compute_dashboard", string="Období výsledku")
    dashboard_published = fields.Date(compute="_compute_dashboard", string="Poslední zveřejnění")
    dashboard_next_valuation = fields.Date(compute="_compute_dashboard", string="Další ocenění")
    dashboard_next_valuation_id = fields.Many2one(
        "investra.valuation", compute="_compute_dashboard", string="Rozpracované ocenění"
    )
    dashboard_next_state = fields.Selection(
        selection="_dashboard_next_state_selection", compute="_compute_dashboard", string="Stav dalšího ocenění"
    )
    dashboard_next_version = fields.Integer(compute="_compute_dashboard", string="Verze dalšího ocenění")
    dashboard_next_late = fields.Boolean(compute="_compute_dashboard", string="Další ocenění po termínu")
    dashboard_deadline_id = fields.Many2one(
        "investra.regulatory.deadline", compute="_compute_dashboard", string="Termín ČNB"
    )
    dashboard_deadline_state = fields.Selection(
        [("overdue", "Po lhůtě"), ("open", "Otevřeno"), ("submitted", "Podáno")],
        compute="_compute_dashboard",
        string="Stav termínu ČNB",
    )
    dashboard_next_deadline = fields.Char(compute="_compute_dashboard", string="Další termín ČNB")
    dashboard_exceptions = fields.Text(compute="_compute_dashboard", string="Výjimky")
    dashboard_exception_count = fields.Integer(compute="_compute_dashboard", string="Počet výjimek")
    dashboard_status = fields.Selection(
        [("ok", "V pořádku"), ("warning", "Upozornění"), ("danger", "Vyžaduje zásah"), ("none", "Bez ocenění")],
        compute="_compute_dashboard",
        string="Stav",
    )

    def _dashboard_next_state_selection(self):
        """Stavy rozpracovaného ocenění převzaté z modelu ocenění beze změny popisků, navíc „Nezaloženo“."""
        states = dict(self.env["investra.valuation"]._fields["state"]._description_selection(self.env))
        return [(state, states[state]) for state in NEXT_STATES] + [("none", self.env._("Nezaloženo"))]

    def _compute_dashboard(self):
        today = fields.Date.context_today(self)
        for fund in self:
            fund.update(fund.sudo()._dashboard_values(today))

    def _dashboard_values(self, today):
        self.ensure_one()
        Valuation = self.env["investra.valuation"]
        latest = Valuation.search(
            [("fund_id", "=", self.id), ("state", "in", POSTED_STATES)], order="date desc, version desc", limit=1
        )
        published = Valuation.search([("fund_id", "=", self.id), ("state", "=", "published")], order="date desc")
        missing = self.env["investra.valuation.calendar"].search(
            [("fund_id", "=", self.id), ("date", "not in", published.mapped("date"))], order="date"
        )
        upcoming, entry, next_date = self._dashboard_next(latest)
        deadlines = self.env["investra.regulatory.deadline"].search(
            [("fund_id", "=", self.id), ("state", "=", "open")], order="due_date, id"
        )
        deadline, deadline_state, deadline_text = self._dashboard_deadline(deadlines, today)
        danger, warning = self._dashboard_exceptions(latest, missing, deadlines, today, checked=upcoming or latest)
        status = "danger" if danger else "warning" if warning else "ok" if latest else "none"
        states = dict(Valuation._fields["state"]._description_selection(self.env))
        result, has_result, period = self._dashboard_result(latest)
        return {
            "dashboard_valuation_id": latest.id,
            "dashboard_date": latest.date,
            "dashboard_state": states.get(latest.state, False),
            "dashboard_capital": latest.fund_capital,
            "dashboard_result": result,
            "dashboard_has_result": has_result,
            "dashboard_result_period": period,
            "dashboard_published": published[:1].date,
            "dashboard_next_valuation": next_date,
            "dashboard_next_valuation_id": upcoming.id,
            "dashboard_next_state": upcoming.state if upcoming else ("none" if next_date else False),
            "dashboard_next_version": upcoming.version,
            # Stejné pravidlo jako výjimka „Ocenění po termínu“; mimořádné ocenění mimo kalendář termín nemá.
            "dashboard_next_late": bool(entry and (entry.published_on or entry.date) < today),
            "dashboard_deadline_id": deadline.id,
            "dashboard_deadline_state": deadline_state,
            "dashboard_next_deadline": deadline_text,
            "dashboard_exceptions": "\n".join(danger + warning),
            "dashboard_exception_count": len(danger) + len(warning),
            "dashboard_status": status,
        }

    def _dashboard_next(self, latest):
        """Další ocenění po posledním zaúčtovaném: první datum z kalendáře, mimořádné ocenění dřív má přednost.

        Vrátí rozpracované ocenění k tomu datu (nejvyšší verze, která není vrácená ani stornovaná),
        položku kalendáře a datum. Bez rozpracovaného ocenění je stav „Nezaloženo“.
        """
        after = [("fund_id", "=", self.id)] + ([("date", ">", latest.date)] if latest else [])
        entry = self.env["investra.valuation.calendar"].search(after, order="date", limit=1)
        upcoming = self.env["investra.valuation"].search(
            after + [("state", "in", NEXT_STATES)], order="date, version desc", limit=1
        )
        if entry and (not upcoming or entry.date < upcoming.date):
            upcoming = upcoming.browse()
        next_date = upcoming.date if upcoming else entry.date
        if entry.date != next_date:
            entry = entry.browse()
        return upcoming, entry, next_date or False

    def _dashboard_deadline(self, deadlines, today):
        """Termín ČNB na kartu: nejstarší po lhůtě, jinak nejbližší otevřený, jinak poslední podaný.

        Otevřené termíny jsou seřazené podle termínu, takže první je zároveň nejstarší po lhůtě.
        Datum podání model nemá, proto se u podaného výkazu ukazuje jen termín.
        """
        _ = self.env._
        deadline = deadlines[:1]
        if deadline:
            state = "overdue" if deadline.due_date < today else "open"
        else:
            deadline = self.env["investra.regulatory.deadline"].search(
                [("fund_id", "=", self.id), ("state", "=", "submitted")], order="period_end desc, due_date desc, id desc", limit=1
            )
            state = "submitted" if deadline else False
        if not deadline:
            return deadline, False, False
        text = _("%(report)s · období %(period)s · termín %(due)s",
                 report=deadline.report, period=deadline.period_end.strftime("%m/%Y"),
                 due=deadline.due_date.strftime("%d.%m.%Y"))
        if len(deadlines) > 1:
            text += _(" (+%s další)", len(deadlines) - 1)
        return deadline, state, text

    def _dashboard_result(self, latest):
        """Výsledek období ocenění: společná + specifická změna přes třídy (stejný zdroj jako detail ocenění).

        U prvního ocenění fondu výsledek není (karta ukáže pomlčku). Období je od dne po předchozím ocenění.
        """
        if not latest or not latest.previous_id:
            return 0.0, False, False
        lines = latest.class_line_ids
        result = self.currency_id.round(sum(lines.mapped("shared_result")) + sum(lines.mapped("delta")))
        start = latest.previous_id.date + timedelta(days=1)
        end = latest.date
        period = f"{start.strftime('%d.%m.' if start.year == end.year else '%d.%m.%Y')}–{end.strftime('%d.%m.%Y')}"
        return result, True, period

    def _dashboard_exceptions(self, latest, missing, deadlines, today, checked=None):
        """Vrátí výjimky vyžadující zásah a upozornění jako texty.

        Kontroly se berou z rozpracovaného dalšího ocenění, bez něj z posledního zaúčtovaného (`checked`).
        """
        checked = latest if checked is None else checked
        _ = self.env._
        danger, warning = [], []
        late = missing.filtered(lambda c: (c.published_on or c.date) < today)
        if late:
            danger.append(_("Ocenění po termínu: %s", len(late)))
        if self._dashboard_returned(latest):
            danger.append(_("Ocenění je vrácené"))
        stops = checked.check_ids.filtered(lambda c: c.status == "stop")
        warnings = checked.check_ids.filtered(lambda c: c.status == "warning")
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

    def _dashboard_returned(self, latest):
        """Vrácené ocenění po posledním zaúčtovaném, ke kterému nezůstala žádná živá verze (nová verze smazaná)."""
        Valuation = self.env["investra.valuation"]
        after = [("fund_id", "=", self.id)] + ([("date", ">", latest.date)] if latest else [])
        returned = Valuation.search(after + [("state", "=", "returned")])
        if not returned:
            return False
        alive = Valuation.search(after + [("state", "not in", ("returned", "reversed")), ("date", "in", returned.mapped("date"))])
        return bool(set(returned.mapped("date")) - set(alive.mapped("date")))

    def action_open_valuation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.valuation",
            "res_id": self.dashboard_valuation_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }

    def action_open_next_valuation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.valuation",
            "res_id": self.dashboard_next_valuation_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }
