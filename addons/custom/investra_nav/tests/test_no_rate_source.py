from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase

MESSAGE = "nemá zdroj kurzů pro funkční měnu USD"


@tagged("post_install", "-at_install")
class TestNoRateSource(NavCase):
    """MN-08: fond v USD má zdroj kurzů Neimplementováno. Bez kurzu jde jen to, co kurz nepotřebuje;
    kde kurz potřeba je, výpočet skončí chybou a kurz ČNB se tiše nepoužije. Rok 2034 je jen pro tyto testy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usd = cls.env.ref("base.USD")
        cls.usd.active = True

    def setUp(self):
        super().setUp()
        # Kurz ČNB k datu existuje: chyba nesmí vzniknout tím, že kurz chybí, ale tím, že kniha zdroj nemá.
        self.rate("2034-01-02", 22, currency="USD")
        self.rate("2034-01-31", 23, currency="USD")

    def test_book_has_no_rate_source(self):
        fund = self.make_fund(currency=self.usd, launch="2034-01-02", classes=[{"code": "U", "currency_id": self.usd.id}])
        self.assertEqual(fund.entity_id.rate_source, "none")
        self.assertEqual(fund._fx_at(self.usd, fund.launch_date), 1)
        with self.assertRaisesRegex(UserError, MESSAGE):
            fund._fx_at(self.czk, fund.launch_date)

    def test_functional_currency_class_works_without_rates(self):
        """Třída ve funkční měně kurz nepotřebuje: úpis i ocenění projdou."""
        fund = self.make_fund(currency=self.usd, launch="2034-01-02", classes=[{"code": "U", "currency_id": self.usd.id}])
        self.subscribe(self.cls(fund, "U"), "2034-01-03", 1000, 10)
        valuation = self.valuation(fund, "2034-01-31")
        valuation.action_compute()
        self.assertEqual(valuation.state, "computed")
        self.assertEqual(self.result(valuation, "U").capital, 1000)

    def test_foreign_class_movement_is_refused(self):
        fund = self.make_fund(currency=self.usd, launch="2034-01-02", classes=[{"code": "C"}])  # třída v CZK
        Movement = self.env["investra.class.movement"]
        values = {"class_id": self.cls(fund, "C").id, "date": "2034-01-02", "manual_reason": "Test",
                  "movement_type": "subscription", "amount_class": 1000, "units": 10}
        with self.assertRaisesRegex(UserError, MESSAGE):
            Movement.create(values)
        # Ani ručně zadaný kurz se nepřijme, dokud o ručním kurzu nerozhodne Martin.
        with self.assertRaisesRegex(UserError, MESSAGE):
            Movement.create({**values, "fx_rate": 0.045})
        with self.assertRaisesRegex(UserError, MESSAGE):
            Movement.create({**values, "amount_class": 0, "amount": 45})

    def test_valuation_with_foreign_class_is_refused(self):
        fund = self.make_fund(currency=self.usd, launch="2034-01-02",
                              classes=[{"code": "U", "currency_id": self.usd.id}, {"code": "C"}])
        self.subscribe(self.cls(fund, "U"), "2034-01-03", 1000, 10)
        valuation = self.valuation(fund, "2034-01-31")
        with self.assertRaisesRegex(UserError, MESSAGE):
            valuation.action_compute()
