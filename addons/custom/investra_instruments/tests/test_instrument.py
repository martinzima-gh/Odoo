from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInstrument(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.eur = cls.env.ref("base.EUR")
        (cls.czk | cls.eur).active = True
        cls.book = cls.env["investra.entity"].create_book("Fond", "fund", "cas501", cls.czk, "investra_fund")
        cls.company = cls.book.company_id
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company.id]))
        cls.fund = cls.env["investra.fund"].create({"entity_id": cls.book.id})
        cls.instrument = cls.env["investra.instrument"].create(
            {"name": "Akcie X", "currency_id": cls.eur.id, "instrument_type": "equity"}
        )

        def user(login, group):
            return cls.env["res.users"].create({
                "name": login, "login": login, "company_id": cls.company.id, "company_ids": [(6, 0, [cls.company.id])],
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
            })

        cls.preparer = user("inst_prep", "investra_entity.group_valuation_preparer")
        cls.approver = user("inst_appr", "investra_entity.group_valuation_approver")

    def price(self, user=None):
        return self.env["investra.instrument.price"].with_user(user or self.preparer).create({
            "instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-11-30", "price": 10, "source": "test",
        })

    def test_preparer_cannot_approve(self):
        with self.assertRaises(UserError):
            self.price().action_approve()

    def test_approver_approves_foreign_price(self):
        price = self.price()
        price.with_user(self.approver).action_approve()
        self.assertEqual(price.state, "approved")
        self.assertEqual(price.approved_by, self.approver)

    def test_entered_by_cannot_approve_own(self):
        self.approver.group_ids |= self.env.ref("investra_entity.group_valuation_preparer")
        price = self.price(self.approver)
        with self.assertRaises(UserError):
            price.with_user(self.approver).action_approve()

    def test_approved_price_is_immutable(self):
        price = self.price()
        price.with_user(self.approver).action_approve()
        with self.assertRaises(UserError):
            price.write({"price": 11})
        with self.assertRaises(UserError):
            price.unlink()

    def test_trade_posts_event_with_instrument_and_currency(self):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "trade_date": date(2026, 11, 2),
            "quantity": 10, "price": 100, "fx_rate": 25,
        })
        trade._book()
        line = trade.event_id.move_id.line_ids.filtered("investra_instrument_id")
        self.assertEqual(line.balance, 25000)
        self.assertEqual(line.amount_currency, 1000)
        self.assertEqual(line.currency_id, self.eur)

    def test_positions_net_sale_and_respect_date(self):
        Trade = self.env["investra.trade"]
        base = {"fund_id": self.fund.id, "instrument_id": self.instrument.id, "price": 1}
        Trade.create({**base, "trade_date": "2026-11-02", "quantity": 10})
        Trade.create({**base, "trade_date": "2026-11-20", "quantity": -4})
        self.assertEqual(Trade._positions(self.fund, date(2026, 11, 10))[self.instrument], 10)
        self.assertEqual(Trade._positions(self.fund, date(2026, 11, 30))[self.instrument], 6)

    def test_closed_position_disappears(self):
        Trade = self.env["investra.trade"]
        base = {"fund_id": self.fund.id, "instrument_id": self.instrument.id, "price": 1}
        Trade.create({**base, "trade_date": "2026-11-02", "quantity": 10})
        Trade.create({**base, "trade_date": "2026-11-20", "quantity": -10})
        self.assertFalse(Trade._positions(self.fund, date(2026, 11, 30)))

    def test_instrument_in_hash(self):
        self.assertIn("investra_instrument_id", self.env["account.move.line"]._get_integrity_hash_fields())
