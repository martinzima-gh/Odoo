from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_rates.models.rate import parse_cnb

# Rok 2035 je jen pro tyto testy: kurzy jsou v databázi společné.
DAILY = """02.01.2035 #1
země|měna|množství|kód|kurz
EMU|euro|1|EUR|25,000
"""
MONTHLY = """31.01.2035 #1
země|měna|množství|kód|kurz
Afghánistán|afghání|100|AFN|33,612
Venezuela|bolívar|1|VES|0,000
"""


@tagged("post_install", "-at_install")
class TestRateProtection(TransactionCase):
    """Ochrana kurzů (rozhodnutí 2026-11-10): kurzy Odoo jen z evidence, ruční kurz jen s důvodem."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rate = cls.env["investra.rate"]
        cls.eur = cls.env.ref("base.EUR")
        cls.afn = cls.env.ref("base.AFN")
        (cls.eur | cls.afn).active = True
        cls.day = date(2035, 1, 2)
        cls.approver = cls._user("rate_approver", "investra_entity.group_valuation_approver")
        cls.accountant = cls._user("rate_accountant", "account.group_account_manager")
        cls.published = cls.Rate._store("cnb", *parse_cnb(DAILY), DAILY)
        cls.published._publish()

    @classmethod
    def _user(cls, login, group):
        return cls.env["res.users"].create({
            "name": login, "login": login,
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
        })

    def odoo_rate(self, currency, day):
        return self.env["res.currency.rate"].search(
            [("currency_id", "=", currency.id), ("name", "=", day), ("company_id", "=", False)]
        )

    def override(self, rate, reason="Chyba zdroje", user=None, origin="override", currency=None, day=None):
        return self.Rate.with_user(user or self.approver).create_manual(
            origin, "cnb", currency or self.eur, day or self.day, 1, rate, reason,
        )

    def test_manual_change_of_odoo_rate_is_refused(self):
        rate = self.odoo_rate(self.eur, self.day)
        self.assertTrue(rate)
        Rate = self.env["res.currency.rate"].with_user(self.accountant)
        with self.assertRaises(UserError):
            Rate.create({"currency_id": self.eur.id, "name": "2035-01-03", "rate": 0.05})
        with self.assertRaises(UserError):
            rate.with_user(self.accountant).write({"rate": 0.05})
        with self.assertRaises(UserError):
            rate.with_user(self.accountant).unlink()

    def test_override_wins_in_evidence_and_odoo(self):
        record = self.override(26)
        self.assertEqual((record.origin, record.overridden_id), ("override", self.published))
        self.assertEqual(self.Rate._effective("cnb", self.eur, self.day), record)
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, self.day), Decimal(26))
        self.assertAlmostEqual(self.odoo_rate(self.eur, self.day).rate, 1 / 26, places=10)

    def test_later_override_wins(self):
        first = self.override(26)
        second = self.override(25.5, reason="Oprava přepisu")
        self.assertEqual(second.overridden_id, first)
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, self.day), Decimal("25.5"))
        self.assertAlmostEqual(self.odoo_rate(self.eur, self.day).rate, 1 / 25.5, places=10)

    def test_override_needs_reason_and_approver(self):
        with self.assertRaises(UserError):
            self.override(26, reason=" ")
        with self.assertRaises(AccessError):
            self.override(26, user=self.accountant)

    def test_override_and_manual_kind_must_fit(self):
        with self.assertRaises(UserError):
            self.override(26, origin="manual")
        with self.assertRaises(UserError):
            self.override(26, day=date(2035, 1, 9))

    def test_manual_rate_for_day_without_published_rate(self):
        day = date(2035, 1, 9)
        record = self.override(24.8, origin="manual", reason="Zdroj kurz nevyhlásil", day=day)
        self.assertEqual(record.origin, "manual")
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, day), Decimal("24.8"))
        self.assertAlmostEqual(self.odoo_rate(self.eur, day).rate, 1 / 24.8, places=10)

    def test_manual_rate_cannot_be_changed(self):
        record = self.override(26)
        with self.assertRaises(UserError):
            record.sudo().write({"rate": 27})
        with self.assertRaises(UserError):
            record.sudo().unlink()

    def test_download_does_not_overwrite_different_odoo_rate(self):
        day = date(2035, 1, 16)
        self.env["res.currency.rate"].sudo().create({"currency_id": self.eur.id, "name": day, "rate": 0.05, "company_id": False})
        text = DAILY.replace("02.01.2035", "16.01.2035")
        with self.assertLogs("odoo.addons.investra_rates.models.rate", level="WARNING"):
            differences = self.Rate._store("cnb", *parse_cnb(text), text)._publish()
        self.assertEqual(len(differences), 1)
        self.assertEqual(self.odoo_rate(self.eur, day).rate, 0.05)

    def test_monthly_rates_skip_zero_and_stay_valid_for_a_month(self):
        stored = self.Rate._store("cnb", *parse_cnb(MONTHLY), MONTHLY, periodicity="monthly")
        self.assertEqual(stored.currency_id, self.afn)
        self.assertEqual(stored.periodicity, "monthly")
        self.assertEqual(self.Rate.get_rate("cnb", self.afn, date(2035, 2, 27)), Decimal("0.33612"))
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.afn, date(2035, 3, 10))

    def test_wizard_creates_override(self):
        wizard = self.env["investra.rate.override.wizard"].with_user(self.approver).create({
            "origin": "override", "source": "cnb", "currency_id": self.eur.id, "date": self.day,
            "quantity": 1, "rate": 26, "reason": "Chyba zdroje",
        })
        self.assertEqual(wizard.current_id, self.published)
        action = wizard.action_confirm()
        self.assertEqual(self.Rate.browse(action["res_id"]).origin, "override")
