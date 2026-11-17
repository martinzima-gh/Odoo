from datetime import date

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestApprovalMatrix(NavCase):
    """Schvalovací matice pro celou aplikaci (rozhodnutí 2026-11-11, zjednodušení 2026-11-17, ZJ-01).

    Automatické testy běží s výchozí maticí (druhá osoba jako dřív) a tady i bez druhé osoby. Uživatelé mají
    testové role se stejným chováním jako skupiny před ZJ-01 (`investra_fund/tests/common.py`).
    Rok 2041 je pro kurzy jen těchto testů.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        self.day = date(2027, 1, 31)
        self.Matrix = self.env["investra.approval.matrix"]
        self.Log = self.env["investra.approval.log"]

    def matrix(self, activity, second_person="no", steps=None, role=None):
        vals = {"activity": activity, "second_person": second_person}
        if steps:
            vals["step_ids"] = [(0, 0, {"sequence": i, "name": name, "role_id": role.id if role else False})
                                for i, name in enumerate(steps)]
        return self.Matrix.create(vals)

    def check(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code)

    def logs(self, record):
        return self.Log.search([("res_model", "=", record._name), ("res_id", "=", record.id)])

    def confirmed(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        return valuation

    # --- schválení ocenění ----------------------------------------------------------------------

    def test_choosing_no_second_person_clears_approvers(self):
        """Volba „Ne – stačí jeden člověk“ smaže kroky schvalovatelů a počet osob je 1 (2026-11-12, zkouška v UI)."""
        form = Form(self.Matrix)
        form.activity = "valuation_approve"
        form.second_person = "yes"
        with form.step_ids.new() as step:
            step.name = "Schválení"
        self.assertEqual(form.persons, 2)
        form.second_person = "no"
        self.assertEqual((len(form.step_ids), form.persons), (0, 1))

    def test_default_matrix_keeps_second_person(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.assertEqual(self.check(valuation, "matrix_valuation").status, "ok")
        valuation.action_submit()
        with self.assertRaises(UserError):
            valuation.action_approve()
        valuation.with_user(self.approver).action_approve()
        self.assertEqual(valuation.state, "approved")
        self.assertFalse(self.logs(valuation))

    def test_one_person_valuation_is_logged_and_shown(self):
        self.matrix("valuation_approve")
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.assertEqual(self.check(valuation, "matrix_valuation").status, "warning")
        valuation.action_submit()
        valuation.action_approve()
        self.assertEqual(valuation.state, "approved")
        self.assertEqual(valuation.approval_ids.user_id, self.preparer)
        self.assertEqual(self.logs(valuation).user_id, self.preparer)
        valuation.action_post()
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        valuation.with_user(self.approver).action_publish()
        following = self.valuation(self.fund, date(2027, 2, 28))
        following.action_compute()
        check = self.check(following, "second_person")
        self.assertEqual(check.status, "warning")
        self.assertIn("Schválení ocenění", check.detail)
        # Zveřejnění podle výchozího řádku (chování před maticí) je jen v záznamu, kontrola ho neukazuje.
        self.assertTrue(self.logs(valuation).filtered(lambda l: l.activity == "valuation_publish"))
        self.assertNotIn("Zveřejnění", check.detail)

    def test_matrix_change_is_shown_in_next_valuation(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        valuation.with_user(self.approver).action_publish()
        self.matrix("valuation_return", "yes")
        following = self.valuation(self.fund, date(2027, 2, 28))
        following.action_compute()
        check = self.check(following, "matrix_change")
        self.assertEqual(check.status, "warning")
        self.assertIn("Vrácení a storno ocenění", check.detail)
        self.assertEqual(self.check(following, "second_person").status, "ok")

    def test_step_with_role_only(self):
        """Krok s rolí (ZJ-01): schválí jen člen té role s příznakem Schvaluje, ne jiný schvalovatel."""
        board = self.env["investra.role"].create({
            "name": "Vedení", "access_level": "read", "user_ids": [(6, 0, self.approver2.ids)],
            "line_ids": [(0, 0, {"activity": "valuation_approve", "perform": False, "approve": True})],
        })
        self.matrix("valuation_approve", "yes", steps=["Vedení"], role=board)
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        self.assertEqual((valuation.approval_ids.role_id, valuation.approval_ids.min_role), (board, "Vedení"))
        with self.assertRaises(AccessError):
            valuation.with_user(self.approver).action_approve()
        valuation.with_user(self.approver2).action_approve()
        self.assertEqual(valuation.state, "approved")

    def test_matrix_has_no_fund_or_manager(self):
        """ZJ-01: matice je jedna pro celou aplikaci; pro činnost a den smí být jen jeden řádek."""
        for name in ("manager_id", "fund_id", "performer_role", "performer_user_ids", "company_id"):
            self.assertNotIn(name, self.Matrix._fields)
        self.matrix("valuation_publish", "yes")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.matrix("valuation_publish", "no")

    # --- řádky matice ----------------------------------------------------------------------------

    def test_valid_row_is_superseded_not_changed(self):
        row = self.env.ref("investra_fund.matrix_default_valuation_publish")
        with self.assertRaises(UserError):
            row.with_user(self.admin_user).write({"second_person": "yes"})
        with self.assertRaises(AccessError):
            self.Matrix.with_user(self.preparer).create({"activity": "valuation_publish", "second_person": "no"})
        # ZJ-02: ani schvalovatel matici nemění, jen úroveň Správa.
        with self.assertRaises(AccessError):
            self.Matrix.with_user(self.approver).create({"activity": "valuation_publish", "second_person": "no"})
        with self.assertRaises(UserError):
            self.Matrix.with_user(self.admin_user).create({
                "activity": "valuation_publish", "second_person": "no", "valid_from": "2020-01-01",
            })
        new = self.Matrix.with_user(self.admin_user).create({"activity": "valuation_publish", "second_person": "yes"})
        self.assertFalse(new.step_ids.role_id)
        self.assertEqual(self.Matrix._rule("valuation_publish").persons, 2)
        self.assertEqual(row.second_person, "no")

    # --- MN-18: výchozí řádky z modulu a upozornění na čekající žádost ----------------------------

    def _builtin(self, activity="valuation_publish"):
        row = self.Matrix.search([("activity", "=", activity), ("builtin", "=", True)], limit=1)
        self.assertTrue(row)
        return row

    def test_builtin_row_has_own_error(self):
        row = self._builtin()
        for call in (lambda: row.with_user(self.admin_user).write({"note": "x"}),
                     lambda: row.with_user(self.admin_user).unlink(),
                     lambda: row.step_ids.with_user(self.admin_user).unlink() if row.step_ids else row.with_user(self.admin_user).write({"valid_from": "2030-01-01"})):
            with self.assertRaises(UserError) as ctx:
                call()
            self.assertIn("Výchozí řádek z modulu", str(ctx.exception))
        self.assertTrue(row.exists())

    def test_builtin_row_sudo_unchanged(self):
        row = self._builtin()
        row.sudo().write({"note": "sudo"})
        self.assertEqual(row.note, "sudo")

    def test_custom_row_with_later_valid_from_allowed(self):
        new = self.Matrix.with_user(self.admin_user).create({"activity": "valuation_publish", "second_person": "no"})
        self.assertFalse(new.builtin)
        self.assertEqual(new.valid_from, fields.Date.context_today(new))

    def test_custom_valid_row_keeps_original_error(self):
        row = self.matrix("valuation_publish", "no")
        row.sudo().valid_from = date(2020, 1, 1)
        with self.assertRaises(UserError) as ctx:
            row.with_user(self.admin_user).write({"note": "x"})
        self.assertIn("Platný řádek matice", str(ctx.exception))
        self.assertNotIn("Výchozí řádek z modulu", str(ctx.exception))

    def test_pending_request_shown_on_record(self):
        self.matrix("valuation_publish", "yes")
        valuation = self.confirmed()
        self.assertFalse(valuation.pending_request_id)
        self.assertFalse(valuation.action_open_pending_request())
        action = valuation.with_user(self.approver).action_publish()
        request = self.env["investra.approval.request"].browse(action["res_id"])
        valuation.invalidate_recordset(["pending_request_id"])
        self.assertEqual(valuation.pending_request_id, request)
        self.assertEqual(valuation.action_open_pending_request()["res_id"], request.id)
        request.with_user(self.approver2).action_approve()
        valuation.invalidate_recordset(["pending_request_id"])
        self.assertFalse(valuation.pending_request_id)

    # --- jednorázové úkony přes žádost ------------------------------------------------------------

    def test_publish_with_four_eyes_goes_through_request(self):
        self.matrix("valuation_publish", "yes")
        valuation = self.confirmed()
        action = valuation.with_user(self.approver).action_publish()
        self.assertEqual(valuation.state, "confirmed")
        request = self.env["investra.approval.request"].browse(action["res_id"])
        self.assertEqual(request.state, "pending")
        with self.assertRaises(UserError):
            request.with_user(self.approver).action_approve()
        with self.assertRaises(AccessError):
            request.with_user(self.preparer).action_approve()
        request.with_user(self.approver2).action_approve()
        self.assertEqual(request.state, "done")
        self.assertEqual(valuation.state, "published")
        self.assertEqual(self.fund.company_id.fiscalyear_lock_date, self.day)

    def test_preparer_cannot_request_publish(self):
        self.matrix("valuation_publish", "yes")
        valuation = self.confirmed()
        with self.assertRaises(AccessError):
            valuation.with_user(self.preparer).action_publish()

    def test_return_with_four_eyes_through_wizard(self):
        self.matrix("valuation_return", "yes")
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        wizard = self.env["investra.valuation.return.wizard"].with_user(self.approver).create({
            "valuation_id": valuation.id, "mode": "return", "reason": "Chybí faktura",
        })
        action = wizard.action_confirm()
        self.assertEqual(action["res_model"], "investra.approval.request")
        self.assertEqual(valuation.state, "submitted")
        request = self.env["investra.approval.request"].browse(action["res_id"])
        request.with_user(self.approver2).action_reject()
        self.assertEqual(request.state, "rejected")
        self.assertEqual(valuation.state, "submitted")
        action = wizard.action_confirm()
        self.env["investra.approval.request"].browse(action["res_id"]).with_user(self.approver2).action_approve()
        self.assertEqual(valuation.state, "returned")
        self.assertTrue(valuation.search([("fund_id", "=", self.fund.id), ("version", "=", 2)]))

    def test_manual_rate_with_four_eyes(self):
        self.matrix("manual_rate", "yes")
        self.rate("2041-01-02", 25)
        Rate = self.env["investra.rate"].sudo()
        request = self.env["investra.rate"].with_user(self.approver).create_manual(
            "override", "cnb", self.eur, date(2041, 1, 2), 1, 26, "Chyba zdroje",
        )
        self.assertEqual(request._name, "investra.approval.request")
        self.assertEqual(Rate._effective("cnb", self.eur, date(2041, 1, 2)).rate, 25)
        request.with_user(self.approver2).action_approve()
        effective = Rate._effective("cnb", self.eur, date(2041, 1, 2))
        self.assertEqual((effective.rate, effective.origin), (26, "override"))

    # --- záznamy se schválením: cena, výjimka, ruční kategorie --------------------------------------

    def instrument(self, kind="equity", currency=None):
        return self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Nástroj {kind}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref(f"investra_instruments.type_{kind}").id,
        }, self.fund))

    def test_price_one_person_is_logged(self):
        self.matrix("price_approve")
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "instrument_id": self.instrument().id, "fund_id": self.fund.id, "date": self.day, "price": 10, "source": "test",
        })
        price.with_user(self.preparer).action_approve()
        self.assertEqual(price.state, "approved")
        self.assertEqual(self.logs(price).user_id, self.preparer)

    def test_price_steps_need_two_other_people(self):
        self.matrix("price_approve", "steps", steps=["Kontrola", "Vedení"])
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "instrument_id": self.instrument().id, "fund_id": self.fund.id, "date": self.day, "price": 10, "source": "test",
        })
        price.with_user(self.approver).action_approve()
        self.assertEqual(price.state, "draft")
        with self.assertRaises(UserError):
            price.with_user(self.approver).action_approve()
        price.with_user(self.approver2).action_approve()
        self.assertEqual(price.state, "approved")

    def test_classification_override_needs_request(self):
        self.matrix("classification_override", "yes")
        bond = self.instrument("bond")
        Classification = self.env["investra.portfolio.classification"].with_user(self.preparer)
        values = {"portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id, "valid_from": "2000-01-01"}
        with self.assertRaises(UserError):
            Classification.create({**values, "category_override": "fvoci", "override_note": "Metodik"})
        record = Classification.create(values)
        action = record.request_category_override("fvoci", "Metodik: strategická držba")
        self.assertFalse(record.category_override)
        request = self.env["investra.approval.request"].browse(action["res_id"])
        with self.assertRaises(UserError):
            request.with_user(self.preparer).action_approve()
        request.with_user(self.approver).action_approve()
        self.assertEqual((record.category_override, record.ifrs9_category), ("fvoci", "fvoci"))

    def test_classification_override_one_person_is_logged(self):
        bond = self.instrument("bond")
        record = self.env["investra.portfolio.classification"].with_user(self.preparer).create({
            "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id, "valid_from": "2000-01-01",
            "category_override": "fvoci", "override_note": "Metodik",
        })
        self.assertEqual(self.logs(record).activity, "classification_override")
