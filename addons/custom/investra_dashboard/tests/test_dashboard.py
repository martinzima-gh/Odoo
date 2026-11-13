from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.investra_nav.tests.common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestDashboard(NavCase):
    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.today = fields.Date.context_today(self.fund)

    def calendar(self, days):
        return self.env["investra.valuation.calendar"].create({"fund_id": self.fund.id, "date": self.today + timedelta(days=days)})

    def deadline(self, days, **vals):
        return self.env["investra.regulatory.deadline"].create({
            "fund_id": self.fund.id, "report": "TEST", "period_end": self.today, "due_date": self.today + timedelta(days=days), **vals,
        })

    def posted(self):
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        valuation = self.valuation(self.fund, "2032-01-31")
        self.run_to_posted(valuation)
        return valuation

    def test_fund_without_valuation(self):
        self.assertEqual(self.fund.dashboard_status, "none")
        self.assertFalse(self.fund.dashboard_valuation_id)

    def test_shows_latest_valuation(self):
        valuation = self.posted()
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.dashboard_valuation_id, valuation)
        self.assertEqual(self.fund.dashboard_capital, 1000)
        self.assertEqual(self.fund.dashboard_state, "Zaúčtováno")
        self.assertIn("A: 100.0000 CZK", self.fund.dashboard_prices)
        self.assertEqual(self.fund.dashboard_status, "ok")

    def test_overdue_valuation_is_danger(self):
        self.calendar(-1)
        self.assertEqual(self.fund.dashboard_status, "danger")
        self.assertIn("Ocenění po termínu", self.fund.dashboard_exceptions)

    def test_next_valuation(self):
        entry = self.calendar(5)
        self.assertEqual(self.fund.dashboard_next_valuation, entry.date)
        self.assertEqual(self.fund.dashboard_status, "none")

    def test_deadline_soon_warns_and_overdue_is_danger(self):
        self.deadline(3)
        self.assertEqual(self.fund.dashboard_status, "warning")
        self.fund.invalidate_recordset()
        self.deadline(-1, report="JINY")
        self.assertEqual(self.fund.dashboard_status, "danger")
        self.assertEqual(self.fund.dashboard_exception_count, 2)

    def test_submitted_deadline_is_ignored(self):
        self.deadline(-1, state="submitted")
        self.assertEqual(self.fund.dashboard_status, "none")
        self.assertFalse(self.fund.dashboard_next_deadline)

    def test_manual_is_default_source(self):
        self.assertEqual(self.deadline(3).source, "manual")

    def test_pending_price_warns(self):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Akcie", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        }))
        self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": self.today, "price": 1, "source": "Test",
        })
        self.assertIn("Ceny čekající", self.fund.dashboard_exceptions)

    def test_action_opens_valuation(self):
        valuation = self.posted()
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.action_open_valuation()["res_id"], valuation.id)

    def test_approver_cannot_change_deadline(self):
        deadline = self.deadline(3)
        with self.assertRaises(AccessError):
            deadline.with_user(self.approver).write({"state": "submitted"})

    def test_deadline_stays_in_book(self):
        deadline = self.deadline(5)
        other = self.make_fund(classes=[{"code": "A"}])
        with self.assertRaises(UserError):
            deadline.with_user(self.preparer).write({"fund_id": other.id})
        self.assertEqual(deadline.fund_id, self.fund)

    def test_views_load(self):
        result = self.env["investra.fund"].get_views([
            (self.env.ref("investra_dashboard.view_fund_dashboard_kanban").id, "kanban"),
            (self.env.ref("investra_dashboard.view_fund_dashboard_list").id, "list"),
        ])
        self.assertIn("kanban", result["views"])
