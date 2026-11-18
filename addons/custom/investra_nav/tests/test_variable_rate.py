from datetime import date
from decimal import Decimal

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .. import engine
from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids

D = Decimal
QTY = D(1000000)


@tagged("post_install", "-at_install")
class TestVariableRate(NavCase):
    """Variabilní sazba (IM-11, docs/navrh-variabilni-sazba.md, varianta a: prospektivní EIR).

    Číselný příklad návrhu posunutý do roku 2029 (stejné počty dní, act365): vklad 1 000 000 kusů za 0,98 dne
    1. 1. 2029, splatnost 1. 1. 2030, pololetně 4 %; od 1. 7. 2029 nová sazba 5 %.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.deposit = self.instrument("deposit", principal=1, coupon_rate=4, day_count="act365", coupon_frequency="semiannual",
                                       start_date="2029-01-01", maturity_date="2030-01-01", rate_type="variable")
        self.deposit.action_generate_schedule()

    def instrument(self, code, model="hold_to_collect", **vals):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"{code} {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        }, self.fund))
        self.classify(self.fund, instrument, model)
        return instrument

    def trade(self, instrument, day, quantity, price, model="hold_to_collect"):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund, model).id, "instrument_id": instrument.id,
            "trade_date": day, "quantity": quantity, "price": price,
        })

    def new_rate(self, instrument, day, rate, user=None):
        wizard = self.env["investra.instrument.rate.wizard"].with_user(user or self.preparer).create(
            {"instrument_id": instrument.id, "valid_from": day, "rate": rate})
        wizard.action_confirm()
        return wizard

    def flows(self, instrument):
        return [(str(f.date), f.flow_type, f.amount, f.estimated) for f in instrument.cashflow_ids.sorted(lambda f: (f.date, f.flow_type))]

    def ac(self, day):
        return self.deposit._accrued_value(self.fund, date.fromisoformat(day))

    @staticmethod
    def manual(cost, segments, day):
        """Kontrolní výpočet po úsecích přímo z engine.effective_rate a engine.amortised_cost (jen čísla z testu)."""
        value = D(cost)
        for index, (start, flows) in enumerate(segments):
            end = segments[index + 1][0] if index + 1 < len(segments) else day
            value = engine.amortised_cost([(start, -value), *[(d, a) for d, a in flows if d > start]], end)
        return value

    # --- generátor a příznak odhadu ------------------------------------------------------------------------

    def test_variable_schedule_equals_fixed_and_marks_estimates(self):
        fixed = self.instrument("deposit", principal=1, coupon_rate=4, day_count="act365", coupon_frequency="semiannual",
                                start_date="2029-01-01", maturity_date="2030-01-01")
        fixed.action_generate_schedule()
        self.assertEqual([f[:3] for f in self.flows(self.deposit)], [f[:3] for f in self.flows(fixed)])
        self.assertEqual(self.flows(self.deposit), [
            ("2029-07-01", "interest", 0.01983562, False), ("2030-01-01", "interest", 0.02016438, True),
            ("2030-01-01", "principal", 1.0, False),
        ])
        self.assertFalse(any(fixed.cashflow_ids.mapped("estimated")))
        self.assertEqual(self.deposit.rate_period_ids.mapped(lambda p: (str(p.valid_from), p.rate)), [("2029-01-01", 4.0)])

    def test_schedule_splits_period_over_rate_change(self):
        """Období sazby zadané před generováním: kupón přes změnu po částech, další období poslední sazbou jako odhad."""
        bond = self.instrument("deposit", principal=1, coupon_rate=4, day_count="act365", coupon_frequency="semiannual",
                               start_date="2029-01-01", maturity_date="2030-07-01", rate_type="variable")
        self.new_rate(bond, "2029-04-01", 5)
        bond.action_generate_schedule()
        # 1. 1. – 1. 4. 90 dní 4 %, 1. 4. – 1. 7. 91 dní 5 %: (3,6 + 4,55) / 365 = 0,02232877.
        self.assertEqual(self.flows(bond), [
            ("2029-07-01", "interest", 0.02232877, False), ("2030-01-01", "interest", 0.02520548, True),
            ("2030-07-01", "interest", 0.02479452, True), ("2030-07-01", "principal", 1.0, False),
        ])

    # --- číselný příklad návrhu: prospektivní přepočet EIR ------------------------------------------------

    def test_design_example(self):
        self.trade(self.deposit, "2029-01-01", QTY, 0.98)
        self.assertEqual(self.ac("2029-04-01"), D("994608.63"))
        self.assertEqual(self.ac("2029-07-01"), D("989765.37"))
        self.new_rate(self.deposit, "2029-07-01", 5)
        self.assertEqual(self.flows(self.deposit), [
            ("2029-07-01", "interest", 0.01983562, False), ("2030-01-01", "interest", 0.02520548, False),
            ("2030-01-01", "principal", 1.0, False),
        ])
        archived = self.deposit.superseded_cashflow_ids
        self.assertEqual(archived.mapped(lambda f: (str(f.date), f.amount, str(f.superseded_on))),
                         [("2030-01-01", 0.02016438, "2029-07-01")])
        # Minulé dny beze změny, v den změny bez skoku, potom nová EIR 7,228004 %.
        self.assertEqual(self.ac("2029-04-01"), D("994608.63"))
        self.assertEqual(self.ac("2029-07-01"), D("989765.37"))
        self.assertEqual(self.ac("2029-10-01"), D("1007329.58"))
        rate = engine.effective_rate([(date(2029, 7, 1), D("-989765.37")), (date(2030, 1, 1), D("1025205.48"))])
        self.assertEqual(round(rate * 100, 6), D("7.228004"))
        self.assertEqual(self.deposit.coupon_rate, 5)

    def test_two_changes_and_trade_between(self):
        self.trade(self.deposit, "2029-01-01", QTY, 0.98)
        self.new_rate(self.deposit, "2029-04-01", 5)
        self.trade(self.deposit, "2029-05-01", 500000, 0.99)
        self.new_rate(self.deposit, "2029-08-01", 3)
        # Kupón 1. 1. 2030 po druhé změně: 1. 7. – 1. 8. 31 dní 5 %, 1. 8. – 1. 1. 153 dní 3 % = 6,14 / 365.
        self.assertEqual(self.flows(self.deposit)[1][:3], ("2030-01-01", "interest", 0.01682192))
        c1, c2a, c2b, c2c = D("0.01983562"), D("0.02016438"), D("0.02520548"), D("0.01682192")
        jul, jan = D("0.02232877"), date(2030, 1, 1)

        def version(quantity, july, january):
            return [(date(2029, 7, 1), quantity * july), (jan, quantity * (1 + january))]

        a = self.manual(QTY * D("0.98"), [
            (date(2029, 1, 1), version(QTY, c1, c2a)), (date(2029, 4, 1), version(QTY, jul, c2b)),
            (date(2029, 8, 1), version(QTY, jul, c2c)),
        ], date(2029, 10, 1))
        b = self.manual(D(500000) * D("0.99"), [
            (date(2029, 5, 1), version(D(500000), jul, c2b)), (date(2029, 8, 1), version(D(500000), jul, c2c)),
        ], date(2029, 10, 1))
        self.assertEqual(self.ac("2029-10-01"), engine.money(a + b))
        # Před první změnou jen původní kalendář prvního nákupu.
        self.assertEqual(self.ac("2029-03-01"), engine.amortised_cost(
            [(date(2029, 1, 1), -QTY * D("0.98")), *version(QTY, c1, c2a)], date(2029, 3, 1)))

    def test_mid_period_change_keeps_past_days(self):
        self.trade(self.deposit, "2029-01-01", QTY, 0.98)
        before = self.ac("2029-04-01")
        self.new_rate(self.deposit, "2029-04-01", 5)
        self.assertEqual(self.ac("2029-04-01"), before)
        expected = engine.amortised_cost(
            [(date(2029, 4, 1), -before), (date(2029, 7, 1), D("22328.77")), (date(2030, 1, 1), D("1025205.48"))],
            date(2029, 5, 1))
        self.assertEqual(self.ac("2029-05-01"), expected)

    def deposit_position(self):
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 1000000, 1000)
        trade = self.trade(self.deposit, "2029-01-01", QTY, 0.98)
        trade._book()
        return trade

    def test_extraordinary_repayment_after_change_scales_value(self):
        self.deposit_position()
        self.new_rate(self.deposit, "2029-07-01", 5)
        unscaled = self.ac("2029-10-01")
        repayment = self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund, "hold_to_collect").id,
            "instrument_id": self.deposit.id, "date": "2029-08-01", "kind": "extraordinary", "principal_amount": 400000,
        })
        repayment._book()
        self.assertAlmostEqual(float(self.ac("2029-10-01")), float(unscaled) * 0.6, delta=0.02)

    # --- lineární úročení a reálná hodnota ------------------------------------------------------------------

    def test_linear_deposit_after_change(self):
        deposit = self.instrument("deposit", principal=1, coupon_rate=4, day_count="act365", coupon_frequency="maturity",
                                  start_date="2029-01-01", maturity_date="2030-01-01", rate_type="variable",
                                  accrual_method="linear", accrual_note="Krátký vklad")
        deposit.action_generate_schedule()
        self.trade(deposit, "2029-01-01", QTY, 0.98)
        value = deposit._accrued_value
        before = value(self.fund, date(2029, 7, 1))
        self.new_rate(deposit, "2029-07-01", 5)
        self.assertEqual(value(self.fund, date(2029, 7, 1)), before)
        self.assertEqual(before, engine.linear_accrual(D(980000), D(1040000), date(2029, 1, 1), date(2030, 1, 1), date(2029, 7, 1)))
        # Splatná částka po změně: (0,04 × 181 + 0,05 × 184) / 365 = 0,0450411 na jednotku.
        self.assertEqual(value(self.fund, date(2029, 10, 1)), engine.linear_accrual(
            before, D("1045041.10"), date(2029, 7, 1), date(2030, 1, 1), date(2029, 10, 1)))
        self.assertEqual(value(self.fund, date(2030, 1, 1)), 0)

    def test_fair_value_bond_earned_interest_by_rate_segments(self):
        bond = self.instrument("bond", model="fair_value", principal=1000, coupon_rate=6, day_count="thirty360_eu",
                               coupon_frequency="semiannual", start_date="2029-01-01", maturity_date="2031-01-01",
                               rate_type="variable")
        bond.action_generate_schedule()
        self.assertEqual(bond._accrued_coupon_unit(date(2029, 3, 1)), 10)
        self.env["investra.instrument.rate.period"].create({"instrument_id": bond.id, "valid_from": "2029-04-01", "rate": 8})
        # Kupón 1. 7.: 90 dní 6 % + 90 dní 8 % = 15 + 20; další kupóny 40 jako odhad.
        self.assertEqual(self.flows(bond)[:2], [("2029-07-01", "interest", 35.0, False), ("2030-01-01", "interest", 40.0, True)])
        self.assertEqual(bond._accrued_coupon_unit(date(2029, 3, 1)), 10)
        self.assertEqual(engine.money(bond._accrued_coupon_unit(date(2029, 5, 1))), D("21.67"))
        trade = self.trade(bond, "2029-05-01", 10, 1000, model="fair_value")
        self.assertEqual(trade.accrued_interest, 216.67)

    # --- odmítnutí, historie, návrat ----------------------------------------------------------------------

    def test_wizard_shows_effect_and_period_warning(self):
        form = Form(self.env["investra.instrument.rate.wizard"].with_user(self.preparer).with_context(
            default_instrument_id=self.deposit.id))
        form.valid_from = date(2029, 4, 1)
        form.rate = 5
        self.assertIn("není začátkem kupónového období", form.period_warning)
        self.assertIn("2030-01-01: 0.0201644 → 0.0252055", form.effect)
        form.valid_from = date(2029, 7, 1)
        self.assertFalse(form.period_warning)
        self.assertEqual(self.deposit.rate_period_ids.mapped("rate"), [4.0])

    def test_refusals(self):
        self.deposit_position()
        with self.assertRaisesRegex(UserError, "po posledním období"):
            self.new_rate(self.deposit, "2029-01-01", 5)
        with self.assertRaisesRegex(UserError, "od splatnosti"):
            self.new_rate(self.deposit, "2030-01-01", 5)
        with self.assertRaisesRegex(UserError, "tlačítkem Zadat novou sazbu"):
            self.deposit.with_user(self.preparer).write({"coupon_rate": 5})
        with self.assertRaisesRegex(UserError, "na pevnou"):
            self.deposit.with_user(self.preparer).write({"rate_type": "fixed"})
        self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund, "hold_to_collect").id,
            "instrument_id": self.deposit.id, "date": "2029-07-01", "principal_amount": 0, "interest_amount": 19835.62,
        })
        with self.assertRaisesRegex(UserError, "splátku k 2029-07-01"):
            self.new_rate(self.deposit, "2029-06-01", 5)
        self.new_rate(self.deposit, "2029-07-01", 5)

    def test_locked_valuation_refuses_and_posted_value_stays(self):
        self.deposit_position()
        valuation = self.run_to_posted(self.valuation(self.fund, date(2029, 6, 30)))
        line = valuation.portfolio_line_ids.filtered(lambda l: l.instrument_id == self.deposit)
        with self.assertRaisesRegex(UserError, "ocenění"):
            self.new_rate(self.deposit, "2029-06-30", 5)
        self.new_rate(self.deposit, "2029-07-01", 5)
        self.assertEqual(self.ac("2029-06-30"), D(str(line.fair_value_currency)))

    def test_history_generator_lock_and_revert(self):
        before = self.flows(self.deposit)
        self.new_rate(self.deposit, "2029-07-01", 5)
        bodies = " ".join(self.deposit.message_ids.mapped("body"))
        self.assertIn("Nová sazba 5 % p.a. platí od 2029-07-01", bodies)
        self.assertIn("2030-01-01 0.0201644 → 0.0252055", bodies)
        with self.assertRaisesRegex(UserError, "nahrazenými toky"):
            self.deposit.action_generate_schedule()
        periods = self.deposit.rate_period_ids
        with self.assertRaisesRegex(UserError, "jen poslední"):
            periods[0].with_user(self.preparer).unlink()
        with self.assertRaisesRegex(UserError, "jen poznámka"):
            periods[-1].with_user(self.preparer).write({"rate": 6})
        periods[-1].with_user(self.preparer).unlink()
        self.assertEqual(self.flows(self.deposit), before)
        self.assertFalse(self.deposit.superseded_cashflow_ids)
        self.assertEqual(self.deposit.coupon_rate, 4)

    def test_fixed_to_variable_after_trade(self):
        fixed = self.instrument("deposit", principal=1, coupon_rate=4, day_count="act365", coupon_frequency="semiannual",
                                start_date="2029-01-01", maturity_date="2030-01-01")
        fixed.action_generate_schedule()
        self.trade(fixed, "2029-01-01", QTY, 0.98)
        before = fixed._accrued_value(self.fund, date(2029, 4, 1))
        fixed.with_user(self.preparer).write({"rate_type": "variable"})
        self.assertEqual(fixed._accrued_value(self.fund, date(2029, 4, 1)), before)
        self.assertEqual([f[3] for f in self.flows(fixed)], [False, True, False])
        self.assertIn("Druh sazby: Pevná → Variabilní", " ".join(fixed.message_ids.mapped("body")))

    # --- ZJ-10 fáze 2: sledování období sazby (mixin jen poznámka; ruční zprávy nástroje beze změny, bez duplicit) ---

    def _tracking_mark(self):
        self.env.flush_all()
        self.env.cr.precommit.run()
        return set(self.deposit.message_ids.ids)

    def _tracking_bodies(self, mark):
        self.env.flush_all()
        self.env.cr.precommit.run()
        return [m.body or "" for m in self.deposit.message_ids.filtered(lambda m: m.id not in mark)]


    def test_note_change_goes_to_instrument_chatter(self):
        period = self.deposit.rate_period_ids
        mark = self._tracking_mark()
        period.write({"note": "3M PRIBOR + 1 %"})
        text = "\n".join(self._tracking_bodies(mark))
        self.assertIn("Období sazby od 2029-01-01 – Poznámka: – → 3M PRIBOR + 1 %", text)

    def test_new_rate_keeps_manual_message_without_duplicate(self):
        mark = self._tracking_mark()
        self.new_rate(self.deposit, "2029-07-01", 5)
        bodies = self._tracking_bodies(mark)
        self.assertEqual(sum("Nová sazba 5 % p.a. platí od 2029-07-01" in b for b in bodies), 1)
        self.assertFalse([b for b in bodies if "Přidáno" in b], bodies)

        mark = self._tracking_mark()
        self.deposit.rate_period_ids[-1].with_user(self.preparer).unlink()
        bodies = self._tracking_bodies(mark)
        self.assertEqual(sum("Smazána sazba 5 % p.a. platná od 2029-07-01" in b for b in bodies), 1)
        self.assertFalse([b for b in bodies if "Odebráno" in b], bodies)

    def test_rate_type_switch_does_not_log_period_lines(self):
        mark = self._tracking_mark()
        self.deposit.write({"rate_type": "fixed"})
        bodies = self._tracking_bodies(mark)
        self.assertTrue([b for b in bodies if "Druh sazby" in b])
        self.assertFalse([b for b in bodies if "Odebráno" in b], bodies)
