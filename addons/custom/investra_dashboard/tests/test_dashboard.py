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
        self.assertEqual(self.fund.dashboard_date_text, "31.01.2032")
        self.assertFalse(self.fund.dashboard_latest_published)
        self.assertEqual(self.fund.dashboard_status, "ok")
        # První ocenění fondu nemá předchozí období: karta ukáže pomlčku, ne nulu.
        self.assertFalse(self.fund.dashboard_has_result)
        self.assertFalse(self.fund.dashboard_result_period)

    def test_missed_valuation_is_not_alert(self):
        # MN-14: lhůta zveřejnění se nehlídá, upozornění „Ocenění po termínu“ zaniklo.
        self.fund.launch_date = self.today - timedelta(days=100)
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.dashboard_status, "none")
        self.assertEqual(self.fund.dashboard_next_state, "none")
        self.assertNotIn("termínu", self.fund.dashboard_exceptions or "")
        self.assertNotIn("dashboard_next_late", self.env["investra.fund"]._fields)

    def test_next_valuation_from_launch_date(self):
        # Fond bez ocenění: z Data vzniku (2026-12-31) a měsíční frekvence = poslední den dalšího měsíce.
        self.assertEqual(str(self.fund.dashboard_next_valuation), "2027-01-31")
        self.assertEqual(self.fund.dashboard_next_text, "31.01.2027")
        self.assertEqual(self.fund.dashboard_next_state, "none")
        self.assertFalse(self.fund.dashboard_next_valuation_id)
        self.assertEqual(self.fund.dashboard_status, "none")

    def test_fund_without_launch_date_has_no_next(self):
        self.fund.launch_date = False
        self.fund.invalidate_recordset()
        self.assertFalse(self.fund.dashboard_next_valuation)
        self.assertFalse(self.fund.dashboard_next_state)

    def test_deadline_soon_warns_and_overdue_is_danger(self):
        self.deadline(3)
        self.assertEqual(self.fund.dashboard_status, "warning")
        self.fund.invalidate_recordset()
        self.deadline(-1, report="JINY")
        self.assertEqual(self.fund.dashboard_status, "danger")
        self.assertEqual(self.fund.dashboard_exception_count, 2)

    def test_submitted_deadline_is_shown_without_exception(self):
        # Rozhodnutí 2026-11-14: podaný výkaz se ukáže jako „Podáno“, ale výjimku nevyvolá (dřív se skrýval).
        self.deadline(-1, state="submitted")
        self.assertEqual(self.fund.dashboard_status, "none")
        self.assertEqual(self.fund.dashboard_deadline_state, "submitted")
        self.assertIn("TEST", self.fund.dashboard_next_deadline)

    def test_deadline_priority(self):
        self.deadline(-30, state="submitted", period_end=self.today - timedelta(days=60))
        self.deadline(10, report="BLIZKY")
        self.assertEqual(self.fund.dashboard_deadline_state, "open")
        self.assertIn("BLIZKY", self.fund.dashboard_next_deadline)
        self.fund.invalidate_recordset()
        late = self.deadline(-2, report="POZDE")
        self.assertEqual(self.fund.dashboard_deadline_id, late)
        self.assertEqual(self.fund.dashboard_deadline_state, "overdue")
        self.assertIn("(+1 další)", self.fund.dashboard_next_deadline)
        self.assertEqual(self.fund.dashboard_deadline_due, late.due_date.strftime("%d.%m.%Y"))

    def test_draft_is_next_not_latest(self):
        # Poslední ocenění je jen zaúčtované; rozpracované je „další“ se stavem z modelu ocenění.
        # Rozpracované ocenění je další, jen když není později než očekávané datum z frekvence (MN-14).
        self.fund.launch_date = "2031-12-31"
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        draft = self.valuation(self.fund, "2032-01-31")
        self.assertFalse(self.fund.dashboard_valuation_id)
        self.assertEqual(self.fund.dashboard_status, "none")
        self.assertEqual(self.fund.dashboard_next_valuation_id, draft)
        self.assertEqual(self.fund.dashboard_next_valuation, draft.date)
        self.assertEqual(self.fund.dashboard_next_state, "draft")
        self.assertEqual(self.fund.dashboard_next_version, 1)
        self.assertEqual(self.fund.dashboard_next_text, "31.01.2032")

    def test_next_after_latest_from_frequency(self):
        valuation = self.posted()
        self.assertEqual(str(self.fund.dashboard_next_valuation), "2032-02-29")
        self.assertEqual(self.fund.dashboard_next_state, "none")
        self.assertFalse(self.fund.dashboard_next_valuation_id)
        self.fund.valuation_frequency = "quarterly"
        self.fund.invalidate_recordset()
        self.assertEqual(str(self.fund.dashboard_next_valuation), "2032-06-30")
        self.fund.valuation_frequency = "monthly"
        self.fund.invalidate_recordset()
        nxt = self.valuation(self.fund, "2032-02-29")
        self.assertEqual(self.fund.dashboard_next_valuation_id, nxt)
        self.assertEqual(self.fund.dashboard_next_state, "draft")
        self.assertGreater(nxt.date, valuation.date)

    def test_extraordinary_valuation_has_priority(self):
        self.posted()
        extra = self.valuation(self.fund, "2032-02-15")
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.dashboard_next_valuation_id, extra)
        self.assertEqual(str(self.fund.dashboard_next_valuation), "2032-02-15")

    def test_result_of_second_valuation(self):
        self.posted()
        self.subscribe(self.cls(self.fund, "A"), "2032-02-10", 500, 5)
        second = self.run_to_posted(self.valuation(self.fund, "2032-02-29"))
        self.fund.invalidate_recordset()
        lines = second.class_line_ids
        self.assertEqual(self.fund.dashboard_valuation_id, second)
        self.assertTrue(self.fund.dashboard_has_result)
        self.assertAlmostEqual(
            self.fund.dashboard_result, sum(lines.mapped("shared_result")) + sum(lines.mapped("delta")), places=2
        )
        # Výsledek nezahrnuje úpisy: změna FK minus pohyby investorů.
        flows = sum(lines.mapped("subscription_amount")) - sum(lines.mapped("redemption_amount"))
        self.assertAlmostEqual(
            self.fund.dashboard_result, second.fund_capital - second.previous_id.fund_capital - flows, places=2
        )
        self.assertEqual(self.fund.dashboard_result_period, "01.02.–29.02.2032")

    def test_checks_come_from_next_valuation(self):
        self.posted()
        nxt = self.valuation(self.fund, "2032-02-29")
        self.env["investra.valuation.check"].sudo().create({
            "valuation_id": nxt.id, "code": "test", "name": "Test", "status": "warning",
        })
        self.fund.invalidate_recordset()
        self.assertIn("Kontroly s upozorněním: 1", self.fund.dashboard_exceptions)

    def test_published_valuation_checks_are_hidden(self):
        """Kontroly zveřejněného a uzamčeného ocenění karta neukazuje; před zveřejněním ano."""
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        valuation = self.valuation(self.fund, "2032-01-31")
        self.run_to_posted(valuation)
        self.env["investra.valuation.check"].sudo().create({
            "valuation_id": valuation.id, "code": "test", "name": "Test", "status": "warning",
        })
        self.fund.invalidate_recordset()
        self.assertIn("Kontroly s upozorněním", self.fund.dashboard_exceptions)
        valuation.sudo().state = "published"
        self.fund.invalidate_recordset()
        self.assertNotIn("Kontroly s upozorněním", self.fund.dashboard_exceptions or "")
        self.assertFalse(self.fund.action_open_checks())

    def test_manual_is_default_source(self):
        self.assertEqual(self.deadline(3).source, "manual")

    def test_pending_price_warns(self):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Akcie", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        }))
        self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": self.today, "price": 1, "source": "Test",
        })
        # Ceny ke schválení jsou v bloku Ke zpracování (pro schvalovatele) a kartu zvednou na Upozornění.
        item = next(i for i in self.fund.dashboard_todo if i["key"] == "prices")
        self.assertEqual((item["count"], item["role"], item["warn"]), (1, "approver", True))
        self.assertEqual(self.fund.dashboard_status, "warning")
        self.assertFalse(self.fund.dashboard_exceptions)

    def test_action_opens_valuation(self):
        valuation = self.posted()
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.action_open_valuation()["res_id"], valuation.id)

    def test_action_opens_next_valuation(self):
        # Rozpracované ocenění je další, jen když není později než očekávané datum z frekvence (MN-14).
        self.fund.launch_date = "2031-12-31"
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        draft = self.valuation(self.fund, "2032-01-31")
        self.assertEqual(self.fund.action_open_next_valuation()["res_id"], draft.id)

    def test_todo_lists_valuation_step_for_role(self):
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        draft = self.valuation(self.fund, "2032-01-31")
        fund = self.fund.with_user(self.preparer)
        item = next(i for i in fund.dashboard_todo if i["key"] == "valuation_draft")
        self.assertEqual((item["count"], item["role"], item["mine"]), (1, "preparer", True))
        self.assertTrue(fund.dashboard_my_todo)
        approver_view = self.fund.with_user(self.approver)
        self.assertFalse(next(i for i in approver_view.dashboard_todo if i["key"] == "valuation_draft")["mine"])
        action = fund.action_open_todo("valuation_draft")
        self.assertEqual(action["res_model"], "investra.valuation")
        self.assertEqual(self.env["investra.valuation"].search(action["domain"]), draft)
        draft.action_compute()
        draft.action_submit()
        approver_view.invalidate_recordset()
        item = next(i for i in approver_view.dashboard_todo if i["key"] == "valuation_submitted")
        self.assertTrue(item["mine"])
        self.assertIn(self.fund, self.env["investra.fund"].with_user(self.approver).search([("dashboard_my_todo", "=", True)]))

    def test_my_step_follows_matrix(self):
        """„Můj krok“ u schválení: zadavatel se skupinou schvalovatele vlastní ocenění schválit nesmí."""
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        draft = self.valuation(self.fund, "2032-01-31")
        draft.action_compute()
        draft.action_submit()
        self.assertTrue(draft.approval_ids)

        def mine(user):
            fund = self.fund.with_user(user)
            fund.invalidate_recordset()
            return next(i for i in fund.dashboard_todo if i["key"] == "valuation_submitted")["mine"]

        self.assertTrue(mine(self.approver))
        draft.sudo().preparer_id = self.approver
        self.assertFalse(mine(self.approver))
        draft.sudo().preparer_id = self.preparer
        draft.approval_ids.sudo().allowed_user_ids = self.preparer
        self.assertFalse(mine(self.approver))

    def test_todo_sorted_my_step_first(self):
        self.subscribe(self.cls(self.fund, "A"), "2032-01-01", 1000, 10)
        draft = self.valuation(self.fund, "2032-01-31")
        draft.action_compute()
        draft.action_submit()
        self.env["investra.class.movement"].create({
            "class_id": self.cls(self.fund, "A").id, "date": "2032-02-05", "manual_reason": "Test",
            "movement_type": "subscription", "amount": 100, "units": 1,
        })
        todo = self.fund.with_user(self.approver).dashboard_todo
        self.assertGreater(len(todo), 1)
        self.assertEqual(todo[0]["key"], "valuation_submitted")
        self.assertEqual([i["mine"] for i in todo], sorted((i["mine"] for i in todo), reverse=True))

    def test_filters_and_card_links(self):
        Fund = self.env["investra.fund"]
        self.deadline(-1)
        self.assertIn(self.fund, Fund.search([("dashboard_deadline_state", "=", "overdue")]))
        self.assertNotIn(self.fund, Fund.search([("dashboard_deadline_state", "in", ["open", "submitted"])]))
        self.assertEqual(self.fund.action_open_fund()["res_id"], self.fund.id)
        action = self.fund.action_open_deadlines()
        self.assertEqual(action["domain"], [("fund_id", "=", self.fund.id)])
        self.assertTrue(action["context"]["search_default_filter_open"])
        self.assertFalse(self.fund.action_open_checks())
        valuation = self.posted()
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.action_open_checks()["domain"][0], ("valuation_id", "=", valuation.id))

    def test_missing_price_and_outlook(self):
        """Držený nástroj bez ceny k nastalému dni ocenění zvedne kartu; výhled na 7 dnů je jen informace."""
        day = lambda days: self.today + timedelta(days=days)
        self.subscribe(self.cls(self.fund, "A"), day(-10), 50000, 500)
        bond = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Dluhopis {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "start_date": day(-10), "day_count": "thirty360_eu",
        }, self.fund))
        bond.cashflow_ids = [
            (0, 0, {"date": day(3), "amount": 30, "flow_type": "interest"}),
            (0, 0, {"date": day(400), "amount": 1000, "flow_type": "principal"}),
        ]
        self.classify(self.fund, bond)
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": bond.id,
            "trade_date": day(-5), "quantity": 10, "price": 1000,
        })
        trade._book()
        todo = lambda: {i["key"]: i for i in self.fund.dashboard_todo}
        # Den ocenění ještě nenastal: chybějící cena se nehlásí.
        self.fund.write({"launch_date": self.today, "valuation_frequency": "yearly"})
        self.fund.invalidate_recordset()
        self.assertNotIn("missing_prices", todo())
        # Denní frekvence od data před pěti dny: očekávané ocenění už nastalo.
        self.fund.write({"launch_date": day(-5), "valuation_frequency": "daily"})
        self.fund.invalidate_recordset()
        item = todo()["missing_prices"]
        self.assertEqual((item["count"], item["warn"]), (1, True))
        self.assertEqual(self.env[item["model"]].search(item["domain"]), bond)
        flows = todo()["soon_flows"]
        self.assertEqual((flows["count"], flows["info"], flows["mine"], flows["warn"]), (1, True, False, False))
        self.assertEqual(self.fund.dashboard_todo[-1]["key"], "soon_flows")
        self.assertEqual(self.fund.dashboard_todo_count, len([i for i in self.fund.dashboard_todo if not i["info"]]))
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": bond.id, "date": self.fund.dashboard_next_valuation, "price": 1000, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        self.fund.invalidate_recordset()
        self.assertNotIn("missing_prices", todo())

    def test_net_flow_lock_and_summary(self):
        cls = self.cls(self.fund, "A")
        self.subscribe(cls, "2032-01-01", 1000, 10)
        self.run_to_published(self.valuation(self.fund, "2032-01-31"))
        self.fund.invalidate_recordset()
        # První ocenění nemá období: úpisy − odkupy se neukazují; zveřejnění uzamklo období.
        self.assertFalse(self.fund.dashboard_net_flow)
        self.assertEqual(self.fund.dashboard_lock_text, "31.01.2032")
        self.assertFalse(self.fund.dashboard_lock_exception_count)
        self.subscribe(cls, "2032-02-10", 500, 5)
        self.subscribe(cls, "2032-02-20", 200, 2, kind="redemption")
        self.run_to_posted(self.valuation(self.fund, "2032-02-29"))
        self.fund.invalidate_recordset()
        self.assertEqual(self.fund.dashboard_net_flow, 300)
        summary = self.env["investra.fund"].dashboard_summary()
        self.assertEqual(summary["total"], self.env["investra.fund"].search_count([]))
        self.assertEqual([c["filter"] for c in summary["cards"]],
                         ["filter_danger", "filter_warning", "filter_my_todo"])

    def test_movement_draft_is_todo(self):
        movement = self.env["investra.class.movement"].create({
            "class_id": self.cls(self.fund, "A").id, "date": "2032-01-05", "manual_reason": "Test",
            "movement_type": "subscription", "amount": 100, "units": 1,
        })
        item = next(i for i in self.fund.dashboard_todo if i["key"] == "movements")
        self.assertEqual(self.env[item["model"]].search(item["domain"]), movement)
        # Běžná práce kartu nezvedá na Upozornění, jen čeká v bloku Ke zpracování.
        self.assertEqual(self.fund.dashboard_status, "none")

    def test_cards_sorted_by_urgency(self):
        quiet = self.make_fund(classes=[{"code": "A"}])
        # make_fund přepne povolené knihy na novou; pro srovnání obou fondů povolit obě.
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=(self.fund | quiet).company_id.ids))
        self.env["investra.regulatory.deadline"].create({
            "fund_id": self.fund.id, "report": "TEST", "period_end": self.today, "due_date": self.today - timedelta(days=1),
        })
        Fund = self.env["investra.fund"].with_context(investra_dashboard_order=1)
        result = Fund.web_search_read([("id", "in", (self.fund | quiet).ids)], {"name": {}})
        self.assertEqual([r["id"] for r in result["records"]], [self.fund.id, quiet.id])
        self.assertEqual(result["length"], 2)
        self.assertEqual(self.env["investra.fund"].search([("dashboard_status", "=", "danger"), ("id", "in", (self.fund | quiet).ids)]), self.fund)

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
