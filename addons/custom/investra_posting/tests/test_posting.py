from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.book = cls.env["investra.entity"].create_book("Fond", "fund", "cas501", cls.czk, "investra_fund")
        cls.company = cls.book.company_id
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company.id]))
        cls.fund = cls.env["investra.fund"].create({"entity_id": cls.book.id})
        cls.class_a = cls.env["investra.fund.class"].create(
            {"fund_id": cls.fund.id, "code": "A", "name": "A", "currency_id": cls.czk.id}
        )
        cls.Event = cls.env["investra.accounting.event"]
        cls.user = cls.env["res.users"].create({
            "name": "Účetní",
            "login": "posting_accountant",
            "company_id": cls.company.id,
            "company_ids": [(6, 0, [cls.company.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref("account.group_account_manager").id])],
        })

    def lines(self, amount=100):
        return [
            {"role": "bank", "amount": amount, "movement_type": "transaction"},
            {"role": "performance_payable", "amount": -amount, "class_id": self.class_a.id, "movement_type": "fee"},
        ]

    def event(self, key="k1", day=date(2026, 11, 30), amount=100):
        return self.Event._create_event(self.company, key, "Test", day, "other", self.lines(amount))

    def posted(self, key="p1"):
        event = self.event(key)
        event._lock_events()
        event._post_events()
        return event

    def test_event_creates_draft_with_class_on_line(self):
        event = self.event()
        self.assertEqual(event.move_id.state, "draft")
        line = event.move_id.line_ids.filtered("investra_class_id")
        self.assertEqual(line.investra_class_id, self.class_a)
        self.assertEqual(line.credit, 100)

    def test_same_key_same_content_returns_same_event(self):
        self.assertEqual(self.event(), self.event())
        self.assertEqual(self.Event.search_count([("key", "=", "k1")]), 1)

    def test_same_key_other_content_is_error(self):
        self.event()
        with self.assertRaises(UserError):
            self.event(amount=101)

    def test_user_cannot_change_event_draft(self):
        move = self.event().move_id.with_user(self.user)
        with self.assertRaises(UserError):
            move.ref = "změna"
        with self.assertRaises(UserError):
            move.line_ids[0].name = "změna"
        with self.assertRaises(UserError):
            move.line_ids[0].investra_class_id = False

    def test_user_cannot_post_delete_or_add_line(self):
        move = self.event().move_id.with_user(self.user)
        with self.assertRaises(UserError):
            move.action_post()
        with self.assertRaises(UserError):
            move.unlink()
        with self.assertRaises(UserError):
            move.line_ids[0].unlink()
        with self.assertRaises(UserError):
            self.env["account.move.line"].with_user(self.user).create({
                "move_id": move.id,
                "account_id": move.line_ids[0].account_id.id,
                "balance": 0,
            })

    def test_superuser_bypass_context_string_does_not_work(self):
        move = self.event().move_id.with_user(self.user).with_context(investra_service="SERVICE")
        with self.assertRaises(UserError):
            move.action_post()

    def test_user_has_no_write_on_event(self):
        event = self.event()
        with self.assertRaises(AccessError):
            event.with_user(self.user).write({"state": "posted"})

    def test_post_only_from_locked(self):
        event = self.event()
        with self.assertRaises(UserError):
            event._post_events()
        event._lock_events()
        event._post_events()
        self.assertEqual(event.move_id.state, "posted")
        self.assertEqual(event.state, "posted")

    def test_posted_event_is_hashed(self):
        self.assertTrue(self.posted().move_id.inalterable_hash)

    def test_class_change_after_posting_is_blocked_even_for_service(self):
        move = self.posted().move_id
        line = move.line_ids.filtered("investra_class_id")
        with self.assertRaises(UserError):
            line.sudo().write({"investra_class_id": False})

    def test_manual_entry_class_locked_after_posting(self):
        accounts = self.env["investra.role.account"].search([("company_id", "=", self.company.id)], limit=2).account_id
        journal = self.env["account.journal"].search([("company_id", "=", self.company.id), ("type", "=", "general")], limit=1)
        move = self.env["account.move"].create({
            "journal_id": journal.id,
            "date": "2026-11-30",
            "line_ids": [
                (0, 0, {"account_id": accounts[0].id, "debit": 5, "investra_class_id": self.class_a.id}),
                (0, 0, {"account_id": accounts[1].id, "credit": 5}),
            ],
        })
        move.action_post()
        with self.assertRaises(UserError):
            move.line_ids[0].investra_class_id = False

    def test_class_is_part_of_hash(self):
        self.assertIn("investra_class_id", self.env["account.move.line"]._get_integrity_hash_fields())

    def test_hash_chain_stays_valid(self):
        first = self.posted("h1").move_id
        second = self.posted("h2").move_id
        self.assertEqual(first._calculate_hashes(""), {first: first.inalterable_hash})
        self.assertEqual(second._calculate_hashes(first.inalterable_hash), {second: second.inalterable_hash})

    def test_reset_to_draft_blocked(self):
        move = self.posted().move_id
        with self.assertRaises(UserError):
            move.button_draft()

    def test_reversal_keeps_date_and_class(self):
        event = self.posted()
        event._reverse_events()
        reversal = event.reversal_move_id
        self.assertEqual(reversal.date, event.date)
        self.assertEqual(reversal.state, "posted")
        self.assertEqual(event.state, "reversed")
        self.assertEqual(reversal.line_ids.filtered("investra_class_id").investra_class_id, self.class_a)
        total = sum((event.move_id.line_ids | reversal.line_ids).filtered("investra_class_id").mapped("balance"))
        self.assertEqual(total, 0)

    def test_reversal_outside_service_blocked(self):
        event = self.posted()
        with self.assertRaises(UserError):
            event.move_id._reverse_moves(cancel=True)

    def test_posting_into_locked_period_fails_and_does_not_shift(self):
        self.company.hard_lock_date = date(2026, 11, 30)
        event = self.event()
        event._lock_events()
        with self.assertRaises(UserError):
            event._post_events()

    def test_reversal_into_locked_period_fails(self):
        event = self.posted()
        self.company.hard_lock_date = date(2026, 11, 30)
        with self.assertRaises(UserError):
            event._reverse_events()

    def test_manual_entry_in_fund_book_cannot_shift_date(self):
        self.company.hard_lock_date = date(2026, 10, 31)
        accounts = self.env["investra.role.account"].search([("company_id", "=", self.company.id)], limit=2).account_id
        journal = self.env["account.journal"].search([("company_id", "=", self.company.id), ("type", "=", "general")], limit=1)
        move = self.env["account.move"].create({
            "journal_id": journal.id,
            "date": "2026-10-15",
            "line_ids": [(0, 0, {"account_id": accounts[0].id, "debit": 1}), (0, 0, {"account_id": accounts[1].id, "credit": 1})],
        })
        with self.assertRaises(UserError):
            move.action_post()

    def test_discard_removes_draft_without_storno(self):
        event = self.event()
        event._lock_events()
        move_id = event.move_id.id
        event._discard_events()
        self.assertEqual(event.state, "discarded")
        self.assertFalse(self.env["account.move"].browse(move_id).exists())

    def test_discard_of_posted_is_error(self):
        event = self.posted()
        with self.assertRaises(UserError):
            event._discard_events()

    def test_key_is_free_after_discard(self):
        event = self.event()
        event._discard_events()
        self.assertNotEqual(self.event(), event)

    # Bod 15: fond, zdroj, částka a měna události (docs/navrh-ucetni-udalosti.md)

    def test_amount_is_debit_sum_of_move(self):
        event = self.posted("a1")
        self.assertEqual(event.amount, 100)
        self.assertEqual(event.amount, sum(event.move_id.line_ids.mapped("debit")))
        self.assertEqual(event.currency_id, self.czk)
        self.assertFalse(event.foreign_currency_id)
        self.assertFalse(event.amount_currency)

    def test_source_and_fund_from_source(self):
        event = self.Event._create_event(self.company, "s1", "Test", date(2026, 11, 30), "other", self.lines(), source=self.class_a)
        self.assertEqual((event.res_model, event.res_id), ("investra.fund.class", self.class_a.id))
        self.assertEqual(event.fund_id, self.fund)
        self.assertEqual(event.source_name, self.class_a.display_name)
        action = event.action_open_source()
        self.assertEqual((action["res_model"], action["res_id"]), ("investra.fund.class", self.class_a.id))
        self.assertEqual(event.action_open_move()["res_id"], event.move_id.id)

    def test_without_source_has_no_fund_and_open_source_is_error(self):
        event = self.event("s2")
        self.assertFalse(event.fund_id)
        self.assertFalse(event.source_name)
        with self.assertRaises(UserError):
            event.action_open_source()

    def test_same_key_with_source_returns_same_event(self):
        first = self.event("s3")
        again = self.Event._create_event(self.company, "s3", "Test", date(2026, 11, 30), "other", self.lines(), source=self.class_a)
        self.assertEqual(first, again)

    def test_one_foreign_currency_gives_original_amount(self):
        eur = self.env.ref("base.EUR")
        lines = [
            {"role": "bank", "amount": -2500, "currency_id": eur.id, "amount_currency": -100},
            {"role": "performance_payable", "amount": 2500, "class_id": self.class_a.id},
        ]
        event = self.Event._create_event(self.company, "f1", "Test", date(2026, 11, 30), "other", lines)
        self.assertEqual(event.amount, 2500)
        self.assertEqual(event.foreign_currency_id, eur)
        self.assertEqual(event.amount_currency, 100)

    def test_mixed_foreign_currencies_leave_original_amount_empty(self):
        eur, usd = self.env.ref("base.EUR"), self.env.ref("base.USD")
        lines = [
            {"role": "bank", "amount": 2500, "currency_id": eur.id, "amount_currency": 100},
            {"role": "performance_payable", "amount": -2500, "currency_id": usd.id, "amount_currency": -110},
        ]
        event = self.Event._create_event(self.company, "f2", "Test", date(2026, 11, 30), "other", lines)
        self.assertEqual(event.amount, 2500)
        self.assertFalse(event.foreign_currency_id)

    def test_discarded_event_keeps_amount(self):
        event = self.event("d1")
        event._discard_events()
        self.assertFalse(event.move_id)
        self.assertEqual(event.amount, 100)

    def test_user_cannot_write_new_fields(self):
        event = self.event("w1")
        for values in ({"fund_id": self.fund.id}, {"amount": 1}, {"res_model": "res.partner"}, {"event_type": "trade"}):
            with self.assertRaises(AccessError):
                event.with_user(self.user).write(values)

    def test_user_can_read_event_form(self):
        event = self.posted("r1").with_user(self.user)
        self.assertEqual(event.amount, 100)
        self.assertEqual(len(event.move_line_ids), 2)
