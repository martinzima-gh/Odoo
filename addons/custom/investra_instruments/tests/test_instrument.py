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
        cls.classify(cls.fund, cls.instrument)

        def user(login, group):
            return cls.env["res.users"].create({
                "name": login, "login": login, "company_id": cls.company.id, "company_ids": [(6, 0, [cls.company.id])],
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
            })

        cls.preparer = user("inst_prep", "investra_entity.group_valuation_preparer")
        cls.approver = user("inst_appr", "investra_entity.group_valuation_approver")

    @classmethod
    def portfolio(cls, fund, model="fair_value"):
        found = fund.portfolio_ids.filtered(lambda p: p.business_model == model)[:1]
        return found or cls.env["investra.fund.portfolio"].create({"fund_id": fund.id, "name": model, "business_model": model})

    @classmethod
    def classify(cls, fund, instrument, model="fair_value", day="2000-01-01", **vals):
        if model in ("hold_to_collect", "hold_collect_sell") and instrument.type_id.kind in ("bond", "loan", "deposit", "repo"):
            vals.setdefault("sppi", "pass")
            vals.setdefault("sppi_note", "Test: pevný úrok a jistina")
        return cls.env["investra.portfolio.classification"].create({
            "portfolio_id": cls.portfolio(fund, model).id, "instrument_id": instrument.id, "valid_from": day, **vals,
        })


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

    def test_context_cannot_approve_price(self):
        price = self.env["investra.instrument.price"].with_user(self.preparer).with_context(
            default_state="approved", default_approved_by=self.approver.id, default_entered_by=self.approver.id,
        ).create({"instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-11-30", "price": 10, "source": "test"})
        self.assertEqual(price.state, "draft")
        self.assertFalse(price.approved_by)
        self.assertEqual(price.entered_by, self.preparer)

    def test_create_cannot_set_entered_by(self):
        with self.assertRaises(UserError):
            self.env["investra.instrument.price"].with_user(self.preparer).create({
                "instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-11-30", "price": 10, "source": "test",
                "entered_by": self.approver.id,
            })

    def test_editor_of_draft_cannot_approve(self):
        self.approver.group_ids |= self.env.ref("investra_entity.group_valuation_preparer")
        price = self.price()
        price.with_user(self.approver).write({"price": 150})
        self.assertEqual(price.entered_by, self.approver)
        with self.assertRaises(UserError):
            price.with_user(self.approver).action_approve()

    def test_creator_cannot_approve_when_entered_by_differs(self):
        self.approver.group_ids |= self.env.ref("investra_entity.group_valuation_preparer")
        price = self.price(self.approver)
        price.sudo().entered_by = self.preparer
        with self.assertRaises(UserError):
            price.with_user(self.approver).action_approve()

    def test_approved_price_cannot_be_approved_again(self):
        price = self.price()
        price.with_user(self.approver).action_approve()
        second = self.approver.copy({"login": "inst_appr2"})
        with self.assertRaises(UserError):
            price.with_user(second).action_approve()
        self.assertEqual(price.approved_by, self.approver)

    def test_context_cannot_set_trade_state(self):
        trade = self.env["investra.trade"].with_user(self.preparer).with_context(default_state="settled").create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "trade_date": "2026-11-30", "quantity": 1, "price": 1,
        })
        self.assertEqual(trade.state, "draft")
        with self.assertRaises(UserError):
            self.env["investra.instrument.price"].with_user(self.preparer).create({
                "instrument_id": self.instrument.id, "fund_id": self.fund.id, "date": "2026-12-31",
                "price": 1, "source": "x", "state": "approved",
            })

    def test_approved_price_cannot_be_deleted_or_moved(self):
        # Opravu ceny řeší test_shared_price (rozhodnutí 2026-11-11); smazat ani přesunout ji nejde.
        price = self.price()
        price.with_user(self.approver).action_approve()
        with self.assertRaises(UserError):
            price.with_user(self.preparer).write({"date": "2026-11-29"})
        with self.assertRaises(UserError):
            price.with_user(self.preparer).unlink()

    def test_shared_price_needs_manager_book(self):
        with self.assertRaises(UserError):
            self.env["investra.instrument.price"].with_user(self.preparer).create({
                "instrument_id": self.instrument.id, "date": "2026-11-30", "price": 10, "source": "test",
            })

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
        fields = self.env["account.move.line"]._get_integrity_hash_fields()
        self.assertIn("investra_instrument_id", fields)
        # Odchylka od plánu klasifikace: zařazení v hashi není, aby nerozbilo hash dříve zaúčtovaných dokladů.
        self.assertNotIn("investra_classification_id", fields)

    def test_trade_line_carries_classification(self):
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "trade_date": "2026-11-02", "quantity": 1, "price": 1,
        })
        trade._book()
        line = trade.event_id.move_id.line_ids.filtered("investra_instrument_id")
        self.assertEqual(line.investra_classification_id, trade.classification_id)
        with self.assertRaises(UserError):
            line.write({"investra_classification_id": False})


@tagged("post_install", "-at_install")
class TestInstrumentType(InstrumentCase):
    """Typ navrhuje hodnoty, rozhoduje nástroj."""

    def make(self, code, **vals):
        return self.env["investra.instrument"].create({
            "name": code, "currency_id": self.czk.id, "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })

    def test_type_prefills_proposal(self):
        deposit = self.make("deposit")
        self.assertEqual(deposit.cnb_sheet, deposit.type_id.cnb_sheet)
        self.assertFalse(deposit.deviates_from_type)
        held = self.classify(self.fund, deposit, "hold_to_collect")
        self.assertEqual((held.ifrs9_category, held.valuation_method, held.role_id.code), ("amortised", "amortised", "deposit"))
        self.assertFalse(held.deviates_from_proposal)
        # Tentýž vklad v modelu Řízení na reálnou hodnotu: FVTPL, ocenění modelem (IFRS 9 4.1.4).
        other = self.classify(self.fund, deposit)
        self.assertEqual((other.ifrs9_category, other.valuation_method), ("fvtpl", "model"))

    def test_accountant_can_override_proposal(self):
        bond = self.make("bond")
        classification = self.classify(self.fund, bond)
        classification.with_user(self.preparer).write({"valuation_method": "model"})
        self.assertTrue(classification.deviates_from_proposal)
        self.assertEqual(self.env.ref("investra_instruments.type_bond").valuation_method, "price")

    def test_override_is_tracked(self):
        classification = self.classify(self.fund, self.make("bond"))
        self.env.cr.flush()  # Změna ve stejné transakci jako založení se nezaznamenává.
        classification.write({"valuation_method": "model"})
        self.env.cr.flush()
        messages = self.env["mail.message"].search([
            ("model", "=", "investra.portfolio.classification"), ("res_id", "=", classification.id), ("message_type", "=", "tracking"),
        ])
        self.assertEqual(len(messages), 1)

    def test_override_at_creation_keeps_rest_of_proposal(self):
        bond = self.make("bond")
        classification = self.classify(self.fund, bond, "hold_collect_sell", valuation_method="model")
        self.assertEqual(classification.ifrs9_category, "fvoci")
        self.assertEqual(classification.valuation_method, "model")
        self.assertEqual(classification.role_id.code, "instrument_debt")
        self.assertEqual(bond.cnb_sheet, "DOFO31_12")

    def test_form_fills_proposal(self):
        with Form(self.env["investra.instrument"]) as form:
            form.name = "Vklad"
            form.currency_id = self.czk
            form.type_id = self.env.ref("investra_instruments.type_deposit")
            self.assertEqual(form.cnb_sheet, self.env.ref("investra_instruments.type_deposit").cnb_sheet)
        deposit = self.make("deposit")
        with Form(self.env["investra.portfolio.classification"]) as form:
            form.portfolio_id = self.portfolio(self.fund, "hold_to_collect")
            form.instrument_id = deposit
            form.sppi = "pass"
            form.sppi_note = "Pevná sazba, jistina"
            self.assertEqual(form.instrument_nature, "debt")
            self.assertEqual(form.ifrs9_category, "amortised")
            self.assertEqual(form.valuation_method, "amortised")

    def test_amortised_needs_matching_method(self):
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("bond"), "hold_to_collect", valuation_method="price")

    def test_classification_locked_after_trade(self):
        bond = self.make("bond")
        classification = self.classify(self.fund, bond)
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "trade_date": "2026-11-02", "quantity": 1, "price": 10,
        })
        with self.assertRaises(UserError):
            classification.with_user(self.preparer).write({"valuation_method": "model"})
        with self.assertRaises(UserError):
            bond.with_user(self.preparer).write({"type_id": self.env.ref("investra_instruments.type_equity").id})
        with self.assertRaises(UserError):
            classification.unlink()
        with self.assertRaises(UserError):  # druhé zařazení po obchodu = reklasifikace, zatím není
            self.classify(self.fund, bond, day="2026-12-01")
        with self.assertRaises(UserError):
            self.fund.portfolio_ids.with_user(self.preparer).write({"business_model": "hold_to_collect"})
        bond.with_user(self.preparer).write({"name": "Nový název"})
        classification.with_user(self.preparer).write({"note": "Doplněné zdůvodnění"})

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
        self.assertEqual(self.classify(self.fund, holding).valuation_method, "position")
        self.assertEqual(holding.cnb_sheet, "RIS33_13")

    def test_other_holding_requires_fund_and_kind(self):
        with self.assertRaises(ValidationError):
            self.make("other_holding")

    def test_commitment_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self.make("other_holding", fund_id=self.fund.id, holding_kind="shares", commitment_amount=-1)

    def test_other_holding_trade_is_not_booked(self):
        holding = self.make("other_holding", fund_id=self.fund.id, holding_kind="shares")
        self.classify(self.fund, holding)
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
        other["investra.portfolio.classification"].create({
            "portfolio_id": fund.portfolio_ids.id, "instrument_id": cls.instrument.id, "valid_from": "2000-01-01",
        })
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


@tagged("post_install", "-at_install")
class TestChartRoles(InstrumentCase):
    def test_participation_at_fair_value_has_own_role(self):
        """Účast ve FVTPL má roli participation_fv (účet 413100), rozhodnutí 2026-11-11 a 2026-11-12."""
        participation = self.env["investra.instrument"].create({
            "name": "Účast Y", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_participation").id,
        })
        classification = self.classify(self.fund, participation)
        self.assertEqual(classification.ifrs9_category, "fvtpl")
        self.assertEqual(classification.role_id, self.env.ref("investra_entity.role_participation_fv"))
        self.assertFalse(classification.deviates_from_proposal)
