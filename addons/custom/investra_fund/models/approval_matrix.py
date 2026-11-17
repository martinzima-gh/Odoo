"""Schvalovací matice (rozhodnutí „Schvalovací matice“ 2026-11-11, zjednodušení 2026-11-17, úkol ZJ-01).

Matice platí pro celou aplikaci. Řádek určí pro činnost jen počet osob: jeden člověk, čtyři oči, nebo kroky;
krok může volitelně požadovat konkrétní roli. Kdo činnost smí provést a kdo ji smí schválit, určují role
(`investra.role`): uživatel musí mít roli s činností a příznakem Provádí, resp. Schvaluje.
Změna pravidla = nový řádek s pozdějším „Platí od“; historie zůstává.

Úkon bez druhé osoby se zapíše do `investra.approval.log` a ocenění ho ukáže v kontrolách.
Jednorázové úkony se čtyřma očima jdou přes žádost `investra.approval.request`: první osoba požádá,
další potvrdí a teprve po posledním potvrzení se úkon provede jménem žadatele.
"""

import json
from dataclasses import dataclass, field

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

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
    ("trade_reverse", "Storno a oprava obchodu"),
]
SECOND_PERSON = [("no", "Ne – stačí jeden člověk"), ("yes", "Ano – čtyři oči"), ("steps", "Kroky")]

# Dnešní chování před maticí: počet schvalovatelů (osob navíc k tomu, kdo činnost provádí); platí, jen když
# matice pro činnost nemá žádný řádek. Počty beze změny proti stavu před ZJ-01, role se už neurčují (ZJ-01 bod 5).
BUILTIN = {
    "valuation_approve": 1,
    "valuation_return": 0,
    "valuation_publish": 0,
    "price_approve": 1,
    "manual_rate": 0,
    "lock_exception": 1,
    "subscription_manual": 0,
    "classification_override": 0,
    # Výchozí bez druhé osoby (rozhodnutí uživatele 2026-11-12 „Zámek a storno splátky“).
    "repayment_reverse": 0,
    # Storno vypořádání, storno a oprava obchodu: výchozí jako storno splátky (rozhodnutí uživatele 2026-11-12).
    "trade_reverse": 0,
}
DEFAULT_STEP = "Kontrola druhou osobou"
PERFORM, APPROVE = "perform", "approve"

# Provedení schválené žádosti; hodnotu nejde poslat přes API, proto ji nikdo nepodvrhne.
_CTX = "investra_matrix_pass"


class _Pass:
    def __init__(self, request):
        self.key = (request.activity, request.res_model, request.res_id)


def user_can(env, user, activity, mode, role=None):
    """Má uživatel aktivní roli s činností a příznakem Provádí (`mode="perform"`), resp. Schvaluje (`"approve"`)?
    Je-li zadaná `role`, musí to být právě ona."""
    domain = [("activity", "=", activity), (mode, "=", True),
              ("role_id.active", "=", True), ("role_id.user_ids", "in", user.ids)]
    if role:
        domain.append(("role_id", "=", role.id))
    return bool(env["investra.role.line"].sudo().search_count(domain, limit=1))


def check_user(env, user, activity, mode, role=None):
    """Výjimka, když uživatel nemá roli s činností a příslušným příznakem (superuživatel prochází)."""
    if env.su or user_can(env, user, activity, mode, role):
        return
    what = dict(ACTIVITIES)[activity]
    if mode == PERFORM:
        raise AccessError(env._(
            "%(what)s smí podle schvalovací matice provést jen uživatel s rolí, která má tuto činnost s příznakem Provádí.",
            what=what,
        ))
    if role:
        raise AccessError(env._(
            "%(what)s smí v tomto kroku schválit jen uživatel s rolí %(role)s, která má činnost s příznakem Schvaluje.",
            what=what, role=role.name,
        ))
    raise AccessError(env._(
        "%(what)s smí podle schvalovací matice schválit jen uživatel s rolí, která má tuto činnost s příznakem Schvaluje.",
        what=what,
    ))


@dataclass
class Step:
    name: str
    role: object  # investra.role; prázdná = kdokoli, kdo činnost schvaluje


@dataclass
class Rule:
    """Platné pravidlo činnosti; `row` je řádek matice (prázdný = dnešní chování bez matice)."""

    activity: str
    row: object
    steps: list = field(default_factory=list)

    @property
    def persons(self):
        return 1 + len(self.steps)

    def label(self):
        return "jeden člověk" if self.persons == 1 else f"{self.persons} osoby"

    def check_performer(self, env, user=None):
        check_user(env, user or env.user, self.activity, PERFORM)

    def check_approver(self, env, user, step):
        check_user(env, user, self.activity, APPROVE, step.role)


class InvestraApprovalMatrix(models.Model):
    _name = "investra.approval.matrix"
    _inherit = ["mail.thread"]
    _description = "Řádek schvalovací matice"
    _order = "activity, valid_from desc, id desc"

    activity = fields.Selection(ACTIVITIES, required=True, tracking=True, string="Činnost")
    valid_from = fields.Date(required=True, default=fields.Date.context_today, tracking=True, string="Platí od")
    second_person = fields.Selection(SECOND_PERSON, required=True, default="yes", tracking=True, string="Druhá osoba")
    step_ids = fields.One2many("investra.approval.matrix.step", "matrix_id", string="Kdo schvaluje")
    persons = fields.Integer(compute="_compute_persons", string="Počet osob")
    note = fields.Char(string="Poznámka", tracking=True)
    builtin = fields.Boolean(
        readonly=True, string="Výchozí řádek",
        help="Řádek dodaný modulem = chování před maticí. Úkony podle něj se zapisují, kontroly ocenění je neukazují.",
    )

    _uniq = models.Constraint("UNIQUE (activity, valid_from)", "Pro činnost a den už řádek matice existuje.")

    @api.depends("step_ids", "second_person")
    def _compute_persons(self):
        for row in self:
            row.persons = 1 if row.second_person == "no" else 1 + len(row.step_ids)

    @api.onchange("second_person")
    def _onchange_second_person(self):
        """Bez druhé osoby nemá řádek schvalovatele: volba Ne je smaže (2026-11-12, zkouška v UI)."""
        for row in self:
            if row.second_person == "no" and row.step_ids:
                row.step_ids = [(5,)]

    @api.depends("activity", "valid_from")
    def _compute_display_name(self):
        for row in self:
            row.display_name = f"{dict(ACTIVITIES).get(row.activity, '')} – od {row.valid_from}"

    # --- změny ---------------------------------------------------------------------------------

    @api.model
    def _check_manage(self):
        """Matici mění jen úroveň Správa (nebo správce systému); rozhodnutí 2026-11-17 po ZJ-01."""
        user = self.env.user
        if self.env.su or user.has_group("investra_entity.group_investra_admin") or user.has_group("base.group_system"):
            return
        raise AccessError(self.env._("Schvalovací matici mění jen uživatel s úrovní přístupu Správa."))

    def _check_editable(self):
        if self.env.su:
            return
        self._check_manage()
        # MN-18 (nález MN-13 č. 5): výchozí řádek z modulu má vlastní, srozumitelnější hlášení než obecný platný řádek.
        if self.filtered("builtin"):
            raise UserError(self.env._(
                "Výchozí řádek z modulu nejde měnit ani smazat; zadejte nový řádek s pozdějším „Platí od“."
            ))
        today = fields.Date.context_today(self)
        if self.filtered(lambda r: r.valid_from < today):
            raise UserError(self.env._(
                "Platný řádek matice nejde měnit ani mazat. Změnu zadejte novým řádkem s pozdějším „Platí od“."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            self._check_manage()
            today = fields.Date.context_today(self)
            if any(fields.Date.to_date(v.get("valid_from") or today) < today for v in vals_list):
                raise UserError(self.env._("Řádek matice nejde založit zpětně; „Platí od“ musí být dnes nebo později."))
        for vals in vals_list:
            if vals.get("second_person", "yes") == "yes" and not vals.get("step_ids"):
                vals["step_ids"] = [(0, 0, {"name": DEFAULT_STEP})]
        return super().create(vals_list)

    def write(self, vals):
        self._check_editable()
        if vals.get("second_person") == "yes" and "step_ids" not in vals and not self.step_ids:
            vals = dict(vals, step_ids=[(0, 0, {"name": DEFAULT_STEP})])
        result = super().write(vals)
        if "valid_from" in vals:
            self._check_editable()
        return result

    def unlink(self):
        self._check_editable()
        return super().unlink()

    @api.constrains("second_person", "step_ids")
    def _check_row(self):
        for row in self:
            if row.second_person == "no" and row.step_ids:
                raise ValidationError(self.env._("Bez druhé osoby nemá řádek schvalovatele. Smažte je nebo změňte volbu."))
            if row.second_person == "yes" and len(row.step_ids) > 1:
                raise ValidationError(self.env._("Čtyři oči mají jednoho schvalovatele; pro více použijte Kroky."))
            if row.second_person == "steps" and not row.step_ids:
                raise ValidationError(self.env._("Kroky musí mít aspoň jednoho schvalovatele."))

    # --- platné pravidlo ------------------------------------------------------------------------

    @api.model
    def _row_rule(self, row):
        steps = [Step(s.name, s.role_id) for s in row.step_ids.sorted("sequence")]
        return Rule(row.activity, row, steps)

    @api.model
    def _builtin_rule(self, activity):
        Role = self.env["investra.role"]
        return Rule(activity, self.browse(), [Step(DEFAULT_STEP, Role) for _ in range(BUILTIN[activity])])

    @api.model
    def _rule(self, activity, day=None):
        """Platné pravidlo činnosti k `day` (výchozí dnes): nejnovější řádek matice, jinak dnešní chování."""
        day = day or fields.Date.context_today(self)
        row = self.sudo().search(
            [("activity", "=", activity), ("valid_from", "<=", day)], order="valid_from desc, id desc", limit=1,
        )
        return self._row_rule(row) if row else self._builtin_rule(activity)

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
    def _gate(self, activity, record, method, kwargs=None, summary="", company=None):
        """Jednorázový úkon podle matice.

        Vrátí None, když se úkon má provést hned (jeden člověk, nebo právě běží schválená žádost),
        jinak založí žádost a vrátí ji; volající pak úkon neprovede.
        """
        if self._passing(activity, record) or self.env.su:
            return None
        rule = self._rule(activity)
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
                (0, 0, {"sequence": i, "name": s.name, "role_id": s.role.id, "role": s.role.name or False})
                for i, s in enumerate(rule.steps)
            ],
        }).sudo(False)

    @api.model
    def _approve_step(self, activity, record, performers):
        """Další krok schválení záznamu (cena, výjimka). Vrátí True po posledním kroku.

        `performers` = kdo záznam zadal. Jeden člověk: schválit smí i zadavatel (zapíše se); stačí mu role
        s příznakem Provádí. Čtyři oči a kroky: role s příznakem Schvaluje (případně role kroku) a každý krok
        jiný člověk než zadavatel a předchozí schvalovatelé.
        """
        Done = self.env["investra.approval.done"].sudo()
        user = self.env.user
        rule = self._rule(activity)
        done = Done.search([("res_model", "=", record._name), ("res_id", "=", record.id)])
        what = dict(ACTIVITIES)[activity]
        company = record.company_id if "company_id" in record._fields else self.env["res.company"]
        if rule.persons == 1:
            rule.check_performer(self.env, user)
            Done.create({"res_model": record._name, "res_id": record.id, "sequence": 0, "name": what,
                         "user_id": user.id, "company_id": company.id})
            if user in performers:
                self._log_alone(rule, record)
            return True
        step = rule.steps[min(len(done), len(rule.steps) - 1)]
        rule.check_approver(self.env, user, step)
        if not self.env.su and (user in performers or user in done.user_id):
            raise UserError(self.env._("%s: každý krok musí provést jiný člověk než zadavatel a předchozí schvalovatelé.", what))
        Done.create({"res_model": record._name, "res_id": record.id, "sequence": len(done), "name": step.name,
                     "user_id": user.id, "company_id": company.id})
        return len(done) + 1 >= len(rule.steps)


class InvestraApprovalMatrixStep(models.Model):
    _name = "investra.approval.matrix.step"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Schvalovatel v řádku matice"
    _order = "matrix_id, sequence, id"

    _line_tracking_parent = "matrix_id"

    matrix_id = fields.Many2one("investra.approval.matrix", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10, string="Pořadí")
    name = fields.Char(required=True, default=DEFAULT_STEP, tracking=True, string="Krok")
    role_id = fields.Many2one(
        "investra.role", ondelete="restrict", tracking=True, string="Role",
        help="Prázdné = kdokoli s rolí, která má činnost s příznakem Schvaluje.",
    )

    def _line_tracking_desc(self):
        role_label = self.role_id.name or "kdokoli, kdo schvaluje"
        return f"{self.name} ({role_label})"

    def _touch(self, rows):
        # Změna kroku je změnou řádku: posune datum změny (kontrola „změna matice“).
        # Detailní zprávu o změně schvalovatele zapisuje mixin line tracking.
        for row in rows:
            row.sudo().write({"note": row.note})

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
            check_user(self.env, user, request.activity, APPROVE, line.role_id)
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
                check_user(self.env, self.env.user, request.activity, APPROVE, line.role_id)
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
    role_id = fields.Many2one("investra.role", readonly=True, ondelete="restrict", string="Role kroku")
    # Text role v okamžiku žádosti; u žádostí před ZJ-01 název tehdejší nejnižší role (převedeno migrací).
    role = fields.Char(readonly=True, string="Role (text)")
    user_id = fields.Many2one("res.users", readonly=True, string="Potvrdil")
    approved_at = fields.Datetime(readonly=True, string="Potvrzeno dne")

