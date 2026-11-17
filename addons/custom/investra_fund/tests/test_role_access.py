"""ZJ-02: formuláře rolí, přístup podle úrovně, příznak ručního účtování, schvalování mezi ukázkovými rolemi."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.investra_fund.models.approval_matrix import ACTIVITIES

ACCOUNTING = "account.group_account_user"
ALL = [a for a, _label in ACTIVITIES]


@tagged("post_install", "-at_install")
class TestRoleAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Role, Users = cls.env["investra.role"], cls.env["res.users"]
        base = cls.env.ref("base.group_user")

        def role(name, level, manual, perform, approve):
            return Role.create({
                "name": name, "access_level": level, "manual_posting": manual,
                "line_ids": [(0, 0, {"activity": a, "perform": True, "approve": approve}) for a in (ALL if perform else [])],
            })

        cls.r_admin = role("T Admin", "admin", True, True, True)
        cls.r_acc = role("T Účetní", "process", True, True, False)
        cls.r_appr = role("T Schvalovatel", "process", True, True, True)
        cls.r_view = role("T Náhled", "read", False, False, False)

        def user(login, r):
            return Users.create({"name": login, "login": login, "group_ids": [(6, 0, base.ids)],
                                 "investra_role_ids": [(6, 0, r.ids)]})

        cls.admin, cls.ucetni, cls.schvalovatel, cls.view = (
            user("t_admin", cls.r_admin), user("t_ucetni", cls.r_acc), user("t_schvalovatel", cls.r_appr),
            user("t_view", cls.r_view))
        cls.Matrix = cls.env["investra.approval.matrix"]

    def test_manual_posting_group_follows_flag(self):
        self.assertTrue(self.ucetni.has_group(ACCOUNTING))
        self.assertTrue(self.schvalovatel.has_group(ACCOUNTING))
        self.assertFalse(self.view.has_group(ACCOUNTING))
        self.r_acc.manual_posting = False
        self.assertFalse(self.ucetni.has_group(ACCOUNTING))
        self.r_acc.manual_posting = True
        self.assertTrue(self.ucetni.has_group(ACCOUNTING))

    def test_manual_posting_kept_when_other_role_gives_it(self):
        self.ucetni.investra_role_ids = [(4, self.r_appr.id)]
        self.r_acc.manual_posting = False
        self.assertTrue(self.ucetni.has_group(ACCOUNTING))
        self.ucetni.investra_role_ids = [(3, self.r_appr.id)]
        self.assertFalse(self.ucetni.has_group(ACCOUNTING))

    def test_manual_posting_not_removed_from_system_admin(self):
        self.admin.group_ids |= self.env.ref("base.group_system")
        self.r_admin.manual_posting = False
        self.assertTrue(self.admin.has_group(ACCOUNTING))

    def test_view_writes_nothing(self):
        Role = self.env["investra.role"].with_user(self.view)
        with self.assertRaises(AccessError):
            Role.create({"name": "Cokoli", "access_level": "read"})
        with self.assertRaises(AccessError):
            self.r_view.with_user(self.view).write({"name": "Přejmenovat"})
        with self.assertRaises(AccessError):
            self.Matrix.with_user(self.view).create({"activity": "price_approve", "second_person": "no"})
        with self.assertRaises(AccessError):
            self.view.with_user(self.view).investra_role_ids = [(4, self.r_admin.id)]
        rule = self.Matrix._rule("manual_rate")
        with self.assertRaises(AccessError):
            rule.check_performer(self.env(user=self.view))

    def test_only_admin_changes_matrix_and_roles(self):
        for user in (self.ucetni, self.schvalovatel):
            with self.assertRaises(AccessError):
                self.Matrix.with_user(user).create({"activity": "price_approve", "second_person": "no"})
            with self.assertRaises(AccessError):
                self.env["investra.role"].with_user(user).create({"name": f"X {user.login}", "access_level": "read"})
        row = self.Matrix.with_user(self.admin).create({"activity": "price_approve", "second_person": "yes"})
        self.assertEqual(self.Matrix._rule("price_approve").persons, 2)
        self.assertTrue(row)

    def test_menu_roles_only_for_admin_level(self):
        menu = self.env.ref("investra_fund.menu_role")
        parent = self.env.ref("investra_fund.menu_setup_users")
        for user, visible in ((self.admin, True), (self.ucetni, False), (self.schvalovatel, False), (self.view, False)):
            ids = self.env["ir.ui.menu"].with_user(user)._visible_menu_ids()
            self.assertEqual((menu.id in ids, parent.id in ids), (visible, visible), user.login)

    def test_role_form(self):
        form = Form(self.env["investra.role"].with_user(self.admin))
        form.name = "T Z formuláře"
        form.access_level = "process"
        form.manual_posting = True
        with form.line_ids.new() as line:
            line.activity = "price_approve"
            line.perform = True
            line.approve = True
        form.user_ids.add(self.view)
        role = form.save()
        self.assertEqual((role.line_ids.activity, role.line_ids.approve), ("price_approve", True))
        self.assertTrue(self.view.has_group(ACCOUNTING))
        self.assertTrue(self.view.has_group("investra_entity.group_valuation_approver"))

    def test_user_form_tab_assigns_roles(self):
        # Uživatele upravuje správce nastavení (Správa + správce systému); ostatní záložku Role Investra nevidí.
        self.admin.group_ids |= self.env.ref("base.group_system")
        users = self.env["res.users"].with_user(self.admin)
        form = Form(users.browse(self.view.id), view="base.view_users_form")
        form.investra_role_ids.add(self.r_acc)
        form.save()
        self.assertTrue(self.view.has_group("investra_entity.group_valuation_preparer"))
        arch = self.env["res.users"].with_user(self.ucetni).get_view(self.env.ref("base.view_users_form").id)["arch"]
        self.assertNotIn("investra_role_ids", arch)

    def test_approver_confirms_accountant_request(self):
        self.Matrix.create({"activity": "manual_rate", "second_person": "yes"})
        record = self.env["res.partner"].create({"name": "Záznam ke schválení"})
        request = self.Matrix.with_user(self.ucetni)._gate("manual_rate", record, "message_post", {"body": "x"})
        self.assertEqual(request.state, "pending")
        with self.assertRaises(UserError):
            request.with_user(self.ucetni).action_approve()
        with self.assertRaises(AccessError):
            request.with_user(self.view).action_approve()
        request.with_user(self.schvalovatel).action_approve()
        self.assertEqual(request.state, "done")
