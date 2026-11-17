from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import format_amount

from odoo.addons.investra_fund.models.approval_matrix import APPROVE, PERFORM, user_can
from odoo.addons.investra_fund.models.schedule import next_valuation_date

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
    # Čisté úpisy − odkupy za stejné období jako výsledek (rozhodnutí 2026-11-15): zaúčtované pohyby tříd
    # s datem v období, změna kapitálu ve funkční měně; úpis kladně, odkup záporně.
    dashboard_net_flow = fields.Monetary(
        compute="_compute_dashboard", string="Úpisy − odkupy", currency_field="currency_id",
        help="Zaúčtované úpisy minus odkupy s datem v období posledního ocenění, změna kapitálu ve funkční měně.",
    )
    # Uzávěrka: zámek období knihy fondu (nastavuje zveřejnění ocenění) a právě platné výjimky ze zámku.
    dashboard_lock_text = fields.Char(compute="_compute_dashboard", string="Uzamčeno do")
    dashboard_lock_exception_count = fields.Integer(compute="_compute_dashboard", string="Platné výjimky ze zámku")
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
    dashboard_deadline_id = fields.Many2one(
        "investra.regulatory.deadline", compute="_compute_dashboard", string="Termín ČNB"
    )
    dashboard_deadline_state = fields.Selection(
        [("overdue", "Po lhůtě"), ("open", "Otevřeno"), ("submitted", "Podáno")],
        compute="_compute_dashboard",
        search="_search_dashboard_deadline_state",
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
        upcoming, next_date = self._dashboard_next(latest)
        deadlines = self.env["investra.regulatory.deadline"].search(
            [("fund_id", "=", self.id), ("state", "=", "open")], order="due_date, id"
        )
        deadline, deadline_state, deadline_text = self._dashboard_deadline(deadlines, today)
        danger, warning = self._dashboard_exceptions(
            latest, deadlines, today, checked=upcoming or self._dashboard_unpublished(latest)
        )
        todo = self._dashboard_todo(today, next_date)
        warned = warning or any(item["warn"] for item in todo)
        status = "danger" if danger else "warning" if warned else "ok" if latest else "none"
        states = dict(Valuation._fields["state"]._description_selection(self.env))
        result, has_result, period = self._dashboard_result(latest)
        lock = self.company_id.fiscalyear_lock_date
        exceptions = self.env["investra.lock.exception.request"].search_count([
            ("company_id", "=", self.company_id.id), ("state", "=", "active"), ("end_datetime", ">", fields.Datetime.now()),
        ])
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
            "dashboard_net_flow": self._dashboard_net_flow(latest) if has_result else 0.0,
            "dashboard_lock_text": lock.strftime("%d.%m.%Y") if lock else False,
            "dashboard_lock_exception_count": exceptions,
            "dashboard_published": published[:1].date,
            "dashboard_next_valuation": next_date,
            "dashboard_next_text": next_date.strftime("%d.%m.%Y") if next_date else False,
            "dashboard_next_valuation_id": upcoming.id,
            "dashboard_next_state": upcoming.state if upcoming else ("none" if next_date else False),
            "dashboard_next_version": upcoming.version,
            "dashboard_deadline_id": deadline.id,
            "dashboard_deadline_state": deadline_state,
            "dashboard_next_deadline": deadline_text,
            "dashboard_deadline_due": deadline.due_date.strftime("%d.%m.%Y") if deadline else False,
            "dashboard_todo": todo,
            # Výhledové položky (info) jsou jen informace, do počtu práce se nepočítají.
            "dashboard_todo_count": len([item for item in todo if not item["info"]]),
            "dashboard_my_todo": any(item["mine"] for item in todo),
            "dashboard_exceptions": "\n".join(danger + warning),
            "dashboard_exception_count": len(danger) + len(warning),
            "dashboard_status": status,
        }

    def _dashboard_next(self, latest):
        """Další ocenění po posledním zaúčtovaném: očekávané datum z frekvence fondu (MN-14), dřívější
        rozpracované nebo mimořádné ocenění má přednost.

        Očekávané datum = `next_valuation_date` z data posledního zaúčtovaného ocenění, u prvního z Data
        vzniku fondu. Vrátí rozpracované ocenění (nejvyšší verze, která není vrácená ani stornovaná) a datum.
        Bez rozpracovaného ocenění je stav „Nezaloženo“; bez data vzniku a bez ocenění datum není.
        """
        after = [("fund_id", "=", self.id)] + ([("date", ">", latest.date)] if latest else [])
        upcoming = self.env["investra.valuation"].search(
            after + [("state", "in", NEXT_STATES)], order="date, version desc", limit=1
        )
        expected = next_valuation_date(latest.date if latest else self.launch_date, self.valuation_frequency)
        if upcoming and (not expected or upcoming.date <= expected):
            return upcoming, upcoming.date
        return upcoming.browse(), expected

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

    @staticmethod
    def _dashboard_unpublished(latest):
        """Poslední zaúčtované ocenění, jen dokud není zveřejněné a uzamčené."""
        return latest if latest.state != "published" else latest.browse()

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

    def _dashboard_net_flow(self, latest):
        """Úpisy minus odkupy za období posledního ocenění (od dne po předchozím ocenění do data ocenění)."""
        groups = self.env["investra.class.movement"]._read_group(
            [("fund_id", "=", self.id), ("state", "=", "posted"),
             ("date", ">", latest.previous_id.date), ("date", "<=", latest.date)],
            ["movement_type"], ["capital_amount:sum"],
        )
        return self.currency_id.round(sum(
            (1 if movement_type == "subscription" else -1) * (amount or 0.0) for movement_type, amount in groups
        ))

    def _dashboard_exceptions(self, latest, deadlines, today, checked=None):
        """Vrátí výjimky vyžadující zásah a upozornění jako texty.

        Kontroly se berou z rozpracovaného dalšího ocenění, bez něj z posledního zaúčtovaného, dokud není
        zveřejněné (`checked`); kontroly zveřejněného a uzamčeného ocenění už karta neukazuje (rozhodnutí 2026-11-15).
        """
        checked = latest if checked is None else checked
        _ = self.env._
        danger, warning = [], []
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

    def _dashboard_todo(self, today, next_date=False):
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

        def add(key, label, count, model, domain, role, warn=False, amount=None, info=False):
            if count:
                items.append({
                    "key": key, "label": label, "count": count, "amount": amount, "role": role,
                    "mine": bool(roles.get(role)) and not info, "warn": warn, "info": info,
                    "model": model, "domain": domain,
                })

        Valuation = self.env["investra.valuation"]
        Matrix = self.env["investra.approval.matrix"]
        steps = [
            (("draft", "computed"), _("Ocenění k dopracování"), "preparer"),
            (("submitted",), _("Ocenění ke schválení"), "approver"),
            (("approved",), _("Ocenění k zaúčtování"), "preparer"),
            (("posted",), _("Ocenění k odeslání depozitáři"), "preparer"),
            (("sent",), _("Ocenění k potvrzení za depozitáře"), "approver"),
            (("confirmed",), _("Ocenění ke zveřejnění"), "approver"),
        ]
        # Počty ocenění podle stavu jedním dotazem (dřív šest dotazů na kartu).
        counts = dict(Valuation._read_group([("fund_id", "=", self.id)], ["state"], ["__count"]))
        for states, label, role in steps:
            domain = [("fund_id", "=", self.id), ("state", "in", list(states))]
            add("valuation_" + states[0], label, sum(counts.get(state, 0) for state in states), "investra.valuation", domain, role)

        def simple(key, label, model, domain, role, warn=False, info=False):
            add(key, label, self.env[model].search_count(domain), model, domain, role, warn=warn, info=info)

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
        # Nástroje bez použitelné ceny k dalšímu ocenění; jen když den ocenění už nastal (dřív cena být nemůže).
        if next_date and next_date <= today:
            unpriced = self._dashboard_unpriced(next_date)
            add("missing_prices", _("Nástroje bez aktuální ceny k ocenění"), len(unpriced), "investra.instrument",
                [("id", "in", unpriced)], "preparer", warn=True)
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
            balance = self.env["account.move.line"].sudo()._read_group(domain, [], ["balance:sum"])[0][0] or 0.0
            if not self.currency_id.is_zero(balance):
                add(code, label, 1, "account.move.line", domain, "preparer",
                    amount=format_amount(self.env, balance, self.currency_id))
        # Výhled na SOON_DAYS dnů: jen informace, stav karty nemění a „můj krok“ nemá.
        soon = [("date", ">=", fields.Date.to_string(today)), ("date", "<=", fields.Date.to_string(today + timedelta(days=SOON_DAYS)))]
        held = [i.id for i in instruments]
        simple("soon_flows", _("Splátky a kupóny do %s dnů", SOON_DAYS), "investra.instrument.cashflow",
               [("instrument_id", "in", held)] + soon, "preparer", info=True)
        simple("soon_settlements", _("Vypořádání obchodů do %s dnů", SOON_DAYS), "investra.trade",
               [("fund_id", "=", self.id), ("state", "=", "unsettled")]
               + [("settlement_date", leaf[1], leaf[2]) for leaf in soon], "preparer", info=True)
        simple("soon_maturities", _("Splatnost nástrojů do %s dnů", SOON_DAYS), "investra.instrument",
               [("id", "in", held)] + [("maturity_date", leaf[1], leaf[2]) for leaf in soon], "preparer", info=True)
        # „Můj krok“ u kroků řízených schvalovací maticí: rozhodují role uživatele (Provádí / Schvaluje, role kroku)
        # a jiná osoba než zadavatel, ne jen skupina. Ostatní kroky zůstávají podle skupiny.
        matrix = {
            "valuation_submitted": lambda records: any(self._dashboard_can_approve(v, user) for v in records),
            "valuation_confirmed": lambda records: self._dashboard_can_perform(
                Matrix._rule("valuation_publish"), user),
            "prices": lambda records: any(self._dashboard_can_approve_price(p, user) for p in records),
            "requests": lambda records: any(self._dashboard_can_confirm(r, user) for r in records),
        }
        for item in items:
            if item["key"] in matrix:
                item["mine"] = bool(matrix[item["key"]](self.env[item["model"]].search(item["domain"])))
        # Pořadí: nejdřív můj krok, pak varování, jinak pořadí pracovního postupu (řazení je stabilní).
        items.sort(key=lambda item: (item["info"], not item["mine"], not item["warn"]))
        return items

    def _dashboard_unpriced(self, day):
        """Držené nástroje, které ocenění k `day` neocení nebo na ně upozorní: bez schválené ceny, nebo s cenou
        starší než maximální stáří nástroje. Stejná pravidla jako `investra.valuation._approved_price`
        a kontrola `price_age`; nástroje v naběhlé hodnotě cenu nepotřebují."""
        Classification = self.env["investra.portfolio.classification"]
        Price = self.env["investra.instrument.price"]
        found = set()
        for (instrument, portfolio), quantity in self.env["investra.trade"].sudo()._holdings(self, day).items():
            if instrument.id in found or not quantity:
                continue
            if Classification._valid(portfolio, instrument, day).valuation_method == "amortised":
                continue
            price = Price.search([
                ("instrument_id", "=", instrument.id), ("date", "<=", day), ("state", "=", "approved"),
                "|", ("fund_id", "=", self.id), ("fund_id", "=", False),
            ], order="date desc", limit=1)
            if not price or (day - price.date).days > instrument.max_price_age:
                found.add(instrument.id)
        return sorted(found)

    def _dashboard_can_perform(self, rule, user):
        """Má uživatel roli s činností pravidla a příznakem Provádí? Stejné pravidlo jako `check_user` matice."""
        return user_can(self.env, user, rule.activity, PERFORM)

    def _dashboard_can_approve(self, valuation, user):
        """Smí uživatel schválit další krok ocenění? Podmínky jako `investra.valuation.action_approve`."""
        step = valuation.approval_ids.filtered(lambda a: not a.user_id).sorted("sequence")[:1]
        if not step or not user_can(self.env, user, "valuation_approve", PERFORM if step.alone else APPROVE, step.role_id):
            return False
        return step.alone or (valuation.preparer_id != user and user not in valuation.approval_ids.user_id)

    def _dashboard_can_approve_price(self, price, user):
        """Smí uživatel schválit cenu? Podmínky jako `investra.approval.matrix._approve_step`."""
        rule = self.env["investra.approval.matrix"]._rule("price_approve")
        if rule.persons == 1:
            return self._dashboard_can_perform(rule, user)
        done = self.env["investra.approval.done"].search([("res_model", "=", price._name), ("res_id", "=", price.id)])
        step = rule.steps[min(len(done), len(rule.steps) - 1)]
        performers = price.entered_by | price.create_uid
        return (user_can(self.env, user, "price_approve", APPROVE, step.role)
                and user not in performers and user not in done.user_id)

    def _dashboard_can_confirm(self, request, user):
        """Smí uživatel potvrdit žádost? Podmínky jako `investra.approval.request.action_approve`."""
        lines = request.line_ids.sorted("sequence")
        line = lines.filtered(lambda l: not l.user_id)[:1]
        if not line or not user_can(self.env, user, request.activity, APPROVE, line.role_id):
            return False
        return user != request.requested_by and user not in lines.user_id

    def _search_dashboard_status(self, operator, value):
        if operator not in ("=", "in"):
            raise NotImplementedError(operator)
        values = {value} if isinstance(value, str) else set(value)
        return [("id", "in", self.search([]).filtered(lambda f: f.dashboard_status in values).ids)]


    def _search_dashboard_deadline_state(self, operator, value):
        if operator not in ("=", "in"):
            raise NotImplementedError(operator)
        values = {value} if isinstance(value, (str, bool)) else set(value)
        return [("id", "in", self.search([]).filtered(lambda f: f.dashboard_deadline_state in values).ids)]

    def _search_dashboard_my_todo(self, operator, value):
        return self._search_dashboard_bool("dashboard_my_todo", operator, value)

    def _search_dashboard_bool(self, name, operator, value):
        # Odoo 20 předává i tvar ("in", {True}); „!=“ a „not in“ obrací výsledek.
        values = {bool(v) for v in value} if isinstance(value, (list, tuple, set, frozenset)) else {bool(value)}
        if operator in ("!=", "not in"):
            values = {True, False} - values
        elif operator not in ("=", "in"):
            raise NotImplementedError(operator)
        return [("id", "in", self.search([]).filtered(lambda f: bool(f[name]) in values).ids)]

    @api.model
    def dashboard_summary(self):
        """Souhrnný pás nad kartami: počty fondů podle stavu. Jen počty, žádné součty částek napříč fondy
        (rozhodnutí 2026-11-14). `filter` je název filtru vyhledávání, který pás po kliknutí přepne."""
        _ = self.env._
        funds = self.search([])
        cards = [
            ("danger", _("Vyžaduje zásah"), "filter_danger", lambda f: f.dashboard_status == "danger"),
            ("warning", _("Upozornění"), "filter_warning", lambda f: f.dashboard_status == "warning"),
            ("mine", _("Čeká na můj krok"), "filter_my_todo", lambda f: f.dashboard_my_todo),
        ]
        return {
            "total": len(funds),
            "cards": [
                {"key": key, "label": label, "filter": name, "count": len(funds.filtered(test))}
                for key, label, name, test in cards
            ],
        }

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

    def action_open_fund(self):
        """Otevře formulář fondu (akce Přehledu má jen karty a tabulku)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.fund",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }

    def action_open_checks(self):
        """Otevře kontroly ocenění, ze kterého karta bere výjimky: rozpracované další, jinak poslední zaúčtované,
        dokud není zveřejněné."""
        self.ensure_one()
        valuation = self.dashboard_next_valuation_id or self._dashboard_unpublished(self.dashboard_valuation_id)
        if not valuation:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("%s: kontroly ocenění", valuation.display_name),
            "res_model": "investra.valuation.check",
            "domain": [("valuation_id", "=", valuation.id), ("status", "!=", "ok")],
            "views": [(False, "list")],
            "context": {"create": False},
        }

    def action_open_deadlines(self):
        """Otevře termíny ČNB fondu; výchozí filtr Otevřeno, pokud nějaký otevřený je."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("investra_dashboard.action_deadline")
        action["name"] = self.env._("%s: termíny ČNB", self.name)
        action["domain"] = [("fund_id", "=", self.id)]
        action["context"] = {"search_default_filter_open": 1} if self.dashboard_deadline_state in ("open", "overdue") else {}
        return action

    def action_open_valuation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "investra.valuation",
            "res_id": self.dashboard_valuation_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
        }

    def action_create_next_valuation(self):
        """Otevře nový návrh ocenění s předvyplněným fondem a očekávaným datem (`_dashboard_next`); datum lze přepsat.

        Nic nezaloží: návrh vznikne až uložením formuláře a kontroly pořadí ocenění platí jako při ručním zadání.
        """
        self.ensure_one()
        context = {"default_fund_id": self.id}
        if self.dashboard_next_valuation:
            context["default_date"] = fields.Date.to_string(self.dashboard_next_valuation)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Nové ocenění: %s", self.name),
            "res_model": "investra.valuation",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "context": context,
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
