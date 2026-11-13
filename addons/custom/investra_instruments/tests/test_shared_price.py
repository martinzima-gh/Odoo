from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .test_instrument import InstrumentCase
from .common import manager_book, with_ids


@tagged("post_install", "-at_install")
class TestSharedPrice(InstrumentCase):
    """Sdílené tržní ceny a cena fondu (rozhodnutí 2026-11-11, docs/navrh-sdilene-ceny.md)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager_book = manager_book(cls.env, cls.czk)
        cls.manager_company = cls.manager_book.company_id
        cls.both = [cls.manager_company.id, cls.company.id]
        for user in (cls.preparer, cls.approver):
            user.company_ids = [(4, cls.manager_company.id)]
        # Uživatel jen s knihou fondu: sdílené ceny čte, nezapisuje.
        cls.fund_only = cls.env["res.users"].create({
            "name": "fund_only", "login": "fund_only", "company_id": cls.company.id, "company_ids": [(6, 0, [cls.company.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref("investra_entity.group_valuation_preparer").id])],
        })
        cls.Price = cls.env["investra.instrument.price"]

    def shared(self, user=None, **values):
        return self.Price.with_user(user or self.preparer).with_context(allowed_company_ids=self.both).create({
            "instrument_id": self.instrument.id, "date": "2026-11-30", "price": 10, "source": "Bloomberg", **values,
        })

    def approve(self, price):
        price.with_user(self.approver).with_context(allowed_company_ids=self.both).action_approve()

    def test_shared_price_belongs_to_manager_book(self):
        price = self.shared()
        self.assertEqual(price.company_id, self.manager_company)
        self.assertEqual(price.scope, "shared")
        self.assertEqual(price.currency_id, self.eur)

    def test_duplicate_shared_price_rejected(self):
        self.shared()
        with self.assertRaises(Exception), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.shared(price=11)

    def test_fund_price_needs_reason_when_shared_exists(self):
        self.shared()
        values = {"instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-11-30", "price": 9, "source": "Posudek"}
        with self.assertRaises(ValidationError):
            self.Price.with_user(self.preparer).create(values)
        price = self.Price.with_user(self.preparer).create({**values, "deviation_reason": "Nelikvidní pozice"})
        self.assertEqual(price.scope, "fund")
        self.assertEqual(price.company_id, self.company)

    def test_currency_must_match_instrument(self):
        with self.assertRaises(ValidationError):
            self.shared(currency_id=self.czk.id)

    def test_fund_only_instrument_has_no_shared_price(self):
        own = self.env["investra.instrument"].create({
            "name": "Úvěr SPV", "currency_id": self.czk.id, "fund_id": self.fund.id,
            "type_id": self.env.ref("investra_instruments.type_loan").id, "identifier_kind": "contract", "identifier": "SPV-1",
        })
        with self.assertRaises(ValidationError):
            self.shared(instrument_id=own.id)
        price = self.Price.with_user(self.preparer).create({
            "instrument_id": own.id, "fund_id": self.fund.id, "date": "2026-11-30", "price": 1, "source": "Posudek",
        })
        self.assertEqual(price.fund_id, self.fund)

    def test_fund_user_reads_shared_price_but_cannot_change_it(self):
        price = self.shared()
        self.assertIn(price, self.Price.with_user(self.fund_only).search([("instrument_id", "=", self.instrument.id)]))
        with self.assertRaises(AccessError):
            price.with_user(self.fund_only).write({"price": 12})
        with self.assertRaises((AccessError, UserError)):
            self.shared(user=self.fund_only)

    def test_shared_price_cannot_move_to_fund(self):
        price = self.shared()
        with self.assertRaises(UserError):
            price.with_user(self.preparer).with_context(allowed_company_ids=self.both).write({"fund_id": self.fund.id})

    def test_correcting_approved_price_returns_it_for_approval(self):
        price = self.shared()
        self.approve(price)
        price.with_user(self.preparer).with_context(allowed_company_ids=self.both).write({"price": 11})
        self.assertEqual(price.state, "draft")
        self.assertFalse(price.approved_by)
        self.assertEqual(price.entered_by, self.preparer)
        self.approve(price)
        self.assertEqual((price.state, price.price), ("approved", 11))
        # Kdo cenu opravil, ji neschválí (schvalovatel s přípravou, jinak cenu měnit nesmí).
        self.approver.group_ids |= self.env.ref("investra_entity.group_valuation_preparer")
        price.with_user(self.approver).with_context(allowed_company_ids=self.both).write({"price": 12})
        with self.assertRaises(UserError):
            self.approve(price)

    def test_max_price_age_comes_from_type(self):
        kind = self.env.ref("investra_instruments.type_equity")
        kind.max_price_age = 5
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {"name": "Akcie Y", "currency_id": self.eur.id, "type_id": kind.id}, self.fund))
        self.assertEqual(instrument.max_price_age, 5)
