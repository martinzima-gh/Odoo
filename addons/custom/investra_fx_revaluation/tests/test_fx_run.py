from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestFxRun(AccountTestInvoicingCommon):
    """1 000 v cizí měně při kurzu 25, přecenění při 26 a 24."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.foreign = cls.setup_other_currency("EUR", rates=[
            ("2040-01-01", 1 / 25), ("2040-01-31", 1 / 26), ("2040-02-29", 1 / 24),
        ])
        cls.base = cls.company_data["company"].currency_id
        for day, value in ((date(2040, 1, 1), "25"), (date(2040, 1, 31), "26"), (date(2040, 2, 29), "24")):
            rates = {"EUR": (Decimal(1), Decimal(value)), cls.base.name: (Decimal(1), Decimal(1))}
            cls.env["investra.rate"].sudo()._store("cnb", day, rates, f"{day}{value}")
        cls.company = cls.company_data["company"]
        cls.receivable = cls.company_data["default_account_receivable"]
        cls.payable = cls.company_data["default_account_payable"]
        cls.revenue = cls.company_data["default_account_revenue"]
        cls.gain = cls.env["account.account"].create({"name": "Zisk z přecenění", "code": "663900", "account_type": "income_other"})
        cls.loss = cls.env["account.account"].create({"name": "Ztráta z přecenění", "code": "563900", "account_type": "expense"})
        cls.profile = cls.env["investra.fx.profile"].create({
            "name": "Pohledávky a závazky", "account_ids": [(6, 0, (cls.receivable | cls.payable).ids)],
            "gain_account_id": cls.gain.id, "loss_account_id": cls.loss.id, "journal_id": cls.company_data["default_journal_misc"].id,
        })

    def entry(self, account, amount_currency, balance, day="2040-01-02", post=True, currency=None):
        move = self.env["account.move"].create({
            "move_type": "entry", "date": day, "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                (0, 0, {"account_id": account.id, "partner_id": self.partner_a.id, "currency_id": (currency or self.foreign).id,
                        "amount_currency": amount_currency, "balance": balance}),
                (0, 0, {"account_id": self.revenue.id, "currency_id": (currency or self.foreign).id,
                        "amount_currency": -amount_currency, "balance": -balance}),
            ],
        })
        if post:
            move.action_post()
        return move

    def create_run(self, day="2040-01-31"):
        run = self.env["investra.fx.run"].create({"profile_id": self.profile.id, "date": day})
        run.action_compute()
        return run

    def test_receivable_gain_goes_to_own_account_as_draft(self):
        self.entry(self.receivable, 1000, 25000)
        run = self.create_run()
        self.assertEqual(run.line_ids.rate, 26)
        self.assertEqual(run.line_ids.target, 26000)
        self.assertEqual(run.difference, 1000)
        run.action_create_move()
        self.assertEqual(run.move_id.state, "draft")
        counter = run.move_id.line_ids.filtered(lambda l: l.account_id == self.gain)
        self.assertEqual(counter.balance, -1000)
        self.assertFalse(run.move_id.line_ids.filtered(lambda l: l.account_id == self.company.income_currency_exchange_account_id))

    def test_payable_loss(self):
        self.entry(self.payable, -1000, -25000)
        run = self.create_run()
        self.assertEqual(run.difference, -1000)
        run.action_create_move()
        self.assertEqual(run.move_id.line_ids.filtered(lambda l: l.account_id == self.loss).balance, 1000)

    def test_second_run_tops_up_to_required_balance(self):
        self.entry(self.receivable, 1000, 25000)
        first = self.create_run()
        first.action_create_move()
        first.move_id.action_post()
        second = self.create_run("2040-02-29")
        self.assertEqual(second.line_ids.balance, 26000)
        self.assertEqual(second.difference, -2000)

    def test_settled_item_reverses_previous_revaluation(self):
        self.entry(self.receivable, 1000, 25000)
        first = self.create_run()
        first.action_create_move()
        first.move_id.action_post()
        self.entry(self.receivable, -1000, -25000, day="2040-02-10")
        second = self.create_run("2040-02-29")
        self.assertEqual(second.line_ids.amount_currency, 0)
        self.assertEqual(second.difference, -1000)

    def test_repeated_compute_replaces_proposal(self):
        self.entry(self.receivable, 1000, 25000)
        run = self.create_run()
        run.action_create_move()
        move = run.move_id
        run.action_compute()
        self.assertFalse(move.exists())
        self.assertEqual(len(run.line_ids), 1)

    def test_posted_run_is_locked(self):
        self.entry(self.receivable, 1000, 25000)
        run = self.create_run()
        run.action_create_move()
        run.move_id.action_post()
        with self.assertRaises(UserError):
            run.action_compute()

    def post_run(self, day="2040-01-31"):
        run = self.create_run(day)
        run.action_create_move()
        run.move_id.action_post()
        return run

    def test_backdated_document_adds_only_its_difference(self):
        self.entry(self.receivable, 1000, 25000)
        first = self.post_run()
        self.entry(self.receivable, 500, 12500, day="2040-01-20")
        extra = self.create_run()
        self.assertEqual(extra.difference, 500)
        extra.action_create_move()
        self.assertEqual(extra.move_id.date, date(2040, 1, 31))
        self.assertEqual(extra.move_id.state, "draft")
        self.assertEqual(first.move_id.state, "posted")

    def test_repeat_without_change_has_no_difference(self):
        self.entry(self.receivable, 1000, 25000)
        self.post_run()
        extra = self.create_run()
        self.assertFalse(extra.line_ids)
        with self.assertRaises(UserError):
            extra.action_create_move()

    def test_two_open_proposals_are_refused(self):
        self.entry(self.receivable, 1000, 25000)
        self.create_run().action_create_move()
        with self.assertRaises(UserError):
            self.create_run()

    def test_earlier_run_after_posted_later_run_warns(self):
        self.entry(self.receivable, 1000, 25000)
        self.post_run("2040-02-29")
        earlier = self.create_run("2040-01-31")
        self.assertTrue(earlier.later_run_warning)
        self.assertEqual(earlier.difference, 1000)

    def test_no_warning_without_later_run(self):
        self.entry(self.receivable, 1000, 25000)
        self.assertFalse(self.create_run().later_run_warning)

    def test_locked_period_stops_proposal(self):
        self.entry(self.receivable, 1000, 25000)
        run = self.create_run()
        self.company.sudo().write({"hard_lock_date": "2040-01-31"})
        with self.assertRaises(UserError):
            run.action_create_move()
        self.assertFalse(run.move_id)

    def test_draft_documents_and_other_accounts_are_ignored(self):
        self.entry(self.receivable, 1000, 25000, post=False)
        self.assertFalse(self.create_run().line_ids)

    def test_document_on_valuation_day_is_included_at_that_days_rate(self):
        self.entry(self.receivable, 1000, 25000, day="2040-01-31")
        self.assertEqual(self.create_run().difference, 1000)

    def test_nothing_to_revalue_stops_move(self):
        with self.assertRaises(UserError):
            self.create_run().action_create_move()

    def test_incomplete_profile_stops(self):
        self.profile.gain_account_id = False
        with self.assertRaises(UserError):
            self.create_run()

    def test_missing_rate_stops(self):
        self.entry(self.receivable, 1000, 25000, day="2039-12-01")
        with self.assertRaises(UserError):
            self.create_run("2039-12-31")

    def test_stale_rate_stops(self):
        self.entry(self.receivable, 1000, 25000)
        with self.assertRaises(UserError):
            self.create_run("2040-01-20")

    def test_allowed_age_comes_from_profile(self):
        self.profile.max_rate_age_days = 30
        self.entry(self.receivable, 1000, 25000)
        self.assertFalse(self.create_run("2040-01-20").line_ids)

    def test_later_rate_is_never_used(self):
        self.profile.max_rate_age_days = 30
        self.entry(self.receivable, 1000, 24000)
        self.assertEqual(self.create_run("2040-01-30").line_ids.rate, 25)

    def test_lines_are_hidden_from_other_company(self):
        other = self.env["res.company"].create({"name": "Jiná společnost FX"})
        reader = self.env["res.users"].create({
            "name": "fx_jina", "login": "fx_jina", "company_id": other.id, "company_ids": [(6, 0, other.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("account.group_account_readonly").id])],
        })
        self.entry(self.receivable, 1000, 25000)
        line = self.create_run().line_ids
        Lines = self.env["investra.fx.run.line"].with_user(reader).with_context(allowed_company_ids=other.ids)
        self.assertFalse(Lines.search([("id", "=", line.id)]))
        with self.assertRaises(AccessError):
            Lines.browse(line.id).read(["difference"])

    def test_lines_are_visible_in_own_company(self):
        self.entry(self.receivable, 1000, 25000)
        line = self.create_run().line_ids
        self.assertEqual(self.env["investra.fx.run.line"].search([("id", "=", line.id)]), line)

    def test_reader_cannot_compute(self):
        reader = self.env["res.users"].create({
            "name": "fx_cteni", "login": "fx_cteni", "company_id": self.company.id, "company_ids": [(6, 0, self.company.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("account.group_account_readonly").id])],
        })
        self.entry(self.receivable, 1000, 25000)
        run = self.create_run()
        with self.assertRaises(AccessError):
            run.with_user(reader).action_compute()
