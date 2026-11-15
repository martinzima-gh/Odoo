from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import DerivativeCase


@tagged("post_install", "-at_install")
class TestDerivativeRecord(DerivativeCase):
    """Evidence FX derivátu (DE-02): založení nástroje a kontroly smlouvy a noh; nic se neúčtuje."""

    def test_forward_creates_instrument(self):
        forward = self.forward()
        instrument = forward.instrument_id
        self.assertEqual(forward.state, "draft")
        self.assertEqual(forward.name, "FX forward EUR/CZK 31.12.2026")
        self.assertEqual(instrument.type_id, self.env.ref("investra_instruments.type_derivative_otc"))
        self.assertEqual(instrument.fund_id, self.fund)
        self.assertEqual(instrument.company_id, self.fund.company_id)
        self.assertEqual((instrument.identifier_kind, instrument.identifier), ("contract", "FX-1"))
        self.assertEqual(instrument.name, forward.name)
        self.assertTrue(instrument.code.startswith("OTC-"))
        self.assertEqual(instrument.currency_id, self.czk)
        self.assertEqual(instrument.maturity_date, date(2026, 12, 31))
        self.assertEqual(instrument.counterparty_id, self.bank)
        self.assertEqual(forward.portfolio_id, self.portfolio(self.fund, "fair_value") or forward.portfolio_id)
        self.assertFalse(self.env["account.move"].search_count([("company_id", "=", self.fund.company_id.id)]))

    def test_rate_is_functional_per_foreign_unit(self):
        swap = self.swap()
        near, far = swap.leg_ids.sorted("settlement_date")
        self.assertAlmostEqual(near.rate, 25.0, places=6)
        self.assertAlmostEqual(far.rate, 24.9, places=6)
        self.assertEqual(set(swap.leg_ids.mapped("state")), {"open"})
        self.assertEqual(swap.name, "FX swap EUR/CZK 31.12.2026")

    def test_swap_saves_in_form(self):
        with Form(self.env["investra.derivative"].with_user(self.preparer)) as form:
            form.fund_id = self.fund
            form.partner_id = self.bank
            form.kind = "swap"
            form.trade_date = date(2026, 9, 30)
            form.contract_ref = "FX-FORM"
            with form.leg_ids.new() as leg:
                leg.settlement_date = date(2026, 10, 2)
                leg.buy_currency_id = self.eur
                leg.buy_amount = 1_000_000
                leg.sell_currency_id = self.czk
                leg.sell_amount = 25_000_000
            with form.leg_ids.new() as leg:
                leg.settlement_date = date(2026, 12, 31)
                leg.buy_currency_id = self.czk
                leg.buy_amount = 24_900_000
                leg.sell_currency_id = self.eur
                leg.sell_amount = 1_000_000
        swap = form.record
        self.assertEqual(len(swap.leg_ids), 2)
        self.assertTrue(swap.instrument_id)
        self.assertTrue(swap.portfolio_id)

    def test_draft_change_updates_instrument(self):
        forward = self.forward()
        forward.write({"contract_ref": "FX-2"})
        forward.leg_ids.write({"settlement_date": "2027-01-29"})
        self.assertEqual(forward.instrument_id.identifier, "FX-2")
        self.assertEqual(forward.instrument_id.maturity_date, date(2027, 1, 29))
        self.assertEqual(forward.instrument_id.name, "FX forward EUR/CZK 29.01.2027")

    def test_value_record(self):
        forward = self.forward()
        value = self.env["investra.derivative.value"].with_user(self.preparer).create({
            "derivative_id": forward.id, "date": "2026-10-31", "amount": 150000, "currency_id": self.czk.id,
            "source": "Potvrzení banky", "reason": "Ocenění protistrany",
        })
        self.assertEqual(value.company_id, self.fund.company_id)
        with self.assertRaises(ValidationError):
            value.date = "2026-09-29"

    # --- kontroly ---------------------------------------------------------------------------------------------------

    def assert_invalid(self, text, kind, legs):
        with self.assertRaises(ValidationError) as error:
            self.derivative(kind, legs)
        self.assertIn(text, str(error.exception))

    def test_forward_needs_one_leg(self):
        two = [self.leg("2026-10-02", self.eur, 1, self.czk, 25), self.leg("2026-12-31", self.czk, 25, self.eur, 1)]
        self.assert_invalid("právě jednu nohu", "forward", two)
        self.assert_invalid("právě jednu nohu", "forward", [])

    def test_swap_needs_two_opposite_legs_in_order(self):
        near = self.leg("2026-10-02", self.eur, 1_000_000, self.czk, 25_000_000)
        self.assert_invalid("právě dvě nohy", "swap", [near])
        self.assert_invalid("opačný směr", "swap", [near, self.leg("2026-12-31", self.eur, 1_000_000, self.czk, 24_900_000)])
        self.assert_invalid("pozdější datum", "swap", [near, self.leg("2026-10-02", self.czk, 24_900_000, self.eur, 1_000_000)])

    def test_leg_checks(self):
        self.assert_invalid("musí lišit", "forward", [self.leg("2026-12-31", self.eur, 1, self.eur, 1)])
        self.assert_invalid("kladné", "forward", [self.leg("2026-12-31", self.eur, -1, self.czk, 25)])
        self.assert_invalid("kladné", "forward", [self.leg("2026-12-31", self.eur, 1, self.czk, 0)])
        self.assert_invalid("před sjednáním", "forward", [self.leg("2026-09-29", self.eur, 1, self.czk, 25)])
        self.assert_invalid("funkční měna fondu", "forward", [self.leg("2026-12-31", self.eur, 1, self.usd, 1.1)])

    def test_trade_date_after_settlement_is_rejected(self):
        forward = self.forward()
        with self.assertRaises(ValidationError):
            forward.trade_date = "2027-01-01"

    def test_duplicate_contract_ref_in_fund(self):
        self.forward()
        with self.assertRaises(ValidationError) as error:
            self.forward()
        self.assertIn("číslem smlouvy FX-1", str(error.exception))
        other = self.forward(ref="FX-2")
        with self.assertRaises(ValidationError):
            other.contract_ref = "FX-1"

    def test_spot_is_single_leg_like_forward(self):
        spot = self.derivative("spot", [self.leg("2026-10-02", self.eur, 1_000_000, self.czk, 25_000_000)], ref="SPOT-1")
        self.assertEqual(spot.name, "FX spot EUR/CZK 02.10.2026")
        self.assertTrue(spot.instrument_id)
        two = [self.leg("2026-10-02", self.eur, 1, self.czk, 25), self.leg("2026-12-31", self.czk, 25, self.eur, 1)]
        self.assert_invalid("právě jednu nohu", "spot", two)

    # --- ochrana -----------------------------------------------------------------------------------------------------

    def test_system_fields_are_protected(self):
        forward = self.forward()
        with self.assertRaises(UserError):
            forward.write({"state": "agreed"})
        with self.assertRaises(UserError):
            forward.leg_ids.write({"state": "settled"})
        with self.assertRaises(UserError):
            self.env["investra.derivative"].with_user(self.preparer).create({
                "fund_id": self.fund.id, "partner_id": self.bank.id, "kind": "forward", "trade_date": "2026-09-30",
                "contract_ref": "FX-X", "state": "agreed",
                "leg_ids": [self.leg("2026-12-31", self.czk, 24_900_000, self.eur, 1_000_000)],
            })

    def test_agreed_contract_is_read_only(self):
        swap = self.swap()
        swap.sudo().state = "agreed"
        with self.assertRaises(UserError):
            swap.write({"contract_ref": "FX-9"})
        with self.assertRaises(UserError):
            swap.leg_ids[0].write({"buy_amount": 2_000_000})
        with self.assertRaises(UserError):
            swap.leg_ids[0].unlink()
        with self.assertRaises(UserError):
            swap.write({"leg_ids": [self.leg("2027-01-31", self.eur, 1, self.czk, 25)]})
        with self.assertRaises(UserError):
            swap.sudo(False).unlink()
        # Ruční hodnotu jde zadat i ke sjednané smlouvě (oceňuje se právě sjednaná).
        self.env["investra.derivative.value"].with_user(self.preparer).create({
            "derivative_id": swap.id, "date": "2026-10-31", "amount": 1, "currency_id": self.czk.id, "source": "Banka",
        })
