from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import format_amount

SOON_DAYS = 7
# Stavy, ve kterých je ocenění zaúčtované; stejnou množinu bere výpočet jako předchozí ocenění.
POSTED_STATES = ("posted", "sent", "confirmed", "published")
# Stavy rozpracovaného ocenění před zaúčtováním (vrácené a stornované verze se přeskakují).
NEXT_STATES = ("draft", "computed", "submitted", "approved")
PREPARER = "investra_entity.group_valuation_preparer"
APPROVER = "investra_entity.group_valuation_approver"


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
    # Texty dat pro kartu: vždy dd.mm.rrrr (rozhodnutí 2026-11-13 „Formát data v aplikaci“); pole Date
    # v kanbanu u letošních dat vynechává rok.
    dashboard_date_text = fields.Char(compute="_compute_dashboard", string="Datum ocenění (text)")
    dashboard_latest_published = fields.Boolean(compute="_compute_dashboard", string="Poslední ocenění zveřejněno")
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
    dashboard_next_text = fields.Char(compute="_compute_dashboard", string="Další ocenění (text)")
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
    dashboard_deadline_due = fields.Char(compute="_compute_dashboard", string="Termín ČNB (text)")
    # Blok „Ke zpracování“ (rozhodnutí 2026-11-14 „Přehled fondů – Ke zpracování“): položky s počtem, rolí,
    # která je na řadě, a filtrem seznamu, který karta po kliknutí otevře. Jen čtení, nic se nemění.
    dashboard_todo = fields.Json(compute="_compute_dashboard", string="Ke zpracování")
    dashboard_todo_count = fields.Integer(compute="_compute_dashboard", string="Počet položek ke zpracování")
    dashboard_my_todo = fields.Boolean(
        compute="_compute_dashboard", search="_search_dashboard_my_todo", string="Čeká na můj krok"
    )
    dashboard_exceptions = fields.Text(compute="_compute_dashboard", string="Výjimky")
    dashboard_exception_count = fields.Integer(compute="_compute_dashboard", string="Počet výjimek")
    dashboard_status = fields.Selection(
        [("ok", "V pořádku"), ("warning", "Upozornění"), ("danger", "Vyžaduje zásah"), ("none", "Bez ocenění")],
        compute="_compute_dashboard",
        search="_search_dashboard_status",
        string="Stav",
    )

    def _dashboard_next_state_selection(self):
        """Stavy rozpracovaného ocenění převzaté z modelu ocenění beze změny popisků, navíc „Nezaloženo“."""
        states = dict(self.env["investra.valuation"]._fields["state"]._description_selection(self.env))
        return [(state, states[state]) for state in NEXT_STATES] + [("none", self.env._("Nezaloženo"))]

    # Blok Ke zpracování závisí na rolích přihlášeného uživatele: bez toho by se hodnoty sdílely mezi uživateli.
    @api.depends_context("uid", "allowed_company_ids")
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
        todo = self._dashboard_todo(today)
        warned = warning or any(item["warn"] for item in todo)
        status = "danger" if danger else "warning" if warned else "ok" if latest else "none"
        states = dict(Valuation._fields["state"]._description_selection(self.env))
        result, has_result, period = self._dashboard_result(latest)
        return {
            "dashboard_valuation_id": latest.id,
            "dashboard_date": latest.date,
            "dashboard_date_text": latest.date.strftime("%d.%m.%Y") if latest else False,
            "dashboard_latest_published": latest.state == "published",
            "dashboard_state": states.get(latest.state, False),
            "dashboard_capital": latest.fund_capital,
            "dashboard_result": result,
            "dashboard_has_result": has_result,
            "dashboard_result_period": period,
            "dashboard_published": published[:1].date,
            "dashboard_next_valuation": next_date,
            "dashboard_next_text": next_date.strftime("%d.%m.%Y") if next_date else False,
            "dashboard_next_valuation_id": upcoming.id,
            "dashboard_next_state": upcoming.state if upcoming else ("none" if next_date else False),
            "dashboard_next_version": upcoming.version,
            # Stejné pravidlo jako výjimka „Ocenění po termínu“; mimořádné ocenění mimo kalendář termín nemá.
            "dashboard_next_late": bool(entry and (entry.published_on or entry.date) < today),
            "dashboard_deadline_id": deadline.id,
            "dashboard_deadline_state": deadline_state,
            "dashboard_next_deadline": deadline_text,
            "dashboard_deadline_due": deadline.due_date.strftime("%d.%m.%Y") if deadline else False,
            "dashboard_todo": todo,
            "dashboard_todo_count": len(todo),
            "dashboard_my_todo": any(item["mine"] for item in todo),
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
        text = _("ČNB · %(report)s · období %(period)s", report=deadline.report, period=deadline.period_end.strftime("%m/%Y"))
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
        # Obchody po termínu vypořádání a ceny ke schválení jsou v bloku Ke zpracování (_dashboard_todo);
        # stav karty zvyšují na Upozornění přes příznak `warn` položky.
        return danger, warning

    def _dashboard_todo(self, today):
        """Položky bloku Ke zpracování: co ve fondu čeká na krok a kdo je na řadě.

        Role podle skupin (připravovatel / schvalovatel) a kroků ocenění: odeslat ke schválení, zaúčtovat
        a odeslat depozitáři dělá připravovatel; schválit, potvrdit za depozitáře a zveřejnit schvalovatel
        (u schválení a zveřejnění rozhoduje ještě schvalovací matice). `mine` = přihlášený uživatel má roli.
        Každá položka nese model a doménu seznamu, který karta po kliknutí otevře.
        """
        self.ensure_one()
        _ = self.env._
        user = self.env.user
        roles = {"preparer": user.has_group(PREPARER), "approver": user.has_group(APPROVER)}
        items = []

        def add(key, label, count, model, domain, role, warn=False, amount=None):
            if count:
                items.append({
                    "key": key, "label": label, "count": count, "amount": amount, "role": role,
                    "mine": bool(roles.get(role)), "warn": warn, "model": model, "domain": domain,
                })

        Valuation = self.env["investra.valuation"]
        steps = [
            (("draft", "computed"), _("Ocenění k dopracování"), "preparer"),
            (("submitted",), _("Ocenění ke schválení"), "approver"),
            (("approved",), _("Ocenění k zaúčtování"), "preparer"),
            (("posted",), _("Ocenění k odeslání depozitáři"), "preparer"),
            (("sent",), _("Ocenění k potvrzení za depozitáře"), "approver"),
            (("confirmed",), _("Ocenění ke zveřejnění"), "approver"),
        ]
        for states, label, role in steps:
            domain = [("fund_id", "=", self.id), ("state", "in", list(states))]
            add("valuation_" + states[0], label, Valuation.search_count(domain), "investra.valuation", domain, role)

        def simple(key, label, model, domain, role, warn=False):
            add(key, label, self.env[model].search_count(domain), model, domain, role, warn=warn)

        simple("events", _("Nezaúčtované návrhy dokladů"), "investra.accounting.event",
               [("fund_id", "=", self.id), ("state", "=", "draft")], "preparer")
        simple("movements", _("Úpisy a odkupy k zaúčtování"), "investra.class.movement",
               [("fund_id", "=", self.id), ("state", "=", "draft")], "preparer")
        simple("repayments", _("Návrhy splátek k zaúčtování"), "investra.instrument.repayment",
               [("fund_id", "=", self.id), ("state", "=", "draft")], "preparer")
        simple("trades", _("Obchody po termínu vypořádání"), "investra.trade",
               [("fund_id", "=", self.id), ("state", "=", "unsettled"), ("settlement_date", "<", fields.Date.to_string(today))],
               "preparer", warn=True)
        # Ceny fondu v návrhu a sdílené ceny v návrhu pro nástroje, které fond drží.
        instruments = self.env["investra.trade"].sudo()._positions(self, today)
        simple("prices", _("Ceny ke schválení"), "investra.instrument.price", [
            ("state", "=", "draft"), "|", ("fund_id", "=", self.id),
            "&", ("fund_id", "=", False), ("instrument_id", "in", [i.id for i in instruments]),
        ], "approver", warn=True)
        simple("requests", _("Žádosti ke schválení"), "investra.approval.request",
               [("company_id", "=", self.company_id.id), ("state", "=", "pending")], "approver")
        if "investra.fx.run" in self.env:
            simple("fx_runs", _("Přecenění kurzů k zaúčtování"), "investra.fx.run",
                   [("company_id", "=", self.company_id.id), ("move_id.state", "=", "draft")], "preparer")
        # Zůstatky, které mají být k datu ocenění nulové nebo vysvětlené (ve funkční měně fondu).
        Role = self.env["investra.account.role"]
        for code, label in (("unidentified_payment", _("Neidentifikované platby")), ("cash_in_transit", _("Peníze na cestě"))):
            accounts = Role.accounts_for(self.company_id, code)
            if not accounts:
                continue
            domain = [("company_id", "=", self.company_id.id), ("account_id", "in", accounts.ids), ("parent_state", "=", "posted")]
            balance = sum(self.env["account.move.line"].sudo().search(domain).mapped("balance"))
            if not self.currency_id.is_zero(balance):
                add(code, label, 1, "account.move.line", domain, "preparer",
                    amount=format_amount(self.env, balance, self.currency_id))
        return items

    def _search_dashboard_status(self, operator, value):
        if operator not in ("=", "in"):
            raise NotImplementedError(operator)
        values = {value} if isinstance(value, str) else set(value)
        return [("id", "in", self.search([]).filtered(lambda f: f.dashboard_status in values).ids)]

    def _search_dashboard_my_todo(self, operator, value):
        # Odoo 20 předává i tvar ("in", {True}); „!=“ a „not in“ obrací výsledek.
        values = {bool(v) for v in value} if isinstance(value, (list, tuple, set, frozenset)) else {bool(value)}
        if operator in ("!=", "not in"):
            values = {True, False} - values
        elif operator not in ("=", "in"):
            raise NotImplementedError(operator)
        return [("id", "in", self.search([]).filtered(lambda f: f.dashboard_my_todo in values).ids)]

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        """Přehled fondů řadí karty podle naléhavosti (Vyžaduje zásah, Upozornění, V pořádku, Bez ocenění), pak názvu.

        Stav je počítaný a neukládá se, proto se řadí v Pythonu; fondů je řádově desítky.
        """
        if not self.env.context.get("investra_dashboard_order"):
            return super().web_search_read(domain, specification, offset=offset, limit=limit, order=order,
                                           count_limit=count_limit)
        funds = self.search(domain)
        rank = {"danger": 0, "warning": 1, "ok": 2, "none": 3}
        funds = funds.sorted(lambda f: (rank.get(f.dashboard_status, 4), (f.name or "").lower()))
        page = funds[offset:offset + limit] if limit else funds[offset:]
        return {"length": len(funds), "records": page.web_read(specification)}

    def action_open_todo(self, key):
        """Otevře seznam položky Ke zpracování (doménu počítá model, karta ji jen předá)."""
        self.ensure_one()
        item = next((i for i in self.dashboard_todo or [] if i["key"] == key), None)
        if not item:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name}: {item['label']}",
            "res_model": item["model"],
            "domain": item["domain"],
            "views": [(False, "list"), (False, "form")],
            "context": {"create": False},
        }

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
