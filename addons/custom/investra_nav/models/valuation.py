import hashlib
import json
from datetime import date as date_type, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, ROUND_UP, Decimal

from odoo import api, fields, models
from odoo.tools import format_date, html2plaintext
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.investra_entity.models.entity import RATE_SOURCE_NONE
from odoo.addons.investra_fund.models.approval_matrix import APPROVE, PERFORM, check_user

from .. import engine

BALANCE_SHEET = ("asset", "liability")
PREPARER = "investra_entity.group_valuation_preparer"
APPROVER = "investra_entity.group_valuation_approver"
STOPPING = ("stop",)
PRICE_ROUNDING = {"down": ROUND_DOWN, "half_up": ROUND_HALF_UP, "up": ROUND_UP}
# Pole, která smí nastavit jen postup ocenění; přes API je uživatel nezapíše.
SYSTEM_FIELDS = {
    "state", "previous_id", "preparer_id", "fund_capital", "neutral_capital", "class_line_ids", "fee_line_ids",
    "portfolio_line_ids", "check_ids", "approval_ids", "event_ids", "snapshot", "snapshot_hash", "return_reason",
    "published_at", "package_id", "package_checksum", "step_ids",
}

# Historie kroků ocenění (ZJ-06 bod 12, rozhodnutí 2026-11-17): nezměnitelná auditní stopa.
VALUATION_STEPS = [
    ("created", "Založení"),
    ("computed", "Spočítání"),
    ("submitted", "Odeslání ke schválení"),
    ("approved", "Schválení"),
    ("request", "Žádost podle schvalovací matice"),
    ("returned", "Vrácení"),
    ("posted", "Zaúčtování"),
    ("sent", "Odeslání depozitáři"),
    ("confirmed", "Potvrzení depozitářem"),
    ("depositary_returned", "Vrácení depozitářem"),
    ("reversed", "Storno"),
    ("published", "Zveřejnění"),
]


def d(value):
    return Decimal(str(value or 0))


class InvestraFund(models.Model):
    # Historie fondu (chatter): zápis o zrušení návrhu ocenění (OC-01, rozhodnutí 2026-11-15).
    _name = "investra.fund"
    _inherit = ["investra.fund", "mail.thread"]

    launch_date = fields.Date(string="Datum vzniku", help="Začátek prvního oceňovacího období.")
    # Záložka Úplaty ve formuláři fondu (ZJ-03); nabídka Pravidla úplat zůstává jako přehled.
    fee_rule_ids = fields.One2many("investra.fee.rule", "fund_id", string="Pravidla úplat")
    launch_locked = fields.Boolean(compute="_compute_launch_locked", string="Datum vzniku uzamčeno")
    # Kroky schválení (dříve approval_step_ids) určuje schvalovací matice; převedla je migrace 20.0.0.6.0.

    @api.model_create_multi
    def create(self, vals_list):
        funds = super().create(vals_list)
        funds._ensure_fx_profile()
        return funds

    def _compute_launch_locked(self):
        # MN-03: po prvním ocenění, které není stornované, datum vzniku určuje první oceňovací období a nemění se.
        locked = {
            group[0].id
            for group in self.env["investra.valuation"].sudo()._read_group(
                [("fund_id", "in", self.ids), ("state", "!=", "reversed")], ["fund_id"], []
            )
        } if self.ids else set()
        for fund in self:
            fund.launch_locked = fund.id in locked

    def write(self, vals):
        if "launch_date" in vals:
            for fund in self.filtered(lambda f: f.launch_locked and f.launch_date != fields.Date.to_date(vals["launch_date"])):
                raise UserError(self.env._(
                    "Datum vzniku fondu %s nejde změnit, protože fond má ocenění, které není stornované. "
                    "Změna by posunula první oceňovací období.", fund.display_name
                ))
        return super().write(vals)

    def _ensure_fx_profile(self):
        """Profil přecenění knihy fondu (rozhodnutí 2026-11-13, varianta A): banky a závazek z úplat, rozdíl na role
        kurzového zisku a ztráty. Další peněžní účty přidá uživatel do profilu. Kniha s profilem se nemění."""
        Profile = self.env["investra.fx.profile"].sudo()
        Mapping = self.env["investra.role.account"].sudo()
        # Profil se pozná podle fondu; ručně založené profily knihy zůstávají beze změny a ocenění je použije také.
        for fund in self:
            company = fund.company_id
            if Profile.with_context(active_test=False).search_count([("fund_id", "=", fund.id)]):
                continue
            maps = {m.role_id.code: m for m in Mapping.search([("company_id", "=", company.id)])}
            accounts = self.env["account.account"]
            for code in ("bank", "fee_payable"):
                if code in maps:
                    accounts |= maps[code].account_id | maps[code].extra_account_ids
            journal = self.env["account.journal"].sudo().search(
                [("company_id", "=", company.id), ("type", "=", "general")], order="sequence, id", limit=1
            )
            # ZJ-10 fáze 2: automaticky založený profil nemá v novém chatteru dělat šum.
            Profile.with_context(tracking_disable=True, mail_create_nolog=True).create({
                "name": self.env._("Přecenění – %s", fund.display_name),
                "fund_id": fund.id,
                "company_id": company.id,
                "account_ids": [(6, 0, accounts.ids)],
                "gain_account_id": maps["gain_fx"].account_id.id if "gain_fx" in maps else False,
                "loss_account_id": maps["loss_fx"].account_id.id if "loss_fx" in maps else False,
                "journal_id": journal.id,
                # Zdroj kurzu doplní profil podle funkční měny (dřív záložně ČNB, MN-08).
            })


class InvestraFxProfile(models.Model):
    _inherit = "investra.fx.profile"

    fund_id = fields.Many2one("investra.fund", ondelete="cascade", index=True, readonly=True, tracking=True, string="Fond",
                              help="Profil založený pro fond; jeho účty přeceňuje ocenění fondu.")


class InvestraValuation(models.Model):
    """Jedno ocenění fondu k datu ve verzi. Stavy vedou přes schválení k zaúčtování a zveřejnění."""

    _name = "investra.valuation"
    _inherit = ["investra.record.guard", "investra.approval.pending.mixin"]
    _description = "Ocenění"
    _order = "fund_id, date desc, version desc"
    _book_fields = ("fund_id",)
    _system_fields = SYSTEM_FIELDS
    # Ocenění nemá vlastní název; hledání podle názvu (např. ve výběru) hledá podle fondu.
    _rec_names_search = ["fund_id"]

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="fund_id.currency_id")
    date = fields.Date(required=True, string="Datum ocenění")
    # Bez součtu ve skupinách: součet čísel verzí nedává smysl (rozhodnutí 2026-11-14).
    version = fields.Integer(default=1, required=True, readonly=True, string="Verze", aggregator=None)
    state = fields.Selection(
        [
            ("draft", "Návrh"),
            ("computed", "Spočteno"),
            ("submitted", "Ke schválení"),
            ("approved", "Schváleno"),
            ("posted", "Zaúčtováno"),
            ("sent", "U depozitáře"),
            ("confirmed", "Potvrzeno depozitářem"),
            ("published", "Zveřejněno a uzamčeno"),
            ("returned", "Vráceno"),
            ("reversed", "Stornováno"),
        ],
        default="draft",
        required=True,
        readonly=True,
        string="Stav",
    )
    previous_id = fields.Many2one("investra.valuation", readonly=True, string="Předchozí ocenění")
    # ZJ-06 bod 12: pole se přepíše při každém Spočítat; tento uživatel nesmí ocenění schválit (čtyři oči).
    # Kdo ocenění založil, je create_uid; celý sled kroků je v historii (step_ids).
    preparer_id = fields.Many2one("res.users", readonly=True, string="Spočítal",
                                  help="Kdo ocenění naposledy spočítal. Ocenění nesmí schválit (čtyři oči).")
    step_ids = fields.One2many("investra.valuation.step", "valuation_id", readonly=True, string="Historie")
    # Bez součtu ve skupinách: FK a NFK jsou stavové veličiny k datu; součet přes data a verze nedává smysl
    # (rozhodnutí 2026-11-14).
    fund_capital = fields.Monetary(readonly=True, string="FK", aggregator=None)
    neutral_capital = fields.Monetary(readonly=True, string="NFK", aggregator=None)
    # Jen zobrazení v seznamu: stejná hodnota jako „Změna FK od minula“ v detailu ocenění (FK − součet FK (t−1) tříd
    # z přemostění), včetně úpisů a odkupů, tedy ne výkonnost. Prázdná u návrhu, vráceného a prvního ocenění
    # (rozhodnutí 2026-11-14 „Seznam Ocenění – změna FK“).
    fund_capital_change = fields.Monetary(
        compute="_compute_fund_capital_change", string="Změna FK", aggregator=None,
        help="Změna FK od předchozího ocenění včetně úpisů a odkupů; není to výkonnost.",
    )
    has_capital_change = fields.Boolean(compute="_compute_fund_capital_change", string="Má změnu FK")
    class_line_ids = fields.One2many("investra.valuation.class", "valuation_id", readonly=True, string="Třídy")
    fee_line_ids = fields.One2many("investra.valuation.fee", "valuation_id", readonly=True, string="Úplaty")
    portfolio_line_ids = fields.One2many("investra.valuation.portfolio", "valuation_id", readonly=True, string="Portfolio")
    check_ids = fields.One2many("investra.valuation.check", "valuation_id", readonly=True, string="Kontroly")
    approval_ids = fields.One2many("investra.valuation.approval", "valuation_id", readonly=True, string="Schválení")
    external_fee_ids = fields.One2many("investra.valuation.external", "valuation_id", string="Ručně doložené úplaty")
    event_ids = fields.Many2many("investra.accounting.event", readonly=True, string="Doklady")
    snapshot = fields.Text(readonly=True, string="Snímek")
    snapshot_hash = fields.Char(readonly=True, string="Otisk snímku")
    return_reason = fields.Text(readonly=True, string="Důvod vrácení")
    published_at = fields.Datetime(readonly=True, string="Zveřejněno")
    # Neaktuální výpočet (rozhodnutí Martina 2026-11-17): po výpočtu se uloží otisk vstupů; změní-li se, formulář upozorní
    # a ocenění nejde odeslat ke schválení, dokud se nespočte znovu. Čas výpočtu navíc obnoví souhrn s grafem.
    computed_at = fields.Datetime(readonly=True, copy=False, string="Spočteno")
    inputs_stamp = fields.Text(readonly=True, copy=False, string="Otisk vstupů výpočtu")
    stale_note = fields.Char(compute="_compute_stale_note", string="Neaktuální výpočet")

    _uniq = models.Constraint("unique(fund_id, date, version)", "Verze ocenění k datu už existuje.")

    @api.depends("state", "previous_id", "fund_capital", "class_line_ids.opening_capital")
    def _compute_fund_capital_change(self):
        for valuation in self:
            shown = valuation.previous_id and valuation.state not in ("draft", "returned")
            valuation.has_capital_change = bool(shown)
            valuation.fund_capital_change = (
                valuation.currency_id.round(valuation.fund_capital - sum(valuation.class_line_ids.mapped("opening_capital")))
                if shown else 0.0
            )

    @api.depends("fund_id.display_name", "date", "version")
    def _compute_display_name(self):
        # Název ve tvaru „fond – datum – v1“; datum podle jazyka uživatele.
        for valuation in self:
            parts = [valuation.fund_id.display_name or "", format_date(self.env, valuation.date) if valuation.date else ""]
            valuation.display_name = " – ".join(p for p in parts if p) + (f" – v{valuation.version}" if valuation.version else "")

    # --- práva ---------------------------------------------------------------------------------

    def _require(self, group):
        if not self.env.su and not self.env.user.has_group(group):
            raise AccessError(self.env._("Na tento krok nemáte oprávnění."))
        if not self.env.su and self.sudo().company_id - self.env.companies:
            raise AccessError(self.env._("Ocenění patří jiné společnosti."))

    def _require_company(self):
        if not self.env.su and self.sudo().company_id - self.env.companies:
            raise AccessError(self.env._("Ocenění patří jiné společnosti."))

    def _matrix_gate(self, activity, method, summary, **kwargs):
        """Jednorázový úkon podle schvalovací matice; vrátí žádost, má-li úkon počkat na potvrzení."""
        self.ensure_one()
        request = self.env["investra.approval.matrix"]._gate(activity, self, method, kwargs, summary=summary)
        if request:
            self._log_step("request", summary)
        return request

    def _log_step(self, step, note=False):
        """Zapíše krok do historie ocenění (ZJ-06 bod 12): kdo (přihlášený uživatel, i při sudo), kdy, co, poznámka."""
        self.env["investra.valuation.step"].sudo().create([
            {"valuation_id": record.id, "step": step, "user_id": self.env.uid, "note": note or False} for record in self
        ])

    def _compute_note(self):
        """Souhrn výpočtu do historie: FK a kurzy tříd."""
        self.ensure_one()
        prices = ", ".join(f"{line.class_id.code} {line.price}" for line in self.class_line_ids)
        return self.env._("FK %(fk).2f %(currency)s; kurzy tříd: %(prices)s",
                          fk=self.fund_capital, currency=self.currency_id.name or "", prices=prices or "-")

    def _require_state(self, *states):
        for record in self:
            if record.state not in states:
                raise UserError(self.env._("Krok není ve stavu %s možný.", record.state))

    # --- hlavní kniha --------------------------------------------------------------------------

    def _line_domain(self, *extra):
        self.ensure_one()
        drafts = self.event_ids.filtered(lambda e: e.state in ("draft", "locked")).move_id.ids
        return [
            ("company_id", "=", self.company_id.id),
            ("date", "<=", self.date),
            "|", ("parent_state", "=", "posted"), ("move_id", "in", drafts),
            *extra,
        ]

    def _sum(self, *extra):
        Line = self.env["account.move.line"].sudo()
        total = Line._read_group(self._line_domain(*extra), aggregates=["balance:sum"])[0][0]
        return d(total).quantize(engine.CENT, rounding=ROUND_HALF_UP)

    def _net_assets(self):
        """FK z rozvahy: aktiva a závazky včetně návrhů tohoto ocenění."""
        return self._sum(("account_id.account_type", "=like", "asset%")) + self._sum(
            ("account_id.account_type", "=like", "liability%")
        )

    def _assets(self):
        return self._sum(("account_id.account_type", "=like", "asset%"))

    def _period_start(self):
        self.ensure_one()
        if self.previous_id:
            return self.previous_id.date
        if not self.fund_id.launch_date:
            raise UserError(self.env._("Fond nemá datum vzniku."))
        return self.fund_id.launch_date

    def _delta(self, fund_class):
        """Změna rozvahových položek označených třídou za období."""
        start = self._period_start()
        return self._sum(
            ("investra_class_id", "=", fund_class.id),
            ("date", ">", start),
            ("account_id.account_type", "not like", "equity"),
            ("account_id.account_type", "not like", "income"),
            ("account_id.account_type", "not like", "expense"),
        )

    def _role_balance(self, role, *extra):
        # Hlavní i další účty role (rozhodnutí 2026-11-12 „Role s více účty“); chybějící role je chyba jako dosud.
        Role = self.env["investra.account.role"]
        Role.account_for(self.company_id, role)
        return self._sum(("account_id", "in", Role.accounts_for(self.company_id, role).ids), *extra)

    def _accounts_without_role(self):
        """Účty se zůstatkem k datu, které nemají v knize roli (výkazy ČNB je nevidí). Výsledek běžného období
        (equity_unaffected) se vykazuje zvlášť."""
        mappings = self.env["investra.role.account"].sudo().search([("company_id", "=", self.company_id.id)])
        covered = mappings.account_id | mappings.extra_account_ids
        groups = self.env["account.move.line"].sudo()._read_group(
            self._line_domain(("account_id", "not in", covered.ids), ("account_id.account_type", "!=", "equity_unaffected")),
            groupby=["account_id"], aggregates=["balance:sum"],
        )
        return [account for account, balance in groups if d(balance).quantize(engine.CENT) != 0]

    def _position_balance(self):
        """Zůstatek všech účtů, na kterých jsou nástroje, podle rolí typů a zařazení fondu."""
        roles = self.env["investra.instrument.type"].sudo().search([]).role_id
        roles |= self.env["investra.portfolio.classification"].sudo().search([("fund_id", "=", self.fund_id.id)]).role_id
        mappings = self.env["investra.role.account"].sudo().search(
            [("company_id", "=", self.company_id.id), ("role_id", "in", roles.ids)]
        )
        return self._sum(("account_id", "in", (mappings.account_id | mappings.extra_account_ids).ids))

    # --- výpočet -------------------------------------------------------------------------------

    def action_compute(self):
        """Přepočte návrh ocenění. Opakovaný výpočet nahradí návrhy, nic nezdvojí."""
        self._require(PREPARER)
        self._require_state("draft", "computed")
        for record in self.sudo():
            if not record.fund_id.class_ids:
                raise UserError(self.env._("Fond %s nemá žádnou třídu; ocenění nejde spočítat.", record.fund_id.display_name))
            record._compute_all()
            record._log_step("computed", record._compute_note())
        return True

    def _find_previous(self):
        return self.search([
            ("fund_id", "=", self.fund_id.id),
            ("date", "<", self.date),
            ("state", "in", ("posted", "sent", "confirmed", "published")),
        ], order="date desc, version desc", limit=1)

    def _clear(self):
        self.event_ids.filtered(lambda e: e.state == "draft")._discard_events()
        self.write({"event_ids": [(5,)]})
        self.class_line_ids.unlink()
        self.fee_line_ids.unlink()
        self.portfolio_line_ids.unlink()
        self.check_ids.unlink()

    def _class_context(self):
        """Předběžný kapitál, kusy a poměr tříd."""
        start = self._period_start()
        result = {}
        previous = {line.class_id: line for line in self.previous_id.class_line_ids}
        for fund_class in self.fund_id.class_ids:
            movements = self.env["investra.class.movement"].sudo().search([
                ("class_id", "=", fund_class.id), ("date", ">", start), ("date", "<=", self.date),
                ("state", "!=", "reversed"),
            ])
            prior = previous.get(fund_class)
            capital = d(prior.capital if prior else 0)
            units = d(prior.units if prior else 0)
            subscriptions = movements.filtered(lambda m: m.movement_type == "subscription")
            redemptions = movements - subscriptions
            result[fund_class] = {
                "pre_capital": capital + sum((d(m.signed_amount) for m in movements), Decimal(0)),
                "units": units + sum((d(m.signed_units) for m in movements), Decimal(0)),
                "movements": movements,
                "previous": prior,
                # Přemostění: počáteční stav a pohyby; odkupy kladně, odčítají se.
                "opening_capital": capital,
                "opening_units": units,
                "subscriptions": subscriptions,
                "redemptions": redemptions,
                "subscription_amount": sum((d(m.capital_amount) for m in subscriptions), Decimal(0)),
                "subscription_units": sum((d(m.units) for m in subscriptions), Decimal(0)),
                "redemption_amount": sum((d(m.capital_amount) for m in redemptions), Decimal(0)),
                "redemption_units": sum((d(m.units) for m in redemptions), Decimal(0)),
            }
        total = sum(row["pre_capital"] for row in result.values())
        if not total:
            raise UserError(self.env._("Předběžný kapitál fondu je nulový."))
        for row in result.values():
            row["ratio"] = row["pre_capital"] / total
        return result

    def _add_event(self, kind, name, lines, event_type="valuation"):
        lines = [line for line in lines if line["amount"]]
        if not lines:
            return self.env["investra.accounting.event"]
        for line in lines:
            line["amount"] = str(line["amount"])
        event = self.env["investra.accounting.event"]._create_event(
            self.company_id, f"valuation:{self.id}:{self.env.context.get('compute_run', 0)}:{kind}",
            f"{name} ({self.date})", self.date, event_type, lines, source=self,
        )
        self.event_ids = [(4, event.id)]
        return event

    def _compute_all(self):
        self._clear()
        self.previous_id = self._find_previous()
        self.preparer_id = self.env.user
        self = self.with_company(self.company_id)
        context = self._class_context()
        self._compute_portfolio()
        self._compute_bank_fx()
        self._compute_unsettled()
        # Pevné pořadí podle druhu (ZJ-06 bod 7, rozhodnutí 2026-11-17; nahrazuje pořadí pravidel z 2026-11-05):
        # časově rozlišené a ručně doložené úplaty → výkonnostní odměna (po nich, před sebou) → daň nakonec.
        # Výkonnostní odměna má základ před úplatami, po úplatách, nebo po dani; „po dani“ se počítá až po dani
        # a daň se pak ve stejném ocenění doúčtuje o odměnu, která šla do výsledku (rozhodnutí 2026-11-17).
        rules = self.env["investra.fee.rule"].search([("fund_id", "=", self.fund_id.id)])
        performance = rules.filtered(lambda r: r.kind == "performance")
        taxes = rules.filtered(lambda r: r.kind == "tax")
        before_fees = {fund_class: self._class_value(fund_class, context) for fund_class in context} \
            if any(rule.perf_base == "before_fees" for rule in performance) else {}
        self._apply_periodic_fees(rules.filtered(lambda r: r.kind == "periodic"), context)
        for rule in performance.filtered(lambda r: r.perf_base != "after_tax"):
            self._apply_performance(rule, context, before_fees)
        for rule in taxes:
            self._apply_tax(rule)
        late = performance.filtered(lambda r: r.perf_base == "after_tax")
        for rule in late:
            self._apply_performance(rule, context, before_fees)
        if late:
            for rule in taxes:
                self._apply_tax(rule, correction=True)
        self._apply_scheme(context)
        self._finish(context)
        self.state = "computed"
        self.write({"computed_at": fields.Datetime.now(),
                    "inputs_stamp": json.dumps(self._inputs_now(), ensure_ascii=False)})

    def _rate_source(self):
        return self.fund_id.entity_id._require_rate_source()

    def _fx(self, currency):
        """Měna fondu za jednotku měny, jen z vyhlášeného kurzu k datu."""
        return self.fund_id._fx_at(currency, self.date)

    def _approved_price(self, instrument):
        """Poslední známá schválená cena do data ocenění; téhož dne má cena fondu přednost před sdílenou."""
        prices = self.env["investra.instrument.price"].search([
            ("instrument_id", "=", instrument.id), ("date", "<=", self.date), ("state", "=", "approved"),
            "|", ("fund_id", "=", self.fund_id.id), ("fund_id", "=", False),
        ], order="date desc", limit=2)
        if not prices:
            raise UserError(self.env._("Chybí schválená cena %(name)s do %(day)s.", name=instrument.name, day=self.date))
        latest = prices.filtered(lambda p: p.date == prices[0].date)
        return latest.filtered("fund_id")[:1] or latest[:1]

    def _closed_positions(self, positions):
        """Pozice (nástroj, obchodní model) bez kusů, jejichž účet nástroje má k datu zůstatek."""
        Role = self.env["investra.account.role"]
        groups = self.env["account.move.line"].sudo()._read_group(
            self._line_domain(("investra_instrument_id", "!=", False), ("investra_classification_id", "!=", False)),
            groupby=["investra_instrument_id", "investra_classification_id", "account_id"], aggregates=["balance:sum"],
        )
        closed = set()
        for instrument, classification, account, balance in groups:
            key = (instrument, classification.portfolio_id)
            if key in positions or not d(balance).quantize(engine.CENT, rounding=ROUND_HALF_UP):
                continue
            if account == Role.account_for(self.company_id, classification.role_id.code):
                closed.add(key)
        return closed

    def _compute_portfolio(self):
        """Přecení nástroje a založí řádky listu portfolio; změna ceny a kurzu jde zvlášť."""
        Trade = self.env["investra.trade"].sudo()
        Role = self.env["investra.account.role"]
        Classification = self.env["investra.portfolio.classification"]
        several = len(self.fund_id.portfolio_ids) > 1
        rows, lines = [], []
        positions = Trade._holdings(self.fund_id, self.date)
        previous = self._find_previous()
        # Splacená nebo prodaná pozice bez kusů, která má na účtu nástroje zůstatek, se doúčtuje na nulu
        # (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“: splátka jistiny snižuje kusy).
        for key in self._closed_positions(positions):
            positions[key] = 0.0
        for (instrument, portfolio), quantity in positions.items():
            # Klasifikace podle obchodního modelu fondu k datu ocenění (rozhodnutí 2026-11-11).
            classification = Classification._valid(portfolio, instrument, self.date)
            if not classification:
                raise UserError(self.env._(
                    "Nástroj %(name)s nemá v obchodním modelu %(portfolio)s k %(day)s zařazení.",
                    name=instrument.name, portfolio=portfolio.name, day=self.date,
                ))
            amortised = classification.valuation_method == "amortised"
            role = classification.role_id.code
            instrument_account = Role.account_for(self.company_id, role)
            fx = self._fx(instrument.currency_id)
            # Úrok v RH zvlášť (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“): vydělaný úrok od minulého
            # ocenění do úrokových výnosů, naběhlý úrok v hodnotě dluhopisu; přecenění až ze zbytku.
            interest_ccy, accrued_ccy = Decimal(0), Decimal(0)
            if not amortised:
                current = instrument._fair_value_interest(self.fund_id, portfolio, self.date)
                if current:
                    before = previous and instrument._fair_value_interest(self.fund_id, portfolio, previous.date)
                    interest_ccy = current[0] - (before[0] if before else 0)
                    accrued_ccy = current[1]
            if not quantity:
                value_ccy, unit_price, price_source, price_values = Decimal(0), 0.0, self.env._("Splaceno"), {}
            elif amortised:
                value_ccy = instrument._accrued_value(self.fund_id, self.date, portfolio)
                unit_price, price_source = float(value_ccy / d(quantity)), self.env._("Naběhlá hodnota")
                price_values = {}
            else:
                price = self._approved_price(instrument)
                value_ccy = d(quantity) * d(price.price)
                if instrument.price_excludes_accrued:
                    value_ccy += accrued_ccy
                unit_price, price_source = price.price, price.source
                price_values = {"price_id": price.id, "price_date": price.date}
            value = engine.money(value_ccy * fx)
            # Jen účet nástrojů: protiúčty přecenění nesou nástroj také, ale nejsou jeho účetní hodnotou.
            # Pozice je nástroj v jednom obchodním modelu; podle portfolia, aby přežila budoucí reklasifikaci.
            domain = [
                ("investra_instrument_id", "=", instrument.id), ("account_id", "=", instrument_account.id),
                ("investra_classification_id.portfolio_id", "=", portfolio.id),
            ]
            carrying = self._sum(*domain)
            line_model = self.env["account.move.line"].sudo()
            foreign_raw = line_model._read_group(self._line_domain(*domain), aggregates=["amount_currency:sum"])[0][0]
            foreign = d(foreign_raw)
            foreign_currency = instrument.currency_id != self.fund_id.currency_id
            interest = engine.money(interest_ccy * fx)
            cost_ccy, cost, realised_fx = self._cost_walk(instrument, portfolio, previous)
            realised_ccy = realised = Decimal(0)
            if not amortised:
                realised_ccy, realised_rated = self._realised_ccy(
                    instrument, portfolio, previous, Role.account_for(self.company_id, role), foreign_currency,
                )
                realised = engine.money(realised_rated if foreign_currency else realised_ccy)
            if foreign_currency:
                # Realizace kurzem prodeje či splátky, zbytek ceny kurzem ocenění (rozhodnutí 2026-11-12
                # „Realizovaný kurzový rozdíl“); kurzový rozdíl ze zbytku, z něj realizovaný proti pořizovací ceně.
                price_effect = engine.money((value_ccy - foreign - interest_ccy - realised_ccy) * fx) + realised
                fx_effect = value - carrying - interest - price_effect
                realised_fx = engine.money(realised_fx) if not amortised else Decimal(0)
            else:
                price_effect, fx_effect, realised_fx = value - carrying - interest, Decimal(0), Decimal(0)
            movement = "accrued_interest" if amortised else "price_revaluation"
            extra = {"investra_instrument_id": instrument.id, "investra_classification_id": classification.id}
            currency_values = {"currency_id": instrument.currency_id.id} if foreign_currency else {}
            if interest:
                lines.append({
                    "role": role, "amount": interest, "movement_type": "accrued_interest", "extra": extra,
                    "name": self.env._("Naběhlý úrok %s", instrument.name),
                    **({**currency_values, "amount_currency": str(interest_ccy)} if foreign_currency else {}),
                })
                lines.append({"role": "income_interest", "amount": -interest, "movement_type": "accrued_interest", "extra": extra})
            if price_effect:
                lines.append({
                    "role": role, "amount": price_effect, "movement_type": movement, "extra": extra,
                    **({**currency_values, "amount_currency": str(value_ccy - foreign - interest_ccy)} if foreign_currency else {}),
                })
            if amortised and price_effect:
                lines.append({"role": "income_interest", "amount": -price_effect, "movement_type": movement, "extra": extra})
            elif price_effect or realised:
                # Realizovaný výsledek prodaných a splacených jednotek zvlášť, zbytek je nerealizované přecenění.
                unrealised = price_effect - realised
                for part, gain, loss in ((realised, "gain_realised", "loss_realised"),
                                         (unrealised, "gain_fair_value", "loss_fair_value")):
                    if part:
                        label = {"name": self.env._("Realizace %s", instrument.name)} if gain == "gain_realised" else {}
                        lines.append({"role": gain if part > 0 else loss, "amount": -part, "movement_type": movement,
                                      "extra": extra, **label})
            # Realizovaný kurzový rozdíl prodaných a splacených jednotek zvlášť (stejné účty, vlastní druh pohybu),
            # zbytek je nerealizovaný kurzový rozdíl.
            for part, fx_movement in ((realised_fx, "fx_realised"), (fx_effect - realised_fx, "fx_revaluation")):
                if not part:
                    continue
                label = {"name": self.env._("Realizovaný kurz %s", instrument.name)} if fx_movement == "fx_realised" else {}
                lines.append({
                    "role": role, "amount": part, "movement_type": fx_movement, "extra": extra, **label,
                    **({**currency_values, "amount_currency": "0"} if foreign_currency else {}),
                })
                lines.append({
                    "role": "gain_fx" if part > 0 else "loss_fx",
                    "amount": -part, "movement_type": fx_movement, "extra": extra, **label,
                })
            if not quantity or (amortised and not value):
                continue
            rows.append({
                "valuation_id": self.id,
                "kind": instrument.type_id.kind,
                "instrument_id": instrument.id,
                "portfolio_id": portfolio.id,
                "classification_id": classification.id,
                # Fond s více obchodními modely: tentýž nástroj může mít dva řádky, název je rozliší.
                "name": f"{instrument.name} – {portfolio.name}" if several else instrument.name,
                "isin": instrument.isin,
                "currency_id": instrument.currency_id.id,
                "quantity": quantity,
                "price": unit_price,
                "price_source": price_source,
                **price_values,
                "cost_currency": float(cost_ccy),
                "cost": float(cost),
                "accrued_interest_currency": float(accrued_ccy if not amortised else 0),
                "realised": float(realised),
                "fair_value_currency": float(value_ccy),
                "fx_rate": float(fx),
                "fx_source": self._rate_source() if foreign_currency else False,
                "fair_value": float(value),
            })
        self._add_event("portfolio", "Přecenění portfolia", lines)
        self.env["investra.valuation.portfolio"].sudo().create(rows)

    # --- realizovaný výsledek a průměrná pořizovací cena (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“) --

    def _position_events(self, instrument, portfolio, start, end):
        """Obchody a zaúčtované splátky jistiny pozice v období (start, end] po datech:
        [(datum, kusy se znaménkem, částka bez úroku v měně nástroje, kurz zaúčtování, uzavírá pozici)]."""
        Trade = self.env["investra.trade"].sudo()
        trades = Trade._recognised(self.fund_id, end, instrument, portfolio)
        if start:
            trades -= Trade._recognised(self.fund_id, start, instrument, portfolio)
        # Náhled obchodu (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“): uložená verze obchodu se nahradí
        # hodnotami z formuláře, nebo se vynechá; běžné ocenění kontext nemá.
        preview = self.env.context.get("investra_trade_preview")
        if preview:
            trades = trades.filtered(lambda t: t.id != preview["exclude_id"])
        events = [(t._recognition_date(), d(t.quantity), d(t.quantity) * d(t.price), d(t._booked_fx()), False) for t in trades]
        added = preview and preview.get("trade")
        if added and (not start or added._recognition_date() > start) and added._recognition_date() <= end:
            events.append((added._recognition_date(), d(added.quantity), d(added.quantity) * d(added.price),
                           d(added._booked_fx()), False))
        domain = [("fund_id", "=", self.fund_id.id), ("instrument_id", "=", instrument.id), ("portfolio_id", "=", portfolio.id),
                  ("state", "=", "posted"), ("date", "<=", end)]
        if start:
            domain.append(("date", ">", start))
        ppu = d(instrument._principal_per_unit())
        for repayment in self.env["investra.instrument.repayment"].sudo().search(domain):
            principal = d(repayment.principal_amount)
            events.append((repayment.date, -principal / ppu, -principal, d(repayment.fx_rate), repayment.closes_position))
        # Nákupy téhož dne před prodeji a splátkami.
        return sorted(events, key=lambda e: (e[0], e[1] < 0))

    def _cost_walk(self, instrument, portfolio, previous):
        """Pořizovací cena zbývajících kusů průměrem (pravidlo „Částečný prodej“), v měně nástroje a ve funkční měně,
        bez naběhlého úroku zaplaceného u nákupu; a realizovaný kurzový rozdíl prodejů a splátek jistiny od minulého
        ocenění ve funkční měně.

        Realizovaný kurz = průměrná pořizovací cena prodaných jednotek v měně nástroje × (kurz prodeje − průměrný kurz
        nákupu), tj. proti pořizovací ceně, ne proti minulému přecenění (rozhodnutí 2026-11-12 „Realizovaný kurzový
        rozdíl“). Výsledek: (pořizovací cena v měně nástroje, ve funkční měně, realizovaný kurz nezaokrouhleně)."""
        since = previous.date if previous else None
        units = cost_ccy = cost = realised_fx = Decimal(0)
        for day, quantity, amount, fx, closes in self._position_events(instrument, portfolio, None, self.date):
            if quantity > 0:
                units, cost_ccy, cost = units + quantity, cost_ccy + amount, cost + amount * fx
            elif units > 0:
                share = Decimal(1) if closes else min(-quantity / units, Decimal(1))
                if since is None or day > since:
                    realised_fx += share * (cost_ccy * fx - cost)
                units, cost_ccy, cost = units * (1 - share), cost_ccy * (1 - share), cost * (1 - share)
        return engine.money(cost_ccy), engine.money(cost), realised_fx

    def _realised_ccy(self, instrument, portfolio, previous, account, foreign_currency):
        """Realizovaný výsledek pozice od minulého ocenění v měně nástroje: výnos prodaných a splacených jednotek
        (bez úroku) − jejich poměrná účetní hodnota průměrem. Účetní hodnota k minulému ocenění = zůstatek účtu nástroje
        bez naběhlého úroku; dříve zaúčtované přecenění zůstává (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).
        Výsledek: (realizace v měně nástroje, realizace přepočtená kurzem zaúčtování prodeje či splátky)."""
        units = carrying = Decimal(0)
        if previous:
            units = d(self.env["investra.trade"].sudo()._holdings(self.fund_id, previous.date).get((instrument, portfolio), 0))
            field = "amount_currency" if foreign_currency else "balance"
            total = self.env["account.move.line"].sudo()._read_group([
                ("company_id", "=", self.company_id.id), ("date", "<=", previous.date), ("parent_state", "=", "posted"),
                ("investra_instrument_id", "=", instrument.id), ("account_id", "=", account.id),
                ("investra_classification_id.portfolio_id", "=", portfolio.id),
            ], aggregates=[f"{field}:sum"])[0][0]
            accrued = instrument._fair_value_interest(self.fund_id, portfolio, previous.date)
            carrying = d(total) - (accrued[1] if accrued else 0)
        realised = rated = Decimal(0)
        for _day, quantity, amount, fx, closes in self._position_events(instrument, portfolio, previous.date if previous else None, self.date):
            if quantity > 0:
                units, carrying = units + quantity, carrying + amount
            elif units > 0:
                share = Decimal(1) if closes else min(-quantity / units, Decimal(1))
                part = -amount - carrying * share
                realised, rated = realised + part, rated + part * fx
                units, carrying = units * (1 - share), carrying * (1 - share)
        return realised, rated

    def _compute_bank_fx(self):
        """FX přecenění peněžních položek v cizí měně a řádky bank v listu portfolio."""
        Role = self.env["investra.account.role"]
        Line = self.env["account.move.line"].sudo()
        self._add_event("bank_fx", "FX přecenění peněžních položek", self._fx_revaluation_lines())
        totals = {}
        groups = Line._read_group(
            self._line_domain(("account_id", "in", Role.accounts_for(self.company_id, "bank").ids)),
            groupby=["currency_id"],
            aggregates=["amount_currency:sum", "balance:sum"],
        )
        for currency, amount, balance in groups:
            totals[currency] = [d(amount), d(balance)]
        rows = []
        for currency, (amount, balance) in totals.items():
            fx = self._fx(currency)
            value = engine.money(amount * fx)
            rows.append({
                "valuation_id": self.id,
                "kind": "bank",
                "name": f"Bankovní účty {currency.name}",
                "currency_id": currency.id,
                "fair_value_currency": float(d(amount)),
                "cost_currency": float(d(amount)),
                "cost": float(engine.money(balance)),
                "fx_rate": float(fx),
                "fx_source": self._rate_source() if currency != self.fund_id.currency_id else False,
                "fair_value": float(value),
            })
        self.env["investra.valuation.portfolio"].sudo().create(rows)

    def _fx_accounts(self):
        """Přeceňované účty knihy: banky (vždy, i nově přidané účty role) a účty profilů přecenění knihy.

        Účty nevypořádaných obchodů přeceňuje vlastní krok (_compute_unsettled), proto se z profilu vynechají.
        """
        Role = self.env["investra.account.role"]
        company = self.company_id
        profiles = self.env["investra.fx.profile"].sudo().search([("company_id", "=", company.id)])
        own = Role.accounts_for(company, "unsettled_receivable") | Role.accounts_for(company, "unsettled_payable")
        return (Role.accounts_for(company, "bank") | profiles.account_ids) - own

    def _fx_revaluation_lines(self):
        """Přecenění podle profilu (rozhodnutí 2026-11-13, varianta A): výběr zůstatků je společný s modulem
        investra_fx_revaluation, kurz a zaokrouhlení jsou kurzem fondu jako dosud u bank.

        Řádek nese roli účtu; účet, který není hlavním účtem své role, jde přes extra (u hlavního účtu banky se řádek
        nemění, otisk dřívějších ocenění zůstává). Peněžní účty (banky) se nedělí podle partnera, ostatní ano.
        """
        company = self.company_id
        mappings = self.env["investra.role.account"].sudo().search([("company_id", "=", company.id)])
        roles = {}
        for mapping in mappings:
            for account in mapping.extra_account_ids:
                roles[account] = (mapping.role_id.code, False)
            roles[mapping.account_id] = (mapping.role_id.code, True)
        balances = self.env["investra.fx.profile"].sudo()._foreign_balances(
            company, self._fx_accounts(), self.date, domain=self._line_domain(),
            by_partner=lambda account: account.account_type != "asset_cash",
        )
        lines = []
        for account, currency, partner, amount, balance in balances:
            if account not in roles:
                raise UserError(self.env._("Účet %s v profilu přecenění nemá v knize roli.", account.display_name))
            code, main = roles[account]
            difference = engine.money(d(amount) * self._fx(currency)) - engine.money(d(balance))
            if not difference:
                continue
            line = {"role": code, "amount": difference, "movement_type": "fx_revaluation",
                    "currency_id": currency.id, "amount_currency": "0"}
            if not main:
                line["extra"] = {"account_id": account.id}
            if partner:
                line["partner_id"] = partner.id
            lines.append(line)
            lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                          "movement_type": "fx_revaluation"})
        return lines

    def _compute_unsettled(self):
        """Nevypořádané obchody: přecenění pohledávek a závazků kurzem a změna RH před vypořádáním."""
        Mapping = self.env["investra.role.account"].sudo()
        Line = self.env["account.move.line"].sudo()
        lines = []
        for role in ("unsettled_receivable", "unsettled_payable"):
            account = Mapping.search([("company_id", "=", self.company_id.id), ("role_id.code", "=", role)]).account_id
            if not account:
                continue
            groups = Line._read_group(
                self._line_domain(("account_id", "=", account.id)),
                groupby=["currency_id"], aggregates=["amount_currency:sum", "balance:sum"],
            )
            for currency, amount, balance in groups:
                if currency == self.fund_id.currency_id:
                    continue
                difference = engine.money(d(amount) * self._fx(currency)) - engine.money(balance)
                if difference:
                    lines.append({"role": role, "amount": difference, "movement_type": "fx_revaluation",
                                  "currency_id": currency.id, "amount_currency": "0"})
                    lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                                  "movement_type": "fx_revaluation"})
        self._add_event("unsettled_fx", "FX přecenění nevypořádaných obchodů", lines)
        self._compute_unsettled_fair_value(Mapping, Line)

    def _compute_unsettled_fair_value(self, Mapping, Line):
        """Settlement date accounting: změna RH do vypořádání, IFRS 9 B3.1.6. Po vypořádání se zůstatek rozpustí."""
        account = Mapping.search([("company_id", "=", self.company_id.id), ("role_id.code", "=", "unsettled_fair_value")]).account_id
        if not account:
            return
        targets = {}
        pending = self.env["investra.trade"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("trade_date", "<=", self.date), ("state", "=", "unsettled"),
        ]).filtered(lambda t: t._recognition_date() > self.date)
        for trade in pending:
            instrument = trade.instrument_id
            classification = trade._classification()
            if classification.ifrs9_category == "fvoci":
                raise UserError(self.env._("Změna RH do OCI zatím není podporovaná: %s.", instrument.name))
            if classification.ifrs9_category == "amortised":
                continue
            value = d(trade.quantity) * d(self._approved_price(instrument).price) * self._fx(instrument.currency_id)
            cost = d(trade.quantity) * d(trade.price) * d(trade.fx_rate)
            key = (instrument, classification)
            targets[key] = targets.get(key, Decimal(0)) + value - cost
        groups = Line._read_group(
            self._line_domain(("account_id", "=", account.id)),
            groupby=["investra_instrument_id", "investra_classification_id"], aggregates=["balance:sum"],
        )
        balances = {(instrument, classification): engine.money(balance) for instrument, classification, balance in groups}
        lines = []
        for key in {*targets, *balances}:
            instrument, classification = key
            difference = engine.money(targets.get(key, 0)) - balances.get(key, Decimal(0))
            if difference:
                extra = {"investra_instrument_id": instrument.id, "investra_classification_id": classification.id}
                lines.append({"role": "unsettled_fair_value", "amount": difference, "movement_type": "price_revaluation", "extra": extra})
                lines.append({"role": "gain_fair_value" if difference > 0 else "loss_fair_value", "amount": -difference,
                              "movement_type": "price_revaluation", "extra": extra})
        self._add_event("unsettled_fv", "Změna RH nevypořádaných obchodů", lines)

    def _fee_record(self, rule, amount, fund_class=None, detail=None, manual=None):
        self.env["investra.valuation.fee"].sudo().create({
            "valuation_id": self.id,
            "rule_id": rule.id if rule else False,
            "external_id": manual.id if manual else False,
            "class_id": fund_class.id if fund_class else False,
            "amount": float(amount),
            "detail": json.dumps(detail or {}, ensure_ascii=False, default=str),
        })

    def _class_value(self, fund_class, context):
        """Kapitál třídy podle aktuálního stavu knihy, před dalším krokem."""
        deltas = {c: self._delta(c) for c in context}
        neutral = self._net_assets() - sum(deltas.values())
        return context[fund_class]["ratio"] * neutral + deltas[fund_class]

    def _fee_base(self, rule, context, fund_class=None):
        if rule.base_source == "none":
            return Decimal(0)
        if rule.base_source == "assets":
            return self._assets()
        if rule.base_source == "class_fk" and fund_class:
            return self._class_value(fund_class, context)
        return self._net_assets()

    def _book_fee(self, rule, amount, fund_class, movement="fee", payable="fee_payable", kind_suffix="", name=None):
        """Zaúčtuje úplatu: část příjemcům z tříd přes vnitřní zúčtování, zbytek jako náklad a závazek.

        Částka smí být záporná (oprava úplaty, ZJ-11): náklad, závazek i přesun mezi třídami mají opačné znaménko.
        """
        class_id = fund_class.id if fund_class else False
        share = d(rule.recipient_share) if rule.recipient_class_ids else Decimal(0)
        to_classes = engine.money(amount * share)
        external = amount - to_classes
        lines = []
        if external:
            lines += [
                {"role": rule.expense_role, "amount": external, "class_id": class_id, "movement_type": movement},
                {"role": payable, "amount": -external, "class_id": class_id, "movement_type": movement},
            ]
        if to_classes:
            lines += self._transfer_lines(fund_class, self._recipient_parts(rule, to_classes))
        self._add_event(f"fee:{rule.id}:{class_id}{kind_suffix}", name or rule.name, lines)

    def _recipient_parts(self, rule, amount):
        context = self._class_context()
        weights = {c: self._class_value(c, context) for c in rule.recipient_class_ids}
        weights = {c.code: max(v, Decimal(0)) for c, v in weights.items()}
        parts = engine.split_amount(amount, weights)
        return {c: parts[c.code] for c in rule.recipient_class_ids}

    def _transfer_lines(self, payer, parts):
        """Přesun hodnoty mezi třídami: účet vnitřního zúčtování má v součtu nulu, FK se nemění."""
        total = sum(parts.values())
        lines = [{"role": "internal_clearing", "amount": -total, "class_id": payer.id, "movement_type": "class_transfer"}]
        for fund_class, amount in parts.items():
            lines.append({"role": "internal_clearing", "amount": amount, "class_id": fund_class.id, "movement_type": "class_transfer"})
        return lines

    def _apply_average(self, rule, current):
        """Úplata z průměrného FK: nárok od začátku roku minus to, co už je v tomto roce naúčtované.

        `current` = FK k datu ocenění před všemi úplatami (ZJ-06 bod 7); dřívější ocenění vstupují zveřejněným FK.
        """
        year_start = date_type(self.date.year - 1, 12, 31)
        start = max(year_start, self.fund_id.launch_date or year_start)
        earlier = self.search([
            ("fund_id", "=", self.fund_id.id), ("date", ">", year_start), ("date", "<", self.date),
            ("state", "in", ("posted", "sent", "confirmed", "published")),
        ])
        capitals = [d(v.fund_capital) for v in earlier] + [current]
        average = sum(capitals) / len(capitals)
        result = engine.periodic_fee(
            rule._engine_rule(start, self.date), start, self.date, average, classes_count=len(self.fund_id.class_ids)
        )
        booked = sum(
            (d(line.amount) for line in earlier.fee_line_ids.filtered(lambda l: l.rule_id == rule)), Decimal(0)
        )
        amount = result["amount"] - booked
        self._fee_record(rule, amount, None, {"average": average, "booked": booked, **result})
        self._book_fee(rule, amount, None)

    def _periodic_amount(self, rule, base):
        """Částka časově rozlišené úplaty z daného základu; základ před/po řeší volající, ne engine."""
        start, end = self._period_start(), self.date
        spec = dict(rule._engine_rule(start, end), base_mode="before")
        return engine.periodic_fee(spec, start, end, base, classes_count=len(self.fund_id.class_ids))

    def _apply_periodic_fees(self, rules, context):
        """Časově rozlišené a ručně doložené úplaty (ZJ-06 bod 7, rozhodnutí 2026-11-17).

        Základ „před“ = stav před všemi úplatami v ocenění (snímek před první úplatou); úplaty se navzájem neovlivňují.
        Základ „po“ = stav po všech časově rozlišených a ručně doložených úplatách včetně počítané; úplaty „po“ se
        dopočtou společně opakováním do ustálení. Průměrný FK, Aktiva a Bez základu volbu nemají (počítají jako „před“).
        Ručně doložené úplaty (ZJ-03) mají pevnou částku; zaúčtují se po úplatách „před“ a před dopočtem úplat „po“.
        """
        payers = [(rule, fund_class) for rule in rules for fund_class in (rule.class_ids or [None])]
        after = [key for key in payers if key[0].base_mode == "after" and key[0].base_source in ("fk", "class_fk")]
        # Snímek před první úplatou: základy úplat „před“ a váhy přijímajících tříd pro odhad dopadu úplat „po“.
        fund_before = self._net_assets()
        class_before = {fund_class: self._class_value(fund_class, context) for fund_class in context} if after else {}
        bases = {key: self._fee_base(key[0], context, key[1]) for key in payers
                 if key not in after and key[0].base_source != "average_fk"}
        for rule, fund_class in payers:
            if (rule, fund_class) in after:
                continue
            if rule.base_source == "average_fk":
                self._apply_average(rule, fund_before)
                continue
            base = bases[(rule, fund_class)]
            result = self._periodic_amount(rule, base)
            self._fee_record(rule, result["amount"], fund_class, {"base": base, "base_mode": "before", **result})
            self._book_fee(rule, result["amount"], fund_class)
        self._apply_manual_fees()
        if not after:
            return
        # Stav knihy po úplatách „před“ a ručně doložených úplatách; od něj se odečítají úplaty „po“ (včetně sebe).
        current = {key: self._fee_base(key[0], context, key[1]) for key in after}
        exact = dict.fromkeys(after, Decimal(0))
        for _step in range(100):
            updated = {
                key: self._periodic_amount(key[0], current[key] - self._after_effect(key, exact, context, class_before))["exact"]
                for key in after
            }
            settled = all(abs(updated[key] - exact[key]) < Decimal("0.000001") for key in after)
            exact = updated
            if settled:
                break
        else:
            raise UserError(self.env._("Výpočet úplat se základem po všech úplatách se neustálil."))
        for key in after:
            rule, fund_class = key
            base = current[key] - self._after_effect(key, exact, context, class_before)
            result = self._periodic_amount(rule, base)
            self._fee_record(rule, result["amount"], fund_class, {"base": base, "base_mode": "after", **result})
            self._book_fee(rule, result["amount"], fund_class)

    def _after_effect(self, key, amounts, context, class_before):
        """O kolik úplaty „po“ (ještě nezaúčtované) sníží základ pravidla `key`.

        Fondový kapitál: náklad mimo fond (bez podílu přijímajícím třídám). Kapitál třídy: úplaty té třídy celé,
        úplaty celého fondu poměrem třídy, a naopak podíl, který třída z úplat dostane (váhy podle kapitálu před úplatami).
        """
        rule, fund_class = key
        total = Decimal(0)
        for (other, payer), amount in amounts.items():
            share = d(other.recipient_share) if other.recipient_class_ids else Decimal(0)
            if rule.base_source == "fk" or fund_class is None:
                total += amount * (1 - share)
                continue
            if payer == fund_class:
                total += amount
            elif not payer:
                total += amount * context[fund_class]["ratio"]
            if share and fund_class in other.recipient_class_ids:
                weights = {c: max(class_before[c], Decimal(0)) for c in other.recipient_class_ids}
                if sum(weights.values()):
                    total -= amount * share * weights[fund_class] / sum(weights.values())
        return total

    def _performance_state(self, rule, fund_class, row, version):
        """Srovnávací hodnoty, naběhlá odměna a období od poslední krystalizace."""
        previous = row["previous"]
        if previous and previous.perf_base_date:
            return d(previous.perf_reference), d(previous.perf_hwm), d(previous.perf_accrued), previous.perf_base_date
        initial = d(version.initial_reference)
        return initial, initial, Decimal(0), self.fund_id.launch_date

    def _is_crystallisation(self, rule):
        day = self.date
        month_end = (day + timedelta(days=1)).day == 1
        if rule.crystallisation == "valuation":
            # ZJ-06 bod 10b: k datu každého ocenění (podmínku „odměna je kladná“ doplní volající jako u ostatních voleb).
            return True
        if rule.crystallisation == "month":
            return month_end
        if rule.crystallisation == "quarter":
            return month_end and day.month in (3, 6, 9, 12)
        if rule.crystallisation == "year":
            return month_end and day.month == 12
        return False

    def _apply_performance(self, rule, context, before_fees=None):
        version = rule._version_at(self.date)
        for fund_class in rule.class_ids:
            row = context[fund_class]
            reference, hwm, accrued, base_date = self._performance_state(rule, fund_class, row, version)
            # Základ „před úplatami“ = hodnota třídy před úplatami tohoto ocenění; jinak aktuální stav knihy
            # (po úplatách, u „po dani“ i po dani). Naběhlá odměna se přičítá zpět: odměna počítá před sebou samou.
            value = before_fees[fund_class] if rule.perf_base == "before_fees" else self._class_value(fund_class, context)
            gross = value + accrued
            flows = []
            if version.perf_measure == "capital":
                movements = self.env["investra.class.movement"].sudo().search([
                    ("class_id", "=", fund_class.id), ("date", ">", base_date), ("date", "<=", self.date),
                    ("state", "!=", "reversed"),
                ])
                flows = [(m.date, m.signed_amount) for m in movements]
            spec = {
                "measure": version.perf_measure,
                "rate": version.rate,
                "reference": reference,
                "hwm": hwm if version.perf_use_hwm else None,
                "hurdle_kind": version.hurdle_kind,
                "hurdle_rate": version.hurdle_rate,
                "hurdle_margin": version.hurdle_margin,
                "hurdle_type": version.hurdle_type,
                "catch_up": version.catch_up,
                "hurdle_floor_zero": version.hurdle_floor_zero,
                "basis": rule.basis,
                "require_positive_return": version.require_positive_return,
                "probability": version.probability,
                "cap_rate": version.cap_rate or None,
            }
            if version.hurdle_kind == "index":
                spec["index_start"] = version.benchmark_id._value_at(base_date)
                spec["index_end"] = version.benchmark_id._value_at(self.date)
            result = engine.performance_fee(spec, base_date, self.date, gross, units=row["units"], flows=flows, accrued=accrued)
            self._fee_record(rule, result["move"], fund_class, {"gross": gross, "base_date": base_date, **result})
            self._book_fee(rule, result["move"], fund_class, payable="performance_payable")
            row["perf"] = {
                "reference": reference, "hwm": hwm, "accrued": result["required"], "base_date": base_date,
                "crystallise": self._is_crystallisation(rule) and result["required"] > 0,
                "measure": version.perf_measure,
            }
            if rule.cover_class_id and result["shortfall"] > 0:
                available = max(self._class_value(rule.cover_class_id, context), Decimal(0))
                covered = min(result["shortfall"], engine.money(available))
                lines = self._transfer_lines(rule.cover_class_id, {fund_class: covered})
                self._add_event(f"cover:{rule.id}:{fund_class.id}", f"Krytí {rule.name}", lines)
                self._fee_record(rule, -covered, fund_class, {"covered_by": rule.cover_class_id.code})

    def _apply_tax(self, rule, correction=False):
        """Očekávaná daň jako doplatek do požadovaného zůstatku; základ je výsledek od začátku roku.

        `correction` = doúčtování daně po výkonnostní odměně se základem po dani (rozhodnutí 2026-11-17): výsledek
        už obsahuje odměnu, která šla do výsledovky; podíl převedený třídám výsledek nemění.
        """
        version = rule._version_at(self.date)
        year_start = date_type(self.date.year, 1, 1)
        tax_account = self.env["investra.account.role"].account_for(self.company_id, "expense_tax")
        result = -(
            self._sum(("date", ">=", year_start), ("account_id.account_type", "=like", "income%"))
            + self._sum(("date", ">=", year_start), ("account_id.account_type", "=like", "expense%"), ("account_id", "!=", tax_account.id))
        )
        required = engine.money(max(result, Decimal(0)) * d(version.rate))
        booked = self._sum(("date", ">=", year_start), ("account_id", "=", tax_account.id))
        move = required - booked
        self._fee_record(rule, move, None, {"base": result, "required": required, "booked": booked, "correction": correction})
        suffix = ":perf" if correction else ""
        name = self.env._("%s – doúčtování po výkonnostní odměně", rule.name) if correction else rule.name
        self._add_event(f"tax:{rule.id}{suffix}", name, [
            {"role": "expense_tax", "amount": move, "movement_type": "fee"},
            {"role": "tax_payable", "amount": -move, "movement_type": "fee"},
        ])

    def _apply_manual_fees(self):
        """Ručně doložené úplaty (ZJ-03): částka spočtená mimo Odoo na zvolený nákladový účet, protiúčet závazek z úplat.

        Třída prázdná = společný náklad celého fondu (dělí se poměrem), jinak jen dané třídě. Cizí měna se přepočte
        kurzem k datu ocenění ze zdroje kurzů fondu; řádky nesou i původní měnu, aby závazek přecenilo FX přecenění.

        Oprava úplaty (ZJ-11, rozhodnutí 2026-11-18): s vyplněným „Opravuje úplatu“ se účtuje přes `_book_fee` jako
        úplata pravidla (nákladová role pravidla, podíl příjemcům z tříd); jen v měně fondu. Řádek rozpisu nemá pravidlo,
        proto ho průměrný FK v dalším ocenění neodečítá a oprava platí trvale.
        """
        fund_currency = self.fund_id.currency_id
        for entry in self.external_fee_ids:
            currency = entry.currency_id or fund_currency
            original = engine.money(d(entry.amount))
            rate = self._fx(currency)
            amount = engine.money(original * rate)
            rule = entry.corrects_rule_id
            if rule:
                self._fee_record(None, amount, entry.class_id, {
                    "manual": True, "corrects": rule.name, "note": entry.note, "currency": currency.name,
                }, manual=entry)
                self._book_fee(rule, amount, entry.class_id or None, kind_suffix=f":manual:{entry.id}",
                               name=self.env._("Oprava úplaty %s", rule.name))
                continue
            class_id = entry.class_id.id or False
            foreign = {} if currency == fund_currency else {"currency_id": currency.id}
            lines = [
                {"role": "expense_other", "amount": amount, "class_id": class_id, "movement_type": "fee",
                 "extra": {"account_id": entry.account_id.id},
                 **({"amount_currency": original, **foreign} if foreign else {})},
                {"role": "fee_payable", "amount": -amount, "class_id": class_id, "movement_type": "fee",
                 **({"amount_currency": -original, **foreign} if foreign else {})},
            ]
            self._fee_record(None, amount, entry.class_id, {
                "manual": True, "note": entry.note, "account": entry.account_id.code,
                "currency": currency.name, "amount_currency": str(original), "rate": str(rate),
            }, manual=entry)
            self._add_event(f"fee:manual:{entry.id}", self.env._("Ručně doložená úplata"), lines)

    def _apply_scheme(self, context):
        """U pořadí nároků zaúčtuje rozdíl proti alokačnímu poměru jako přesun mezi třídami."""
        scheme = self.env["investra.allocation.scheme"].sudo()._for_date(self.fund_id, self.date)
        if not scheme or scheme.method != "waterfall":
            return
        start = self._period_start()
        deltas = {c: self._delta(c) for c in context}
        neutral = self._net_assets() - sum(deltas.values())
        pre_total = sum(row["pre_capital"] for row in context.values())
        change = neutral - pre_total
        fraction = engine.year_fraction(start, self.date, "act365")
        lines = scheme.line_ids
        tiers = []
        for rank in sorted(set(lines.filtered("target_rate").mapped("rank"))):
            tiers.append({
                line.class_id.code: context[line.class_id]["pre_capital"] * d(line.target_rate) * fraction
                for line in lines.filtered(lambda l: l.rank == rank and l.target_rate)
            })
        residual = {l.class_id.code: l.residual_share for l in lines if l.residual_share}
        capitals = {c.code: row["pre_capital"] for c, row in context.items()}
        loss_order = [l.class_id.code for l in lines.filtered("loss_rank").sorted("loss_rank")]
        targets = engine.waterfall(change, capitals, tiers, residual, d(scheme.residual_pro_rata), loss_order)
        transfers = {
            c: engine.money(targets[c.code]) - engine.money(row["ratio"] * change)
            for c, row in context.items()
        }
        rounding = -sum(transfers.values())
        if rounding:
            largest = max(transfers, key=lambda c: abs(transfers[c]))
            transfers[largest] += rounding
        for fund_class, amount in transfers.items():
            context[fund_class]["allocation"] = amount
        event_lines = [
            {"role": "internal_clearing", "amount": amount, "class_id": c.id, "movement_type": "class_transfer"}
            for c, amount in transfers.items()
        ]
        self._add_event("waterfall", "Rozdělení mezi třídy", event_lines)

    def _finish(self, context):
        """Finální kapitál tříd, kurzy a kontroly."""
        fund_capital = self._net_assets()
        deltas = {c: self._delta(c) for c in context}
        neutral = fund_capital - sum(deltas.values())
        raw = {c: row["ratio"] * neutral + deltas[c] for c, row in context.items()}
        rounded = {c: engine.money(value) for c, value in raw.items()}
        remainder = fund_capital - sum(rounded.values())
        if remainder:
            rounded[max(sorted(rounded, key=lambda c: c.code), key=lambda c: rounded[c])] += remainder
        rows = []
        bridges = {}
        for fund_class, row in context.items():
            value = rounded[fund_class]
            value_class = value
            foreign = fund_class.currency_id != self.fund_id.currency_id
            fx_rate = self._fx(fund_class.currency_id) if foreign else Decimal(1)
            if foreign:
                value_class = value / fx_rate
            digits = Decimal(1).scaleb(-fund_class.price_digits)
            method = PRICE_ROUNDING[fund_class.price_rounding]
            price = (value_class / row["units"]).quantize(digits, rounding=method) if row["units"] else Decimal(0)
            bridge = self._class_bridge(fund_class, row, value, value_class, deltas[fund_class], neutral, fx_rate, price)
            bridges[fund_class] = bridge
            perf = row.get("perf") or {}
            previous = row["previous"]
            reference = d(previous.perf_reference) if previous else Decimal(0)
            hwm = d(previous.perf_hwm) if previous else Decimal(0)
            accrued = d(previous.perf_accrued) if previous else Decimal(0)
            base_date = previous.perf_base_date if previous else False
            if perf:
                reference, hwm, accrued, base_date = perf["reference"], perf["hwm"], perf["accrued"], perf["base_date"]
                if perf["crystallise"]:
                    current = value if perf["measure"] == "capital" else value / row["units"]
                    reference, hwm, accrued, base_date = current, max(hwm, current), Decimal(0), self.date
            rows.append({
                "valuation_id": self.id,
                "class_id": fund_class.id,
                "pre_capital": float(row["pre_capital"]),
                "ratio": float(row["ratio"]),
                "delta": float(deltas[fund_class]),
                "capital": float(value),
                "units": float(row["units"]),
                "price": str(price),
                "perf_reference": float(reference),
                "perf_hwm": float(hwm),
                "perf_accrued": float(accrued),
                "perf_base_date": base_date,
                **{key: (v if isinstance(v, (str, bool)) else float(v)) for key, v in bridge.items()},
            })
        self.env["investra.valuation.class"].sudo().create(rows)
        self.write({"fund_capital": float(fund_capital), "neutral_capital": float(neutral)})
        self._run_checks(fund_capital, rounded)
        self._run_bridge_checks(context, bridges, rounded)

    def _class_bridge(self, fund_class, row, value, value_class, delta, neutral, fx_rate, price):
        """Přemostění třídy od minulého ocenění ke konečnému kapitálu a kurzu.

        FK (t−1) + úpisy − odkupy − dividendy = upravený FK (základ poměru);
        upravený FK + společná změna + specifická změna = FK. Společná změna obsahuje zaokrouhlení,
        specifická změna se dál dělí na úplaty, výkonnostní odměnu, přesun podle pořadí nároků a ostatní.
        Výsledek ocenění se tím nemění, jen se ukládá rozpad, který výpočet zná.
        """
        previous = row["previous"]
        same_currency = fund_class.currency_id == self.fund_id.currency_id
        fees = self.fee_line_ids.filtered(lambda line: line.class_id == fund_class)
        performance = -sum((d(l.amount) for l in fees if l.rule_id.kind == "performance"), Decimal(0))
        fee = -sum((d(l.amount) for l in fees if l.rule_id.kind != "performance"), Decimal(0))
        allocation = d(row.get("allocation"))
        shared = value - row["pre_capital"] - delta
        shared_raw = engine.money(row["ratio"] * neutral) - row["pre_capital"]

        # Kapitál třídy bere čistou částku pohybu (poplatek jen ve prospěch třídy, rozdíl podle toho, komu patří).
        def in_class_currency(movement):
            if same_currency:
                return d(movement.capital_amount)
            if movement.amount_class:
                return d(movement.capital_amount_class)
            return d(movement.capital_amount) / (d(movement.fx_rate) or fx_rate)

        if not previous:
            opening_class = Decimal(0)
        elif same_currency:
            opening_class = d(previous.capital)
        elif previous.capital_class:
            opening_class = d(previous.capital_class)
        else:
            # Starší ocenění kapitál v měně třídy neukládalo; náhradou kusy × kurz.
            opening_class = d(previous.units) * d(previous.price)
        opening_price = d(previous.price) if previous else Decimal(0)
        return {
            "opening_capital": row["opening_capital"],
            "opening_units": row["opening_units"],
            "opening_price": previous.price if previous else False,
            "subscription_amount": row["subscription_amount"],
            "subscription_units": row["subscription_units"],
            "redemption_amount": row["redemption_amount"],
            "redemption_units": row["redemption_units"],
            "dividend_amount": Decimal(0),
            "shared_result": shared,
            "rounding_amount": shared - shared_raw,
            "fee_amount": fee,
            "performance_amount": performance,
            "allocation_amount": allocation,
            "other_amount": delta - fee - performance - allocation,
            "fx_rate": fx_rate,
            "opening_capital_class": engine.money(opening_class),
            "subscription_amount_class": engine.money(sum((in_class_currency(m) for m in row["subscriptions"]), Decimal(0))),
            "redemption_amount_class": engine.money(sum((in_class_currency(m) for m in row["redemptions"]), Decimal(0))),
            "capital_class": engine.money(value_class),
            "price_change_pct": (price / opening_price - 1) * 100 if opening_price else Decimal(0),
        }

    def _run_bridge_checks(self, context, bridges, rounded):
        """Kontroly přemostění tříd; rozdíl nad 0,01 zastaví ocenění."""
        tolerance = Decimal("0.01")
        movements, units, result, specific = [], [], [], []
        for fund_class, row in context.items():
            b = bridges[fund_class]
            code = fund_class.code
            pre = b["opening_capital"] + b["subscription_amount"] - b["redemption_amount"] - b["dividend_amount"]
            if abs(pre - row["pre_capital"]) > tolerance:
                movements.append(f"{code}: {pre} ≠ {row['pre_capital']}")
            count = b["opening_units"] + b["subscription_units"] - b["redemption_units"]
            if abs(count - row["units"]) > Decimal("0.000001"):
                units.append(f"{code}: {count} ≠ {row['units']}")
            specific_total = b["fee_amount"] + b["performance_amount"] + b["allocation_amount"] + b["other_amount"]
            end = row["pre_capital"] + b["shared_result"] + specific_total
            if abs(end - rounded[fund_class]) > tolerance:
                result.append(f"{code}: {end} ≠ {rounded[fund_class]}")
        opening = sum((b["opening_capital"] for b in bridges.values()), Decimal(0))
        previous_fk = d(self.previous_id.fund_capital) if self.previous_id else Decimal(0)
        self._check("bridge_movements", "Přemostění: FK (t−1) + úpisy − odkupy = upravený FK", not movements,
                    "; ".join(movements))
        self._check("bridge_units", "Přemostění: kusy (t−1) + úpisy − odkupy = kusy", not units, "; ".join(units))
        self._check("bridge_result", "Přemostění: upravený FK + společná a specifická změna = FK", not result,
                    "; ".join(result))
        self._check("bridge_opening", "Přemostění: součet FK (t−1) tříd = FK minulého ocenění",
                    abs(opening - previous_fk) <= tolerance, f"{opening} / {previous_fk}")

    def _run_movement_checks(self):
        """Úpisy a odkupy období (rozhodnutí „Úpisy a odkupy (bod 8 UX)“, 2026-11-11).

        Nezaúčtovaný pohyb ocenění zastaví (rozhodnutí 2026-11-11): jinak by ruční pohyb vstoupil do NAV bez
        schválení podle matice. Poplatek a cena jsou upozornění.
        """
        movements = self.env["investra.class.movement"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("date", ">", self._period_start()), ("date", "<=", self.date),
            ("state", "!=", "reversed"),
        ])
        draft = movements.filtered(lambda m: m.state == "draft")
        self._check("movements_posted", "Úpisy a odkupy období jsou zaúčtované", not draft,
                    "; ".join(draft.mapped("display_name")))
        fees = movements.filtered(lambda m: abs(d(m.fee_amount_class) - d(m.fee_expected_class)) > Decimal("0.01"))
        self._check("movement_fee_rate", "Poplatky úpisů a odkupů odpovídají sazbě třídy", not fees,
                    "; ".join(f"{m.display_name}: {m.fee_amount_class} / {m.fee_expected_class}" for m in fees),
                    severity="warning")
        prices = movements.filtered("price_reason")
        self._check("movement_price", "Úpisy a odkupy za zveřejněný kurz třídy", not prices,
                    "; ".join(f"{m.display_name}: {m.price_reason}" for m in prices), severity="warning")

    def _check(self, code, name, ok, detail="", severity="stop"):
        self.env["investra.valuation.check"].sudo().create({
            "valuation_id": self.id,
            "code": code,
            "name": name,
            "status": "ok" if ok else severity,
            "detail": str(detail),
        })

    def _run_checks(self, fund_capital, rounded):
        self._check("classes_sum", "Součet tříd se rovná FK", sum(rounded.values()) == fund_capital, sum(rounded.values()))
        clearing = self._role_balance("internal_clearing")
        self._check("clearing_zero", "Vnitřní zúčtování je za fond nulové", clearing == 0, clearing)
        instrument_ledger = self._position_balance()
        positions = sum(
            (d(line.fair_value) for line in self.portfolio_line_ids if line.kind != "bank"), Decimal(0)
        )
        self._check("positions_ledger", "Pozice se rovnají hlavní knize", instrument_ledger == engine.money(positions),
                    f"{instrument_ledger} / {positions}")
        overdue = self.env["investra.trade"].sudo().search_count([
            ("fund_id", "=", self.fund_id.id), ("state", "=", "unsettled"), ("settlement_date", "<=", self.date),
        ])
        self._check("trades_settled", "Obchody po termínu vypořádání jsou vypořádané", not overdue, overdue, severity="warning")
        # Pozice bere jen obchody s dokladem (rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“, závažnost stop):
        # obchod, který by k datu už byl v pozici, ale doklad nemá, je chybějící doklad, nebo neprovedený návrh ke smazání.
        unbooked = self.env["investra.trade"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("trade_date", "<=", self.date), ("state", "!=", "reversed"),
            ("event_id", "=", False),
        ]).filtered(lambda t: t._recognition_date() <= self.date)
        self._check("trades_booked", "Obchody k datu jsou zaúčtované", not unbooked,
                    ", ".join(f"{t.instrument_id.name} {t.trade_date}" for t in unbooked))
        # Ruční přepsání kategorie IFRS 9 je odchylka od rozhodovacího stromu; schvalovatel ji musí vidět (rozhodnutí 2026-11-11).
        overridden = self.portfolio_line_ids.classification_id.filtered("category_override")
        self._check(
            "classification_override", "Pozice bez ručně přepsané kategorie IFRS 9", not overridden,
            ", ".join(overridden.mapped("display_name")), severity="warning",
        )
        # Role nebo způsob ocenění jinak než návrh (např. repo s nebankovní protistranou na roli repo s bankou,
        # rozhodnutí 2026-11-11 „Osnova fondů – převodová tabulka“).
        deviating = self.portfolio_line_ids.classification_id.filtered("deviates_from_proposal")
        self._check(
            "classification_proposal", "Zařazení pozic odpovídá návrhu (způsob ocenění, role účtu)", not deviating,
            ", ".join(deviating.mapped("display_name")), severity="warning",
        )
        # Inkasa na cestě (splátky nástrojů čekající na výpis) mají od 2026-11-12 vlastní roli; kniha bez ní se nesčítá.
        transit = self._role_balance("cash_in_transit")
        if self.env["investra.role.account"].sudo().search_count(
            [("company_id", "=", self.company_id.id), ("role_id.code", "=", "cash_in_transit_receipt")], limit=1
        ):
            transit += self._role_balance("cash_in_transit_receipt")
        self._check("transit_zero", "Peníze a inkasa na cestě jsou nulové", transit == 0, transit, severity="warning")
        # Kalendářní splátka bez zaúčtování: ocenění by ji odúčtovalo do úroků (rozhodnutí 2026-11-12
        # „Návrhy kalendářních splátek“).
        Repayment = self.env["investra.instrument.repayment"].sudo()
        missing = Repayment._missing_scheduled(self.fund_id, self.date, posted_only=True)
        # Rozlišení pro uživatele: splátka je v návrhu (stačí zaúčtovat), nebo chybí úplně.
        absent = {(i, m, d) for i, m, d, _p, _n in Repayment._missing_scheduled(self.fund_id, self.date)}
        self._check(
            "scheduled_repayments", "Splátky splatné podle kalendáře jsou zaúčtované", not missing,
            ", ".join(
                f"{i.name} {format_date(self.env, d)}: {p + n} ({self.env._('chybí') if (i, m, d) in absent else self.env._('v návrhu')})"
                for i, m, d, p, n in missing
            ), severity="warning",
        )
        unassigned = self._accounts_without_role()
        self._check("accounts_role", "Účty se zůstatkem mají roli (jinak chybí ve výkazech ČNB)", not unassigned,
                    ", ".join(a.display_name for a in unassigned), severity="warning")
        pending = self.env["account.move"].sudo().search_count([
            ("company_id", "=", self.company_id.id), ("state", "=", "draft"), ("date", "<=", self.date),
            ("id", "not in", self.event_ids.move_id.ids),
        ])
        self._check("no_foreign_drafts", "K datu nejsou jiné nezaúčtované doklady", not pending, pending, severity="warning")
        manual = self._manual_rates()
        self._check("manual_rate", "Ocenění používá jen vyhlášené kurzy", not manual, "; ".join(manual), severity="warning")
        stale = self._stale_prices()
        self._check("price_age", "Ceny nejsou starší než povolené stáří", not stale, "; ".join(stale), severity="warning")
        # Dluhopis bez kalendáře: naběhlý úrok pozice se nepočítá (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“).
        no_calendar = self.portfolio_line_ids.instrument_id.filtered(
            lambda i: i.type_id.kind == "bond" and not i.cashflow_ids
        )
        self._check("bond_calendar", "Dluhopisy v portfoliu mají kalendář toků (jinak se nepočítá naběhlý úrok)",
                    not no_calendar, ", ".join(no_calendar.mapped("name")), severity="warning")
        exceptions = self._lock_exceptions_since_previous()
        self._check("lock_exception", "Uzamčené období nebylo otevřeno výjimkou", not exceptions,
                    "; ".join(exceptions), severity="warning")
        self._run_movement_checks()
        # Souběh pravidel téže nákladové role (ZJ-03): jen upozornění, výpočet nezastaví.
        rules = self.env["investra.fee.rule"].search([("fund_id", "=", self.fund_id.id)])
        overlaps = rules._overlaps([(r, r.class_ids) for r in rules])
        self._check("fee_overlap", "Úplaty téže role nejsou zároveň na fondu a na třídách", not overlaps,
                    "; ".join(overlaps), severity="warning")
        deviating = self._deviating_prices()
        self._check("price_fund_deviation", "Fond používá sdílené tržní ceny", not deviating, "; ".join(deviating),
                    severity="warning")
        # Schvalovací matice (rozhodnutí 2026-11-11): vypnutí druhé osoby musí vidět schvalovatel, depozitář i auditor.
        rule = self.env["investra.approval.matrix"]._rule("valuation_approve")
        self._check("matrix_valuation", "Ocenění schvaluje druhá osoba", rule.persons > 1,
                    rule.row.display_name or "", severity="warning")
        alone = self._acts_without_second_person()
        self._check("second_person", "Úkony od minulého ocenění provedla druhá osoba", not alone, "; ".join(alone),
                    severity="warning")
        changes = self._matrix_changes()
        self._check("matrix_change", "Schvalovací matice se od minulého ocenění nezměnila", not changes,
                    "; ".join(changes), severity="warning")
        # Sdílené nástroje a pravidlo knihy (rozhodnutí 2026-11-13): změnu sdíleného i fondového nástroje musí vidět schvalovatel.
        changed = self._instrument_changes()
        self._check("instrument_changes", "Údaje nástrojů v portfoliu se od minulého ocenění nezměnily", not changed,
                    "; ".join(changed), severity="warning")

    def _since_previous(self):
        """Okamžik kontrol předchozího ocenění: co se stalo potom (i jeho schválení), ukáže toto ocenění."""
        previous = self.previous_id
        if not previous:
            return False
        return max(previous.check_ids.mapped("create_date"), default=previous.create_date)

    def _acts_without_second_person(self):
        """Úkony bez druhé osoby od minulého ocenění: kniha fondu a sdílené záznamy (kurzy, sdílené ceny)."""
        # Úkony podle výchozích řádků (chování před maticí) zůstávají jen v záznamu, aby upozornění neztratilo význam.
        domain = ["|", ("company_id", "=", self.company_id.id), ("company_id", "=", False),
                  ("matrix_id", "!=", False), ("matrix_id.builtin", "=", False)]
        since = self._since_previous()
        if since:
            domain.append(("create_date", ">=", since))
        logs = self.env["investra.approval.log"].sudo().search(domain, order="id")
        activities = dict(self.env["investra.approval.log"]._fields["activity"].selection)
        return [f"{activities[log.activity]}: {log.record_name or '-'} ({log.user_id.name}, {log.create_date:%Y-%m-%d %H:%M})"
                for log in logs]

    def _matrix_changes(self):
        """Řádky matice (od ZJ-01 společné pro celou aplikaci), které vznikly nebo se změnily od minulého ocenění."""
        since = self._since_previous()
        if not since:
            return []
        rows = self.env["investra.approval.matrix"].sudo().search([("write_date", ">=", since)], order="id")
        return rows.mapped("display_name")

    def _instrument_changes(self):
        """Změny údajů a toků nástrojů, které fond držel k minulému ocenění, provedené po jeho kontrolách."""
        since = self._since_previous()
        if not since:
            return []
        held = self.env["investra.trade"].sudo()._positions(self.fund_id, self.previous_id.date)
        if not held:
            return []
        messages = self.env["mail.message"].sudo().search([
            ("model", "=", "investra.instrument"), ("res_id", "in", [instrument.id for instrument in held]),
            ("subtype_id", "=", self.env.ref("investra_instruments.mt_instrument_change").id), ("date", ">=", since),
        ], order="date, id")
        names = {instrument.id: instrument.name for instrument in held}
        return [
            f"{names[m.res_id]}: {html2plaintext(m.body or '').strip()} ({m.author_id.name}, {fields.Datetime.to_string(m.date)})"
            for m in messages
        ]

    def _lock_exceptions_since_previous(self):
        """Výjimky z uzamčení knihy od zveřejnění předchozího ocenění (vrstva 2 zámku, rozhodnutí 2026-11-11)."""
        # U fondové knihy vzniká výjimka Odoo jen potvrzením žádosti; čas potvrzení i zveřejnění je čas aplikace.
        domain = [("company_id", "=", self.company_id.id), ("state", "in", ("active", "revoked"))]
        if self.previous_id.published_at:
            domain.append(("confirmed_at", ">=", self.previous_id.published_at))
        requests = self.env["investra.lock.exception.request"].sudo().search(domain, order="id")
        return [
            f"{r.user_id.name}, do {r.lock_date}: {r.reason} (požádal {r.requested_by.name}, potvrdil {r.confirmed_by.name})"
            for r in requests
        ]

    def _stale_prices(self):
        """Ceny starší než maximální stáří nástroje (poslední známá cena, rozhodnutí 2026-11-11)."""
        found = []
        for line in self.portfolio_line_ids.filtered("price_id").sorted("name"):
            age = (self.date - line.price_date).days
            if age > line.instrument_id.max_price_age:
                found.append(self.env._(
                    "%(name)s: cena k %(day)s, stáří %(age)s dní (limit %(limit)s)",
                    name=line.name, day=line.price_date, age=age, limit=line.instrument_id.max_price_age,
                ))
        return found

    def _deviating_prices(self):
        """Ceny fondu použité tam, kde ke stejnému dni existuje schválená sdílená cena."""
        Price = self.env["investra.instrument.price"].sudo()
        found = []
        for line in self.portfolio_line_ids.filtered(lambda l: l.price_id.fund_id).sorted("name"):
            shared = Price.search([
                ("instrument_id", "=", line.instrument_id.id), ("date", "=", line.price_date),
                ("fund_id", "=", False), ("state", "=", "approved"),
            ], limit=1)
            if shared:
                found.append(self.env._(
                    "%(name)s %(day)s: cena fondu %(fund)s místo sdílené %(shared)s (%(reason)s)",
                    name=line.name, day=line.price_date, fund=line.price_id.price, shared=shared.price,
                    reason=line.price_id.deviation_reason or "",
                ))
        return found

    def _manual_rates(self):
        """Ruční kurzy, které ocenění k datu použilo (měny portfolia, tříd a fondu)."""
        Rate = self.env["investra.rate"].sudo()
        if self.fund_id.entity_id.rate_source == RATE_SOURCE_NONE:
            return []  # kniha bez zdroje kurzů: kurz se nepoužil, jinak by ocenění skončilo chybou dřív (MN-08)
        source = self._rate_source()
        base = Rate.base_currency(source)
        currencies = self.portfolio_line_ids.currency_id | self.fund_id.class_ids.currency_id | self.fund_id.currency_id
        found = []
        for currency in (currencies - base).sorted("name"):
            record = Rate._effective(source, currency, self.date)
            if record and record.origin != "published":
                kind = dict(record._fields["origin"].selection)[record.origin]
                found.append(f"{currency.name} {record.date}: {kind} ({record.reason})")
        return found

    # --- postup --------------------------------------------------------------------------------

    def _fingerprint(self):
        """Otisk výsledků a řádků návrhů: zaúčtovat lze jen to, co bylo schváleno."""
        self.ensure_one()
        lines = sorted(
            (l.account_id.code or "", str(l.balance), l.investra_class_id.code or "", l.investra_movement_type or "")
            for l in self.event_ids.filtered(lambda e: e.state in ("draft", "locked", "posted")).move_id.sudo().line_ids
        )
        classes = sorted((c.class_id.code, c.capital, c.units, c.price) for c in self.class_line_ids)
        payload = json.dumps({"date": str(self.date), "version": self.version, "fk": self.fund_capital,
                              "classes": classes, "lines": lines}, ensure_ascii=False)
        return payload, hashlib.sha256(payload.encode()).hexdigest()

    def _inputs_now(self):
        """Otisk vstupů výpočtu: počet, poslední změna a největší id záznamů po skupinách (smazání i úprava se projeví)."""
        self.ensure_one()
        env, fund, day = self.env, self.fund_id, self.date
        positions = env["investra.trade"].sudo()._positions(fund, day)

        def stamp(model, domain, **ctx):
            rows = env[model].sudo().with_context(active_test=False, **ctx).search(domain)
            return [len(rows), str(max(rows.mapped("write_date"), default="")), max(rows.ids, default=0)]

        groups = {
            self.env._("ruční úplaty"): stamp("investra.valuation.external", [("valuation_id", "=", self.id)]),
            self.env._("pravidla úplat"): stamp("investra.fee.rule", [("fund_id", "=", fund.id)]),
            self.env._("verze úplat"): stamp("investra.fee.version", [("rule_id.fund_id", "=", fund.id)]),
            self.env._("třídy fondu"): stamp("investra.fund.class", [("fund_id", "=", fund.id)]),
            self.env._("úpisy a odkupy"): stamp("investra.class.movement", [("fund_id", "=", fund.id), ("date", "<=", day)]),
            self.env._("obchody"): stamp(
                "investra.trade", [("fund_id", "=", fund.id), "|", ("trade_date", "<=", day), ("settlement_date", "<=", day)]),
            self.env._("ceny nástrojů"): stamp(
                "investra.instrument.price", [("instrument_id", "in", [i.id for i in positions]), ("date", "<=", day),
                                             ("state", "=", "approved"), "|", ("fund_id", "=", fund.id), ("fund_id", "=", False)]),
            self.env._("schvalovací matice"): stamp("investra.approval.matrix", []),
        }
        source = fund.entity_id.rate_source
        if source and source != "none":
            groups[self.env._("kurzy")] = stamp("investra.rate", [("source", "=", source), ("date", "<=", day)])
        return groups

    def _inputs_changed(self):
        """Názvy skupin vstupů, které se změnily po posledním výpočtu (prázdné = výpočet je aktuální nebo není otisk)."""
        self.ensure_one()
        if self.state != "computed" or not self.inputs_stamp:
            return []
        try:
            before = json.loads(self.inputs_stamp)
        except ValueError:
            return []
        now = self._inputs_now()
        return [name for name, value in now.items() if before.get(name) != value]

    @api.depends("state", "inputs_stamp", "computed_at")
    def _compute_stale_note(self):
        for record in self:
            changed = record._inputs_changed() if record.id else []
            record.stale_note = (
                self.env._("Vstupy výpočtu se změnily po posledním výpočtu (%s). Stiskněte Spočítat; do té doby nejde ocenění odeslat ke schválení.",
                           ", ".join(changed)) if changed else False
            )

    def action_submit(self):
        """Zamkne návrhy a uloží snímek."""
        self._require(PREPARER)
        self._require_state("computed")
        for record in self.sudo():
            changed = record._inputs_changed()
            if changed:
                raise UserError(self.env._(
                    "Výpočet ocenění není aktuální, po výpočtu se změnilo: %s. Stiskněte Spočítat a ocenění odešlete znovu.",
                    ", ".join(changed)))
            stops = record.check_ids.filtered(lambda c: c.status in STOPPING)
            if stops:
                raise UserError(self.env._("Ocenění má nesplněné kontroly: %s", ", ".join(stops.mapped("name"))))
            record.event_ids._lock_events()
            payload, digest = record._fingerprint()
            record.write({"snapshot": payload, "snapshot_hash": digest, "state": "submitted"})
            record._log_step("submitted")
            # Kroky schválení podle schvalovací matice platné v okamžiku předložení (rozhodnutí 2026-11-11).
            rule = self.env["investra.approval.matrix"]._rule("valuation_approve")
            rule.check_performer(self.env)
            if rule.persons == 1:
                steps = [{"name": "Schválení (bez druhé osoby)", "alone": True}]
            else:
                steps = [{"name": step.name, "role_id": step.role.id, "min_role": step.role.name or False}
                         for step in rule.steps]
            record.env["investra.valuation.approval"].create([
                {"valuation_id": record.id, "sequence": index, "matrix_id": rule.row.id, **step}
                for index, step in enumerate(steps)
            ])
        return True

    def action_approve(self):
        """Schválí další krok podle schvalovací matice zapsané při předložení.

        Čtyři oči a kroky: zadavatel nesmí schválit a jeden člověk jen jeden krok. Jeden člověk: schválit smí
        i zadavatel; zapíše se to a další ocenění to ukáže v kontrolách.
        """
        self._require_company()
        self._require_state("submitted")
        user = self.env.user
        for record in self.sudo():
            step = record.approval_ids.filtered(lambda a: not a.user_id).sorted("sequence")[:1]
            # Krok bez druhé osoby schválí ten, kdo ocenění smí schvalovat sám (Provádí); jinak role se Schvaluje.
            check_user(self.env, user, "valuation_approve", PERFORM if step.alone else APPROVE, step.role_id)
            if not step.alone:
                if record.preparer_id == user:
                    raise UserError(self.env._("Zadavatel nemůže schválit vlastní ocenění."))
                if user in record.approval_ids.user_id:
                    raise UserError(self.env._("Jeden člověk nemůže schválit dva kroky."))
            step.write({"user_id": user.id, "approved_at": fields.Datetime.now()})
            record._log_step("approved", step.name)
            if step.alone and user == record.preparer_id:
                Matrix = self.env["investra.approval.matrix"]
                rule = Matrix._row_rule(step.matrix_id) if step.matrix_id else Matrix._builtin_rule("valuation_approve")
                Matrix._log_alone(rule, record)
            if not record.approval_ids.filtered(lambda a: not a.user_id):
                record.state = "approved"
        return True

    def action_return(self, reason):
        """Vrácení před zaúčtováním: návrhy zaniknou bez storen a vznikne nová verze."""
        self._require_company()
        self._require_state("submitted", "approved")
        if not reason:
            raise UserError(self.env._("Uveďte důvod vrácení."))
        request = self._matrix_gate("valuation_return", "action_return", self.env._("Vrácení: %s", reason), reason=reason)
        if request:
            return request
        record = self.sudo()
        record.event_ids.filtered(lambda e: e.state in ("draft", "locked"))._discard_events()
        record.write({"state": "returned", "return_reason": reason})
        record._log_step("returned", reason)
        return record._new_version()

    def action_cancel_draft(self):
        """Zrušení návrhu ocenění (Návrh, Spočteno) tlačítkem; jen zpracovatel (OC-01, rozhodnutí 2026-11-15).

        Návrhy dokladů zaniknou bez storen (nebyly zaúčtované), záznam ocenění se smaže a do historie fondu se zapíše,
        kdo, kdy a které ocenění zrušil. Zaúčtované doklady se nemění. Stav „Zrušeno“ se nezavádí.
        """
        self._require(PREPARER)
        self._require_state("draft", "computed")
        states = dict(self._fields["state"]._description_selection(self.env))
        author = self.env.user.partner_id
        for record in self.sudo():
            fund, name, state = record.fund_id, record.display_name, states.get(record.state)
            drafts = record.event_ids.filtered(lambda e: e.state in ("draft", "locked"))
            record.unlink()
            fund.message_post(
                body=self.env._(
                    "Zrušen návrh ocenění %(valuation)s (stav: %(state)s); zrušené návrhy dokladů: %(count)s.",
                    valuation=name, state=state, count=len(drafts),
                ),
                author_id=author.id,
            )
        return self.env["ir.actions.act_window"]._for_xml_id("investra_nav.action_valuation")

    def _new_version(self):
        self.ensure_one()
        return self.create({"fund_id": self.fund_id.id, "date": self.date, "version": self.version + 1})

    def action_post(self):
        """Zaúčtuje návrhy jedním krokem, jen pokud sedí se schváleným snímkem."""
        self._require(PREPARER)
        self._require_state("approved")
        for record in self.sudo():
            if record._fingerprint()[1] != record.snapshot_hash:
                raise UserError(self.env._("Stav se od schválení změnil, ocenění se musí přepočítat."))
            record.event_ids.filtered(lambda e: e.state == "locked").sorted("id")._post_events()
            record.state = "posted"
            record._log_step("posted")
        return True

    def action_send_depositary(self):
        self._require(PREPARER)
        self._require_state("posted")
        self.sudo().state = "sent"
        self._log_step("sent")
        return True

    def action_depositary_confirm(self):
        self._require(APPROVER)
        self._require_state("sent")
        self.sudo().state = "confirmed"
        self._log_step("confirmed")
        return True

    def action_depositary_return(self, reason):
        """Vrácení depozitářem: storno všech dokladů ocenění a nová verze."""
        self._require_company()
        self._require_state("sent")
        return self._reverse_with_new_version(reason, "action_depositary_return")

    def action_reverse(self, reason):
        """Storno zaúčtovaného nebo depozitářem potvrzeného ocenění a nová verze (rozhodnutí 2026-11-10).

        Zveřejněné ocenění se nestornuje: období je uzamčené, oprava jde jen výjimkou z uzamčení.
        """
        self._require_company()
        self._require_state("posted", "confirmed")
        return self._reverse_with_new_version(reason, "action_reverse")

    def _reverse_with_new_version(self, reason, method):
        """Stornuje zaúčtované doklady ocenění k jejich datu a založí novou verzi v návrhu.

        Podle schvalovací matice může místo storna vzniknout žádost; vrátí ji místo nové verze.
        """
        self.ensure_one()
        if not reason:
            raise UserError(self.env._("Uveďte důvod vrácení."))
        request = self._matrix_gate("valuation_return", method, self.env._("Storno: %s", reason), reason=reason)
        if request:
            return request
        record = self.sudo()
        later = record.search([
            ("fund_id", "=", record.fund_id.id), ("date", ">", record.date),
            ("state", "in", ("submitted", "approved", "posted", "sent", "confirmed", "published")),
        ], limit=1)
        if later:
            raise UserError(self.env._(
                "Na ocenění navazuje pozdější ocenění %s. Nejdřív vraťte to pozdější.", later.display_name
            ))
        record.event_ids.filtered(lambda e: e.state == "posted").sorted("id", reverse=True)._reverse_events()
        record.write({"state": "reversed", "return_reason": reason})
        record._log_step("depositary_returned" if method == "action_depositary_return" else "reversed", reason)
        return record._new_version()

    def action_publish(self):
        """Zveřejnění uzamkne ocenění i období zámkem pro všechny (vrstva 2, rozhodnutí 2026-11-11).

        Zámek je vratný jen výjimkou ze žádosti (`investra.lock.exception.request`); nevratný hard lock
        se nastavuje ručně až po auditu účetní závěrky.
        """
        self._require_company()
        self._require_state("confirmed")
        requests = self.env["investra.approval.request"]
        for record in self:
            request = record._matrix_gate("valuation_publish", "action_publish", self.env._("Zveřejnění a uzamčení období"))
            if request:
                requests |= request
                continue
            record = record.sudo()
            company = record.company_id
            if not company.fiscalyear_lock_date or company.fiscalyear_lock_date < record.date:
                company.fiscalyear_lock_date = record.date
            record.write({"state": "published", "published_at": fields.Datetime.now()})
            record._log_step("published")
        return requests[:1]._action_open() if requests else True

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(SYSTEM_FIELDS & set(vals) for vals in vals_list):
            raise UserError(self.env._("Stav a výsledky ocenění nastavuje jen postup ocenění."))
        records = super().create(vals_list)
        records._check_previous_published()
        records._check_no_later_valuation()
        for record in records:
            record._log_step("created", self.env._("Verze %s", record.version) if record.version > 1 else False)
        return records

    def write(self, vals):
        if not self.env.su and SYSTEM_FIELDS & set(vals):
            raise UserError(self.env._("Stav a výsledky ocenění nastavuje jen postup ocenění."))
        guarded = {"fund_id", "date", "version"}
        if guarded & set(vals) and self.filtered(lambda v: v.state != "draft"):
            raise UserError(self.env._("Datum ani fond ocenění po výpočtu nejde změnit."))
        result = super().write(vals)
        if {"fund_id", "date"} & set(vals):
            self._check_previous_published()
            self._check_no_later_valuation()
        return result

    def _check_previous_published(self):
        """Nové ocenění vznikne, jen když je předchozí ocenění fondu zveřejněné (rozhodnutí 2026-11-14, varianta A).

        Předchozí = poslední dřívější verze, která není vrácená ani stornovaná. Platí pro první verzi k datu
        (založení nebo změnu data návrhu); nová verze po vrácení nebo stornu k témuž datu vzniká dál, aby šlo
        opravit i ocenění založená před zavedením pravidla. První ocenění fondu předchozí nemá.
        """
        for record in self.filtered(lambda v: v.version == 1 and v.fund_id and v.date):
            previous = record.sudo().search([
                ("fund_id", "=", record.fund_id.id), ("date", "<", record.date),
                ("state", "not in", ("returned", "reversed")),
            ], order="date desc, version desc", limit=1)
            if previous and previous.state != "published":
                states = dict(self._fields["state"]._description_selection(self.env))
                raise UserError(self.env._(
                    "Nové ocenění lze založit až po zveřejnění předchozího ocenění %(previous)s (stav: %(state)s).",
                    previous=previous.display_name, state=states.get(previous.state),
                ))

    def _check_no_later_valuation(self):
        """Nové ocenění jen po posledním ocenění fondu (OC-01, rozhodnutí 2026-11-15).

        Blokuje pozdější ocenění v jakémkoli stavu kromě Vráceno a Stornováno. Platí jako `_check_previous_published`
        jen pro první verzi k datu (založení nebo změnu data a fondu návrhu); nové verze po vrácení nebo stornu vznikají
        dál. Stávající záznamy se zpětně nekontrolují.
        """
        for record in self.filtered(lambda v: v.version == 1 and v.fund_id and v.date):
            later = record.sudo().search([
                ("fund_id", "=", record.fund_id.id), ("date", ">", record.date),
                ("state", "not in", ("returned", "reversed")),
            ], order="date desc, version desc", limit=1)
            if later:
                raise UserError(self.env._(
                    "Fond už má ocenění k pozdějšímu datu %(date)s. Nové ocenění lze založit jen po posledním ocenění.",
                    date=format_date(self.env, later.date),
                ))

    def unlink(self):
        if self.filtered(lambda v: v.state not in ("draft", "computed")):
            raise UserError(self.env._("Ocenění po odeslání ke schválení nejde smazat."))
        # Návrhy dokladů zaniknou s oceněním, aby po smazání nezůstaly osiřelé (OC-01).
        self.sudo().event_ids.filtered(lambda e: e.state in ("draft", "locked"))._discard_events()
        return super().unlink()


class InvestraValuationClass(models.Model):
    _name = "investra.valuation.class"
    _description = "Výsledek třídy"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict", string="Třída")
    pre_capital = fields.Float(digits=(20, 2), string="Předběžný kapitál")
    ratio = fields.Float(digits=(16, 12), string="Alokační poměr")
    delta = fields.Float(digits=(20, 2), string="Specifická změna")
    capital = fields.Float(digits=(20, 2), string="Kapitál třídy")
    units = fields.Float(digits=(20, 6), string="Kusy")
    price = fields.Char(string="Kurz")
    perf_reference = fields.Float(digits=(20, 8), string="Srovnávací hodnota odměny")
    perf_hwm = fields.Float(digits=(20, 8), string="High-water mark")
    perf_accrued = fields.Float(digits=(20, 2), string="Naběhlá odměna")
    perf_base_date = fields.Date(string="Začátek období odměny")

    # Přemostění od minulého ocenění (plní výpočet, rozhodnutí 2026-11-10 „Přemostění kapitálu tříd“).
    # Částky ve funkční měně fondu, odkupy a dividendy kladně (odčítají se). Ocenění před zavedením mají 0.
    currency_name = fields.Char(related="class_id.currency_id.name", string="Měna")
    # Jen pro zobrazení v tabulce tříd ocenění (zobrazovaný název třídy obsahuje i název fondu).
    class_code = fields.Char(related="class_id.code", string="Třída")
    opening_capital = fields.Float(digits=(20, 2), string="FK (t−1)", help="Kapitál třídy z minulého ocenění.")
    opening_units = fields.Float(digits=(20, 6), string="Kusy (t−1)")
    opening_price = fields.Char(string="Kurz (t−1)")
    subscription_amount = fields.Float(digits=(20, 2), string="Úpisy")
    subscription_units = fields.Float(digits=(20, 6), string="Úpisy ks")
    redemption_amount = fields.Float(digits=(20, 2), string="Odkupy", help="Kladně; od kapitálu se odčítá.")
    redemption_units = fields.Float(digits=(20, 6), string="Odkupy ks")
    dividend_amount = fields.Float(digits=(20, 2), string="Dividendy",
                                   help="Výplata dividendy z třídy; do zavedení pohybu „výplata dividendy“ je 0.")
    shared_result = fields.Float(digits=(20, 2), string="Změna společná",
                                 help="Podíl třídy na změně společné části fondu podle alokačního poměru, včetně zaokrouhlení.")
    rounding_amount = fields.Float(digits=(20, 2), string="Z toho zaokrouhlení")
    fee_amount = fields.Float(digits=(20, 2), string="Úplaty třídy", help="Úplaty účtované na třídu, bez výkonnostní odměny.")
    performance_amount = fields.Float(digits=(20, 2), string="Výkonnostní odměna")
    allocation_amount = fields.Float(digits=(20, 2), string="Přesun podle pořadí nároků")
    other_amount = fields.Float(digits=(20, 2), string="Ostatní specifické",
                                help="Ostatní položky třídy, např. měnové zajištění nebo podíl na úplatě jiné třídy.")
    fx_rate = fields.Float(digits=(16, 8), string="Kurz přepočtu", help="Funkční měna fondu za 1 jednotku měny třídy.")
    opening_capital_class = fields.Float(digits=(20, 2), string="FK (t−1) v měně třídy")
    subscription_amount_class = fields.Float(digits=(20, 2), string="Úpisy v měně třídy")
    redemption_amount_class = fields.Float(digits=(20, 2), string="Odkupy v měně třídy")
    capital_class = fields.Float(digits=(20, 2), string="FK v měně třídy")
    price_change_pct = fields.Float(digits=(16, 4), string="Změna kurzu %")
    foreign_currency = fields.Boolean(compute="_compute_foreign_currency", string="Třída v cizí měně")
    # Jen pro zobrazení v tabulce tříd: kurz je uložený jako text (přesná hodnota), tady v notaci jazyka uživatele.
    price_display = fields.Char(compute="_compute_display", string="Kurz")
    price_change_display = fields.Char(compute="_compute_display", string="Změna kurzu")

    @api.depends("price", "price_change_pct")
    def _compute_display(self):
        lang = self.env["res.lang"]._get_data(code=self.env.lang or "en_US")
        point, sep = lang.decimal_point or ",", lang.thousands_sep or " "

        def number(text, digits=None):
            value = Decimal(text)
            if digits is not None:
                value = value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
            sign, digits_text = ("−", f"{-value:f}") if value < 0 else ("", f"{value:f}")
            whole, _, frac = digits_text.partition(".")
            groups = []
            while len(whole) > 3:
                groups.insert(0, whole[-3:])
                whole = whole[:-3]
            groups.insert(0, whole)
            return sign + sep.join(groups) + (point + frac if frac else "")

        for line in self:
            line.price_display = number(line.price) if line.price else ""
            if line.opening_price:
                change = number(str(line.price_change_pct), 2)
                line.price_change_display = ("+" if line.price_change_pct > 0 else "") + change + " %"
            else:
                line.price_change_display = ""

    @api.depends("class_id.currency_id", "valuation_id.fund_id.currency_id")
    def _compute_foreign_currency(self):
        for line in self:
            line.foreign_currency = line.class_id.currency_id != line.valuation_id.fund_id.currency_id


class InvestraValuationFee(models.Model):
    _name = "investra.valuation.fee"
    _description = "Rozpis úplaty"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    # Bez pravidla je to ručně doložená úplata (ZJ-03); název ji pak popíše poznámkou.
    rule_id = fields.Many2one("investra.fee.rule", ondelete="restrict", string="Pravidlo")
    external_id = fields.Many2one("investra.valuation.external", ondelete="set null", string="Ručně doložená úplata")
    name = fields.Char(compute="_compute_name", string="Úplata")
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict", string="Třída")
    amount = fields.Float(digits=(20, 2), string="Částka")
    detail = fields.Text(string="Výpočet")

    @api.depends("rule_id.name", "external_id.note", "external_id.corrects_rule_id.name")
    def _compute_name(self):
        for line in self:
            if line.rule_id:
                line.name = line.rule_id.name
            else:
                note = (line.external_id.note or "").splitlines()
                corrected = line.external_id.corrects_rule_id
                label = self.env._("Oprava úplaty %s", corrected.name) if corrected else self.env._("Ručně doložená úplata")
                line.name = label + (f": {note[0]}" if note else "")


class InvestraValuationExternal(models.Model):
    """Ručně doložená úplata (ZJ-03, rozhodnutí 2026-11-17): bez pravidla, schvaluje se s oceněním.

    Třída prázdná = celý fond. Částka smí být záporná (oprava), ne nulová. Poznámka je povinná, příloha nepovinná.
    Účtuje se k datu ocenění na zvolený nákladový účet, protiúčet je vždy závazek z úplat.

    Oprava úplaty (ZJ-11): s vyplněným „Opravuje úplatu“ se nákladový účet nezadává, účtuje se jako úplata pravidla.
    """

    _name = "investra.valuation.external"
    _inherit = ["investra.record.guard"]
    _description = "Ručně doložená úplata"
    _book_fields = ("valuation_id",)

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict", string="Třída",
                               help="Prázdné = úplata celého fondu, dělí se mezi třídy poměrem.")
    amount = fields.Float(digits=(20, 2), required=True, string="Částka",
                          help="Náklad fondu; záporná částka náklad snižuje (oprava). Nula není dovolená.")
    currency_id = fields.Many2one("res.currency", default=lambda self: self._default_currency(), string="Měna",
                                  help="Cizí měna se přepočte kurzem k datu ocenění ze zdroje kurzů fondu.")
    # Povinnost účtu a poznámky hlídá kontrola v Pythonu a formulář (ne NOT NULL), aby migrace staré řádky stihla smazat.
    account_id = fields.Many2one("account.account", ondelete="restrict", string="Nákladový účet",
                                 domain="[('account_type', '=like', 'expense%')]")
    note = fields.Text(string="Poznámka")
    corrects_rule_id = fields.Many2one(
        "investra.fee.rule", ondelete="restrict", string="Opravuje úplatu",
        domain="[('kind', '=', 'periodic')]",
        help="Oprava vypočtené časově rozlišené úplaty (zaokrouhlení podle faktury, dohoda s depozitářem). Účtuje se "
             "na nákladovou roli pravidla a dělí se příjemcům z tříd jako původní úplata; nákladový účet se nezadává. "
             "Oprava platí trvale: průměrný FK ji v dalším ocenění nedorovná.",
    )
    attachment_id = fields.Many2one("ir.attachment", string="Výpočet", ondelete="restrict")
    # Nahrání souboru přímo v řádku; ukládá se jako příloha ocenění do attachment_id.
    document = fields.Binary(string="Soubor s výpočtem", compute="_compute_document", inverse="_inverse_document")
    document_name = fields.Char(string="Název souboru", compute="_compute_document", inverse="_inverse_document")

    @api.depends("attachment_id")
    def _compute_document(self):
        # Odoo 20 drží obsah přílohy v poli raw; hodnota binárního pole je objekt s obsahem a názvem.
        for row in self:
            attachment = row.attachment_id.sudo()
            row.document = attachment.raw
            row.document_name = attachment.name

    def _inverse_document(self):
        for row in self:
            if not row.document:
                continue
            content = row.document.content
            if row.attachment_id and row.attachment_id.sudo().raw.content == content:
                continue
            attachment = self.env["ir.attachment"].create({
                "name": row.document_name or "vypocet",
                "raw": content,
                "res_model": "investra.valuation",
                "res_id": row.valuation_id.id,
            })
            row.attachment_id = attachment

    def _check_open(self):
        if not self.env.su and self.valuation_id.filtered(lambda v: v.state not in ("draft", "computed")):
            raise UserError(self.env._("Ručně doložené úplaty po odeslání ke schválení nejde měnit."))

    @api.model
    def _default_currency(self):
        valuation = self.env["investra.valuation"].browse(self.env.context.get("default_valuation_id"))
        return valuation.fund_id.currency_id if valuation.exists() else False

    @api.constrains("valuation_id", "class_id", "amount", "account_id", "note", "corrects_rule_id", "currency_id")
    def _check_fund(self):
        # Třída a účet musí patřit fondu ocenění; formulář je nabízí jen z něj, kontrola chrání i import a API.
        for row in self:
            fund = row.valuation_id.fund_id
            if row.class_id and row.class_id.fund_id != fund:
                raise ValidationError(self.env._("Třída ručně doložené úplaty musí patřit fondu ocenění %s.", fund.display_name))
            if row.corrects_rule_id:
                row._check_correction(fund)
            elif not row.account_id or not row.account_id.account_type.startswith("expense"):
                raise ValidationError(self.env._("Ručně doložená úplata potřebuje nákladový účet."))
            if row.account_id.company_ids and row.valuation_id.company_id not in row.account_id.company_ids:
                raise ValidationError(self.env._("Nákladový účet ručně doložené úplaty musí patřit knize fondu %s.", fund.display_name))
            if not (row.note or "").strip():
                raise ValidationError(self.env._("Ručně doložená úplata musí mít poznámku."))
            if not round(row.amount, 2):
                raise ValidationError(self.env._("Částka ručně doložené úplaty nesmí být nulová."))

    def _check_correction(self, fund):
        """Oprava úplaty (ZJ-11): pravidlo fondu ocenění, třída podle pravidla, bez nákladového účtu, měna fondu."""
        rule = self.corrects_rule_id
        if rule.fund_id != fund:
            raise ValidationError(self.env._("Opravovaná úplata %(rule)s nepatří fondu ocenění %(fund)s.",
                                             rule=rule.name, fund=fund.display_name))
        if rule.kind != "periodic":
            # Výkonnostní odměna a daň se počítají jako doplatek do požadovaného stavu; opravu by další ocenění dorovnalo.
            raise ValidationError(self.env._("Opravit jde jen časově rozlišenou úplatu, ne %s.", rule.name))
        if rule.class_ids and self.class_id not in rule.class_ids:
            raise ValidationError(self.env._("Oprava úplaty %(rule)s musí mít třídu, která úplatu platí: %(classes)s.",
                                             rule=rule.name, classes=", ".join(rule.class_ids.mapped("code"))))
        if not rule.class_ids and self.class_id:
            raise ValidationError(self.env._("Úplata %s je úplatou celého fondu; oprava nesmí mít třídu.", rule.name))
        if self.account_id:
            raise ValidationError(self.env._("Oprava úplaty se účtuje na nákladovou roli pravidla; nákladový účet nevyplňujte."))
        if self.currency_id and self.currency_id != fund.currency_id:
            raise ValidationError(self.env._("Oprava úplaty musí být v měně fondu %s.", fund.currency_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_open()
        return records

    def write(self, vals):
        self._check_open()
        return super().write(vals)

    def unlink(self):
        self._check_open()
        return super().unlink()


class InvestraValuationStep(models.Model):
    """Krok ocenění (ZJ-06 bod 12, rozhodnutí 2026-11-17): kdo, kdy a co s oceněním udělal.

    Auditní stopa NAV: zapisuje jen postup ocenění (sudo), záznam nejde změnit ani smazat. Zaniká jen se zrušeným
    návrhem ocenění (kaskáda v databázi); zrušení se zapisuje do historie fondu.
    """

    _name = "investra.valuation.step"
    _description = "Krok ocenění"
    _order = "valuation_id, id desc"

    valuation_id = fields.Many2one("investra.valuation", required=True, readonly=True, ondelete="cascade", index=True,
                                   string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    step = fields.Selection(VALUATION_STEPS, required=True, readonly=True, string="Krok")
    user_id = fields.Many2one("res.users", required=True, readonly=True, ondelete="restrict", string="Provedl")
    done_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now, string="Kdy")
    note = fields.Text(readonly=True, string="Poznámka", help="Důvod vrácení nebo storna, název kroku schválení, souhrn výpočtu.")

    def write(self, vals):
        raise UserError(self.env._("Krok ocenění nejde měnit."))

    def unlink(self):
        raise UserError(self.env._("Krok ocenění nejde smazat."))


class InvestraValuationPortfolio(models.Model):
    """Řádek listu portfolio: finanční aktivum k datu ocenění."""

    _name = "investra.valuation.portfolio"
    _description = "Řádek portfolia"
    _order = "kind, name"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    kind = fields.Selection(
        [("bank", "Bankovní účet"), ("deposit", "Termínovaný vklad"), ("equity", "Akcie"), ("bond", "Dluhopis"),
         ("fund", "Fond"), ("participation", "Účast"), ("loan", "Úvěr"), ("derivative", "Derivát"), ("repo", "Repo"), ("other_holding", "Ostatní podíl")],
        required=True,
        string="Druh",
    )
    instrument_id = fields.Many2one("investra.instrument", ondelete="restrict", string="Nástroj")
    portfolio_id = fields.Many2one("investra.fund.portfolio", ondelete="restrict", string="Obchodní model")
    classification_id = fields.Many2one("investra.portfolio.classification", ondelete="restrict", string="Zařazení")
    ifrs9_category = fields.Selection(related="classification_id.ifrs9_category", string="Kategorie IFRS 9")
    name = fields.Char(required=True, string="Název")
    isin = fields.Char(string="ISIN")
    currency_id = fields.Many2one("res.currency", required=True, string="Měna")
    quantity = fields.Float(digits=(20, 6), string="Kusy")
    price = fields.Float(digits=(20, 8), string="Cena")
    price_source = fields.Char(string="Zdroj ceny")
    price_id = fields.Many2one("investra.instrument.price", ondelete="restrict", string="Použitá cena")
    price_date = fields.Date(string="Datum ceny")
    cost_currency = fields.Float(digits=(20, 2), string="Pořizovací hodnota v měně")
    cost = fields.Float(digits=(20, 2), string="Pořizovací hodnota v měně fondu", help="Zbývající kusy průměrnou cenou, bez naběhlého úroku.")
    accrued_interest_currency = fields.Float(digits=(20, 2), string="Naběhlý úrok v měně",
                                             help="U nástrojů v RH: úrok vydělaný a dosud nepřijatý; u dluhopisů je v reálné hodnotě.")
    realised = fields.Float(digits=(20, 2), string="Realizovaný výsledek v měně fondu",
                            help="Prodej a splacení od minulého ocenění: výnos bez úroku − poměrná účetní hodnota.")
    fair_value_currency = fields.Float(digits=(20, 2), string="Reálná hodnota v měně")
    fx_rate = fields.Float(digits=(16, 8), string="Kurz")
    fx_source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], string="Zdroj kurzu")
    fair_value = fields.Float(digits=(20, 2), string="Reálná hodnota v měně fondu")


class InvestraValuationCheck(models.Model):
    _name = "investra.valuation.check"
    _description = "Kontrola ocenění"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    code = fields.Char(required=True, string="Kód")
    name = fields.Char(required=True, string="Kontrola")
    status = fields.Selection([("ok", "V pořádku"), ("warning", "Upozornění"), ("stop", "Stop")], required=True, string="Výsledek")
    detail = fields.Char(string="Podrobnosti")


class InvestraValuationApproval(models.Model):
    _name = "investra.valuation.approval"
    _description = "Schválení ocenění"
    _order = "valuation_id, sequence"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    sequence = fields.Integer(required=True, string="Pořadí")
    name = fields.Char(required=True, string="Krok")
    user_id = fields.Many2one("res.users", readonly=True, string="Schválil")
    approved_at = fields.Datetime(readonly=True, string="Schváleno dne")
    # Požadavek kroku ze schvalovací matice v okamžiku předložení.
    matrix_id = fields.Many2one("investra.approval.matrix", readonly=True, ondelete="restrict", string="Řádek matice")
    role_id = fields.Many2one("investra.role", readonly=True, ondelete="restrict", string="Role kroku")
    # Text role v okamžiku předložení; u kroků před ZJ-01 název tehdejší nejnižší role (převedeno migrací).
    min_role = fields.Char(readonly=True, string="Role (text)")
    alone = fields.Boolean(readonly=True, string="Bez druhé osoby")


class InvestraRate(models.Model):
    """Ruční kurz se nesmí dotknout už schváleného ocenění (rozhodnutí 2026-11-10 „Ochrana kurzů“).

    Kdo kurz zadá a zda ho potvrdí druhá osoba, určuje schvalovací matice (rozhodnutí 2026-11-11); matice platí
    pro celou aplikaci (ZJ-01).
    """

    _inherit = "investra.rate"

    @api.model
    def _check_manual_access(self, source):
        Matrix = self.env["investra.approval.matrix"]
        if self.env.su or Matrix._passing("manual_rate", self.browse()):
            return
        Matrix._rule("manual_rate").check_performer(self.env)

    @api.model
    def _manual_pending(self, origin, source, currency, day, quantity, rate, reason):
        kind = dict(self._fields["origin"].selection).get(origin, origin)
        return self.env["investra.approval.matrix"]._gate(
            "manual_rate", self.browse(), "_matrix_create_manual",
            {"origin": origin, "source": source, "currency_id": currency.id, "day": str(day),
             "quantity": quantity, "rate": rate, "reason": reason},
            summary=f"{kind} {currency.name} k {day}: {quantity} = {rate} ({reason})",
        )

    @api.model
    def _matrix_create_manual(self, origin, source, currency_id, day, quantity, rate, reason):
        """Provedení schválené žádosti o ruční kurz."""
        return self.create_manual(origin, source, self.env["res.currency"].browse(currency_id), day, quantity, rate, reason)

    @api.model
    def _check_change_allowed(self, source, day):
        blocking = self.env["investra.valuation"].sudo().search([
            ("fund_id.entity_id.rate_source", "=", source),
            ("date", ">=", day),
            ("state", "in", ("approved", "posted", "sent", "confirmed", "published")),
        ], order="date", limit=1)
        if blocking:
            raise UserError(self.env._(
                "K datu %(day)s nebo později je schválené ocenění %(valuation)s; ruční kurz by změnil jeho podklad. "
                "Nejdřív ocenění vraťte.", day=day, valuation=blocking.display_name,
            ))
        return super()._check_change_allowed(source, day)
