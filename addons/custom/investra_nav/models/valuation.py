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
        """Souhrn výpočtu do historie: FK, kurzy tříd a opravy (ZJ-12 B.9)."""
        self.ensure_one()
        prices = ", ".join(f"{line.class_id.code} {line.price}" for line in self.class_line_ids)
        note = self.env._("FK %(fk).2f %(currency)s; kurzy tříd: %(prices)s",
                          fk=self.fund_capital, currency=self.currency_id.name or "", prices=prices or "-")
        corrections = self._corrections_summary()
        return f"{note}\n{corrections}" if corrections else note

    def _corrections_summary(self):
        """Seznam oprav ocenění pro stopu (ZJ-12 B.9): pravidlo, třída, vypočteno → oprava, platnost, zdůvodnění, kdo
        zadal; ukončení a převzetí z verze jsou rozlišené. Na konci počet převzatých oprav dřívějších ocenění."""
        self.ensure_one()
        validity = dict(self.env["investra.valuation.external"]._fields["validity"].selection)
        rows = []
        for entry in self.external_fee_ids.filtered("corrects_rule_id"):
            head = " ".join(filter(None, [entry.corrects_rule_id.name, entry.class_id.code]))
            if entry.correction_target == "base":
                what = self.env._("oprava základu %s", f"{entry.amount:+.2f}")
            else:
                what = self.env._("vypočteno %(computed)s → %(result)s (oprava %(amount)s)",
                                  computed=f"{entry.computed_now:.2f}", result=f"{entry.computed_now + entry.amount:.2f}",
                                  amount=f"{entry.amount:+.2f}")
            extra = []
            if entry.ended_id:
                extra.append(self.env._("ukončuje opravu z %s", entry.ended_id.valuation_id.display_name))
            if entry.origin_id:
                extra.append(self.env._("převzato z verze %s", entry.origin_id.valuation_id.version))
            rows.append("; ".join([f"{head}: {what}", validity.get(entry.validity, ""), entry.note or "",
                                   self.env._("zadal %s", entry.create_uid.name), *extra]))
        carried = self.check_ids.filtered(lambda c: c.code == "carried_corrections" and c.status != "ok")
        if carried:
            rows.append(carried.name)
        return (self.env._("Opravy: ") + " | ".join(rows)) if rows else ""

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
        # ZJ-12 krok 3: společný dopočet úplat, výkonnostní odměny a daně (engine.solve_fees) místo pevného pořadí
        # podle druhu (ZJ-06 bod 7). Základ každého pravidla volí „Základ: po kroku 1–4“; doklady vznikají až po ustálení.
        rules = self.env["investra.fee.rule"].search([("fund_id", "=", self.fund_id.id)])
        self._apply_fees(rules, context)
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
        # ZJ-09 A3: zůstatky po třídách, aby se třída na přeceňovaných účtech neztratila; banky třídu nemají.
        balances = self.env["investra.fx.profile"].sudo()._foreign_balances(
            company, self._fx_accounts(), self.date, domain=self._line_domain(),
            by_partner=lambda account: account.account_type != "asset_cash", extra_groupby=("investra_class_id",),
        )
        lines = []
        for account, currency, partner, amount, balance, fund_class in balances:
            if account not in roles:
                raise UserError(self.env._("Účet %s v profilu přecenění nemá v knize roli.", account.display_name))
            code, main = roles[account]
            difference = engine.money(d(amount) * self._fx(currency)) - engine.money(d(balance))
            if not difference:
                continue
            cls = {"class_id": fund_class.id} if fund_class else {}  # bez třídy klíč nepřidávat → otisk beze změny
            line = {"role": code, "amount": difference, "movement_type": "fx_revaluation",
                    "currency_id": currency.id, "amount_currency": "0", **cls}
            if not main:
                line["extra"] = {"account_id": account.id}
            if partner:
                line["partner_id"] = partner.id
            lines.append(line)
            lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                          "movement_type": "fx_revaluation", **cls})
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
            # ZJ-09 A2(e): pohledávka a závazek nevypořádaného obchodu v portfoliu třídy nesou třídu, přecenění po třídách.
            groups = Line._read_group(
                self._line_domain(("account_id", "=", account.id)),
                groupby=["currency_id", "investra_class_id"], aggregates=["amount_currency:sum", "balance:sum"],
            )
            for currency, fund_class, amount, balance in groups:
                if currency == self.fund_id.currency_id:
                    continue
                difference = engine.money(d(amount) * self._fx(currency)) - engine.money(balance)
                if difference:
                    cls = {"class_id": fund_class.id} if fund_class else {}  # bez třídy klíč nepřidávat → otisk beze změny
                    lines.append({"role": role, "amount": difference, "movement_type": "fx_revaluation",
                                  "currency_id": currency.id, "amount_currency": "0", **cls})
                    lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                                  "movement_type": "fx_revaluation", **cls})
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

    def _book_fee(self, rule, amount, fund_class, movement="fee", payable="fee_payable", kind_suffix="", name=None,
                  weights=None):
        """Zaúčtuje úplatu: část příjemcům z tříd přes vnitřní zúčtování, zbytek jako náklad a závazek.

        Částka smí být záporná (oprava úplaty, ZJ-11): náklad, závazek i přesun mezi třídami mají opačné znaménko.
        `weights` = hodnoty tříd, se kterými počítal společný dopočet (po kroku 1).
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
            lines += self._transfer_lines(fund_class, self._recipient_parts(rule, to_classes, weights))
        self._add_event(f"fee:{rule.id}:{class_id}{kind_suffix}", name or rule.name, lines)

    def _recipient_parts(self, rule, amount, weights=None):
        """Podíl přijímajícím třídám podle jejich hodnoty (záporná hodnota = váha 0).

        ZJ-12 krok 3: váhy jsou hodnoty tříd po kroku 1, stejné jako v dopočtu; dřív aktuální stav knihy v okamžiku
        zaúčtování, který závisel na pořadí dokladů. Bez `weights` zůstává dřívější chování.
        """
        if weights is None:
            context = self._class_context()
            weights = {c: self._class_value(c, context) for c in rule.recipient_class_ids}
        weights = self._recipient_weights(rule, weights)
        if not any(weights.values()):
            raise UserError(self.env._(
                "Pravidlo %s: žádná přijímající třída nemá kladnou hodnotu, podíl příjemcům nelze rozdělit.", rule.name))
        parts = engine.split_amount(amount, {c.code: weight for c, weight in weights.items()})
        return {c: parts[c.code] for c in rule.recipient_class_ids}

    @staticmethod
    def _recipient_weights(rule, values):
        """Váhy přijímajících tříd (rozhodnutí 2026-11-19) – stejné pro dopočet, doklad i uložený rozpad.

        Jediná přijímající třída dostane celý podíl bez ohledu na svou hodnotu (i nulovou: třída, která se neúčastní
        výsledku portfolia a jen přijímá odměnu, může začínat bez kapitálu). Více tříd: váha = kladná hodnota, nekladné
        nedostanou nic; když není kladná žádná, `_recipient_parts` ocenění zastaví srozumitelnou chybou.
        """
        classes = rule.recipient_class_ids
        if len(classes) == 1:
            return {classes: Decimal(1)}
        return {c: max(d(values[c]), Decimal(0)) for c in classes}

    def _transfer_lines(self, payer, parts):
        """Přesun hodnoty mezi třídami: účet vnitřního zúčtování má v součtu nulu, FK se nemění.

        Plátce prázdný = celý fond (úplata fondu s příjemci, rozhodnutí 2026-11-19): řádek bez třídy nesou třídy poměrem,
        stejně jako v dopočtu (`engine.fee_effects`, plátce None).
        """
        total = sum(parts.values())
        lines = [{"role": "internal_clearing", "amount": -total, "class_id": payer.id if payer else False,
                  "movement_type": "class_transfer"}]
        for fund_class, amount in parts.items():
            lines.append({"role": "internal_clearing", "amount": amount, "class_id": fund_class.id, "movement_type": "class_transfer"})
        return lines

    def _periodic_amount(self, rule, base):
        """Částka časově rozlišené úplaty z daného základu; základ podle kroku řeší společný dopočet, ne engine."""
        start, end = self._period_start(), self.date
        spec = rule._engine_rule(start, end)
        return engine.periodic_fee(spec, start, end, base, classes_count=len(self.fund_id.class_ids))

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

    # --- společný dopočet úplat, odměny a daně (ZJ-12 krok 3) ----------------------------------------------------

    def _year_start(self):
        """Poslední den předchozího roku: ocenění „od 1. 1.“ mají datum po něm."""
        return date_type(self.date.year - 1, 12, 31)

    def _earlier_valuations(self, after_day):
        """Zaúčtovaná dřívější ocenění fondu po dni `after_day` a před tímto oceněním."""
        return self.search([
            ("fund_id", "=", self.fund_id.id), ("date", ">", after_day), ("date", "<", self.date),
            ("state", "in", ("posted", "sent", "confirmed", "published")),
        ], order="date, version")

    def _earlier_fee_items(self, after_day):
        """Úplaty, ruční úplaty, opravy a výkonnostní odměny dřívějších ocenění po dni `after_day` (ZJ-12 B.3, B.4).

        Položka: krok (2 úplaty, 3 odměna), plátce, náklad mimo fond (`expense`), částka nesená třídami (`borne`) a kusy
        tříd v tom ocenění. Řádky od ZJ-12 kroku 3 mají `expense` a `borne` v detailu. Starší řádky je nemají: náklad =
        částka × (1 − podíl příjemců pravidla), plátce-třída nese celou částku, společnou úplatu nesou třídy poměrem
        ocenění; podíl přijatý od jiných tříd se u nich nezná a vynechá se (odchylka jen u řádků před krokem 3).
        Krytí (`covered_by`) je přesun mezi třídami, ne náklad. Daň (krok 4, pro základ odměny): třída nesla podíl pohybu
        daně podle poměru ocenění minus přesun daňového efektu do třídy (`transfers` v detailu; starší řádky ho nemají).
        """
        result = []
        for valuation in self._earlier_valuations(after_day):
            ratios = {line.class_id.id: d(line.ratio) for line in valuation.class_line_ids}
            units = {line.class_id.id: d(line.units) for line in valuation.class_line_ids}
            averages = set()
            for line in valuation.fee_line_ids:
                detail = json.loads(line.detail or "{}")
                rule = line.rule_id or line.external_id.corrects_rule_id
                if detail.get("covered_by") or detail.get("target") == "base":
                    continue
                if rule and rule.kind == "tax":
                    amount = d(line.amount)
                    transfers = {int(key): d(value) for key, value in (detail.get("transfers") or {}).items()}
                    result.append({
                        "stage": engine.STAGE_TAX, "payer": None, "expense": amount, "units": units,
                        "borne": {key: ratio * amount - transfers.get(key, Decimal(0)) for key, ratio in ratios.items()},
                    })
                    continue
                if line.rule_id.base_source == "average_fk" and not detail.get("per_class"):
                    # Před krokem 3 vznikal u průměrného FK s více třídami řádek za každou třídu se stejnou částkou
                    # (doklad jen jeden, B.6): z ocenění se bere jen první řádek pravidla. Řádky po třídách (ZJ-14,
                    # `per_class`) jsou samostatné úplaty tříd a neslučují se.
                    if line.rule_id in averages:
                        continue
                    averages.add(line.rule_id)
                amount = d(line.amount)
                if "expense" in detail:
                    expense = d(detail["expense"])
                else:
                    share = d(rule.recipient_share) if rule and rule.recipient_class_ids else Decimal(0)
                    expense = amount * (1 - share)
                if "borne" in detail:
                    borne = {int(key): d(value) for key, value in detail["borne"].items()}
                elif line.class_id:
                    borne = {line.class_id.id: amount}
                else:
                    borne = {key: ratio * amount for key, ratio in ratios.items()}
                result.append({
                    "stage": engine.STAGE_PERFORMANCE if rule and rule.kind == "performance" else engine.STAGE_FEE,
                    "payer": line.class_id.id or None, "expense": expense, "borne": borne, "units": units,
                })
        return result

    def _borne_since(self, fund_class, day, measure, units_now, stages):
        """Úplaty (krok 2) a daň (krok 4), které třída nesla v dřívějších oceněních po dni `day` („přičti od data D“,
        ZJ-12 B.3): {krok: částka} pro zadané kroky.

        Položky tohoto ocenění se nepřičítají: základ po kroku 1 nebo 2 je stav před nimi. U měřítka hodnota na kus se
        přičte částka na kus podle kusů v každém ocenění, převedená na dnešní kusy.
        """
        total = {stage: Decimal(0) for stage in stages}
        for item in self._earlier_fee_items(day):
            if item["stage"] not in total:
                continue
            borne = item["borne"].get(fund_class.id, Decimal(0))
            if measure == "unit":
                units = item["units"].get(fund_class.id)
                total[item["stage"]] += borne / units * d(units_now) if units else Decimal(0)
            else:
                total[item["stage"]] += borne
        return total

    def _recipients(self, rule, values):
        """Podíl a váhy přijímajících tříd pro dopočet: hodnoty tříd po kroku 1 (stejné váhy pak zaúčtování)."""
        if not rule.recipient_class_ids:
            return {}
        return {"share": d(rule.recipient_share),
                "recipients": {c.id: weight for c, weight in self._recipient_weights(rule, values).items()}}

    def _periodic_item(self, rule, fund_class):
        """Časově rozlišená úplata: základ FK nebo kapitál třídy po zvoleném kroku; aktiva a bez základu jsou pevné."""
        constant = base = None
        shift = {"base": Decimal(0)}
        if rule.base_source in ("none", "assets"):
            constant = Decimal(0) if rule.base_source == "none" else self._assets()
        elif rule.base_source == "class_fk" and fund_class:
            base = {"scope": "class", "class": fund_class.id, "step": int(rule.base_step)}
        else:
            base = {"scope": "fund", "step": int(rule.base_step)}

        def full(value):
            # Oprava základu (B.7) se přičte ke stavu k datu jen v tomto ocenění.
            value = (constant if base is None else value) + shift["base"]
            result = self._periodic_amount(rule, value)
            return {"base": value, "base_step": rule.base_step, **result, "move": result["amount"]}

        return {"base": base, "amount": lambda value: full(value)["exact"], "full": full, "shift": shift}

    def _average_item(self, rule):
        """Úplata z průměrného FK (ZJ-12 B.6): nárok od začátku roku minus to, co už je v roce naúčtované.

        Průměr prostý: dřívější body jsou zveřejněné FK, dnešní bod je FK po zvoleném kroku (v dopočtu váha 1/n).
        Pravidlo bez Platí třídy dává jednu položku celého fondu (oprava B.6: dřív řádek za každou třídu a dvojí „booked“);
        pravidlo s třídami počítá `_average_class_item` (ZJ-14).
        """
        year_start = self._year_start()
        start = max(year_start, self.fund_id.launch_date or year_start)
        earlier = self._earlier_valuations(year_start)
        # ZJ-14 (doplněno Claudem): pravidlo počítané letos po třídách nejde v roce přepnout na celý fond.
        if any(json.loads(line.detail or "{}").get("per_class")
               for line in earlier.fee_line_ids.filtered(lambda l: l.rule_id == rule)):
            raise UserError(self.env._(
                "Pravidlo %s bylo letos počítáno po třídách; přepnout na celý fond jde od 1. 1. nebo novým pravidlem.",
                rule.name))
        capitals = [d(v.fund_capital) for v in earlier]
        booked = Decimal(0)
        for valuation in earlier:
            # Starší ocenění mohou mít řádek za každou třídu se stejnou částkou (B.6): bere se jeden.
            lines = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
            booked += d(lines[0].amount) if lines else Decimal(0)
        spec = rule._engine_rule(start, self.date)
        count = len(self.fund_id.class_ids)
        shift = {"base": Decimal(0)}

        def full(current):
            # Oprava základu (B.7) upravuje celoroční průměr; převzatá platí do konce roku.
            average = (sum(capitals, Decimal(0)) + current) / (len(capitals) + 1) + shift["base"]
            result = engine.periodic_fee(spec, start, self.date, average, classes_count=count)
            return {"average": average, "booked": booked, "base_step": rule.base_step, **result,
                    "move": result["amount"] - booked}

        return {"base": {"scope": "fund", "step": int(rule.base_step)},
                "amount": lambda current: full(current)["exact"] - booked, "full": full, "shift": shift}

    def _first_subscription(self, fund_class):
        """Vznik třídy (ZJ-14): datum prvního nestornovaného úpisu do data ocenění, jinak None."""
        movement = self.env["investra.class.movement"].sudo().search([
            ("class_id", "=", fund_class.id), ("movement_type", "=", "subscription"), ("state", "!=", "reversed"),
            ("date", "<=", self.date),
        ], order="date", limit=1)
        return movement.date if movement else None

    def _average_class_item(self, rule, fund_class):
        """Úplata z průměrného FK třídy (ZJ-14): nárok od začátku nároku třídy minus to, co třída v roce už nesla.

        Začátek nároku S = nejpozdější z: 31. 12. minulého roku (a vznik fondu), první úpis třídy, zařazení třídy do
        pravidla. Zařazení = první zaúčtované ocenění v roce s řádkem (pravidlo, třída, `per_class`); S = začátek jeho
        období. Body: kapitál třídy zaúčtovaných ocenění v roce po S, která řádek (pravidlo, třída, `per_class`) mají
        (třída v nich byla v pravidle), plus dnešní bod = hodnota třídy po zvoleném kroku (v dopočtu váha 1/n).
        Pevné části, minimum, maximum a příplatky za každou třídu. Booked = řádky (pravidlo, třída, `per_class`);
        ruční opravy částky (řádky bez pravidla) se neodečítají, platí trvale. Třída bez úpisu položku nemá (None).
        """
        created = self._first_subscription(fund_class)
        if not created:
            return None
        year_start = self._year_start()
        earlier = self._earlier_valuations(year_start)
        in_rule = {}
        for valuation in earlier:
            lines = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)
            details = [json.loads(line.detail or "{}") for line in lines]
            if any(not detail.get("per_class") for detail in details):
                raise UserError(self.env._(
                    "Pravidlo %s bylo letos počítáno za celý fond; přepnout na třídy jde od 1. 1. nebo novým pravidlem.",
                    rule.name))
            own = lines.filtered(lambda l: l.class_id == fund_class)
            if own:
                in_rule[valuation] = own
        first = next((v for v in earlier if v in in_rule), None)
        entry = first._period_start() if first else self._period_start()
        start = max(year_start, self.fund_id.launch_date or year_start, created, entry)
        points, booked = [], Decimal(0)
        for valuation in earlier:
            if valuation not in in_rule:
                continue
            booked += sum((d(line.amount) for line in in_rule[valuation]), Decimal(0))
            if valuation.date > start:
                row = valuation.class_line_ids.filtered(lambda l: l.class_id == fund_class)[:1]
                points.append((valuation.date, d(row.capital)))
        # Přerušené zařazení: zaúčtované ocenění po prvním zařazení bez řádku třídy (třída v něm v pravidle nebyla).
        gap = bool(first) and any(v.date > first.date and v not in in_rule for v in earlier)
        spec = rule._engine_rule(start, self.date)
        count = len(self.fund_id.class_ids)
        shift = {"base": Decimal(0)}

        def full(current):
            result = engine.average_fee(spec, start, self.date, [value for _day, value in points], current,
                                        booked=booked, shift=shift["base"], classes_count=count)
            result.pop("exact_move")
            return {"per_class": True, "start": start, "points": [[day, value] for day, value in points],
                    "today": current, "base_step": rule.base_step, **result}

        return {"base": {"scope": "class", "class": fund_class.id, "step": int(rule.base_step)},
                "amount": lambda current: full(current)["exact"] - booked, "full": full, "shift": shift,
                "gap": gap}

    def _performance_item(self, rule, fund_class, context):
        """Výkonnostní odměna třídy: základ hodnota třídy po kroku 1, 2 nebo 4, nikdy po sobě samé.

        Od poslední krystalizace se k hodnotě třídy přičte, co třída nesla (ZJ-12 B.3): po kroku 1 úplaty a daň, po kroku 2
        daň, po kroku 4 nic. Naběhlá odměna se přičítá zpět; částka pro dopočet je přesný doplatek proti naběhlé odměně.
        """
        version = rule._version_at(self.date)
        row = context[fund_class]
        reference, hwm, accrued, base_date = self._performance_state(rule, fund_class, row, version)
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
        stages = {"1": (engine.STAGE_FEE, engine.STAGE_TAX), "2": (engine.STAGE_TAX,)}.get(rule.base_step, ())
        borne = self._borne_since(fund_class, base_date, version.perf_measure, row["units"], stages)
        added_fees = borne.get(engine.STAGE_FEE, Decimal(0))
        added_tax = borne.get(engine.STAGE_TAX, Decimal(0))

        shift = {"base": Decimal(0)}

        def full(value):
            gross = value + accrued + added_fees + added_tax + shift["base"]
            result = engine.performance_fee(spec, base_date, self.date, gross, units=row["units"], flows=flows,
                                            accrued=accrued)
            return {"gross": gross, "base_date": base_date, "base_step": rule.base_step, "added_fees": added_fees,
                    "added_tax": added_tax, **result}

        state = {"reference": reference, "hwm": hwm, "base_date": base_date, "measure": version.perf_measure}
        return {"base": {"scope": "class", "class": fund_class.id, "step": int(rule.base_step)},
                "amount": lambda value: full(value)["exact"] - accrued, "full": full, "state": state, "shift": shift}

    def _tax_item(self, rule):
        """Očekávaná daň (ZJ-12 B.4, B.5): vstupy dopočtu z knihy po kroku 1 a z dřívějších ocenění od 1. 1.

        Výsledek od 1. 1. bez účtu daně; náklady dřívějších ocenění, které podle volby základ nesnižují (krok 1:
        úplaty a odměna, krok 2: odměna), se přičtou zpět. Specifické položky tříd = výsledkové řádky s třídou od 1. 1.
        (úplaty a odměna tříd, opravy, zajištění) bez nezapočitatelných. Daňový efekt minulého ocenění v roce (pro
        přírůstkový přesun) je v detailu jeho řádku daně (`effect`, `effect_total`).
        """
        version = rule._version_at(self.date)
        step = int(rule.base_step)
        year_start = date_type(self.date.year, 1, 1)
        tax_account = self.env["investra.account.role"].account_for(self.company_id, "expense_tax")
        pnl = [("date", ">=", year_start), ("account_id", "!=", tax_account.id),
               "|", ("account_id.account_type", "=like", "income%"), ("account_id.account_type", "=like", "expense%")]
        result = -self._sum(*pnl)
        specific = {c.id: Decimal(0) for c in self.fund_id.class_ids}
        groups = self.env["account.move.line"].sudo()._read_group(
            self._line_domain(*pnl, ("investra_class_id", "in", self.fund_id.class_ids.ids)),
            groupby=["investra_class_id"], aggregates=["balance:sum"],
        )
        for fund_class, balance in groups:
            specific[fund_class.id] = d(balance).quantize(engine.CENT, rounding=ROUND_HALF_UP)
        for item in self._earlier_fee_items(self._year_start()):
            if item["stage"] == engine.STAGE_TAX:
                continue
            if item["stage"] > step:
                result += item["expense"]
                if item["payer"] in specific:
                    specific[item["payer"]] -= item["expense"]
        previous, previous_total = self._previous_tax_effect(rule)
        booked = self._sum(("date", ">=", year_start), ("account_id", "=", tax_account.id))
        transfers_booked, transfers_exact = self._tax_transfer_history(rule)
        return {"stage": engine.STAGE_TAX, "payer": None, "tax": {
            "rate": d(version.rate), "step": step, "result": result, "booked": booked, "specific": specific,
            "previous_effect": previous, "previous_effect_total": previous_total,
            "transfers_booked": transfers_booked, "transfers_exact": transfers_exact,
        }}

    def _tax_transfer_history(self, rule):
        """Přesuny daňového efektu od 1. 1. (rozhodnutí 2026-11-19): zaúčtované po třídách a přesný součet.

        Zaúčtované = součet `transfers` řádků daně dřívějších ocenění v roce. Přesný (nezaokrouhlený) součet je
        `transfers_exact` posledního řádku, který ho má; starší řádky ho nemají, pak přesný součet = zaúčtované přesuny.
        """
        booked, exact = {}, None
        for valuation in self._earlier_valuations(self._year_start()):
            for line in valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule):
                detail = json.loads(line.detail or "{}")
                for key, value in (detail.get("transfers") or {}).items():
                    booked[int(key)] = booked.get(int(key), Decimal(0)) + d(value)
                if "transfers_exact" in detail:
                    exact = {int(k): d(v) for k, v in detail["transfers_exact"].items()}
        return booked, (dict(booked) if exact is None else exact)

    def _previous_tax_effect(self, rule):
        """Daňový efekt tříd posledního dřívějšího ocenění v roce ({třída: e × spec_c}, e × Σ spec), ZJ-12 B.5.

        Řádky z kroku 3 před přírůstkovým přesunem efekt neukládají: dopočte se z `effective_rate` a `specific`
        (zaokrouhlené na haléře, rozdíl nejvýš e × 0,005 na třídu). Řádek bez efektivní sazby (před krokem 3) = 0.
        """
        for valuation in reversed(self._earlier_valuations(self._year_start())):
            line = valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)[:1]
            if not line:
                continue
            detail = json.loads(line.detail or "{}")
            if "effect" in detail:
                return ({int(k): d(v) for k, v in detail["effect"].items()}, d(detail["effect_total"]))
            rate = d(detail.get("effective_rate") or 0)
            effect = {int(k): rate * d(v) for k, v in (detail.get("specific") or {}).items()}
            return effect, sum(effect.values(), Decimal(0))
        return {}, Decimal(0)

    def _manual_item(self, entry, values):
        """Ručně doložená úplata nebo oprava (ZJ-03, ZJ-11, ZJ-12 B.7): pevná částka v měně fondu.

        Ručně doložená úplata a oprava úplaty jsou krok 2, oprava odměny krok 3 (plátce třída), oprava daně krok 4
        (plátce fond; do základu daně nevstupuje, je to daň). `corrects` = klíč opraveného pravidla v dopočtu.
        """
        currency = entry.currency_id or self.fund_id.currency_id
        original = engine.money(d(entry.amount))
        rate = self._fx(currency)
        item = {"key": ("manual", entry.id), "stage": engine.STAGE_FEE, "payer": entry.class_id.id or None,
                "base": None, "amount": engine.money(original * rate), "kind": "manual", "entry": entry,
                "original": original, "rate": rate, "currency": currency}
        rule = entry.corrects_rule_id
        if rule:
            item["corrects"] = self._correction_key(rule, entry.class_id.id or None)
            if rule.kind == "tax":
                item.update(stage=engine.STAGE_TAX, payer=None)
                return item
            item.update(self._recipients(rule, values))
            if rule.kind == "performance":
                item["stage"] = engine.STAGE_PERFORMANCE
        return item

    @staticmethod
    def _correction_key(rule, class_id):
        """Klíč položky pravidla v dopočtu, ke které se oprava vztahuje."""
        if rule.kind == "tax":
            return ("tax", rule.id)
        if rule.kind == "performance":
            return ("perf", rule.id, class_id)
        # Průměrný FK bez tříd je úplata celého fondu; s třídami (ZJ-14) položka za každou třídu.
        return ("fee", rule.id, None if rule.base_source == "average_fk" and not rule.class_ids else class_id)

    def _carried_corrections(self, rule, fund_class, since, target="amount"):
        """Převzaté opravy částky (ZJ-12 B.7): opravy s platností „do konce období“ z dřívějších ocenění po dni `since`.

        Odměna od poslední krystalizace, daň od 1. 1.; časově rozlišená úplata se nepřebírá (oprava je trvalá).
        Ukončení (`ended_id`) je oprava o −částku s toutéž platností, proto se v součtu s ukončenou vyruší.
        """
        earlier = self._earlier_valuations(since)
        if not earlier:
            return self.env["investra.valuation.external"]
        return self.env["investra.valuation.external"].sudo().search([
            ("valuation_id", "in", earlier.ids), ("corrects_rule_id", "=", rule.id),
            ("correction_target", "=", target), ("validity", "=", "period"),
            ("class_id", "=", fund_class.id if fund_class else False),
        ], order="id")

    def _apply_base_correction(self, item, base_entries):
        """Oprava základu (ZJ-12 B.7): nové opravy tohoto ocenění a převzaté „do konce období“ se přičtou k základu.

        Daň: k základu (ruční úprava ZJ-07 bod 2), převzatá od 1. 1. Průměrný FK: k celoročnímu průměru, převzatá od 1. 1.
        Odměna: k hodnotě třídy, převzatá od krystalizace. Úplata ze stavu k datu (FK, kapitál třídy, aktiva): jen toto
        ocenění. Oprava základu nepevní částku: pravidlo se z opraveného základu spočítá (i v průchodu „Vypočteno“,
        kde jsou vynechané jen opravy částky).
        """
        if item["kind"] not in ("periodic", "performance", "tax"):
            return
        rule, fund_class = item["rule"], item.get("fund_class")
        new = base_entries.filtered(
            lambda e: self._correction_key(e.corrects_rule_id, e.class_id.id or None) == item["key"])
        if item["kind"] == "tax" or rule.base_source == "average_fk":
            # Průměrný FK po třídách (ZJ-14): oprava základu třídy upravuje průměr třídy, převzatá do konce roku.
            carried = self._carried_corrections(rule, fund_class, self._year_start(), target="base")
        elif item["kind"] == "performance":
            carried = self._carried_corrections(rule, fund_class, item["state"]["base_date"], target="base")
        else:
            carried = self.env["investra.valuation.external"]
        entries = carried | new
        if not entries:
            return
        total = sum((engine.money(d(e.amount)) for e in entries), Decimal(0))
        item.update(base_entries=entries, base_correction=total)
        if item["kind"] == "tax":
            item["tax"]["base_correction"] = total
        else:
            item["shift"]["base"] = total

    def _check_corrected_rules(self):
        """Stop (ZJ-12 B.8): oprava odkazuje na pravidlo, které mezitím změnilo druh nebo třídy nebo je archivované."""
        for entry in self.external_fee_ids.filtered("corrects_rule_id"):
            rule = entry.corrects_rule_id
            if not rule.active:
                raise UserError(self.env._(
                    "Oprava %s: pravidlo je archivované. Opravu smažte, nebo pravidlo znovu aktivujte.", rule.name))
            try:
                entry._check_correction(self.fund_id)
            except ValidationError as error:
                raise UserError(self.env._(
                    "Oprava %(rule)s už neodpovídá pravidlu (změna druhu nebo tříd): %(error)s",
                    rule=rule.name, error=error.args[0])) from error

    def _capture_computed(self, items, corrections, first):
        """Snímek „Vypočteno“ u oprav částky zadaných v tomto ocenění a kontrola změny (ZJ-12 B.8, D4).

        Vypočteno = průchod bez oprav částky + převzaté opravy (= částka řádku pravidla bez nových oprav). Snímek bez
        tlačítka Opravit (`computed_captured` nevyplněné) se pořídí při prvním výpočtu. Liší-li se nový výpočet od snímku,
        ocenění se zastaví; uživatel zvolí „Ponechat rozdíl“ nebo „Ponechat výsledek“ (`computed_now` = nynější hodnota).
        Převzaté opravy dřívějších ocenění se nekontrolují.
        """
        targets = {item["key"]: item for item in items}
        changed = []
        for item in corrections:
            entry, target = item["entry"], targets[item["corrects"]]
            computed = engine.money(first["amounts"][item["corrects"]] + target.get("carried", Decimal(0)))
            values = {"computed_now": float(computed)}
            if not entry.computed_captured:
                values.update(computed_at_entry=float(computed), computed_captured=True)
            entry.sudo().write(values)
            if engine.money(d(entry.computed_at_entry)) != computed:
                changed.append(self.env._(
                    "%(rule)s: při opravě %(then)s, nyní %(now)s; oprava %(amount)s",
                    rule=entry.corrects_rule_id.name, then=f"{entry.computed_at_entry:.2f}", now=f"{computed:.2f}",
                    amount=f"{entry.amount:.2f}"))
        self._check("correction_changed", self.env._("Vypočtená částka opravených úplat se od zadání opravy nezměnila"),
                    not changed, "; ".join(changed))

    def _previous_valuation(self):
        return self.search([
            ("fund_id", "=", self.fund_id.id), ("date", "<", self.date),
            ("state", "in", ("posted", "sent", "confirmed", "published")),
        ], order="date desc, version desc", limit=1)

    def _check_previous_corrections(self):
        """Upozornění (ZJ-12 B.7, B.8): opravy minulého ocenění, které v tomto už neplatí.

        Oprava základu úplaty ze stavu k datu platí jen pro své ocenění; oprava odměny nebo daně „jen toto ocenění“ se
        tímto oceněním vrací na vypočtený stav.
        """
        previous = self._previous_valuation()
        corrections = previous.external_fee_ids.filtered("corrects_rule_id")
        base = corrections.filtered(
            lambda e: e.correction_target == "base" and e.corrects_rule_id.kind == "periodic"
            and e.corrects_rule_id.base_source != "average_fk")
        names = ", ".join(sorted(set(base.mapped("corrects_rule_id.name"))))
        self._check("base_correction_ended", self.env._("Oprava základu z minulého ocenění skončila"), not base,
                    self.env._("Minulé ocenění mělo opravu základu u pravidla %s.", names) if base else "",
                    severity="warning")
        once = corrections.filtered(lambda e: e.validity == "valuation")
        names = ", ".join(sorted(set(once.mapped("corrects_rule_id.name"))))
        self._check("correction_once_ended", self.env._("Opravy „jen toto ocenění“ z minulého ocenění skončily"),
                    not once, self.env._("Skončila oprava „jen toto ocenění“ u pravidla %s.", names) if once else "",
                    severity="warning")

    def _check_carried(self, items):
        """Upozornění (ZJ-12 B.8): ocenění obsahuje převzaté opravy (n); ukončené dvojice se nepočítají."""
        carried = self.env["investra.valuation.external"]
        for item in items:
            carried |= item.get("carried_entries") or carried.browse()
            carried |= (item.get("base_entries") or carried.browse()).filtered(lambda e: e.valuation_id != self)
        ending = self.external_fee_ids.filtered("ended_id")
        ended = carried.mapped("ended_id") | ending.mapped("ended_id")
        live = carried.filtered(lambda e: e not in ended and not (e.ended_id and e.ended_id in carried))
        detail = "; ".join(f"{e.corrects_rule_id.name} {e.class_id.code or ''} {e.amount:.2f} ({e.valuation_id.display_name})"
                           for e in live)
        self._check("carried_corrections", self.env._("Obsahuje převzaté opravy (%s)", len(live)), not live, detail,
                    severity="warning")

    def end_correction(self, entry, note):
        """Ukončí převzatou opravu (ZJ-12 B.7): nová oprava o −její částku s povinnou poznámkou a odkazem `ended_id`.

        Tlačítko „Ukončit opravu“ u převzatých oprav přidá krok 5; kontroly ukončení jsou v `_check_ending`.
        """
        self.ensure_one()
        if not (note or "").strip():
            raise UserError(self.env._("Ukončení opravy musí mít poznámku."))
        self.write({"external_fee_ids": [(0, 0, {
            "corrects_rule_id": entry.corrects_rule_id.id, "class_id": entry.class_id.id,
            "correction_target": entry.correction_target, "validity": "period", "amount": -entry.amount,
            "currency_id": entry.currency_id.id, "note": note, "ended_id": entry.id,
        })]})
        return self.external_fee_ids.filtered(lambda row: row.ended_id == entry)

    def _solve_fees(self, classes, items, pinned=None):
        try:
            return engine.solve_fees(classes, items, pinned)
        except ValueError as error:
            raise UserError(self.env._("Ocenění %(name)s: %(error)s", name=self.display_name, error=error)) from error

    def _apply_fees(self, rules, context):
        """Společný dopočet (ZJ-12 B.1): všechny částky z engine.solve_fees, zaúčtování až po ustálení.

        Opravy (B.7) ve dvou průchodech: bez oprav = „Vypočteno“; pak má opravené pravidlo pevnou vypočtenou částku,
        oprava se přidá jako samostatná položka a ostatní pravidla se dopočtou k ní. Výsledek = vypočteno + oprava.
        """
        values = {c: self._class_value(c, context) for c in context}
        classes = {c.id: {"value": values[c], "ratio": context[c]["ratio"]} for c in context}
        items = []
        gaps = []
        for rule in rules.filtered(lambda r: r.kind == "periodic"):
            if rule.base_source == "average_fk" and rule.class_ids:
                # ZJ-14: průměrný FK po třídách, plátce je třída (příjemci, daňový efekt a přemostění jako úplata třídy).
                for fund_class in rule.class_ids:
                    average = self._average_class_item(rule, fund_class)
                    if average is None:
                        continue
                    if average.pop("gap"):
                        gaps.append((fund_class.code, rule.name))
                    items.append({"key": ("fee", rule.id, fund_class.id), "stage": engine.STAGE_FEE,
                                  "payer": fund_class.id, "kind": "periodic", "rule": rule, "fund_class": fund_class,
                                  **self._recipients(rule, values), **average})
                continue
            if rule.base_source == "average_fk":
                # Rozhodnutí 2026-11-19: příjemci i u průměrného FK, aby dopočet počítal stejně jako doklad (`_book_fee`).
                items.append({"key": ("fee", rule.id, None), "stage": engine.STAGE_FEE, "payer": None,
                              "kind": "periodic", "rule": rule, "fund_class": None,
                              **self._recipients(rule, values), **self._average_item(rule)})
                continue
            for fund_class in rule.class_ids or [None]:
                class_id = fund_class.id if fund_class else None
                items.append({"key": ("fee", rule.id, class_id), "stage": engine.STAGE_FEE, "payer": class_id,
                              "kind": "periodic", "rule": rule, "fund_class": fund_class,
                              **self._recipients(rule, values), **self._periodic_item(rule, fund_class)})
        base_entries = self.external_fee_ids.filtered(
            lambda e: e.corrects_rule_id and e.correction_target == "base")
        manual = [self._manual_item(entry, values) for entry in self.external_fee_ids - base_entries]
        items += manual
        for rule in rules.filtered(lambda r: r.kind == "performance"):
            for fund_class in rule.class_ids:
                items.append({"key": ("perf", rule.id, fund_class.id), "stage": engine.STAGE_PERFORMANCE,
                              "payer": fund_class.id, "kind": "performance", "rule": rule, "fund_class": fund_class,
                              **self._recipients(rule, values), **self._performance_item(rule, fund_class, context)})
        for rule in rules.filtered(lambda r: r.kind == "tax"):
            items.append({"key": ("tax", rule.id), "kind": "tax", "rule": rule, **self._tax_item(rule)})
        for item in items:
            self._apply_base_correction(item, base_entries)
        for item in items:
            if item["kind"] == "performance":
                carried = self._carried_corrections(item["rule"], item["fund_class"], item["state"]["base_date"])
            elif item["kind"] == "tax":
                carried = self._carried_corrections(item["rule"], None, self._year_start())
            else:
                continue
            item["carried_entries"] = carried
            item["carried"] = sum((engine.money(d(e.amount)) for e in carried), Decimal(0))
        self._check_corrected_rules()
        first = self._solve_fees(classes, [item for item in items if not item.get("corrects")])
        solved, pinned = first, {}
        corrections = [item for item in manual if item.get("corrects")]
        for item in corrections:
            if item["corrects"] not in first["amounts"]:
                raise UserError(self.env._(
                    "Oprava %(rule)s: pravidlo se v tomto ocenění nepočítá pro tuto třídu.",
                    rule=item["entry"].corrects_rule_id.name,
                ))
            pinned[item["corrects"]] = first["amounts"][item["corrects"]]
        self._capture_computed(items, corrections, first)
        for item in items:
            # Převzaté opravy: opravené pravidlo má pevnou částku vypočteno + převzaté (B.7).
            if item.get("carried_entries"):
                pinned[item["key"]] = first["amounts"][item["key"]] + item["carried"]
        for item in corrections:
            target = next(i for i in items if i["key"] == item["corrects"])
            target["new_corrections"] = target.get("new_corrections", Decimal(0)) + item["amount"]
        if pinned:
            solved = self._solve_fees(classes, items, pinned)
        residual = solved["residual"]
        self._check("fee_consistency", self.env._("Společný dopočet úplat je konzistentní"),
                    residual <= Decimal("1e-10"), f"kroků {solved['steps']}, relativní zbytek {float(residual):.1e}")
        ratios = {c.id: context[c]["ratio"] for c in context}
        for entry in base_entries:
            self._fee_record(None, Decimal(0), entry.class_id, {
                "manual": True, "corrects": entry.corrects_rule_id.name, "corrects_kind": entry.corrects_rule_id.kind,
                "target": "base", "base_correction": engine.money(d(entry.amount)), "validity": entry.validity,
                "note": entry.note, **({"ends": entry.ended_id.id} if entry.ended_id else {}),
            }, manual=entry)
        self._check_previous_corrections()
        self._check_carried(items)
        if any(r.kind == "periodic" and r.base_source == "average_fk" and r.class_ids for r in rules):
            self._check("average_class_gap", self.env._("Třídy průměrného FK jsou v pravidle bez přerušení"), not gaps,
                        "; ".join(self.env._("Třída %(cls)s byla v pravidle %(rule)s letos přerušeně", cls=c, rule=r)
                                  for c, r in gaps), severity="warning")
        self._check_version_copies()
        negative = []
        for item in items:
            # Opravené pravidlo: částka i základ z průchodu bez oprav („Vypočteno“).
            source = first if item["key"] in pinned else solved
            if item["kind"] == "tax":
                result = self._book_tax(item, solved["tax"], first["tax"] if item["key"] in pinned else None)
            elif item["kind"] == "manual":
                self._book_manual(item, ratios, values)
                continue
            else:
                result = self._book_rule_fee(
                    item, source["bases"].get(item["key"]), item["key"] in pinned, ratios, values, context)
            if ("new_corrections" in item or item.get("carried_entries")) and engine.money(result) < 0:
                fund_class = item.get("fund_class")
                negative.append((" ".join(filter(None, [item["rule"].name, fund_class and fund_class.code])),
                                 engine.money(result)))
        self._check_negative_corrections(negative)

    def _check_negative_corrections(self, negative):
        """Upozornění (rozhodnutí 2026-11-19): výsledek opravy je záporný; ocenění nezastaví.

        Výsledek = stav pravidla po opravách částky (nových i převzatých): u úplaty částka řádku pravidla + opravy,
        u výkonnostní odměny naběhlá odměna, u daně požadovaná daň. Odměna a daň se porovnávají se stavem, ne s pohybem,
        protože záporný pohyb (rozpuštění naběhlé odměny, vrácení daně) je běžný.
        """
        names = ", ".join(label for label, _value in negative)
        name = (self.env._("Výsledek opravy %s je záporný", names) if negative
                else self.env._("Výsledek oprav úplat není záporný"))
        self._check("correction_negative", name, not negative,
                    "; ".join(f"{label}: {value:.2f}" for label, value in negative), severity="warning")

    def _effect_detail(self, item, amount, ratios, values):
        """Náklad mimo fond a částky nesené třídami (pro přičtení úplat od data v dalších oceněních, B.3 a B.4).

        Podíl příjemcům se dělí stejnou funkcí jako na dokladu (`money(částka × podíl)`, `_recipient_parts`, zbytkový haléř
        třídě s největší vahou), aby rozpad odpovídal zaúčtování (revize CP-2026-11-19, nález 1).
        """
        rule = item.get("rule") or (item["entry"].corrects_rule_id if item.get("entry") else None)
        payer = item.get("payer")
        borne = {key: (amount if payer == key else (rho * amount if payer is None else Decimal(0)))
                 for key, rho in ratios.items()}
        to_classes = Decimal(0)
        if rule and item.get("recipients"):
            to_classes = engine.money(amount * d(item["share"]))
            if to_classes:
                for fund_class, part in self._recipient_parts(rule, to_classes, values).items():
                    borne[fund_class.id] = borne.get(fund_class.id, Decimal(0)) - part
        return {"expense": engine.money(amount - to_classes),
                "borne": {str(key): str(engine.money(value)) for key, value in borne.items() if engine.money(value)}}

    def _book_rule_fee(self, item, base, corrected, ratios, values, context):
        rule, fund_class = item["rule"], item["fund_class"]
        full = item["full"](base)
        carried = item.get("carried", Decimal(0))
        amount = full["move"] + carried
        detail = {**full, **self._effect_detail(item, amount, ratios, values)}
        if corrected:
            detail["corrected"] = True
        if item.get("base_entries"):
            detail.update(base_correction=item["base_correction"], base_correction_ids=item["base_entries"].ids)
        if item.get("carried_entries"):
            # Vypočteno (bez oprav) a převzaté opravy; řádek pravidla zaúčtuje oboje, nové opravy mají vlastní řádky.
            detail.update(computed=full["move"], carried=carried, carried_ids=item["carried_entries"].ids)
        self._fee_record(rule, amount, fund_class, detail)
        if item["kind"] != "performance":
            self._book_fee(rule, amount, fund_class, weights=values)
            return amount + item.get("new_corrections", Decimal(0))
        self._book_fee(rule, amount, fund_class, payable="performance_payable", weights=values)
        state = item["state"]
        # Naběhlá odměna včetně oprav (B.7): „jen toto ocenění“ se dalším oceněním vrátí, „do konce období“ drží
        # převzetí; při krystalizaci je oprava součástí splatné odměny.
        accrued = full["required"] + carried + item.get("new_corrections", Decimal(0))
        context[fund_class]["perf"] = {
            "reference": state["reference"], "hwm": state["hwm"], "accrued": accrued,
            "base_date": state["base_date"], "crystallise": self._is_crystallisation(rule) and accrued > 0,
            "measure": state["measure"],
        }
        if rule.cover_class_id and full["shortfall"] > 0:
            available = max(self._class_value(rule.cover_class_id, context), Decimal(0))
            covered = min(full["shortfall"], engine.money(available))
            lines = self._transfer_lines(rule.cover_class_id, {fund_class: covered})
            self._add_event(f"cover:{rule.id}:{fund_class.id}", f"Krytí {rule.name}", lines)
            self._fee_record(rule, -covered, fund_class, {"covered_by": rule.cover_class_id.code})
        return accrued

    def _book_manual(self, item, ratios, values):
        """Ručně doložená úplata (ZJ-03) na zvolený nákladový účet, nebo oprava úplaty (ZJ-11) jako úplata pravidla.

        Třída prázdná = společný náklad celého fondu (dělí se poměrem), jinak jen dané třídě. Cizí měna se přepočte
        kurzem k datu ocenění ze zdroje kurzů fondu; řádky nesou i původní měnu, aby závazek přecenilo FX přecenění.
        Oprava se účtuje přes `_book_fee` (nákladová role pravidla, podíl příjemcům z tříd); jen v měně fondu. Řádek
        rozpisu nemá pravidlo, proto ho průměrný FK v dalším ocenění neodečítá a oprava platí trvale.
        """
        entry, amount, original, currency = item["entry"], item["amount"], item["original"], item["currency"]
        effect = self._effect_detail(item, amount, ratios, values)
        rule = entry.corrects_rule_id
        if rule:
            self._fee_record(None, amount, entry.class_id, {
                "manual": True, "corrects": rule.name, "corrects_kind": rule.kind, "validity": entry.validity,
                "note": entry.note, "currency": currency.name, **effect,
                **({"ends": entry.ended_id.id} if entry.ended_id else {}),
            }, manual=entry)
            name = {"tax": self.env._("Oprava daně %s", rule.name),
                    "performance": self.env._("Oprava odměny %s", rule.name)}.get(
                        rule.kind, self.env._("Oprava úplaty %s", rule.name))
            if rule.kind == "tax":
                self._add_event(f"tax:{rule.id}:manual:{entry.id}", name, [
                    {"role": "expense_tax", "amount": amount, "movement_type": "fee"},
                    {"role": "tax_payable", "amount": -amount, "movement_type": "fee"},
                ])
                return
            payable = "performance_payable" if rule.kind == "performance" else "fee_payable"
            self._book_fee(rule, amount, entry.class_id or None, kind_suffix=f":manual:{entry.id}", name=name,
                           payable=payable, weights=values)
            return
        class_id = entry.class_id.id or False
        foreign = {} if currency == self.fund_id.currency_id else {"currency_id": currency.id}
        lines = [
            {"role": "expense_other", "amount": amount, "class_id": class_id, "movement_type": "fee",
             "extra": {"account_id": entry.account_id.id},
             **({"amount_currency": original, **foreign} if foreign else {})},
            {"role": "fee_payable", "amount": -amount, "class_id": class_id, "movement_type": "fee",
             **({"amount_currency": -original, **foreign} if foreign else {})},
        ]
        self._fee_record(None, amount, entry.class_id, {
            "manual": True, "note": entry.note, "account": entry.account_id.code,
            "currency": currency.name, "amount_currency": str(original), "rate": str(item["rate"]), **effect,
        }, manual=entry)
        self._add_event(f"fee:manual:{entry.id}", self.env._("Ručně doložená úplata"), lines)

    def _book_tax(self, item, tax, computed=None):
        """Daň jedním dokladem (ZJ-12 B.4): doplatek do požadované daně a přesun daňového efektu tříd (B.5).

        Přesuny se dorovnávají proti přesnému součtu od 1. 1. (`transfers_exact`, rozhodnutí 2026-11-19); rozdíl, aby byl
        součet v ocenění nulový, nese přesun s největší absolutní hodnotou.
        Doúčtování po výkonnostní odměně (`tax:<id>:perf`) zaniká, odměnu a daň počítá společný dopočet.
        Opravená daň (`computed` = průchod bez oprav, B.7): doplatek z vypočtené daně + převzaté opravy; nové opravy
        mají vlastní doklady. Přesuny daňového efektu jsou z konečného stavu (oprava daně do nich nevstupuje).
        """
        rule, spec = item["rule"], item["tax"]
        carried = item.get("carried", Decimal(0))
        required = engine.money((computed or tax)["required"])
        move = required - spec["booked"] + carried
        # Dorovnání mezi oceněními (rozhodnutí 2026-11-19): přesun = money(přesný součet od 1. 1.) − už zaúčtované přesuny
        # třídy od 1. 1.; uvnitř ocenění zbytek do nuly nese přesun s největší absolutní hodnotou.
        booked_transfers, previous_exact = spec.get("transfers_booked") or {}, spec.get("transfers_exact") or {}
        exact = {key: previous_exact.get(key, Decimal(0)) + value for key, value in tax["transfers"].items()}
        for key, value in previous_exact.items():
            exact.setdefault(key, value)
        transfers = {key: engine.money(value) - booked_transfers.get(key, Decimal(0)) for key, value in exact.items()}
        rounding = -sum(transfers.values(), Decimal(0))
        if rounding and transfers:
            transfers[max(sorted(transfers), key=lambda key: abs(transfers[key]))] += rounding
        transfers = {key: value for key, value in transfers.items() if value}
        self._fee_record(rule, move, None, {
            "base": tax["base"], "base_step": rule.base_step, "required": required, "booked": spec["booked"],
            "result": spec["result"], "specific": {str(k): str(engine.money(v)) for k, v in tax["specific"].items()},
            "effective_rate": tax["effective_rate"], "transfers": {str(k): str(v) for k, v in transfers.items()},
            "transfers_exact": {str(k): str(v) for k, v in exact.items()},
            "effect": {str(k): str(v) for k, v in tax["effect"].items()}, "effect_total": str(tax["effect_total"]),
            **({"corrected": True} if computed else {}),
            **({"base_correction": item["base_correction"], "base_correction_ids": item["base_entries"].ids}
               if item.get("base_entries") else {}),
            **({"computed": required - spec["booked"], "carried": carried,
                "carried_ids": item["carried_entries"].ids} if item.get("carried_entries") else {}),
        })
        lines = [
            {"role": "expense_tax", "amount": move, "movement_type": "fee"},
            {"role": "tax_payable", "amount": -move, "movement_type": "fee"},
        ] + [{"role": "internal_clearing", "amount": value, "class_id": key, "movement_type": "class_transfer"}
             for key, value in transfers.items()]
        self._add_event(f"tax:{rule.id}", rule.name, lines)
        # Požadovaná daň po opravách (pro upozornění na záporný výsledek opravy).
        return required + carried + item.get("new_corrections", Decimal(0))

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
        specifická změna se dál dělí na úplaty, výkonnostní odměnu, přesun podle pořadí nároků, daňový efekt a ostatní.
        Výsledek ocenění se tím nemění, jen se ukládá rozpad, který výpočet zná.
        """
        previous = row["previous"]
        same_currency = fund_class.currency_id == self.fund_id.currency_id
        fees = self.fee_line_ids.filtered(lambda line: line.class_id == fund_class)

        def kind(line):
            # ZJ-12 krok 6c (b): oprava odměny (řádek bez pravidla) patří do Výkonnostní odměny, ne do Úplat třídy.
            return (line.rule_id or line.external_id.corrects_rule_id).kind

        performance = -sum((d(l.amount) for l in fees if kind(l) == "performance"), Decimal(0))
        fee = -sum((d(l.amount) for l in fees if kind(l) != "performance"), Decimal(0))
        allocation = d(row.get("allocation"))
        # ZJ-12 krok 6c: přesun daňového efektu (vnitřní zúčtování z `_book_tax`), tytéž zaokrouhlené částky jako na dokladu.
        # Starší ocenění `transfers` nemají, efekt pak zůstává v Ostatní specifické.
        tax_effect = Decimal(0)
        for line in self.fee_line_ids.filtered(lambda l: l.rule_id.kind == "tax"):
            transfers = json.loads(line.detail or "{}").get("transfers") or {}
            tax_effect += d(transfers.get(str(fund_class.id), 0))
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
            "tax_effect_amount": tax_effect,
            "other_amount": delta - fee - performance - allocation - tax_effect,
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
            specific_total = (b["fee_amount"] + b["performance_amount"] + b["allocation_amount"] + b["tax_effect_amount"]
                              + b["other_amount"])
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
            record._log_step("submitted", record._corrections_summary() or False)
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

    def _previous_version(self):
        """Vrácená nebo stornovaná verze, ze které tato verze vznikla (ZJ-12 B.10)."""
        self.ensure_one()
        return self.search([("fund_id", "=", self.fund_id.id), ("date", "=", self.date),
                            ("version", "=", self.version - 1), ("state", "in", ("returned", "reversed"))], limit=1)

    def _copy_fields(self, line):
        return {
            "class_id": line.class_id.id, "amount": line.amount, "currency_id": line.currency_id.id,
            "account_id": line.account_id.id, "note": line.note, "corrects_rule_id": line.corrects_rule_id.id,
            "correction_target": line.correction_target, "validity": line.validity,
            "computed_at_entry": line.computed_at_entry, "computed_captured": line.computed_captured,
            "ended_id": line.ended_id.id, "origin_id": line.id,
        }

    def action_copy_from_version(self):
        """Převzít z verze n (ZJ-12 B.10): zkopíruje ruční úpravy a opravy zadané ve vrácené verzi (ne převzaté opravy
        dřívějších ocenění, ty vzniknou výpočtem znovu), s novou kopií přílohy patřící této verzi a `origin_id`.
        Už převzaté řádky se nekopírují znovu; nechtěné se v návrhu smažou."""
        self.ensure_one()
        self._require_state("draft", "computed")
        previous = self._previous_version()
        if not previous:
            raise UserError(self.env._("Ocenění nemá vrácenou ani stornovanou předchozí verzi."))
        copied = self.external_fee_ids.mapped("origin_id")
        commands = []
        for line in previous.external_fee_ids - copied:
            values = self._copy_fields(line)
            if line.attachment_id:
                values["attachment_id"] = line.attachment_id.sudo().copy(
                    {"res_model": "investra.valuation", "res_id": self.id}).id
            commands.append((0, 0, values))
        if commands:
            self.write({"external_fee_ids": commands})
        return len(commands)

    def _check_version_copies(self):
        """Upozornění (ZJ-12 B.8): předchozí verze měla ruční úpravy (n), které v této verzi nejsou."""
        previous = self._previous_version() if self.version > 1 else self.browse()
        missing = previous.external_fee_ids - self.external_fee_ids.mapped("origin_id")
        self._check("version_entries_missing",
                    self.env._("Předchozí verze měla ruční úpravy (%s), které v této verzi nejsou", len(missing)),
                    not missing, "; ".join(f"{l.corrects_rule_id.name or l.note} {l.amount:.2f}" for l in missing),
                    severity="warning")

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
        # Odchylka: nové ocenění k datu, ke kterému jsou jen vrácené nebo stornované verze (např. po zrušení návrhu),
        # dostane další číslo verze; dřív dostalo 1 a narazilo na unique(fond, datum, verze). Aktivní verzi to nepřebije.
        for vals in vals_list:
            if "version" not in vals and vals.get("fund_id") and vals.get("date"):
                existing = self.sudo().search([("fund_id", "=", vals["fund_id"]), ("date", "=", vals["date"])])
                if existing and all(v.state in ("returned", "reversed") for v in existing):
                    vals["version"] = max(existing.mapped("version")) + 1
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
    allocation_amount = fields.Float(
        digits=(20, 2), string="Přesun podle pořadí nároků",
        help="Jen u fondu se schématem rozdělení „pořadí nároků“: rozdíl mezi výsledkem rozděleným podle pořadí nároků "
             "a podle alokačního poměru, zaúčtovaný jako přesun mezi třídami přes vnitřní zúčtování (FK fondu nemění). "
             "+ třída dostala víc, než by jí patřilo podle poměru; − méně.")
    tax_effect_amount = fields.Float(
        digits=(20, 2), string="Daňový efekt specifických položek",
        help="Přesun daňového efektu položek výsledku třídy přes vnitřní zúčtování (+ zvyšuje kapitál třídy).")
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
    # ZJ-11: oprava se řadí hned pod původní úplatu (skupina = pravidlo, oprava za původními řádky), ruční úplaty na konec.
    _order = "valuation_id, group_key, is_correction, id"

    valuation_id = fields.Many2one("investra.valuation", required=True, ondelete="cascade", index=True, string="Ocenění")
    company_id = fields.Many2one(related="valuation_id.company_id", store=True, index=True)
    # Bez pravidla je to ručně doložená úplata (ZJ-03); název ji pak popíše poznámkou.
    rule_id = fields.Many2one("investra.fee.rule", ondelete="restrict", string="Pravidlo")
    external_id = fields.Many2one("investra.valuation.external", ondelete="set null", string="Ručně doložená úplata")
    name = fields.Char(compute="_compute_name", string="Úplata")
    class_id = fields.Many2one("investra.fund.class", ondelete="restrict", string="Třída")
    amount = fields.Float(digits=(20, 2), string="Částka")
    detail = fields.Text(string="Výpočet")
    group_key = fields.Integer(compute="_compute_group_key", store=True, string="Skupina řazení")
    is_correction = fields.Boolean(compute="_compute_group_key", store=True, string="Oprava")
    can_correct = fields.Boolean(compute="_compute_can_correct", string="Lze opravit")

    @api.depends("rule_id", "external_id.corrects_rule_id")
    def _compute_group_key(self):
        for line in self:
            corrected = line.external_id.corrects_rule_id
            rule = line.rule_id or corrected
            line.group_key = rule.id if rule else 2**31 - 1
            line.is_correction = bool(corrected)

    @api.depends("rule_id.kind", "valuation_id.state")
    def _compute_can_correct(self):
        for line in self:
            # ZJ-12 krok 5: opravit jde pravidlo každého druhu (úplata, odměna, daň).
            line.can_correct = bool(line.rule_id) and line.valuation_id.state in ("draft", "computed")

    def action_correct(self):
        """Otevře formulář ruční úplaty s předvyplněným „Opravuje úplatu“ (ZJ-11); uloží se až s částkou a poznámkou."""
        self.ensure_one()
        if not self.can_correct:
            raise UserError(self.env._("Opravit jde jen úplatu, odměnu nebo daň v ocenění ve stavu Návrh nebo Spočteno."))
        valuation = self.valuation_id
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Oprava úplaty %s", self.rule_id.name),
            "res_model": "investra.valuation.external",
            "view_mode": "form",
            "views": [(self.env.ref("investra_nav.view_valuation_external_correction_form").id, "form")],
            "target": "new",
            "context": {
                "default_valuation_id": valuation.id,
                "default_corrects_rule_id": self.rule_id.id,
                "default_class_id": self.class_id.id,
                "default_currency_id": valuation.fund_id.currency_id.id,
                # ZJ-12 A.3: snímek vypočtené částky při zadání; krok 4 ho porovná s novým výpočtem (kontrola B.8).
                "default_computed_at_entry": self.amount,
            },
        }

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
    # ZJ-12 A.3, B.7: opravit jde pravidlo každého druhu, částku i základ (výpočet od kroku 4). Formuláře zatím nabízejí
    # jen časově rozlišenou úplatu (domény ve views); rozšíří je krok 5.
    corrects_rule_id = fields.Many2one(
        "investra.fee.rule", ondelete="restrict", string="Opravuje úplatu",
        help="Oprava vypočtené úplaty, výkonnostní odměny nebo daně (zaokrouhlení podle faktury, dohoda s depozitářem). "
             "Účtuje se jako úplata pravidla; nákladový účet se nezadává. Oprava časově rozlišené úplaty platí trvale: "
             "průměrný FK ji v dalším ocenění nedorovná.",
    )
    correction_target = fields.Selection(
        [("amount", "Částka"), ("base", "Základ")], default="amount", required=True, string="Co opravuje",
        help="Částka: oprava se přičte k vypočtené částce pravidla. Základ: přičte se k základu pravidla; u daně je to "
             "ruční úprava základu (kladná = připočitatelná, záporná = odčitatelná položka), platí do konce roku.",
    )
    validity = fields.Selection(
        [("period", "Do konce období"), ("valuation", "Jen toto ocenění")], default="period", required=True,
        string="Platnost",
        help="Jen oprava výkonnostní odměny a daně. Do konce období: další ocenění opravu převezmou (odměna do "
             "krystalizace, daň do konce roku). Jen toto ocenění: další ocenění upozorní, že oprava skončila.",
    )
    computed_at_entry = fields.Float(
        digits=(20, 2), readonly=True, string="Vypočteno při zadání",
        help="Vypočtená částka pravidla v okamžiku zadání opravy (snímek). Liší-li se nový výpočet, ocenění opravu "
             "zastaví k potvrzení.",
    )
    origin_id = fields.Many2one(
        "investra.valuation.external", ondelete="set null", readonly=True, copy=False, index="btree_not_null",
        string="Převzato z",
        help="Řádek předchozí verze ocenění nebo dřívějšího ocenění, ze kterého se ruční úprava nebo oprava převzala.",
    )
    computed_captured = fields.Boolean(
        readonly=True, copy=False, string="Snímek pořízen",
        help="Snímek „Vypočteno při zadání“ je uložený (tlačítkem Opravit, nebo prvním výpočtem po zadání opravy).",
    )
    computed_now = fields.Float(
        digits=(20, 2), readonly=True, copy=False, string="Vypočteno nyní",
        help="Vypočtená částka pravidla v posledním výpočtu ocenění (pro Ponechat rozdíl / Ponechat výsledek).",
    )
    ended_id = fields.Many2one(
        "investra.valuation.external", ondelete="restrict", readonly=True, copy=False, index="btree_not_null",
        string="Ukončuje opravu",
        help="Převzatá oprava dřívějšího ocenění, kterou tento řádek ukončuje (oprava o −její částku, ZJ-12 B.7). "
             "Liší se od „Převzato z“ (převzetí z verze ocenění).",
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

    @api.constrains("valuation_id", "class_id", "amount", "account_id", "note", "corrects_rule_id", "currency_id",
                    "correction_target", "validity", "ended_id")
    def _check_fund(self):
        # Třída a účet musí patřit fondu ocenění; formulář je nabízí jen z něj, kontrola chrání i import a API.
        for row in self:
            fund = row.valuation_id.fund_id
            if row.class_id and row.class_id.fund_id != fund:
                raise ValidationError(self.env._("Třída ručně doložené úplaty musí patřit fondu ocenění %s.", fund.display_name))
            if row.ended_id and not row.corrects_rule_id:
                raise ValidationError(self.env._("Ukončit jde jen převzatou opravu úplaty."))
            if row.corrects_rule_id:
                row._check_correction(fund)
                if row.ended_id:
                    row._check_ending()
            elif row.correction_target != "amount" or row.validity != "period":
                raise ValidationError(self.env._("Co opravuje a Platnost se vyplňují jen u opravy úplaty."))
            elif not row.account_id or not row.account_id.account_type.startswith("expense"):
                raise ValidationError(self.env._("Ručně doložená úplata potřebuje nákladový účet."))
            if row.account_id.company_ids and row.valuation_id.company_id not in row.account_id.company_ids:
                raise ValidationError(self.env._("Nákladový účet ručně doložené úplaty musí patřit knize fondu %s.", fund.display_name))
            if not (row.note or "").strip():
                raise ValidationError(self.env._("Ručně doložená úplata musí mít poznámku."))
            if not round(row.amount, 2):
                raise ValidationError(self.env._("Částka ručně doložené úplaty nesmí být nulová."))

    def _check_correction(self, fund):
        """Oprava úplaty (ZJ-11, ZJ-12 A.3): pravidlo fondu ocenění (každého druhu), třída podle pravidla, bez nákladového
        účtu, měna fondu. Platnost „jen toto ocenění“ má smysl jen u odměny a daně (časově rozlišená úplata je trvalá)."""
        rule = self.corrects_rule_id
        if rule.fund_id != fund:
            raise ValidationError(self.env._("Opravovaná úplata %(rule)s nepatří fondu ocenění %(fund)s.",
                                             rule=rule.name, fund=fund.display_name))
        if self.correction_target == "base" and rule.kind == "periodic" and rule.base_source == "none":
            raise ValidationError(self.env._("Úplata %s nemá základ; opravte její částku.", rule.name))
        if self.validity != "period" and rule.kind == "periodic":
            raise ValidationError(self.env._(
                "Oprava časově rozlišené úplaty %s platí trvale; platnost „Jen toto ocenění“ je jen u odměny a daně.",
                rule.name))
        if rule.class_ids and self.class_id not in rule.class_ids:
            raise ValidationError(self.env._("Oprava úplaty %(rule)s musí mít třídu, která úplatu platí: %(classes)s.",
                                             rule=rule.name, classes=", ".join(rule.class_ids.mapped("code"))))
        if not rule.class_ids and self.class_id:
            raise ValidationError(self.env._("Úplata %s je úplatou celého fondu; oprava nesmí mít třídu.", rule.name))
        if self.account_id:
            raise ValidationError(self.env._("Oprava úplaty se účtuje na nákladovou roli pravidla; nákladový účet nevyplňujte."))
        if self.currency_id and self.currency_id != fund.currency_id:
            raise ValidationError(self.env._("Oprava úplaty musí být v měně fondu %s.", fund.currency_id.name))

    def _check_ending(self):
        """Ukončení převzaté opravy (ZJ-12 B.7): stejné pravidlo, třída a cíl, ukončovaná je oprava „do konce období“
        z dřívějšího ocenění téhož fondu, částka přesně −její částka, platnost „do konce období“, každá jen jednou."""
        ended = self.ended_id
        same = (ended.corrects_rule_id, ended.class_id, ended.correction_target) == (
            self.corrects_rule_id, self.class_id, self.correction_target)
        earlier = (ended.valuation_id.fund_id == self.valuation_id.fund_id and ended.valuation_id.date < self.valuation_id.date
                   and ended.valuation_id.state not in ("returned", "reversed"))
        if not same or not earlier or ended.validity != "period" or ended.ended_id:
            raise ValidationError(self.env._(
                "Ukončit jde jen převzatou opravu „do konce období“ téhož pravidla a třídy z dřívějšího ocenění."))
        if self.validity != "period" or round(self.amount + ended.amount, 2):
            raise ValidationError(self.env._(
                "Ukončení opravy má částku %(amount)s (−částka ukončované opravy) a platnost „Do konce období“.",
                amount=-ended.amount))
        # Ukončení ve vrácené nebo stornované verzi neplatí (nová verze ho smí převzít, B.10).
        if self.search_count([("ended_id", "=", ended.id), ("id", "!=", self.id),
                              ("valuation_id.state", "not in", ("returned", "reversed"))]):
            raise ValidationError(self.env._("Oprava %s už je ukončená.", ended.display_name))

    def action_keep_difference(self):
        """Ponechat rozdíl (ZJ-12 B.8): oprava zůstává, snímek se přepíše nynější vypočtenou částkou; přepočet."""
        self.ensure_one()
        self.write({"computed_at_entry": self.computed_now, "computed_captured": True})
        if not self.env.context.get("investra_skip_compute"):
            self.valuation_id.action_compute()

    def action_keep_result(self):
        """Ponechat výsledek (ZJ-12 B.8): výsledek při zadání (snímek + oprava) zůstává, oprava se dopočte k nynější
        vypočtené částce; snímek se přepíše; přepočet."""
        self.ensure_one()
        amount = round(self.computed_at_entry + self.amount - self.computed_now, 2)
        if not amount:
            raise UserError(self.env._(
                "Výsledek se rovná nynější vypočtené částce, oprava by byla nulová. Řádek opravy smažte."))
        self.write({"amount": amount, "computed_at_entry": self.computed_now, "computed_captured": True})
        if not self.env.context.get("investra_skip_compute"):
            self.valuation_id.action_compute()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "computed_at_entry" in vals:
                vals.setdefault("computed_captured", True)
            else:
                self._capture_from_existing_row(vals)
        records = super().create(vals_list)
        records._check_open()
        return records

    @api.model
    def _capture_from_existing_row(self, vals):
        """Snímek „Vypočteno při zadání“ u opravy částky zadané bez tlačítka Opravit (ZJ-12, upřesnění kroku 4, bod 3).

        Je-li ocenění už spočtené, snímek se vezme hned při uložení z řádku rozpisu téhož pravidla a třídy (částka řádku =
        vypočteno + převzaté opravy, bez nových oprav). Řádek rozpisu ještě není: snímek pořídí první výpočet (`_capture_computed`).
        """
        if not vals.get("corrects_rule_id") or vals.get("correction_target", "amount") != "amount":
            return
        line = self.env["investra.valuation.fee"].sudo().search([
            ("valuation_id", "=", vals.get("valuation_id")), ("rule_id", "=", vals["corrects_rule_id"]),
            ("class_id", "=", vals.get("class_id") or False)], limit=1)
        if line:
            vals.update(computed_at_entry=line.amount, computed_captured=True)

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
