import io
import zipfile
from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import format_date

from .common import NavCase


@tagged("post_install", "-at_install")
class TestWorkflow(NavCase):
    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")
        self.subscribe(self.a, "2027-01-01", 1000, 10)
        self.subscribe(self.b, "2027-01-01", 1000, 10)
        self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Úplata", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})],
        })
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        self.day = date(2027, 1, 31)

    def moves(self, valuation):
        return valuation.sudo().event_ids.move_id

    def test_display_name_shows_fund_date_and_version(self):
        first = self.valuation(self.fund, self.day)
        second = self.valuation(self.fund, self.day, version=2)
        day = format_date(self.env, self.day)
        self.assertEqual(first.display_name, f"{self.fund.display_name} – {day} – v1")
        self.assertEqual(second.display_name, f"{self.fund.display_name} – {day} – v2")
        self.assertNotIn("investra.valuation", first.display_name)

    def test_name_search_finds_valuations_by_part_of_fund_name(self):
        self.fund.entity_id.sudo().name = "Zlatý důl"
        mine = self.valuation(self.fund, self.day) | self.valuation(self.fund, date(2027, 2, 28))
        other = self.make_fund(classes=[{"code": "A"}])  # přepne kontext na knihu druhého fondu
        other.entity_id.sudo().name = "Stříbrná řeka"
        theirs = self.valuation(other, self.day)
        both = [self.fund.company_id.id, other.company_id.id]
        valuations = self.env["investra.valuation"].with_user(self.preparer).with_context(allowed_company_ids=both)
        found = valuations.search([("id", "in", (mine | theirs).ids), ("display_name", "ilike", "atý dů")])
        self.assertEqual(found, mine)
        self.assertEqual(
            {record_id for record_id, _ in valuations.name_search("atý dů", limit=100)} & set((mine | theirs).ids),
            set(mine.ids),
        )
        self.assertEqual(mine[0].display_name, f"Zlatý důl – {format_date(self.env, self.day)} – v1")

    def test_repeat_compute_gives_same_result_and_no_duplicates(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        first = (valuation.fund_capital, valuation.class_line_ids.mapped("capital"))
        count = len(valuation.event_ids)
        valuation.action_compute()
        self.assertEqual((valuation.fund_capital, valuation.class_line_ids.mapped("capital")), first)
        self.assertEqual(len(valuation.event_ids), count)
        self.assertEqual(self.env["account.move"].search_count([("company_id", "=", self.fund.company_id.id), ("state", "=", "draft")]), count)

    def test_nav_counts_drafts_before_posting(self):
        # 2 100 × 0,0365 × 31/365 = 6,51 úplaty je jen v návrhu, FK už je po ní
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        self.assertAlmostEqual(valuation.fund_capital, 2093.49, places=2)
        self.assertTrue(all(m.state == "draft" for m in self.moves(valuation)))

    def test_preparer_cannot_approve_own_valuation(self):
        self.preparer.group_ids |= self.env.ref("investra_entity.group_valuation_approver")
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            valuation.with_user(self.preparer).action_approve()

    def test_approver_without_preparer_group_cannot_compute(self):
        valuation = self.valuation(self.fund, self.day)
        with self.assertRaises(AccessError):
            valuation.with_user(self.approver).action_compute()

    def test_preparer_without_approver_group_cannot_approve(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(AccessError):
            valuation.with_user(self.preparer).action_approve()

    def test_cannot_post_without_approval(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            valuation.action_post()

    def test_submitted_draft_cannot_be_changed_or_posted_by_hand(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        move = self.moves(valuation)[0]
        manager = self.env["res.users"].create({
            "name": "m", "login": "nav_mgr", "company_id": self.fund.company_id.id,
            "company_ids": [(6, 0, self.fund.company_id.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("account.group_account_manager").id])],
        })
        with self.assertRaises(UserError):
            move.with_user(manager).action_post()
        with self.assertRaises(UserError):
            move.with_user(manager).line_ids[0].name = "změna"

    def test_two_step_approval_needs_two_people(self):
        self.env["investra.fund.approval.step"].create([
            {"fund_id": self.fund.id, "sequence": 1, "name": "Kontrola"},
            {"fund_id": self.fund.id, "sequence": 2, "name": "Vedení fondu"},
        ])
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        valuation.with_user(self.approver).action_approve()
        self.assertEqual(valuation.state, "submitted")
        with self.assertRaises(UserError):
            valuation.with_user(self.approver).action_approve()
        valuation.with_user(self.approver2).action_approve()
        self.assertEqual(valuation.state, "approved")

    def test_tampered_snapshot_blocks_posting(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        valuation.with_user(self.approver).action_approve()
        valuation.sudo().class_line_ids[0].capital = 1
        with self.assertRaises(UserError):
            valuation.action_post()

    def test_posting_is_single_step_at_valuation_date(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        self.assertTrue(all(m.state == "posted" and m.date == self.day for m in self.moves(valuation)))

    def test_return_before_posting_makes_new_version_without_storno(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        count = self.env["account.move"].search_count([("company_id", "=", self.fund.company_id.id)])
        drafts = len(valuation.event_ids)
        new = valuation.with_user(self.approver).action_return("Chybná cena")
        self.assertEqual(valuation.state, "returned")
        self.assertEqual(new.version, 2)
        self.assertEqual(self.env["account.move"].search_count([("company_id", "=", self.fund.company_id.id)]), count - drafts)
        self.assertFalse(self.env["account.move"].search_count([("company_id", "=", self.fund.company_id.id), ("ref", "like", "Storno")]))

    def test_return_needs_reason(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            valuation.with_user(self.approver).action_return("")

    def test_depositary_return_reverses_all_and_new_version_gives_same_nav(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        capital = valuation.fund_capital
        valuation.action_send_depositary()
        new = valuation.with_user(self.approver).action_depositary_return("Rozdíl v kusech")
        self.assertEqual(valuation.state, "reversed")
        reversals = valuation.sudo().event_ids.reversal_move_id
        self.assertEqual(len(reversals), len(valuation.event_ids))
        self.assertTrue(all(m.date == self.day and m.state == "posted" for m in reversals))
        self.assertEqual(new.version, 2)
        new.with_user(self.preparer).action_compute()
        self.assertAlmostEqual(new.fund_capital, capital, places=2)

    def test_reversed_valuation_is_not_previous(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        valuation.action_send_depositary()
        new = valuation.with_user(self.approver).action_depositary_return("x").with_user(self.preparer)
        self.run_to_posted(new)
        following = self.valuation(self.fund, date(2027, 2, 28))
        following.action_compute()
        self.assertEqual(following.previous_id, new)

    def test_publish_locks_period_and_blocks_later_storno(self):
        valuation = self.run_to_published(self.valuation(self.fund, self.day))
        self.assertEqual(valuation.state, "published")
        self.assertEqual(self.fund.company_id.hard_lock_date, self.day)
        with self.assertRaises(UserError):
            valuation.sudo().event_ids._reverse_events()

    def test_publish_requires_depositary(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        with self.assertRaises(UserError):
            valuation.with_user(self.approver).action_publish()

    def test_user_of_other_book_cannot_read_valuation(self):
        valuation = self.valuation(self.fund, self.day)
        other = self.env["investra.entity"].create_book("Jiný", "fund", "cas501", self.czk, "investra_fund")
        user = self.env["res.users"].create({
            "name": "o", "login": "nav_other", "company_id": other.company_id.id,
            "company_ids": [(6, 0, other.company_id.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("account.group_account_readonly").id])],
        })
        with self.assertRaises(AccessError):
            valuation.with_user(user).read(["fund_capital"])

    def test_package_has_four_sheets_with_portfolio_columns(self):
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        attachment = valuation.action_build_package()
        data = zipfile.ZipFile(io.BytesIO(attachment.raw))
        workbook = data.read("xl/workbook.xml").decode()
        for name in ("Portfolio", "NAV", "Předvaha", "Úplaty"):
            self.assertIn(name, workbook)
        strings = data.read("xl/sharedStrings.xml").decode()
        for label in ("Reálná hodnota v měně fondu", "Pořizovací hodnota v měně", "Zdroj kurzu", "Bankovní účty CZK"):
            self.assertIn(label, strings)

    def test_price_rounding_per_class(self):
        # 1 000 / 3 kusy = 333,3333…; 2 000 / 3 = 666,6666…
        fund = self.make_fund(classes=[
            {"code": "D", "price_digits": 2, "price_rounding": "down"},
            {"code": "M", "price_digits": 2, "price_rounding": "half_up"},
            {"code": "N", "price_digits": 2, "price_rounding": "up"},
            {"code": "Z", "price_digits": 0, "price_rounding": "down"},
        ])
        for code, amount in (("D", 2000), ("M", 2000), ("N", 1000), ("Z", 2000)):
            self.subscribe(self.cls(fund, code), "2027-01-01", amount, 3)
        valuation = self.valuation(fund, self.day)
        valuation.action_compute()
        self.assertEqual(self.result(valuation, "D").price, "666.66")
        self.assertEqual(self.result(valuation, "M").price, "666.67")
        self.assertEqual(self.result(valuation, "N").price, "333.34")
        self.assertEqual(self.result(valuation, "Z").price, "666")

    def test_state_cannot_be_written_directly(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        for field, value in (("state", "approved"), ("snapshot_hash", "x"), ("fund_capital", 1), ("preparer_id", self.approver.id)):
            with self.assertRaises(UserError):
                valuation.write({field: value})

    def test_cannot_create_valuation_in_advanced_state(self):
        with self.assertRaises(UserError):
            self.env["investra.valuation"].with_user(self.preparer).create(
                {"fund_id": self.fund.id, "date": self.day, "state": "approved"}
            )

    def test_cannot_jump_version_by_hand_after_compute(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        with self.assertRaises(UserError):
            valuation.write({"version": 9})

    def test_package_only_after_posting(self):
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        with self.assertRaises(UserError):
            valuation.action_build_package()


@tagged("post_install", "-at_install")
class TestPortfolio(NavCase):
    # Kurzy jsou v databázi společné a neměnné; rok 2028 se nepřekrývá s ukázkovými daty.

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2028-01-01", 100000, 1000)
        self.instrument = self.env["investra.instrument"].create(
            {"name": "Akcie", "isin": "XS0000000000", "currency_id": self.eur.id, "type_id": self.env.ref("investra_instruments.type_equity").id}
        )
        self.classify(self.fund, self.instrument)
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "trade_date": "2028-01-05",
            "quantity": 10, "price": 100, "fx_rate": 25,
        })
        trade._book()
        self.day = date(2028, 1, 31)

    def approved_price(self, value):
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": self.instrument.id, "date": self.day, "price": value, "source": "Burza",
        })
        price.with_user(self.approver).action_approve()

    def test_missing_approved_price_stops(self):
        self.rate("2028-01-29", 26)
        with self.assertRaises(UserError):
            self.valuation(self.fund, self.day).action_compute()

    def test_missing_rate_stops(self):
        self.approved_price(110)
        with self.assertRaises(UserError):
            self.valuation(self.fund, self.day).action_compute()

    def test_price_and_fx_effects_are_separated(self):
        # Pořízení 1 000 EUR × 25 = 25 000; 1 100 EUR × 26 = 28 600
        # Cena: 100 EUR × 26 = 2 600; kurz: 1 000 EUR × 1 = 1 000
        self.approved_price(110)
        self.rate("2028-01-29", 26)
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        line = valuation.portfolio_line_ids.filtered("instrument_id")
        self.assertAlmostEqual(line.fair_value, 28600, places=2)
        self.assertAlmostEqual(line.fair_value_currency, 1100, places=2)
        self.assertAlmostEqual(line.cost, 25000, places=2)
        self.assertAlmostEqual(line.cost_currency, 1000, places=2)
        self.assertEqual(line.fx_rate, 26)
        self.assertEqual(line.fx_source, "cnb")
        moves = valuation.sudo().event_ids.move_id.line_ids
        instrument_lines = moves.filtered("investra_instrument_id").filtered(lambda l: l.debit)
        price = instrument_lines.filtered(lambda l: l.investra_movement_type == "price_revaluation")
        fx = instrument_lines.filtered(lambda l: l.investra_movement_type == "fx_revaluation")
        self.assertEqual(price.debit, 2600)
        self.assertEqual(fx.debit, 1000)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "positions_ledger").status, "ok")
        # Nákup šel z banky v EUR do mínusu −1 000 EUR, ta se při kurzu 26 přecení o −1 000 CZK
        self.assertAlmostEqual(valuation.fund_capital, 100000 + 3600 - 1000, places=2)

    def test_package_shows_rate_source_with_diacritics(self):
        self.approved_price(110)
        self.rate("2028-01-29", 26)
        valuation = self.run_to_posted(self.valuation(self.fund, self.day))
        row = [r for r in valuation._package_rows_portfolio() if r["name"] == "Akcie"][0]
        self.assertEqual(row["fx_source"], "ČNB")

    def test_second_valuation_revalues_only_change(self):
        self.approved_price(110)
        self.rate("2028-01-29", 26)
        self.run_to_posted(self.valuation(self.fund, self.day))
        self.day = date(2028, 2, 26)
        self.approved_price(110)
        self.rate("2028-02-26", 26)
        second = self.valuation(self.fund, self.day)
        second.action_compute()
        self.assertFalse(second.event_ids)
        self.assertAlmostEqual(second.fund_capital, 102600, places=2)

    def test_foreign_bank_is_revalued(self):
        # 1 000 EUR na účtu zaúčtovaných po 25; při 26 přecenění +1 000
        self.book(self.fund, "banka", "2028-01-10", [
            {"role": "bank", "amount": "25000", "currency_id": self.eur.id, "amount_currency": "1000"},
            {"role": "income_other", "amount": "-25000"},
        ])
        self.approved_price(100)
        self.rate("2028-01-29", 25)
        self.rate("2028-01-30", 26)
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        row = valuation.portfolio_line_ids.filtered(lambda l: l.kind == "bank" and l.currency_id == self.eur)
        self.assertEqual(row.fx_rate, 26)
        self.assertTrue(valuation.sudo().event_ids.move_id.line_ids.filtered(lambda l: l.investra_movement_type == "fx_revaluation"))
