from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestClassLock(NavCase):
    """MN-07: po prvním zaúčtovaném pohybu třídy nejde změnit kód a měna; poplatky ano.

    MN-12: zaokrouhlení a desetinná místa kurzu a kusů jdou měnit i po pohybu; platí pro další pohyby a ocenění,
    zaúčtované pohyby a uložená ocenění se nepřepočítají.
    """

    def _locked_class(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        return fund, self.cls(fund, "A"), self.cls(fund, "B")

    def test_free_before_first_movement(self):
        fund, class_a, _class_b = self._locked_class()
        class_a.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_a.movement_locked)
        class_a.write({"code": "A1", "currency_id": self.eur.id, "price_digits": 2, "unit_digits": 3,
                       "price_rounding": "up", "unit_rounding": "up"})
        self.assertEqual(class_a.code, "A1")

    def test_draft_movement_does_not_lock(self):
        _fund, class_a, _class_b = self._locked_class()
        self.env["investra.class.movement"].create({
            "class_id": class_a.id, "date": "2027-01-01", "manual_reason": "Test", "movement_type": "subscription",
            "amount": 1000, "units": 10,
        })
        class_a.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_a.movement_locked)
        class_a.code = "A2"

    def test_locked_after_posted_movement(self):
        _fund, class_a, class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        class_a.invalidate_recordset(["movement_locked"])
        self.assertTrue(class_a.movement_locked)
        for vals in ({"code": "X"}, {"currency_id": self.eur.id}):
            with self.assertRaisesRegex(UserError, "zaúčtovaný úpis nebo odkup"):
                class_a.write(vals)
        # Stejná hodnota není změna; jiná třída bez pohybu zůstává volná.
        class_a.write({"code": class_a.code, "currency_id": class_a.currency_id.id})
        class_b.invalidate_recordset(["movement_locked"])
        self.assertFalse(class_b.movement_locked)
        class_b.code = "B2"

    def test_fees_and_name_stay_editable(self):
        _fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        class_a.write({
            "name": "Nový název", "entry_fee_rate": 1.5, "exit_fee_rate": 0.5,
            "entry_fee_recipient": "distributor", "exit_fee_recipient": "fund", "isin": "US0378331005", "sequence": 5,
        })
        self.assertEqual(class_a.entry_fee_rate, 1.5)
        self.assertEqual(class_a.entry_fee_recipient, "distributor")

    def test_reversed_movement_keeps_lock(self):
        _fund, class_a, _class_b = self._locked_class()
        movement = self.subscribe(class_a, "2027-01-01", 1000, 10)
        movement.sudo().write({"state": "reversed"})
        class_a.invalidate_recordset(["movement_locked"])
        self.assertTrue(class_a.movement_locked)
        with self.assertRaisesRegex(UserError, "zaúčtovaný úpis nebo odkup"):
            class_a.code = "X"

    def test_form_fields_read_only_when_locked(self):
        fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        view = fund.get_view(self.env.ref("investra_fund.view_fund_form").id)
        arch = view["arch"]
        for name in ("code", "currency_id"):
            self.assertRegex(arch, rf'<field name="{name}"[^>]*readonly="movement_locked"', name)
        for name in ("price_digits", "unit_digits", "price_rounding", "unit_rounding"):
            self.assertNotRegex(arch, rf'<field name="{name}"[^>]*readonly="movement_locked"', name)
        self.assertIn('widget="handle"', arch)
        Form(fund)  # formulář se načte

    # --- MN-12: zaokrouhlení a místa po pohybu -------------------------------------------------------------

    def _priced(self, fund_class, gross, units, price, kind="subscription", day="2027-01-05"):
        return self.env["investra.class.movement"].create({
            "class_id": fund_class.id, "date": day, "movement_type": kind, "amount_class": gross, "units": units,
            "price": price, "manual_reason": "Test", "price_reason": "Počáteční kurz",
        })

    def test_rounding_editable_after_posted_movement(self):
        _fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 10)
        class_a.write({"price_digits": 2, "price_rounding": "up", "unit_digits": 2, "unit_rounding": "up"})
        self.assertEqual((class_a.price_digits, class_a.price_rounding, class_a.unit_digits, class_a.unit_rounding),
                         (2, "up", 2, "up"))
        # Kód a měna zůstávají zamčené i při společném zápisu se zaokrouhlením.
        with self.assertRaisesRegex(UserError, "nejde změnit: Kód"):
            class_a.write({"code": "X", "unit_digits": 3})
        self.assertEqual(class_a.unit_digits, 2)

    def test_next_movement_uses_new_rounding_old_unchanged(self):
        _fund, class_a, _class_b = self._locked_class()
        # Výchozí třída: 6 míst kusů, dolů → 1000 / 0,3 = 3333,333333 (cena pod 1, aby setina kusu byla pod tolerancí zbytku).
        first = self._priced(class_a, 1000, 3333.333333, 0.3)
        first.action_book()
        amounts = (first.units, first.amount, first.capital_amount, first.event_id.move_id.amount_total)
        class_a.write({"unit_digits": 2, "unit_rounding": "up"})
        # Další úpis: nová přesnost a zaokrouhlení nahoru → 3333,34; starý počet kusů už neprojde.
        old_style = self._priced(class_a, 1000, 3333.333333, 0.3, day="2027-01-06")
        with self.assertRaisesRegex(UserError, "víc než 2 desetinných míst"):
            old_style.action_book()
        down = self._priced(class_a, 1000, 3333.33, 0.3, day="2027-01-06")
        with self.assertRaisesRegex(UserError, "neodpovídají zaokrouhlení třídy"):
            down.action_book()
        second = self._priced(class_a, 1000, 3333.34, 0.3, day="2027-01-06")
        second.action_book()
        self.assertEqual(second.state, "posted")
        # Zaúčtovaný pohyb se nepřepočítal.
        first.invalidate_recordset()
        self.assertEqual((first.units, first.amount, first.capital_amount, first.event_id.move_id.amount_total), amounts)
        self.assertEqual(first.state, "posted")

    def test_approved_valuation_keeps_values_next_uses_new_digits(self):
        fund, class_a, _class_b = self._locked_class()
        self.subscribe(class_a, "2027-01-01", 1000, 3)
        self.common_result(fund, "mn12-1", "2027-01-15", 1)
        first = self.run_to_posted(self.valuation(fund, "2027-01-31"))
        line = self.result(first, "A")
        # 1001 / 3 = 333,666…; výchozí 4 místa dolů.
        self.assertEqual(line.price, "333.6666")
        before = (line.price, line.units, line.capital, first.fund_capital)
        class_a.write({"price_digits": 2, "price_rounding": "up"})
        first.invalidate_recordset()
        line.invalidate_recordset()
        self.assertEqual((line.price, line.units, line.capital, first.fund_capital), before)
        self.assertEqual(first._fingerprint()[1], first.snapshot_hash)
        second = self.valuation(fund, "2027-02-28")
        second.action_compute()
        self.assertEqual(self.result(second, "A").price, "333.67")
