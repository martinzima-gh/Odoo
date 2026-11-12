"""Schvalovací matice obhospodařovatele (rozhodnutí „Schvalovací matice“, 2026-11-11).

Řádek matice určí pro činnost, kolik lidí ji provede (jeden člověk, čtyři oči, nebo kroky) a jakou nejnižší
roli musí mít každý stupeň; volitelně jmenovitě uživatele. Matice je u obhospodařovatele (kniha druhu
Investiční společnost); řádky bez obhospodařovatele jsou výchozí matice. Fond smí řádek jen zpřísnit.
Změna pravidla = nový řádek s pozdějším „Platí od“; historie zůstává.

Úkon bez druhé osoby se zapíše do `investra.approval.log` a ocenění ho ukáže v kontrolách.
Jednorázové úkony se čtyřma očima jdou přes žádost `investra.approval.request`: první osoba požádá,
další potvrdí a teprve po posledním potvrzení se úkon provede jménem žadatele.
"""

import json
from dataclasses import dataclass, field
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

ROLES = [("preparer", "Příprava ocenění"), ("approver", "Schvalování ocenění")]
ROLE_GROUPS = {
    "preparer": "investra_entity.group_valuation_preparer",
    "approver": "investra_entity.group_valuation_approver",
}
# Pořadí rolí pro „nejnižší roli“: vyšší role splní i nižší požadavek (zadání uživatele 2026-11-11).
ROLE_RANK = {"preparer": 1, "approver": 2}

ACTIVITIES = [
    ("valuation_approve", "Schválení ocenění"),
    ("valuation_return", "Vrácení a storno ocenění"),
    ("valuation_publish", "Zveřejnění ocenění"),
    ("price_approve", "Schválení ceny"),
    ("manual_rate", "Ruční kurz a přepis kurzu"),
    ("lock_exception", "Výjimka z uzamčení"),
    ("subscription_manual", "Ruční zadání úpisu a odkupu"),
    ("classification_override", "Ruční přepsání kategorie IFRS 9"),
    ("repayment_reverse", "Storno a oprava splátky nástroje"),
]
SECOND_PERSON = [("no", "Ne – stačí jeden člověk"), ("yes", "Ano – čtyři oči"), ("steps", "Kroky")]

# Dnešní chování před maticí; platí, jen když matice pro činnost nemá žádný řádek.
BUILTIN = {
    "valuation_approve": ("preparer", ["approver"]),
    "valuation_return": ("approver", []),
    "valuation_publish": ("approver", []),
    "price_approve": ("preparer", ["approver"]),
    "manual_rate": ("approver", []),
    "lock_exception": ("approver", ["approver"]),
    "subscription_manual": ("preparer", []),
    "classification_override": ("preparer", []),
    # Výchozí bez druhé osoby (rozhodnutí uživatele 2026-11-12 „Zámek a storno splátky“).
    "repayment_reverse": ("preparer", []),
}
DEFAULT_STEP = "Kontrola druhou osobou"

# Provedení schválené žádosti; hodnotu nejde poslat přes API, proto ji nikdo nepodvrhne.
_CTX = "investra_matrix_pass"


class _Pass:
    def __init__(self, request):
        self.key = (request.activity, request.res_model, request.res_id)


def user_rank(user):
    return max((ROLE_RANK[role] for role, group in ROLE_GROUPS.items() if user.has_group(group)), default=0)


def check_user(env, user, role, users, what):
    """Splňuje uživatel nejnižší roli stupně a případný výčet jmenovitých uživatelů?"""
    if env.su:
        return
    if user_rank(user) < ROLE_RANK[role or "approver"]:
        raise AccessError(env._(
            "%(what)s vyžaduje podle schvalovací matice aspoň roli %(role)s.",
            what=what, role=dict(ROLES)[role or "approver"],
        ))
    if users and user not in users:
        raise AccessError(env._(
            "%(what)s smí podle schvalovací matice provést jen: %(users)s.",
            what=what, users=", ".join(users.mapped("name")),
        ))


@dataclass
class Step:
    name: str
    role: str
    users: object  # res.users


@dataclass
class Rule:
    """Platné pravidlo činnosti; `row` je řádek matice (prázdný = dnešní chování bez matice)."""

    activity: str
    row: object
    performer_role: str
    performer_users: object
    steps: list = field(default_factory=list)

    @property
    def persons(self):
        return 1 + len(self.steps)

    def key(self):
        return (self.persons, ROLE_RANK[self.performer_role], sum(ROLE_RANK[s.role] for s in self.steps))

    def covers(self, other):
        """Je toto pravidlo aspoň tak přísné jako `other`? (fond smí jen zpřísnit)"""
        if self.persons < other.persons or ROLE_RANK[self.performer_role] < ROLE_RANK[other.performer_role]:
            return False
        if other.performer_users and not (self.performer_users and self.performer_users <= other.performer_users):
            return False
        for mine, theirs in zip(self.steps, other.steps):
            if ROLE_RANK[mine.role] < ROLE_RANK[theirs.role]:
                return False
            if theirs.users and not (mine.users and mine.users <= theirs.users):
                return False
        return True

    def label(self):
        return "jeden člověk" if self.persons == 1 else f"{self.persons} osoby"

    def check_user(self, env, user, role, users, what):
        check_user(env, user, role, users, what)

    def check_performer(self, env, user=None):
        name = dict(ACTIVITIES)[self.activity]
        self.check_user(env, user or env.user, self.performer_role, self.performer_users, name)


class InvestraApprovalMatrix(models.Model):
    _name = "investra.approval.matrix"
    _inherit = ["mail.thread"]
    _description = "Řádek schvalovací matice"
    _order = "activity, manager_id, fund_id, valid_from desc, id desc"

    activity = fields.Selection(ACTIVITIES, required=True, tracking=True, string="Činnost")
    manager_id = fields.Many2one(
        "investra.entity", ondelete="restrict", index=True, tracking=True, string="Obhospodařovatel",
        domain=[("entity_type", "=", "manager")], help="Prázdné = výchozí matice pro fondy bez obhospodařovatele.",
    )
    fund_id = fields.Many2one(
        "investra.fund", ondelete="cascade", index=True, tracking=True, string="Zpřísnění pro fond",
        help="Řádek fondu smí pravidlo obhospodařovatele jen zpřísnit.",
    )
    company_id = fields.Many2one("res.company", compute="_compute_company", store=True, index=True)
    valid_from = fields.Date(required=True, default=fields.Date.context_today, tracking=True, string="Platí od")
    performer_role = fields.Selection(ROLES, required=True, default="preparer", tracking=True, string="Kdo provádí (nejnižší role)")
    performer_user_ids = fields.Many2many(
        "res.users", "investra_approval_matrix_performer_rel", "matrix_id", "user_id", string="Jen tito uživatelé",
        help="Prázdné = každý s rolí.",
    )
    second_person = fields.Selection(SECOND_PERSON, required=True, default="yes", tracking=True, string="Druhá osoba")
    step_ids = fields.One2many("investra.approval.matrix.step", "matrix_id", string="Kdo schvaluje")
    persons = fields.Integer(compute="_compute_persons", string="Počet osob")
    note = fields.Char(string="Poznámka", tracking=True)
    builtin = fields.Boolean(
        readonly=True, string="Výchozí řádek",
        help="Řádek dodaný modulem = chování před maticí. Úkony podle něj se zapisují, kontroly ocenění je neukazují.",
    )

    _uniq = models.Constraint(
        "UNIQUE NULLS NOT DISTINCT (activity, manager_id, fund_id, valid_from)",
        "Pro činnost a den už řádek matice existuje.",
    )

    @api.depends("manager_id", "fund_id")
    def _compute_company(self):
        for row in self:
            row.company_id = row.fund_id.company_id or row.manager_id.company_id

    @api.depends("step_ids")
    def _compute_persons(self):
        for row in self:
            row.persons = 1 + len(row.step_ids)

    @api.depends("activity", "manager_id", "fund_id", "valid_from")
    def _compute_display_name(self):
        for row in self:
            owner = row.fund_id.display_name or row.manager_id.display_name or "výchozí"
            row.display_name = f"{dict(ACTIVITIES).get(row.activity, '')} – {owner} – od {row.valid_from}"

    # --- změny ---------------------------------------------------------------------------------

    def _check_editable(self):
        if self.env.su:
            return
        if not self.env.user.has_group(ROLE_GROUPS["approver"]):
            raise AccessError(self.env._("Schvalovací matici mění jen skupina schvalování ocenění."))
        today = fields.Date.context_today(self)
        if self.filtered(lambda r: r.valid_from < today):
            raise UserError(self.env._(
                "Platný řádek matice nejde měnit ani mazat. Změnu zadejte novým řádkem s pozdějším „Platí od“."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            if not self.env.user.has_group(ROLE_GROUPS["approver"]):
                raise AccessError(self.env._("Schvalovací matici mění jen skupina schvalování ocenění."))
            today = fields.Date.context_today(self)
            if any(fields.Date.to_date(v.get("valid_from") or today) < today for v in vals_list):
                raise UserError(self.env._("Řádek matice nejde založit zpětně; „Platí od“ musí být dnes nebo později."))
        for vals in vals_list:
            if vals.get("second_person", "yes") == "yes" and not vals.get("step_ids"):
                vals["step_ids"] = [(0, 0, {"name": DEFAULT_STEP, "role": "approver"})]
        return super().create(vals_list)

    def write(self, vals):
        self._check_editable()
        if vals.get("second_person") == "yes" and "step_ids" not in vals and not self.step_ids:
            vals = dict(vals, step_ids=[(0, 0, {"name": DEFAULT_STEP, "role": "approver"})])
        result = super().write(vals)
        if "valid_from" in vals:
            self._check_editable()
        return result

    def unlink(self):
        self._check_editable()
        return super().unlink()

    @api.constrains("second_person", "step_ids", "manager_id", "fund_id")
    def _check_row(self):
        for row in self:
            if row.manager_id and row.fund_id:
                raise ValidationError(self.env._("Řádek patří buď obhospodařovateli, nebo fondu (zpřísnění)."))
            if row.second_person == "no" and row.step_ids:
                raise ValidationError(self.env._("Bez druhé osoby nemá řádek schvalovatele. Smažte je nebo změňte volbu."))
            if row.second_person == "yes" and len(row.step_ids) > 1:
                raise ValidationError(self.env._("Čtyři oči mají jednoho schvalovatele; pro více použijte Kroky."))
            if row.second_person == "steps" and not row.step_ids:
                raise ValidationError(self.env._("Kroky musí mít aspoň jednoho schvalovatele."))
            if row.fund_id:
                for day in {row.valid_from, fields.Date.context_today(row)}:
                    base = self._base_rule(row.activity, row.fund_id, day)
                    if not self._row_rule(row).covers(base):
                        raise ValidationError(self.env._(
                            "Fond %(fund)s smí pravidlo matice jen zpřísnit; platí %(base)s s nejnižšími rolemi podle matice.",
                            fund=row.fund_id.display_name, base=base.label(),
                        ))

    # --- platné pravidlo ------------------------------------------------------------------------

    @api.model
    def _row_rule(self, row):
        steps = [Step(s.name, s.role, s.user_ids) for s in row.step_ids.sorted("sequence")]
        return Rule(row.activity, row, row.performer_role, row.performer_user_ids, steps)

    @api.model
    def _builtin_rule(self, activity):
        performer, steps = BUILTIN[activity]
        Users = self.env["res.users"]
        return Rule(activity, self.browse(), performer, Users, [Step(DEFAULT_STEP, role, Users) for role in steps])

    @api.model
    def _latest(self, domain, day):
        return self.sudo().search(domain + [("valid_from", "<=", day)], order="valid_from desc, id desc", limit=1)

    @api.model
    def _base_rule(self, activity, fund, day):
        """Pravidlo obhospodařovatele fondu, jinak výchozí matice, jinak dnešní chování."""
        manager = fund.manager_id if fund else self.env["investra.entity"]
        row = manager and self._latest(
            [("activity", "=", activity), ("manager_id", "=", manager.id), ("fund_id", "=", False)], day
        )
        row = row or self._latest([("activity", "=", activity), ("manager_id", "=", False), ("fund_id", "=", False)], day)
        return self._row_rule(row) if row else self._builtin_rule(activity)

    @api.model
    def _rule(self, activity, funds=None, day=None):
        """Platné pravidlo činnosti pro fondy. Sdílený záznam (sdílená cena, kurz) se týká všech fondů,
        proto platí nejpřísnější z jejich pravidel."""
        day = day or fields.Date.context_today(self)
        rules = []
        for fund in (funds or self.env["investra.fund"]).sudo():
            base = self._base_rule(activity, fund, day)
            row = self._latest([("activity", "=", activity), ("fund_id", "=", fund.id)], day)
            own = row and self._row_rule(row)
            rules.append(own if own and own.covers(base) else base)
        if not rules:
            rules.append(self._base_rule(activity, None, day))
        return max(rules, key=Rule.key)

    # --- provedení ------------------------------------------------------------------------------

    @api.model
    def _log_alone(self, rule, record, user=None, name=""):
        """Zápis úkonu, který provedl jeden člověk; ocenění ho ukáže v kontrolách."""
        user = user or self.env.user
        return self.env["investra.approval.log"].sudo().create({
            "activity": rule.activity,
            "matrix_id": rule.row.id,
            "user_id": user.id,
            "res_model": record._name,
            "res_id": record.id or 0,
            "record_name": (record.display_name if record.id else "") or name,
            "company_id": record.company_id.id if "company_id" in record._fields and record.id else False,
        })

    @api.model
    def _passing(self, activity, record):
        """Běží právě provedení schválené žádosti pro tento úkon?"""
        token = self.env.context.get(_CTX)
        return isinstance(token, _Pass) and token.key == (activity, record._name, record.id or 0)

    @api.model
    def _gate(self, activity, record, method, funds, kwargs=None, summary="", company=None):
        """Jednorázový úkon podle matice.

        Vrátí None, když se úkon má provést hned (jeden člověk, nebo právě běží schválená žádost),
        jinak založí žádost a vrátí ji; volající pak úkon neprovede.
        """
        if self._passing(activity, record) or self.env.su:
            return None
        rule = self._rule(activity, funds)
        rule.check_performer(self.env)
        if rule.persons == 1:
            self._log_alone(rule, record, name=summary)
            return None
        if record.id and len(record) != 1:
            raise UserError(self.env._("Úkon se čtyřma očima se žádá pro jeden záznam."))
        company = company or (record.company_id if "company_id" in record._fields and record.id else None)
        return self.env["investra.approval.request"].sudo().create({
            "activity": activity,
            "matrix_id": rule.row.id,
            "res_model": record._name,
            "res_id": record.id or 0,
            "record_name": record.display_name if record.id else "",
            "method": method,
            "payload": json.dumps(kwargs or {}, ensure_ascii=False, default=str),
            "summary": summary,
            "company_id": company.id if company else False,
            "requested_by": self.env.user.id,
            "line_ids": [
                (0, 0, {"sequence": i, "name": s.name, "role": s.role, "user_ids": [(6, 0, s.users.ids)]})
                for i, s in enumerate(rule.steps)
            ],
        }).sudo(False)

    @api.model
    def _approve_step(self, activity, record, funds, performers):
        """Další krok schválení záznamu (cena, výjimka). Vrátí True po posledním kroku.

        `performers` = kdo záznam zadal. Jeden člověk: schválit smí i zadavatel (zapíše se). Čtyři oči a kroky:
        každý krok jiný člověk než zadavatel a předchozí schvalovatelé.
        """
        Done = self.env["investra.approval.done"].sudo()
        user = self.env.user
        rule = self._rule(activity, funds)
        done = Done.search([("res_model", "=", record._name), ("res_id", "=", record.id)])
        what = dict(ACTIVITIES)[activity]
        company = record.company_id if "company_id" in record._fields else self.env["res.company"]
        if rule.persons == 1:
            rule.check_user(self.env, user, rule.performer_role, rule.performer_users, what)
            Done.create({"res_model": record._name, "res_id": record.id, "sequence": 0, "name": what,
                         "user_id": user.id, "company_id": company.id})
            if user in performers:
                self._log_alone(rule, record)
            return True
        step = rule.steps[min(len(done), len(rule.steps) - 1)]
        rule.check_user(self.env, user, step.role, step.users, what)
        if not self.env.su and (user in performers or user in done.user_id):
            raise UserError(self.env._("%s: každý krok musí provést jiný člověk než zadavatel a předchozí schvalovatelé.", what))
        Done.create({"res_model": record._name, "res_id": record.id, "sequence": len(done), "name": step.name,
                     "user_id": user.id, "company_id": company.id})
        return len(done) + 1 >= len(rule.steps)


class InvestraApprovalMatrixStep(models.Model):
    _name = "investra.approval.matrix.step"
    _description = "Schvalovatel v řádku matice"
    _order = "matrix_id, sequence, id"

    matrix_id = fields.Many2one("investra.approval.matrix", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10, string="Pořadí")
    name = fields.Char(required=True, default=DEFAULT_STEP, string="Krok")
    role = fields.Selection(ROLES, required=True, default="approver", string="Nejnižší role")
    user_ids = fields.Many2many("res.users", string="Jen tito uživatelé", help="Prázdné = každý s rolí.")

    def _touch(self, rows):
        # Změna kroku je změnou řádku: posune datum změny (kontrola „změna matice“) a zapíše se do historie.
        for row in rows:
            row.sudo().write({"note": row.note})
            row.message_post(body=self.env._("Změněni schvalovatelé: %s", ", ".join(
                f"{s.name} ({dict(ROLES)[s.role]})" for s in row.step_ids.sorted("sequence")) or "žádní"))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.matrix_id._check_editable()
        records._touch(records.matrix_id)
        return records

    def write(self, vals):
        self.matrix_id._check_editable()
        result = super().write(vals)
        self._touch(self.matrix_id)
        return result

    def unlink(self):
        rows = self.matrix_id
        rows._check_editable()
        result = super().unlink()
        self._touch(rows.exists())
        return result


class InvestraApprovalLog(models.Model):
    _name = "investra.approval.log"
    _description = "Úkon bez druhé osoby"
    _order = "id desc"

    activity = fields.Selection(ACTIVITIES, required=True, readonly=True, string="Činnost")
    matrix_id = fields.Many2one("investra.approval.matrix", readonly=True, ondelete="restrict", string="Řádek matice")
    user_id = fields.Many2one("res.users", required=True, readonly=True, string="Provedl")
    res_model = fields.Char(readonly=True, string="Model")
    res_id = fields.Integer(readonly=True, string="Záznam")
    record_name = fields.Char(readonly=True, string="Název záznamu")
    company_id = fields.Many2one("res.company", readonly=True, index=True, string="Účetní kniha")

    def write(self, vals):
        raise UserError(self.env._("Záznam úkonu nejde měnit."))

    def unlink(self):
        raise UserError(self.env._("Záznam úkonu nejde smazat."))


class InvestraApprovalDone(models.Model):
    _name = "investra.approval.done"
    _description = "Provedený krok schválení"
    _order = "res_model, res_id, sequence"

    res_model = fields.Char(required=True, readonly=True, index=True)
    res_id = fields.Integer(required=True, readonly=True, index=True)
    sequence = fields.Integer(readonly=True, string="Pořadí")
    name = fields.Char(readonly=True, string="Krok")
    user_id = fields.Many2one("res.users", required=True, readonly=True, string="Schválil")
    company_id = fields.Many2one("res.company", readonly=True, index=True)


class InvestraApprovalRequest(models.Model):
    """Žádost o jednorázový úkon se čtyřma očima. Úkon se provede jménem žadatele po posledním potvrzení."""

    _name = "investra.approval.request"
    _inherit = ["mail.thread"]
    _description = "Žádost podle schvalovací matice"
    _order = "id desc"

    activity = fields.Selection(ACTIVITIES, required=True, readonly=True, string="Činnost")
    matrix_id = fields.Many2one("investra.approval.matrix", readonly=True, ondelete="restrict", string="Řádek matice")
    company_id = fields.Many2one("res.company", readonly=True, index=True, string="Účetní kniha")
    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(readonly=True)
    record_name = fields.Char(readonly=True, string="Záznam")
    method = fields.Char(required=True, readonly=True)
    payload = fields.Text(readonly=True)
    summary = fields.Text(readonly=True, string="Co se provede")
    requested_by = fields.Many2one("res.users", required=True, readonly=True, string="Požádal")
    state = fields.Selection(
        [("pending", "Čeká na potvrzení"), ("done", "Provedeno"), ("rejected", "Zamítnuto")],
        default="pending", required=True, readonly=True, tracking=True, string="Stav",
    )
    line_ids = fields.One2many("investra.approval.request.line", "request_id", readonly=True, string="Potvrzení")
    done_at = fields.Datetime(readonly=True, string="Provedeno")

    @api.depends("activity", "record_name")
    def _compute_display_name(self):
        for request in self:
            request.display_name = " – ".join(p for p in (dict(ACTIVITIES).get(request.activity), request.record_name) if p)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise UserError(self.env._("Žádost vzniká jen úkonem podle schvalovací matice."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            raise UserError(self.env._("Žádost se mění jen potvrzením nebo zamítnutím."))
        return super().write(vals)

    def unlink(self):
        raise UserError(self.env._("Žádost nejde smazat; zamítněte ji."))

    def _action_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id,
            "view_mode": "form", "target": "current",
        }

    def action_approve(self):
        user = self.env.user
        for request in self:
            if request.state != "pending":
                raise UserError(self.env._("Potvrdit lze jen čekající žádost."))
            lines = request.line_ids.sorted("sequence")
            line = lines.filtered(lambda l: not l.user_id)[:1]
            check_user(self.env, user, line.role, line.user_ids, dict(ACTIVITIES)[request.activity])
            if user == request.requested_by or user in lines.user_id:
                raise UserError(self.env._("Žádost musí potvrdit jiný člověk než žadatel a předchozí schvalovatelé."))
            line.sudo().write({"user_id": user.id, "approved_at": fields.Datetime.now()})
            request.sudo().message_post(body=self.env._("Potvrdil %(user)s (%(step)s).", user=user.name, step=line.name))
            if not request.line_ids.filtered(lambda l: not l.user_id):
                request._execute()
        return True

    def _execute(self):
        self.ensure_one()
        target = self.env[self.res_model].browse(self.res_id) if self.res_id else self.env[self.res_model]
        companies = (self.company_id or self.requested_by.company_id).ids
        target = target.with_user(self.requested_by).with_context(
            allowed_company_ids=companies, **{_CTX: _Pass(self)}
        )
        getattr(target, self.method)(**json.loads(self.payload or "{}"))
        self.sudo().write({"state": "done", "done_at": fields.Datetime.now()})

    def action_reject(self):
        for request in self:
            if request.state != "pending":
                raise UserError(self.env._("Zamítnout lze jen čekající žádost."))
            line = request.line_ids.filtered(lambda l: not l.user_id).sorted("sequence")[:1]
            if self.env.user != request.requested_by:
                check_user(self.env, self.env.user, line.role, line.user_ids, dict(ACTIVITIES)[request.activity])
            request.sudo().write({"state": "rejected"})
            request.sudo().message_post(body=self.env._("Zamítl %s.", self.env.user.name))
        return True

    def action_open_record(self):
        self.ensure_one()
        if not self.res_id:
            return False
        return {"type": "ir.actions.act_window", "res_model": self.res_model, "res_id": self.res_id,
                "view_mode": "form", "target": "current"}


class InvestraApprovalRequestLine(models.Model):
    _name = "investra.approval.request.line"
    _description = "Potvrzení žádosti"
    _order = "request_id, sequence"

    request_id = fields.Many2one("investra.approval.request", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(readonly=True, string="Pořadí")
    name = fields.Char(readonly=True, string="Krok")
    role = fields.Selection(ROLES, readonly=True, string="Nejnižší role")
    user_ids = fields.Many2many("res.users", readonly=True, string="Jen tito uživatelé")
    user_id = fields.Many2one("res.users", readonly=True, string="Potvrdil")
    approved_at = fields.Datetime(readonly=True, string="Potvrzeno dne")

