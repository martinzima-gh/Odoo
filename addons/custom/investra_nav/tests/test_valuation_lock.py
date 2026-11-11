from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


class LockCase(NavCase):
    """Společný fond, úpis a pomůcky pro testy zámku ocenění."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.a = self.cls(self.fund, "A")
        self.subscribe(self.a, "2027-01-01", 1000, 10)
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        self.day = date(2027, 1, 31)

    def submitted(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        return valuation

    def manual_move(self, day):
        company = self.fund.company_id
        journal = self.env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")], limit=1)
        accounts = self.env["account.account"].search([("company_ids", "in", company.id)], limit=2)
        return self.env["account.move"].with_company(company).create({
            "move_type": "entry", "journal_id": journal.id, "date": day,
            "line_ids": [
                (0, 0, {"account_id": accounts[0].id, "debit": 10, "credit": 0, "name": "x"}),
                (0, 0, {"account_id": accounts[1].id, "debit": 0, "credit": 10, "name": "x"}),
            ],
        })



@tagged("post_install", "-at_install")
class TestValuationLock(LockCase):
    """Zámek ocenění, vrstva 1: od Ke schválení do Potvrzeno nic s datem ≤ datu ocenění."""

    def test_computed_valuation_does_not_lock(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.common_result(self.fund, "r2", "2027-01-20", 5)
        self.subscribe(self.a, "2027-01-20", 100, 1)

    def test_event_in_locked_period_is_rejected_after_is_allowed(self):
        self.submitted()
        with self.assertRaisesRegex(UserError, "Ke schválení"):
            self.common_result(self.fund, "r2", "2027-01-31", 5)
        self.common_result(self.fund, "r3", "2027-02-01", 5)

    def test_manual_entry_cannot_be_posted_or_reset_in_locked_period(self):
        posted = self.manual_move("2027-01-20")
        posted.action_post()
        draft = self.manual_move("2027-01-25")
        self.submitted()
        with self.assertRaises(UserError):
            draft.action_post()
        with self.assertRaises(UserError):
            posted.button_draft()
        later = self.manual_move("2027-02-01")
        later.action_post()
        self.assertEqual(later.state, "posted")

    def test_movement_cannot_be_created_changed_or_deleted_in_locked_period(self):
        draft = self.env["investra.class.movement"].create({
            "class_id": self.a.id, "date": "2027-01-20", "movement_type": "subscription", "amount": 100, "units": 1,
        })
        self.submitted()
        with self.assertRaises(UserError):
            self.env["investra.class.movement"].create({
                "class_id": self.a.id, "date": "2027-01-31", "movement_type": "subscription", "amount": 100, "units": 1,
            })
        with self.assertRaises(UserError):
            draft.units = 2
        with self.assertRaises(UserError):
            draft.unlink()
        with self.assertRaises(UserError):
            draft._book()
        later = self.env["investra.class.movement"].create({
            "class_id": self.a.id, "date": "2027-02-01", "movement_type": "redemption", "amount": 50, "units": 0.5,
        })
        with self.assertRaises(UserError):
            later.date = "2027-01-30"
        later._book()
        self.assertTrue(later.event_id)

    def test_lock_holds_through_confirmed_and_return_releases_it(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        with self.assertRaises(UserError):
            self.subscribe(self.a, "2027-01-31", 100, 1)
        new = valuation.with_user(self.approver).action_reverse("Oprava úpisu")
        self.assertEqual(valuation.state, "reversed")
        self.subscribe(self.a, "2027-01-31", 100, 1)
        new.with_user(self.preparer).action_compute()
        self.assertAlmostEqual(self.result(new, "A").units, 11, places=6)

    def test_submitted_return_releases_lock(self):
        valuation = self.submitted()
        with self.assertRaises(UserError):
            self.subscribe(self.a, "2027-01-31", 100, 1)
        valuation.with_user(self.approver).action_return("Chybí úpis")
        self.subscribe(self.a, "2027-01-31", 100, 1)

    def test_other_fund_is_not_locked(self):
        self.submitted()
        other = self.make_fund(classes=[{"code": "X"}])
        self.subscribe(self.cls(other, "X"), "2027-01-20", 100, 1)


@tagged("post_install", "-at_install")
class TestLockException(LockCase):
    """Zámek ocenění, vrstva 2: vratný zámek po zveřejnění a výjimka se dvěma schvalovateli."""

    def setUp(self):
        super().setUp()
        self.published = self.run_to_published(self.valuation(self.fund, self.day))
        self.company = self.fund.company_id
        self.Request = self.env["investra.lock.exception.request"]

    def request(self, user=None, lock_date="2027-01-15"):
        return self.Request.with_user(user or self.approver).create({
            "company_id": self.company.id, "user_id": self.env.user.id, "lock_date": lock_date,
            "end_datetime": "2099-01-01 00:00:00", "reason": "Oprava chybného úpisu",
        })

    def test_publish_sets_soft_lock_only(self):
        self.assertEqual(self.company.fiscalyear_lock_date, self.day)
        self.assertFalse(self.company.hard_lock_date)
        with self.assertRaises(UserError):
            self.manual_move("2027-01-20").action_post()

    def test_lock_cannot_be_lowered_or_bypassed_by_odoo_exception(self):
        with self.assertRaises(UserError):
            self.company.fiscalyear_lock_date = "2027-01-15"
        with self.assertRaises(UserError):
            self.company.fiscalyear_lock_date = False
        with self.assertRaises(UserError):
            self.env["account.lock_exception"].create({
                "company_id": self.company.id, "fiscalyear_lock_date": "2027-01-15", "reason": "obejití",
            })
        self.company.fiscalyear_lock_date = "2027-02-28"

    def test_only_approver_requests_and_other_approver_confirms(self):
        from odoo.exceptions import AccessError
        with self.assertRaises(AccessError):
            self.request(user=self.preparer)
        request = self.request()
        with self.assertRaises(UserError):
            request.with_user(self.approver).action_confirm()
        request.with_user(self.approver2).action_confirm()
        self.assertEqual(request.state, "active")
        self.assertEqual(request.exception_id.state, "active")
        move = self.manual_move("2027-01-20")
        move.action_post()
        self.assertEqual(move.state, "posted")
        following = self.valuation(self.fund, date(2027, 2, 28))
        following.action_compute()
        check = following.check_ids.filtered(lambda c: c.code == "lock_exception")
        self.assertEqual(check.status, "warning")
        self.assertIn("Oprava chybného úpisu", check.detail)
        request.with_user(self.approver).action_revoke()
        self.assertEqual(request.exception_id.state, "revoked")
        with self.assertRaises(UserError):
            self.manual_move("2027-01-21").action_post()

    def test_matrix_without_second_person_lets_requester_confirm(self):
        # Schvalovací matice (rozhodnutí 2026-11-11): výjimka podle matice, i bez druhé osoby; zapíše se.
        self.env["investra.approval.matrix"].create({
            "activity": "lock_exception", "second_person": "no", "performer_role": "approver",
        })
        request = self.request()
        request.with_user(self.approver).action_confirm()
        self.assertEqual(request.state, "active")
        log = self.env["investra.approval.log"].search([
            ("res_model", "=", request._name), ("res_id", "=", request.id),
        ])
        self.assertEqual(log.user_id, self.approver)

    def test_rejected_request_creates_no_exception(self):
        request = self.request()
        request.with_user(self.approver2).action_reject()
        self.assertFalse(request.exception_id)
        with self.assertRaises(UserError):
            request.with_user(self.approver2).action_confirm()

    def test_hard_lock_cannot_be_opened(self):
        self.company.sudo().hard_lock_date = "2027-01-20"
        with self.assertRaises(UserError):
            self.request(lock_date="2027-01-15")

    def test_next_valuation_without_exception_is_ok(self):
        following = self.valuation(self.fund, date(2027, 2, 28))
        following.action_compute()
        self.assertEqual(following.check_ids.filtered(lambda c: c.code == "lock_exception").status, "ok")
