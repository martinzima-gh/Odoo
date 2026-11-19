"""AG-019: dopočty ve formuláři úpisu a odkupu při ručním zadání (odoo.tests.Form).

Formulář jen předvyplňuje hodnoty; kontroly a zaúčtování pohybu zůstávají beze změny, proto každý předvyplněný pohyb
projde `action_book`. Rok 2027 (ocenění k 31. 1.) je jen pro tyto testy; kurz EUR v roce 2038 jiné testy neukládají.
"""

from datetime import date

from odoo import fields
from odoo.tests import Form, tagged

from .common import NavCase

PRICE = 1036.6444  # cena ze vzorového úpisu (zadání AG-019, bod B)
DAY = date(2027, 2, 10)  # po zveřejněném ocenění z 31. 1. 2027


@tagged("post_install", "-at_install")
class TestMovementOnchange(NavCase):

    def setUp(self):
        super().setUp()
        # A: 1 % vstupní i výstupní poplatek, 6 míst dolů; B: bez poplatků; R: 2 desetinná místa kusů (rozdíl u odkupu podle částky)
        self.fund = self.make_fund(classes=[
            {"code": "A", "entry_fee_rate": 1, "exit_fee_rate": 1},
            {"code": "B"},
            {"code": "R", "entry_fee_rate": 1, "exit_fee_rate": 1, "unit_digits": 2},
        ])
        self.a, self.b, self.r = (self.cls(self.fund, code) for code in "ABR")
        for fund_class in (self.a, self.b, self.r):
            self.subscribe(fund_class, "2027-01-05", 1036644.40, 1000)  # kurz třídy 1 036,6444
        self.run_to_published(self.valuation(self.fund, date(2027, 1, 31)))
        self.Movement = self.env["investra.class.movement"]

    def form(self, kind, fund_class, day=DAY, **ctx):
        form = Form(self.Movement.with_context(default_movement_type=kind, **ctx))
        form.class_id = fund_class
        form.date = day
        form.manual_reason = "Test"
        return form

    # --- úpis -------------------------------------------------------------------------------------

    def test_subscription_from_payment(self):
        """Vzorový úpis: platba 1 000 000, sazba 1 %, cena 1 036,6444, 6 míst dolů."""
        form = self.form("subscription", self.a)
        self.assertEqual(form.price, PRICE, "cena ze zveřejněného kurzu třídy")
        self.assertEqual(form.published_price, PRICE)
        self.assertEqual(form.published_date, date(2027, 1, 31))
        self.assertTrue(form.price_matches)
        form.amount_class = 1000000
        self.assertEqual(form.fee_amount_class, 10000.00)
        self.assertEqual(form.units, 955.004435)  # zadání uvádělo 955,004437, přepočet dolů na 6 míst dává …435
        self.assertEqual(form.value_class, 990000.00)
        self.assertEqual(form.rounding_amount_class, 0.00)
        self.assertEqual(form.residual_class, 0.00)
        self.assertEqual(form.fee_recipient, "manager")
        self.assertFalse(form.fee_warning)
        movement = form.save()
        movement.action_book()  # stejné kontroly, žádný důvod odlišné ceny
        self.assertEqual(movement.state, "posted")
        self.assertEqual(movement.units, 955.004435)

    def test_subscription_rounding_difference(self):
        """Třída se 2 místy kusů: rozdíl ze zaokrouhlení vyjde z platby a zbytek je 0."""
        form = self.form("subscription", self.r)
        form.amount_class = 100000
        # čistá 99 000,00 / 1 036,6444 = 95,50 dolů na 2 místa; 95,50 × 1 036,6444 = 98 999,54 (rozdíl 0,46)
        self.assertEqual(form.units, 95.50)
        self.assertEqual(form.value_class, 98999.54)
        self.assertEqual(form.rounding_amount_class, 0.46)
        self.assertEqual(form.residual_class, 0.00)
        movement = form.save()
        movement.action_book()
        self.assertEqual(movement.state, "posted")

    def test_first_subscription_without_published_valuation(self):
        """Třída bez zveřejněného ocenění: cena se nepředvyplní, důvod dostane nápovědu; po zadání ceny projde zaúčtování."""
        fund = self.make_fund(classes=[{"code": "X", "entry_fee_rate": 1}])
        form = self.form("subscription", self.cls(fund, "X"), day=date(2027, 1, 20))
        self.assertEqual(form.price, 0.0)
        self.assertFalse(form.published_date)
        self.assertEqual(form.price_reason, "První úpis třídy")
        form.price = 100
        form.amount_class = 10000
        self.assertEqual(form.fee_amount_class, 100.0)
        self.assertEqual(form.units, 99.0)
        movement = form.save()
        movement.action_book()
        self.assertEqual(movement.state, "posted")

    def test_manual_fee_survives_until_input_changes(self):
        form = self.form("subscription", self.a)
        form.amount_class = 100000
        self.assertEqual(form.fee_amount_class, 1000.0)
        form.fee_amount_class = 500
        self.assertEqual(form.fee_amount_class, 500.0)
        self.assertIn("liší", form.fee_warning)
        self.assertEqual(form.residual_class, 0.0, "poplatek je vstup pro kusy, zbytek zůstává 0")
        form.amount_class = 200000  # změna vstupu přepočte poplatek
        self.assertEqual(form.fee_amount_class, 2000.0)
        self.assertFalse(form.fee_warning)

    def test_zero_rate_class_manual_fee_books(self):
        """Třída bez sazby: poplatek 0,00, ruční poplatek s příjemcem z třídy projde zaúčtováním."""
        form = self.form("subscription", self.b)
        form.amount_class = 100000
        self.assertEqual(form.fee_amount_class, 0.0)
        self.assertFalse(form.fee_warning)
        form.fee_amount_class = 500
        self.assertEqual(form.fee_warning, "Třída nemá sazbu poplatku; poplatek zadán ručně.")
        self.assertEqual(form.fee_recipient, "manager")
        movement = form.save()
        movement.action_book()
        self.assertEqual(movement.state, "posted")
        self.assertEqual(movement.fee_amount_class, 500.0)

    def test_save_as_preparer(self):
        """Formulář uloží běžný uživatel (role Příprava): do `create` se nedostane `valuation_id` ani jiné systémové pole."""
        movements = self.Movement.with_user(self.preparer)
        form = Form(movements.with_context(default_movement_type="subscription"))
        form.class_id = self.a
        form.date = DAY
        form.manual_reason = "Test"
        form.amount_class = 1000000
        movement = form.save()
        self.assertEqual(movement.sudo().units, 955.004435)
        self.assertEqual(movement.state, "draft")

    # --- odkup ------------------------------------------------------------------------------------

    def test_redemption_by_units(self):
        form = self.form("redemption", self.a)
        self.assertEqual(form.redemption_by, "units")
        form.units = 100
        self.assertEqual(form.amount_class, 103664.44)  # 100 × 1 036,6444
        self.assertEqual(form.fee_amount_class, 1036.64)
        self.assertEqual(form.rounding_amount_class, 0.0)
        self.assertEqual(form.payout_class, 102627.80)
        self.assertEqual(form.residual_class, 0.0)
        movement = form.save()
        movement.action_book()
        self.assertEqual(movement.state, "posted")

    def test_redemption_by_amount_with_difference(self):
        """Podle částky: kusy se zaokrouhlí podle třídy, výplata investorovi = požadovaná částka − poplatek."""
        form = self.form("redemption", self.r)
        form.redemption_by = "amount"
        form.requested_amount = 100000
        self.assertEqual(form.units, 96.46)  # 100 000 / 1 036,6444 dolů na 2 místa
        self.assertEqual(form.amount_class, 99994.72)
        self.assertEqual(form.fee_amount_class, 999.95)
        self.assertEqual(form.rounding_amount_class, -5.28)  # hrubá − požadovaná (odchylka od zadání, viz model)
        self.assertEqual(form.payout_class, 99000.05)  # 100 000 − 999,95
        self.assertEqual(form.residual_class, 0.0)
        movement = form.save()
        movement.action_book()
        self.assertEqual(movement.state, "posted")

    def test_redemption_manual_override_survives(self):
        form = self.form("redemption", self.a)
        form.units = 100
        form.fee_amount_class = 1000
        self.assertEqual(form.fee_amount_class, 1000.0)
        form.units = 50  # změna vstupu přepočte poplatek
        self.assertEqual(form.fee_amount_class, 518.32)

    # --- cizí měna, zdroj IS, výchozí hodnoty -------------------------------------------------------

    def test_foreign_currency_prefills_rate(self):
        self.rate("2038-01-05", 25)
        fund = self.make_fund(classes=[{"code": "E", "currency_id": self.eur.id}])
        form = self.form("subscription", self.cls(fund, "E"), day=date(2038, 1, 5))
        self.assertTrue(form.foreign_currency)
        self.assertEqual(form.fx_rate, 25)
        form.price = 100
        form.amount_class = 1000
        self.assertEqual(form.amount, 25000)  # hrubá částka ve funkční měně
        self.assertEqual(form.units, 10)
        form.save().action_book()
        czk_form = self.form("subscription", self.a)
        self.assertFalse(czk_form.foreign_currency)

    def test_source_is_computes_nothing(self):
        form = Form(self.Movement.with_context(default_movement_type="subscription"))
        form.source = "is"
        form.external_ref = "D99/1"
        form.class_id = self.a
        form.date = DAY
        form.amount_class = 1000000
        self.assertEqual(form.price, 0.0)
        self.assertEqual(form.fee_amount_class, 0.0)
        self.assertEqual(form.units, 0.0)
        self.assertEqual(form.rounding_amount_class, 0.0)

    def test_defaults(self):
        self.assertEqual(self.Movement.default_get(["date"])["date"], fields.Date.context_today(self.Movement))
        fund = self.make_fund(classes=[{"code": "S"}])
        defaults = self.Movement.with_context(default_fund_id=fund.id).default_get(["class_id"])
        self.assertEqual(defaults["class_id"], self.cls(fund, "S").id)
        defaults = self.Movement.with_context(default_fund_id=self.fund.id).default_get(["class_id"])
        self.assertNotIn("class_id", defaults, "fond s více třídami třídu nepředvyplní")
