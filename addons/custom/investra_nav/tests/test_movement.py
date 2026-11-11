from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import NavCase


@tagged("post_install", "-at_install")
class TestMovement(NavCase):
    """Úpisy a odkupy, body A–E (docs/navrh-upisy-odkupy.md, rozhodnutí 2026-11-11).

    Úpis: platba = kusy × cena + poplatek + rozdíl + zbytek; odkup: kusy × cena = výplata + poplatek + rozdíl,
    hrubá částka = kusy × cena + zbytek. Rok 2027 v knize jen těchto testů.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[
            {"code": "A"},
            {"code": "F", "entry_fee_rate": 1, "exit_fee_rate": 2},
            {"code": "R", "unit_digits": 0},
        ])
        self.a, self.f, self.r = (self.cls(self.fund, code) for code in "AFR")
        self.Movement = self.env["investra.class.movement"]

    def move(self, fund_class, gross, units, price, kind="subscription", day="2027-01-05", **vals):
        return self.Movement.create({
            "class_id": fund_class.id, "date": day, "movement_type": kind, "amount_class": gross, "units": units,
            "price": price, "manual_reason": "Test", "price_reason": "Počáteční kurz", **vals,
        })

    def lines(self, movement):
        mapping = self.env["investra.role.account"].sudo().search([("company_id", "=", movement.company_id.id)])
        roles = {m.account_id: m.role_id.code for m in mapping}
        result = {}
        for line in movement.event_id.move_id.line_ids:
            role = roles[line.account_id]
            result[role] = round(result.get(role, 0) + line.balance, 2)
        return result

    # --- B: bez poplatku a rozdílu je doklad stejný jako dřív ------------------------------------------

    def test_without_fee_booking_is_unchanged(self):
        sub = self.move(self.a, 1000, 100, 10)
        sub.action_book()
        self.assertEqual(sub.state, "posted")
        self.assertEqual(self.lines(sub), {"bank": 1000, "class_capital": -1000})
        self.assertEqual(sub.capital_amount, 1000)
        red = self.move(self.a, 500, 50, 10, kind="redemption", day="2027-01-06")
        red.action_book()
        self.assertEqual(self.lines(red), {"bank": -500, "class_capital": 500})
        self.assertEqual(red.signed_amount, -500)

    # --- C: poplatek ----------------------------------------------------------------------------------

    def test_entry_fee_goes_to_payable_capital_gets_net(self):
        movement = self.move(self.f, 1010, 99.99, 10, fee_amount_class=10.10)
        self.assertAlmostEqual(movement.fee_expected_class, 10.10, places=2)
        self.assertEqual(movement.fee_recipient, "manager")
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": 1010, "class_capital": -999.90, "subscription_fee_payable": -10.10})
        self.assertAlmostEqual(movement.capital_amount, 999.90, places=2)

    def test_exit_fee_reduces_payout(self):
        movement = self.move(self.f, 1000, 100, 10, kind="redemption", fee_amount_class=20)
        self.assertAlmostEqual(movement.payout_class, 980, places=2)
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": -980, "class_capital": 1000, "subscription_fee_payable": -20})

    def test_fee_needs_recipient(self):
        movement = self.move(self.f, 1010, 99.99, 10, fee_amount_class=10.10)
        movement.fee_recipient = False
        with self.assertRaisesRegex(UserError, "příjemce"):
            movement.action_book()

    def test_manual_entry_prefills_fee_from_rate(self):
        movement = self.Movement.new({"class_id": self.f.id, "movement_type": "subscription", "amount_class": 1010,
                                      "source": "manual"})
        movement._onchange_fee()
        self.assertAlmostEqual(movement.fee_amount_class, 10.10, places=2)

    # --- B: rozdíl ze zaokrouhlení kusů a zbytek ------------------------------------------------------

    def test_rounding_stays_in_fund(self):
        movement = self.move(self.r, 1000, 333, 3, rounding_amount_class=1)
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": 1000, "class_capital": -1000})

    def test_rounding_returned_to_investor(self):
        movement = self.move(self.r, 1000, 333, 3, rounding_amount_class=1, rounding_owner="investor")
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": 1000, "class_capital": -999, "investor_rounding_payable": -1})
        self.assertEqual(movement.capital_amount, 999)

    def test_small_residual_goes_to_rounding_account(self):
        movement = self.move(self.r, 1000, 333, 3, rounding_amount_class=0.99)
        self.assertAlmostEqual(movement.residual_class, 0.01, places=2)
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": 1000, "class_capital": -999.99, "rounding_gain": -0.01})

    def test_redemption_residual_is_loss(self):
        movement = self.move(self.a, 1000.01, 100, 10, kind="redemption")
        movement.action_book()
        self.assertEqual(self.lines(movement), {"bank": -1000.01, "class_capital": 1000, "rounding_loss": 0.01})

    def test_large_residual_stops_booking(self):
        movement = self.move(self.r, 1000, 333, 3, rounding_amount_class=0.98)
        with self.assertRaisesRegex(UserError, "zbytek"):
            movement.action_book()
        self.assertEqual(movement.state, "draft")

    def test_units_must_follow_class_rounding(self):
        with self.assertRaisesRegex(UserError, "zaokrouhlení třídy"):
            self.move(self.r, 1000, 334, 3, rounding_amount_class=-2).action_book()
        with self.assertRaisesRegex(UserError, "desetinných"):
            self.move(self.r, 1000, 333.5, 3, rounding_amount_class=-0.5).action_book()

    def test_price_differs_from_published_needs_reason(self):
        movement = self.move(self.a, 1000, 100, 10, price_reason=False)
        with self.assertRaisesRegex(UserError, "zveřejněného kurzu"):
            movement.action_book()
        movement.price_reason = "Počáteční kurz"
        movement.action_book()
        self.assertEqual(movement.state, "posted")

    def test_ui_booking_needs_price(self):
        movement = self.move(self.a, 1000, 100, 0)
        with self.assertRaisesRegex(UserError, "cena"):
            movement.action_book()

    # --- A: zdroj ---------------------------------------------------------------------------------------

    def test_manual_entry_needs_reason_and_is_needs_reference(self):
        with self.assertRaisesRegex(ValidationError, "důvod"):
            self.move(self.a, 1000, 100, 10, manual_reason=False)
        with self.assertRaisesRegex(ValidationError, "identifikátor"):
            self.move(self.a, 1000, 100, 10, source="is")
        self.move(self.a, 1000, 100, 10, source="is", external_ref="D1/1")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.move(self.f, 1000, 100, 10, source="is", external_ref="D1/1")

    # --- D: historie, storno a oprava -------------------------------------------------------------------

    def test_changes_are_tracked(self):
        movement = self.move(self.a, 1000, 100, 10)
        # Odoo nesleduje změny záznamu založeného ve stejné transakci; zpracování transakce to odpovídá uložení formuláře.
        self.env.flush_all()
        self.env.cr.precommit.run()
        movement.units = 99
        self.env.flush_all()
        self.env.cr.precommit.run()
        # Odoo 20 ukládá změny sledovaných polí do textu zprávy: „stará → <b>nová</b> <i>(Pole)</i>“.
        bodies = " ".join(str(m.body) for m in movement.message_ids)
        self.assertIn("(Kusy)", bodies)

    def test_posted_movement_is_corrected_by_reversal_and_new_movement(self):
        movement = self.move(self.a, 1000, 100, 10)
        movement.action_book()
        with self.assertRaises(UserError):
            movement.with_user(self.preparer).write({"units": 101})
        new = movement.with_user(self.preparer).action_correct("Chybné kusy")
        self.assertEqual(movement.state, "reversed")
        self.assertEqual(movement.event_id.state, "reversed")
        self.assertEqual(movement.reversal_reason, "Chybné kusy")
        self.assertEqual((new.state, new.replaced_id, new.source), ("draft", movement, "manual"))
        self.assertIn("Chybné kusy", new.manual_reason)
        self.assertFalse(new.event_id)

    def test_reversal_into_submitted_valuation_is_refused_until_return(self):
        movement = self.move(self.a, 1000, 100, 10)
        movement.action_book()
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaisesRegex(UserError, "Ke schválení"):
            movement.action_reverse("Chyba")
        self.assertEqual(movement.state, "posted")
        valuation.with_user(self.approver).action_return("Oprava úpisu")
        movement.action_reverse("Chyba")
        self.assertEqual(movement.state, "reversed")

    def test_valuation_skips_reversed_and_warns_on_fee(self):
        kept = self.move(self.a, 1000, 100, 10)
        kept.action_book()
        wrong = self.move(self.a, 500, 50, 10, day="2027-01-06")
        wrong.action_book()
        wrong.action_reverse("Duplicita")
        fee = self.move(self.f, 1010, 100.5, 10, fee_amount_class=5)
        fee.action_book()
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "A").units, 100, places=6)
        self.assertAlmostEqual(self.result(valuation, "F").subscription_amount, 1005, places=2)
        checks = {c.code: c.status for c in valuation.check_ids}
        self.assertEqual(checks["movement_fee_rate"], "warning")
        self.assertEqual(checks["movements_posted"], "ok")
        self.assertEqual(checks["movement_price"], "warning")

    def test_unbooked_movement_stops_valuation(self):
        self.move(self.a, 1000, 100, 10)
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertEqual({c.code: c.status for c in valuation.check_ids}["movements_posted"], "stop")
        with self.assertRaisesRegex(UserError, "zaúčtované"):
            valuation.action_submit()

    # --- E: zaúčtování v UI a schvalovací matice -----------------------------------------------------------

    def test_bulk_booking_from_list(self):
        movements = self.move(self.a, 1000, 100, 10) | self.move(self.a, 500, 50, 10, day="2027-01-06")
        movements.with_user(self.preparer).action_book()
        self.assertEqual(set(movements.mapped("state")), {"posted"})

    def test_manual_booking_follows_matrix_four_eyes(self):
        self.env["investra.approval.matrix"].create({"activity": "subscription_manual", "second_person": "yes"})
        movement = self.move(self.a, 1000, 100, 10)
        action = movement.with_user(self.preparer).action_book()
        self.assertEqual(action["res_model"], "investra.approval.request")
        self.assertEqual(movement.state, "draft")
        request = self.env["investra.approval.request"].browse(action["res_id"])
        with self.assertRaises(UserError):
            request.with_user(self.preparer).action_approve()
        request.with_user(self.approver).action_approve()
        self.assertEqual(movement.state, "posted")
        self.assertEqual(request.state, "done")

    def test_is_movement_skips_matrix(self):
        self.env["investra.approval.matrix"].create({"activity": "subscription_manual", "second_person": "yes"})
        movement = self.move(self.a, 1000, 100, 10, source="is", external_ref="D2/1")
        movement.with_user(self.preparer).action_book()
        self.assertEqual(movement.state, "posted")

    def test_only_preparer_books(self):
        movement = self.move(self.a, 1000, 100, 10)
        outsider = self._make_user("mv_outsider", "base.group_user")
        outsider.write({"company_ids": [(4, self.fund.company_id.id)], "company_id": self.fund.company_id.id})
        with self.assertRaises(Exception):
            movement.with_user(outsider).action_book()
