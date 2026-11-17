"""Role Investry (rozhodnutí 2026-11-17 „Role a schvalovací matice zjednodušeny“, úkol ZJ-01).

Roli zakládá uživatel s úrovní Správa a skládá ji z činností schvalovací matice s příznaky Provádí a Schvaluje;
uživatel má rolí více. Skupiny Odoo se uživateli odvozují z jeho rolí (ručně se nenastavují):

- úroveň Čtení → `investra_entity.group_investra_read`,
- Zpracování → `investra_entity.group_valuation_preparer`,
- Správa → `investra_entity.group_investra_admin` (implikuje Zpracování),
- příznak Schvaluje v některé roli → `investra_entity.group_valuation_approver`.

Synchronizace mění jen tyto skupiny (a skupinu účtování, viz níže); ostatní skupiny uživatele (účetnictví Odoo, správa systému) nechává.

Příznak role „Účtuje ručně v hlavní knize“ (rozhodnutí 2026-11-17 po ZJ-01) odvozuje `account.group_account_user`.
Odebere se jen tehdy, když ho nedává jiná role uživatele a uživatel není správce systému ani správce účetnictví
(rozhodnutí 2026-11-17 „Ruční účtování: správci“). Pozor: v Odoo 20 ho žádná z těchto skupin neimplikuje;
správce si ho jen ponechá, má-li ho přidělený.
"""

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .approval_matrix import ACTIVITIES

ACCESS_LEVELS = [("read", "Čtení"), ("process", "Zpracování"), ("admin", "Správa")]
LEVEL_RANK = {"read": 1, "process": 2, "admin": 3}
READ = "investra_entity.group_investra_read"
PREPARER = "investra_entity.group_valuation_preparer"
APPROVER = "investra_entity.group_valuation_approver"
ADMIN = "investra_entity.group_investra_admin"
ACCOUNTING = "account.group_account_user"
MANAGED_GROUPS = (READ, PREPARER, APPROVER, ADMIN, ACCOUNTING)


class InvestraRole(models.Model):
    _name = "investra.role"
    _inherit = ["mail.thread"]
    _description = "Role Investry"
    _order = "name, id"

    name = fields.Char(required=True, tracking=True, string="Název")
    access_level = fields.Selection(
        ACCESS_LEVELS, required=True, default="read", tracking=True, string="Úroveň přístupu",
        help="Čtení: jen čte. Zpracování: zpracovává ocenění, obchody a pohyby. Správa: navíc zakládá a mění role.",
    )
    manual_posting = fields.Boolean(
        tracking=True, string="Účtuje ručně v hlavní knize",
        help="Člen role smí zadávat ruční doklady v hlavní knize Odoo mimo náhled zaúčtování a schvalovací matici "
             "(skupina Odoo „Účetnictví“). Zapněte jen rolím, které to smějí.",
    )
    line_ids = fields.One2many("investra.role.line", "role_id", copy=True, string="Činnosti")
    user_ids = fields.Many2many(
        "res.users", "investra_role_user_rel", "role_id", "user_id", tracking=True, string="Uživatelé",
        domain=[("share", "=", False)],
    )
    active = fields.Boolean(default=True, tracking=True, string="Aktivní")
    note = fields.Text(string="Poznámka")

    _name_uniq = models.Constraint("UNIQUE (name)", "Role s tímto názvem už existuje.")

    # --- oprávnění ---------------------------------------------------------------------------------

    @api.model
    def _check_admin(self):
        """Role zakládá a mění jen úroveň Správa nebo správce systému."""
        if self.env.su or self.env.user.has_group(ADMIN) or self.env.user.has_group("base.group_system"):
            return
        raise AccessError(self.env._("Role zakládá a mění jen uživatel s úrovní přístupu Správa."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_admin()
        roles = super().create(vals_list)
        roles._sync_users(roles.user_ids)
        return roles

    def write(self, vals):
        self._check_admin()
        before = self.with_context(active_test=False).user_ids
        result = super().write(vals)
        if {"user_ids", "access_level", "active", "line_ids", "manual_posting"} & set(vals):
            self._sync_users(before | self.user_ids)
        return result

    def unlink(self):
        self._check_admin()
        users = self.with_context(active_test=False).user_ids
        result = super().unlink()
        self._sync_users(users)
        return result

    # --- skupiny Odoo ------------------------------------------------------------------------------

    @api.model
    def _groups_for(self, roles):
        """Skupiny Investry, které uživateli s danými (aktivními) rolemi patří."""
        rank = max((LEVEL_RANK[r.access_level] for r in roles), default=0)
        wanted = set()
        if rank >= 1:
            wanted.add(READ)
        if rank >= 2:
            wanted.add(PREPARER)
        if rank >= 3:
            wanted.add(ADMIN)
        if any(roles.line_ids.mapped("approve")):
            wanted.add(APPROVER)
        if any(roles.mapped("manual_posting")):
            wanted.add(ACCOUNTING)
        return wanted

    @api.model
    def _sync_users(self, users):
        """Odvodí skupiny Investry uživatelům z jejich aktivních rolí; mění jen MANAGED_GROUPS."""
        users = users.exists().filtered(lambda u: not u.share)
        if not users:
            return
        groups = {xmlid: self.env.ref(xmlid) for xmlid in MANAGED_GROUPS}
        Role = self.sudo().with_context(active_test=True)
        for user in users.sudo():
            wanted = self._groups_for(Role.search([("user_ids", "in", user.id)]))
            keep_accounting = user.has_group("base.group_system") or user.has_group("account.group_account_manager")
            commands = [
                (4 if xmlid in wanted else 3, group.id) for xmlid, group in groups.items()
                if xmlid in wanted or not (xmlid == ACCOUNTING and keep_accounting)
            ]
            user.write({"group_ids": commands})


class InvestraRoleLine(models.Model):
    _name = "investra.role.line"
    _description = "Činnost v roli"
    _order = "role_id, activity"

    role_id = fields.Many2one("investra.role", required=True, ondelete="cascade", index=True, string="Role")
    activity = fields.Selection(ACTIVITIES, required=True, string="Činnost")
    perform = fields.Boolean(default=True, string="Provádí")
    approve = fields.Boolean(string="Schvaluje")

    _activity_uniq = models.Constraint("UNIQUE (role_id, activity)", "Činnost je v roli dvakrát.")

    @api.constrains("perform", "approve")
    def _check_flags(self):
        for line in self:
            if not (line.perform or line.approve):
                raise ValidationError(self.env._("Činnost v roli musí mít aspoň příznak Provádí nebo Schvaluje."))

    @api.model_create_multi
    def create(self, vals_list):
        self.env["investra.role"]._check_admin()
        lines = super().create(vals_list)
        lines.role_id._sync_users(lines.role_id.user_ids)
        return lines

    def write(self, vals):
        self.env["investra.role"]._check_admin()
        roles = self.role_id
        result = super().write(vals)
        roles |= self.role_id
        roles._sync_users(roles.user_ids)
        return result

    def unlink(self):
        self.env["investra.role"]._check_admin()
        roles = self.role_id
        result = super().unlink()
        roles.exists()._sync_users(roles.exists().user_ids)
        return result


class ResUsers(models.Model):
    _inherit = "res.users"

    investra_role_ids = fields.Many2many(
        "investra.role", "investra_role_user_rel", "user_id", "role_id", string="Role Investry",
        help="Skupiny Investry se odvozují z rolí; ručně se nenastavují.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("investra_role_ids") for vals in vals_list):
            self.env["investra.role"]._check_admin()
        users = super().create(vals_list)
        with_roles = users.filtered("investra_role_ids")
        if with_roles:
            self.env["investra.role"]._sync_users(with_roles)
        return users

    def write(self, vals):
        if "investra_role_ids" in vals:
            self.env["investra.role"]._check_admin()
        result = super().write(vals)
        if "investra_role_ids" in vals:
            self.env["investra.role"]._sync_users(self)
        return result
