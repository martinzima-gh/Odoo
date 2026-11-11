from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestValuationLock(NavCase):
    """Zámek ocenění, vrstva 1: od Ke schválení do Potvrzeno nic s datem ≤ datu ocenění."""

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
