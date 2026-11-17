from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestValuationSteps(NavCase):
    """Historie kroků ocenění (ZJ-06 bod 12): kdo, kdy, co; nezměnitelná."""

    def prepared(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        return self.valuation(fund, date(2027, 1, 31))

    def steps(self, valuation):
        return [(s.step, s.user_id) for s in valuation.step_ids.sorted("id")]

    def test_each_step_records_user(self):
        valuation = self.run_to_posted(self.prepared())
        self.assertEqual(self.steps(valuation), [
            ("created", self.preparer), ("computed", self.preparer), ("submitted", self.preparer),
            ("approved", self.approver), ("posted", self.preparer),
        ])
        computed = valuation.step_ids.filtered(lambda s: s.step == "computed")
        self.assertIn("FK", computed.note)
        self.assertEqual(valuation.create_uid, self.preparer)

    def test_step_cannot_be_changed_or_deleted(self):
        valuation = self.prepared()
        step = valuation.step_ids
        for record in (step.with_user(self.preparer), step.sudo()):
            with self.assertRaises(UserError):
                record.write({"note": "jinak"})
            with self.assertRaises(UserError):
                record.unlink()
        with self.assertRaises(AccessError):
            self.env["investra.valuation.step"].with_user(self.preparer).create({
                "valuation_id": valuation.id, "step": "posted", "user_id": self.preparer.id,
            })

    def test_return_records_reason_and_new_version(self):
        valuation = self.prepared()
        valuation.action_compute()
        valuation.action_submit()
        new = valuation.with_user(self.approver).action_return("Oprava úpisu")
        returned = valuation.step_ids.filtered(lambda s: s.step == "returned")
        self.assertEqual((returned.user_id, returned.note), (self.approver, "Oprava úpisu"))
        self.assertEqual(new.step_ids.step, "created")
        self.assertEqual(new.step_ids.note, "Verze 2")

    def test_cancelled_draft_takes_its_history(self):
        valuation = self.prepared()
        valuation.action_compute()
        steps = valuation.step_ids
        valuation.with_user(self.preparer).action_cancel_draft()
        self.assertFalse(steps.exists())
