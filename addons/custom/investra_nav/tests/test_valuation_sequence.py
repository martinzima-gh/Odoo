from datetime import date

from odoo.exceptions import AccessError, UserError
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
        # Dříve: návrh 15. 1. vedle rozpracovaného 31. 1. a posun za něj. Takový návrh od OC-01 nevznikne
        # (pozdější ocenění existuje), proto se ověřuje posun dozadu před zveřejněné ocenění a posun dopředu.
        self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        draft = self.valuation(self.fund, date(2027, 2, 28))
        with self.assertRaisesRegex(UserError, "pozdějšímu datu"):
            draft.write({"date": date(2027, 1, 15)})
        draft.write({"date": date(2027, 3, 31)})
        self.assertEqual(draft.date, date(2027, 3, 31))

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


@tagged("post_install", "-at_install")
class TestValuationOrderAndCancel(NavCase):
    """OC-01: ocenění jen po posledním ocenění fondu a zrušení návrhu tlačítkem (rozhodnutí 2026-11-15)."""

    enforce_sequence = True

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        self.common_result(self.fund, "r1", "2027-01-15", 100)

    def test_before_published_later_valuation_fails(self):
        self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        with self.assertRaisesRegex(UserError, "pozdějšímu datu"):
            self.valuation(self.fund, date(2027, 1, 15))

    def test_before_draft_later_valuation_fails(self):
        self.valuation(self.fund, date(2027, 1, 31)).action_compute()
        with self.assertRaisesRegex(UserError, "pozdějšímu datu"):
            self.valuation(self.fund, date(2027, 1, 15))

    def test_later_returned_valuation_does_not_block(self):
        later = self.valuation(self.fund, date(2027, 1, 31))
        later.action_compute()
        later.action_submit()
        new = later.with_user(self.approver).action_return("Oprava")
        new.with_user(self.preparer).action_cancel_draft()
        self.assertEqual(later.state, "returned")
        self.assertTrue(self.valuation(self.fund, date(2027, 1, 15)))

    def test_later_reversed_valuation_does_not_block(self):
        later = self.run_to_posted(self.valuation(self.fund, date(2027, 1, 31)))
        new = later.with_user(self.approver).action_reverse("Oprava")
        new.with_user(self.preparer).action_cancel_draft()
        self.assertEqual(later.state, "reversed")
        self.assertTrue(self.valuation(self.fund, date(2027, 1, 15)))

    def test_first_and_following_valuations_pass(self):
        self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        self.assertTrue(self.valuation(self.fund, date(2027, 2, 28)))

    def posted_lines(self):
        lines = self.env["account.move.line"].sudo().search([
            ("company_id", "=", self.fund.company_id.id), ("parent_state", "=", "posted"),
        ])
        return sorted((l.id, l.move_id.id, l.account_id.id, l.balance) for l in lines)

    def test_cancel_computed_removes_record_and_drafts(self):
        self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        self.common_result(self.fund, "r2", "2027-02-15", 50)
        # Pevná měsíční úplata, aby výpočet vytvořil návrh dokladu (jako úplaty u ocenění id 39).
        self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Úplata", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "fixed_monthly": 10, "fixed_mode": "started_month"})],
        })
        valuation = self.valuation(self.fund, date(2027, 2, 28))
        valuation.action_compute()
        self.assertEqual(valuation.state, "computed")
        events = valuation.sudo().event_ids
        moves = events.move_id
        self.assertTrue(moves, "Výpočet má vytvořit návrhy dokladů.")
        self.assertTrue(all(m.state == "draft" for m in moves))
        posted = self.posted_lines()
        # Jako ocenění id 39: návrhy dokladů leží v uzamčeném období.
        self.fund.company_id.sudo().fiscalyear_lock_date = date(2027, 3, 31)
        name = valuation.display_name
        valuation.with_user(self.preparer).action_cancel_draft()
        self.assertFalse(valuation.exists())
        self.assertFalse(moves.exists())
        self.assertEqual(set(events.mapped("state")), {"discarded"})
        self.assertEqual(self.posted_lines(), posted)
        message = self.fund.message_ids[:1]
        self.assertIn(name, message.body)
        self.assertEqual(message.author_id, self.preparer.partner_id)

    def test_cancel_after_submit_fails(self):
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            valuation.with_user(self.preparer).action_cancel_draft()
        with self.assertRaises(UserError):
            valuation.sudo().unlink()
        self.assertTrue(valuation.exists())

    def test_user_without_preparer_role_cannot_cancel(self):
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        company = self.fund.company_id
        viewer = self.env["res.users"].create({
            "name": "nav_viewer", "login": "nav_viewer", "company_id": company.id, "company_ids": [(6, 0, company.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            valuation.with_user(viewer).action_cancel_draft()
        self.assertTrue(valuation.exists())
