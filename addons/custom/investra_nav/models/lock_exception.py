"""Zámek ocenění, vrstvy 2 a 3 (rozhodnutí „Zámek ocenění ve třech vrstvách“, 2026-11-11).

Zveřejnění ocenění nastaví vratný zámek Odoo pro všechny (`fiscalyear_lock_date`). Snížit ho pod datum
zveřejněného ocenění nejde. Pojistkou je výjimka Odoo (`account.lock_exception`); u fondové knihy vzniká jen
ze žádosti, kterou podá schvalovatel ocenění a potvrdí jiný schvalovatel. Nevratný `hard_lock_date` se nastavuje
ručně až po auditu účetní závěrky (standardní průvodce Odoo).
"""

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

APPROVER = "investra_entity.group_valuation_approver"
# Výjimku a snížení zámku u fondové knihy smí provést jen tento modul.
_ALLOW = object()


def _allowed(env):
    return env.context.get("investra_lock_exception") is _ALLOW


def _fund_books(env, companies):
    return env["investra.fund"].sudo().search([("company_id", "in", companies.ids)]).company_id


def _last_published(env, company):
    return env["investra.valuation"].sudo().search([
        ("company_id", "=", company.id), ("state", "=", "published"),
    ], order="date desc", limit=1)


class ResCompany(models.Model):
    _inherit = "res.company"

    def write(self, vals):
        if "fiscalyear_lock_date" in vals and not _allowed(self.env):
            new = fields.Date.to_date(vals["fiscalyear_lock_date"])
            for company in _fund_books(self.env, self):
                published = _last_published(self.env, company)
                if published and (not new or new < published.date):
                    raise UserError(self.env._(
                        "Zámek knihy %(company)s nejde snížit pod datum zveřejněného ocenění %(valuation)s. "
                        "Pro opravu požádejte o výjimku z uzamčení.",
                        company=company.name, valuation=published.display_name,
                    ))
        # Odoo při změně zámku znovu zakládá aktivní výjimky; to je povolené.
        return super(ResCompany, self.with_context(investra_lock_exception=_ALLOW)).write(vals)


class AccountLockException(models.Model):
    _inherit = "account.lock_exception"

    @api.model_create_multi
    def create(self, vals_list):
        if not _allowed(self.env):
            companies = self.env["res.company"].browse(
                [vals.get("company_id", self.env.company.id) for vals in vals_list]
            )
            if _fund_books(self.env, companies):
                raise UserError(self.env._(
                    "Výjimku z uzamčení fondové knihy zakládá jen žádost v Investra (Nastavení → Auditní stopa)."
                ))
        return super().create(vals_list)


class InvestraLockExceptionRequest(models.Model):
    _name = "investra.lock.exception.request"
    _description = "Žádost o výjimku z uzamčení"
    _order = "create_date desc, id desc"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True, string="Účetní kniha",
    )
    user_id = fields.Many2one("res.users", required=True, string="Pro uživatele")
    lock_date = fields.Date(
        required=True, string="Dočasně uzamčeno do",
        help="Po dobu výjimky může uživatel účtovat doklady s datem po tomto dni.",
    )
    end_datetime = fields.Datetime(required=True, string="Platí do")
    reason = fields.Text(required=True, string="Důvod")
    state = fields.Selection(
        [("draft", "Čeká na potvrzení"), ("active", "Potvrzeno"), ("rejected", "Zamítnuto"), ("revoked", "Odvoláno")],
        default="draft", required=True, readonly=True, string="Stav",
    )
    requested_by = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True, readonly=True, string="Požádal",
    )
    confirmed_by = fields.Many2one("res.users", readonly=True, string="Potvrdil")
    confirmed_at = fields.Datetime(readonly=True, string="Potvrzeno dne")
    exception_id = fields.Many2one("account.lock_exception", readonly=True, string="Výjimka Odoo")

    def _require_approver(self):
        if not self.env.su and not self.env.user.has_group(APPROVER):
            raise AccessError(self.env._("Výjimku z uzamčení řeší jen skupina schvalování ocenění."))

    @api.model_create_multi
    def create(self, vals_list):
        self._require_approver()
        for vals in vals_list:
            vals.pop("requested_by", None)
            vals["state"] = "draft"
        records = super().create(vals_list)
        records._validate()
        return records

    def write(self, vals):
        if not self.env.su and self.filtered(lambda r: r.state != "draft"):
            raise UserError(self.env._("Vyřízenou žádost nejde měnit."))
        result = super().write(vals)
        self._validate()
        return result

    def _validate(self):
        for record in self:
            company = record.company_id.sudo()
            if company not in _fund_books(self.env, company):
                raise UserError(self.env._("Výjimka se žádá jen pro fondovou knihu."))
            if not company.fiscalyear_lock_date or record.lock_date >= company.fiscalyear_lock_date:
                raise UserError(self.env._("Datum musí být před současným zámkem knihy (%s).", company.fiscalyear_lock_date))
            if company.hard_lock_date and record.lock_date < company.hard_lock_date:
                raise UserError(self.env._(
                    "Období do %s je nevratně uzamčené (po auditu); výjimka ho neotevře.", company.hard_lock_date
                ))
            if record.end_datetime <= fields.Datetime.now():
                raise UserError(self.env._("Konec výjimky musí být v budoucnosti."))

    def action_confirm(self):
        self._require_approver()
        for record in self:
            if record.state != "draft":
                raise UserError(self.env._("Potvrdit lze jen čekající žádost."))
            if record.requested_by == self.env.user:
                raise UserError(self.env._("Žádost musí potvrdit jiný schvalovatel než ten, kdo o ni požádal."))
            record._validate()
            exception = self.env["account.lock_exception"].sudo().with_context(investra_lock_exception=_ALLOW).create({
                "company_id": record.company_id.id,
                "user_id": record.user_id.id,
                "fiscalyear_lock_date": record.lock_date,
                "end_datetime": record.end_datetime,
                "reason": f"{record.reason} (žádost {record.id}, požádal {record.requested_by.name}, "
                          f"potvrdil {self.env.user.name})",
            })
            record.sudo().write({
                "state": "active", "exception_id": exception.id,
                "confirmed_by": self.env.user.id, "confirmed_at": fields.Datetime.now(),
            })
        return True

    def action_reject(self):
        self._require_approver()
        if self.filtered(lambda r: r.state != "draft"):
            raise UserError(self.env._("Zamítnout lze jen čekající žádost."))
        self.sudo().state = "rejected"
        return True

    def action_revoke(self):
        """Předčasné ukončení výjimky, např. po dokončení opravy."""
        self._require_approver()
        for record in self.filtered(lambda r: r.state == "active"):
            record.exception_id.sudo().action_revoke()
            record.sudo().state = "revoked"
        return True
