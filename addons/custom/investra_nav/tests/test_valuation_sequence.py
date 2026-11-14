from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestValuationSequence(NavCase):
    """Nové ocenění vznikne až po zveřejnění předchozího (rozhodnutí 2026-11-14, varianta A)."""

    enforce_sequence = True

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)

    def test_first_valuation_is_allowed(self):
        self.assertTrue(self.valuation(self.fund, date(2027, 1, 31)))

    def test_new_valuation_waits_for_publication(self):
        first = self.valuation(self.fund, date(2027, 1, 31))
        with self.assertRaisesRegex(UserError, "zveřejnění předchozího"):
            self.valuation(self.fund, date(2027, 2, 28))
        self.run_to_posted(first)
        with self.assertRaisesRegex(UserError, "Zaúčtováno"):
            self.valuation(self.fund, date(2027, 2, 28))
        first.action_send_depositary()
        first.with_user(self.approver).action_depositary_confirm()
        first.with_user(self.approver).action_publish()
        self.assertTrue(self.valuation(self.fund, date(2027, 2, 28)))

    def test_moving_draft_date_is_checked(self):
        self.valuation(self.fund, date(2027, 1, 31))
        draft = self.valuation(self.fund, date(2027, 1, 15))
        with self.assertRaises(UserError):
            draft.write({"date": date(2027, 2, 28)})

    def test_new_version_after_return_is_allowed(self):
        # Oprava vrácením zůstává možná i u ocenění založených před zavedením pravidla.
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        valuation.action_submit()
        new = valuation.with_user(self.approver).action_return("Oprava")
        self.assertEqual(new.version, 2)

    def test_returned_and_reversed_versions_are_skipped(self):
        first = self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        second = self.valuation(self.fund, date(2027, 2, 28))
        second.action_compute()
        second.action_submit()
        second.with_user(self.approver).action_return("Oprava")
        self.assertEqual(first.state, "published")
        # Předchozí je živá verze 2 v návrhu, ne vrácená verze 1 ani zveřejněné lednové ocenění.
        with self.assertRaisesRegex(UserError, "v2"):
            self.valuation(self.fund, date(2027, 3, 31))
