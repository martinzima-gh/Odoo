from datetime import date

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged


class InstrumentCase(TransactionCase):
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
            {"name": "Akcie X", "currency_id": cls.eur.id, "type_id": cls.env.ref("investra_instruments.type_equity").id}
        )

        def user(login, group):
            return cls.env["res.users"].create({
                "name": login, "login": login, "company_id": cls.company.id, "company_ids": [(6, 0, [cls.company.id])],
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
            })

        cls.preparer = user("inst_prep", "investra_entity.group_valuation_preparer")
        cls.approver = user("inst_appr", "investra_entity.group_valuation_approver")


@tagged("post_install", "-at_install")
class TestInstrument(InstrumentCase):
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

    def test_state_cannot_be_written_directly(self):
        price = self.price()
        with self.assertRaises(UserError):
            price.with_user(self.preparer).write({"state": "approved"})
        with self.assertRaises(UserError):
            price.with_user(self.preparer).write({"entered_by": self.approver.id})
        with self.assertRaises(UserError):
            self.env["investra.instrument.price"].with_user(self.preparer).create({
                "instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-12-31",
                "price": 1, "source": "x", "state": "approved",
            })

    def test_approved_price_is_immutable(self):
        price = self.price()
        price.with_user(self.approver).action_approve()
        with self.assertRaises(UserError):
            price.with_user(self.preparer).write({"price": 11})
        with self.assertRaises(UserError):
            price.with_user(self.preparer).unlink()

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


@tagged("post_install", "-at_install")
class TestInstrumentType(InstrumentCase):
    """Typ navrhuje hodnoty, rozhoduje nástroj."""

    def make(self, code, **vals):
        return self.env["investra.instrument"].create({
            "name": code, "currency_id": self.czk.id, "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })

    def test_type_prefills_proposal(self):
        deposit = self.make("deposit")
        self.assertEqual(deposit.ifrs9_category, "amortised")
        self.assertEqual(deposit.valuation_method, "amortised")
        self.assertEqual(deposit.role_id.code, "deposit")
        self.assertFalse(deposit.deviates_from_type)

    def test_accountant_can_override_proposal(self):
        bond = self.make("bond")
        bond.with_user(self.preparer).write({"ifrs9_category": "fvoci"})
        self.assertEqual(bond.ifrs9_category, "fvoci")
        self.assertTrue(bond.deviates_from_type)
        self.assertEqual(self.env.ref("investra_instruments.type_bond").ifrs9_category, "fvtpl")

    def test_override_is_tracked(self):
        bond = self.make("bond")
        self.env.cr.flush()  # Změna ve stejné transakci jako založení se nezaznamenává.
        bond.write({"ifrs9_category": "fvoci"})
        self.env.cr.flush()
        messages = self.env["mail.message"].search([
            ("model", "=", "investra.instrument"), ("res_id", "=", bond.id), ("message_type", "=", "tracking"),
        ])
        self.assertEqual(len(messages), 1)
        self.assertIn("Kategorie IFRS 9", str(messages.body))

    def test_override_at_creation_keeps_rest_of_proposal(self):
        bond = self.make("bond", ifrs9_category="fvoci")
        self.assertEqual(bond.ifrs9_category, "fvoci")
        self.assertEqual(bond.role_id.code, "instrument_debt")
        self.assertEqual(bond.cnb_sheet, "DOFO31_12")

    def test_form_type_change_fills_proposal(self):
        with Form(self.env["investra.instrument"]) as form:
            form.name = "Vklad"
            form.currency_id = self.czk
            form.type_id = self.env.ref("investra_instruments.type_deposit")
            self.assertEqual(form.ifrs9_category, "amortised")

    def test_amortised_needs_matching_method(self):
        with self.assertRaises(ValidationError):
            self.make("bond", ifrs9_category="amortised")

    def test_classification_locked_after_trade(self):
        bond = self.make("bond")
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "trade_date": "2026-11-02", "quantity": 1, "price": 10,
        })
        with self.assertRaises(UserError):
            bond.with_user(self.preparer).write({"ifrs9_category": "fvoci"})
        bond.with_user(self.preparer).write({"name": "Nový název"})

    def test_linear_needs_note(self):
        with self.assertRaises(ValidationError):
            self.make("deposit", accrual_method="linear")
        with self.assertRaises(ValidationError):
            self.fund.accrual_method = "linear"

    def test_effective_accrual(self):
        deposit = self.make("deposit")
        self.assertEqual(self.fund.accrual_method, "eir")
        self.assertEqual(deposit._effective_accrual(self.fund), "eir")
        self.fund.write({"accrual_method": "linear", "accrual_note": "Nevýznamný rozdíl"})
        self.assertEqual(deposit._effective_accrual(self.fund), "linear")
        deposit.accrual_method = "eir"
        self.assertEqual(deposit._effective_accrual(self.fund), "eir")

    def test_other_holding_is_own_group(self):
        holding = self.make("other_holding", fund_id=self.fund.id, holding_kind="shares", commitment_amount=5000)
        self.assertEqual(holding.type_group, "other_holding")
        self.assertEqual(holding.valuation_method, "position")
        self.assertEqual(holding.cnb_sheet, "RIS33_13")

    def test_other_holding_requires_fund_and_kind(self):
        with self.assertRaises(ValidationError):
            self.make("other_holding")

    def test_commitment_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self.make("other_holding", fund_id=self.fund.id, holding_kind="shares", commitment_amount=-1)

    def test_other_holding_trade_is_not_booked(self):
        holding = self.make("other_holding", fund_id=self.fund.id, holding_kind="shares")
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": holding.id, "trade_date": "2026-11-02", "quantity": 1, "price": 10,
        })
        with self.assertRaises(UserError):
            trade._book()


@tagged("post_install", "-at_install")
class TestTradeCompanyAccess(InstrumentCase):
    """Přípravář jedné společnosti nesmí účtovat obchod jiné společnosti."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        other_book = cls.env["investra.entity"].sudo().create_book("Fond cizí", "fund", "cas501", cls.czk, "investra_fund")
        other = cls.env(su=True, context=dict(cls.env.context, allowed_company_ids=[other_book.company_id.id]))
        fund = other["investra.fund"].create({"entity_id": other_book.id})
        cls.foreign_trade = other["investra.trade"].create({
            "fund_id": fund.id, "instrument_id": cls.instrument.id, "trade_date": "2026-11-02",
            "settlement_date": "2026-11-04", "quantity": 1, "price": 10,
        })

    def own_trade(self):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "trade_date": "2026-11-02",
            "settlement_date": "2026-11-04", "quantity": 1, "price": 10, "fx_rate": 25,
        })

    def test_preparer_cannot_book_other_company_trade(self):
        with self.assertRaises(AccessError):
            self.foreign_trade.with_user(self.preparer).action_book()
        self.assertEqual(self.foreign_trade.state, "draft")

    def test_preparer_cannot_settle_other_company_trade(self):
        self.foreign_trade.sudo()._book()
        with self.assertRaises(AccessError):
            self.foreign_trade.with_user(self.preparer).action_settle()
        self.assertEqual(self.foreign_trade.state, "unsettled")

    def test_preparer_books_and_settles_own_trade(self):
        trade = self.own_trade()
        trade.with_user(self.preparer).action_book()
        self.assertEqual(trade.state, "unsettled")
        trade.with_user(self.preparer).action_settle()
        self.assertEqual(trade.state, "settled")
