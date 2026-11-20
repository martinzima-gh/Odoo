from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestDividendEvent(NavCase):
    """ZJ-22: dividenda se zadává na cenný papír; držitelé (fond, portfolio) se načtou k večeru dne před ex-datem.

    Fond 1 a fond 2 drží stejnou akcii, fond 3 ne. Ex-datum 10. 4., výplata 20. 4. 2031, dividenda 10 na kus.
    """

    def setUp(self):
        super().setUp()
        self.funds = []
        for _index in range(3):
            fund = self.make_fund(classes=[{"code": "A"}])
            self.subscribe(self.cls(fund, "A"), "2031-03-01", 100000, 1000)
            self.funds.append(fund)
        self.companies = [fund.company_id.id for fund in self.funds]
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=self.companies))
        self.stock = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Akcie ZJ-22", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id}, self.funds[0]))
        for fund, quantity in zip(self.funds[:2], (1000, 500)):
            self.classify(fund, self.stock, "fair_value")
            trade = self.env["investra.trade"].create({
                "fund_id": fund.id, "portfolio_id": self.portfolio(fund).id, "instrument_id": self.stock.id,
                "trade_date": "2031-03-02", "quantity": quantity, "price": 100, "fx_rate": 1})
            trade.with_user(self.preparer).action_book()

    def event(self, **vals):
        return self.env["investra.dividend.event"].create({
            "instrument_id": self.stock.id, "ex_date": "2031-04-10", "pay_date": "2031-04-20", "per_share": 10,
            "kind": "domestic", **vals})

    def as_preparer(self, record, companies=None):
        return record.with_user(self.preparer).with_context(allowed_company_ids=companies or self.companies)

    def test_load_holders_across_funds(self):
        event = self.event()
        self.as_preparer(event).action_load_holders()
        lines = event.line_ids
        self.assertEqual({l.fund_id for l in lines}, set(self.funds[:2]))  # třetí fond nedrží
        self.assertEqual({l.fund_id.id: (l.units, l.gross_amount, l.withheld_amount, l.net_amount) for l in lines},
                         {self.funds[0].id: (1000, 10000, 1500, 8500), self.funds[1].id: (500, 5000, 750, 4250)})
        self.assertEqual((event.gross_total, event.withheld_total, event.net_total), (15000, 2250, 12750))
        self.as_preparer(event).action_load_holders()  # opakované načtení nic nepřidá
        self.assertEqual(len(event.line_ids), 2)
        self.assertEqual(event.state, "draft")

    def test_book_and_pay_per_fund_book(self):
        event = self.event()
        self.as_preparer(event).action_load_holders()
        result = self.as_preparer(event).action_book_all()
        self.assertEqual(event.state, "booked", result["params"]["message"])
        for line in event.line_ids:
            self.assertEqual(line.event_id.company_id, line.fund_id.company_id)  # doklad v knize svého fondu
        self.as_preparer(event).action_pay_all()
        self.assertEqual(event.state, "paid")
        self.assertEqual(set(event.line_ids.mapped("state")), {"paid"})

    def test_partial_booking_with_limited_rights(self):
        limited = self._make_user("div_limited", "investra_entity.group_valuation_preparer")
        limited.write({"company_ids": [(6, 0, [self.companies[0]])], "company_id": self.companies[0]})
        event = self.event()
        self.as_preparer(event).action_load_holders()
        event.with_user(limited).with_context(allowed_company_ids=[self.companies[0]]).action_book_all()
        by_fund = {l.fund_id: l.state for l in event.line_ids}
        self.assertEqual(by_fund, {self.funds[0]: "booked", self.funds[1]: "draft"})
        self.assertEqual(event.state, "draft")

    def test_reverse_one_line_and_duplicate_event(self):
        event = self.event()
        self.as_preparer(event).action_load_holders()
        self.as_preparer(event).action_book_all()
        first, second = event.line_ids.sorted("id")
        self.as_preparer(first).action_reverse("Chyba")
        self.assertEqual(event.state, "booked")
        with self.assertRaises(UserError):  # jedna událost na cenný papír a ex-datum
            self.event()
        self.as_preparer(second).action_reverse("Chyba")
        self.assertEqual(event.state, "reversed")
        self.assertTrue(self.event())  # oprava dalším záznamem po stornu

    def test_header_change_propagates_and_locks(self):
        event = self.event()
        self.as_preparer(event).action_load_holders()
        event.per_share = 12
        self.assertEqual(sorted(event.line_ids.mapped("gross_amount")), [6000, 12000])
        event.pay_date = "2031-04-25"
        self.assertEqual(set(event.line_ids.mapped("pay_date")), {date(2031, 4, 25)})
        self.as_preparer(event).action_book_all()
        with self.assertRaises(UserError):
            event.ex_date = "2031-04-11"
        event.pay_date = "2031-04-28"  # výplatu jde posunout i po zaúčtování
        self.assertEqual(set(event.line_ids.mapped("pay_date")), {date(2031, 4, 28)})

    def test_line_created_directly_gets_event(self):
        values = {"fund_id": self.funds[0].id, "instrument_id": self.stock.id, "portfolio_id": self.portfolio(self.funds[0]).id,
                  "ex_date": "2031-04-10", "pay_date": "2031-04-20", "per_share": 10}
        one = self.env["investra.dividend"].create(values)
        two = self.env["investra.dividend"].create({**values, "fund_id": self.funds[1].id, "portfolio_id": self.portfolio(self.funds[1]).id})
        self.assertTrue(one.dividend_event_id)
        self.assertEqual(one.dividend_event_id, two.dividend_event_id)

    def test_foreign_event_defaults_to_lines(self):
        event = self.event(kind="foreign", withholding_rate=25, treaty_rate=15)
        self.as_preparer(event).action_load_holders()
        line = event.line_ids.filtered(lambda l: l.fund_id == self.funds[0])
        self.assertEqual((line.withheld_amount, line.creditable_amount, line.excess_amount), (2500, 1500, 1000))

    def test_migration_groups_existing_lines(self):
        import importlib.util
        from odoo.modules import get_module_path
        path = get_module_path("investra_nav") + "/migrations/20.0.0.41.0/post-migration.py"
        spec = importlib.util.spec_from_file_location("zj22_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        migrate = module.migrate
        values = {"instrument_id": self.stock.id, "ex_date": "2031-04-10", "pay_date": "2031-04-20", "per_share": 10}
        lines = self.env["investra.dividend"]
        for fund in self.funds[:2]:
            lines |= self.env["investra.dividend"].create({**values, "fund_id": fund.id, "portfolio_id": self.portfolio(fund).id})
        event = lines.dividend_event_id
        self.env.cr.execute("UPDATE investra_dividend SET dividend_event_id = NULL WHERE id IN %s", (tuple(lines.ids),))
        event.invalidate_recordset(); lines.invalidate_recordset()
        self.env.cr.execute("DELETE FROM investra_dividend_event WHERE id = %s", (event.id,))
        migrate(self.env.cr, "20.0.0.39.0")
        lines.invalidate_recordset()
        self.assertEqual(len(lines.dividend_event_id), 1)
        self.assertEqual(lines.dividend_event_id.per_share, 10)
