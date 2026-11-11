from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_instrument import InstrumentCase


@tagged("post_install", "-at_install")
class TestClassification(InstrumentCase):
    """Klasifikace podle obchodního modelu fondu (plán docs/navrh-klasifikace-ifrs9.md, rozhodnutí 2026-11-11)."""

    def bond(self):
        return self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id,
        })

    def trade(self, instrument, quantity, day="2026-11-02", portfolio=None, fund=None):
        fund = fund or self.fund
        vals = {"fund_id": fund.id, "instrument_id": instrument.id, "trade_date": day, "quantity": quantity, "price": 100}
        if portfolio:
            vals["portfolio_id"] = portfolio.id
        return self.env["investra.trade"].create(vals)

    def test_new_fund_has_main_portfolio(self):
        self.assertEqual(self.fund.portfolio_ids.mapped("name"), ["Hlavní"])
        self.assertEqual(self.fund.portfolio_ids.business_model, "other")
        self.assertEqual(self.trade(self.instrument, 1).portfolio_id, self.fund.portfolio_ids)

    def test_two_portfolios_need_choice(self):
        self.portfolio(self.fund, "hold_to_collect")
        with self.assertRaises(UserError):
            self.trade(self.instrument, 1)

    def test_trade_without_classification_is_not_booked(self):
        trade = self.trade(self.bond(), 1)
        self.assertFalse(trade.classification_id)
        with self.assertRaises(UserError):
            trade._book()
        self.assertEqual(trade.state, "draft")

    def test_same_instrument_in_two_portfolios(self):
        bond = self.bond()
        main = self.fund.portfolio_ids
        held = self.portfolio(self.fund, "hold_to_collect")
        fair = self.classify(self.fund, bond)
        amortised = self.classify(self.fund, bond, "hold_to_collect")
        first = self.trade(bond, 10, portfolio=main)
        second = self.trade(bond, 4, portfolio=held)
        self.assertEqual((first.classification_id, second.classification_id), (fair, amortised))
        self.assertEqual((first.ifrs9_category, second.ifrs9_category), ("fvtpl", "amortised"))
        Trade = self.env["investra.trade"]
        self.assertEqual(Trade._holdings(self.fund, date(2026, 11, 30)), {(bond, main): 10, (bond, held): 4})
        self.assertEqual(Trade._positions(self.fund, date(2026, 11, 30)), {bond: 14})

    def test_sale_is_limited_to_portfolio(self):
        bond = self.bond()
        main = self.fund.portfolio_ids
        held = self.portfolio(self.fund, "hold_to_collect")
        self.classify(self.fund, bond)
        self.classify(self.fund, bond, "hold_to_collect")
        self.trade(bond, 10, portfolio=main)._book()
        self.trade(bond, 4, portfolio=held)._book()
        with self.assertRaises(UserError):
            self.trade(bond, -5, day="2026-11-10", portfolio=held)._book()
        self.trade(bond, -4, day="2026-11-10", portfolio=held)._book()
        holdings = self.env["investra.trade"]._holdings(self.fund, date(2026, 11, 30))
        self.assertEqual(holdings, {(bond, main): 10})

    def test_two_funds_classify_independently(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 2", "fund", "cas501", self.czk, "investra_fund")
        env = self.env(context=dict(self.env.context, allowed_company_ids=[self.company.id, other_book.company_id.id]))
        other = env["investra.fund"].create({"entity_id": other_book.id})
        bond = self.bond()
        first = self.classify(self.fund, bond)
        self.trade(bond, 1)._book()
        second = env["investra.portfolio.classification"].create({
            "portfolio_id": env["investra.fund.portfolio"].create({
                "fund_id": other.id, "name": "Inkaso", "business_model": "hold_to_collect",
            }).id,
            "instrument_id": bond.id, "valid_from": "2000-01-01", "sppi": "pass",
        })
        self.assertEqual((first.ifrs9_category, second.ifrs9_category), ("fvtpl", "amortised"))

    def test_reserved_instrument_only_in_own_fund(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 3", "fund", "cas501", self.czk, "investra_fund")
        env = self.env(su=True)
        other = env["investra.fund"].create({"entity_id": other_book.id})
        holding = self.env["investra.instrument"].create({
            "name": "Podíl", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_other_holding").id,
            "fund_id": self.fund.id, "holding_kind": "shares",
        })
        with self.assertRaises(ValidationError):
            env["investra.portfolio.classification"].create({
                "portfolio_id": other.portfolio_ids.id, "instrument_id": holding.id, "valid_from": "2000-01-01",
            })

    def test_portfolio_must_belong_to_fund(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 4", "fund", "cas501", self.czk, "investra_fund")
        other = self.env(su=True)["investra.fund"].create({"entity_id": other_book.id})
        with self.assertRaises(ValidationError):
            self.env(su=True)["investra.trade"].create({
                "fund_id": self.fund.id, "portfolio_id": other.portfolio_ids.id, "instrument_id": self.instrument.id,
                "trade_date": "2026-11-02", "quantity": 1, "price": 1,
            })
