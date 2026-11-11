from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestSharedPriceValuation(NavCase):
    """Poslední známá cena, sdílená tržní cena a cena fondu v ocenění (rozhodnutí 2026-11-11)."""
    # Kurzy jsou v databázi společné a neměnné; kurz EUR v roce 2032 jiné testy neukládají.

    def setUp(self):
        super().setUp()
        manager = self.env["investra.entity"].create_book("Investiční společnost", "manager", "cas501", self.czk, "cz")
        self.manager_company = manager.company_id
        for user in (self.preparer, self.approver, self.approver2):
            user.company_ids = [(4, self.manager_company.id)]
        self.instrument = self.env["investra.instrument"].create({
            "name": "Akcie", "currency_id": self.eur.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        })
        self.fund = self.new_fund()
        self.day = date(2032, 1, 31)
        self.rate("2032-01-29", 26)

    def new_fund(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2032-01-01", 100000, 1000)
        self.env["investra.trade"].create({
            "fund_id": fund.id, "instrument_id": self.instrument.id, "trade_date": "2032-01-05",
            "quantity": 10, "price": 100, "fx_rate": 25,
        })._book()
        return fund

    def price(self, value, day=None, fund=None, **extra):
        companies = [self.manager_company.id] + self.env.context.get("allowed_company_ids", [])
        price = self.env["investra.instrument.price"].with_user(self.preparer).with_context(allowed_company_ids=companies).create({
            "instrument_id": self.instrument.id, "fund_id": fund.id if fund else False, "date": day or self.day,
            "price": value, "source": "Bloomberg", **extra,
        })
        price.with_user(self.approver).with_context(allowed_company_ids=companies).action_approve()
        return price

    def compute(self, fund=None):
        fund = fund or self.fund
        valuation = self.env["investra.valuation"].with_user(self.preparer).with_context(
            allowed_company_ids=[fund.company_id.id],
        ).create({"fund_id": fund.id, "date": self.day, "version": 1})
        valuation.action_compute()
        return valuation

    def line(self, valuation):
        return valuation.portfolio_line_ids.filtered("instrument_id")

    def status(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code).status

    def test_last_known_price_within_limit(self):
        self.instrument.max_price_age = 5
        price = self.price(110, day=date(2032, 1, 27))
        valuation = self.compute()
        self.assertEqual(self.line(valuation).price_id, price)
        self.assertEqual(self.line(valuation).price_date, date(2032, 1, 27))
        self.assertEqual(self.status(valuation, "price_age"), "ok")

    def test_stale_price_warns_but_does_not_stop(self):
        self.price(110, day=date(2032, 1, 20))
        valuation = self.compute()
        self.assertEqual(self.status(valuation, "price_age"), "warning")
        self.assertAlmostEqual(self.line(valuation).fair_value, 1100 * 26, places=2)

    def test_price_after_valuation_date_is_ignored(self):
        self.price(120, day=date(2032, 2, 1))
        with self.assertRaises(UserError):
            self.compute()

    def test_shared_price_serves_two_funds(self):
        shared = self.price(110)
        other = self.new_fund()
        for fund in (self.fund, other):
            valuation = self.compute(fund)
            self.assertEqual(self.line(valuation).price_id, shared)
            self.assertEqual(self.status(valuation, "price_fund_deviation"), "ok")
        self.assertEqual(shared.with_user(self.preparer)._used_in_valuations().fund_id, self.fund | other)

    def test_fund_price_wins_same_day_and_warns(self):
        self.price(110)
        own = self.price(105, fund=self.fund, deviation_reason="Posudek")
        valuation = self.compute()
        self.assertEqual(self.line(valuation).price_id, own)
        self.assertEqual(self.status(valuation, "price_fund_deviation"), "warning")

    def test_newer_shared_price_wins_over_older_fund_price(self):
        self.price(105, day=date(2032, 1, 30), fund=self.fund)
        shared = self.price(110)
        self.assertEqual(self.line(self.compute()).price_id, shared)

    def test_corrected_price_keeps_finished_valuation(self):
        shared = self.price(110)
        valuation = self.compute()
        companies = [self.manager_company.id] + self.env.context.get("allowed_company_ids", [])
        shared.with_user(self.preparer).with_context(allowed_company_ids=companies).write({"price": 120})
        self.assertEqual(shared.state, "draft")
        self.assertEqual(self.line(valuation).price, 110)
        self.assertIn(valuation, shared._used_in_valuations())
