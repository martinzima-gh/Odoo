from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import DerivativeCase


@tagged("post_install", "-at_install")
class TestDerivativeRecord(DerivativeCase):
    """Evidence FX derivátu (DE-02): založení nástroje a kontroly smlouvy a noh; nic se neúčtuje."""

    def test_portfolio_menu_order_and_location(self):
        names = (
            "investra_instruments.menu_trade",
            "investra_nav.menu_repayment",
            "investra_derivative.menu_derivative",
            "investra_instruments.menu_price",
            "investra_instruments.menu_classification",
        )
        menus = [self.env.ref(name) for name in names]
        self.assertEqual([menu.sequence for menu in menus], [10, 20, 30, 40, 50])
        self.assertTrue(all(menu.parent_id == self.env.ref("investra_instruments.menu_instruments") for menu in menus))
        self.assertEqual(
            self.env.ref("investra_instruments.menu_portfolio").parent_id,
            self.env.ref("investra_entity.menu_setup_funds"),
        )
        self.assertEqual(self.env.ref("investra_instruments.action_portfolio").name, "Portfolia")

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

    def test_forward_form_defaults_one_leg_and_functional_currency(self):
        form = Form(self.env["investra.derivative"].with_user(self.preparer))
        form.fund_id = self.fund
        self.assertEqual(form.kind, "forward")
        self.assertEqual(len(form.leg_ids), 1)
        with form.leg_ids.edit(0) as leg:
            self.assertEqual(leg.buy_currency_id, self.czk)
            # Noha se při opuštění ukládá, proto ji vyplníme celou (povinná pole).
            leg.settlement_date = date(2026, 10, 2)
            leg.buy_amount = 25_000_000
            leg.sell_currency_id = self.eur
            leg.sell_amount = 1_000_000

    def test_swap_form_prefills_far_leg_and_agrees(self):
        self.rate("2026-09-30", 25)
        form = Form(self.env["investra.derivative"].with_user(self.preparer))
        form.fund_id = self.fund
        form.partner_id = self.bank
        form.kind = "swap"
        form.trade_date = date(2026, 9, 30)
        form.contract_ref = "FX-PREFILL"
        with form.leg_ids.edit(0) as near:
            near.settlement_date = date(2026, 10, 2)
            near.buy_currency_id = self.eur
            near.buy_amount = 1_000_000
            near.sell_currency_id = self.czk
            near.sell_amount = 25_000_000
        with form.leg_ids.edit(1) as far:
            self.assertEqual((far.buy_currency_id, far.buy_amount), (self.czk, 25_000_000))
            self.assertEqual((far.sell_currency_id, far.sell_amount), (self.eur, 1_000_000))
            self.assertFalse(far.settlement_date)
            far.settlement_date = date(2026, 12, 31)
        derivative = form.save()
        derivative.action_agree()
        self.assertEqual(derivative.state, "agreed")

    def test_swap_saves_in_form(self):
        with Form(self.env["investra.derivative"].with_user(self.preparer)) as form:
            form.fund_id = self.fund
            form.partner_id = self.bank
            form.kind = "swap"
            form.trade_date = date(2026, 9, 30)
            form.contract_ref = "FX-FORM"
            with form.leg_ids.edit(0) as leg:
                leg.settlement_date = date(2026, 10, 2)
                leg.buy_currency_id = self.eur
                leg.buy_amount = 1_000_000
                leg.sell_currency_id = self.czk
                leg.sell_amount = 25_000_000
            with form.leg_ids.edit(1) as leg:
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
