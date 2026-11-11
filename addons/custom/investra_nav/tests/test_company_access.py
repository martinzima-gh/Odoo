from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestCompanyAccess(NavCase):
    """Uživatel bez přístupu do společnosti fondu nespustí nad jeho oceněním žádný krok."""

    def setUp(self):
        super().setUp()
        own = self.own = self.make_fund(classes=[{"code": "A"}])
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.own_company = own.company_id
        self.outsider = self.env["res.users"].create({
            "name": "cizi_uzivatel", "login": "cizi_uzivatel", "company_id": self.own_company.id, "company_ids": [(6, 0, self.own_company.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("investra_entity.group_valuation_preparer").id,
                                  self.env.ref("investra_entity.group_valuation_approver").id])],
        })
        self.foreign = self.valuation(self.fund, "2037-01-31")

    def as_outsider(self, record):
        return record.with_user(self.outsider).with_context(allowed_company_ids=self.own_company.ids)

    def test_outsider_cannot_compute(self):
        with self.assertRaises(AccessError):
            self.as_outsider(self.foreign).action_compute()
        self.assertEqual(self.foreign.state, "draft")

    def test_outsider_cannot_approve(self):
        with self.assertRaises(AccessError):
            self.as_outsider(self.foreign).action_approve()

    def test_outsider_cannot_approve_price(self):
        instrument = self.env["investra.instrument"].create({
            "name": "Akcie", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        })
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": "2037-01-31", "price": 1, "source": "Test",
        })
        with self.assertRaises(AccessError):
            self.as_outsider(price).action_approve()
        self.assertEqual(price.state, "draft")

    def instrument(self, **vals):
        return self.env["investra.instrument"].create({
            "name": "Akcie", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_equity").id, **vals,
        })

    def assert_stays_in_book(self, model, vals, field, target):
        record = self.as_outsider(self.env[model]).create(vals)
        original = record.sudo()[field]
        with self.assertRaises(UserError):
            record.write({field: target.id})
        self.assertEqual(record.sudo()[field], original)
        record.write({field: original.id})

    def test_movement_stays_in_book(self):
        self.assert_stays_in_book("investra.class.movement", {
            "class_id": self.cls(self.own, "A").id, "date": "2037-01-15", "movement_type": "subscription", "amount": 100, "units": 1,
        }, "class_id", self.cls(self.fund, "A"))

    def test_trade_stays_in_book(self):
        self.assert_stays_in_book("investra.trade", {
            "fund_id": self.own.id, "instrument_id": self.instrument().id, "trade_date": "2037-01-15", "quantity": 1, "price": 1,
        }, "fund_id", self.fund)

    def test_price_stays_in_book(self):
        self.assert_stays_in_book("investra.instrument.price", {
            "fund_id": self.own.id, "instrument_id": self.instrument().id, "date": "2037-01-15", "price": 1, "source": "Test",
        }, "fund_id", self.fund)

    def test_repayment_stays_in_book(self):
        deposit = self.instrument(type_id=self.env.ref("investra_instruments.type_deposit").id)
        held = self.classify(self.own, deposit, "hold_to_collect").portfolio_id
        self.assert_stays_in_book("investra.instrument.repayment", {
            "fund_id": self.own.id, "portfolio_id": held.id, "instrument_id": deposit.id, "date": "2037-01-15", "amount": 1,
        }, "fund_id", self.fund)

    def test_valuation_stays_in_book(self):
        self.assert_stays_in_book("investra.valuation", {"fund_id": self.own.id, "date": "2037-02-28", "version": 1}, "fund_id", self.fund)

    def test_external_stays_in_book(self):
        rule = self.env["investra.fee.rule"].create({"fund_id": self.own.id, "name": "Mimo Odoo", "kind": "external"})
        valuation = self.as_outsider(self.env["investra.valuation"]).create({"fund_id": self.own.id, "date": "2037-01-31", "version": 1})
        self.assert_stays_in_book("investra.valuation.external", {
            "valuation_id": valuation.id, "rule_id": rule.id, "amount": 1,
        }, "valuation_id", self.foreign)

    def test_context_cannot_set_valuation_state(self):
        valuation = self.as_outsider(self.env["investra.valuation"]).with_context(default_state="published").create({
            "fund_id": self.own.id, "date": "2037-01-31", "version": 1,
        })
        self.assertEqual(valuation.state, "draft")

    def test_booked_movement_is_locked(self):
        movement = self.subscribe(self.cls(self.fund, "A"), "2037-01-15", 100, 1)
        with self.assertRaises(UserError):
            movement.with_user(self.preparer).write({"units": 2})
        with self.assertRaises(UserError):
            movement.with_user(self.preparer).unlink()

    def test_movement_event_is_system_field(self):
        event = self.subscribe(self.cls(self.fund, "A"), "2037-01-15", 100, 1).event_id
        vals = {"class_id": self.cls(self.fund, "A").id, "date": "2037-01-16", "movement_type": "subscription", "amount": 1, "units": 1}
        Movement = self.env["investra.class.movement"].with_user(self.preparer)
        with self.assertRaises(UserError):
            Movement.create({**vals, "event_id": event.id})
        with self.assertRaises(UserError):
            Movement.create(vals).write({"event_id": event.id})

    def test_preparer_deletes_unbooked_movement(self):
        movement = self.as_outsider(self.env["investra.class.movement"]).create({
            "class_id": self.cls(self.own, "A").id, "date": "2037-01-15", "movement_type": "subscription", "amount": 100, "units": 1,
        })
        movement.write({"units": 2})
        movement.unlink()
        self.assertFalse(movement.exists())
