from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestReturn(NavCase):
    """Vrácení a storno ocenění s důvodem (rozhodnutí 2026-11-10 „Vrácení a storno ocenění“)."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        self.day = date(2027, 1, 31)

    def wizard(self, valuation, mode, reason="Chyba v ceně", user=None):
        return self.env["investra.valuation.return.wizard"].with_user(user or self.approver).create({
            "valuation_id": valuation.id, "mode": mode, "reason": reason,
        })

    def test_reverse_posted_valuation_makes_storno_and_new_version(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        capital = valuation.fund_capital
        action = self.wizard(valuation, "reverse").action_confirm()
        self.assertEqual(valuation.state, "reversed")
        self.assertEqual(valuation.return_reason, "Chyba v ceně")
        reversals = valuation.sudo().event_ids.reversal_move_id
        self.assertEqual(len(reversals), len(valuation.event_ids))
        self.assertTrue(all(m.date == self.day and m.state == "posted" for m in reversals))
        new = self.env["investra.valuation"].browse(action["res_id"])
        self.assertEqual((new.version, new.state), (2, "draft"))
        new.with_user(self.preparer).action_compute()
        self.assertAlmostEqual(new.fund_capital, capital, places=2)

    def test_reverse_confirmed_valuation(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        self.wizard(valuation, "reverse").action_confirm()
        self.assertEqual(valuation.state, "reversed")

    def test_published_valuation_cannot_be_reversed(self):
        valuation = self.run_to_published(self.valuation(self.fund, self.day))
        with self.assertRaises(UserError):
            self.wizard(valuation, "reverse").action_confirm()

    def test_preparer_cannot_reverse(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        with self.assertRaises(AccessError):
            valuation.with_user(self.preparer).action_reverse("x")

    def test_reverse_needs_reason(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        with self.assertRaises(UserError):
            valuation.with_user(self.approver).action_reverse("")

    def test_reverse_refused_when_later_valuation_builds_on_it(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        self.run_to_posted(self.valuation(self.fund, date(2027, 2, 28)))
        with self.assertRaisesRegex(UserError, "pozdější"):
            self.wizard(valuation, "reverse").action_confirm()
        self.assertEqual(valuation.state, "posted")

    def test_later_draft_does_not_block_reverse(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        self.valuation(self.fund, date(2027, 2, 28)).action_compute()
        self.wizard(valuation, "reverse").action_confirm()
        self.assertEqual(valuation.state, "reversed")

    def test_wizard_return_before_posting_opens_new_version(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        wizard = self.wizard(valuation, "return")
        self.assertIn("bez storna", wizard.effect)
        action = wizard.action_confirm()
        self.assertEqual(valuation.state, "returned")
        self.assertEqual(self.env["investra.valuation"].browse(action["res_id"]).version, 2)

    def test_wizard_depositary_return(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        self.wizard(valuation, "depositary").action_confirm()
        self.assertEqual(valuation.state, "reversed")
