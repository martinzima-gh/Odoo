"""Role Investry a matice podle rolí (ZJ-01, rozhodnutí 2026-11-17)."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.investra_fund.zj01_migration import merge_matrix_rows, role_codes_to_text

READ = "investra_entity.group_investra_read"
PREPARER = "investra_entity.group_valuation_preparer"
APPROVER = "investra_entity.group_valuation_approver"
ADMIN = "investra_entity.group_investra_admin"


@tagged("post_install", "-at_install")
class TestRole(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env["res.users"]
        base = cls.env.ref("base.group_user")

        def user(login):
            return Users.create({"name": login, "login": login, "group_ids": [(6, 0, base.ids)]})

        cls.alice, cls.bob, cls.carol = user("zj_alice"), user("zj_bob"), user("zj_carol")
        cls.Role = cls.env["investra.role"]
        cls.Matrix = cls.env["investra.approval.matrix"]
        cls.record = cls.env["res.partner"].create({"name": "Záznam ke schválení"})

    def role(self, name, level="process", users=(), **lines):
        """lines: činnost=„p“ (Provádí), „a“ (Schvaluje) nebo „pa“."""
        return self.Role.create({
            "name": name, "access_level": level, "user_ids": [(6, 0, [u.id for u in users])],
            "line_ids": [(0, 0, {"activity": a, "perform": "p" in f, "approve": "a" in f}) for a, f in lines.items()],
        })

    def groups(self, user):
        return {xmlid for xmlid in (READ, PREPARER, APPROVER, ADMIN) if user.has_group(xmlid)}

    # --- skupiny odvozené z rolí ---------------------------------------------------------------------

    def test_groups_follow_roles(self):
        accountant = self.role("Účetní", "process", [self.alice], price_approve="p")
        self.assertEqual(self.groups(self.alice), {READ, PREPARER})
        checker = self.role("Kontrola", "read", [self.alice], price_approve="a")
        self.assertEqual(self.groups(self.alice), {READ, PREPARER, APPROVER})
        accountant.user_ids = [(3, self.alice.id)]
        self.assertEqual(self.groups(self.alice), {READ, APPROVER})
        checker.line_ids.perform = True
        checker.line_ids.approve = False
        self.assertEqual(self.groups(self.alice), {READ})
        checker.active = False
        self.assertEqual(self.groups(self.alice), set())
        checker.active = True
        checker.access_level = "admin"
        self.assertEqual(self.groups(self.alice), {READ, PREPARER, ADMIN})
        checker.unlink()
        self.assertEqual(self.groups(self.alice), set())

    def test_groups_follow_user_roles_field(self):
        role = self.role("Schvalovatel", "process", price_approve="pa")
        self.bob.investra_role_ids = [(4, role.id)]
        self.assertEqual(self.groups(self.bob), {READ, PREPARER, APPROVER})
        self.bob.investra_role_ids = [(5,)]
        self.assertEqual(self.groups(self.bob), set())

    def test_sync_keeps_other_groups(self):
        readonly = self.env.ref("account.group_account_readonly")
        self.alice.group_ids |= readonly
        role = self.role("Čtenář", "read", [self.alice])
        role.user_ids = [(5,)]
        self.assertIn(readonly, self.alice.group_ids)
        self.assertTrue(self.alice.has_group("base.group_user"))

    def test_only_admin_level_manages_roles(self):
        self.role("Účetní", "process", [self.alice], price_approve="p")
        with self.assertRaises(AccessError):
            self.Role.with_user(self.alice).create({"name": "Vlastní", "access_level": "admin"})
        self.role("Správce", "admin", [self.bob])
        created = self.Role.with_user(self.bob).create({"name": "Vlastní", "access_level": "read"})
        created.with_user(self.bob).user_ids = [(4, self.carol.id)]
        self.assertEqual(self.groups(self.carol), {READ})

    def test_line_needs_a_flag(self):
        with self.assertRaises(ValidationError):
            self.role("Prázdná", price_approve="")

    # --- matice podle rolí --------------------------------------------------------------------------

    def test_performer_needs_role_with_activity(self):
        self.role("Účetní", "process", [self.alice], price_approve="p")
        rule = self.Matrix._rule("price_approve")
        rule.check_performer(self.env(user=self.alice))
        with self.assertRaises(AccessError):
            self.Matrix._rule("manual_rate").check_performer(self.env(user=self.alice))
        with self.assertRaises(AccessError):
            rule.check_performer(self.env(user=self.bob))

    def test_approver_differs_from_requester(self):
        # Výchozí matice ceny: čtyři oči (BUILTIN beze změny).
        self.assertEqual(self.Matrix._rule("price_approve").persons, 2)
        self.role("Účetní", "process", [self.alice], price_approve="p")
        self.role("Schvalovatel", "read", [self.alice, self.bob], price_approve="a")
        Matrix = self.Matrix.with_user(self.alice).sudo(False)
        with self.assertRaises(UserError):
            Matrix._approve_step("price_approve", self.record, self.alice)
        with self.assertRaises(AccessError):
            self.Matrix.with_user(self.carol)._approve_step("price_approve", self.record, self.alice)
        self.assertTrue(self.Matrix.with_user(self.bob)._approve_step("price_approve", self.record, self.alice))

    def test_steps_with_role(self):
        board = self.role("Vedení", "read", [self.carol], price_approve="a")
        self.role("Schvalovatel", "read", [self.bob], price_approve="a")
        self.Matrix.create({"activity": "price_approve", "second_person": "steps", "step_ids": [
            (0, 0, {"sequence": 1, "name": "Kontrola"}),
            (0, 0, {"sequence": 2, "name": "Vedení", "role_id": board.id}),
        ]})
        rule = self.Matrix._rule("price_approve")
        self.assertEqual((rule.persons, rule.steps[1].role), (3, board))
        self.assertFalse(self.Matrix.with_user(self.bob)._approve_step("price_approve", self.record, self.alice))
        # Druhý krok má roli Vedení: schvalovatel bez ní neprojde, i kdyby nebyl předchozím schvalovatelem.
        self.role("Jiný", "read", [self.alice], price_approve="a")
        with self.assertRaises(AccessError):
            self.Matrix.with_user(self.alice)._approve_step("price_approve", self.record, self.env["res.users"])
        self.assertTrue(self.Matrix.with_user(self.carol)._approve_step("price_approve", self.record, self.alice))

    def test_request_line_keeps_role(self):
        board = self.role("Vedení", "read", [self.carol], manual_rate="a")
        self.role("Kurzy", "process", [self.alice], manual_rate="p")
        self.Matrix.create({"activity": "manual_rate", "second_person": "yes",
                            "step_ids": [(0, 0, {"name": "Vedení", "role_id": board.id})]})
        request = self.Matrix.with_user(self.alice)._gate("manual_rate", self.record, "write", {"comment": "x"})
        self.assertEqual((request.line_ids.role_id, request.line_ids.role), (board, "Vedení"))
        self.role("Jiný", "read", [self.bob], manual_rate="a")
        with self.assertRaises(AccessError):
            request.with_user(self.bob).action_approve()

    # --- migrace ZJ-01 --------------------------------------------------------------------------------

    def _old_schema(self):
        """Stav před ZJ-01 v této transakci: sloupce obhospodařovatele a fondu, bez unikátnosti (činnost, den)."""
        cr = self.env.cr
        cr.execute("ALTER TABLE investra_approval_matrix ADD COLUMN manager_id int, ADD COLUMN fund_id int")
        cr.execute("""SELECT conname FROM pg_constraint
                       WHERE conrelid = 'investra_approval_matrix'::regclass AND contype = 'u'""")
        for (name,) in cr.fetchall():
            cr.execute(f'ALTER TABLE investra_approval_matrix DROP CONSTRAINT "{name}"')

    def _row(self, activity, day, manager=None):
        self.env.cr.execute("""
            INSERT INTO investra_approval_matrix (activity, valid_from, second_person, manager_id)
            VALUES (%s, %s, 'no', %s) RETURNING id""", (activity, day, manager))
        return self.env.cr.fetchone()[0]

    def test_migration_manager_rows_become_global(self):
        self._old_schema()
        global_row = self._row("trade_reverse", "2026-11-16")
        manager_row = self._row("trade_reverse", "2026-11-16", manager=1)
        other = self._row("manual_rate", "2026-11-16", manager=1)
        log = self.env["investra.approval.log"].sudo().create({
            "activity": "trade_reverse", "matrix_id": global_row, "user_id": self.alice.id,
            "res_model": "res.partner", "res_id": self.record.id,
        })
        with mute_logger("odoo.addons.investra_fund.zj01_migration"):
            messages = merge_matrix_rows(self.env.cr)
        self.assertEqual(len(messages), 2, messages)
        self.assertIn(f"ponechán novější id {manager_row}", messages[0])
        self.env.cr.execute("SELECT id FROM investra_approval_matrix WHERE id IN %s ORDER BY id",
                            ((global_row, manager_row, other),))
        self.assertEqual([r[0] for r in self.env.cr.fetchall()], [manager_row, other])
        self.env.cr.execute("SELECT count(*) FROM investra_approval_matrix WHERE manager_id IS NOT NULL")
        self.assertEqual(self.env.cr.fetchone()[0], 0)
        log.invalidate_recordset()
        self.assertEqual(log.matrix_id.id, manager_row)

    def test_migration_stops_on_fund_rows(self):
        self._old_schema()
        self.env.cr.execute("UPDATE investra_approval_matrix SET fund_id = 1 WHERE id = %s",
                            (self._row("trade_reverse", "2026-11-20"),))
        with self.assertRaises(RuntimeError):
            merge_matrix_rows(self.env.cr)

    def test_migration_role_codes_to_text(self):
        self.env.cr.execute("ALTER TABLE investra_approval_matrix_step ADD COLUMN old_role varchar")
        row = self.Matrix.create({"activity": "valuation_publish", "second_person": "yes"})
        self.env.cr.execute("UPDATE investra_approval_matrix_step SET old_role = 'approver' WHERE matrix_id = %s", (row.id,))
        with mute_logger("odoo.addons.investra_fund.zj01_migration"):
            self.assertEqual(role_codes_to_text(self.env.cr, "investra_approval_matrix_step", "old_role"), 1)
        self.env.cr.execute("SELECT old_role FROM investra_approval_matrix_step WHERE matrix_id = %s", (row.id,))
        self.assertEqual(self.env.cr.fetchone()[0], "Schvalování ocenění")
